import { useCallback, useEffect, useMemo, useState } from 'react'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import PanelValidacion from '../components/actas/PanelValidacion.jsx'
import PanelVersiones from '../components/actas/PanelVersiones.jsx'
import VisorActa from '../components/actas/VisorActa.jsx'
import {
  analizarRevisionActa,
  decidirActa,
  descargarPdfGuardado,
  listarBitacora,
  mensajeDeError,
  obtenerBandejaActas,
} from '../api/client.js'
import { TIPOS_ASAMBLEA, etiquetaFlujoActa, etiquetaDe } from '../constants/catalogos.js'
import { descargarBlob } from '../utils/archivos.js'
import { formatearAccion, normalizarTexto, tonoDeAccion } from '../utils/bitacora.js'
import {
  diasHabilesEntre,
  fechaAprobacionActa,
  fechaCorta,
  inicioEtapaActa,
  marcaTiempo,
} from '../utils/formato.js'

const DIAS_HABILES_LIMITE_ATRASO = 5

const diasHabilesDeEtapa = (acta) => {
  const inicio = inicioEtapaActa(acta)
  return inicio ? diasHabilesEntre(inicio) : null
}

const CONFIGURACION = {
  capturista: {
    titulo: 'Mis actas',
    descripcion: 'Consulta el avance de tus actas y corrige las que fueron devueltas.',
  },
  revisor: {
    titulo: 'Revisión de actas',
    descripcion: 'Revisa cada nueva versión y apruébala para el Abogado o devuélvela con observaciones.',
  },
  abogado: {
    titulo: 'Aprobación de actas',
    descripcion: 'Revisa las actas del Revisor y las correcciones enviadas directamente a esta etapa.',
  },
}

function IndicadorRevisor({ titulo, valor, detalle, tono = 'verde', activo = false, onClick = null }) {
  const estilos = {
    verde: 'border-corporativo-200 bg-corporativo-50/60 text-corporativo-800',
    rojo: 'border-red-200 bg-red-50/70 text-red-800',
    neutro: 'border-slate-200 bg-white text-slate-800',
    ambar: 'border-amber-200 bg-amber-50/70 text-amber-900',
  }
  const clase = `rounded-xl border p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md motion-reduce:transform-none motion-reduce:transition-none ${
    estilos[tono] || estilos.verde
  } ${activo ? 'ring-2 ring-corporativo-500 ring-offset-1' : ''}`
  const contenido = (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide opacity-75">{titulo}</p>
        {activo ? (
          <span className="rounded-full bg-white/70 px-2 py-0.5 text-[10px] font-semibold">
            Vista activa
          </span>
        ) : null}
      </div>
      <p className="mt-2 text-2xl font-bold tracking-tight">{valor}</p>
      <p className="mt-1 text-xs opacity-75">{detalle}</p>
    </>
  )

  return onClick ? (
    <button
      type="button"
      className={`${clase} w-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-corporativo-600`}
      aria-pressed={activo}
      onClick={onClick}
    >
      {contenido}
    </button>
  ) : (
    <div className={clase}>{contenido}</div>
  )
}

