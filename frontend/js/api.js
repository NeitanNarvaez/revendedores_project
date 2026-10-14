// Same-origin by default: FastAPI serves this frontend under /app/.
const API_BASE = window.API_BASE || '/api';
const session = {
  token: () => sessionStorage.getItem('revendedores_token'),
  save: token => sessionStorage.setItem('revendedores_token', token),
  clear: () => sessionStorage.removeItem('revendedores_token')
};
async function api(path, method = 'GET', data) {
  const headers = {'Content-Type': 'application/json'};
  if (session.token()) headers.Authorization = `Bearer ${session.token()}`;
  let response;
  try {
    response = await fetch(API_BASE + path, {method, headers, body: data === undefined ? undefined : JSON.stringify(data)});
  } catch (_) { throw new Error('No se pudo conectar con el servidor. Comprueba que la API esté en ejecución.'); }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/auth/login')) {
      session.clear(); location.href = 'login.html';
    }
    const detail = body.detail;
    const message = Array.isArray(detail) ? detail.map(e => `${e.loc.slice(1).join('.')}: ${e.msg}`).join(' · ') : detail;
    throw new Error(typeof message === 'string' ? message : 'No fue posible completar la solicitud.');
  }
  return body;
}
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function money(value) {
  return new Intl.NumberFormat('es-CO', {style: 'currency', currency: 'COP', maximumFractionDigits: 2}).format(Number(value || 0));
}
