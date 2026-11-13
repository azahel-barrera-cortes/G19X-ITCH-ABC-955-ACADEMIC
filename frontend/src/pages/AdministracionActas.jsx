import { Fragment, useCallback, useEffect, useMemo, useState } from 'react'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import DialogoConfirmacion from '../components/ui/DialogoConfirmacion.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import PanelVersiones from '../components/actas/PanelVersiones.jsx'
import {
  fijarCaducidad,
  listarBitacora,
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

const normalizarTexto = (valor) =>
  String(valor ?? '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()

const formatearAccion = (accion) =>
  String(accion || 'Actividad')
    .replace(/[_.-]+/g, ' ')
    .replace(/^./, (letra) => letra.toUpperCase())

const tonoDeAccion = (accion) => {
  const normalizada = normalizarTexto(accion)
  if (normalizada.includes('eliminar') || normalizada.includes('devolver')) return 'error'
  if (normalizada.includes('crear') || normalizada.includes('aprobar') || normalizada.includes('firmar')) {
    return 'exito'
  }
  if (normalizada.includes('actualizar') || normalizada.includes('restaurar')) return 'advertencia'
  return 'info'
}

const celdaCsv = (valor) => {
  const texto = String(valor ?? '')
  const seguro = /^[\s]*[=+\-@]/.test(texto) ? `'${texto}` : texto
  return `"${seguro.replace(/"/g, '""')}"`
}

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
export default function AdministracionActas({
  versionActaInicial = null,
  onVersionActaInicialMostrada = null,
}) {
  const [resumen, setResumen] = useState(null)
  const [actas, setActas] = useState([])
  const [filtro, setFiltro] = useState('')
  const [busquedaActa, setBusquedaActa] = useState('')
  const [filtroEstatus, setFiltroEstatus] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [operando, setOperando] = useState(null)
  const [seleccionada, setSeleccionada] = useState(null)
  const [actaPendienteQuitarPlazo, setActaPendienteQuitarPlazo] = useState(null)

  // Formularios de caducidad abiertos: { actaId: { fecha, motivo } }.
  const [formularios, setFormularios] = useState({})
  const [bitacora, setBitacora] = useState([])
  const [cargandoBitacora, setCargandoBitacora] = useState(true)
  const [errorBitacora, setErrorBitacora] = useState(null)
  const [busquedaBitacora, setBusquedaBitacora] = useState('')
  const [filtroAccionBitacora, setFiltroAccionBitacora] = useState('')
  const [limiteBitacora, setLimiteBitacora] = useState(10)

  const cargarBitacora = useCallback(async () => {
    setCargandoBitacora(true)
    setErrorBitacora(null)
    try {
      const datos = await listarBitacora({ entidad: 'actas', limite: 50 })
      setBitacora(Array.isArray(datos) ? datos : [])
    } catch (fallo) {
      setErrorBitacora(await mensajeDeError(fallo))
    } finally {
      setCargandoBitacora(false)
    }
  }, [])

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

  useEffect(() => {
    cargarBitacora()
  }, [cargarBitacora])

  useEffect(() => {
    if (versionActaInicial == null || !actas.length) return
    const acta = actas.find(
      (elemento) => String(elemento.id) === String(versionActaInicial),
    )
    if (!acta) return
    setSeleccionada(acta)
    onVersionActaInicialMostrada?.()
  }, [actas, onVersionActaInicialMostrada, versionActaInicial])

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

  const actualizarTodo = async () => {
    await Promise.all([cargar(), cargarBitacora()])
  }

  const limpiarFiltrosActas = () => {
    setFiltro('')
    setBusquedaActa('')
    setFiltroEstatus('')
  }

  const actasFiltradas = useMemo(() => {
    const termino = normalizarTexto(busquedaActa)
    return actas.filter((acta) => {
      const texto = normalizarTexto(
        [
          acta.folio,
          acta.sociedad,
          etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea),
          etiquetaDe(ESTATUS_ACTA, acta.estatus),
          acta.estado_caducidad,
          acta.motivo_caducidad,
        ].join(' '),
      )
      return (
        (!termino || texto.includes(termino)) &&
        (!filtroEstatus || acta.estatus === filtroEstatus)
      )
    })
  }, [actas, busquedaActa, filtroEstatus])

  const accionesBitacora = useMemo(
    () =>
      Array.from(new Set(bitacora.map((entrada) => String(entrada.accion || '')).filter(Boolean)))
        .sort((primera, segunda) => primera.localeCompare(segunda, 'es')),
    [bitacora],
  )

  const bitacoraFiltrada = useMemo(() => {
    const termino = normalizarTexto(busquedaBitacora)
    return bitacora.filter((entrada) => {
      const datos = entrada.datos_despues || entrada.datos_antes || {}
      const folio = datos.folio || `Acta #${entrada.entidad_id || 'general'}`
      const texto = normalizarTexto(
        [
          folio,
          entrada.accion,
          formatearAccion(entrada.accion),
          entrada.usuario_nombre,
          entrada.usuario_rol,
        ].join(' '),
      )
      return (
        (!termino || texto.includes(termino)) &&
        (!filtroAccionBitacora || entrada.accion === filtroAccionBitacora)
      )
    })
  }, [bitacora, busquedaBitacora, filtroAccionBitacora])

  const bitacoraVisible = bitacoraFiltrada.slice(0, limiteBitacora)
  const totalVencidas = resumen?.vigencia?.vencidas ?? 0
  const filtrosActasActivos = Boolean(filtro || busquedaActa.trim() || filtroEstatus)

  const exportarActasCsv = () => {
    if (!actasFiltradas.length) return

    const filas = [
      ['Folio', 'Sociedad', 'Tipo de acta', 'Estatus', 'Vigencia', 'Fecha de caducidad', 'Motivo'],
      ...actasFiltradas.map((acta) => [
        acta.folio,
        acta.sociedad,
        etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea),
        etiquetaDe(ESTATUS_ACTA, acta.estatus),
        vigencia(acta.estado_caducidad, acta.dias_para_caducar).texto,
        acta.fecha_caducidad || 'Sin caducidad',
        acta.motivo_caducidad,
      ]),
    ]
    const csv = `\uFEFF${filas.map((fila) => fila.map(celdaCsv).join(',')).join('\r\n')}`
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const ahora = new Date()
    const fechaArchivo = [
      ahora.getFullYear(),
      String(ahora.getMonth() + 1).padStart(2, '0'),
      String(ahora.getDate()).padStart(2, '0'),
    ].join('-')
    const enlace = document.createElement('a')
    enlace.href = url
    enlace.download = `actas-vigencia-${fechaArchivo}.csv`
    document.body.appendChild(enlace)
    enlace.click()
    enlace.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 0)
  }

  const confirmarQuitarPlazo = async () => {
    if (!actaPendienteQuitarPlazo) return
    await guardarCaducidad(
      actaPendienteQuitarPlazo,
      '',
      'Plazo eliminado desde administración',
    )
    setActaPendienteQuitarPlazo(null)
  }

  return (
    <div className="space-y-5">
      <header className="pgac-panel-in flex flex-col gap-5 rounded-2xl bg-corporativo-800 px-5 py-5 text-white shadow-lg shadow-corporativo-900/10 sm:flex-row sm:items-center sm:justify-between sm:px-7">
        <div className="flex items-start gap-4">
          <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/10 text-corporativo-50 ring-1 ring-inset ring-white/15">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              className="h-6 w-6"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 4h14v16H5z" />
              <path strokeLinecap="round" d="M8 9h8M8 13h8M8 17h5" />
            </svg>
          </span>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-corporativo-100">
              Centro de control documental
            </p>
            <h1 className="mt-1 text-xl font-bold tracking-tight sm:text-2xl">
              Administración de actas
            </h1>
            <p className="mt-1 max-w-2xl text-sm leading-5 text-corporativo-50/90">
              Supervisa vigencias, consulta versiones y revisa la actividad reciente del repositorio.
            </p>
          </div>
        </div>
        <Boton
          variante="secundario"
          cargando={cargando || cargandoBitacora}
          onClick={actualizarTodo}
          className="shrink-0 border-0"
          icono={
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="h-4 w-4"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M20 7v5h-5M4 17v-5h5" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M5.6 9a7 7 0 0112-2L20 12M4 12l2.4 5a7 7 0 0012-2" />
            </svg>
          }
        >
          Actualizar todo
        </Boton>
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
        <Resumen
          tarjeta="Total de actas"
          valor={resumen?.total_actas}
          cargando={cargando}
          tono="corporativo"
          seleccionado={!filtrosActasActivos}
          onClick={limpiarFiltrosActas}
        />
        <Resumen
          tarjeta="Versiones registradas"
          valor={resumen?.total_versiones}
          cargando={cargando}
          tono="neutral"
        />
        <Resumen
          tarjeta="Vencidas"
          valor={resumen?.vigencia?.vencidas}
          cargando={cargando}
          tono="error"
          seleccionado={filtro === 'vencida'}
          onClick={() => setFiltro('vencida')}
        />
        <Resumen
          tarjeta="Por vencer (≤ 30 días)"
          valor={resumen?.vigencia?.por_vencer}
          cargando={cargando}
          tono="advertencia"
          seleccionado={filtro === 'por_vencer'}
          onClick={() => setFiltro('por_vencer')}
        />
      </section>

      {/* --- Vigencia / caducidad ------------------------------------------- */}
      <section className="tarjeta overflow-hidden" aria-labelledby="vigencia-actas-titulo" aria-busy={cargando}>
        <div className="border-b border-slate-200 px-4 py-4 sm:px-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 id="vigencia-actas-titulo" className="text-sm font-semibold uppercase tracking-wide text-corporativo-700">
                Expedientes y vigencia
              </h3>
              <p className="mt-1 text-xs text-slate-500">
                Busca actas, combina filtros y administra sus plazos de conservación.
              </p>
            </div>
            <Etiqueta tono={actasFiltradas.length ? 'info' : 'neutral'}>
              {actasFiltradas.length} de {actas.length} actas
            </Etiqueta>
          </div>

          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-[minmax(220px,1.4fr)_minmax(180px,1fr)_minmax(180px,1fr)]">
            <div>
              <label className="etiqueta-campo" htmlFor="buscar-acta">
                Buscar expediente
              </label>
              <input
                id="buscar-acta"
                type="search"
                className="campo"
                value={busquedaActa}
                onChange={(evento) => setBusquedaActa(evento.target.value)}
                placeholder="Folio, sociedad o tipo de acta"
              />
            </div>
            <div>
              <label className="etiqueta-campo" htmlFor="filtro-estatus-acta">
                Estatus del acta
              </label>
              <select
                id="filtro-estatus-acta"
                className="campo"
                value={filtroEstatus}
                onChange={(evento) => setFiltroEstatus(evento.target.value)}
              >
                <option value="">Todos los estatus</option>
                {ESTATUS_ACTA.map((estatus) => (
                  <option key={estatus.valor} value={estatus.valor}>
                    {estatus.etiqueta}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="etiqueta-campo" htmlFor="filtro-vigencia">
                Estado de vigencia
              </label>
              <select
                id="filtro-vigencia"
                className="campo"
                value={filtro}
                onChange={(evento) => setFiltro(evento.target.value)}
              >
                <option value="">Todas las vigencias</option>
                {ESTADOS_VIGENCIA.map((estado) => (
                  <option key={estado.valor} value={estado.valor}>
                    {estado.etiqueta}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500" aria-live="polite">
              {cargando
                ? 'Actualizando expedientes…'
                : `Mostrando ${actasFiltradas.length} de ${actas.length} resultados`}
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <Boton
                tamano="sm"
                variante="fantasma"
                disabled={!filtrosActasActivos}
                onClick={limpiarFiltrosActas}
              >
                Limpiar filtros
              </Boton>
              <Boton
                tamano="sm"
                variante="secundario"
                disabled={!actasFiltradas.length || cargando}
                onClick={exportarActasCsv}
              >
                Exportar CSV
              </Boton>
              <Boton tamano="sm" variante="secundario" cargando={cargando} onClick={cargar}>
                Actualizar lista
              </Boton>
            </div>
          </div>
        </div>

        {cargando && !actas.length ? (
          <p className="px-5 py-10 text-center text-sm text-slate-500">Cargando expedientes…</p>
        ) : !actasFiltradas.length ? (
          <div className="px-5 py-12 text-center">
            <span className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-corporativo-50 text-corporativo-700">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
                <circle cx="10.5" cy="10.5" r="6.5" />
                <path strokeLinecap="round" d="m15.5 15.5 5 5" />
              </svg>
            </span>
            <p className="mt-3 text-sm font-semibold text-slate-700">
              {actas.length ? 'No hay actas que coincidan' : 'Aún no hay actas registradas'}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {actas.length
                ? 'Prueba con otros términos o restablece los filtros.'
                : 'Cuando se registren expedientes, aparecerán aquí.'}
            </p>
            {actas.length && filtrosActasActivos ? (
              <Boton className="mt-4" tamano="sm" variante="secundario" onClick={limpiarFiltrosActas}>
                Restablecer filtros
              </Boton>
            ) : null}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px] text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Expediente</th>
                  <th className="px-4 py-3">Vigencia</th>
                  <th className="px-4 py-3">Caducidad</th>
                  <th className="px-4 py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {actasFiltradas.map((acta) => (
                  <Fragment key={acta.id}>
                    <FilaActa
                      acta={acta}
                      formulario={formularios[acta.id] || null}
                      operando={operando === acta.id}
                      seleccionada={seleccionada?.id === acta.id}
                      onEditarCampo={editarCampo}
                      onGuardar={guardarCaducidad}
                      onCerrarFormulario={cerrarFormulario}
                      onSolicitarQuitarPlazo={() => setActaPendienteQuitarPlazo(acta)}
                      onSeleccionar={() =>
                        setSeleccionada(seleccionada?.id === acta.id ? null : acta)
                      }
                    />
                    {seleccionada?.id === acta.id ? (
                      <tr>
                        <td colSpan={4} className="bg-corporativo-50/40 p-3 sm:p-4">
                          <PanelVersiones acta={acta} onCambio={cargar} />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="tarjeta overflow-hidden" aria-labelledby="bitacora-actas-titulo">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-4 sm:px-5">
          <div>
            <h3 id="bitacora-actas-titulo" className="text-sm font-semibold uppercase tracking-wide text-corporativo-700">
              Bitácora de actas
            </h3>
            <p className="mt-1 text-xs text-slate-500">
              Actividad reciente. Se consultan hasta 50 registros por actualización.
            </p>
          </div>
          <Boton
            tamano="sm"
            variante="secundario"
            cargando={cargandoBitacora}
            onClick={cargarBitacora}
          >
            Actualizar bitácora
          </Boton>
        </div>

        <div className="grid gap-3 border-b border-slate-100 bg-slate-50/70 p-4 md:grid-cols-[minmax(220px,1fr)_minmax(180px,0.7fr)_auto] md:items-end">
          <div>
            <label className="etiqueta-campo" htmlFor="buscar-bitacora">
              Buscar actividad
            </label>
            <input
              id="buscar-bitacora"
              type="search"
              className="campo"
              value={busquedaBitacora}
              onChange={(evento) => {
                setBusquedaBitacora(evento.target.value)
                setLimiteBitacora(10)
              }}
              placeholder="Folio, usuario o acción"
            />
          </div>
          <div>
            <label className="etiqueta-campo" htmlFor="filtro-accion-bitacora">
              Tipo de actividad
            </label>
            <select
              id="filtro-accion-bitacora"
              className="campo"
              value={filtroAccionBitacora}
              onChange={(evento) => {
                setFiltroAccionBitacora(evento.target.value)
                setLimiteBitacora(10)
              }}
            >
              <option value="">Todas las acciones</option>
              {accionesBitacora.map((accion) => (
                <option key={accion} value={accion}>
                  {formatearAccion(accion)}
                </option>
              ))}
            </select>
          </div>
          <Boton
            tamano="sm"
            variante="fantasma"
            disabled={!busquedaBitacora && !filtroAccionBitacora}
            onClick={() => {
              setBusquedaBitacora('')
              setFiltroAccionBitacora('')
              setLimiteBitacora(10)
            }}
          >
            Limpiar filtros
          </Boton>
        </div>

        {errorBitacora ? (
          <div className="p-4"><Alerta tono="error">{errorBitacora}</Alerta></div>
        ) : cargandoBitacora && !bitacora.length ? (
          <p className="px-4 py-8 text-sm text-slate-500">Cargando actividad…</p>
        ) : !bitacora.length ? (
          <p className="px-4 py-8 text-center text-sm text-slate-500">
            Aún no hay actividad registrada en actas.
          </p>
        ) : !bitacoraFiltrada.length ? (
          <div className="px-4 py-8 text-center">
            <p className="text-sm font-semibold text-slate-700">No hay actividad que coincida</p>
            <p className="mt-1 text-xs text-slate-500">Cambia los términos o limpia los filtros.</p>
          </div>
        ) : (
          <>
            <ol aria-label="Actividad reciente de actas" className="max-h-[34rem] divide-y divide-slate-100 overflow-y-auto">
              {bitacoraVisible.map((entrada) => {
                const datos = entrada.datos_despues || entrada.datos_antes || {}
                const folio = datos.folio || `Acta #${entrada.entidad_id || 'general'}`
                const fecha = entrada.created_at ? new Date(entrada.created_at) : null
                const fechaValida = fecha && !Number.isNaN(fecha.getTime())
                return (
                  <li
                    key={entrada.id}
                    className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-slate-50 motion-reduce:transition-none"
                  >
                    <div className="flex min-w-0 items-start gap-3">
                      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-corporativo-50 text-corporativo-700">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l2.5 2.5M21 12a9 9 0 11-18 0 9 9 0 0118 0Z" />
                        </svg>
                      </span>
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <Etiqueta tono={tonoDeAccion(entrada.accion)}>
                            {formatearAccion(entrada.accion)}
                          </Etiqueta>
                          <span className="truncate font-mono text-xs font-semibold text-corporativo-800">
                            {folio}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          {entrada.usuario_nombre || 'Usuario'} · {entrada.usuario_rol || 'sin rol'}
                        </p>
                      </div>
                    </div>
                    <time
                      dateTime={fechaValida ? fecha.toISOString() : undefined}
                      className="pl-11 text-xs text-slate-500 sm:pl-0"
                    >
                      {fechaValida ? fecha.toLocaleString('es-MX') : 'Fecha no disponible'}
                    </time>
                  </li>
                )
              })}
            </ol>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-4 py-3">
              <p className="text-xs text-slate-500" aria-live="polite">
                Mostrando {Math.min(limiteBitacora, bitacoraFiltrada.length)} de {bitacoraFiltrada.length} actividades
              </p>
              {bitacoraFiltrada.length > 10 ? (
                <Boton
                  tamano="sm"
                  variante="fantasma"
                  onClick={() =>
                    setLimiteBitacora((actual) =>
                      actual >= bitacoraFiltrada.length
                        ? 10
                        : Math.min(actual + 10, bitacoraFiltrada.length),
                    )
                  }
                >
                  {limiteBitacora >= bitacoraFiltrada.length
                    ? 'Mostrar menos'
                    : `Mostrar ${Math.min(10, bitacoraFiltrada.length - limiteBitacora)} más`}
                </Boton>
              ) : null}
            </div>
          </>
        )}
      </section>

      <p className="rounded-xl border border-corporativo-100 bg-corporativo-50/50 px-4 py-3 text-xs leading-5 text-corporativo-800">
        Cada cambio de contenido o de caducidad genera una versión nueva, por lo que el historial
        siempre avanza: restaurar una versión anterior no borra las posteriores, sino que emite una
        versión con el contenido recuperado.
      </p>

      <DialogoConfirmacion
        abierto={Boolean(actaPendienteQuitarPlazo)}
        titulo="¿Quitar la fecha de caducidad?"
        descripcion={
          actaPendienteQuitarPlazo
            ? `${actaPendienteQuitarPlazo.folio} quedará sin plazo declarado. El expediente y su historial de versiones no se eliminarán.`
            : ''
        }
        etiquetaConfirmar="Quitar plazo"
        cargando={Boolean(
          actaPendienteQuitarPlazo && operando === actaPendienteQuitarPlazo.id,
        )}
        onCancelar={() => setActaPendienteQuitarPlazo(null)}
        onConfirmar={confirmarQuitarPlazo}
      />
    </div>
  )
}

/** Tarjeta de indicador del resumen general. */
function Resumen({
  tarjeta,
  valor,
  tono = 'corporativo',
  cargando = false,
  seleccionado = false,
  onClick = null,
}) {
  const estilos = {
    corporativo: {
      tarjeta: 'border-corporativo-200 bg-white',
      etiqueta: 'text-corporativo-600',
      valor: 'text-corporativo-800',
    },
    neutral: {
      tarjeta: 'border-slate-200 bg-white',
      etiqueta: 'text-slate-500',
      valor: 'text-slate-800',
    },
    error: {
      tarjeta: 'border-red-200 bg-red-50/60',
      etiqueta: 'text-red-700',
      valor: 'text-red-800',
    },
    advertencia: {
      tarjeta: 'border-amber-200 bg-amber-50/60',
      etiqueta: 'text-amber-800',
      valor: 'text-amber-900',
    },
  }[tono]
  const clases = `tarjeta w-full p-4 text-left ${estilos.tarjeta} ${
    onClick
      ? 'cursor-pointer transition-transform hover:-translate-y-0.5 hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-corporativo-600 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100 motion-reduce:transform-none'
      : ''
  } ${seleccionado ? 'ring-2 ring-corporativo-600 ring-offset-1' : ''}`
  const contenido = (
    <>
      <div className="flex items-center justify-between gap-2">
        <p className={`text-xs font-semibold uppercase tracking-wide ${estilos.etiqueta}`}>
          {tarjeta}
        </p>
        {onClick ? (
          <span className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
            {seleccionado ? 'Vista activa' : 'Filtrar'}
          </span>
        ) : null}
      </div>
      <p className={`mt-2 text-3xl font-bold tracking-tight ${estilos.valor}`}>
        {cargando ? '…' : valor ?? '—'}
      </p>
      {onClick ? (
        <p className="mt-1 text-xs text-slate-500">
          {seleccionado ? 'Mostrando esta vista' : 'Ver expedientes'}
        </p>
      ) : null}
    </>
  )

  return onClick ? (
    <button
      type="button"
      aria-pressed={seleccionado}
      disabled={cargando}
      onClick={onClick}
      className={clases}
    >
      {contenido}
    </button>
  ) : (
    <div className={clases}>{contenido}</div>
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
  onSolicitarQuitarPlazo,
  onSeleccionar,
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
    <tr className={`align-top transition-colors hover:bg-slate-50/80 motion-reduce:transition-none ${
      seleccionada ? 'bg-corporativo-50/40' : ''
    }`}>
      <td className="px-3 py-3">
        <p className="font-mono text-sm font-semibold text-corporativo-800">{acta.folio}</p>
        <p className="mt-0.5 font-medium text-slate-800">{acta.sociedad}</p>
        <p className="mt-1 text-xs text-slate-500">
          {etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea)} · {fechaCorta(acta.fecha)}
        </p>
        <p className="mt-0.5 text-[11px] text-slate-400">
          v{acta.version} · {etiquetaDe(ESTATUS_ACTA, acta.estatus)}
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
          <p className="mt-1 max-w-[220px] text-xs leading-5 text-slate-400">{acta.motivo_caducidad}</p>
        ) : null}
        {formulario ? (
          <div className="pgac-message-in mt-2 space-y-1.5 motion-reduce:animate-none">
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
              variante="peligro"
              disabled={operando}
              onClick={onSolicitarQuitarPlazo}
            >
              Quitar plazo
            </Boton>
          ) : null}

          <Boton
            tamano="sm"
            variante={seleccionada ? 'secundario' : 'fantasma'}
            aria-expanded={seleccionada}
            onClick={onSeleccionar}
          >
            {seleccionada ? 'Ocultar versiones' : 'Versiones'}
          </Boton>

        </div>
      </td>
    </tr>
  )
}