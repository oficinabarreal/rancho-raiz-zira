
// ─── Configuration ──────────────────────────────────────────────
const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1dd2sVgDAHPITFcE83QGP00eTNs8qiv1pFT3PmJaNikI/edit';
const PASSWORD_KEY='***';
const DEFAULT_PASSWORD='***';

// ─── State ──────────────────────────────────────────────────────
let state = { authenticated: false, data: null, tab: 'dashboard' };

// ─── Router ─────────────────────────────────────────────────────
function navigate(tab) {
  state.tab = tab;
  render();
}

// ─── Auth ────────────────────────────────────────────────────────
function checkAuth() {
  const stored = sessionStorage.getItem(PASSWORD_KEY);
  if (stored === DEFAULT_PASSWORD) {
    state.authenticated = true;
    return true;
  }
  return false;
}

function login(password) {
  if (password === DEFAULT_PASSWORD) {
    sessionStorage.setItem(PASSWORD_KEY, password);
    state.authenticated = true;
    render();
    return true;
  }
  return false;
}

function logout() {
  sessionStorage.removeItem(PASSWORD_KEY);
  state.authenticated = false;
  render();
}

// ─── Login handler (separado para evitar closures rotas) ───────
function handleLoginAttempt() {
  const input = document.getElementById('login-pwd');
  const errorEl = document.getElementById('login-error');
  if (!input) return;
  const pwd = input.value;
  if (login(pwd)) {
    // success — render() ya se llamó desde login()
  } else {
    if (errorEl) errorEl.textContent = 'Contraseña incorrecta';
    input.value = '';
    input.focus();
  }
}

// Se registra cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
  const app = document.getElementById('app');
  if (!app) return;
  // Escuchar Enter en el input de login (delegación)
  app.addEventListener('keydown', function(e) {
    if (e.target && e.target.id === 'login-pwd' && e.key === 'Enter') {
      handleLoginAttempt();
    }
  });
  // Escuchar clicks en el botón de login (delegación)
  app.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'login-btn') {
      handleLoginAttempt();
    }
  });
});

// ─── Data loading ────────────────────────────────────────────────
async function loadData() {
  try {
    const resp = await fetch('cms_data.json?_t=' + Date.now());
    if (!resp.ok) throw new Error('HTTP ' + resp.status);
    state.data = await resp.json();
  } catch(e) {
    console.warn('Could not load cms_data.json:', e);
    state.data = null;
  }
  render();
}

// ─── Formatters ─────────────────────────────────────────────────
function esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate() {
  return new Date().toLocaleString('es-AR', { timeZone: 'America/Argentina/San_Juan' });
}

// ─── Renderers ──────────────────────────────────────────────────

function renderLogin() {
  document.getElementById('app').innerHTML = `
    <div class="login-box fade-in">
      <div class="card text-center" style="padding:32px">
        <div style="font-size:32px;margin-bottom:8px">▲</div>
        <h2 style="font-size:20px;font-weight:700;margin-bottom:4px">Admin CMS</h2>
        <p style="font-size:13px;color:#64748b;margin-bottom:24px">Rancho Raíz · Panel de gestión</p>
        <input id="login-pwd" type="password" placeholder="Contraseña" 
               style="margin-bottom:12px;text-align:center">
        <p id="login-error" style="color:#ef4444;font-size:13px;margin-bottom:12px;min-height:20px"></p>
        <button id="login-btn" class="btn-gold" style="width:100%">Entrar</button>
        <p style="font-size:11px;color:#475569;margin-top:16px">Solo para el equipo de Rancho Raíz</p>
      </div>
    </div>
  `;
  const input = document.getElementById('login-pwd');
  if (input) input.focus();
}

