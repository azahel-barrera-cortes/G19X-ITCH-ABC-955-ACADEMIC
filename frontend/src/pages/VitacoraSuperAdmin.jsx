import { Fragment, useCallback, useEffect, useMemo, useState } from 'react'

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
]

const ENTIDADES = [
  { valor: 'todos', etiqueta: 'Todas las entidades' },
  { valor: 'actas', etiqueta: 'Actas' },
  { valor: 'usuarios', etiqueta: 'Usuarios' },
  { valor: 'expedientes', etiqueta: 'Expedientes' },
  { valor: 'notaria', etiqueta: 'Notaría' },
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
}

const FORMATO_FECHA = new Intl.DateTimeFormat('es-MX', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

const esHoy = (fecha) => {
  if (!fecha) return false
  const hoy = new Date()
  const valor = new Date(fecha)
  return hoy.toDateString() === valor.toDateString()
}

const etiquetaAccion = (accion) =>
  ETIQUETAS_ACCION[accion] || {
    texto: accion.replaceAll('_', ' '),
    tono: 'neutral',
  }

const resumenEntidad = (entrada) => {
  const datos = entrada.datos_despues || entrada.datos_antes
  if (!datos || typeof datos !== 'object') return `Registro #${entrada.entidad_id || 'general'}`
  return datos.folio || datos.nombre || datos.email || `Registro #${entrada.entidad_id || 'general'}`
}

const textoJson = (valor) => (valor ? JSON.stringify(valor, null, 2) : 'Sin información')
const INTERVALO_SINCRONIZACION = 5000

export default function VitacoraSuperAdmin() {
  const [entradas, setEntradas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [actualizando, setActualizando] = useState(false)
  const [ultimaActualizacion, setUltimaActualizacion] = useState(null)
  const [error, setError] = useState('')
  const [entradaAbierta, setEntradaAbierta] = useState(null)
  const [filtros, setFiltros] = useState({
    busqueda: '',
    accion: 'todos',
    entidad: 'todos',
    fechaDesde: '',
    fechaHasta: '',
  })

  const cargarBitacora = useCallback(async (manual = false) => {
    if (manual) setActualizando(true)
    else setCargando(true)
    setError('')
    try {
      const datos = await listarBitacora({ limite: 500 })
      setEntradas(Array.isArray(datos) ? datos : [])
      setUltimaActualizacion(new Date())
    } catch (fallo) {
      setError(
        fallo.response?.data?.detail ||
          fallo.message ||
          'No se pudo consultar la bitácora de acciones.',
      )
    } finally {
      setCargando(false)
      setActualizando(false)
    }
  }, [])

  useEffect(() => {
    cargarBitacora()
    const intervalo = window.setInterval(() => cargarBitacora(), INTERVALO_SINCRONIZACION)
    return () => window.clearInterval(intervalo)
  }, [cargarBitacora])

  const entradasFiltradas = useMemo(() => {
    const termino = filtros.busqueda.trim().toLowerCase()
    return entradas.filter((entrada) => {
      const accionOk = filtros.accion === 'todos' || entrada.accion === filtros.accion
      const entidadOk = filtros.entidad === 'todos' || entrada.entidad === filtros.entidad
      const fechaRegistro = entrada.created_at ? new Date(entrada.created_at) : null
      const fechaLocal = fechaRegistro
        ? [
            fechaRegistro.getFullYear(),
            String(fechaRegistro.getMonth() + 1).padStart(2, '0'),
            String(fechaRegistro.getDate()).padStart(2, '0'),
          ].join('-')
        : ''
      const fechaDesdeOk = !filtros.fechaDesde || fechaLocal >= filtros.fechaDesde
      const fechaHastaOk = !filtros.fechaHasta || fechaLocal <= filtros.fechaHasta
      const texto = [
        entrada.usuario_nombre,
        entrada.usuario_rol,
        entrada.entidad,
        entrada.accion,
        resumenEntidad(entrada),
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
    () => {
      const sesionesPorUsuario = new Map()
      const eventosSesion = entradas
        .filter(
          (entrada) =>
            entrada.accion === 'iniciar_sesion' || entrada.accion === 'cerrar_sesion',
        )
        .filter((entrada) => entrada.usuario_rol !== 'SuperAdministrador')
        .sort(
          (a, b) =>
            new Date(a.created_at || 0).getTime() -
              new Date(b.created_at || 0).getTime() ||
            a.id - b.id,
        )

      eventosSesion.forEach((entrada) => {
        const clave = entrada.usuario_id || entrada.usuario_nombre
        if (!clave) return
        const sesionesAbiertas = sesionesPorUsuario.get(clave) || 0
        sesionesPorUsuario.set(
          clave,
          entrada.accion === 'iniciar_sesion'
            ? sesionesAbiertas + 1
            : Math.max(0, sesionesAbiertas - 1),
        )
      })

      return {
        total: entradas.length,
        hoy: entradas.filter((entrada) => esHoy(entrada.created_at)).length,
        actas: entradas.filter((entrada) => entrada.entidad === 'actas').length,
        usuarios: [...sesionesPorUsuario.values()].filter((sesiones) => sesiones > 0).length,
      }
    },
    [entradas],
  )

  const cambiarFiltro = (campo, valor) =>
    setFiltros((previos) => ({ ...previos, [campo]: valor }))

  const limpiarFiltros = () =>
    setFiltros({
      busqueda: '',
      accion: 'todos',
      entidad: 'todos',
      fechaDesde: '',
      fechaHasta: '',
    })

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-[1480px] items-center justify-between gap-4 px-4 py-5 md:px-8">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-corporativo-600">
              Super Administración / Auditoría
            </p>
            <h1 className="mt-1 text-2xl font-bold text-slate-900">
              Bitácora de acciones
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Consulta quién hizo cada cambio, cuándo ocurrió y qué información fue afectada.
            </p>
          </div>
          <Boton
            variante="secundario"
            tamano="sm"
            onClick={() => cargarBitacora(true)}
            cargando={actualizando}
          >
            Actualizar
          </Boton>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1480px] px-4 py-6 md:px-8">
        {error && (
          <Alerta tono="error" titulo="No se pudo cargar la bitácora">
            {error}
          </Alerta>
        )}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ['Eventos registrados', estadisticas.total, 'Historial visible'],
            ['Eventos de hoy', estadisticas.hoy, 'Actividad reciente'],
            ['Cambios en actas', estadisticas.actas, 'Entidad más auditada'],
            ['Usuarios activos', estadisticas.usuarios, 'Sesiones abiertas'],
          ].map(([titulo, valor, detalle]) => (
            <div
              key={titulo}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                {titulo}
              </p>
              <p className="mt-3 text-3xl font-bold text-slate-900">{valor}</p>
              <p className="mt-1 text-xs text-slate-500">{detalle}</p>
            </div>
          ))}
        </section>

        <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 p-5 md:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Actividad del sistema</h2>
                <p className="mt-1 text-sm text-slate-500">
                  Los registros nuevos aparecen automáticamente sin actualizar la página.
                </p>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700">
                <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
                En tiempo real
              </span>
            </div>
            {ultimaActualizacion && (
              <p className="mt-3 text-xs text-slate-400">
                Última sincronización: {ultimaActualizacion.toLocaleTimeString('es-MX')}
              </p>
            )}

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
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
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Boton variante="secundario" tamano="sm" onClick={limpiarFiltros}>
                Limpiar filtros
              </Boton>
              <span className="text-xs text-slate-500">
                Consulta registros actuales y anteriores por rango de fechas.
              </span>
            </div>
          </div>

          {cargando ? (
            <div className="flex min-h-52 items-center justify-center gap-2 text-sm text-slate-500">
              <Indicador /> Cargando actividad…
            </div>
          ) : entradasFiltradas.length === 0 ? (
            <div className="m-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
              <p className="text-sm font-semibold text-slate-700">No hay acciones para mostrar</p>
              <p className="mt-1 text-sm text-slate-500">
                Prueba con otros filtros o actualiza la información.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[860px] text-left">
                <thead className="bg-slate-50">
                  <tr className="border-b border-slate-200">
                    {['Acción', 'Usuario y rol', 'Entidad afectada', 'Fecha y hora', ''].map(
                      (titulo) => (
                        <th
                          key={titulo || 'detalle'}
                          className="px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500"
                        >
                          {titulo}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {entradasFiltradas.map((entrada) => {
                    const accion = etiquetaAccion(entrada.accion)
                    const abierta = entradaAbierta === entrada.id
                    return (
                      <Fragment key={entrada.id}>
                        <tr className="border-b border-slate-100 align-top">
                          <td className="px-5 py-4">
                            <Etiqueta tono={accion.tono}>{accion.texto}</Etiqueta>
                            <p className="mt-2 text-xs text-slate-500">
                              Evento #{entrada.id}
                            </p>
                          </td>
                          <td className="px-5 py-4">
                            <p className="text-sm font-semibold text-slate-800">
                              {entrada.usuario_nombre || `Usuario #${entrada.usuario_id || 'sistema'}`}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {entrada.usuario_rol ? etiquetaRol(entrada.usuario_rol) : 'Sistema'}
                            </p>
                          </td>
                          <td className="px-5 py-4">
                            <p className="text-sm font-medium capitalize text-slate-800">
                              {entrada.entidad}
                            </p>
                            <p className="mt-1 text-xs text-slate-500">
                              {resumenEntidad(entrada)}
                            </p>
                          </td>
                          <td className="whitespace-nowrap px-5 py-4 text-sm text-slate-600">
                            {entrada.created_at
                              ? FORMATO_FECHA.format(new Date(entrada.created_at))
                              : 'Fecha no disponible'}
                          </td>
                          <td className="px-5 py-4 text-right">
                            <button
                              type="button"
                              onClick={() => setEntradaAbierta(abierta ? null : entrada.id)}
                              className="rounded-lg px-3 py-2 text-xs font-semibold text-corporativo-600 transition hover:bg-corporativo-50"
                              aria-expanded={abierta}
                            >
                              {abierta ? 'Ocultar detalle' : 'Ver detalle'}
                            </button>
                          </td>
                        </tr>
                        {abierta && (
                          <tr className="border-b border-slate-100">
                            <td colSpan="5" className="bg-slate-50 px-5 pb-5">
                            <div className="grid gap-4 border-t border-slate-200 pt-4 md:grid-cols-2">
                              <div>
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                  Datos anteriores
                                </p>
                                <pre className="mt-2 max-h-52 overflow-auto rounded-lg bg-white p-3 text-xs text-slate-600 ring-1 ring-slate-200">
                                  {textoJson(entrada.datos_antes)}
                                </pre>
                              </div>
                              <div>
                                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                  Datos posteriores
                                </p>
                                <pre className="mt-2 max-h-52 overflow-auto rounded-lg bg-white p-3 text-xs text-slate-600 ring-1 ring-slate-200">
                                  {textoJson(entrada.datos_despues)}
                                </pre>
                              </div>
                              <div className="text-xs text-slate-500 md:col-span-2">
                                <span className="font-semibold">IP de origen:</span>{' '}
                                {entrada.ip_origen || 'No disponible'}
                                <span className="mx-3 text-slate-300">|</span>
                                <span className="font-semibold">ID de entidad:</span>{' '}
                                {entrada.entidad_id || 'No disponible'}
                              </div>
                            </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