function EstadoVacioRevisor() {
  const pasos = [
    ['01', 'Confirma la versión', 'Revisa el documento, su historial y las observaciones previas.'],
    ['02', 'Valida los datos', 'Usa el análisis asistido como apoyo; verifica personalmente cada hallazgo.'],
    ['03', 'Cierra la revisión', 'Envía al Abogado o devuelve el acta con cambios concretos.'],
  ]

  return (
    <section className="overflow-hidden rounded-2xl border border-corporativo-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-start gap-4 border-b border-corporativo-100 bg-corporativo-50/60 px-5 py-5 sm:px-7">
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-800" aria-hidden="true">
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m5 12 4 4L19 6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <div className="min-w-[220px] flex-1">
          <Etiqueta tono="exito">Bandeja al día</Etiqueta>
          <h2 className="mt-2 text-lg font-bold text-corporativo-800">
            No hay actas pendientes de revisión
          </h2>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-600">
            Las nuevas actas aparecerán aquí cuando el Capturista las envíe. Mientras tanto,
            puedes consultar los movimientos recientes y el flujo de revisión.
          </p>
        </div>
      </div>
      <div className="grid gap-3 p-5 sm:grid-cols-3 sm:p-6">
        {pasos.map(([numero, titulo, descripcion]) => (
          <article key={numero} className="rounded-xl border border-slate-200 bg-white p-4">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg bg-corporativo-100 text-xs font-bold text-corporativo-800">
              {numero}
            </span>
            <h3 className="mt-3 text-sm font-semibold text-slate-800">{titulo}</h3>
            <p className="mt-1 text-xs leading-5 text-slate-500">{descripcion}</p>
          </article>
        ))}
      </div>
      <p className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500 sm:px-7">
        Referencia de seguimiento: prioriza las actas con más de{' '}
        <strong>{DIAS_HABILES_LIMITE_ATRASO} días hábiles</strong> en revisión.
      </p>
    </section>
  )
}

