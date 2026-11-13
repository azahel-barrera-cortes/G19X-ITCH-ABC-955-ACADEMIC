export const normalizarTexto = (valor) =>
  String(valor ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()

export const formatearAccion = (accion) =>
  String(accion || 'Actividad')
    .replace(/[_.-]+/g, ' ')
    .replace(/^./, (letra) => letra.toUpperCase())

export const tonoDeAccion = (accion) => {
  const normalizada = normalizarTexto(accion)
  if (normalizada.includes('eliminar') || normalizada.includes('devolver')) return 'error'
  if (normalizada.includes('crear') || normalizada.includes('aprobar') || normalizada.includes('firmar')) {
    return 'exito'
  }
  if (normalizada.includes('actualizar') || normalizada.includes('restaurar') || normalizada.includes('reenviar')) {
    return 'advertencia'
  }
  return 'info'
}
