/**
 * Cliente API de autenticación para PGAC.
 *
 * Todas las funciones devuelven promesas que resuelven con el JSON de respuesta
 * o rechazan con un objeto con mensaje legible.
 */
const BASE = import.meta.env.VITE_API_URL || ''

async function peticion(path, { method = 'GET', headers = {}, body, token } = {}) {
  const cabeceras = { 'Content-Type': 'application/json', ...headers }
  if (token) cabeceras.Authorization = `Bearer ${token}`
  const respuesta = await fetch(`${BASE}/api/v1${path}`, {
    method,
    headers: cabeceras,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!respuesta.ok) {
    const texto = await respuesta.text()
    let detalle
    try {
      detalle = JSON.parse(texto).detail
    } catch {
      detalle = texto
    }
    throw new Error(detalle || `Error HTTP ${respuesta.status}`)
  }
  return respuesta.json()
}

/* ── Registro / Login ─────────────────────────────────────────────── */
export async function registrar({ email, nombre_completo, rol, password }) {
  return peticion('/auth/registro', { method: 'POST', body: { email, nombre_completo, rol, password } })
}

export async function iniciarSesion({ email, password }) {
  return peticion('/auth/login', { method: 'POST', body: { email, password } })
}

/* ── Perfil ─────────────────────────────────────────────────────────── */
export async function obtenerPerfil(token) {
  return peticion('/auth/me', { token })
}

export async function actualizarPerfil(token, cambios) {
  return peticion('/auth/me', { method: 'PUT', token, body: cambios })
}

/* ── Contraseñas ────────────────────────────────────────────────────── */
export async function cambiarPassword(token, nuevo_password) {
  return peticion('/auth/me', { method: 'PUT', token, body: { password: nuevo_password } })
}

export async function solicitarResetPassword(email) {
  return peticion('/auth/reset-password', { method: 'POST', body: { email } })
}

export async function confirmarResetPassword({ token, nuevo_password }) {
  return peticion('/auth/reset-password/confirm', {
    method: 'POST',
    body: { token, nuevo_password },
  })
}
