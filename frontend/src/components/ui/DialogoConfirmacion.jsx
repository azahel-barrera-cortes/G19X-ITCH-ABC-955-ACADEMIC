import { useEffect, useId, useRef } from 'react'
import { createPortal } from 'react-dom'
import Boton from './Boton.jsx'

export default function DialogoConfirmacion({
  abierto,
  titulo,
  descripcion,
  etiquetaConfirmar = 'Eliminar',
  etiquetaCancelar = 'Cancelar',
  varianteConfirmar = 'peligro',
  cargando = false,
  onConfirmar,
  onCancelar,
}) {
  const id = useId()
  const panelRef = useRef(null)
  const cancelarRef = useRef(null)
  const cargandoRef = useRef(cargando)
  const onCancelarRef = useRef(onCancelar)

  cargandoRef.current = cargando
  onCancelarRef.current = onCancelar

  useEffect(() => {
    if (!abierto) return undefined

    const elementoAnterior = document.activeElement
    const overflowAnterior = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    cancelarRef.current?.focus()

    const manejarTecla = (evento) => {
      if (evento.key === 'Escape') {
        evento.preventDefault()
        if (!cargandoRef.current) onCancelarRef.current?.()
        return
      }

      if (evento.key !== 'Tab') return
      const botones = Array.from(panelRef.current?.querySelectorAll('button:not(:disabled)') || [])
      if (!botones.length) return

      const primero = botones[0]
      const ultimo = botones[botones.length - 1]
      if (evento.shiftKey && document.activeElement === primero) {
        evento.preventDefault()
        ultimo.focus()
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault()
        primero.focus()
      }
    }

    document.addEventListener('keydown', manejarTecla)
    return () => {
      document.removeEventListener('keydown', manejarTecla)
      document.body.style.overflow = overflowAnterior
      if (elementoAnterior instanceof HTMLElement && elementoAnterior.isConnected) {
        elementoAnterior.focus()
      }
    }
  }, [abierto])

  if (!abierto || typeof document === 'undefined') return null

  return createPortal(
    <div className="pgac-dialog-backdrop fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/45 p-4 backdrop-blur-[2px]">
      <section
        ref={panelRef}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={`${id}-titulo`}
        aria-describedby={`${id}-descripcion`}
        className="pgac-confirmation-dialog w-full max-w-md overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-950/20"
      >
        <div className="flex items-start gap-4 px-5 pb-4 pt-5">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-700">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              className="h-5 w-5"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M10 11v6m4-6v6M5 7l1 13h12l1-13M9 7V4h6v3" />
            </svg>
          </span>
          <div className="min-w-0 pt-0.5">
            <h2 id={`${id}-titulo`} className="text-base font-semibold text-slate-900">
              {titulo}
            </h2>
            <p id={`${id}-descripcion`} className="mt-1.5 text-sm leading-6 text-slate-600">
              {descripcion}
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-slate-100 bg-slate-50 px-5 py-4">
          <Boton
            ref={cancelarRef}
            variante="secundario"
            onClick={onCancelar}
            disabled={cargando}
          >
            {etiquetaCancelar}
          </Boton>
          <Boton
            variante={varianteConfirmar}
            cargando={cargando}
            onClick={onConfirmar}
          >
            {etiquetaConfirmar}
          </Boton>
        </div>
      </section>
    </div>,
    document.body,
  )
}
