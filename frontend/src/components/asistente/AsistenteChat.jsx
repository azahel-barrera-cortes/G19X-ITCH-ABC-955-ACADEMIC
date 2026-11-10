import { useEffect, useRef, useState } from 'react'
import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../ui/Tarjeta.jsx'
import { chatearAsistente, descargarPdfGuardado, descargarBlob, mensajeDeError, obtenerAyudaAsistente } from '../../api/client.js'

const SUGERENCIAS = [
  'Quiero crear un acta',
  'Qué tipos de acta hay?',
  'Crear acta ordinaria',
  'Valida el acta 1',
  'Estatus de PGAC-2026-0001',
  'Cuantas actas hay por estatus?',
]

function burbujaClase(origen) {
  return origen === 'usuario'
    ? 'ml-auto bg-corporativo-700 text-white'
    : 'mr-auto bg-white text-slate-700 ring-1 ring-inset ring-slate-200'
}

export default function AsistenteChat({ modo = 'pagina', titulo = null, onUsarBorrador = null }) {
  const [mensajes, setMensajes] = useState([
    { origen: 'ia', texto: 'Hola, te acompaño a crear tu acta paso a paso. Dime «Quiero crear un acta» o «Qué tipos de acta hay?» y empezamos. Al final genero el texto organizado + PDF descargable con su control (folio, fecha, autor, caducidad, versión).' },
  ])
  const [entrada, setEntrada] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState(null)
  const [ejemplos, setEjemplos] = useState(SUGERENCIAS)
  const [sesionId, setSesionId] = useState(null)
  const [descargando, setDescargando] = useState(false)
  const finRef = useRef(null)
  const compacto = modo === 'compacto'

  useEffect(() => {
    obtenerAyudaAsistente()
      .then((d) => { if (d?.sugerencias?.length) setEjemplos(d.sugerencias.slice(0, 6)) })
      .catch(() => {})
  }, [])

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [mensajes, cargando])

  const enviar = async (libre = null) => {
    const texto = (libre ?? entrada).trim()
    if (!texto || cargando) return
    setEntrada('')
    setError(null)
    setMensajes((p) => [...p, { origen: 'usuario', texto }])
    setCargando(true)
    try {
      const r = await chatearAsistente(texto, { sesionId })
      if (r.sesion_id) setSesionId(r.sesion_id)
      // Sesión cerrada (acta generada o cancelada): libera para empezar otra.
      if (r.control_acta || r.intencion === 'cancelar_creacion') setSesionId(null)
      setMensajes((p) => [...p, {
        origen: 'ia', texto: r.respuesta, acta: r.acta || null,
        acciones: r.acciones || [], borrador: r.texto_borrador || null,
        sesion: r.sesion_id || null, tipos: r.tipos_acta || null,
        control: r.control_acta || null, progreso: r.progreso || null,
        actaId: r.acta_id || r.acta?.id || null,
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
    if (a.accion === 'aprobar' && a.acta_id) { enviar(`Pasa el acta ${a.acta_id} a ${a.estatus || 'revision'}`) }
  }

  return (
    <div className="space-y-4">
      {!compacto ? (
        <header className="mb-2">
          <h1 className="text-lg font-semibold text-corporativo-700 flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-corporativo-100 text-corporativo-700 text-sm font-bold">IA</span>
            {titulo || 'Asistente IA de actas'}
          </h1>
          <p className="text-sm text-slate-500">Te acompaña a crear el acta paso a paso, genera texto + PDF y lleva el control (folio, fecha, autor, caducidad, versión).</p>
        </header>
      ) : null}
      {sesionId ? <Alerta tono="info" titulo={`Creación en curso · sesión ${sesionId}`}>Responde el dato pedido o escribe «cancelar» para empezar de nuevo.</Alerta> : null}
      {error ? <Alerta tono="error" titulo="Sin conexión al asistente">{error}</Alerta> : null}

      {/* Contenedor principal con borde arcoíris animado */}
      <div className="relative rounded-3xl p-[3px] bg-white">
        {/* Borde de arcoíris que se mueve (gradiente cónico rotativo) */}
        <div
          className="absolute inset-0 rounded-3xl bg-[conic-gradient(from_0deg_at_50%_50%_,#ff0000,#ff7f00,#ffff00,#00ff00,#0000ff,#4b0082,#8b00ff,#ff0000)] animate-[spin_4s_linear_infinite] pointer-events-none opacity-100"
          aria-hidden="true"
        ></div>
        {/* Centro blanco que cubre todo excepto el borde de 3px */}
        <div className="absolute inset-[3px] z-10 rounded-[calc(3xl-3px)] bg-white overflow-hidden flex flex-col h-full">
          <Tarjeta className="border-none shadow-none p-0 mb-0">
            <TarjetaEncabezado
              titulo="Conversación"
              descripcion="Creación guiada de actas"
              acciones={<Etiqueta tono="info">IA interna</Etiqueta>}
            />
            <TarjetaCuerpo className="p-0">
          {/* Espacio grande para ver los mensajes entre el usuario y la IA */}
          <div className="flex-1 min-h-[320px] max-h-[520px] overflow-y-auto p-6 space-y-5">
            {mensajes.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-slate-400 text-sm">
                <p className="font-medium">Sin mensajes aún</p>
                <p className="mt-1 text-xs">Escribe «Quiero crear un acta» para comenzar.</p>
              </div>
            ) : (
              <>
                {mensajes.map((m, i) => (
                  <div key={i} className={`max-w-[90%] rounded-2xl px-4 py-3.5 text-sm ${burbujaClase(m.origen)} shadow-sm border`}>
                    <p className="whitespace-pre-line leading-relaxed">{m.texto}</p>
                    {m.progreso ? <p className="mt-2 text-xs opacity-80">Progreso: {m.progreso.completados}/{m.progreso.total} datos</p> : null}
                    {m.tipos?.length ? (
                      <ul className="mt-3 space-y-2">
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
                    {m.acta ? (
                      <p className="mt-3 rounded-lg bg-slate-100 px-3 py-2 text-xs text-slate-600 border border-slate-100">
                        {m.acta.folio} · {m.acta.estatus} · v{m.acta.version}{m.acta.creado_por ? ` · por ${m.acta.creado_por}` : ''}
                      </p>
                    ) : null}
                    {m.control ? (
                      <div className="mt-3 rounded-xl bg-emerald-50 p-3 text-xs text-emerald-900 border border-emerald-100">
                        <p className="font-semibold mb-1">Control: {m.control.folio} · v{m.control.version}</p>
                        <p className="mb-1">Fecha: {m.control.fecha_acta} · Creada: {m.control.fecha_creacion || '—'} · Por: {m.control.creado_por || '—'}</p>
                        <p className="mb-2">Caducidad: {m.control.fecha_caducidad || 'sin fecha'} ({m.control.estado_caducidad})</p>
                        <Boton tamano="sm" variante="primario" cargando={descargando} onClick={() => descargar(m.actaId || m.control.acta_id, m.control.pdf_nombre)}>
                          Descargar PDF ({m.control.pdf_paginas || '?'} págs.)
                        </Boton>
                      </div>
                    ) : null}
                    {m.borrador && onUsarBorrador ? (
                      <div className="mt-3"><Boton tamano="sm" variante="secundario" onClick={() => onUsarBorrador(m)}>Usar en formulario</Boton></div>
                    ) : null}
                    {m.acciones?.length ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {m.acciones.map((a, j) => (
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
                    <span className="h-3 w-3 rounded-full border-2 border-corporativo-500 border-t-transparent animate-spin"></span>
                    El asistente está pensando…
                  </div>
                ) : null}
                <div ref={finRef} />
              </>
            )}
          </div>
          {/* Opciones en botones (sugerencias rápidas) */}
          <div className="p-6 border-t border-slate-100 bg-slate-50/50">
            <div className="flex flex-wrap gap-2 pb-3">
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

          {/* Entrada de texto para pedir el acta */}
          <form className="p-6 border-t border-slate-100 bg-white" onSubmit={(e) => { e.preventDefault(); enviar() }}>
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
