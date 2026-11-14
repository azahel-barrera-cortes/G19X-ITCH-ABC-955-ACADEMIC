import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { listarBitacora } from '../api/client.js'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import Indicador from '../components/ui/Indicador.jsx'
import { etiquetaRol } from '../constants/roles.js'

const ACCIONES = [
  { valor: 'todos', etiqueta: 'Todas las acciones' },
  { valor: 'crear', etiqueta: 'Creación' },
  { valor: 'actualizar', etiqueta: 'Modificación' },
  { valor: 'eliminar', etiqueta: 'Eliminación' },
  { valor: 'cambiar_estatus', etiqueta: 'Cambio de estatus' },
  { valor: 'validar', etiqueta: 'Validación' },
  { valor: 'iniciar_sesion', etiqueta: 'Inicio de sesión' },
  { valor: 'cerrar_sesion', etiqueta: 'Cierre de sesión' },
  { valor: 'generar_con_ia', etiqueta: 'Generación con IA' },
  { valor: 'generar_con_plantillas', etiqueta: 'Generación con plantillas' },
  { valor: 'cambiar_password', etiqueta: 'Cambio de contraseña' },
  { valor: 'crear_codigo_empresa', etiqueta: 'Creación de empresa' },
  { valor: 'analizar_revision', etiqueta: 'Análisis de revisión' },
  { valor: 'reenviar_revision', etiqueta: 'Reenvío a revisión' },
  { valor: 'reasignar_empresa', etiqueta: 'Reasignación de empresa' },
  { valor: 'restaurar_version', etiqueta: 'Restauración de versión' },
  { valor: 'fijar_caducidad', etiqueta: 'Cambio de caducidad' },
]

const ENTIDADES = [
  { valor: 'todos', etiqueta: 'Todas las entidades' },
  { valor: 'actas', etiqueta: 'Actas' },
  { valor: 'usuarios', etiqueta: 'Usuarios' },
  { valor: 'sesiones', etiqueta: 'Sesiones' },
]

const ETIQUETAS_ACCION = {
  crear: { texto: 'Creación', tono: 'exito' },
  actualizar: { texto: 'Modificación', tono: 'info' },
  eliminar: { texto: 'Eliminación', tono: 'error' },
  cambiar_estatus: { texto: 'Cambio de estatus', tono: 'advertencia' },
  validar: { texto: 'Validación', tono: 'info' },
  iniciar_sesion: { texto: 'Inicio de sesión', tono: 'neutral' },
  cerrar_sesion: { texto: 'Cierre de sesión', tono: 'advertencia' },
  generar_con_ia: { texto: 'Creación con IA', tono: 'info' },
  generar_con_plantillas: { texto: 'Generación con plantillas', tono: 'neutral' },
  cambiar_password: { texto: 'Cambio de contraseña', tono: 'advertencia' },
  crear_codigo_empresa: { texto: 'Creación de empresa', tono: 'info' },
  analizar_revision: { texto: 'Análisis de revisión', tono: 'info' },
  reenviar_revision: { texto: 'Reenvío a revisión', tono: 'advertencia' },
  reasignar_empresa: { texto: 'Reasignación de empresa', tono: 'advertencia' },
  restaurar_version: { texto: 'Restauración de versión', tono: 'info' },
  fijar_caducidad: { texto: 'Cambio de caducidad', tono: 'advertencia' },
}

