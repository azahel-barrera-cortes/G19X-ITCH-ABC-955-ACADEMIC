import Etiqueta from '../ui/Etiqueta.jsx'
import { claseSeveridad, porcentaje as formatearPorcentaje } from '../../utils/formato.js'

/** Traduce la severidad del backend a un tono visual. */
function tonoSeveridad(severidad) {
  if (severidad === 'critico') return 'error'
  if (severidad === 'advertencia') return 'advertencia'
  return 'info'
}

/**
 * Panel de la validación de consistencia: puntaje, hallazgos y recomendaciones.
 * El puntaje se calcula en el backend (reglas deterministas + IA cuando está
 * configurada), de modo que el usuario siempre recibe un resultado.
 */
export default function PanelValidacion({ validacion, onRevalidar = null, cargando = false }) {
  if (!validacion) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
        Aún no se ha ejecutado la validación de consistencia.
      </div>
    )
  }

  const puntaje = Number(validacion.puntaje) || 0
  const colorBarra = puntaje >= 90 ? 'bg-emerald-500' : puntaje >= 70 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-corporativo-700">{formatearPorcentaje(puntaje, 2)}</span>
          <div>
            <p className="text-sm font-semibold text-slate-700">Consistencia documental</p>
            <p className="text-xs text-slate-500">
              Proveedor: {validacion.proveedor} · {validacion.generado_por_ia ? 'validado con IA' : 'reglas locales'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Etiqueta tono={puntaje >= 90 ? 'exito' : puntaje >= 70 ? 'advertencia' : 'error'}>
            {puntaje >= 90 ? 'Apto para firma' : puntaje >= 70 ? 'Requiere ajustes' : 'No recomendado'}
          </Etiqueta>
          {onRevalidar ? (
            <button
              type="button"
              onClick={onRevalidar}
              disabled={cargando}
              className="rounded-lg px-3 py-1.5 text-xs font-semibold text-corporativo-600 ring-1 ring-inset ring-corporativo-200 transition hover:bg-corporativo-50 disabled:opacity-60"
            >
              {cargando ? 'Validando…' : 'Volver a validar'}
            </button>
          ) : null}
        </div>
      </div>

      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
        <div className={`h-2 ${colorBarra}`} style={{ width: `${Math.min(Math.max(puntaje, 0), 100)}%` }} />
      </div>

      <p className="text-sm text-slate-700">{validacion.consistencia}</p>

      {validacion.hallazgos?.length ? (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Hallazgos ({validacion.hallazgos.length})
          </p>
          <ul className="space-y-2">
            {validacion.hallazgos.map((hallazgo, indice) => (
              <li
                key={`${hallazgo.campo || 'general'}-${indice}`}
                className={`rounded-lg px-3 py-2 text-sm ring-1 ring-inset ${claseSeveridad(hallazgo.severidad)}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Etiqueta tono={tonoSeveridad(hallazgo.severidad)}>{hallazgo.severidad}</Etiqueta>
                  {hallazgo.campo ? (
                    <span className="font-mono text-[11px] text-slate-500">{hallazgo.campo}</span>
                  ) : null}
                </div>
                <p className="mt-1 text-slate-700">{hallazgo.mensaje}</p>
                {hallazgo.sugerencia ? (
                  <p className="mt-1 text-xs italic text-slate-500">Sugerencia: {hallazgo.sugerencia}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          No se detectaron hallazgos: el acta cumple con las verificaciones automáticas.
        </p>
      )}

      {validacion.recomendaciones?.length ? (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Recomendaciones
          </p>
          <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-600">
            {validacion.recomendaciones.map((recomendacion, indice) => (
              <li key={`recomendacion-${indice}`}>{recomendacion}</li>
            ))}
          </ol>
        </div>
      ) : null}
    </div>
  )
}
