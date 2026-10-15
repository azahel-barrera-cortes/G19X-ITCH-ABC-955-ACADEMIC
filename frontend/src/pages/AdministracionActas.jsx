import { useCallback, useEffect, useState } from 'react'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import PanelVersiones from '../components/actas/PanelVersiones.jsx'
import {
  fijarCaducidad,
  mensajeDeError,
  obtenerActasPorVigencia,
  obtenerResumenAdministracion,
} from '../api/client.js'
import {
  ESTADOS_VIGENCIA,
  ESTATUS_ACTA,
  TIPOS_ASAMBLEA,
  etiquetaDe,
} from '../constants/catalogos.js'
import { fechaCorta, vigencia } from '../utils/formato.js'

/**
 * Página «Administración de actas».
 *
 * Reúne tres responsabilidades de gobernanza documental:
 *
 * 1. **Resumen** — totales por estatus y clasificación de vigencia.
 * 2. **Caducidad** — fija, amplía o elimina la fecha de caducidad de cada acta;
 *    las vencidas aparecen primero para atenderlas con prioridad.
 * 3. **Versiones** — historial completo de cada expediente con detalle y
 *    restauración de versiones previas.
 */
export default function AdministracionActas({ onEditar = null }) {
  const [resumen, setResumen] = useState(null)
  const [actas, setActas] = useState([])
  const [filtro, setFiltro] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [operando, setOperando] = useState(null)
  const [seleccionada, setSeleccionada] = useState(null)

  // Formularios de caducidad abiertos: { actaId: { fecha, motivo } }.
  const [formularios, setFormularios] = useState({})

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      const [datosResumen, datosActas] = await Promise.all([
        obtenerResumenAdministracion(),
        obtenerActasPorVigencia({ estado: filtro }),
      ])
      setResumen(datosResumen)
      setActas(datosActas)
      // Refresca la seleccionada para mantener sincronizada su versión.
      setSeleccionada((previa) =>
        previa ? datosActas.find((acta) => acta.id === previa.id) || null : previa,
      )
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }, [filtro])

  useEffect(() => {
    cargar()
  }, [cargar])

  const editarCampo = (actaId, campo, valor) =>
    setFormularios((previo) => ({
      ...previo,
      [actaId]: { ...(previo[actaId] || {}), [campo]: valor },
    }))

  const cerrarFormulario = (actaId) =>
    setFormularios((previo) => {
      const copia = { ...previo }
      delete copia[actaId]
      return copia
    })

  const guardarCaducidad = async (acta, fecha, motivo) => {
    setOperando(acta.id)
    setError(null)
    try {
      const actualizada = await fijarCaducidad(acta.id, {
        fechaCaducidad: fecha || null,
        motivo: motivo || 'Actualización de vigencia desde administración',
      })
      setAviso(
        actualizada.fecha_caducidad
          ? `${acta.folio} vigente hasta el ${fechaCorta(actualizada.fecha_caducidad)}.`
          : `${acta.folio} sin fecha de caducidad (plazo eliminado).`,
      )
      cerrarFormulario(acta.id)
      await cargar()
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(null)
    }
  }