const FORMATO_FECHA = new Intl.DateTimeFormat('es-MX', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const LIMITE_REGISTROS = 500
const REGISTROS_POR_PAGINA = 25
const INTERVALO_SINCRONIZACION = 5000

const esHoy = (fecha) => {
  if (!fecha) return false
  const hoy = new Date()
  const valor = new Date(fecha)
  return !Number.isNaN(valor.getTime()) && hoy.toDateString() === valor.toDateString()
}

const formatearFecha = (fecha) => {
  if (!fecha) return 'Fecha no disponible'
  const valor = new Date(fecha)
  return Number.isNaN(valor.getTime()) ? 'Fecha no disponible' : FORMATO_FECHA.format(valor)
}

const etiquetaAccion = (entrada) => {
  if (
    ['crear', 'actualizar'].includes(entrada.accion) &&
    entrada.datos_despues?.generado_con_ia === true
  ) {
    return ETIQUETAS_ACCION.generar_con_ia
  }
  return ETIQUETAS_ACCION[entrada.accion] || {
    texto: (entrada.accion || 'Acción desconocida').replaceAll('_', ' '),
    tono: 'neutral',
  }
}

const esGeneracionIa = (entrada) =>
  entrada.accion === 'generar_con_ia' || entrada.datos_despues?.generado_con_ia === true

const combinarEntradas = (anteriores, nuevas) => {
  const porId = new Map(anteriores.map((entrada) => [entrada.id, entrada]))
  nuevas.forEach((entrada) => porId.set(entrada.id, entrada))
  return [...porId.values()].sort((a, b) => b.id - a.id)
}

const resumenEntidad = (entrada) => {
  const datos = entrada.datos_despues || entrada.datos_antes
  if (!datos || typeof datos !== 'object') return `Registro #${entrada.entidad_id || 'general'}`
  return (
    datos.folio ||
    datos.nombre ||
    datos.nombre_completo ||
    datos.email ||
    datos.codigo_empresa ||
    `Registro #${entrada.entidad_id || 'general'}`
  )
}

const textoJson = (valor) =>
  valor == null ? 'Sin información' : JSON.stringify(valor, null, 2)

export default function VitacoraSuperAdmin() {
  const [entradas, setEntradas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [actualizando, setActualizando] = useState(false)
  const [cargandoAnteriores, setCargandoAnteriores] = useState(false)
  const [hayMasRegistros, setHayMasRegistros] = useState(false)
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null)
  const [error, setError] = useState('')
  const [entradaAbierta, setEntradaAbierta] = useState(null)
  const [pagina, setPagina] = useState(1)
  const solicitudActiva = useRef(false)
  const historialInicialCargado = useRef(false)
  const montado = useRef(true)
  const [filtros, setFiltros] = useState({
    busqueda: '',
    accion: 'todos',
    entidad: 'todos',
    fechaDesde: '',
    fechaHasta: '',
  })

  const cargarBitacora = useCallback(async (manual = false) => {
    if (solicitudActiva.current) return
    solicitudActiva.current = true
    if (manual) setActualizando(true)
    setError('')
    try {
      const datos = await listarBitacora({ limite: LIMITE_REGISTROS })
      if (!Array.isArray(datos)) {
        throw new Error('La respuesta del servidor para la bitácora no es válida.')
      }
      if (montado.current) {
        setEntradas((actuales) => combinarEntradas(actuales, datos))
        if (!historialInicialCargado.current) {
          setHayMasRegistros(datos.length === LIMITE_REGISTROS)
          historialInicialCargado.current = true
        }
        setUltimaActualizacion(new Date())
      }
    } catch (fallo) {
      if (montado.current) {
        setError(
          fallo.response?.data?.detail ||
            fallo.message ||
            'No se pudo consultar la bitácora de acciones.',
        )
      }
    } finally {
      solicitudActiva.current = false
      if (montado.current) {
        setCargando(false)
        setActualizando(false)
      }
    }
  }, [])

  const cargarAnteriores = async () => {
    if (solicitudActiva.current || !hayMasRegistros || entradas.length === 0) return
    solicitudActiva.current = true
    setCargandoAnteriores(true)
    setError('')
    try {
      const cursorId = entradas[entradas.length - 1].id
      const datos = await listarBitacora({
        limite: LIMITE_REGISTROS,
        cursor_id: cursorId,
      })
      if (!Array.isArray(datos)) {
        throw new Error('La respuesta del servidor para la bitácora no es válida.')
      }
      if (montado.current) {
        setEntradas((actuales) => combinarEntradas(actuales, datos))
        setHayMasRegistros(datos.length === LIMITE_REGISTROS)
      }
    } catch (fallo) {
      if (montado.current) {
        setError(
          fallo.response?.data?.detail ||
            fallo.message ||
            'No se pudieron cargar eventos anteriores.',
        )
      }
    } finally {
      solicitudActiva.current = false
      if (montado.current) setCargandoAnteriores(false)
    }
  }

  useEffect(() => {
    montado.current = true
    cargarBitacora()
    const intervalo = window.setInterval(() => cargarBitacora(), INTERVALO_SINCRONIZACION)
    return () => {
      montado.current = false
      window.clearInterval(intervalo)
    }
  }, [cargarBitacora])

  const entradasFiltradas = useMemo(() => {
    const termino = filtros.busqueda.trim().toLowerCase()
    return entradas.filter((entrada) => {
      const accionOk =
        filtros.accion === 'todos' ||
        (filtros.accion === 'generar_con_ia'
          ? esGeneracionIa(entrada)
          : entrada.accion === filtros.accion)
      const entidadOk = filtros.entidad === 'todos' || entrada.entidad === filtros.entidad
      const fechaRegistro = entrada.created_at ? new Date(entrada.created_at) : null
      const fechaValida = fechaRegistro && !Number.isNaN(fechaRegistro.getTime())
      const fechaLocal = fechaValida
        ? [
            fechaRegistro.getFullYear(),
            String(fechaRegistro.getMonth() + 1).padStart(2, '0'),
            String(fechaRegistro.getDate()).padStart(2, '0'),
          ].join('-')
        : ''
      const fechaDesdeOk = !filtros.fechaDesde || (fechaValida && fechaLocal >= filtros.fechaDesde)
      const fechaHastaOk = !filtros.fechaHasta || (fechaValida && fechaLocal <= filtros.fechaHasta)
      const texto = [
        entrada.usuario_nombre,
        entrada.usuario_rol,
        entrada.entidad,
        entrada.accion,
        resumenEntidad(entrada),
        JSON.stringify(entrada.datos_despues || {}),
        JSON.stringify(entrada.datos_antes || {}),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return (
        accionOk &&
        entidadOk &&
        fechaDesdeOk &&
        fechaHastaOk &&
        (!termino || texto.includes(termino))
      )
    })
  }, [entradas, filtros])

  const estadisticas = useMemo(
    () => ({
      total: entradas.length,
      hoy: entradas.filter((entrada) => esHoy(entrada.created_at)).length,
      actas: entradas.filter((entrada) => entrada.entidad === 'actas').length,
      usuarios: new Set(
        entradas
          .map((entrada) => entrada.usuario_id ?? entrada.usuario_nombre)
          .filter((usuario) => usuario !== undefined && usuario !== null && usuario !== ''),
      ).size,
    }),
    [entradas],
  )

  const cambiarFiltro = (campo, valor) => {
    setFiltros((previos) => ({ ...previos, [campo]: valor }))
    setPagina(1)
  }

  const limpiarFiltros = () => {
    setFiltros({
      busqueda: '',
      accion: 'todos',
      entidad: 'todos',
      fechaDesde: '',
      fechaHasta: '',
    })
    setPagina(1)
  }

  const filtrosActivos = [
    filtros.busqueda.trim(),
    filtros.accion !== 'todos',
    filtros.entidad !== 'todos',
    filtros.fechaDesde,
    filtros.fechaHasta,
  ].filter(Boolean).length
  const totalPaginas = Math.max(1, Math.ceil(entradasFiltradas.length / REGISTROS_POR_PAGINA))
  const paginaActual = Math.min(pagina, totalPaginas)
  const inicioPagina = (paginaActual - 1) * REGISTROS_POR_PAGINA
  const entradasPagina = entradasFiltradas.slice(
    inicioPagina,
    inicioPagina + REGISTROS_POR_PAGINA,
  )
  const primerResultado = entradasFiltradas.length ? inicioPagina + 1 : 0
  const ultimoResultado = Math.min(
    inicioPagina + REGISTROS_POR_PAGINA,
    entradasFiltradas.length,
  )
  const indicadores = [
    {
      titulo: 'Eventos cargados',
      valor: estadisticas.total,
      detalle: 'Eventos incorporados al historial de esta vista',
      acento: 'bg-corporativo-600',
    },
    {
      titulo: 'Eventos de hoy',
      valor: estadisticas.hoy,
      detalle: 'Actividad de la fecha actual',
      acento: 'bg-emerald-500',
    },
    {
      titulo: 'Cambios en actas',
      valor: estadisticas.actas,
      detalle: 'Dentro de los registros consultados',
      acento: 'bg-amber-500',
    },
    {
      titulo: 'Usuarios con actividad',
      valor: estadisticas.usuarios,
      detalle: 'Actores únicos en la consulta',
      acento: 'bg-sky-500',
    },
  ]

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-gradient-to-br from-white via-white to-corporativo-50/70">
        <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-5 px-4 py-6 sm:flex-row sm:items-center sm:justify-between md:px-8">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-corporativo-700">
              Super Administración <span className="px-1 text-slate-300">/</span> Auditoría
            </p>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 sm:text-3xl">
              Bitácora de acciones
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Revisa quién realizó cada acción, cuándo sucedió y qué información fue afectada.
            </p>
          </div>
          <div className="flex shrink-0 flex-col items-start gap-2 sm:items-end">
            <Boton
              variante="secundario"
              tamano="md"
              onClick={() => cargarBitacora(true)}
              cargando={actualizando}
            >
              Actualizar ahora
            </Boton>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
              Sincronización automática cada 5 s
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1480px] space-y-6 px-4 py-6 md:px-8">
        {error && (
          <Alerta tono="error" titulo="No se pudo cargar la bitácora">
            {error}
          </Alerta>
        )}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {indicadores.map(({ titulo, valor, detalle, acento }) => (
            <div
              key={titulo}
              className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md"
            >
              <span className={`absolute inset-x-0 top-0 h-1 ${acento}`} aria-hidden="true" />
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {titulo}
              </p>
              <p className="mt-3 text-3xl font-bold tabular-nums tracking-tight text-slate-950">
                {valor}
              </p>
              <p className="mt-1 text-xs text-slate-500">{detalle}</p>
            </div>
          ))}
        </section>

        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 p-4 sm:p-5 md:p-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-700">
                  Registro de auditoría
                </p>
                <h2 className="mt-1 text-lg font-semibold text-slate-900">
                  Actividad del sistema
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Filtra los eventos y consulta el detalle de cada registro.
                </p>
              </div>
              {ultimaActualizacion && (
                <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
                  Última consulta{' '}
                  <span className="font-semibold tabular-nums text-slate-700">
                    {ultimaActualizacion.toLocaleTimeString('es-MX')}
                  </span>
                </p>
              )}
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              <label className="block">
                <span className="etiqueta-campo">Buscar en la bitácora</span>
                <input
                  className="campo"
                  type="search"
                  value={filtros.busqueda}
                  onChange={(evento) => cambiarFiltro('busqueda', evento.target.value)}
                  placeholder="Usuario, folio, acción o entidad"
                />
              </label>
              <label className="block">
                <span className="etiqueta-campo">Tipo de acción</span>
                <select
                  className="campo"
                  value={filtros.accion}
                  onChange={(evento) => cambiarFiltro('accion', evento.target.value)}
                >
                  {ACCIONES.map((opcion) => (
                    <option key={opcion.valor} value={opcion.valor}>
                      {opcion.etiqueta}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="etiqueta-campo">Entidad afectada</span>
                <select
                  className="campo"
                  value={filtros.entidad}
                  onChange={(evento) => cambiarFiltro('entidad', evento.target.value)}
                >
                  {ENTIDADES.map((opcion) => (
                    <option key={opcion.valor} value={opcion.valor}>
                      {opcion.etiqueta}
                    </option>
                  ))}
                </select>
              </label>
              <label className="block">
                <span className="etiqueta-campo">Fecha desde</span>
                <input
                  className="campo"
                  type="date"
                  value={filtros.fechaDesde}
                  max={filtros.fechaHasta || undefined}
                  onChange={(evento) => cambiarFiltro('fechaDesde', evento.target.value)}
                />
              </label>
              <label className="block">
                <span className="etiqueta-campo">Fecha hasta</span>
                <input
                  className="campo"
                  type="date"
                  min={filtros.fechaDesde || undefined}
                  value={filtros.fechaHasta}
                  onChange={(evento) => cambiarFiltro('fechaHasta', evento.target.value)}
                />
              </label>
            </div>
            <div className="mt-4 flex flex-col gap-3 border-t border-slate-100 pt-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap items-center gap-3">
                <Boton
                  variante="secundario"
                  tamano="sm"
                  onClick={limpiarFiltros}
                  disabled={!filtrosActivos}
                >
                  Limpiar filtros
                </Boton>
                <span className="text-xs font-medium text-slate-600" aria-live="polite">
                  {filtrosActivos
                    ? `${filtrosActivos} ${filtrosActivos === 1 ? 'filtro activo' : 'filtros activos'}`
                    : 'Sin filtros aplicados'}
                </span>
              </div>
              <p className="max-w-xl text-xs leading-5 text-slate-500">
                {hayMasRegistros
                  ? `Se han cargado ${entradas.length} eventos. Hay eventos anteriores disponibles.`
                  : `Se han cargado ${entradas.length} eventos; no hay más eventos anteriores.`}
              </p>
            </div>
          </div>

          {cargando ? (
            <div
              className="flex min-h-64 items-center justify-center gap-3 text-sm text-slate-500"
              aria-live="polite"
            >
              <Indicador /> Cargando actividad…
            </div>
          ) : entradasFiltradas.length === 0 ? (
            <div className="m-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-12 text-center sm:m-6">
              <p className="text-sm font-semibold text-slate-800">
                {entradas.length ? 'No hay resultados para estos filtros' : 'Aún no hay actividad'}
              </p>
              <p className="mx-auto mt-1 max-w-md text-sm leading-6 text-slate-500">
                {entradas.length
                  ? 'Prueba con otros criterios o limpia los filtros para ver los eventos consultados.'
                  : 'Cuando se registren acciones en el sistema, aparecerán aquí.'}
              </p>
            </div>
          ) : (
            <div>
              <div className="hidden grid-cols-5 gap-4 border-b border-slate-200 bg-slate-50 px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 lg:grid">
                <span>Acción</span>
                <span>Usuario y rol</span>
                <span>Entidad afectada</span>
                <span>Fecha y hora</span>
                <span className="text-right">Detalle</span>
              </div>
              <div>
                {entradasPagina.map((entrada) => {
                  const accion = etiquetaAccion(entrada)
                  const abierta = entradaAbierta === entrada.id
                  const nombreUsuario =
                    entrada.usuario_nombre ||
                    `Usuario #${entrada.usuario_id || 'del sistema'}`
                  return (
                      <article
                        key={entrada.id}
                        className="border-b border-slate-100 last:border-b-0"
                      >
                        <div className="grid gap-4 p-4 transition-colors hover:bg-slate-50/80 sm:grid-cols-2 lg:grid-cols-5 lg:items-center lg:px-6">
                          <div>
                            <Etiqueta tono={accion.tono}>{accion.texto}</Etiqueta>
                            <p className="mt-2 text-xs tabular-nums text-slate-500">
                              Evento #{entrada.id}
                            </p>
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-slate-800">
                              {nombreUsuario}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {entrada.usuario_rol
                                ? etiquetaRol(entrada.usuario_rol)
                                : 'Sistema'}
                            </p>
                          </div>
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium capitalize text-slate-800">
                              {entrada.entidad || 'Entidad general'}
                            </p>
                            <p className="mt-1 truncate text-xs text-slate-500">
                              {resumenEntidad(entrada)}
                            </p>
                          </div>
                          <p className="text-sm tabular-nums text-slate-600">
                            {formatearFecha(entrada.created_at)}
                          </p>
                          <div className="flex justify-start lg:justify-end">
                            <button
                              type="button"
                              onClick={() => setEntradaAbierta(abierta ? null : entrada.id)}
                              className="rounded-lg px-3 py-2 text-xs font-semibold text-corporativo-700 transition hover:bg-corporativo-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-corporativo-600"
                              aria-expanded={abierta}
                              aria-controls={
                                abierta ? `detalle-bitacora-${entrada.id}` : undefined
                              }
                            >
                              {abierta ? 'Ocultar detalle' : 'Ver detalle'}
                            </button>
                          </div>
                        </div>
                        {abierta && (
                          <div
                            id={`detalle-bitacora-${entrada.id}`}
                            className="border-t border-slate-100 bg-slate-50 px-4 pb-5 sm:px-6"
                          >
                            <div className="grid gap-4 border-t border-slate-200 pt-4 md:grid-cols-2">
                              <div className="min-w-0">
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                  Datos anteriores
                                </p>
                                <pre className="mt-2 max-h-52 overflow-auto break-all rounded-lg bg-white p-3 text-xs leading-5 text-slate-600 ring-1 ring-slate-200">
                                  {textoJson(entrada.datos_antes)}
                                </pre>
                              </div>
                              <div className="min-w-0">
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                  Datos posteriores
                                </p>
                                <pre className="mt-2 max-h-52 overflow-auto break-all rounded-lg bg-white p-3 text-xs leading-5 text-slate-600 ring-1 ring-slate-200">
                                  {textoJson(entrada.datos_despues)}
                                </pre>
                              </div>
                              <div className="text-xs text-slate-500 md:col-span-2">
                                <span className="font-semibold text-slate-700">IP de origen:</span>{' '}
                                {entrada.ip_origen || 'No disponible'}
                                <span className="mx-3 text-slate-300">|</span>
                                <span className="font-semibold text-slate-700">ID de entidad:</span>{' '}
                                {entrada.entidad_id ?? 'No disponible'}
                              </div>
                            </div>
                          </div>
                        )}
                      </article>
                  )
                })}
              </div>
              <footer className="flex flex-col gap-3 border-t border-slate-200 bg-white px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
                <p className="text-xs text-slate-500" aria-live="polite">
                  Mostrando{' '}
                  <span className="font-semibold text-slate-700">
                    {primerResultado}–{ultimoResultado}
                  </span>{' '}
                  de{' '}
                  <span className="font-semibold text-slate-700">
                    {entradasFiltradas.length}
                  </span>{' '}
                  eventos
                </p>
                <div className="flex items-center gap-2">
                  {hayMasRegistros && (
                    <Boton
                      variante="secundario"
                      tamano="sm"
                      onClick={cargarAnteriores}
                      disabled={actualizando}
                      cargando={cargandoAnteriores}
                    >
                      Cargar anteriores
                    </Boton>
                  )}
                  <Boton
                    variante="secundario"
                    tamano="sm"
                    disabled={paginaActual <= 1}
                    onClick={() => setPagina((actual) => Math.max(1, actual - 1))}
                  >
                    Anterior
                  </Boton>
                  <span className="min-w-24 text-center text-xs tabular-nums text-slate-500">
                    Página {paginaActual} de {totalPaginas}
                  </span>
                  <Boton
                    variante="secundario"
                    tamano="sm"
                    disabled={paginaActual >= totalPaginas}
                    onClick={() =>
                      setPagina((actual) => Math.min(totalPaginas, actual + 1))
                    }
                  >
                    Siguiente
                  </Boton>
                </div>
              </footer>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
