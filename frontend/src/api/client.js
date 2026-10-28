/**
 * Cliente HTTP de PGAC (Página de Gestión de Actas Corporativas).
 *
 * Centraliza todas las llamadas al backend de FastAPI. Las respuestas binarias
 * (PDF) se solicitan con `responseType: 'blob'` para descargarlas directamente
 * en el navegador sin pasarlas por JSON.
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const CLAVE_TOKEN = 'pgac_token'

export const http = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // la redacción con IA puede tardar: 2 minutos de margen
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Adjunta el JWT de la sesión a todas las llamadas protegidas por el RBAC del
 * backend. El token lo guarda `AuthContext` en localStorage al iniciar sesión;
 * sin sesión las peticiones salen anónimas y el backend responde 401.
 */
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(CLAVE_TOKEN)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/**
 * Normaliza los errores de la API a un mensaje legible para el usuario.
 *
 * Caso especial: cuando la petición usa `responseType: 'blob'` (descarga del PDF),
 * axios entrega **también el error como Blob**. Sin desempaquetarlo, `data.detail`
 * es `undefined` y el usuario vería un error genérico sin saber qué corregir.
 */
export function mensajeDeError(error) {
  const datos = error?.response?.data
  // El cuerpo de un error puede llegar como Blob (JSON serializado dentro).
  if (datos instanceof Blob) {
    return (
      datos
        .text()
        .then((texto) => {
          try {
            return leerDetalle(JSON.parse(texto))
          } catch {
            return texto || 'El servidor rechazó la solicitud.'
          }
        })
        // `mensajeDeError` es síncrono para el resto de callers: se degrada con un
        // mensaje útil en lugar de romper el flujo.
        .catch(() => 'El servidor rechazó la solicitud.')
    )
  }
  return leerDetalle(datos) || error?.message || 'Ocurrió un error inesperado.'
}

/** Extrae el mensaje y los campos señalados de un cuerpo de error de FastAPI. */
function leerDetalle(datos) {
  if (!datos) return ''
  const { detail, detalle, errores } = datos
  const campos = Array.isArray(errores)
    ? ` (${errores.map((item) => `${item.campo}: ${item.mensaje}`).join('; ')})`
    : ''

  // 422 de FastAPI: `detail` es una lista de errores por campo.
  if (Array.isArray(detail)) {
    const mensajes = detail
      .map((item) => {
        if (typeof item === 'string') return item
        const campo = item?.loc?.filter((parte) => parte !== 'body').join('.')
        return campo ? `${campo}: ${item.msg}` : item?.msg
      })
      .filter(Boolean)
    return mensajes.length ? `Corrige los datos del formulario (${mensajes.join('; ')}).` : ''
  }

  return `${detail || ''}${detalle ? ` ${detalle}` : ''}${campos}`.trim()
}

/** Catálogos del formulario (tipos de asamblea, mayorías, caracteres y estatus). */
export async function obtenerCatalogos() {
  const { data } = await http.get('/actas/catalogos')
  return data
}

/** Genera el borrador del acta con IA y devuelve cláusulas + validación (JSON). */
export async function redactarActa(payload) {
  const { data } = await http.post('/actas/redactar', payload)
  return data
}

/**
 * Redacta un acuerdo en vivo contra el endpoint SSE `/actas/redactar-stream`.
 *
 * `EventSource` sólo admite GET, así que se usa `fetch` con lectura por flujo y se
 * interpreta el protocolo SSE a mano. `alFragmento` recibe cada trozo de texto a
 * medida que llega, lo que permite mostrar la redacción mientras se genera.
 *
 * @returns el texto completo de la cláusula generada.
 */