const totalVencidas = resumen?.vigencia?.vencidas ?? 0

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">Administración de actas</h1>
        <p className="text-sm text-slate-500">
          Control del repositorio: estado general, caducidad de los expedientes e historial
          completo de versiones con restauración.
        </p>
      </header>

      {error ? <Alerta tono="error">{error}</Alerta> : null}
      {aviso ? <Alerta tono="exito">{aviso}</Alerta> : null}
      {totalVencidas > 0 ? (
        <Alerta tono="advertencia" titulo={`${totalVencidas} acta(s) vencida(s)`}>
          Hay expedientes cuya fecha de caducidad ya pasó. Revisa su vigencia o amplía el plazo.
        </Alerta>
      ) : null}

      {/* --- Resumen general ------------------------------------------------ */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Resumen tarjeta="Total de actas" valor={resumen?.total_actas} cargando={cargando} />
        <Resumen
          tarjeta="Versiones registradas"
          valor={resumen?.total_versiones}
          cargando={cargando}
        />
        <Resumen
          tarjeta="Vencidas"
          valor={resumen?.vigencia?.vencidas}
          destacado
          cargando={cargando}
        />
        <Resumen
          tarjeta="Por vencer (≤ 30 días)"
          valor={resumen?.vigencia?.por_vencer}
          cargando={cargando}
        />
      </section>

      {/* --- Vigencia / caducidad ------------------------------------------- */}
      <section className="tarjeta p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
            Caducidad de actas
          </h3>
          <div className="flex items-center gap-2">
            <label className="etiqueta-campo" htmlFor="filtro-vigencia">
              Mostrar
            </label>
            <select
              id="filtro-vigencia"
              className="campo w-48"
              value={filtro}
              onChange={(evento) => setFiltro(evento.target.value)}
            >
              <option value="">Todas (vencidas primero)</option>
              {ESTADOS_VIGENCIA.map((estado) => (
                <option key={estado.valor} value={estado.valor}>
                  {estado.etiqueta}
                </option>
              ))}
            </select>
            <Boton tamano="sm" variante="secundario" cargando={cargando} onClick={cargar}>
              Actualizar
            </Boton>
          </div>
        </div>

        {cargando && !actas.length ? (
          <p className="text-sm text-slate-500">Cargando expedientes…</p>
        ) : !actas.length ? (
          <p className="text-sm text-slate-500">No hay actas registradas con este filtro.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-3 py-2">Folio / acta</th>
                  <th className="px-3 py-2">Estado de vigencia</th>
                  <th className="px-3 py-2">Caducidad</th>
                  <th className="px-3 py-2 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {actas.map((acta) => (
                  <FilaActa
                    key={acta.id}
                    acta={acta}
                    formulario={formularios[acta.id] || null}
                    operando={operando === acta.id}
                    seleccionada={seleccionada?.id === acta.id}
                    onEditarCampo={editarCampo}
                    onGuardar={guardarCaducidad}
                    onCerrarFormulario={cerrarFormulario}
                    onSeleccionar={() =>
                      setSeleccionada(seleccionada?.id === acta.id ? null : acta)
                    }
                    onEditar={onEditar}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* --- Historial de versiones ------------------------------------------ */}
      {seleccionada ? <PanelVersiones acta={seleccionada} onCambio={cargar} /> : null}

      <p className="text-xs text-slate-500">
        Cada cambio de contenido o de caducidad genera una versión nueva, por lo que el historial
        siempre avanza: restaurar una versión anterior no borra las posteriores, sino que emite una
        versión con el contenido recuperado.
      </p>
    </div>
  )
}

/** Tarjeta de indicador del resumen general. */
function Resumen({ tarjeta, valor, destacado = false, cargando = false }) {
  return (
    <div className={`tarjeta p-4 ${destacado ? 'border-amber-300 bg-amber-50/60' : ''}`}>
      <p className="text-xs uppercase tracking-wide text-slate-500">{tarjeta}</p>
      <p
        className={`mt-1 text-2xl font-semibold ${
          destacado ? 'text-amber-700' : 'text-corporativo-700'
        }`}
      >
        {cargando ? '…' : valor ?? '—'}
      </p>
    </div>
  )
}

/**
 * Fila de la tabla de caducidad: identificación, vigencia, formulario de
 * edición de la fecha y acciones (guardar, quitar plazo, versiones, editar).
 */
