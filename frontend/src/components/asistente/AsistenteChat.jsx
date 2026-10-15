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
        <header>
          <h1 className="text-lg font-semibold text-corporativo-700">{titulo || 'Asistente IA de actas'}</h1>
          <p className="text-sm text-slate-500">Te acompaña a crear el acta paso a paso, genera texto + PDF y lleva el control (folio, fecha, autor, caducidad, versión).</p>
        </header>
      ) : null}
      {sesionId ? <Alerta tono="info" titulo={`Creación en curso · sesión ${sesionId}`}>Responde el dato pedido o escribe «cancelar» para empezar de nuevo.</Alerta> : null}
      {error ? <Alerta tono="error" titulo="Sin conexion al asistente">{error}</Alerta> : null}
      <Tarjeta>
        <TarjetaEncabezado titulo={compacto ? 'Asistente IA' : 'Conversacion'} descripcion="Creación guiada de actas" acciones={<Etiqueta tono="info">IA interna</Etiqueta>} />
        <TarjetaCuerpo>
          <div className="max-h-96 space-y-3 overflow-y-auto">
            {mensajes.map((m, i) => (
              <div key={i} className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${burbujaClase(m.origen)}`}>
                <p className="whitespace-pre-line">{m.texto}</p>
                {m.progreso ? <p className="mt-1 text-xs opacity-70">Progreso: {m.progreso.completados}/{m.progreso.total} datos</p> : null}
                {m.tipos?.length ? (
                  <ul className="mt-2 space-y-1">
                    {m.tipos.map((t) => (
                      <li key={t.valor}>
                        <button type="button" onClick={() => enviar(t.etiqueta)} className="w-full rounded-lg bg-slate-100 px-2 py-1 text-left text-xs text-slate-700 hover:bg-slate-200">
                          <span className="font-semibold">{t.etiqueta}</span> — {t.descripcion}
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : null}
                {m.acta ? <p className="mt-2 rounded-lg bg-slate-100 px-2 py-1 text-xs text-slate-600">{m.acta.folio} · {m.acta.estatus} · v{m.acta.version}{m.acta.creado_por ? ` · por ${m.acta.creado_por}` : ''}</p> : null}
                {m.control ? (
                  <div className="mt-2 rounded-lg bg-emerald-50 px-2 py-1 text-xs text-emerald-900 ring-1 ring-inset ring-emerald-200">
                    <p className="font-semibold">Control: {m.control.folio} · v{m.control.version}</p>
                    <p>Fecha: {m.control.fecha_acta} · Creada: {m.control.fecha_creacion || '—'} · Por: {m.control.creado_por || '—'}</p>
                    <p>Caducidad: {m.control.fecha_caducidad || 'sin fecha'} ({m.control.estado_caducidad})</p>
                    <div className="mt-1"><Boton tamano="sm" variante="primario" cargando={descargando} onClick={() => descargar(m.actaId || m.control.acta_id, m.control.pdf_nombre)}>Descargar PDF ({m.control.pdf_paginas || '?'} págs.)</Boton></div>
                  </div>
                ) : null}
                {m.borrador && onUsarBorrador ? <div className="mt-2"><Boton tamano="sm" variante="secundario" onClick={() => onUsarBorrador(m)}>Usar en formulario</Boton></div> : null}
                {m.acciones?.length ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.acciones.map((a, j) => (
                      <button key={j} type="button" onClick={() => accionar(a)} className="rounded-full bg-corporativo-50 px-2.5 py-1 text-xs font-medium text-corporativo-700 ring-1 ring-inset ring-corporativo-200 hover:bg-corporativo-100">{a.etiqueta}</button>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            {cargando ? <p className="text-xs text-slate-400">El asistente esta pensando…</p> : null}
            <div ref={finRef} />
          </div>
          <div className="mt-3 flex flex-wrap gap-1.5">
            {ejemplos.map((s) => (
              <button key={s} type="button" disabled={cargando} onClick={() => enviar(s)} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-200 disabled:opacity-50">{s}</button>
            ))}
          </div>
          <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); enviar() }}>
            <input className="campo flex-1" value={entrada} onChange={(e) => setEntrada(e.target.value)} placeholder={sesionId ? 'Responde el dato pedido…' : 'Quiero crear un acta…'} aria-label="Mensaje" />
            <Boton type="submit" variante="primario" cargando={cargando}>Enviar</Boton>
          </form>
        </TarjetaCuerpo>
      </Tarjeta>
    </div>
  )
}
