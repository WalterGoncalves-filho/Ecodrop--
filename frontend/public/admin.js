const API = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : 'https://ecodrop-production.up.railway.app';

// ── Helpers ──────────────────────────────────────────────────────────────────
const token = () => localStorage.getItem('admin_token');

async function req(method, path, body) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token() ? { Authorization: `Bearer ${token()}` } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw data.detail || 'Erro desconhecido';
  return data;
}

function toast(msg, err = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.background = err ? '#c0392b' : '#222';
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), 3000);
}

// ── Estado ───────────────────────────────────────────────────────────────────
let materiais = [];
let agendamentoAtual = null;

// ── Login ────────────────────────────────────────────────────────────────────
document.getElementById('btn-login').addEventListener('click', async () => {
  const email = document.getElementById('l-email').value.trim();
  const senha = document.getElementById('l-senha').value;
  if (!email || !senha) return toast('Preencha e-mail e senha.', true);

  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  try {
    const data = await req('POST', '/auth/login', { email, senha });
    localStorage.setItem('admin_token', data.access_token);

    const me = await req('GET', '/users/me');
    if (me.role !== 'admin') {
      localStorage.removeItem('admin_token');
      return toast('Acesso negado. Conta sem permissão de admin.', true);
    }

    document.getElementById('admin-nome').textContent = me.nome;
    document.getElementById('page-login').style.display = 'none';
    document.getElementById('page-admin').style.display = 'flex';

    await carregarMateriais();
  } catch (e) {
    toast(typeof e === 'string' ? e : 'Credenciais inválidas.', true);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('l-senha').addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('btn-login').click();
});

// ── Logout ───────────────────────────────────────────────────────────────────
document.getElementById('btn-logout').addEventListener('click', () => {
  localStorage.removeItem('admin_token');
  location.reload();
});

// ── Busca ────────────────────────────────────────────────────────────────────
document.getElementById('btn-buscar').addEventListener('click', buscar);
document.getElementById('filtro').addEventListener('keydown', e => { if (e.key === 'Enter') buscar(); });

async function buscar() {
  const q = document.getElementById('filtro').value.trim();
  const container = document.getElementById('lista-agendamentos');
  container.innerHTML = '<p class="empty">Buscando…</p>';
  try {
    const lista = await req('GET', `/admin/agendamentos${q ? `?q=${encodeURIComponent(q)}` : ''}`);
    renderTabela(lista);
  } catch (e) {
    toast(typeof e === 'string' ? e : 'Erro ao buscar agendamentos.', true);
    container.innerHTML = '<p class="empty">Erro ao carregar.</p>';
  }
}

function renderTabela(lista) {
  const container = document.getElementById('lista-agendamentos');
  if (!lista.length) {
    container.innerHTML = '<p class="empty">Nenhum agendamento em aberto encontrado.</p>';
    return;
  }

  const statusLabel = { scheduled: 'Agendado', confirmed: 'Confirmado', checked_in: 'Check-in' };
  const rows = lista.map(a => `
    <tr>
      <td>${a.id}</td>
      <td>${a.usuario_nome}<br/><small style="color:#888">${a.usuario_email}</small></td>
      <td>${a.usuario_cpf || '—'}</td>
      <td>${a.ponto_nome}</td>
      <td>${formatDate(a.data_agendada)}<br/><small>${a.janela_inicio.slice(0,5)}–${a.janela_fim.slice(0,5)}</small></td>
      <td><span class="badge badge-${a.status}">${statusLabel[a.status] || a.status}</span></td>
      <td><button class="btn-validar" onclick="abrirModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">Validar</button></td>
    </tr>
  `).join('');

  container.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead><tr><th>#</th><th>Usuário</th><th>CPF</th><th>Ponto</th><th>Data / Janela</th><th>Status</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

function formatDate(str) {
  const [y, m, d] = str.split('-');
  return `${d}/${m}/${y}`;
}

// ── Materiais ─────────────────────────────────────────────────────────────────
async function carregarMateriais() {
  try { materiais = await req('GET', '/admin/materiais'); } catch { materiais = []; }
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function abrirModal(ag) {
  agendamentoAtual = ag;
  document.getElementById('modal-sub').textContent =
    `Agendamento #${ag.id} · ${ag.usuario_nome} · ${formatDate(ag.data_agendada)}`;
  document.getElementById('itens-list').innerHTML = '';
  document.getElementById('obs-validar').value = '';
  document.getElementById('resultado').style.display = 'none';
  document.getElementById('btn-confirmar').disabled = false;
  adicionarItemRow();
  document.getElementById('modal-overlay').classList.add('open');
}

function fecharModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  agendamentoAtual = null;
}

document.getElementById('modal-fechar').addEventListener('click', fecharModal);
document.getElementById('btn-cancelar').addEventListener('click', fecharModal);
document.getElementById('modal-overlay').addEventListener('click', e => { if (e.target === e.currentTarget) fecharModal(); });

document.getElementById('btn-add-item').addEventListener('click', adicionarItemRow);

function adicionarItemRow() {
  const list = document.getElementById('itens-list');
  const row = document.createElement('div');
  row.className = 'item-row';

  const sel = document.createElement('select');
  sel.innerHTML = '<option value="">Selecione o material…</option>' +
    materiais.map(m => `<option value="${m.id}" data-unidade="${m.unidade}">${m.nome} (${m.unidade})</option>`).join('');

  const qty = document.createElement('input');
  qty.type = 'number';
  qty.min = '0.01';
  qty.step = '0.01';
  qty.placeholder = 'Qtd';

  const rm = document.createElement('button');
  rm.className = 'btn-remove';
  rm.textContent = '✕';
  rm.onclick = () => row.remove();

  row.append(sel, qty, rm);
  list.appendChild(row);
}

// ── Confirmar ─────────────────────────────────────────────────────────────────
document.getElementById('btn-confirmar').addEventListener('click', async () => {
  const rows = document.querySelectorAll('#itens-list .item-row');
  const itens = [];

  for (const row of rows) {
    const material_id = parseInt(row.querySelector('select').value);
    const quantidade = parseFloat(row.querySelector('input').value);
    if (!material_id || !quantidade || quantidade <= 0) continue;
    itens.push({ material_id, quantidade });
  }

  if (!itens.length) return toast('Adicione ao menos um material com quantidade.', true);

  const btn = document.getElementById('btn-confirmar');
  btn.disabled = true;
  try {
    const res = await req('POST', `/admin/agendamentos/${agendamentoAtual.id}/validar`, {
      itens,
      observacoes: document.getElementById('obs-validar').value.trim() || null,
    });

    document.getElementById('res-protocolo').textContent = res.protocolo;
    document.getElementById('res-usuario').textContent = res.usuario;
    document.getElementById('res-pontos').textContent = `${res.total_pontos} pts`;
    document.getElementById('res-valor').textContent = `R$ ${res.total_valor.toFixed(2)}`;
    document.getElementById('resultado').style.display = 'block';
    document.getElementById('btn-add-item').style.display = 'none';
    document.getElementById('itens-list').style.display = 'none';
    document.getElementById('obs-validar').closest('.fg-obs').style.display = 'none';
    document.getElementById('modal-actions') && (document.querySelector('.modal-actions').style.display = 'none');

    toast(`Coleta validada! ${res.total_pontos} pts creditados.`);
    buscar(); // atualiza a lista
  } catch (e) {
    toast(typeof e === 'string' ? e : 'Erro ao validar coleta.', true);
    btn.disabled = false;
  }
});

// ── Auto-login se já tiver token ──────────────────────────────────────────────
(async () => {
  if (!token()) return;
  try {
    const me = await req('GET', '/users/me');
    if (me.role !== 'admin') { localStorage.removeItem('admin_token'); return; }
    document.getElementById('admin-nome').textContent = me.nome;
    document.getElementById('page-login').style.display = 'none';
    document.getElementById('page-admin').style.display = 'flex';
    await carregarMateriais();
  } catch {
    localStorage.removeItem('admin_token');
  }
})();

// ── Tabs ──────────────────────────────────────────────────────────────────────
function switchTab(name) {
  document.querySelectorAll('.tab-btn').forEach((b, i) => {
    const tabs = ['agendamentos', 'suporte'];
    b.classList.toggle('active', tabs[i] === name);
  });
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.getElementById(`tab-${name}`).classList.add('active');
  if (name === 'suporte') carregarTickets('');
}

// ── Tickets Admin ─────────────────────────────────────────────────────────────
let ticketAtual = null;
let ticketStatusFiltro = '';

async function carregarTickets(statusFilter) {
  ticketStatusFiltro = statusFilter;
  const container = document.getElementById('lista-tickets');
  container.innerHTML = '<p class="empty">Carregando…</p>';
  try {
    const url = `/admin/tickets${statusFilter ? `?status=${statusFilter}` : ''}`;
    const tickets = await req('GET', url);
    renderTickets(tickets);
  } catch (e) {
    container.innerHTML = '<p class="empty">Erro ao carregar tickets.</p>';
  }
}

function filtrarTickets(btn, status) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  carregarTickets(status);
}

const statusLabel = { open: 'Aberto', in_progress: 'Em andamento', resolved: 'Resolvido', closed: 'Fechado' };
const prioLabel = { high: 'Alta', medium: 'Média', low: 'Baixa' };

function renderTickets(tickets) {
  const container = document.getElementById('lista-tickets');
  if (!tickets.length) {
    container.innerHTML = '<p class="empty">Nenhum ticket encontrado.</p>';
    return;
  }
  container.innerHTML = '<div class="ticket-list">' + tickets.map(t => `
    <div class="ticket-item" onclick='abrirTicket(${JSON.stringify(t).replace(/'/g,"&#39;")})'>
      <div class="ticket-item-head">
        <div>
          <div class="ticket-item-title">${escHtml(t.subject)}</div>
          <div class="ticket-item-meta">${escHtml(t.usuario_nome)} · ${escHtml(t.usuario_email)}</div>
        </div>
        <span class="chip chip-${t.status}">${statusLabel[t.status] || t.status}</span>
      </div>
      <div class="ticket-item-tags">
        <span class="chip chip-${t.priority}">${prioLabel[t.priority] || t.priority}</span>
        <span class="chip" style="background:#f0ede8;color:#555">${t.interactionCount} interações</span>
        <span class="chip" style="background:#f0ede8;color:#555">${escHtml(t.category)}</span>
      </div>
    </div>
  `).join('') + '</div>';
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function abrirTicket(ticket) {
  ticketAtual = ticket;
  document.getElementById('tk-subject').textContent = ticket.subject;
  document.getElementById('tk-meta').textContent =
    `${ticket.category} · ${ticket.usuario_nome} · CPF: ${ticket.usuario_cpf || '—'}`;
  document.getElementById('tk-reply').value = '';
  document.getElementById('tk-new-status').value = '';

  // Mostrar box de CPF se categoria for "Conta" ou assunto mencionar CPF
  const isCpf = /cpf/i.test(ticket.subject) || /cpf/i.test(ticket.category);
  const cpfBox = document.getElementById('tk-cpf-box');
  cpfBox.style.display = isCpf ? 'block' : 'none';
  if (isCpf) {
    document.getElementById('tk-cpf-atual').textContent = ticket.usuario_cpf || '—';
    document.getElementById('tk-cpf-novo').value = '';
  }

  const thread = document.getElementById('tk-thread');
  thread.innerHTML = (ticket.messages || []).map(m => `
    <div class="bubble ${m.authorId !== ticket.usuario_id ? 'admin-bubble' : ''}">
      <strong>${escHtml(m.authorName)}</strong>
      <small>${m.createdAt ? m.createdAt.slice(0,16).replace('T',' ') : ''}</small>
      <p>${escHtml(m.message)}</p>
    </div>
  `).join('');
  thread.scrollTop = thread.scrollHeight;

  document.getElementById('modal-ticket').classList.add('open');
}

function fecharModalTicket() {
  document.getElementById('modal-ticket').classList.remove('open');
  ticketAtual = null;
}

document.getElementById('modal-ticket').addEventListener('click', e => {
  if (e.target === e.currentTarget) fecharModalTicket();
});

async function enviarRespostaTicket() {
  const msg = document.getElementById('tk-reply').value.trim();
  if (!msg) return toast('Digite uma resposta.', true);
  const newStatus = document.getElementById('tk-new-status').value || undefined;
  try {
    await req('POST', `/admin/tickets/${ticketAtual.id}/reply`, { message: msg, new_status: newStatus || null });
    toast('✅ Resposta enviada.');
    fecharModalTicket();
    carregarTickets(ticketStatusFiltro);
  } catch (e) {
    toast(typeof e === 'string' ? e : 'Erro ao responder.', true);
  }
}

async function adminGrantCpf() {
  if (!confirm(`Liberar edição de CPF para ${ticketAtual.usuario_nome}?`)) return;
  try {
    await req('POST', `/admin/users/${ticketAtual.usuario_id}/grant-cpf-edit`, { ticket_id: ticketAtual.id });
    toast('✅ Permissão de edição de CPF concedida.');
    fecharModalTicket();
    carregarTickets(ticketStatusFiltro);
  } catch (e) {
    toast(typeof e === 'string' ? e : 'Erro ao conceder permissão.', true);
  }
}

async function adminFixCpf() {
  const cpf = document.getElementById('tk-cpf-novo').value.trim();
  if (!cpf) return toast('Informe o novo CPF.', true);
  if (!confirm(`Corrigir CPF de ${ticketAtual.usuario_nome} para ${cpf}?`)) return;
  try {
    await req('PATCH', `/admin/users/${ticketAtual.usuario_id}/fix-cpf`, { cpf });
    toast('✅ CPF corrigido com sucesso.');
    fecharModalTicket();
    carregarTickets(ticketStatusFiltro);
  } catch (e) {
    toast(typeof e === 'string' ? e : 'Erro ao corrigir CPF.', true);
  }
}
