/* All shared AI service requests go through the Student 3 backend. */
(() => {
  const el = id => document.getElementById(id);
  async function send(path, payload, output, button) {
    button.disabled = true;
    output.textContent = 'Contacting the shared local service...';
    try {
      const response = await fetch(`${backend}/r1/${path}`, {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Request failed.');
      if (path === 'mcp' || path === 'rag/refresh' || path === 'rag/retrieve') {
        output.textContent = JSON.stringify(data, null, 2);
      } else {
        output.textContent = [data.answer, '', `Confidence: ${data.confidence_category}`,
          `Status: ${data.status}`, '', 'Sources:',
          ...data.citations.map(c => `${c.source_id} (chunk: ${c.chunk_id})`)
        ].join('\n');
      }
    } catch (error) { output.textContent = error.message; }
    finally { button.disabled = false; }
  }
  el('r1Tool').addEventListener('change', () => {
    el('r1Subject').disabled = el('r1Tool').value !== 'student3_group_requirements';
  });
  el('r1McpBtn').addEventListener('click', () => {
    const tool = el('r1Tool').value;
    const subject = el('r1Subject').value;
    if (tool === 'student3_group_requirements' && !subject) {
      el('r1McpOutput').textContent = 'No subject is selected. If subjects failed to load, check the backend and reload the page.';
      return;
    }
    send('mcp', {tool, subject}, el('r1McpOutput'), el('r1McpBtn'));
  });
  el('r1RagBtn').addEventListener('click', () => send('rag/answer', {
    query: el('r1Query').value, k: 5
  }, el('r1RagOutput'), el('r1RagBtn')));
  el('r1RetrieveBtn').addEventListener('click', () => send('rag/retrieve', {
    query: el('r1Query').value, k: 5
  }, el('r1RagOutput'), el('r1RetrieveBtn')));
  el('r1RefreshBtn').addEventListener('click', () => send('rag/refresh', {}, el('r1RagOutput'), el('r1RefreshBtn')));
})();
