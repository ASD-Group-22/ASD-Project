/* Create, read and delete saved snapshots. No update endpoint or edit control. */
const recommendationHistory = (() => {
  const el = id => document.getElementById(id);
  let latest = null;
  let saving = false;
  let saved = false;
  let generation = 0;
  let listRequest = 0;
  let detailRequest = 0;
  let viewedId = null;

  async function api(path, options = {}) {
    const response = await fetch(`${backend}/recommendations${path}`, options);
    let data;
   
    try { data = await response.json(); }
    catch { throw new Error('The server returned an unreadable response.'); }
    if (!response.ok) throw new Error(data.error || data.message || 'Request failed.');
    return data;
  }

  function updateSaveButton() {
    el('saveRecommendationBtn').disabled = !latest || saving || saved;
  }

  function generationStarted() {
    generation++;
    latest = null;
    saved = false;
   
    el('saveRecommendationStatus').textContent = '';
    updateSaveButton();
  }

  function generationSucceeded(result) {
    latest = JSON.parse(JSON.stringify(result));
    saved = false;
   
    el('saveRecommendationStatus').textContent = 'Decision made. Save this result to history to keep it.';
    updateSaveButton();
  }

  async function save() {
    if (!latest || saving || saved) return;
    const currentGeneration = generation;
    const payload = JSON.stringify(latest);
    
    saving = true;
    
    updateSaveButton();
    el('saveRecommendationStatus').textContent = 'Saving...';
    try {
      const result = await api('/create', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: payload
      });
      
      if (currentGeneration === generation) {
        saved = true;
        el('saveRecommendationStatus').textContent = `Saved as recommendation #${result.id}.`;
      }
     
      await loadHistory();
    } catch (error) {
      if (currentGeneration === generation) el('saveRecommendationStatus').textContent = error.message;
    } finally {
      saving = false;
      updateSaveButton();
    }
  }

  function displayDate(value) {
    if (!value) return 'Not recorded (older entry)';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleString();
  }

  async function loadHistory() {
    const requestId = ++listRequest;
    el('historyStatus').textContent = 'Loading history...';
    try {
      const subject = el('historySubject').value.trim();
      const records = await api(`/history?subject=${encodeURIComponent(subject)}`);
      
      if (requestId !== listRequest) return;
      if (!Array.isArray(records)) throw new Error('The server returned invalid history.');
     
      el('historyRows').replaceChildren();
      records.forEach(record => {
        const row = document.createElement('tr');
        [record.id, record.subject, displayDate(record.saved_at), record.group_count ?? '-'].forEach(value => {
          const cell = document.createElement('td');
          cell.textContent = value;
          row.append(cell);
        });
        const actions = document.createElement('td');
        const view = document.createElement('button');
       
        view.textContent = 'View';
        view.addEventListener('click', () => viewRecord(record.id));
       
        const remove = document.createElement('button');
       
        remove.textContent = 'Delete';
        remove.addEventListener('click', () => deleteRecord(record.id, remove));
        actions.append(view, remove);
        row.append(actions);
        el('historyRows').append(row);
      });
      el('historyStatus').textContent = records.length ? `${records.length} saved recommendation(s). Newest first.` : 'No saved recommendations found.';
    } catch (error) {
      if (requestId === listRequest) {
        el('historyRows').replaceChildren();
        el('historyStatus').textContent = error.message;
      }
    }
  }

  function formatRecord(record) {
    const snapshot = record.snapshot || {};
    const result = snapshot.recommendation;
    const lines = [`Subject: ${record.subject}`, `Saved: ${displayDate(record.saved_at)}`, `Model: ${record.model || 'Not recorded'}`, ''];
    
    if (result && Array.isArray(result.groups)) {
      result.groups.forEach(group => {
        lines.push(group.group_name || 'Group');
        lines.push(`Members: ${(group.members || group.student_ids || []).join(', ')}`);
        lines.push(String(group.reasoning || ''));
        if (group.weighted_skill_score !== undefined) lines.push(`Weighted skill score: ${group.weighted_skill_score}`);
        (group.coverage || []).forEach(c => lines.push(`${c.skill} (${c.required_level}): ${c.met ? 'covered' : 'GAP'}`));
        lines.push('');
      });
      lines.push(...(result.warnings || []));
    } else {
      lines.push(typeof result === 'string' ? result : JSON.stringify(result, null, 2));
    }
    
    if (snapshot.human_decision) lines.push('', `Human decision: ${snapshot.human_decision}`, `Reason: ${snapshot.decision_reason || '-'}`);
    if (snapshot.loop) lines.push('', 'Agentic loop:', JSON.stringify(snapshot.loop, null, 2));
    if (snapshot.note) lines.push('', String(snapshot.note));
    
    if (snapshot.requirements) lines.push('', 'Requirements at the time:', JSON.stringify(snapshot.requirements, null, 2));
    
    if (snapshot.students) lines.push('', 'Skill profiles at the time:', JSON.stringify(snapshot.students, null, 2));
    return lines.join('\n');
  }

  async function viewRecord(id) {
    const requestId = ++detailRequest;
    viewedId = id;
    
    el('historyDetails').hidden = false;
    el('historyDetailsTitle').textContent = `Saved Recommendation #${id}`;
    el('historyDetailsOutput').textContent = 'Loading...';
    try {
      const record = await api(`/history/${id}`);
      if (requestId === detailRequest) el('historyDetailsOutput').textContent = formatRecord(record);
    } catch (error) {
      if (requestId === detailRequest) el('historyDetailsOutput').textContent = error.message;
    }
  }

  function closeDetails() {
    detailRequest++;
    viewedId = null;
    
    el('historyDetails').hidden = true;
    el('historyDetailsOutput').textContent = '';
  }

  async function deleteRecord(id, button) {
    if (!window.confirm(`Delete saved recommendation #${id}? This cannot be undone.`)) return;
    
    button.disabled = true;
    
    try {
      await api(`/history/${id}`, {method: 'DELETE'});
      if (viewedId === id) closeDetails();
      await loadHistory();
    } catch (error) {
      el('historyStatus').textContent = error.message;
      button.disabled = false;
    }
  }

  el('saveRecommendationBtn').addEventListener('click', save);
  el('refreshHistoryBtn').addEventListener('click', loadHistory);
  el('closeHistoryBtn').addEventListener('click', closeDetails);
  el('historySubject').addEventListener('keydown', event => {
    if (event.key === 'Enter') loadHistory();
  });
  
  document.querySelector('[data-target="recommendationsPanel"]').addEventListener('click', loadHistory);
  return {generationStarted, generationSucceeded};
})();
