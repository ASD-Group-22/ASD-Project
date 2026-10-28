(() => {
  const el = id => document.getElementById(id);
  const status = el('maStatus');
  const results = el('maResults');
  const output = el('maOutput');
  const summary = el('maSummary');
  const evidencePanel = el('maEvidence');
  const agentResults = el('maAgentResults');
  const humanStatus = el('maHumanStatus');
  const finalResult = el('maFinalResult');
  const reviewButtons = [...document.querySelectorAll('[data-ma-decision]')];
  let workflowId = null;
  let currentWorkflow = null;
  let workflowInProgress = false;
  let reviewInProgress = false;

  function humanDecisionLabel(decision) {
    return ({ approve: 'Approved', partial_accept: 'Partially accepted', correct: 'Corrected', reject: 'Rejected' })[decision] || decision;
  }

  function reviewFeedback(message) {
    status.textContent = message;
    if (humanStatus) humanStatus.textContent = message;
  }

  function updateReviewControls() {
    const canReview = !workflowInProgress && !reviewInProgress && currentWorkflow?.status === 'awaiting_human_review';
    reviewButtons.forEach(button => { button.disabled = !canReview; });
    el('maStartBtn').disabled = workflowInProgress || reviewInProgress;
  }

  async function request(path, options = {}) {
    const response = await fetch(`${backend}/r2${path}`, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Multi-Agent request failed.');
    return data;
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    })[character]);
  }

  function asList(value) {
    if (Array.isArray(value)) return value.filter(item => item !== null && item !== undefined);
    if (typeof value === 'string' && value.trim()) return [value.trim()];
    return [];
  }

  function displayValue(value) {
    if (value === null || value === undefined || value === '') return 'Not provided.';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  function listHtml(values, emptyText = 'None recorded.') {
    const items = asList(values);
    return items.length
      ? `<ul>${items.map(item => `<li>${escapeHtml(displayValue(item))}</li>`).join('')}</ul>`
      : `<p>${escapeHtml(emptyText)}</p>`;
  }

  function chipsHtml(values, className = '') {
    const items = asList(values);
    return items.length
      ? `<div class="ma-chip-list">${items.map(item => `<span class="ma-chip ${className}">${escapeHtml(displayValue(item))}</span>`).join('')}</div>`
      : '<p>None recorded.</p>';
  }

  function detailValue(object, names, fallback = '') {
    if (!object || typeof object !== 'object') return fallback;
    for (const name of names) {
      if (object[name] !== null && object[name] !== undefined && object[name] !== '') return object[name];
    }
    return fallback;
  }

  function sourceLabel(source) {
    if (!source || typeof source !== 'object') return 'Recorded Student 3 evidence';
    return source.service || source.name || 'Recorded Student 3 evidence';
  }

  function requirementChips(requirements) {
    if (!requirements || typeof requirements !== 'object') return '<p>No subject requirements were returned.</p>';
    const entries = Object.entries(requirements);
    if (!entries.length) return '<p>No subject requirements were returned.</p>';
    return `<div class="ma-chip-list">${entries.map(([skill, detail]) =>
      `<span class="ma-chip">${escapeHtml(skill)}: ${escapeHtml(displayValue(detail))}</span>`
    ).join('')}</div>`;
  }

  function groupMembers(group) {
    const ids = asList(group?.member_student_ids);
    const names = asList(group?.member_names);
    if (names.length && ids.length) return names.map((name, index) => `${name} (${ids[index] ?? '?'})`);
    if (names.length) return names;
    if (ids.length) return ids.map(id => `Student ${id}`);
    return asList(group?.members);
  }

  function renderEvidence(evidence) {
    if (!evidence || typeof evidence !== 'object') {
      evidencePanel.innerHTML = '<div class="ma-evidence-card"><p>No evidence record was returned.</p></div>';
      return;
    }
    const profiles = Array.isArray(evidence.profiles) ? evidence.profiles : [];
    const groups = Array.isArray(evidence.deterministic_group_proposal) ? evidence.deterministic_group_proposal : [];
    const source = sourceLabel(evidence.source);
    const endpoints = asList(evidence.source?.endpoints);
    const context = evidence.request_context || {};
    const evidenceCount = Number.isInteger(evidence.evidence_count)
      ? evidence.evidence_count
      : Array.isArray(evidence.evidence_items) ? evidence.evidence_items.length : 0;

    evidencePanel.innerHTML = `
      <div class="ma-evidence-card">
        <h4>Recorded evidence</h4>
        <p><strong>Source:</strong> ${escapeHtml(source)}</p>
        <p><strong>Subject:</strong> ${escapeHtml(displayValue(context.subject))} · <strong>Profiles:</strong> ${profiles.length} · <strong>Evidence records:</strong> ${evidenceCount}</p>
        ${endpoints.length ? `<p><strong>Endpoints:</strong> ${escapeHtml(endpoints.join(', '))}</p>` : ''}
        <p class="ma-section-label">Subject skill requirements</p>
        ${requirementChips(evidence.requirements)}
      </div>
      ${groups.length ? `
        <p class="ma-section-label">Evidence-based group proposal</p>
        <div class="ma-group-grid">
          ${groups.map(group => `
            <article class="ma-group-card">
              <h4>${escapeHtml(detailValue(group, ['group_name', 'name'], 'Proposed group'))}</h4>
              <p><strong>Members</strong></p>
              ${chipsHtml(groupMembers(group))}
              <p><strong>Covered skills</strong></p>
              ${chipsHtml(detailValue(group, ['covered_required_skills', 'covered_skills'], []), 'covered')}
              <p><strong>Coverage gaps</strong></p>
              ${chipsHtml(detailValue(group, ['missing_required_skills', 'missing_skills'], []), 'gap')}
            </article>`).join('')}
        </div>` : ''}`;
  }

  function plannerCard(planner) {
    const plan = detailValue(planner, ['plan', 'result'], {});
    const content = plan && typeof plan === 'object' ? plan : planner || {};
    const statusText = detailValue(planner, ['status'], 'not run');
    return `
      <article class="ma-agent-card">
        <h4>Planner</h4>
        <div class="ma-agent-meta">${escapeHtml(statusText)} · ${escapeHtml(detailValue(planner, ['model'], 'model unavailable'))}</div>
        <h5>Objective</h5>
        <p>${escapeHtml(displayValue(detailValue(content, ['objective', 'goal', 'summary'], 'No objective was returned.')))}</p>
        <h5>Steps</h5>
        ${listHtml(detailValue(content, ['steps', 'plan_steps'], []))}
        <h5>Constraints</h5>
        ${listHtml(detailValue(content, ['constraints', 'guardrails'], []))}
        <h5>Required evidence</h5>
        ${chipsHtml(detailValue(content, ['required_evidence', 'evidence_needed'], []))}
      </article>`;
  }

  function workerCard(worker, evidence) {
    const result = detailValue(worker, ['result', 'output'], {});
    const content = result && typeof result === 'object' ? result : worker || {};
    const fallback = worker?.status === 'fallback';
    const deterministic = evidence?.deterministic_worker_result || {};
    const answer = detailValue(content, ['answer', 'recommendation', 'response'], fallback ? deterministic.answer : 'No answer was returned.');
    const references = detailValue(content, ['selected_references', 'evidence_references'], fallback ? deterministic.selected_references : []);
    const limitations = detailValue(content, ['limitations', 'limits'], fallback ? deterministic.limitations : []);
    return `
      <article class="ma-agent-card">
        <h4>Worker</h4>
        <div class="ma-agent-meta">${escapeHtml(detailValue(worker, ['status'], 'not run'))} · ${escapeHtml(detailValue(worker, ['model'], 'model unavailable'))}</div>
        ${fallback ? '<div class="ma-review-notice"><h4>Evidence-based fallback shown</h4><p>The model output was unusable. This proposal is derived only from the recorded Student 3 requirements and selected profiles.</p></div>' : ''}
        <h5>Answer</h5>
        <p>${escapeHtml(displayValue(answer))}</p>
        <h5>Selected evidence</h5>
        ${chipsHtml(references)}
        <h5>Limitations</h5>
        ${listHtml(limitations)}
      </article>`;
  }

  function reviewPresentation(workflow) {
    const reviewer = workflow.reviewer || {};
    const sharedReview = detailValue(reviewer, ['review', 'result'], {});
    const review = workflow.student3_review || (sharedReview && typeof sharedReview === 'object' ? sharedReview : {});
    const reviewDecision = String(detailValue(review, ['decision'], '')).toLowerCase();
    const manualReview = reviewDecision === 'needs_human_review' || !['approve', 'revise', 'reject'].includes(reviewDecision);
    const source = String(review.source || '');
    const responseStatus = String(reviewer.model_response_status || '');
    // Older saved workflows used status=success even when evidence rules replaced Llama.
    const evidenceFallback = source === 'student3_evidence_guardrail' || source === 'student3_evidence_validation';
    const invalidResponse = ['invalid_output_guarded', 'invalid_output', 'unavailable'].includes(responseStatus);
    const accepted = reviewer.status === 'success' && !manualReview && !evidenceFallback && !invalidResponse;
    const unavailable = responseStatus === 'unavailable';
    const label = accepted
      ? 'Llama review successful'
      : evidenceFallback
        ? (unavailable ? 'Evidence fallback — Llama unavailable' : 'Evidence fallback — Llama review failed validation')
        : 'Llama review unavailable — human review required';
    return { reviewer, review, manualReview, accepted, evidenceFallback, unavailable, label };
  }

  function reviewerCard(workflow) {
    const { reviewer, review, manualReview, accepted, evidenceFallback, label } = reviewPresentation(workflow);
    const retry = workflow.student3_reviewer_retry;
    const attempts = Array.isArray(reviewer.attempts) ? reviewer.attempts : [];
    const decision = manualReview ? 'Manual review required' : detailValue(review, ['decision'], 'No valid decision returned');
    const issues = detailValue(review, ['issues', 'concerns'], []);
    const recommendation = detailValue(review, ['recommendation', 'notes'], 'No reviewer recommendation was returned.');
    const planFollowed = detailValue(review, ['plan_followed'], null);
    const grounded = detailValue(review, ['evidence_grounded'], null);
    return `
      <article class="ma-agent-card">
        <h4>Reviewer</h4>
        <div class="ma-agent-meta">${escapeHtml(label)}</div>
        <p><strong>${accepted ? 'Reviewer model' : 'Model attempted'}:</strong> ${escapeHtml(detailValue(reviewer, ['model'], 'model unavailable'))}</p>
        ${attempts.length > 1 ? `<p><strong>Reviewer attempts:</strong> ${attempts.length}. ${accepted ? 'The repaired response passed validation.' : 'No attempt produced an accepted model review.'}</p>` : ''}
        ${retry?.performed ? `<p><strong>Review retry:</strong> ${retry.retry_error ? 'The retry could not be completed.' : 'One schema-repair retry was used.'}</p>` : ''}
        ${!accepted ? `<div class="ma-review-notice"><h4>${evidenceFallback ? 'Evidence findings shown' : 'Human review required'}</h4><p>No accepted Llama decision is available. ${evidenceFallback ? 'The findings below come from Student 3 evidence checks.' : 'Inspect the recorded proposal and evidence.'} Complete the human review below.</p>${reviewer.fallback_reason ? `<p><strong>Reason:</strong> ${escapeHtml(reviewer.fallback_reason)}</p>` : ''}</div>` : ''}
        <h5>Decision</h5>
        <p><strong>${escapeHtml(displayValue(decision))}</strong></p>
        ${review.source ? `<p><strong>Review source:</strong> ${escapeHtml(displayValue(review.source))}</p>` : ''}
        ${accepted && planFollowed !== null ? `<p><strong>Plan followed:</strong> ${escapeHtml(displayValue(planFollowed))}</p>` : ''}
        ${accepted && grounded !== null ? `<p><strong>Evidence grounded:</strong> ${escapeHtml(displayValue(grounded))}</p>` : ''}
        <h5>Issues</h5>
        ${listHtml(issues)}
        <h5>Recommendation</h5>
        <p>${escapeHtml(displayValue(recommendation))}</p>
      </article>`;
  }

  function renderHumanResult(workflow) {
    if (!finalResult) return;
    const human = workflow.human_review || {};
    const finished = ['completed', 'rejected'].includes(workflow.status) && human.status === 'completed' && human.decision;
    finalResult.hidden = !finished;
    if (!finished) {
      finalResult.innerHTML = '';
      return;
    }
    const rejected = human.decision === 'reject';
    const acceptedResponse = typeof workflow.final_response === 'string' ? workflow.final_response : '';
    const responseText = escapeHtml(acceptedResponse).replace(/\r?\n/g, '<br>');
    finalResult.innerHTML = `
      <h4 id="maFinalHeading">${escapeHtml(humanDecisionLabel(human.decision))}</h4>
      <p>Your human decision has been saved for workflow ${escapeHtml(workflow.workflow_id || workflowId)}.</p>
      ${rejected
        ? '<p>No proposal was accepted.</p>'
        : `<h5>Accepted response</h5><p>${responseText || 'No accepted response text was returned.'}</p>`}
      ${human.notes ? `<h5>Saved review notes</h5><p>${escapeHtml(human.notes).replace(/\r?\n/g, '<br>')}</p>` : ''}
      <p>This records the workflow outcome. Final groups have not been created automatically.</p>`;
  }

  function render(workflow) {
    currentWorkflow = workflow;
    workflowId = workflow.workflow_id || workflowId;
    const humanDecision = workflow.human_review?.decision;
    summary.innerHTML = [
      ['Workflow', workflow.workflow_id || 'not recorded'],
      ['Status', workflow.status || 'unknown'],
      ['Task', workflow.task_type || 'group formation'],
      ...(humanDecision ? [['Human decision', humanDecision]] : [])
    ].map(([label, value]) => `<span class="ma-summary-item"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(displayValue(value))}</span>`).join('');
    renderEvidence(workflow.evidence);
    agentResults.innerHTML = plannerCard(workflow.planner || {}) + workerCard(workflow.worker || {}, workflow.evidence || {}) + reviewerCard(workflow);
    output.textContent = JSON.stringify(workflow, null, 2);
    results.hidden = false;
    renderHumanResult(workflow);
    updateReviewControls();
  }

  function evidenceProposal(workflow) {
    const evidence = workflow?.evidence;
    if (!Array.isArray(evidence?.deterministic_group_proposal)) return null;
    const answer = evidence?.deterministic_worker_result?.answer;
    return typeof answer === 'string' && answer.trim() ? { groups: evidence.deterministic_group_proposal, answer } : null;
  }

  async function selectedStudentIds() {
    const text = el('maStudentIds').value.trim();
    if (text) {
      const values = text.split(',').map(value => value.trim());
      if (values.some(value => !/^\d+$/.test(value) || Number(value) < 1)) {
        throw new Error('Enter positive student IDs separated by commas.');
      }
      const ids = values.map(Number);
      if (new Set(ids).size !== ids.length) throw new Error('Remove duplicate student IDs.');
      return ids;
    }
    const response = await fetch(`${backend}/ai/profiles`);
    const profiles = await response.json().catch(() => []);
    if (!response.ok || !Array.isArray(profiles) || !profiles.length) {
      throw new Error('Could not load current Skill Profiles.');
    }
    return profiles.map(profile => profile.student_id).filter(Number.isInteger);
  }

  async function loadStatus() {
    try {
      const data = await request('/multi-agent/status');
      status.textContent = data.multi_agent_enabled
        ? (data.service_reachable ? 'Shared Multi-Agent service is available.' : `Service unavailable: ${data.service_error || 'start it on port 5101.'}`)
        : 'Multi-Agent Mode is disabled.';
    } catch (error) {
      status.textContent = error.message;
    }
  }

  el('maStartBtn').addEventListener('click', async () => {
    if (workflowInProgress || reviewInProgress) return;
    workflowInProgress = true;
    currentWorkflow = null;
    workflowId = null;
    updateReviewControls();
    results.hidden = true;
    if (humanStatus) humanStatus.textContent = '';
    if (finalResult) {
      finalResult.hidden = true;
      finalResult.innerHTML = '';
    }
    status.textContent = 'Collecting evidence and running Planner, Worker and Reviewer…';
    try {
      const subject = el('maSubject').value;
      if (!subject) throw new Error('Select a subject.');
      const workflow = await request('/multi-agent/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          subject,
          group_size: Number(el('maGroupSize').value),
          student_ids: await selectedStudentIds(),
          user_request: el('maRequest').value.trim()
        })
      });
      render(workflow);
      const reviewState = reviewPresentation(workflow);
      status.textContent = !reviewState.accepted
        ? `${reviewState.label}. The proposal and evidence remain available for your human decision.`
        : workflow.worker?.status === 'fallback'
          ? 'The Worker used the evidence-based Student 3 proposal. Review it before selecting a human decision.'
          : 'Llama review completed successfully. The workflow is ready for your human decision.';
    } catch (error) {
      status.textContent = error.message;
    } finally {
      workflowInProgress = false;
      updateReviewControls();
    }
  });

  reviewButtons.forEach(button => button.addEventListener('click', async () => {
    if (workflowInProgress || reviewInProgress) return;
    if (!workflowId || currentWorkflow?.status !== 'awaiting_human_review') {
      reviewFeedback('There is no workflow awaiting a human decision. Start a new workflow to review another proposal.');
      return;
    }
    reviewInProgress = true;
    updateReviewControls();
    reviewFeedback('Saving your human decision…');
    try {
      const decision = button.dataset.maDecision;
      const notes = el('maNotes').value.trim();
      const proposal = evidenceProposal(currentWorkflow);
      if (decision === 'approve' && currentWorkflow?.worker?.status === 'fallback' && proposal?.answer) {
        throw new Error('The model result fell back. Review the evidence-based proposal and use Partially Accept to save it, or Reject it.');
      }
      const correctedResponse = decision === 'correct'
        ? notes
        : decision === 'partial_accept' && proposal?.answer
          ? proposal.answer
          : null;
      const workflow = await request(`/multi-agent/workflows/${encodeURIComponent(workflowId)}/human-review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, notes, corrected_response: correctedResponse })
      });
      render(workflow);
      reviewFeedback(`${humanDecisionLabel(workflow.human_review?.decision || decision)} — decision and workflow outcome saved below.`);
    } catch (error) {
      reviewFeedback(error.message);
    } finally {
      reviewInProgress = false;
      updateReviewControls();
    }
  }));

  loadStatus();
})();
