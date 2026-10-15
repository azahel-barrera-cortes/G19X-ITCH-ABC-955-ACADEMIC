/**
 * Utilidades de archivos: descarga de blobs y presentación de tamaños.
 */

/** Fuerza la descarga de un blob en el navegador con el nombre indicado. */
export function descargarBlob(blob, nombreArchivo = 'acta.pdf') {
  const url = window.URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreArchivo
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  // Se libera el objeto URL en el siguiente ciclo para no interrumpir la descarga.
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1500)
}

/** Abre el PDF en una pestaña nueva (vista previa del navegador). */
export function abrirBlob(blob) {
  const url = window.URL.createObjectURL(blob)
  window.open(url, '_blank', 'noopener,noreferrer')
  window.setTimeout(() => window.URL.revokeObjectURL(url), 60000)
}

/** ``1.2 MB``. */
export function formatearBytes(bytes) {
  const valor = Number(bytes)
  if (!Number.isFinite(valor) || valor <= 0) return '—'
  const unidades = ['B', 'KB', 'MB', 'GB']
  const indice = Math.min(Math.floor(Math.log(valor) / Math.log(1024)), unidades.length - 1)
  const cantidad = valor / 1024 ** indice
  return `${cantidad.toFixed(indice === 0 ? 0 : 1)} ${unidades[indice]}`
}

/** Copia texto al portapapeles (con degradación elegante). */
export async function copiarAlPortapapeles(texto) {
  try {
    await navigator.clipboard.writeText(texto)
    return true
  } catch {
    return false
  }
}
