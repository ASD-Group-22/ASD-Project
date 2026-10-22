/* Student 5 UI for the group's SHARED Planner/Worker/Reviewer workflow. */
(() => {
  const byId = id => document.getElementById(id);
  const form = byId('multiAgentForm');
  if (!form) return;
  const API = window.BACKEND_URL || 'http://localhost:8055';
  const status = byId('multiAgentStatus');
  const result = byId('multiAgentResult');
  const review = byId('multiAgentReview');
  let workflowId = null;
  const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

  async function post(path, body) {
    const resp = await fetch(`${API}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await resp.json().catch(() => ({ error: 'Invalid server response' }));
    if (!resp.ok) throw Error(data.error || `Request failed (${resp.status})`);
    return data;
  }

  const pretty = obj => `<pre style="white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px">${safe(JSON.stringify(obj ?? {}, null, 2))}</pre>`;
  function card(space) {
    return `<article class="card">${space.image_url ? `<img src="${safe(space.image_url)}" alt="${safe(space.space_name)}" onerror="this.style.display='none'">` : ''}
      <div class="card-body"><h3>${safe(space.space_name)}</h3><div class="meta">${safe(space.building)} · ${safe(space.room_number)}</div>
      <div class="meta">Capacity ${safe(space.max_capacity)} · ${safe(space.noise_level)}</div></div></article>`;
  }

  function render(data) {
    // The group's coordinator returns evidence separately from worker output.
    // These cards are sourced from the backend and are NOT labelled as approved recommendations.
    const sourceCandidates = data.evidence?.candidates || [];
    const workerText = JSON.stringify(data.worker || {});
    const cited = new Set([...workerText.matchAll(/space:(\d+)/g)].map(match => Number(match[1])));
    const spaces = cited.size
      ? sourceCandidates.filter(space => cited.has(Number(space.space_id)))
      : sourceCandidates;
    const cards = spaces.length
      ? `<p><strong>${cited.size ? 'Worker-referenced spaces' : 'Matching stored evidence (pending human review)'}</strong></p><div class="cards">${spaces.map(card).join('')}</div>`
      : '<p>No stored spaces matched the supplied constraints.</p>';
    const planner = data.planner?.plan || data.planner || {};
    const reviewer = data.reviewer?.review || data.reviewer || {};
    const human = data.human_review || {};
    const isFinal = Boolean(human.decision);
    result.innerHTML = `<div class="release2-flow">
      <div class="agent-stage"><strong>Planner</strong><p>${safe(planner.objective || data.user_request || '')}</p>${pretty(planner)}</div>
      <div class="agent-stage"><strong>Worker</strong><p>${safe(data.evidence?.total_spaces_checked ?? '?')} stored spaces inspected; ${safe(data.evidence?.evidence_count ?? 0)} matching evidence records.</p>${cards}${pretty(data.worker)}</div>
      <div class="agent-stage"><strong>Reviewer</strong>${pretty(reviewer)}</div>
      <div class="agent-stage"><strong>Human Review</strong><p>${safe(isFinal ? human.decision : 'Awaiting your decision')}</p>${human.notes ? `<p>${safe(human.notes)}</p>` : ''}</div>
    </div>`;
    result.classList.remove('hidden');
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    workflowId = null;
    review.classList.add('hidden');
    result.classList.add('hidden');
    status.classList.remove('hidden');
    status.textContent = 'Running shared Planner → Worker → Reviewer…';
    try {
      const data = await post('/api/multi-agent/workflows', {
        query: byId('multiAgentQuery').value.trim()
      });
      workflowId = data.workflow_id;
      render(data);
      if (!workflowId) throw Error('Shared server did not return a workflow_id');
      if (data.human_review?.decision) {
        status.textContent = `Workflow status: ${data.status}`;
      } else {
        status.textContent = 'Agents completed. Human review required.';
        review.classList.remove('hidden');
      }
    } catch (error) {
      status.textContent = error.message;
    }
  });

  review.addEventListener('submit', async event => {
    event.preventDefault();
    if (!workflowId) return;
    const decision = byId('multiAgentDecision').value;
    const comment = byId('multiAgentComment').value.trim();
    if (decision !== 'approve' && !comment) {
      status.textContent = 'Add a reason for this decision.';
      return;
    }
    try {
      const data = await post(`/api/multi-agent/workflows/${encodeURIComponent(workflowId)}/review`, {
        decision, comment
      });
      render(data);
      review.classList.add('hidden');
      status.textContent = `Human decision recorded: ${data.status}`;
    } catch (error) {
      status.textContent = error.message;
    }
  });
})();
