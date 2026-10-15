import Campo from '../ui/Campo.jsx'
import Boton from '../ui/Boton.jsx'
import { CARACTERES_ASISTENTE } from '../../constants/catalogos.js'
import { porcentaje } from '../../utils/formato.js'

/**
 * Editor de un asistente: identificación, carácter, tenencia accionaria y firma.
 * El porcentaje de capital se calcula con base en las acciones en circulación.
 */
export default function EditorAsistente({
  asistente,
  indice,
  porcentajeCalculado = 0,
  onCambiar,
  onEliminar,
}) {
  const actualizar = (cambios) => onCambiar(indice, cambios)

  /** Marca de forma exclusiva el papel de presidente/secretario de la asamblea. */
  const marcarPapel = (campo) => (evento) => {
    if (evento.target.checked) {
      actualizar({
        es_presidente: campo === 'es_presidente',
        es_secretario: campo === 'es_secretario',
      })
    } else {
      actualizar({ [campo]: false })
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Asistente {indice + 1}
        </p>
        <Boton variante="fantasma" tamano="sm" onClick={() => onEliminar(indice)}>
          Quitar
        </Boton>
      </div>

      <div className="grid gap-3 md:grid-cols-12">
        <Campo etiqueta="Nombre completo" requerido className="md:col-span-5">
          <input
            className="campo"
            value={asistente.nombre}
            onChange={(evento) => actualizar({ nombre: evento.target.value })}
            placeholder="Ana María Ruiz Salazar"
          />
        </Campo>

        <Campo etiqueta="Carácter" className="md:col-span-4">
          <select
            className="campo"
            value={asistente.caracter}
            onChange={(evento) => actualizar({ caracter: evento.target.value })}
          >
            {CARACTERES_ASISTENTE.map((caracter) => (
              <option key={caracter.valor} value={caracter.valor}>
                {caracter.etiqueta}
              </option>
            ))}
          </select>
        </Campo>

        <Campo etiqueta="Cargo" className="md:col-span-3" ayuda="Opcional">
          <input
            className="campo"
            value={asistente.cargo}
            onChange={(evento) => actualizar({ cargo: evento.target.value })}
            placeholder="Presidenta del Consejo"
          />
        </Campo>

        <Campo etiqueta="Acciones" className="md:col-span-3">
          <input
            type="number"
            min="0"
            step="1"
            className="campo"
            value={asistente.acciones}
            onChange={(evento) => actualizar({ acciones: evento.target.value })}
            placeholder="50000"
          />
        </Campo>

        <div className="md:col-span-3">
          <span className="etiqueta-campo">% del capital</span>
          <p className="flex h-[38px] items-center rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm font-semibold text-corporativo-600">
            {porcentaje(porcentajeCalculado, 2)}
          </p>
        </div>

        <Campo etiqueta="R.F.C." className="md:col-span-3" ayuda="Opcional">
          <input
            className="campo uppercase"
            maxLength={13}
            value={asistente.rfc}
            onChange={(evento) => actualizar({ rfc: evento.target.value.toUpperCase() })}
          />
        </Campo>

        <Campo etiqueta="Correo electrónico" className="md:col-span-3" ayuda="Opcional">
          <input
            type="email"
            className="campo"
            value={asistente.email}
            onChange={(evento) => actualizar({ email: evento.target.value })}
          />
        </Campo>
      </div>

      <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-600">
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
            checked={Boolean(asistente.es_presidente)}
            onChange={marcarPapel('es_presidente')}
          />
          Preside la asamblea
        </label>
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
            checked={Boolean(asistente.es_secretario)}
            onChange={marcarPapel('es_secretario')}
          />
          Funge como secretario
        </label>
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
            checked={Boolean(asistente.es_escrutador)}
            onChange={(evento) => actualizar({ es_escrutador: evento.target.checked })}
          />
          Escrutador
        </label>
        <label className="inline-flex items-center gap-2">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
            checked={asistente.firma !== false}
            onChange={(evento) => actualizar({ firma: evento.target.checked })}
          />
          Firma el acta
        </label>
      </div>
    </div>
  )
}