function ActividadRecienteRevisor({
  entradas,
  cargando,
  error,
  onReintentar,
  mostrarToda,
  onCambiarVista,
}) {
  const entradasVisibles = mostrarToda ? entradas : entradas.slice(0, 6)

  return (
    <section className="tarjeta overflow-hidden" aria-label="Actividad reciente de actas">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-4 sm:px-5">
        <div>
          <h2 className="font-semibold text-slate-800">Movimientos recientes</h2>
          <p className="mt-1 text-xs text-slate-500">
            Actividad de actas de tu empresa, disponible para seguimiento del flujo.
          </p>
        </div>
        <Etiqueta tono="info">{entradas.length} movimientos</Etiqueta>
      </header>

      {cargando && !entradas.length ? (
        <p className="px-4 py-8 text-center text-sm text-slate-500" aria-live="polite">
          Cargando movimientos…
        </p>
      ) : null}
      {cargando && entradas.length ? (
        <p className="px-4 pt-3 text-xs text-slate-500" aria-live="polite">
          Actualizando movimientos…
        </p>
      ) : null}
      {error ? (
        <div className="flex flex-wrap items-center justify-between gap-3 p-4">
          <Alerta tono="error" titulo="No se pudo cargar la actividad" className="flex-1">
            {error}
          </Alerta>
          <Boton tamano="sm" variante="secundario" cargando={cargando} onClick={onReintentar}>
            Reintentar
          </Boton>
        </div>
      ) : null}
      {!cargando && !error && !entradas.length ? (
        <p className="px-4 py-8 text-center text-sm text-slate-500">
          Aún no hay movimientos de actas para mostrar.
        </p>
      ) : null}
      {entradas.length ? (
        <>
          <ol className="max-h-[28rem] divide-y divide-slate-100 overflow-y-auto">
            {entradasVisibles.map((entrada) => {
              const datos = entrada.datos_despues || entrada.datos_antes || {}
              const folio = datos.folio || `Acta #${entrada.entidad_id || 'general'}`
              const fecha = entrada.created_at ? new Date(entrada.created_at) : null
              const fechaValida = fecha && !Number.isNaN(fecha.getTime())
              return (
                <li
                  key={entrada.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-slate-50 motion-reduce:transition-none sm:px-5"
                >
                  <div className="flex min-w-0 items-start gap-3">
                    <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-corporativo-50 text-corporativo-700" aria-hidden="true">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
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
          {entradas.length > 6 ? (
            <div className="flex justify-end border-t border-slate-100 px-4 py-3 sm:px-5">
              <Boton tamano="sm" variante="fantasma" onClick={onCambiarVista}>
                {mostrarToda ? 'Mostrar menos' : `Ver los ${entradas.length} movimientos`}
              </Boton>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  )
}

export default function BandejaActas({ modo, onEditar = null }) {
  const [actas, setActas] = useState([])
  const [actaVisible, setActaVisible] = useState(null)
  const [versionesActaId, setVersionesActaId] = useState(null)
  const [comentarios, setComentarios] = useState({})
  const [analisisPorActa, setAnalisisPorActa] = useState({})
  const [analisisAbierto, setAnalisisAbierto] = useState({})
  const [cargando, setCargando] = useState(true)
  const [actividadReciente, setActividadReciente] = useState([])
  const [cargandoActividad, setCargandoActividad] = useState(modo === 'revisor')
  const [errorActividad, setErrorActividad] = useState(null)
  const [mostrarTodaActividad, setMostrarTodaActividad] = useState(false)
  const [busquedaActa, setBusquedaActa] = useState('')
  const [filtroTiempo, setFiltroTiempo] = useState('todas')
  const [ordenCola, setOrdenCola] = useState('antiguas')
  const [operando, setOperando] = useState(null)
  const [analizando, setAnalizando] = useState(null)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    if (modo === 'revisor') {
      setCargandoActividad(true)
      setErrorActividad(null)
    }
    try {
      if (modo === 'revisor') {
        const [resultadoBandeja, resultadoActividad] = await Promise.allSettled([
          obtenerBandejaActas(),
          listarBitacora({ entidad: 'actas', limite: 12 }),
        ])
        if (resultadoBandeja.status === 'rejected') {
          setActas([])
          setError(await mensajeDeError(resultadoBandeja.reason))
        } else {
          setActas(Array.isArray(resultadoBandeja.value) ? resultadoBandeja.value : [])
        }

        if (resultadoActividad.status === 'rejected') {
          setActividadReciente([])
          setErrorActividad(await mensajeDeError(resultadoActividad.reason))
        } else {
          setActividadReciente(
            Array.isArray(resultadoActividad.value) ? resultadoActividad.value : [],
          )
        }

      } else {
        setActas(await obtenerBandejaActas())
        setActividadReciente([])
        setErrorActividad(null)
        setCargandoActividad(false)
      }
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargando(false)
      if (modo === 'revisor') setCargandoActividad(false)
    }
  }, [modo])

  useEffect(() => {
    cargar()
  }, [cargar])

  const decidir = async (acta, accion) => {
    const comentario = comentarios[acta.id] || ''
    if (accion === 'devolver' && !comentario.trim()) {
      setError('Escribe las correcciones necesarias antes de devolver el acta.')
      return
    }
    setOperando(acta.id)
    setError(null)
    setAviso(null)
    try {
      const resultado = await decidirActa(acta.id, { accion, comentario })
      setAviso(
        accion === 'aprobar'
          ? `${acta.folio} pasó a ${etiquetaFlujoActa(resultado.estado_flujo)}.`
          : `${acta.folio} fue devuelta al Capturista con tus observaciones.`,
      )
      setComentarios((previo) => ({ ...previo, [acta.id]: '' }))
      await cargar()
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(null)
    }
  }

  const analizar = async (acta) => {
    if (analisisAbierto[acta.id]) {
      setAnalisisAbierto((previo) => ({ ...previo, [acta.id]: false }))
      return
    }
    if (analisisPorActa[acta.id]) {
      setAnalisisAbierto((previo) => ({ ...previo, [acta.id]: true }))
      return
    }

    setAnalizando(acta.id)
    setError(null)
    try {
      const resultado = await analizarRevisionActa(acta.id)
      setAnalisisPorActa((previo) => ({ ...previo, [acta.id]: resultado }))
      setAnalisisAbierto((previo) => ({ ...previo, [acta.id]: true }))
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setAnalizando(null)
    }
  }

  const agregarAnalisisAObservaciones = (acta, analisis) => {
    const validacion = analisis.validacion
    const texto = [
      `Análisis asistido de ${acta.folio} v${analisis.version_actual}: ${validacion.consistencia}`,
      ...validacion.hallazgos.map(
        (hallazgo) =>
          `- ${hallazgo.severidad}${hallazgo.campo ? ` · ${hallazgo.campo}` : ''}: ${hallazgo.mensaje}` +
          (hallazgo.sugerencia ? ` Sugerencia: ${hallazgo.sugerencia}` : ''),
      ),
      ...validacion.recomendaciones.map((recomendacion) => `- Recomendación: ${recomendacion}`),
    ].join('\n')
    setComentarios((previo) => ({
      ...previo,
      [acta.id]: [previo[acta.id], texto].filter(Boolean).join('\n\n').slice(0, 2000),
    }))
  }

  const descargar = async (acta) => {
    setOperando(acta.id)
    setError(null)
    try {
      const archivo = await descargarPdfGuardado(acta.id)
      descargarBlob(archivo.blob, archivo.nombreArchivo)
      setAviso(`PDF final de ${acta.folio} descargado.`)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(null)
    }
  }

  const filas = useMemo(
    () =>
      modo === 'revisor'
        ? actas.filter((acta) => acta.estado_flujo === 'revision')
        : modo === 'abogado'
          ? actas.filter((acta) => ['abogado', 'aprobada'].includes(acta.estado_flujo))
          : actas,
    [actas, modo],
  )

  const filasFiltradas = useMemo(() => {
    if (modo !== 'revisor') return filas
    const termino = normalizarTexto(busquedaActa)
    return filas
      .filter((acta) => {
        const texto = normalizarTexto(
          [
            acta.folio,
            acta.sociedad,
            etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea),
            acta.comentario_revision,
          ].join(' '),
        )
        const dias = diasHabilesDeEtapa(acta)
        const atrasada = dias !== null && dias > DIAS_HABILES_LIMITE_ATRASO
        return (
          (!termino || texto.includes(termino)) &&
          (filtroTiempo === 'todas' ||
            (filtroTiempo === 'atrasadas' && atrasada) ||
            (filtroTiempo === 'en_plazo' && !atrasada))
        )
      })
      .sort((primera, segunda) => {
        const diasPrimera = diasHabilesDeEtapa(primera) ?? 0
        const diasSegunda = diasHabilesDeEtapa(segunda) ?? 0
        return ordenCola === 'antiguas'
          ? diasSegunda - diasPrimera
          : diasPrimera - diasSegunda
      })
  }, [busquedaActa, filtroTiempo, filas, modo, ordenCola])

  const resumenRevision = useMemo(() => {
    const edades = filas.map(diasHabilesDeEtapa).filter((dias) => dias !== null)
    const atrasadas = edades.filter((dias) => dias > DIAS_HABILES_LIMITE_ATRASO).length
    const promedio = edades.length
      ? (edades.reduce((total, dias) => total + dias, 0) / edades.length).toFixed(1)
      : '—'
    const reenviadas = filas.filter((acta) =>
      (acta.historial_revision || []).some((evento) => evento.accion === 'reenviar'),
    ).length
    return { pendientes: filas.length, atrasadas, promedio, reenviadas }
  }, [filas])

  const configuracion = CONFIGURACION[modo]
  const hayFiltrosActivos =
    Boolean(busquedaActa) || filtroTiempo !== 'todas' || ordenCola !== 'antiguas'

  return (
    <div className="space-y-5">
      {modo === 'revisor' ? (
        <header className="flex flex-wrap items-center justify-between gap-4 rounded-2xl bg-corporativo-800 px-5 py-5 text-white shadow-sm sm:px-7">
          <div className="max-w-2xl">
            <Etiqueta tono="info" className="border-white/20 bg-white/10 text-white">
              Centro de revisión
            </Etiqueta>
            <h1 className="mt-2 text-2xl font-bold tracking-tight">{configuracion.titulo}</h1>
            <p className="mt-1 text-sm text-white/80">{configuracion.descripcion}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-white/20 bg-white/10 px-3 py-2 text-xs font-medium">
              Objetivo: {DIAS_HABILES_LIMITE_ATRASO} días hábiles
            </span>
            <Boton variante="secundario" cargando={cargando} onClick={cargar}>
              Actualizar bandeja
            </Boton>
          </div>
        </header>
      ) : (
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-corporativo-700">{configuracion.titulo}</h1>
            <p className="text-sm text-slate-500">{configuracion.descripcion}</p>
          </div>
          <Boton variante="secundario" cargando={cargando} onClick={cargar}>Actualizar</Boton>
        </header>
      )}

      {modo === 'revisor' ? (
        <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="Resumen de revisión">
          <IndicadorRevisor
            titulo="Pendientes"
            valor={resumenRevision.pendientes}
            detalle="Actas en tu bandeja"
            tono="verde"
            activo={filtroTiempo === 'todas'}
            onClick={() => setFiltroTiempo('todas')}
          />
          <IndicadorRevisor
            titulo="Fuera del objetivo"
            valor={resumenRevision.atrasadas}
            detalle={`Más de ${DIAS_HABILES_LIMITE_ATRASO} días hábiles`}
            tono="rojo"
            activo={filtroTiempo === 'atrasadas'}
            onClick={() => setFiltroTiempo('atrasadas')}
          />
          <IndicadorRevisor
            titulo="Promedio en revisión"
            valor={resumenRevision.pendientes ? `${resumenRevision.promedio} días` : '—'}
            detalle="Días hábiles en la etapa actual"
            tono="neutro"
          />
          <IndicadorRevisor
            titulo="Con reenvíos"
            valor={resumenRevision.reenviadas}
            detalle="Pendientes con correcciones previas"
            tono="ambar"
          />
        </section>
      ) : null}

      {error ? <Alerta tono="error" titulo="No se pudo completar la operación">{error}</Alerta> : null}
      {aviso ? <Alerta tono="exito">{aviso}</Alerta> : null}

      {modo === 'revisor' ? (
        <section className="tarjeta space-y-4 p-4 sm:p-5" aria-label="Filtros de la cola de revisión">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <h2 className="font-semibold text-slate-800">Cola de revisión</h2>
              <p className="mt-1 text-xs text-slate-500">
                Busca por folio, sociedad, tipo de asamblea u observación; prioriza las más antiguas.
              </p>
            </div>
            <Etiqueta tono={filasFiltradas.length ? 'info' : 'neutral'}>
              {filasFiltradas.length} de {filas.length} actas
            </Etiqueta>
          </div>
          <div className="grid gap-3 md:grid-cols-[minmax(220px,1fr)_190px_190px_auto] md:items-end">
            <div>
              <label className="etiqueta-campo" htmlFor="buscar-acta-revision">Buscar acta</label>
              <input
                id="buscar-acta-revision"
                className="campo"
                type="search"
                value={busquedaActa}
                onChange={(evento) => setBusquedaActa(evento.target.value)}
                placeholder="Folio, sociedad u observación"
              />
            </div>
            <div>
              <label className="etiqueta-campo" htmlFor="filtro-tiempo-revision">Antigüedad</label>
              <select
                id="filtro-tiempo-revision"
                className="campo"
                value={filtroTiempo}
                onChange={(evento) => setFiltroTiempo(evento.target.value)}
              >
                <option value="todas">Todas las pendientes</option>
                <option value="atrasadas">Fuera del objetivo</option>
                <option value="en_plazo">Dentro del objetivo</option>
              </select>
            </div>
            <div>
              <label className="etiqueta-campo" htmlFor="orden-revision">Ordenar por</label>
              <select
                id="orden-revision"
                className="campo"
                value={ordenCola}
                onChange={(evento) => setOrdenCola(evento.target.value)}
              >
                <option value="antiguas">Más antiguas primero</option>
                <option value="recientes">Más recientes primero</option>
              </select>
            </div>
            <Boton
              variante="fantasma"
              disabled={!hayFiltrosActivos}
              onClick={() => {
                setBusquedaActa('')
                setFiltroTiempo('todas')
                setOrdenCola('antiguas')
              }}
            >
              Limpiar filtros
            </Boton>
          </div>
        </section>
      ) : null}

      {cargando && !actas.length ? (
        <section className="tarjeta animate-pulse p-6 text-sm text-slate-500" aria-live="polite">
          Cargando actas…
        </section>
      ) : modo === 'revisor' && !filas.length ? (
        <EstadoVacioRevisor />
      ) : !filasFiltradas.length ? (
        modo === 'revisor' ? (
          <section className="tarjeta flex flex-col items-center gap-3 p-8 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-50 text-amber-700" aria-hidden="true">
              <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8">
                <circle cx="11" cy="11" r="7" />
                <path d="m16 16 4 4M8 11h6" strokeLinecap="round" />
              </svg>
            </span>
            <div>
              <h2 className="font-semibold text-slate-800">No hay coincidencias</h2>
              <p className="mt-1 text-sm text-slate-500">
                Cambia la búsqueda o los filtros para volver a ver las actas pendientes.
              </p>
            </div>
            <Boton
              variante="secundario"
              onClick={() => {
                setBusquedaActa('')
                setFiltroTiempo('todas')
              }}
            >
              Mostrar todas las pendientes
            </Boton>
          </section>
        ) : (
          <section className="tarjeta p-6 text-sm text-slate-500">
            No hay actas en esta bandeja por el momento.
          </section>
          )
      ) : (
        <section className="space-y-3">
          {filasFiltradas.map((acta) => {
            const pendienteRevision = modo === 'revisor' && acta.estado_flujo === 'revision'
            const pendienteAbogado = modo === 'abogado' && acta.estado_flujo === 'abogado'
            const puedeDecidir = pendienteRevision || pendienteAbogado
            const puedeAnalizar = modo === 'revisor' || modo === 'abogado'
            const analisis = analisisPorActa[acta.id]
            const estaAbierto = Boolean(analisisAbierto[acta.id])
            const ultimaDevolucion = [...(acta.historial_revision || [])]
              .reverse()
              .find((evento) => evento.accion === 'devolver')
            const devolvio = ultimaDevolucion?.etapa === 'abogado' ? 'Abogado' : 'Revisor'
            const etapaInicial = inicioEtapaActa(acta)
            const diasEnEtapa = etapaInicial ? diasHabilesEntre(etapaInicial) : null
            const aprobadaEl = fechaAprobacionActa(acta)
            const diasHastaAprobacion = aprobadaEl && acta.created_at
              ? diasHabilesEntre(acta.created_at, aprobadaEl)
              : null
            const esAtrasada = ['revision', 'abogado', 'con_errores'].includes(acta.estado_flujo)
              && diasEnEtapa > DIAS_HABILES_LIMITE_ATRASO
            const etapaDevolucion = acta.estado_flujo === 'con_errores'
              ? [...(acta.historial_revision || [])]
                .reverse()
                .find((evento) => evento.accion === 'devolver')?.etapa
              : null
            const pasoActivo = acta.estado_flujo === 'aprobada'
              ? 3
              : acta.estado_flujo === 'abogado' || etapaDevolucion === 'abogado'
                ? 1
                : 0
            return (
              <article
                key={acta.id}
                className={`tarjeta space-y-3 p-4 ${pendienteRevision ? 'border-l-4 border-l-corporativo-600' : ''}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-corporativo-600">{acta.folio} · v{acta.version}</p>
                    <h2 className="mt-1 font-semibold text-slate-800">{acta.sociedad}</h2>
                    <p className="text-sm text-slate-500">
                      {etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea)} · {fechaCorta(acta.fecha)}
                    </p>
                  </div>
                  <Etiqueta tono={acta.estado_flujo === 'aprobada' ? 'exito' : acta.estado_flujo === 'con_errores' ? 'advertencia' : 'info'}>
                    {etiquetaFlujoActa(acta.estado_flujo)}
                  </Etiqueta>
                </div>

                <section aria-label={`Seguimiento de ${acta.folio}`} className="rounded-lg border border-slate-100 bg-slate-50/70 px-3 py-3">
                  <ol className="grid grid-cols-3 gap-2 text-center text-[11px]">
                    {['Revisión', 'Abogado', 'Aprobación'].map((etapa, indice) => (
                      <li key={etapa} className="flex flex-col items-center gap-1">
                        <span
                          className={`flex h-6 w-6 items-center justify-center rounded-full font-semibold ${
                            indice < pasoActivo
                              ? 'bg-emerald-100 text-emerald-700'
                              : indice === pasoActivo && acta.estado_flujo !== 'aprobada'
                                ? 'bg-amber-100 text-amber-800 ring-1 ring-amber-300'
                                : acta.estado_flujo === 'aprobada'
                                  ? 'bg-emerald-100 text-emerald-700'
                                  : 'bg-white text-slate-400 ring-1 ring-slate-200'
                          }`}
                        >
                          {indice < pasoActivo || acta.estado_flujo === 'aprobada' ? '✓' : indice + 1}
                        </span>
                        <span className={indice <= pasoActivo ? 'font-medium text-slate-700' : 'text-slate-400'}>
                          {etapa}
                        </span>
                      </li>
                    ))}
                  </ol>
                  <p className="mt-3 text-xs text-slate-600">
                    {acta.estado_flujo === 'aprobada'
                      ? diasHastaAprobacion !== null
                        ? `Tiempo total hasta aprobación: ${diasHastaAprobacion} días hábiles.`
                        : 'Acta aprobada.'
                      : `Tiempo en etapa actual: ${diasEnEtapa ?? 0} días hábiles.`}
                  </p>
                  {pendienteRevision ? (
                    <Etiqueta tono={esAtrasada ? 'advertencia' : 'exito'} className="mt-2">
                      {esAtrasada ? 'Atención prioritaria' : 'Dentro del objetivo'}
                    </Etiqueta>
                  ) : null}
                  {acta.estado_flujo === 'con_errores' ? (
                    <p className="mt-1 text-xs font-medium text-amber-800">Correcciones pendientes del Capturista.</p>
                  ) : null}
                  {esAtrasada ? (
                    <Etiqueta tono="advertencia" className="mt-2">
                      Atrasada · más de {DIAS_HABILES_LIMITE_ATRASO} días hábiles
                    </Etiqueta>
                  ) : null}
                </section>

                {acta.comentario_revision ? (
                  <Alerta
                    tono="advertencia"
                    titulo={modo === 'capturista' ? `Observaciones del ${devolvio}` : 'Correcciones solicitadas'}
                  >
                    {acta.comentario_revision}
                  </Alerta>
                ) : null}

                {acta.historial_revision?.length ? (
                  <details className="rounded-lg border border-slate-200 px-3 py-2">
                    <summary className="cursor-pointer text-xs font-semibold text-corporativo-700">
                      Historial de revisión ({acta.historial_revision.length} movimientos)
                    </summary>
                    <ol className="mt-2 space-y-2">
                      {acta.historial_revision.map((evento, indice) => (
                        <li key={`${evento.version}-${indice}`} className="border-l-2 border-slate-200 pl-3 text-xs text-slate-600">
                          <p>
                            {evento.accion === 'aprobar' ? 'Aprobó' : evento.accion === 'devolver' ? 'Devolvió' : 'Reenvió'}
                            {' · '}{evento.rol} · {evento.usuario} · versión {evento.version}
                            {evento.creado_en ? ` · ${marcaTiempo(evento.creado_en)}` : ''}
                          </p>
                          {evento.comentario ? <p className="mt-1">{evento.comentario}</p> : null}
                        </li>
                      ))}
                    </ol>
                  </details>
                ) : null}

                {puedeDecidir ? (
                  <div>
                    <label className="etiqueta-campo" htmlFor={`comentario-${acta.id}`}>
                      Observaciones (obligatorias si devuelves el acta)
                    </label>
                    <textarea
                      id={`comentario-${acta.id}`}
                      className="campo"
                      rows={3}
                      maxLength={2000}
                      value={comentarios[acta.id] || ''}
                      onChange={(evento) =>
                        setComentarios((previo) => ({ ...previo, [acta.id]: evento.target.value }))
                      }
                      placeholder="Detalla los cambios que debe realizar el Capturista."
                    />
                  </div>
                ) : null}

                <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-3">
                  <Boton variante="secundario" onClick={() => setActaVisible(acta)}>Ver acta</Boton>
                  {puedeAnalizar ? (
                    <Boton
                      variante="secundario"
                      cargando={analizando === acta.id}
                      disabled={operando === acta.id}
                      aria-expanded={estaAbierto}
                      aria-controls={analisis ? `analisis-${acta.id}` : undefined}
                      onClick={() => analizar(acta)}
                    >
                      {estaAbierto ? 'Ocultar análisis' : analisis ? 'Mostrar análisis' : 'Analizar con IA'}
                    </Boton>
                  ) : null}
                  {modo === 'abogado' ? (
                    <Boton
                      variante="fantasma"
                      onClick={() => setVersionesActaId((actual) => actual === acta.id ? null : acta.id)}
                    >
                      {versionesActaId === acta.id ? 'Ocultar versiones' : 'Ver versiones'}
                    </Boton>
                  ) : null}
                  {modo === 'capturista' && acta.estado_flujo === 'con_errores' && onEditar ? (
                    <Boton variante="primario" onClick={() => onEditar(acta)}>Editar y corregir</Boton>
                  ) : null}
                  {puedeDecidir ? (
                    <>
                      <Boton
                        variante="peligro"
                        disabled={operando === acta.id}
                        onClick={() => decidir(acta, 'devolver')}
                      >
                        Devolver con errores
                      </Boton>
                      <Boton
                        variante="primario"
                        cargando={operando === acta.id}
                        onClick={() => decidir(acta, 'aprobar')}
                      >
                        {pendienteRevision
                          ? 'Marcar revisada y enviar al Abogado'
                          : 'Aprobar acta'}
                      </Boton>
                    </>
                  ) : null}
                  {modo === 'abogado' && acta.estado_flujo === 'aprobada' ? (
                    <Boton
                      variante="primario"
                      cargando={operando === acta.id}
                      onClick={() => descargar(acta)}
                    >
                      Descargar PDF final
                    </Boton>
                  ) : null}
                </div>
                {analisis && estaAbierto ? (
                  <section
                    id={`analisis-${acta.id}`}
                    className="space-y-3 rounded-xl border border-corporativo-100 bg-corporativo-50/40 p-4"
                  >
                    <div>
                      <h3 className="text-sm font-semibold text-corporativo-700">
                        Análisis asistido · versión {analisis.version_actual}
                      </h3>
                      <p className="mt-1 text-xs text-slate-600">
                        {analisis.version_comparada
                          ? `Comparada con la versión ${analisis.version_comparada}.`
                          : 'No hay una versión anterior para comparar.'}
                        {' '}El resultado es una ayuda y no sustituye la revisión profesional.
                      </p>
                    </div>
                    {analisis.cambios.length ? (
                      <p className="text-sm text-slate-700">
                        <span className="font-semibold">Secciones modificadas:</span>{' '}
                        {analisis.cambios.join(', ')}.
                      </p>
                    ) : null}
                    <PanelValidacion validacion={analisis.validacion} />
                    {puedeDecidir ? (
                      <div className="flex justify-end">
                        <Boton
                          tamano="sm"
                          variante="secundario"
                          onClick={() => agregarAnalisisAObservaciones(acta, analisis)}
                        >
                          Agregar análisis a observaciones
                        </Boton>
                      </div>
                    ) : null}
                  </section>
                ) : null}
                <p className="text-right text-xs text-slate-400">
                  Última actualización: {marcaTiempo(acta.updated_at)}
                </p>
                {modo === 'abogado' && versionesActaId === acta.id ? (
                  <PanelVersiones acta={acta} soloLectura />
                ) : null}
              </article>
            )
          })}
        </section>
      )}

      {modo === 'revisor' ? (
        <ActividadRecienteRevisor
          entradas={actividadReciente}
          cargando={cargandoActividad}
          error={errorActividad}
          onReintentar={cargar}
          mostrarToda={mostrarTodaActividad}
          onCambiarVista={() => setMostrarTodaActividad((actual) => !actual)}
        />
      ) : null}

      {actaVisible ? (
        <VisorActa
          acta={actaVisible}
          documentoInicial={actaVisible}
          onCerrar={() => setActaVisible(null)}
        />
      ) : null}
    </div>
  )
}
