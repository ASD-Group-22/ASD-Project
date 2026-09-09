const API = window.BACKEND_URL;
let spaces = [];
const $ = (id) => document.getElementById(id);

async function api(path, options={}) {
  const res = await fetch(`${API}${path}`, {headers:{"Content-Type":"application/json", ...(options.headers||{})}, ...options});
  const data = await res.json().catch(()=>({error:"Invalid server response"}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

async function checkHealth(){
  try{const data=await api('/health'); $('serviceDot').classList.add('ok'); $('serviceText').textContent=`Backend online · ${data.model}`}
  catch(e){$('serviceText').textContent='Backend unavailable'}
}

function card(space, recommendation=false){
  const facilities=(space.facilities||[]).map(f=>`<span class="chip">${escapeHtml(f)}</span>`).join('');
  return `<article class="card">
    ${space.image_url?`<img src="${escapeAttr(space.image_url)}" alt="${escapeAttr(space.space_name)}" onerror="this.style.display='none'">`:''}
    <div class="card-body">
      <h3>${escapeHtml(space.space_name)}</h3>
      <div class="meta">${escapeHtml(space.building)} · Level ${escapeHtml(space.building_level)} · ${escapeHtml(space.room_number)}</div>
      <div class="meta">Capacity ${space.max_capacity} · ${escapeHtml(space.noise_level)} · ${escapeHtml(space.space_type)}</div>
      <div class="chips">${facilities}</div>
      <div class="meta">${escapeHtml(space.accessibility||'')}</div>
      ${recommendation?`<div class="reason"><strong>Why:</strong> ${escapeHtml(space.reason||'')}</div>`:`<div class="card-actions"><button class="ghost" onclick="editSpace(${space.space_id})">Edit</button><button class="danger" onclick="deleteSpace(${space.space_id})">Delete</button></div>`}
    </div></article>`;
}
function escapeHtml(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function escapeAttr(v){return escapeHtml(v)}

async function loadSpaces(){
  try{spaces=await api('/api/spaces'); renderSpaces()}catch(e){$('spaceGrid').innerHTML=`<div class="message">${escapeHtml(e.message)}</div>`}
}
function renderSpaces(){
  const text=$('filterText').value.trim().toLowerCase(), noise=$('filterNoise').value.toLowerCase(), cap=Number($('filterCapacity').value||0);
  const filtered=spaces.filter(s=>{
    const hay=`${s.space_name} ${s.building} ${s.room_number} ${(s.facilities||[]).join(' ')}`.toLowerCase();
    return (!text||hay.includes(text))&&(!noise||String(s.noise_level).toLowerCase()===noise)&&(!cap||s.max_capacity>=cap);
  });
  $('spaceGrid').innerHTML=filtered.map(s=>card(s)).join('') || '<div class="message">No spaces match these filters.</div>';
}

$('aiForm').addEventListener('submit', async e=>{
  e.preventDefault(); const query=$('query').value.trim(); if(!query)return;
  $('aiMessage').classList.remove('hidden'); $('aiMessage').textContent='Running Plan → Act → Observe → Adapt…'; $('recommendations').innerHTML='';
  try{
    const data=await api('/api/spaces/recommend',{method:'POST',body:JSON.stringify({query})});
    $('aiMessage').textContent=data.summary; $('recommendations').innerHTML=data.recommendations.map(s=>card(s,true)).join('');
  }catch(err){$('aiMessage').textContent=err.message}
});

document.querySelectorAll('[data-example]').forEach(b=>b.addEventListener('click',()=>{$('query').value=b.dataset.example}));
['filterText','filterNoise','filterCapacity'].forEach(id=>$(id).addEventListener('input',renderSpaces));


const dialog=$('spaceDialog');
$('addBtn').addEventListener('click',()=>openDialog()); $('closeDialog').onclick=()=>dialog.close(); $('cancelDialog').onclick=()=>dialog.close();
function openDialog(space=null){
  $('spaceForm').reset(); $('space_id').value=space?.space_id||''; $('dialogTitle').textContent=space?'Edit space':'Add space';
  const fields=['space_name','building','building_level','room_number','max_capacity','space_type','noise_level','accessibility','opening_time','closing_time','description','image_url'];
  fields.forEach(f=>{if(space && space[f]!=null)$(f).value=space[f]}); $('facilities').value=space?(space.facilities||[]).join(', '):''; dialog.showModal();
}
window.editSpace=id=>openDialog(spaces.find(s=>s.space_id===id));
window.deleteSpace=async id=>{if(!confirm('Delete this campus space?'))return; try{await api(`/api/spaces/${id}`,{method:'DELETE'}); await loadSpaces()}catch(e){alert(e.message)}};
$('spaceForm').addEventListener('submit',async e=>{
  e.preventDefault(); const id=$('space_id').value; const payload={};
  ['space_name','building','building_level','room_number','max_capacity','space_type','noise_level','accessibility','opening_time','closing_time','description','image_url'].forEach(f=>payload[f]=$(f).value);
  payload.max_capacity=Number(payload.max_capacity); payload.facilities=$('facilities').value.split(',').map(x=>x.trim()).filter(Boolean);
  try{await api(id?`/api/spaces/${id}`:'/api/spaces',{method:id?'PUT':'POST',body:JSON.stringify(payload)}); dialog.close(); await loadSpaces()}catch(err){alert(err.message)}
});

checkHealth(); loadSpaces();
