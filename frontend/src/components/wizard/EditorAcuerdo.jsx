import Campo from '../ui/Campo.jsx'
import Boton from '../ui/Boton.jsx'
import { TIPOS_MAYORIA } from '../../constants/catalogos.js'

/**
 * Editor de un acuerdo: título, resumen del asunto y resultado de la votación.
 * El porcentaje requerido se propone a partir del catálogo de mayorías para
 * dejar constancia de la base de cómputo exigida por la LGSM.
 */
export default function EditorAcuerdo({ acuerdo, indice, onCambiar, onVotacion, onEliminar }) {
  const votacion = acuerdo.votacion || {}

  /** Al cambiar la mayoría se propone automáticamente el porcentaje requerido. */
  const cambiarMayoria = (valor) => {
    const tipo = TIPOS_MAYORIA.find((item) => item.valor === valor)
    onVotacion(indice, {
      tipo_mayoria: valor,
      porcentaje_requerido: tipo?.porcentaje_requerido ?? '',
    })
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Acuerdo {indice + 1}
          {acuerdo.materia ? (
            <span className="ml-2 font-normal normal-case text-corporativo-500">
              materia: {String(acuerdo.materia).replace(/_/g, ' ')}
            </span>
          ) : null}
        </p>
        <Boton variante="fantasma" tamano="sm" onClick={() => onEliminar(indice)}>
          Quitar
        </Boton>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <Campo
          etiqueta="Título del acuerdo"
          requerido
          ayuda="Debe coincidir con un punto del orden del día."
          htmlFor={`titulo-acuerdo-${indice}`}
        >
          <input
            id={`titulo-acuerdo-${indice}`}
            className="campo"
            value={acuerdo.titulo}
            onChange={(evento) => onCambiar(indice, { titulo: evento.target.value })}
            placeholder="Aumento de capital social"
          />
        </Campo>

        <Campo etiqueta="Tipo de mayoría" htmlFor={`mayoria-acuerdo-${indice}`}>
          <select
            id={`mayoria-acuerdo-${indice}`}
            className="campo"
            value={votacion.tipo_mayoria || 'mayoria_simple'}
            onChange={(evento) => cambiarMayoria(evento.target.value)}
          >
            {TIPOS_MAYORIA.map((mayoria) => (
              <option key={mayoria.valor} value={mayoria.valor}>
                {mayoria.etiqueta}
              </option>
            ))}
          </select>
        </Campo>
      </div>

      <Campo
        etiqueta="Resumen del asunto"
        requerido
        className="mt-3"
        ayuda="Descríbelo con tus palabras; la IA (o las plantillas legales) lo convertirá en cláusula."
        htmlFor={`resumen-acuerdo-${indice}`}
      >
        <textarea
          id={`resumen-acuerdo-${indice}`}
          rows={3}
          className="campo"
          value={acuerdo.resumen}
          onChange={(evento) => onCambiar(indice, { resumen: evento.target.value })}
          placeholder="Aumentar el capital social en $50,000.00 mediante la emisión de 50,000 acciones ordinarias…"
        />
      </Campo>

      <div className="mt-3 grid gap-3 md:grid-cols-4">
        <Campo etiqueta="Acciones a favor" htmlFor={`favor-${indice}`}>
          <input
            id={`favor-${indice}`}
            type="number"
            min="0"
            className="campo"
            value={votacion.acciones_a_favor ?? ''}
            onChange={(evento) => onVotacion(indice, { acciones_a_favor: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Acciones en contra" htmlFor={`contra-${indice}`}>
          <input
            id={`contra-${indice}`}
            type="number"
            min="0"
            className="campo"
            value={votacion.acciones_en_contra ?? 0}
            onChange={(evento) => onVotacion(indice, { acciones_en_contra: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="Abstenciones" htmlFor={`abstenciones-${indice}`}>
          <input
            id={`abstenciones-${indice}`}
            type="number"
            min="0"
            className="campo"
            value={votacion.abstenciones ?? 0}
            onChange={(evento) => onVotacion(indice, { abstenciones: evento.target.value })}
          />
        </Campo>
        <Campo etiqueta="% requerido" ayuda="Sugerido por mayoría" htmlFor={`requerido-${indice}`}>
          <input
            id={`requerido-${indice}`}
            type="number"
            min="0"
            max="100"
            step="0.01"
            className="campo"
            value={votacion.porcentaje_requerido ?? ''}
            onChange={(evento) => onVotacion(indice, { porcentaje_requerido: evento.target.value })}
          />
        </Campo>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-600">
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
            checked={votacion.aprobado !== false}
            onChange={(evento) => onVotacion(indice, { aprobado: evento.target.checked })}
          />
          Acuerdo aprobado
        </label>
        {votacion.aprobado === false ? (
          <span className="text-xs font-medium text-amber-700">
            Un acuerdo no aprobado genera un hallazgo crítico en la validación.
          </span>
        ) : null}
      </div>

    </div>
  )
}
