import { useEffect, useMemo, useRef, useState } from 'react'
import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import IconoAsistenteIA from '../ui/IconoAsistenteIA.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../ui/Tarjeta.jsx'
import { chatearAsistente, descargarPdfGuardado, descargarBlob, mensajeDeError } from '../../api/client.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { etiquetaRol, tieneAcceso } from '../../constants/roles.js'

const SUGERENCIAS_POR_ROL = {
  capturista: [
    'Quiero crear un acta',
    'Qué tipos de acta hay?',
    'Cuantas actas hay por estatus?',
    'Qué actas llevan más de 5 días hábiles?',
  ],
  revisor: [
    'Qué actas llevan más de 5 días hábiles en revisión?',
    'Cuantas actas hay por estatus?',
    'Valida el acta 1',
    'Qué puedo revisar en un acta?',
  ],
  abogado_responsable: [
    'Qué actas llevan más de 5 días hábiles pendientes de aprobación?',
    'Cuanto tarda en promedio la aprobación?',
    'Valida el acta 1',
    'Cuantas actas hay por estatus?',
  ],
  Administrador: [
    'Cuantas actas hay por estatus?',
    'Qué actas llevan más de 5 días hábiles?',
    'Qué actas están por vencer?',
    'Estatus de PGAC-2026-0001',
  ],
  SuperAdministrador: [
    'Cuantas actas hay por estatus?',
    'Qué actas llevan más de 5 días hábiles?',
    'Cuanto tarda en promedio la aprobación?',
    'Estatus de PGAC-2026-0001',
  ],
}
const SUGERENCIAS_EDICION = [
  'Quiero cambiar la fecha',
  'Quiero cambiar el lugar',
  'Quiero cambiar al presidente',
  'Quiero cambiar las observaciones',
]

const ETIQUETAS_CAMPO = {
  tipo_asamblea: 'Tipo de acta',
  tipo_sociedad: 'Tipo de sociedad',
  'tipo de sociedad': 'Tipo de sociedad',
  sociedad: 'Razón social',
  'sociedad (razon social)': 'Razón social',
  'rfc de la sociedad': 'RFC de la sociedad',
  fecha: 'Fecha',
  'fecha (AAAA-MM-DD)': 'Fecha',
  lugar: 'Lugar',
  presidente: 'Presidente',
  secretario: 'Secretario',
  asistentes: 'Asistentes y acciones',
  'asistentes y acciones': 'Asistentes y acciones',
  orden_y_acuerdos: 'Orden del día y acuerdos',
  'orden del dia y acuerdos': 'Orden del día y acuerdos',
}

function mostrarValor(valor) {
  if (typeof valor === 'boolean') return valor ? 'Sí' : 'No'
  if (valor && typeof valor === 'object') return JSON.stringify(valor)
  return String(valor ?? '—')
}

function sugerenciasPara(rol, mensaje, modoEdicion, sesionActiva) {
  if (modoEdicion) return SUGERENCIAS_EDICION
  if (sesionActiva || mensaje?.confirmacionCreacion) return []
  if (mensaje?.control) {
    return [
      `Estatus de ${mensaje.control.folio}`,
      'Quiero crear un acta',
      'Cuantas actas hay por estatus?',
    ]
  }
  if (mensaje?.acta) {
    return [
      `Valida el acta ${mensaje.acta.id}`,
      `Versiones del acta ${mensaje.acta.id}`,
      'Qué actas llevan más de 5 días hábiles?',
    ]
  }
  if (mensaje?.intencion === 'tiempos') {
    return [
      'Cuanto tarda en promedio la aprobación?',
      'Cuantas actas hay por estatus?',
    ]
  }
  return SUGERENCIAS_POR_ROL[rol] || SUGERENCIAS_POR_ROL.capturista
}

function burbujaClase(origen) {
  return origen === 'usuario'
    ? 'ml-auto border-transparent bg-corporativo-700 text-white'
    : 'mr-auto border-corporativo-100 bg-corporativo-50 text-slate-700 ring-1 ring-inset ring-corporativo-100'
}

