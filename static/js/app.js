/* SGM Drivers — app.js  */
'use strict';

// ─── STATE ───────────────────────────────────────────────
let allDrivers = [];
let licenceChart = null;
const AVATAR_COLORS = ['#3d8ef0','#2fd16e','#f04f3d','#f0903d','#a855f7','#e8f443','#ec4899','#14b8a6','#f59e0b','#8b5cf6'];

// ─── INIT ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadStats();
  loadDriversForDash();
  loadChart();
  document.querySelectorAll('.modal-overlay').forEach(o => {
    o.addEventListener('click', e => { if (e.target === o) o.classList.remove('open'); });
  });
});

// ─── NAVIGATION ──────────────────────────────────────────
const PAGE_TITLES = {
  dashboard:'Dashboard', drivers:'Drivers', licences:'Licences',
  training:'Training & CPC', contracts:'Contracts', payments:'Payments',
  documents:'Documents', reports:'Reports & Export', users:'User Management'
};

function navigate(page, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const sec = document.getElementById('page-' + page);
  if (sec) sec.classList.add('active');
  if (el) el.classList.add('active');
  else {
    const nav = document.getElementById('nav-' + page);
    if (nav) nav.classList.add('active');
  }
  document.getElementById('topbarTitle').textContent = PAGE_TITLES[page] || page;
  // Lazy load data
  const loaders = {
    drivers: loadDrivers, licences: loadLicences, training: loadTraining,
    contracts: loadContracts, payments: loadPayments, documents: loadDocuments,
    reports: loadDbStats, users: loadUsers
  };
  if (loaders[page]) loaders[page]();
  if (page === 'dashboard') { loadStats(); loadDriversForDash(); }
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ─── TOAST ───────────────────────────────────────────────
function showToast(icon, title, msg, type = 'green') {
  const colors = { green: 'var(--green)', red: 'var(--red)', blue: 'var(--blue)', orange: 'var(--orange)' };
  const el = document.createElement('div');
  el.className = 'toast';
  el.innerHTML = `
    <div class="toast-icon">${icon}</div>
    <div class="toast-content">
      <div class="toast-title" style="color:${colors[type]||'var(--text)'}">${title}</div>
      <div class="toast-msg">${msg}</div>
    </div>
    <div class="toast-close" onclick="this.parentElement.remove()">×</div>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

// ─── API HELPERS ──────────────────────────────────────────
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  } catch (err) {
    showToast('❌', 'API Error', err.message, 'red');
    throw err;
  }
}

// ─── MODAL ───────────────────────────────────────────────
function openModal(type) {
  populateDriverSelects();
  // Reset hidden IDs
  const editId = document.getElementById(type.charAt(0) + '_' + (type === 'driver' ? 'first_name' : 'driver_id'));
  const hidden = document.getElementById(type + 'EditId') || document.getElementById('driverEditId');
  if (hidden) hidden.value = '';
  document.getElementById('modal-' + type).classList.add('open');
}

function closeModal(type) {
  document.getElementById('modal-' + type).classList.remove('open');
}

async function populateDriverSelects() {
  if (allDrivers.length === 0) {
    try { allDrivers = await apiFetch('/api/drivers'); } catch { return; }
  }
  const opts = allDrivers.map(d => `<option value="${d.id}">${d.driver_id} — ${d.full_name}</option>`).join('');
  ['l_driver_id','t_driver_id','c_driver_id','p_driver_id','doc_driver_id'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.innerHTML = opts;
  });
}

// ─── HELPERS ─────────────────────────────────────────────
function getInitials(name) {
  return name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

function avatarColor(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length];
}

function expiryClass(dateStr) {
  if (!dateStr) return 'exp-none';
  const diff = (new Date(dateStr) - new Date()) / 86400000;
  if (diff < 0) return 'exp-critical';
  if (diff <= 30) return 'exp-warn';
  return 'exp-ok';
}

function expiryEmoji(dateStr) {
  if (!dateStr) return '—';
  const diff = (new Date(dateStr) - new Date()) / 86400000;
  if (diff < 0) return '❌';
  if (diff <= 30) return '⚠️';
  return '✅';
}

function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
}

function fmtGBP(n) {
  if (!n && n !== 0) return '—';
  return '£' + Number(n).toLocaleString('en-GB', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function statusBadge(status) {
  const map = {
    'Active': 'badge-green', 'Inactive': 'badge-grey', 'Suspended': 'badge-red',
    'Valid': 'badge-green', 'Expiring': 'badge-orange', 'Expired': 'badge-red',
    'Compliant': 'badge-green', 'In Progress': 'badge-blue', 'Overdue': 'badge-red',
    'Completed': 'badge-green', 'Scheduled': 'badge-blue',
    'Paid': 'badge-green', 'Pending': 'badge-orange', 'Failed': 'badge-red',
    'Full-time': 'badge-yellow', 'Part-time': 'badge-blue', 'Temporary': 'badge-orange',
    'Agency': 'badge-purple', 'Zero-hours': 'badge-grey',
    'No Expiry': 'badge-grey'
  };
  return map[status] || 'badge-grey';
}

function statusEmoji(status) {
  const map = {
    'Active':'✅','Inactive':'⚫','Suspended':'🔴','Valid':'✅','Expiring':'⚠️','Expired':'❌',
    'Compliant':'✅','In Progress':'🔄','Overdue':'❌','Completed':'✅','Paid':'✅','Pending':'⏳','Failed':'❌'
  };
  return map[status] || '';
}

// ─── DASHBOARD ───────────────────────────────────────────
async function loadStats() {
  try {
    const s = await apiFetch('/api/stats');
    document.getElementById('stat-drivers').textContent = s.total_drivers;
    document.getElementById('stat-licences').textContent = s.expiring_licences;
    document.getElementById('stat-cpc').textContent = s.cpc_hours + 'h';
    document.getElementById('stat-payroll').textContent = fmtGBP(s.total_payroll);
    document.getElementById('alertCount').textContent = s.alerts_count;
    document.querySelectorAll('.stat-card').forEach(c => c.classList.remove('skeleton'));

    // Alerts badge
    const badge = document.getElementById('badge-licences');
    if (s.expiring_licences > 0) {
      badge.textContent = s.expiring_licences;
      badge.style.display = '';
    }

    // Alerts list
    const list = document.getElementById('alertsList');
    if (!list) return;
    if (s.alerts.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text3);font-size:12px;">✅ No active alerts</div>';
      return;
    }
    list.innerHTML = s.alerts.map(a => `
      <div class="alert-item ${a.type}">
        <div class="alert-dot"></div>
        <div><div class="alert-text">${a.text}</div><div class="alert-time">${a.tag}</div></div>
      </div>`).join('');
  } catch {}
}

async function loadDriversForDash() {
  try {
    const drivers = await apiFetch('/api/drivers');
    allDrivers = drivers;
    const tbody = document.getElementById('dashTable');
    if (!tbody) return;
    if (!drivers.length) { tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text3);">No drivers found</td></tr>'; return; }

    const training = await apiFetch('/api/training');
    const cpcByDriver = {};
    training.forEach(t => { cpcByDriver[t.driver_id] = (cpcByDriver[t.driver_id] || 0) + (t.hours_completed || 0); });

    const licences = await apiFetch('/api/licences');
    const licByDriver = {};
    licences.forEach(l => { licByDriver[l.driver_id] = l; });

    tbody.innerHTML = drivers.slice(0, 7).map(d => {
      const cpc = cpcByDriver[d.id] || 0;
      const pct = Math.min(Math.round((cpc / 35) * 100), 100);
      const lic = licByDriver[d.id];
      const expiry = lic ? lic.expiry_date : null;
      const col = pct >= 100 ? 'var(--green)' : pct > 50 ? 'var(--blue)' : 'var(--orange)';
      return `<tr>
        <td><div class="driver-cell">
          <div class="driver-av" style="background:${avatarColor(d.id)}">${getInitials(d.full_name)}</div>
          <div><div class="td-name">${d.full_name}</div><div class="td-id">${d.driver_id}</div></div>
        </div></td>
        <td><span class="badge badge-blue">${d.licence_type}</span></td>
        <td>${d.contract_type}</td>
        <td style="min-width:130px;">
          <div style="font-size:10.5px;color:var(--text3);">${cpc.toFixed(0)}/35 hrs</div>
          <div class="progress-bar" style="width:100px"><div class="progress-fill" style="width:${pct}%;background:${col}"></div></div>
        </td>
        <td class="${expiryClass(expiry)}">${expiryEmoji(expiry)} ${fmtDate(expiry)}</td>
        <td><span class="badge ${statusBadge(d.status)}">${statusEmoji(d.status)} ${d.status}</span></td>
      </tr>`;
    }).join('');
  } catch {}
}

async function loadChart() {
  try {
    const data = await apiFetch('/api/chart/licences');
    const ctx = document.getElementById('licenceChart');
    if (!ctx) return;
    if (licenceChart) licenceChart.destroy();
    licenceChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          { label: 'Valid', data: data.valid, backgroundColor: 'rgba(47,209,110,.7)', borderRadius: 5 },
          { label: 'Expiring ≤30d', data: data.expiring, backgroundColor: 'rgba(240,144,61,.7)', borderRadius: 5 },
          { label: 'Expired', data: data.expired, backgroundColor: 'rgba(240,79,61,.7)', borderRadius: 5 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#8891a8', font: { family: 'Space Mono', size: 10 }, boxWidth: 10 } } },
        scales: {
          x: { ticks: { color: '#555f78', font: { family: 'Space Mono', size: 10 } }, grid: { color: '#1e2330' } },
          y: { ticks: { color: '#555f78', font: { family: 'Space Mono', size: 10 } }, grid: { color: '#1e2330' } }
        }
      }
    });
  } catch {}
}

// ─── DRIVERS ─────────────────────────────────────────────
async function loadDrivers(q = '', status = '') {
  const tbody = document.getElementById('driversTable');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="8" class="loading-pulse" style="text-align:center;padding:24px">Loading...</td></tr>';
  try {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (status) params.set('status', status);
    const drivers = await apiFetch('/api/drivers?' + params);
    allDrivers = drivers;
    if (!drivers.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:28px;color:var(--text3);">No drivers found</td></tr>';
      return;
    }
    tbody.innerHTML = drivers.map(d => `
      <tr>
        <td class="td-id">${d.driver_id}</td>
        <td><div class="driver-cell">
          <div class="driver-av" style="background:${avatarColor(d.id)}">${getInitials(d.full_name)}</div>
          <div><div class="td-name">${d.full_name}</div><div style="font-size:11px;color:var(--text3)">${d.email || '—'}</div></div>
        </div></td>
        <td><span class="badge badge-blue">${d.licence_type || '—'}</span></td>
        <td><span class="badge ${statusBadge(d.contract_type)}">${d.contract_type}</span></td>
        <td class="td-mono">${fmtGBP(d.salary)}</td>
        <td class="td-id">${fmtDate(d.start_date)}</td>
        <td><span class="badge ${statusBadge(d.status)}">${statusEmoji(d.status)} ${d.status}</span></td>
        <td><div class="action-btns">
          <button class="btn btn-ghost btn-sm" title="Edit" onclick="editDriver(${d.id})">✏️</button>
          <button class="btn btn-ghost btn-sm" title="Delete" onclick="confirmDelete('driver',${d.id},'${d.full_name}')">🗑️</button>
        </div></td>
      </tr>`).join('');
  } catch {}
}

async function editDriver(id) {
  try {
    const d = await apiFetch('/api/drivers/' + id);
    document.getElementById('driverEditId').value = id;
    document.getElementById('driverModalTitle').textContent = '✏️ Edit Driver';
    document.getElementById('d_first_name').value = d.first_name || '';
    document.getElementById('d_last_name').value = d.last_name || '';
    document.getElementById('d_dob').value = d.date_of_birth || '';
    document.getElementById('d_ni').value = d.ni_number || '';
    document.getElementById('d_email').value = d.email || '';
    document.getElementById('d_phone').value = d.phone || '';
    document.getElementById('d_address').value = d.address || '';
    document.getElementById('d_nationality').value = d.nationality || 'British';
    document.getElementById('d_licence_type').value = d.licence_type || 'LGV';
    document.getElementById('d_contract_type').value = d.contract_type || 'Full-time';
    document.getElementById('d_salary').value = d.salary || '';
    document.getElementById('d_start').value = d.start_date || '';
    document.getElementById('d_status').value = d.status || 'Active';
    document.getElementById('d_notes').value = d.notes || '';
    document.getElementById('modal-driver').classList.add('open');
  } catch {}
}

async function saveDriver() {
  const id = document.getElementById('driverEditId').value;
  const fn = document.getElementById('d_first_name').value.trim();
  const ln = document.getElementById('d_last_name').value.trim();
  if (!fn || !ln) { showToast('⚠️','Validation','First name and last name are required','orange'); return; }
  const payload = {
    first_name: fn, last_name: ln,
    date_of_birth: document.getElementById('d_dob').value || null,
    ni_number: document.getElementById('d_ni').value,
    email: document.getElementById('d_email').value,
    phone: document.getElementById('d_phone').value,
    address: document.getElementById('d_address').value,
    nationality: document.getElementById('d_nationality').value,
    licence_type: document.getElementById('d_licence_type').value,
    contract_type: document.getElementById('d_contract_type').value,
    salary: parseFloat(document.getElementById('d_salary').value) || 0,
    start_date: document.getElementById('d_start').value || null,
    status: document.getElementById('d_status').value,
    notes: document.getElementById('d_notes').value
  };
  try {
    if (id) {
      await apiFetch('/api/drivers/' + id, { method: 'PUT', body: JSON.stringify(payload) });
      showToast('✅', 'Driver Updated', fn + ' ' + ln + ' has been updated', 'green');
    } else {
      await apiFetch('/api/drivers', { method: 'POST', body: JSON.stringify(payload) });
      showToast('✅', 'Driver Added', fn + ' ' + ln + ' registered successfully', 'green');
    }
    closeModal('driver');
    allDrivers = [];
    loadDrivers();
    loadDriversForDash();
    loadStats();
  } catch {}
}

// ─── LICENCES ────────────────────────────────────────────
async function loadLicences() {
  const tbody = document.getElementById('licencesTable');
  if (!tbody) return;
  try {
    const licences = await apiFetch('/api/licences');
    const valid = licences.filter(l => l.expiry_status === 'Valid').length;
    const expiring = licences.filter(l => l.expiry_status === 'Expiring').length;
    setIfExists('lic-total', licences.length);
    setIfExists('lic-expiring', expiring);
    setIfExists('lic-valid', valid);

    if (!licences.length) { tbody.innerHTML = emptyRow(9, 'No licences found'); return; }
    tbody.innerHTML = licences.map(l => {
      const days = l.days_to_expiry;
      const daysStr = days === null ? '—' : days < 0 ? `<span style="color:var(--red)">${days}d</span>` :
        days <= 30 ? `<span style="color:var(--orange)">${days}d</span>` :
        `<span style="color:var(--green)">${days}d</span>`;
      return `<tr>
        <td class="td-name">${l.driver_name}</td>
        <td><span class="badge badge-blue">${l.licence_type}</span></td>
        <td class="td-id">${l.licence_number || '—'}</td>
        <td><span class="tag">${l.categories || '—'}</span></td>
        <td class="td-id">${fmtDate(l.issue_date)}</td>
        <td class="${expiryClass(l.expiry_date)}">${expiryEmoji(l.expiry_date)} ${fmtDate(l.expiry_date)}</td>
        <td>${daysStr}</td>
        <td><span class="badge ${statusBadge(l.expiry_status)}">${l.expiry_status}</span></td>
        <td><div class="action-btns">
          <button class="btn btn-ghost btn-sm" onclick='editLicence(${JSON.stringify(l).replace(/'/g,"\\'")}  )'>✏️</button>
          <button class="btn btn-ghost btn-sm" onclick="confirmDelete('licence',${l.id},'licence for ${l.driver_name}')">🗑️</button>
        </div></td>
      </tr>`;
    }).join('');
  } catch {}
}

function editLicence(l) {
  document.getElementById('licenceEditId').value = l.id;
  populateDriverSelects().then(() => {
    document.getElementById('l_driver_id').value = l.driver_id;
    document.getElementById('l_licence_type').value = l.licence_type;
    document.getElementById('l_number').value = l.licence_number || '';
    document.getElementById('l_categories').value = l.categories || '';
    document.getElementById('l_issue').value = l.issue_date || '';
    document.getElementById('l_expiry').value = l.expiry_date || '';
    document.getElementById('l_authority').value = l.issuing_authority || 'DVLA';
    document.getElementById('l_notes').value = l.notes || '';
  });
  document.getElementById('modal-licence').classList.add('open');
}

async function saveLicence() {
  const id = document.getElementById('licenceEditId').value;
  const payload = {
    driver_id: document.getElementById('l_driver_id').value,
    licence_type: document.getElementById('l_licence_type').value,
    licence_number: document.getElementById('l_number').value,
    categories: document.getElementById('l_categories').value,
    issue_date: document.getElementById('l_issue').value || null,
    expiry_date: document.getElementById('l_expiry').value || null,
    issuing_authority: document.getElementById('l_authority').value,
    notes: document.getElementById('l_notes').value
  };
  if (!payload.expiry_date) { showToast('⚠️','Validation','Expiry date is required','orange'); return; }
  try {
    if (id) {
      await apiFetch('/api/licences/' + id, { method: 'PUT', body: JSON.stringify(payload) });
      showToast('✅','Licence Updated','Licence record updated','green');
    } else {
      await apiFetch('/api/licences', { method: 'POST', body: JSON.stringify(payload) });
      showToast('✅','Licence Added','New licence record saved','green');
    }
    closeModal('licence');
    loadLicences();
    loadStats();
  } catch {}
}

// ─── TRAINING ─────────────────────────────────────────────
async function loadTraining() {
  const tbody = document.getElementById('trainingTable');
  if (!tbody) return;
  try {
    const training = await apiFetch('/api/training');
    const compliant = new Set(training.filter(t => t.cpc_total >= 35).map(t => t.driver_id)).size;
    const overdue = training.filter(t => t.status === 'Overdue').length;
    const totalHours = training.reduce((a, t) => a + (t.hours_completed || 0), 0);
    setIfExists('train-compliant', compliant);
    setIfExists('train-hours', totalHours.toFixed(0) + 'h');
    setIfExists('train-overdue', overdue);

    if (!training.length) { tbody.innerHTML = emptyRow(8, 'No training records found'); return; }
    tbody.innerHTML = training.map(t => {
      const cpc = t.cpc_total || 0;
      const pct = Math.min(Math.round((cpc / 35) * 100), 100);
      const col = pct >= 100 ? 'var(--green)' : pct > 50 ? 'var(--blue)' : 'var(--orange)';
      return `<tr>
        <td class="td-name">${t.driver_name}</td>
        <td>${t.course_type}</td>
        <td style="font-size:12px;color:var(--text3)">${t.provider || '—'}</td>
        <td class="td-id">${fmtDate(t.completion_date || t.start_date)}</td>
        <td class="td-mono" style="font-weight:700">${t.hours_completed}h</td>
        <td style="min-width:120px">
          <div style="font-size:10.5px;color:var(--text3);margin-bottom:3px">${cpc.toFixed(0)}/35 hrs</div>
          <div class="progress-bar"><div class="progress-fill" style="width:${pct}%;background:${col}"></div></div>
        </td>
        <td><span class="badge ${statusBadge(t.status)}">${statusEmoji(t.status)} ${t.status}</span></td>
        <td><div class="action-btns">
          <button class="btn btn-ghost btn-sm" onclick="confirmDelete('training',${t.id},'training record')">🗑️</button>
        </div></td>
      </tr>`;
    }).join('');
  } catch {}
}

async function saveTraining() {
  const payload = {
    driver_id: document.getElementById('t_driver_id').value,
    course_type: document.getElementById('t_course_type').value,
    provider: document.getElementById('t_provider').value,
    certificate_number: document.getElementById('t_cert').value,
    start_date: document.getElementById('t_start').value || null,
    completion_date: document.getElementById('t_completion').value || null,
    hours_completed: parseFloat(document.getElementById('t_hours').value) || 0,
    status: document.getElementById('t_status').value,
    notes: document.getElementById('t_notes').value
  };
  try {
    await apiFetch('/api/training', { method: 'POST', body: JSON.stringify(payload) });
    showToast('✅','Training Logged','Training record saved','green');
    closeModal('training');
    loadTraining();
    loadStats();
  } catch {}
}

// ─── CONTRACTS ─────────────────────────────────────────────
async function loadContracts() {
  const tbody = document.getElementById('contractsTable');
  if (!tbody) return;
  try {
    const contracts = await apiFetch('/api/contracts');
    if (!contracts.length) { tbody.innerHTML = emptyRow(9, 'No contracts found'); return; }
    tbody.innerHTML = contracts.map(c => `
      <tr>
        <td class="td-name">${c.driver_name}</td>
        <td><span class="badge ${statusBadge(c.contract_type)}">${c.contract_type}</span></td>
        <td class="td-id">${fmtDate(c.start_date)}</td>
        <td class="td-id">${c.end_date ? fmtDate(c.end_date) : '<span style="color:var(--text3)">Permanent</span>'}</td>
        <td class="td-mono">${fmtGBP(c.salary)}</td>
        <td style="color:var(--text3);font-size:12px">${c.notice_period || '—'}</td>
        <td style="color:var(--text3);font-size:12px">${c.holiday_entitlement || 28}d</td>
        <td><span class="badge ${statusBadge(c.status)}">${statusEmoji(c.status)} ${c.status}</span></td>
        <td><div class="action-btns">
          <button class="btn btn-ghost btn-sm" onclick="confirmDelete('contract',${c.id},'contract for ${c.driver_name}')">🗑️</button>
        </div></td>
      </tr>`).join('');
  } catch {}
}

async function saveContract() {
  const payload = {
    driver_id: document.getElementById('c_driver_id').value,
    contract_type: document.getElementById('c_type').value,
    start_date: document.getElementById('c_start').value || null,
    end_date: document.getElementById('c_end').value || null,
    salary: parseFloat(document.getElementById('c_salary').value) || 0,
    hourly_rate: parseFloat(document.getElementById('c_hourly').value) || null,
    notice_period: document.getElementById('c_notice').value,
    holiday_entitlement: parseInt(document.getElementById('c_holiday').value) || 28,
    notes: document.getElementById('c_notes').value
  };
  if (!payload.start_date) { showToast('⚠️','Validation','Start date is required','orange'); return; }
  try {
    await apiFetch('/api/contracts', { method: 'POST', body: JSON.stringify(payload) });
    showToast('✅','Contract Created','Contract record saved','green');
    closeModal('contract');
    loadContracts();
  } catch {}
}

// ─── PAYMENTS ─────────────────────────────────────────────
function calcNet() {
  const gross = parseFloat(document.getElementById('p_gross').value) || 0;
  const paye = parseFloat(document.getElementById('p_paye').value) || 0;
  const eni = parseFloat(document.getElementById('p_eni').value) || 0;
  const pension = parseFloat(document.getElementById('p_pension').value) || 0;
  const net = gross - paye - eni - pension;
  document.getElementById('p_net').value = net > 0 ? '£' + net.toFixed(2) : '';
}

async function loadPayments() {
  const tbody = document.getElementById('paymentsTable');
  if (!tbody) return;
  try {
    const payments = await apiFetch('/api/payments');
    const totalGross = payments.reduce((a, p) => a + p.gross_pay, 0);
    const totalNet = payments.reduce((a, p) => a + p.net_pay, 0);
    const pending = payments.filter(p => p.status === 'Pending').length;
    setIfExists('pay-gross', fmtGBP(totalGross));
    setIfExists('pay-net', fmtGBP(totalNet));
    setIfExists('pay-pending', pending);

    if (!payments.length) { tbody.innerHTML = emptyRow(10, 'No payment records found'); return; }
    tbody.innerHTML = payments.map(p => `
      <tr>
        <td class="td-name">${p.driver_name}</td>
        <td class="td-id">${p.pay_period || '—'}</td>
        <td class="td-mono" style="font-weight:700">${fmtGBP(p.gross_pay)}</td>
        <td class="td-mono" style="color:var(--red)">£${(p.paye_tax||0).toFixed(0)}</td>
        <td class="td-mono" style="color:var(--orange)">£${(p.employee_ni||0).toFixed(0)}</td>
        <td class="td-mono" style="color:var(--text3)">£${(p.employer_ni||0).toFixed(0)}</td>
        <td class="td-mono" style="color:var(--green);font-weight:700">${fmtGBP(p.net_pay)}</td>
        <td><span class="tag">${p.payment_method || '—'}</span></td>
        <td><span class="badge ${statusBadge(p.status)}">${statusEmoji(p.status)} ${p.status}</span></td>
        <td><div class="action-btns">
          ${p.status === 'Pending' ? `<button class="btn btn-ghost btn-sm" onclick="markPaid(${p.id})">✅</button>` : ''}
          <button class="btn btn-ghost btn-sm" onclick="confirmDelete('payment',${p.id},'payment record')">🗑️</button>
        </div></td>
      </tr>`).join('');
  } catch {}
}

async function markPaid(id) {
  try {
    await apiFetch('/api/payments/' + id, { method: 'PUT', body: JSON.stringify({ status: 'Paid' }) });
    showToast('✅','Payment Updated','Payment marked as paid','green');
    loadPayments();
  } catch {}
}

async function savePayment() {
  const gross = parseFloat(document.getElementById('p_gross').value) || 0;
  if (!gross) { showToast('⚠️','Validation','Gross pay is required','orange'); return; }
  const paye = parseFloat(document.getElementById('p_paye').value) || 0;
  const eni = parseFloat(document.getElementById('p_eni').value) || 0;
  const pension = parseFloat(document.getElementById('p_pension').value) || 0;
  const payload = {
    driver_id: document.getElementById('p_driver_id').value,
    pay_period: document.getElementById('p_period').value,
    gross_pay: gross, paye_tax: paye, employee_ni: eni, pension: pension,
    payment_method: document.getElementById('p_method').value,
    payment_date: document.getElementById('p_date').value || new Date().toISOString().split('T')[0],
    status: document.getElementById('p_status').value
  };
  try {
    await apiFetch('/api/payments', { method: 'POST', body: JSON.stringify(payload) });
    showToast('✅','Payment Logged','Payment record saved','green');
    closeModal('payment');
    loadPayments();
  } catch {}
}

// ─── DOCUMENTS ─────────────────────────────────────────────
async function loadDocuments() {
  const tbody = document.getElementById('documentsTable');
  if (!tbody) return;
  try {
    const docs = await apiFetch('/api/documents');
    if (!docs.length) { tbody.innerHTML = emptyRow(7, 'No documents found'); return; }
    tbody.innerHTML = docs.map(d => `
      <tr>
        <td class="td-name">${d.driver_name}</td>
        <td><span class="badge badge-blue">${d.doc_type}</span></td>
        <td class="td-id">${d.reference_number || '—'}</td>
        <td class="td-id">${fmtDate(d.upload_date)}</td>
        <td class="${expiryClass(d.expiry_date)}">${d.expiry_date ? expiryEmoji(d.expiry_date) + ' ' + fmtDate(d.expiry_date) : '<span style="color:var(--text3)">No Expiry</span>'}</td>
        <td><span class="badge ${statusBadge(d.expiry_status)}">${d.expiry_status}</span></td>
        <td><div class="action-btns">
          <button class="btn btn-ghost btn-sm" title="Delete" onclick="confirmDelete('document',${d.id},'document ${d.doc_type}')">🗑️</button>
        </div></td>
      </tr>`).join('');
  } catch {}
}

async function saveDocument() {
  const payload = {
    driver_id: document.getElementById('doc_driver_id').value,
    doc_type: document.getElementById('doc_type').value,
    reference_number: document.getElementById('doc_ref').value,
    expiry_date: document.getElementById('doc_expiry').value || null,
    file_name: document.getElementById('doc_file').files[0]?.name || '',
    notes: document.getElementById('doc_notes').value
  };
  try {
    await apiFetch('/api/documents', { method: 'POST', body: JSON.stringify(payload) });
    showToast('📁','Document Saved','Document record stored','green');
    closeModal('document');
    loadDocuments();
  } catch {}
}

// ─── USERS ─────────────────────────────────────────────────
async function loadUsers() {
  const tbody = document.getElementById('usersTable');
  if (!tbody) return;
  try {
    const users = await apiFetch('/api/users');
    if (!users.length) { tbody.innerHTML = emptyRow(5, 'No users found'); return; }
    tbody.innerHTML = users.map(u => `
      <tr>
        <td><div class="driver-cell">
          <div class="user-avatar" style="width:28px;height:28px;font-size:11px;">${u.username.slice(0,2).toUpperCase()}</div>
          <span class="td-name">${u.username}</span>
        </div></td>
        <td style="color:var(--text3)">${u.email}</td>
        <td><span class="badge ${u.role==='admin'?'badge-red':u.role==='hr'?'badge-blue':'badge-grey'}">${u.role}</span></td>
        <td class="td-id">${u.id}</td>
        <td><div class="action-btns">
          <button class="btn btn-ghost btn-sm" onclick="confirmDelete('user',${u.id},'user ${u.username}')">🗑️</button>
        </div></td>
      </tr>`).join('');
  } catch {}
}

async function saveUser() {
  const payload = {
    username: document.getElementById('u_username').value.trim(),
    email: document.getElementById('u_email').value.trim(),
    password: document.getElementById('u_password').value,
    role: document.getElementById('u_role').value
  };
  if (!payload.username || !payload.email || !payload.password) {
    showToast('⚠️','Validation','All fields required for new user','orange'); return;
  }
  try {
    await apiFetch('/api/users', { method: 'POST', body: JSON.stringify(payload) });
    showToast('✅','User Created','New user account created','green');
    closeModal('user');
    loadUsers();
  } catch {}
}

// ─── REPORTS / DB STATS ──────────────────────────────────
async function loadDbStats() {
  const el = document.getElementById('dbStats');
  if (!el) return;
  try {
    const s = await apiFetch('/api/stats');
    el.innerHTML = [
      ['Drivers', s.total_drivers, '👥'],
      ['Active Contracts', s.active_contracts, '📋'],
      ['Payroll Records', '—', '💷'],
      ['Alerts Active', s.alerts_count, '⚠️'],
    ].map(([lbl, val, icon]) => `
      <div class="db-stat">
        <div style="font-size:24px;margin-bottom:6px">${icon}</div>
        <div class="db-stat-val">${val}</div>
        <div class="db-stat-lbl">${lbl}</div>
      </div>`).join('');
  } catch {}
}

// ─── EXPORT ──────────────────────────────────────────────
function exportData(entity) {
  showToast('⬇', 'Exporting', 'Preparing ' + entity + ' CSV...', 'blue');
  window.location.href = '/api/export/' + entity;
}

// ─── DELETE CONFIRM ──────────────────────────────────────
const deleteEndpoints = {
  driver: '/api/drivers/', licence: '/api/licences/', training: '/api/training/',
  contract: '/api/contracts/', payment: '/api/payments/', document: '/api/documents/', user: '/api/users/'
};

const afterDelete = {
  driver: () => { loadDrivers(); loadDriversForDash(); loadStats(); },
  licence: () => { loadLicences(); loadStats(); },
  training: loadTraining, contract: loadContracts,
  payment: loadPayments, document: loadDocuments, user: loadUsers
};

function confirmDelete(entity, id, label) {
  document.getElementById('confirmMsg').innerHTML =
    `Are you sure you want to delete <strong style="color:var(--text)">${label}</strong>?<br><br>
     <span style="color:var(--red);font-size:12px">⚠️ This action cannot be undone.</span>`;
  const btn = document.getElementById('confirmBtn');
  btn.onclick = async () => {
    try {
      await apiFetch(deleteEndpoints[entity] + id, { method: 'DELETE' });
      showToast('🗑️', 'Deleted', label + ' has been removed', 'orange');
      closeModal('confirm');
      if (afterDelete[entity]) afterDelete[entity]();
    } catch {}
  };
  document.getElementById('modal-confirm').classList.add('open');
}

// ─── UTILS ───────────────────────────────────────────────
function setIfExists(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function emptyRow(cols, msg) {
  return `<tr><td colspan="${cols}" style="text-align:center;padding:32px;color:var(--text3)">${msg}</td></tr>`;
}