function FilaActa({
  acta,
  formulario,
  operando,
  seleccionada,
  onEditarCampo,
  onGuardar,
  onCerrarFormulario,
  onSeleccionar,
  onEditar,
}) {
  const info = vigencia(acta.estado_caducidad, acta.dias_para_caducar)
  const [fechaLocal, setFechaLocal] = useState(formulario?.fecha ?? acta.fecha_caducidad ?? '')
  const [motivoLocal, setMotivoLocal] = useState(formulario?.motivo ?? '')

  // Sincroniza el borrador cuando cambia la fila seleccionada o se cierra el form.
  useEffect(() => {
    setFechaLocal(formulario?.fecha ?? acta.fecha_caducidad ?? '')
    setMotivoLocal(formulario?.motivo ?? '')
  }, [formulario, acta.fecha_caducidad, acta.id])

  return (
    <tr className="align-top">
      <td className="px-3 py-3">
        <p className="font-medium text-slate-800">{acta.folio}</p>
        <p className="text-xs text-slate-500">{acta.sociedad}</p>
        <p className="text-xs text-slate-400">
          {etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea)} · {fechaCorta(acta.fecha)} · v
          {acta.version} · {etiquetaDe(ESTATUS_ACTA, acta.estatus)}
        </p>
      </td>

      <td className="px-3 py-3">
        <Etiqueta tono={info.tono}>{info.texto}</Etiqueta>
        <p className="mt-1 text-xs text-slate-500">{info.detalle}</p>
      </td>

      <td className="px-3 py-3">
        <p className="text-sm text-slate-700">
          {acta.fecha_caducidad ? fechaCorta(acta.fecha_caducidad) : '—'}
        </p>
        {acta.motivo_caducidad ? (
          <p className="max-w-[220px] text-xs text-slate-400">{acta.motivo_caducidad}</p>
        ) : null}
        {formulario ? (
          <div className="mt-2 space-y-1.5">
            <input
              type="date"
              className="campo text-xs"
              aria-label="Nueva fecha de caducidad"
              value={fechaLocal}
              onChange={(evento) => {
                setFechaLocal(evento.target.value)
                onEditarCampo(acta.id, 'fecha', evento.target.value)
              }}
            />
            <input
              type="text"
              className="campo text-xs"
              aria-label="Motivo del cambio"
              placeholder="Motivo (opcional)"
              value={motivoLocal}
              onChange={(evento) => {
                setMotivoLocal(evento.target.value)
                onEditarCampo(acta.id, 'motivo', evento.target.value)
              }}
            />
          </div>
        ) : null}
      </td>

      <td className="px-3 py-3">
        <div className="flex flex-wrap justify-end gap-1.5">
          {formulario ? (
            <>
              <Boton
                tamano="sm"
                variante="primario"
                cargando={operando}
                onClick={() => onGuardar(acta, fechaLocal, motivoLocal)}
              >
                Guardar
              </Boton>
              <Boton
                tamano="sm"
                variante="fantasma"
                disabled={operando}
                onClick={() => onCerrarFormulario(acta.id)}
              >
                Cancelar
              </Boton>
            </>
          ) : (
            <Boton
              tamano="sm"
              variante="secundario"
              disabled={operando}
              onClick={() => onEditarCampo(acta.id, 'fecha', acta.fecha_caducidad || '')}
            >
              {acta.fecha_caducidad ? 'Ampliar' : 'Fijar caducidad'}
            </Boton>
          )}

          {!formulario && acta.fecha_caducidad ? (
            <Boton
              tamano="sm"
              variante="fantasma"
              cargando={operando}
              onClick={() => onGuardar(acta, '', 'Plazo eliminado desde administración')}
            >
              Quitar plazo
            </Boton>
          ) : null}

          <Boton tamano="sm" variante={seleccionada ? 'secundario' : 'fantasma'} onClick={onSeleccionar}>
            {seleccionada ? 'Ocultar versiones' : 'Versiones'}
          </Boton>

          {onEditar ? (
            <Boton tamano="sm" variante="fantasma" onClick={() => onEditar(acta)}>
              Editar
            </Boton>
          ) : null}
        </div>
      </td>
    </tr>
  )
}