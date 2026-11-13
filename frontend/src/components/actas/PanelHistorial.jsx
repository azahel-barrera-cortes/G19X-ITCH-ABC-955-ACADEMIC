import { Fragment, useState } from 'react'
import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import PanelValidacion from './PanelValidacion.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { tieneAcceso } from '../../constants/roles.js'
import useHistorialActas from '../../hooks/useHistorialActas.js'
import {
  ESTATUS_ACTA,
  TIPOS_ASAMBLEA,
  etiquetaDe,
  etiquetaFlujoActa,
} from '../../constants/catalogos.js'
import { claseEstatus, fechaCorta, marcaTiempo } from '../../utils/formato.js'
import VisorActa from './VisorActa.jsx'

/**
 * Historial de actas: filtros, tabla de registros y acciones por acta
 * (consultar, revalidar y eliminar). Las decisiones del flujo se hacen en las
 * bandejas del Revisor y del Abogado.
 */
export default function PanelHistorial({ catalogos = null }) {
  const { usuario } = useAuth()
  const puedeValidar = tieneAcceso(usuario?.rol, 'abogado_responsable')
  const puedeDescargarPdf = tieneAcceso(usuario?.rol, 'abogado_responsable')
  const puedeEliminar = tieneAcceso(usuario?.rol, 'Administrador')
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
    borrar,
  } = useHistorialActas()

  const tipos = catalogos?.tipos_asamblea || TIPOS_ASAMBLEA
  const estatusDisponibles = catalogos?.estatus_acta || ESTATUS_ACTA
  const [actaVisible, setActaVisible] = useState(null)
  const [validaciones, setValidaciones] = useState({})
  const [validacionesAbiertas, setValidacionesAbiertas] = useState({})

  const validarYMostrar = async (acta) => {
    if (validacionesAbiertas[acta.id]) {
      setValidacionesAbiertas((previo) => ({ ...previo, [acta.id]: false }))
      return
    }
    if (validaciones[acta.id]) {
      setValidacionesAbiertas((previo) => ({ ...previo, [acta.id]: true }))
      return
    }

    const resultado = await validar(acta)
    if (resultado) {
      setValidaciones((previo) => ({ ...previo, [acta.id]: resultado }))
      setValidacionesAbiertas((previo) => ({ ...previo, [acta.id]: true }))
    }
  }

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
                {actas.map((acta) => {
                  const validacion = validaciones[acta.id]
                  const validacionAbierta = Boolean(validacionesAbiertas[acta.id])
                  return (
                    <Fragment key={acta.id}>
                      <tr className="align-top hover:bg-slate-50">
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
                          <p className="mt-1 text-xs font-medium text-corporativo-700">
                            Flujo: {etiquetaFlujoActa(acta.estado_flujo)}
                          </p>
                          <LineaProcesoActa estado={acta.estado_flujo} />
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap justify-end gap-1.5">
                            <Boton
                              tamano="sm"
                              variante="secundario"
                              onClick={() => setActaVisible(acta)}
                            >
                              Ver acta
                            </Boton>
                            {puedeDescargarPdf && acta.estado_flujo === 'aprobada' ? (
                              <Boton
                                tamano="sm"
                                variante="primario"
                                cargando={operando === acta.id}
                                onClick={() => descargar(acta)}
                              >
                                Descargar PDF final
                              </Boton>
                            ) : null}
                            {puedeValidar ? (
                              <Boton
                                tamano="sm"
                                variante="fantasma"
                                cargando={operando === acta.id}
                                aria-expanded={validacionAbierta}
                                aria-controls={validacion ? `validacion-${acta.id}` : undefined}
                                onClick={() => validarYMostrar(acta)}
                              >
                                {validacionAbierta ? 'Ocultar análisis' : 'Analizar con IA'}
                              </Boton>
                            ) : null}
                            {puedeEliminar ? (
                              <Boton
                                tamano="sm"
                                variante="peligro"
                                disabled={operando === acta.id}
                                onClick={() => borrar(acta)}
                              >
                                Eliminar
                              </Boton>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                      {validacion && validacionAbierta ? (
                        <tr>
                          <td className="bg-corporativo-50/30 px-4 py-4" colSpan={7}>
                            <section
                              id={`validacion-${acta.id}`}
                              className="rounded-xl border border-corporativo-100 bg-white p-4"
                            >
                              <h3 className="mb-3 text-sm font-semibold text-corporativo-700">
                                Validación de consistencia · {acta.folio}
                              </h3>
                              <PanelValidacion validacion={validacion} />
                            </section>
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  )
                })}
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
        Las actas conservan el historial de versiones. El PDF final solo está disponible para el
        Abogado después de aprobar el acta.
      </p>

      {actaVisible ? (
        <VisorActa acta={actaVisible} onCerrar={() => setActaVisible(null)} />
      ) : null}
    </div>
  )
}

const PASOS_PROCESO = [
  { valor: 'revision', etiqueta: 'Revisor' },
  { valor: 'abogado', etiqueta: 'Abogado' },
  { valor: 'aprobada', etiqueta: 'Aprobada' },
]

function LineaProcesoActa({ estado }) {
  const pasoActual = PASOS_PROCESO.findIndex((paso) => paso.valor === estado)
  const etiquetaActual = etiquetaFlujoActa(estado)

  return (
    <div className="mt-3 min-w-[190px]" aria-label={`Proceso del acta: ${etiquetaActual}`}>
      <div className="flex items-center">
        {PASOS_PROCESO.map((paso, indice) => (
          <div key={paso.valor} className="flex flex-1 items-center last:flex-none">
            <span
              className={`h-2 w-2 shrink-0 rounded-full ${
                estado === 'con_errores' && indice === 0
                  ? 'bg-red-500 ring-2 ring-red-100'
                  : indice < pasoActual
                  ? 'bg-emerald-500'
                  : indice === pasoActual
                    ? 'bg-corporativo-600 ring-2 ring-corporativo-100'
                    : 'bg-slate-200'
              }`}
              title={paso.etiqueta}
            />
            {indice < PASOS_PROCESO.length - 1 ? (
              <span className={`h-px flex-1 ${indice < pasoActual ? 'bg-emerald-300' : 'bg-slate-200'}`} />
            ) : null}
          </div>
        ))}
      </div>
      <p className="mt-1 text-[10px] text-slate-500">Etapa: {etiquetaActual}</p>
    </div>
  )
}