export async function redactarEnVivo(payload, { alFragmento, alInicio } = {}) {
  const token = localStorage.getItem(CLAVE_TOKEN)
  const respuesta = await fetch(`${BASE_URL}/actas/redactar-stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
  })

  if (!respuesta.ok || !respuesta.body) {
    throw new Error(`El servidor respondió con el código ${respuesta.status}.`)
  }

  const lector = respuesta.body.getReader()
  const decodificador = new TextDecoder('utf-8')
  let buffer = ''
  let acumulado = ''

  const procesar = (bloque) => {
    // Los eventos SSE van separados por una línea en blanco.
    for (const crudo of bloque.split('\n\n')) {
      const lineas = crudo.split('\n')
      const lineaEvento = lineas.find((linea) => linea.startsWith('event:'))
      const lineaDatos = lineas.find((linea) => linea.startsWith('data:'))
      if (!lineaEvento || !lineaDatos) continue

      const evento = lineaEvento.slice(6).trim()
      let datos = {}
      try {
        datos = JSON.parse(lineaDatos.slice(5).trim())
      } catch {
        continue
      }

      if (evento === 'inicio') {
        alInicio?.(datos)
      } else if (evento === 'fragmento') {
        acumulado += datos.texto || ''
        alFragmento?.(datos.texto || '', acumulado)
      } else if (evento === 'error') {
        throw new Error(datos.mensaje || 'No se pudo generar la cláusula.')
      }
    }
  }

  for (;;) {
    const { done, value } = await lector.read()
    if (done) break
    buffer += decodificador.decode(value, { stream: true })
    const partes = buffer.split('\n\n')
    // El último fragmento puede estar incompleto: se conserva en el buffer.
    buffer = partes.pop() ?? ''
    partes.forEach(procesar)
  }
  if (buffer.trim()) procesar(buffer)

  return { texto: acumulado.trim() }
}

/** Redacta, persiste y devuelve el PDF binario con sus metadatos (encabezados). */
export async function generarPdf(payload) {
  const respuesta = await http.post('/actas/generar-pdf', payload, { responseType: 'blob' })
  return {
    blob: respuesta.data,
    nombreArchivo: nombreDesdeCabeceras(respuesta.headers) || `acta_${Date.now()}.pdf`,
    folio: respuesta.headers['x-acta-folio'] || '',
    id: respuesta.headers['x-acta-id'] || '',
    version: respuesta.headers['x-acta-version'] || '1',
    paginas: respuesta.headers['x-acta-paginas'] || '',
    guardada: respuesta.headers['x-acta-guardada'] === 'true',
    proveedorIa: respuesta.headers['x-ia-proveedor'] || 'plantillas',
    iaHabilitada: respuesta.headers['x-ia-habilitada'] === 'true',
    puntajeValidacion: respuesta.headers['x-validacion-puntaje'] || '',
    advertencias: respuesta.headers['x-ia-advertencias'] || '',
  }
}

/** Descarga un PDF ya almacenado (regenerado en el servidor). */
export async function descargarPdfGuardado(actaId, opciones = {}) {
  const respuesta = await http.get(`/actas/${actaId}/pdf`, {
    responseType: 'blob',
    params: {
      incluir_tabla_asistentes: opciones.incluirTablaAsistentes ?? true,
      incluir_hoja_firmas: opciones.incluirHojaFirmas ?? true,
      incluir_anexo_validacion: opciones.incluirAnexoValidacion ?? false,
    },
  })
  const disposicion = respuesta.headers['content-disposition'] || ''
  const coincidencia = /filename\*=UTF-8''([^;]+)/i.exec(disposicion)
  return {
    blob: respuesta.data,
    nombreArchivo: coincidencia ? decodeURIComponent(coincidencia[1]) : `acta_${actaId}.pdf`,
  }
}

/** Crea y guarda un acta en el historial. */
export async function crearActa(payload) {
  const { data } = await http.post('/actas', payload)
  return data
}

/** Lista el historial de actas con filtros opcionales. */
export async function listarActas(filtros = {}) {
  const { data } = await http.get('/actas', { params: filtros })
  return data
}

/** Obtiene una acta completa por su identificador. */
export async function obtenerActa(actaId) {
  const { data } = await http.get(`/actas/${actaId}`)
  return data
}

/** Reemplaza el contenido de un acta almacenada. */
export async function actualizarActa(actaId, payload) {
  const { data } = await http.put(`/actas/${actaId}`, payload)
  return data
}

/** Cambia el estatus del acta dentro de su ciclo de vida. */
export async function cambiarEstatus(actaId, estatus) {
  const { data } = await http.patch(`/actas/${actaId}/estatus`, null, { params: { estatus } })
  return data
}

/** Vuelve a validar la consistencia de un acta almacenada. */
export async function validarActaGuardada(actaId) {
  const { data } = await http.post(`/actas/${actaId}/validar`)
  return data
}

/** Elimina un acta del historial. */
export async function eliminarActa(actaId) {
  const { data } = await http.delete(`/actas/${actaId}`)
  return data
}

/** Estado del backend (base de datos y proveedor de IA). */
export async function consultarEstado() {
  const { data } = await http.get('/sistema/estado')
  return data
}

// ---------------------------------------------------------------------------
// Administración de actas: versiones, caducidad y estadísticas
// ---------------------------------------------------------------------------

/** Estadísticas globales del repositorio (totales, estatus y vigencia). */
export async function obtenerResumenAdministracion() {
  const { data } = await http.get('/administracion/resumen')
  return data
}

/** Actas clasificadas por vigencia; `estado` filtra (vencida, por_vencer, ...). */
export async function obtenerActasPorVigencia({ estado = '', limite = 100 } = {}) {
  const { data } = await http.get('/administracion/vigencia', {
    params: { estado: estado || undefined, limite },
  })
  return data
}

/** Historial de versiones de un acta (más reciente primero). */
export async function obtenerVersiones(actaId) {
  const { data } = await http.get(`/administracion/versiones/${actaId}`)
  return data
}

/** Contenido completo de una versión concreta (instantánea del acta). */
export async function obtenerVersion(actaId, numero) {
  const { data } = await http.get(`/administracion/versiones/${actaId}/${numero}`)
  return data
}

/** Restaura una versión anterior; el backend emite una versión nueva. */
export async function restaurarVersion(actaId, numero) {
  const { data } = await http.post(`/administracion/versiones/${actaId}/${numero}/restaurar`)
  return data
}

/** Fija, amplia o quita la fecha de caducidad de un acta. */
export async function fijarCaducidad(actaId, { fechaCaducidad = null, motivo = '' } = {}) {
  const { data } = await http.put(`/administracion/caducidad/${actaId}`, {
    fecha_caducidad: fechaCaducidad || null,
    motivo: motivo || null,
  })
  return data
}

/** Conversa con el Asistente IA interno de actas (solo temas de actas). */
export async function chatearAsistente(mensaje, { folio = null, actaId = null, sesionId = null, autor = null } = {}) {
  const { data } = await http.post('/asistente/chat', {
    mensaje,
    folio: folio || undefined,
    acta_id: actaId || undefined,
    sesion_id: sesionId || undefined,
    autor: autor || undefined,
  })
  return data
}

/** Capacidades y ejemplos del asistente. */
export async function obtenerAyudaAsistente() {
  const { data } = await http.get('/asistente/ayuda')
  return data
}

/** Descarga un Blob como archivo en el navegador. */
export function descargarBlob(blob, nombreArchivo = 'acta.pdf') {
  const url = window.URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  window.URL.revokeObjectURL(url)
}

/** Extrae el nombre del archivo desde el encabezado Content-Disposition. */
function nombreDesdeCabeceras(headers) {
  const disposicion = headers?.['content-disposition'] || ''
  const coincidencia = /filename\*=UTF-8''([^;]+)/i.exec(disposicion)
  if (coincidencia) return decodeURIComponent(coincidencia[1])
  const simple = /filename="([^"]+)"/i.exec(disposicion)
  return simple ? simple[1] : ''
}
