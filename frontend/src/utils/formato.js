/**
 * Utilidades de formato (es-MX) compartidas por toda la interfaz.
 * Mantienen la misma presentación que el PDF generado por el backend.
 */

const MESES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

/** Convierte un valor ISO (fecha u hora) en objeto Date sin desfase de zona. */
function comoFecha(valor) {
  if (!valor) return null
  if (valor instanceof Date) return valor
  const texto = String(valor)
  const fecha = texto.length <= 10 ? new Date(`${texto}T12:00:00`) : new Date(texto)
  return Number.isNaN(fecha.getTime()) ? null : fecha
}

/** ``15 de marzo de 2026``. */
export function fechaLarga(valor) {
  const fecha = comoFecha(valor)
  if (!fecha) return '—'
  return `${String(fecha.getDate()).padStart(2, '0')} de ${MESES[fecha.getMonth()]} de ${fecha.getFullYear()}`
}

/** ``15/03/2026``. */
export function fechaCorta(valor) {
  const fecha = comoFecha(valor)
  if (!fecha) return '—'
  const dia = String(fecha.getDate()).padStart(2, '0')
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  return `${dia}/${mes}/${fecha.getFullYear()}`
}

/** ``10:30 h``. */
export function horaCorta(valor) {
  if (!valor) return '—'
  return `${String(valor).slice(0, 5)} h`
}

/** ``$100,000.00``. */
export function moneda(valor) {
  const numero = Number(valor)
  if (!Number.isFinite(numero)) return '—'
  return numero.toLocaleString('es-MX', {
    style: 'currency',
    currency: 'MXN',
    minimumFractionDigits: 2,
  })
}

/** ``80,000`` (o ``80,000.5`` si hay decimales). */
export function numero(valor, decimales = 0) {
  const numeroConvertido = Number(valor)
  if (!Number.isFinite(numeroConvertido)) return '—'
  return numeroConvertido.toLocaleString('es-MX', {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  })
}

/** ``80.00%``. */
export function porcentaje(valor, decimales = 2) {
  const numeroConvertido = Number(valor)
  if (!Number.isFinite(numeroConvertido)) return '—'
  return `${numeroConvertido.toFixed(decimales)}%`
}

/** ``27/09/2026 19:28``. */
export function marcaTiempo(valor) {
  const fecha = valor ? new Date(valor) : new Date()
  if (Number.isNaN(fecha.getTime())) return '—'
  const dia = String(fecha.getDate()).padStart(2, '0')
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const horas = String(fecha.getHours()).padStart(2, '0')
  const minutos = String(fecha.getMinutes()).padStart(2, '0')
  return `${dia}/${mes}/${fecha.getFullYear()} ${horas}:${minutos}`
}

/** Clases de color para las etiquetas de estatus del acta. */
export function claseEstatus(estatus) {
  switch (estatus) {
    case 'aprobada':
      return 'bg-emerald-50 text-emerald-700 ring-emerald-200'
    case 'firmada':
      return 'bg-corporativo-100 text-corporativo-700 ring-corporativo-200'
    case 'en_revision':
      return 'bg-amber-50 text-amber-700 ring-amber-200'
    case 'archivada':
      return 'bg-slate-100 text-slate-600 ring-slate-200'
    default:
      return 'bg-slate-50 text-slate-600 ring-slate-200'
  }
}

/** Clases de color para la severidad de un hallazgo de validación. */
export function claseSeveridad(severidad) {
  switch (severidad) {
    case 'critico':
      return 'bg-red-50 text-red-700 ring-red-200'
    case 'advertencia':
      return 'bg-amber-50 text-amber-800 ring-amber-200'
    default:
      return 'bg-corporativo-50 text-corporativo-600 ring-corporativo-200'
  }
}

/** Etiqueta legible y tono para una clasificación de vigencia. */
export function vigencia(estado, dias) {
  switch (estado) {
    case 'vencida':
      return { texto: 'Vencida', tono: 'error', detalle: `Venció hace ${Math.abs(dias)} día(s)` }
    case 'por_vencer':
      return { texto: 'Por vencer', tono: 'advertencia', detalle: `Vence en ${dias} día(s)` }
    case 'vigente':
      return { texto: 'Vigente', tono: 'exito', detalle: `Vence en ${dias} día(s)` }
    case 'sin_fecha':
    default:
      return { texto: 'Sin caducidad', tono: 'neutral', detalle: 'Sin plazo declarado' }
  }
}
