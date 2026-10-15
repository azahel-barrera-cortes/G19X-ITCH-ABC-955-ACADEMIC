/** Mensaje contextual (información, éxito, advertencia o error). */
const TONOS = {
  info: { caja: 'border-corporativo-200 bg-corporativo-50', titulo: 'text-corporativo-700' },
  exito: { caja: 'border-emerald-200 bg-emerald-50', titulo: 'text-emerald-700' },
  advertencia: { caja: 'border-amber-200 bg-amber-50', titulo: 'text-amber-800' },
  error: { caja: 'border-red-200 bg-red-50', titulo: 'text-red-700' },
}

export default function Alerta({ tono = 'info', titulo = null, acciones = null, className = '', children }) {
  const estilo = TONOS[tono] || TONOS.info
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${estilo.caja} ${className}`} role="status">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          {titulo ? <p className={`font-semibold ${estilo.titulo}`}>{titulo}</p> : null}
          {children ? <div className="mt-1 text-slate-700">{children}</div> : null}
        </div>
        {acciones}
      </div>
    </div>
  )
}
