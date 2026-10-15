import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import useHistorialActas from '../../hooks/useHistorialActas.js'
import { ESTATUS_ACTA, TIPOS_ASAMBLEA, etiquetaDe } from '../../constants/catalogos.js'
import { claseEstatus, fechaCorta, marcaTiempo } from '../../utils/formato.js'

/**
 * Historial de actas: filtros, tabla de registros y acciones por acta
 * (editar, descargar PDF, revalidar, cambiar estatus y eliminar).
 */
export default function PanelHistorial({ onEditar = null, catalogos = null }) {
  const {
    actas,
    cargando,
    error,
    aviso,
    operando,
    filtros,
    setFiltros,
    recargar,
    descargar,
    validar,
    cambiarEstatus,
    borrar,
  } = useHistorialActas()

  const tipos = catalogos?.tipos_asamblea || TIPOS_ASAMBLEA
  const estatusDisponibles = catalogos?.estatus_acta || ESTATUS_ACTA

  return (
    <div className="space-y-5">
      <section className="tarjeta p-4">
        <div className="grid gap-3 md:grid-cols-4">
          <div>
            <label className="etiqueta-campo" htmlFor="filtro-texto">
              Búsqueda
            </label>
            <input
              id="filtro-texto"
              className="campo"
              value={filtros.texto}
              onChange={(evento) => setFiltros({ ...filtros, texto: evento.target.value })}
              placeholder="Folio, sociedad o título"
            />
          </div>
          <div>
            <label className="etiqueta-campo" htmlFor="filtro-tipo">
              Tipo de asamblea
            </label>
            <select
              id="filtro-tipo"
              className="campo"
              value={filtros.tipo_asamblea}
              onChange={(evento) => setFiltros({ ...filtros, tipo_asamblea: evento.target.value })}
            >
              <option value="">Todas</option>
              {tipos.map((tipo) => (
                <option key={tipo.valor} value={tipo.valor}>
                  {tipo.etiqueta}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="etiqueta-campo" htmlFor="filtro-estatus">
              Estatus
            </label>
            <select
              id="filtro-estatus"
              className="campo"
              value={filtros.estatus}
              onChange={(evento) => setFiltros({ ...filtros, estatus: evento.target.value })}
            >
              <option value="">Todos</option>
              {estatusDisponibles.map((item) => (
                <option key={item.valor} value={item.valor}>
                  {item.etiqueta}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end gap-2">
            <Boton variante="secundario" onClick={recargar} cargando={cargando}>
              Actualizar
            </Boton>
            <Boton
              variante="fantasma"
              onClick={() => setFiltros({ texto: '', tipo_asamblea: '', estatus: '' })}
            >
              Limpiar
            </Boton>
          </div>
        </div>
      </section>

      {error ? (
        <Alerta tono="error" titulo="Error al consultar el historial">
          {error}
        </Alerta>
      ) : null}
      {aviso ? <Alerta tono="exito">{aviso}</Alerta> : null}

      <section className="tarjeta overflow-hidden">
        {cargando ? (
          <div className="flex items-center justify-center gap-2 px-5 py-10 text-sm text-slate-500">
            Cargando actas…
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Folio</th>
                  <th className="px-4 py-3">Sociedad</th>
                  <th className="px-4 py-3">Asamblea</th>
                  <th className="px-4 py-3">Fecha</th>
                  <th className="px-4 py-3 text-center">Versión</th>
                  <th className="px-4 py-3">Estatus</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {actas.map((acta) => (
                  <tr key={acta.id} className="align-top hover:bg-slate-50">
                    <td className="px-4 py-3 font-mono text-xs text-corporativo-600">{acta.folio}</td>
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800">{acta.sociedad}</p>
                      <p className="text-xs text-slate-500">Creada el {marcaTiempo(acta.created_at)}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{etiquetaDe(tipos, acta.tipo_asamblea)}</td>
                    <td className="px-4 py-3 text-slate-600">{fechaCorta(acta.fecha)}</td>
                    <td className="px-4 py-3 text-center text-slate-600">v{acta.version}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${claseEstatus(
                          acta.estatus,
                        )}`}
                      >
                        {etiquetaDe(estatusDisponibles, acta.estatus)}
                      </span>
                      <select
                        className="campo mt-2 text-xs"
                        value={acta.estatus}
                        disabled={operando === acta.id}
                        onChange={(evento) => cambiarEstatus(acta, evento.target.value)}
                      >
                        {estatusDisponibles.map((item) => (
                          <option key={item.valor} value={item.valor}>
                            {item.etiqueta}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap justify-end gap-1.5">
                        <Boton
                          tamano="sm"
                          variante="secundario"
                          cargando={operando === acta.id}
                          onClick={() => descargar(acta)}
                        >
                          PDF
                        </Boton>
                        {onEditar ? (
                          <Boton tamano="sm" variante="fantasma" onClick={() => onEditar(acta)}>
                            Editar
                          </Boton>
                        ) : null}
                        <Boton
                          tamano="sm"
                          variante="fantasma"
                          disabled={operando === acta.id}
                          onClick={() => validar(acta)}
                        >
                          Validar
                        </Boton>
                        <Boton
                          tamano="sm"
                          variante="peligro"
                          disabled={operando === acta.id}
                          onClick={() => borrar(acta)}
                        >
                          Eliminar
                        </Boton>
                      </div>
                    </td>
                  </tr>
                ))}
                {!actas.length ? (
                  <tr>
                    <td className="px-4 py-10 text-center text-slate-500" colSpan={7}>
                      No hay actas registradas con los filtros actuales.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        )}
      </section>


      <p className="text-xs text-slate-500">
        Las actas se guardan con folio consecutivo por año (PGAC-AAAA-0001) y conservan su versión al
        actualizarse. La descarga del PDF se regenera desde la base de datos sin volver a invocar a la IA.
      </p>
    </div>
  )
}
