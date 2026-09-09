/* Human decision on the current result; persisted only by Save to History. */
const agenticReview = (() => {
  const el = id => document.getElementById(id);
  let current = null;

  function controls(enabled) {
    el('acceptRunBtn').disabled = !enabled;
    el('rejectRunBtn').disabled = !enabled;
    el('decisionReason').disabled = !enabled;
  }

  function started() {
    current = null;
    controls(false);
    el('decisionReason').value = '';
    el('loopOutput').textContent = '';
    el('loopStatus').textContent = 'Qwen is proposing; Python and Llama are checking. One proposal and one advisory review.';
  }

  function formatLoop(loop, result = {}) {
    if (!loop) return 'No loop details were returned. The request may have failed before the loop started.';
    const lines = [];
    if (result.model) lines.push(`Proposer: ${result.model}; reviewer: ${result.review_model}`);
    lines.push(`Attempts: ${loop.attempts ?? loop.trace?.length ?? 0}`,
      `Selected attempt: ${loop.selected_attempt ?? 'None'}`,
      `Stopped: ${loop.stop_reason || 'Unknown'}`);
    if (loop.plan) lines.push(`Planned group sizes: ${(loop.plan.group_sizes || []).join(', ')}`);
    if (loop.review) {
      lines.push(`Llama recommendation (advisory): ${loop.review.approved}. ${loop.review.reason}`,
        ...(loop.review.issues || []));
    } else {
      lines.push('No Llama review is available for a selected proposal. Structurally invalid proposals do not reach the reviewer.');
    }
    if (loop.quality) {
      lines.push(`Suggested quality targets met: ${loop.quality.criteria_met}`,
        `Weighted coverage gaps: ${loop.quality.weighted_gaps}`,
        `Balance ratio: ${Number(loop.quality.balance_ratio).toFixed(3)} (target ${loop.plan?.balance_target ?? '-'})`);
    }
    for (const attempt of loop.trace || []) {
      lines.push('', `Attempt ${attempt.attempt}: ${attempt.status}`, ...(attempt.feedback || []));
    }
    return lines.join('\n');
  }

  function received(data) {
    current = JSON.parse(JSON.stringify(data));
    const loop = current.loop;
    el('loopOutput').textContent = formatLoop(loop, current);
    el('loopStatus').textContent = 'Review the proposed groups and warnings, then Accept or Reject.';
    controls(true);
  }

  function decide(decision) {
    if (!current || current.human_decision !== 'pending') return;
    current.human_decision = decision;
    current.decision_reason = el('decisionReason').value.trim();
    current.note = `Human decision: ${decision}. This does not create groups automatically.`;
    controls(false);
    recommendationHistory.generationSucceeded(current);
    el('loopStatus').textContent = `Proposal ${decision}. Click Save to History to keep the result and decision. Generate again for a new proposal.`;
  }

  function failed(message, loop) {
    current = null;
    controls(false);
    el('loopStatus').textContent = message;
    el('loopOutput').textContent = formatLoop(loop);
  }

  el('acceptRunBtn').addEventListener('click', () => decide('accepted'));
  el('rejectRunBtn').addEventListener('click', () => decide('rejected'));
  controls(false);
  return {started, received, failed};
})();