export default function AsistenteChat({
  modo = 'pagina',
  titulo = null,
  onUsarBorrador = null,
  actaId = null,
  modoEdicion = false,
  onAplicarCambios = null,
  onEditarActa = null,
  onIrAMisActas = null,
  datosAsistente = null,
  abierto,
  onCambiarAbierto = null,
}) {
  const { usuario } = useAuth()
  const rol = usuario?.rol || 'capturista'
  const flotante = modo === 'burbuja'
  const puedeCambiarEstatus = tieneAcceso(rol, 'abogado_responsable')
  const [abiertoInterno, setAbiertoInterno] = useState(false)
  const estaAbierto = abierto ?? abiertoInterno
  const cambiarAbierto = (valor) => {
    setAbiertoInterno(valor)
    onCambiarAbierto?.(valor)
  }
  const [mensajes, setMensajes] = useState(() => [
    {
      origen: 'ia',
      texto: modoEdicion
        ? `Edición asistida del acta ${actaId}. Indícame qué campo quieres cambiar; el tipo de acta y la sociedad permanecen bloqueados.`
        : `Hola, ${etiquetaRol(rol)}. Puedo ayudarte con las tareas de actas de tu rol: consultar estatus, revisar tiempos y, si corresponde, crear o validar documentos. Las decisiones legales siguen requiriendo revisión humana.`,
    },
  ])
  const [entrada, setEntrada] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)
  const [sesionId, setSesionId] = useState(null)
  const [descargando, setDescargando] = useState(false)
  const [cambioEnRevision, setCambioEnRevision] = useState(null)
  const finRef = useRef(null)
  const compacto = modo === 'compacto' || flotante
  const ultimoMensajeIA = [...mensajes].reverse().find((mensaje) => mensaje.origen === 'ia')
  const ejemplos = useMemo(
    () => sugerenciasPara(rol, ultimoMensajeIA, modoEdicion, Boolean(sesionId)),
    [rol, ultimoMensajeIA, modoEdicion, sesionId],
  )

  useEffect(() => {
    const movimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    finRef.current?.scrollIntoView({
      behavior: movimientoReducido ? 'auto' : 'smooth',
      block: 'end',
    })
  }, [mensajes, cargando])

  const enviar = async (libre = null) => {
    const texto = (libre ?? entrada).trim()
    if (!texto || cargando) return
    setEntrada('')
    setError(null)
    setMensajes((p) => [...p, { origen: 'usuario', texto }])
    setCargando(true)
    try {
      const r = await chatearAsistente(texto, {
        sesionId,
        actaId: modoEdicion ? actaId : null,
        modo: modoEdicion ? 'edicion' : 'general',
      })
      if (r.sesion_id) setSesionId(r.sesion_id)
      // Sesión cerrada (acta generada o cancelada): libera para empezar otra.
      if (r.control_acta || r.intencion === 'cancelar_creacion') setSesionId(null)
      setMensajes((p) => [...p, {
        origen: 'ia', texto: r.respuesta, acta: r.acta || null,
        acciones: r.acciones || [], borrador: r.texto_borrador || null,
        sesion: r.sesion_id || null, tipos: r.tipos_acta || null,
        control: r.control_acta || null, progreso: r.progreso || null,
        tipoSociedad: r.tipo_sociedad || null,
        marcoNormativo: r.marco_normativo || null,
        intencion: r.intencion || null,
        confirmacionCreacion: Boolean(r.confirmacion_creacion),
        resumenCreacion: r.resumen_creacion || null,
        catalogoCompletoDisponible: Boolean(r.catalogo_completo_disponible),
        campoSolicitado: r.campo_solicitado || null,
        actaId: r.acta_id || r.acta?.id || null,
        camposEdicion: r.campos_edicion || null,
        cambiosPropuestos: r.cambios_propuestos || null,
      }])
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }

  const descargar = async (actaId, nombre) => {
    if (!actaId || descargando) return
    setDescargando(true)
    try {
      const r = await descargarPdfGuardado(actaId)
      descargarBlob(r.blob, nombre || r.nombreArchivo || `acta_${actaId}.pdf`)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setDescargando(false)
    }
  }

  const accionar = (a) => {
    if (!a) return
    if (a.accion === 'ayuda') { enviar('Ayuda'); return }
    if (a.accion === 'resumen') { enviar('Cuantas actas hay por estatus?'); return }
    if (a.accion === 'validar' && a.acta_id) { enviar(`Valida el acta ${a.acta_id}`); return }
    if (a.accion === 'versiones' && a.acta_id) { enviar(`Versiones del acta ${a.acta_id}`); return }
    if (a.accion === 'descargar_pdf' && a.acta_id) { descargar(a.acta_id); return }
    if (a.accion === 'editar_acta' && a.acta_id) { onEditarActa?.(a.acta_id); return }
    if (a.accion === 'ir_mis_actas') { onIrAMisActas?.(); return }
    if (a.accion === 'aprobar' && a.acta_id) { enviar(`Pasa el acta ${a.acta_id} a ${a.estatus || 'revision'}`) }
  }

  if (flotante && !estaAbierto) {
    return (
      <div className="fixed bottom-5 right-5 z-[70]">
        <button
          type="button"
          aria-label={sesionId ? 'Continuar creación de acta' : 'Abrir asistente IA'}
          aria-expanded="false"
          onClick={() => cambiarAbierto(true)}
          className="pgac-assistant-bubble group relative flex h-16 w-16 items-center justify-center rounded-full bg-corporativo-700 text-white shadow-xl shadow-corporativo-800/25 ring-4 ring-white transition hover:bg-corporativo-800 focus:outline-none focus-visible:ring-4 focus-visible:ring-corporativo-300 motion-reduce:transition-none"
        >
          <IconoAsistenteIA className="h-7 w-7" />
          <span className={`absolute -right-0.5 -top-0.5 h-4 w-4 rounded-full border-2 border-white ${sesionId ? 'bg-amber-400' : 'bg-emerald-400'}`} />
          <span className="pointer-events-none absolute bottom-full right-0 mb-3 translate-y-1 whitespace-nowrap rounded-lg bg-corporativo-800 px-3 py-1.5 text-xs font-semibold text-white opacity-0 shadow-lg transition group-hover:translate-y-0 group-hover:opacity-100 group-focus-visible:translate-y-0 group-focus-visible:opacity-100">
            {sesionId ? 'Continuar creación de acta' : 'Abrir asistente'}
          </span>
        </button>
      </div>
    )
  }

  return (
    <div className={flotante
      ? 'pgac-assistant-panel fixed bottom-5 right-5 z-[70] flex h-[min(88vh,720px)] w-[min(94vw,430px)] flex-col overflow-hidden rounded-3xl border border-corporativo-100 bg-slate-50 shadow-2xl shadow-corporativo-800/20'
      : `w-full space-y-4 bg-slate-100 ${compacto ? 'min-h-0' : 'min-h-[70vh]'}`}>
      {flotante ? (
        <div className="flex shrink-0 items-center justify-between bg-corporativo-700 px-4 py-3 text-white">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-white ring-1 ring-white/25">
              <IconoAsistenteIA className="h-5 w-5" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-bold">Asistente PGAC</p>
              <p className="truncate text-[11px] text-corporativo-50">
                {sesionId ? 'Creación de acta en curso' : `${etiquetaRol(rol)} · conversación activa`}
              </p>
            </div>
          </div>
          <button
            type="button"
            aria-label="Minimizar asistente"
            title="Minimizar"
            onClick={() => cambiarAbierto(false)}
            className="ml-2 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/10 text-xl leading-none transition hover:bg-white/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
          >
            <span aria-hidden="true">−</span>
          </button>
        </div>
      ) : null}
      {!compacto ? (
        <header className="mb-2">
          <h1 className="text-lg font-semibold text-corporativo-700 flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-corporativo-100 text-corporativo-700">
              <IconoAsistenteIA className="h-4 w-4" />
            </span>
            {titulo || `Asistente IA · ${etiquetaRol(rol)}`}
          </h1>
          <p className="text-sm text-slate-500">Opciones y consultas adaptadas a tu rol y al contexto de la conversación.</p>
        </header>
      ) : null}
      {sesionId && !modoEdicion ? (
        <Alerta tono="info" titulo="Creación de acta en curso">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span>
              {ultimoMensajeIA?.campoSolicitado
                ? `Dato pendiente: ${ETIQUETAS_CAMPO[ultimoMensajeIA.campoSolicitado] || ultimoMensajeIA.campoSolicitado}.`
                : ultimoMensajeIA?.tipos?.length
                  ? 'Selecciona un tipo de acta para continuar.'
                  : 'Responde el dato pedido para continuar.'}
              {ultimoMensajeIA?.progreso?.total
                ? ` ${ultimoMensajeIA.progreso.completados}/${ultimoMensajeIA.progreso.total} datos reunidos.`
                : ''}
            </span>
            <button
              type="button"
              disabled={cargando}
              onClick={() => enviar('Cancelar')}
              className="rounded-lg border border-corporativo-200 bg-white px-3 py-1.5 text-xs font-semibold text-corporativo-700 transition hover:bg-corporativo-50 disabled:opacity-50"
            >
              Cancelar creación
            </button>
          </div>
        </Alerta>
      ) : null}
      {error ? <Alerta tono="error" titulo="Sin conexión al asistente">{error}</Alerta> : null}
      {modoEdicion && datosAsistente?.respuestas?.length ? (
        <details className="rounded-xl border border-corporativo-100 bg-white px-4 py-3 text-sm">
          <summary className="cursor-pointer font-semibold text-corporativo-700">
            Respuestas originales guardadas por el asistente
          </summary>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-slate-600">
            {datosAsistente.respuestas.map((item, indice) => (
              <li key={`${item.campo}-${indice}`}>
                <span className="font-medium">{item.pregunta}</span>
                <span className="block whitespace-pre-line">{item.respuesta}</span>
              </li>
            ))}
          </ol>
        </details>
      ) : null}

      <div className={`relative flex min-h-0 flex-1 flex-col overflow-hidden bg-white transition-shadow ${
        flotante ? 'border-0' : 'rounded-3xl border'
      } ${
        cargando
          ? 'border-corporativo-200 shadow-md ring-2 ring-corporativo-100'
          : flotante ? 'shadow-none' : 'border-slate-200 shadow-sm'
      }`}>
        <div className="relative z-10 flex h-full flex-col overflow-hidden">
          <Tarjeta className={`border-none shadow-none p-0 mb-0 ${flotante ? 'flex min-h-0 flex-1 flex-col' : ''}`}>
            {!flotante ? (
              <TarjetaEncabezado
                titulo={rol === 'revisor'
                  ? 'Asistencia para revisión'
                  : rol === 'abogado_responsable'
                    ? 'Asistencia para aprobación'
                    : '¿Qué haremos hoy?'}
                descripcion={modoEdicion ? 'Edición asistida con confirmación antes de aplicar cambios' : 'Consultas y acciones según tu rol'}
                acciones={<Etiqueta tono="info">{etiquetaRol(rol)}</Etiqueta>}
              />
            ) : null}
            <TarjetaCuerpo className={`p-0 ${flotante ? 'flex min-h-0 flex-1 flex-col' : ''}`}>
          <div
            className={`flex-1 overflow-y-auto p-6 space-y-5 ${
              flotante
                ? 'min-h-0 p-4'
                : compacto
                  ? 'min-h-[240px] max-h-[440px]'
                  : 'min-h-[320px] max-h-[520px]'
            }`}
            role="log"
            aria-live="polite"
            aria-relevant="additions text"
          >
            {mensajes.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm">
                <p className="font-medium">Sin mensajes aún</p>
                <p className="mt-1 text-xs">Escribe «Quiero crear un acta» para comenzar.</p>
              </div>
            ) : (
              <>
                {mensajes.map((m, i) => (
                  <div key={i} className={`pgac-chat-message max-w-[90%] rounded-2xl px-4 py-3.5 text-sm ${burbujaClase(m.origen)} shadow-sm border`}>
                    <p className="whitespace-pre-line leading-relaxed">{m.texto}</p>
                    {m.marcoNormativo || m.tipoSociedad ? (
                      <div className="mt-3 rounded-lg border border-corporativo-100 bg-corporativo-50 px-3 py-2 text-xs text-corporativo-800">
                        <p className="font-semibold">Marco de revisión</p>
                        <p>
                          Sociedad: {m.tipoSociedad || 'pendiente'} · Ordenamiento:{' '}
                          {m.marcoNormativo || 'pendiente de seleccionar'}
                        </p>
                      </div>
                    ) : null}
                    {m.progreso && m.progreso.total > 0 ? (
                      <div className="mt-3" aria-label={`Progreso: ${m.progreso.completados} de ${m.progreso.total} datos`}>
                        <div className="mb-1 flex justify-between text-xs opacity-80">
                          <span>Datos recopilados</span>
                          <span>{m.progreso.completados}/{m.progreso.total}</span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-slate-200/70">
                          <div
                            className="h-full rounded-full bg-corporativo-500 transition-[width] duration-500 motion-reduce:transition-none"
                            style={{ width: `${Math.min(100, (m.progreso.completados / m.progreso.total) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ) : null}
                    {m.tipos?.length ? (
                      <ul className={`mt-3 space-y-2 ${m.tipos.length > 4 ? 'max-h-56 overflow-y-auto pr-1' : ''}`}>
                        {m.tipos.map((t) => (
                          <li key={t.valor}>
                            <button
                              type="button"
                              onClick={() => enviar(t.etiqueta)}
                              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 transition"
                            >
                              <span className="font-semibold text-corporativo-700">{t.etiqueta}</span> — {t.descripcion}
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : null}
                    {m.catalogoCompletoDisponible ? (
                      <button
                        type="button"
                        disabled={cargando}
                        onClick={() => enviar('Ver todos los tipos')}
                        className="mt-3 rounded-lg border border-corporativo-200 bg-corporativo-50 px-3 py-2 text-xs font-semibold text-corporativo-700 transition hover:border-corporativo-300 hover:bg-corporativo-100 disabled:opacity-50"
                      >
                        Ver todos los tipos
                      </button>
                    ) : null}
                    {m.camposEdicion?.length ? (
                      <div className="mt-3">
                        <p className="mb-2 text-xs font-semibold text-slate-600">Campos editables</p>
                        <div className="flex flex-wrap gap-2">
                          {m.camposEdicion.map((campo) => (
                            <button
                              key={campo.clave}
                              type="button"
                              disabled={cargando}
                              onClick={() => enviar(campo.clave)}
                              className="rounded-full border border-corporativo-200 bg-corporativo-50 px-3 py-1.5 text-xs font-medium text-corporativo-700 hover:bg-corporativo-100 disabled:opacity-50"
                            >
                              {campo.etiqueta}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : null}
                    {m.cambiosPropuestos && Object.keys(m.cambiosPropuestos).length && onAplicarCambios ? (
                      <div className="mt-3">
                        <Boton
                          tamano="sm"
                          variante="secundario"
                          disabled={cargando}
                          onClick={() => setCambioEnRevision(
                            cambioEnRevision?.indice === i
                              ? null
                              : { indice: i, actaId: m.actaId || actaId, cambios: m.cambiosPropuestos },
                          )}
                        >
                          {cambioEnRevision?.indice === i ? 'Ocultar cambios' : 'Revisar cambios propuestos'}
                        </Boton>
                        {cambioEnRevision?.indice === i ? (
                          <div className="mt-3 rounded-lg border border-corporativo-100 bg-corporativo-50/60 p-3">
                            <p className="text-xs font-semibold text-corporativo-800">
                              Confirma que estos valores son correctos antes de aplicarlos:
                            </p>
                            <ul className="mt-2 space-y-1.5">
                              {Object.entries(cambioEnRevision.cambios).map(([campo, valor]) => (
                                <li key={campo} className="text-xs text-slate-700">
                                  <span className="font-semibold">{ETIQUETAS_CAMPO[campo] || campo}:</span>{' '}
                                  <span className="break-words">{mostrarValor(valor)}</span>
                                </li>
                              ))}
                            </ul>
                            <Boton
                              tamano="sm"
                              variante="primario"
                              className="mt-3"
                              disabled={cargando}
                              onClick={() => {
                                onAplicarCambios({
                                  actaId: cambioEnRevision.actaId,
                                  cambios: cambioEnRevision.cambios,
                                })
                                setCambioEnRevision(null)
                              }}
                            >
                              Confirmar y aplicar al formulario
                            </Boton>
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                    {m.confirmacionCreacion && m.resumenCreacion ? (
                      <section className="mt-3 rounded-xl border border-corporativo-100 bg-corporativo-50/60 p-3">
                        <h3 className="text-xs font-semibold text-corporativo-800">Revisa los datos del acta</h3>
                        <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                          {Object.entries(m.resumenCreacion).map(([campo, valor]) => (
                            <div key={campo} className="rounded-lg bg-white/80 px-2.5 py-2">
                              <dt className="text-[11px] font-semibold text-slate-500">
                                {ETIQUETAS_CAMPO[campo] || campo}
                              </dt>
                              <dd className="mt-0.5 break-words text-xs text-slate-700">{mostrarValor(valor)}</dd>
                            </div>
                          ))}
                        </dl>
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          <Boton
                            tamano="sm"
                            variante="primario"
                            disabled={cargando}
                            onClick={() => enviar('Confirmar y enviar a revisión')}
                          >
                            Confirmar y enviar a revisión
                          </Boton>
                          <details className="text-xs">
                            <summary className="cursor-pointer rounded-lg border border-corporativo-200 bg-white px-3 py-2 font-semibold text-corporativo-700 hover:bg-corporativo-50">
                              Corregir un dato
                            </summary>
                            <div className="mt-2 flex max-w-xl flex-wrap gap-1.5">
                              {Object.keys(m.resumenCreacion)
                                .filter((campo) => !['tipo_asamblea', 'RFC de la sociedad'].includes(campo))
                                .map((campo) => (
                                  <button
                                    key={campo}
                                    type="button"
                                    disabled={cargando}
                                    onClick={() => enviar(`Cambiar campo ${campo}`)}
                                    className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-700 hover:border-corporativo-300 hover:bg-corporativo-50 disabled:opacity-50"
                                  >
                                    {ETIQUETAS_CAMPO[campo] || campo}
                                  </button>
                                ))}
                            </div>
                          </details>
                        </div>
                      </section>
                    ) : null}
                    {m.acta ? (
                      <p className="mt-3 rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600 border border-slate-100">
                        {m.acta.folio} · {m.acta.estatus} · v{m.acta.version}{m.acta.creado_por ? ` · por ${m.acta.creado_por}` : ''}
                      </p>
                    ) : null}
                    {m.control ? (
                      <div className="mt-3 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-900 border border-emerald-100">
                        <p className="font-semibold mb-1">Control: {m.control.folio} · v{m.control.version}</p>
                        <p className="mb-1">Fecha: {m.control.fecha_acta} · Creada: {m.control.fecha_creacion || '—'} · Por: {m.control.creado_por || '—'}</p>
                        <p className="mb-2">Estado: {m.control.estado_flujo || 'En revisión'} · Caducidad: {m.control.fecha_caducidad || 'sin fecha'}</p>
                        {m.control.estado_flujo === 'aprobada' ? (
                          <Boton tamano="sm" variante="primario" cargando={descargando} onClick={() => descargar(m.actaId || m.control.acta_id)}>
                            Descargar PDF final
                          </Boton>
                        ) : (
                          <p>El PDF final estará disponible después de la aprobación del Abogado.</p>
                        )}
                      </div>
                    ) : null}
                    {m.borrador && onUsarBorrador ? (
                      <div className="mt-3"><Boton tamano="sm" variante="secundario" onClick={() => onUsarBorrador(m)}>Usar en formulario</Boton></div>
                    ) : null}
                    {m.acciones?.filter((accion) => accion.accion !== 'aprobar' || puedeCambiarEstatus).length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {m.acciones
                          .filter((accion) => accion.accion !== 'aprobar' || puedeCambiarEstatus)
                          .map((a, j) => (
                          <button
                            key={j}
                            type="button"
                            onClick={() => accionar(a)}
                            className="rounded-full bg-corporativo-50 px-3 py-1.5 text-xs font-semibold text-corporativo-700 border border-corporativo-200 hover:bg-corporativo-100 transition"
                          >
                            {a.etiqueta}
                          </button>
                          ))}
                      </div>
                    ) : null}
                  </div>
                ))}
                {cargando ? (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <span className="h-3 w-3 rounded-full border-2 border-corporativo-500 border-t-transparent motion-safe:animate-spin motion-reduce:animate-none"></span>
                    <span className="motion-safe:animate-pulse motion-reduce:animate-none">Preparando respuesta…</span>
                  </div>
                ) : null}
                <div ref={finRef} />
              </>
            )}
          </div>
          {/* Opciones en botones (sugerencias rápidas) */}
          {ejemplos.length ? (
            <div className={`border-t border-slate-100 bg-slate-50/50 ${flotante ? 'p-3' : 'p-6'}`}>
              <div className="flex flex-wrap gap-2">
                {ejemplos.map((s) => (
                  <button
                    key={s}
                    type="button"
                    disabled={cargando}
                    onClick={() => enviar(s)}
                    className="rounded-full bg-white px-3 py-1.5 text-xs text-slate-600 shadow-sm border border-slate-200 hover:bg-corporativo-50 hover:text-corporativo-700 hover:border-corporativo-300 transition disabled:opacity-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {/* Entrada de texto para pedir el acta */}
          <form className={`border-t border-slate-100 bg-white ${flotante ? 'p-3' : 'p-6'}`} onSubmit={(e) => { e.preventDefault(); enviar() }}>
            <div className="flex gap-2">
              <input
                className="campo flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm focus:ring-2 focus:ring-corporativo-500 focus:border-transparent outline-none transition"
                value={entrada}
                onChange={(e) => setEntrada(e.target.value)}
                placeholder={sesionId ? 'Responde el dato pedido…' : 'Quiero crear un acta…'}
                aria-label="Mensaje"
              />
              <Boton type="submit" variante="primario" cargando={cargando} className="px-4">
                Enviar
              </Boton>
            </div>
          </form>
        </TarjetaCuerpo>
      </Tarjeta>
    </div>
  </div>
</div>
  )
}