function renderSidebar() {
  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
    { id: 'habitaciones', label: '🛏️ Habitaciones', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
    { id: 'servicios', label: '✨ Servicios', icon: 'M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z' },
    { id: 'galeria', label: '🖼️ Galería', icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
    { id: 'promociones', label: '🔥 Promociones', icon: 'M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7' },
    { id: 'config', label: '⚙️ Config', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z },
  ];
  
  return `
    <aside style="width:240px;background:var(--dark-2);border-right:1px solid #1e293b;min-height:100vh;padding:16px;display:flex;flex-direction:column">
      <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;margin-bottom:24px">
        <span style="font-size:20px">▲</span>
        <div>
          <div style="font-weight:700;font-size:15px">Rancho Raíz</div>
          <div style="font-size:11px;color:#64748b">Panel CMS</div>
        </div>
      </div>
      <nav style="flex:1;display:flex;flex-direction:column;gap:2px">
        ${tabs.map(t => `
          <button onclick="navigate('${t.id}')" 
                  style="display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;border:none;background:${state.tab === t.id ? 'rgba(197,160,89,0.15)' : 'transparent'};color:${state.tab === t.id ? '#C5A059' : '#94a3b8'};cursor:pointer;font-size:14px;text-align:left;transition:all 0.2s;width:100%"
                  onmouseover="this.style.background='rgba(197,160,89,0.1)'" onmouseout="this.style.background='${state.tab === t.id ? 'rgba(197,160,89,0.15)' : 'transparent'}'">
            <span>${t.label}</span>
          </button>
        `).join('')}
      </nav>
      <div style="padding:12px;border-top:1px solid #1e293b;margin-top:auto">
        <button onclick="logout()" class="btn-outline" style="width:100%;font-size:13px;padding:8px">Cerrar sesión</button>
      </div>
    </aside>
  `;
}

function renderDashboard() {
  const d = state.data;
  if (!d) return '<div class="p-8"><p class="text-slate-400">No hay datos cargados. Esperá la próxima actualización automática.</p></div>';
  
  const habitaciones = (d.habitaciones || []).filter(h => h.activo === 'SI').length;
  const servicios = (d.servicios || []).filter(s => s.activo === 'SI').length;
  const galeria = (d.galeria || []).filter(g => g.activo === 'SI' && g.imagen_url).length;
  const cfg = d.config || {};
  
  return `
    <div class="p-8 fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px">
        <div>
          <h1 style="font-size:24px;font-weight:700">Dashboard</h1>
          <p style="font-size:13px;color:#64748b">Estado actual del sitio web</p>
        </div>
        <div style="font-size:12px;color:#475569">Actualizado: ${formatDate()}</div>
      </div>
      
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px">
        <div class="card">
          <div style="font-size:13px;color:#64748b;margin-bottom:4px">Habitaciones activas</div>
          <div style="font-size:32px;font-weight:700;color:#C5A059">${habitaciones}</div>
        </div>
        <div class="card">
          <div style="font-size:13px;color:#64748b;margin-bottom:4px">Servicios activos</div>
          <div style="font-size:32px;font-weight:700;color:#C5A059">${servicios}</div>
        </div>
        <div class="card">
          <div style="font-size:13px;color:#64748b;margin-bottom:4px">Fotos en galería</div>
          <div style="font-size:32px;font-weight:700;color:#C5A059">${galeria}</div>
        </div>
        <div class="card">
          <div style="font-size:13px;color:#64748b;margin-bottom:4px">WhatsApp</div>
          <div style="font-size:16px;font-weight:600;color:#C5A059">${cfg.whatsapp || '—'}</div>
        </div>
      </div>
      
      <div class="card" style="margin-bottom:16px">
        <h3 style="font-weight:600;margin-bottom:12px">📋 Cómo actualizar el sitio</h3>
        <ol style="color:#94a3b8;font-size:14px;line-height:2;padding-left:20px">
          <li>Abrí la <a href="${SHEET_URL}" target="_blank" style="color:#C5A059;text-decoration:underline">Planilla de Google Sheets</a></li>
          <li>Editá los datos que quieras cambiar (precios, fotos, descripciones)</li>
          <li>La web se actualiza <strong>automáticamente cada 30 minutos</strong></li>
          <li>Si querés actualizar ya mismo, tocá "Actualizar ahora" abajo</li>
        </ol>
      </div>
      
      <div style="display:flex;gap:12px">
        <a href="${SHEET_URL}" target="_blank" class="btn-gold">✏️ Editar en Google Sheets</a>
        <a href="../index.html" target="_blank" class="btn-outline">👁️ Ver sitio web</a>
      </div>
    </div>
  `;
}

function renderHabitaciones() {
  const items = state.data?.habitaciones || [];
  const rows = items.map((h, i) => `
    <tr>
      <td style="font-weight:500">${esc(h.nombre)}</td>
      <td>$${esc(h.precio)}</td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:#94a3b8">${esc(h.descripcion)}</td>
      <td><span class="badge ${h.activo === 'SI' ? 'badge-active' : 'badge-inactive'}">${h.activo === 'SI' ? 'Activa' : 'Inactiva'}</span></td>
    </tr>
  `).join('');
  
  return `
    <div class="p-8 fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <h1 style="font-size:24px;font-weight:700">🛏️ Habitaciones</h1>
          <p style="font-size:13px;color:#64748b">${items.length} habitaciones cargadas</p>
        </div>
        <a href="${SHEET_URL}" target="_blank" class="btn-gold" style="font-size:13px;padding:8px 16px">Editar en Sheets</a>
      </div>
      <div class="card" style="padding:0;overflow:auto">
        <table>
          <thead>
            <tr><th>Nombre</th><th>Precio</th><th>Descripción</th><th>Estado</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function renderServicios() {
  const items = state.data?.servicios || [];
  const rows = items.map(s => `
    <tr>
      <td style="font-weight:500">${esc(s.nombre)}</td>
      <td style="max-width:350px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:#94a3b8">${esc(s.descripcion)}</td>
      <td><span class="badge ${s.activo === 'SI' ? 'badge-active' : 'badge-inactive'}">${s.activo === 'SI' ? 'Activo' : 'Inactivo'}</span></td>
    </tr>
  `).join('');
  
  return `
    <div class="p-8 fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <h1 style="font-size:24px;font-weight:700">✨ Servicios</h1>
          <p style="font-size:13px;color:#64748b">${items.length} servicios cargados</p>
        </div>
        <a href="${SHEET_URL}" target="_blank" class="btn-gold" style="font-size:13px;padding:8px 16px">Editar en Sheets</a>
      </div>
      <div class="card" style="padding:0;overflow:auto">
        <table>
          <thead><tr><th>Nombre</th><th>Descripción</th><th>Estado</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function renderGaleria() {
  const items = state.data?.galeria || [];
  const rows = items.map(g => `
    <tr>
      <td style="max-width:250px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;color:#64748b">${esc(g.imagen_url) || '—'}</td>
      <td style="font-size:13px">${esc(g.descripcion) || '—'}</td>
      <td><span class="badge ${g.activo === 'SI' ? 'badge-active' : 'badge-inactive'}">${g.activo === 'SI' ? 'Activo' : 'Inactivo'}</span></td>
    </tr>
  `).join('');
  
  return `
    <div class="p-8 fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <h1 style="font-size:24px;font-weight:700">🖼️ Galería</h1>
          <p style="font-size:13px;color:#64748b">${items.length} imágenes cargadas</p>
        </div>
        <a href="${SHEET_URL}" target="_blank" class="btn-gold" style="font-size:13px;padding:8px 16px">Editar en Sheets</a>
      </div>
      <div class="card" style="padding:0;overflow:auto">
        <table>
          <thead><tr><th>URL de imagen</th><th>Descripción</th><th>Estado</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function renderPromociones() {
  const items = state.data?.promociones || [];
  const rows = items.map(p => `
    <tr>
      <td style="font-weight:500">${esc(p.nombre)}</td>
      <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13px;color:#94a3b8">${esc(p.descripcion)}</td>
      <td>${p.precio_regular ? '$' + esc(p.precio_regular) : '—'}</td>
      <td style="color:#22c55e;font-weight:600">${p.precio_promo ? '$' + esc(p.precio_promo) : '—'}</td>
      <td><span class="badge ${p.activo === 'SI' ? 'badge-active' : 'badge-inactive'}">${p.activo === 'SI' ? 'Activa' : 'Inactiva'}</span></td>
    </tr>
  `).join('');

  return `
    <div class="p-8 fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <h1 style="font-size:24px;font-weight:700">🔥 Promociones</h1>
          <p style="font-size:13px;color:#64748b">${items.length} promociones cargadas</p>
        </div>
        <a href="${SHEET_URL}" target="_blank" class="btn-gold" style="font-size:13px;padding:8px 16px">Editar en Sheets</a>
      </div>
      <div class="card" style="padding:0;overflow:auto">
        <table>
          <thead><tr><th>Nombre</th><th>Descripción</th><th>Precio regular</th><th>Precio promo</th><th>Estado</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function renderConfig() {
  const cfg = state.data?.config || {};
  const entries = Object.entries(cfg).map(([k, v]) => `
    <tr>
      <td style="font-weight:500">${esc(k)}</td>
      <td style="color:#94a3b8">${esc(v)}</td>
    </tr>
  `).join('');
  
  return `
    <div class="p-8 fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
        <div>
          <h1 style="font-size:24px;font-weight:700">⚙️ Configuración</h1>
          <p style="font-size:13px;color:#64748b">Datos de contacto y configuración general</p>
        </div>
        <a href="${SHEET_URL}" target="_blank" class="btn-gold" style="font-size:13px;padding:8px 16px">Editar en Sheets</a>
      </div>
      <div class="card" style="padding:0;overflow:auto">
        <table>
          <thead><tr><th>Clave</th><th>Valor</th></tr></thead>
          <tbody>${entries}</tbody>
        </table>
      </div>
    </div>
  `;
}

// ─── Main render ─────────────────────────────────────────────────
function render() {
  if (!state.authenticated) {
    renderLogin();
    return;
  }
  
  const content = (() => {
    switch(state.tab) {
      case 'dashboard': return renderDashboard();
      case 'habitaciones': return renderHabitaciones();
      case 'servicios': return renderServicios();
      case 'galeria': return renderGaleria();
      case 'promociones': return renderPromociones();
      case 'config': return renderConfig();
      default: return renderDashboard();
    }
  })();
  
  document.getElementById('app').innerHTML = `
    <div style="display:flex">
      ${renderSidebar()}
      <main style="flex:1;overflow-y:auto;max-height:100vh">
        ${content}
      </main>
    </div>
  `;
}

// ─── Init ────────────────────────────────────────────────────────
(function init() {
  if (checkAuth()) {
    loadData();
  } else {
    render();
  }
})();

