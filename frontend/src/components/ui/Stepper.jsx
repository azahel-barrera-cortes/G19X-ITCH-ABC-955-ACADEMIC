/** Indicador de avance del formulario por pasos. */
export default function Stepper({ pasos, pasoActual, completados = [], onSeleccionar = null }) {
  return (
    <ol className="flex flex-wrap gap-2" aria-label="Pasos del formulario">
      {pasos.map((paso) => {
        const activo = paso.id === pasoActual
        const completado = completados.includes(paso.id)
        const clase = activo
          ? 'border-corporativo-500 bg-corporativo-50 text-corporativo-700'
          : completado
            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
            : 'border-slate-200 bg-white text-slate-500'

        return (
          <li key={paso.id} className="flex-1 min-w-[190px]">
            <button
              type="button"
              onClick={() => (onSeleccionar ? onSeleccionar(paso.id) : undefined)}
              disabled={!onSeleccionar}
              className={`h-full w-full rounded-xl border px-3 py-2 text-left transition ${clase} ${
                onSeleccionar ? 'hover:border-corporativo-400' : 'cursor-default'
              }`}
              aria-current={activo ? 'step' : undefined}
            >
              <span className="flex items-center gap-2">
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold ${
                    activo || completado ? 'bg-corporativo-500 text-white' : 'bg-slate-200 text-slate-600'
                  }`}
                >
                  {completado && !activo ? '✓' : paso.id}
                </span>
                <span className="text-xs font-semibold uppercase tracking-wide">{paso.titulo}</span>
              </span>
              <span className="mt-1 block text-[11px] leading-tight text-slate-500">{paso.descripcion}</span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
