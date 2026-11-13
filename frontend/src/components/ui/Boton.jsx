import { forwardRef } from 'react'
import Indicador from './Indicador.jsx'

/**
 * Botón del sistema de diseño.
 *
 * variantes: primario | secundario | acento | peligro | fantasma
 * tamaños:   sm | md | lg
 */
const VARIANTES = {
  primario:
    'bg-corporativo-700 text-white shadow-sm hover:bg-corporativo-800 focus-visible:outline-corporativo-700',
  secundario:
    'bg-white text-corporativo-700 ring-1 ring-inset ring-corporativo-200 hover:bg-corporativo-50 focus-visible:outline-corporativo-700',
  acento:
    'bg-corporativo-600 text-white shadow-sm hover:bg-corporativo-700 focus-visible:outline-corporativo-700',
  peligro:
    'bg-red-700 text-white shadow-sm hover:bg-red-800 focus-visible:outline-red-700',
  fantasma:
    'bg-transparent text-slate-600 hover:bg-slate-100 focus-visible:outline-corporativo-700',
}

const TAMANOS = {
  sm: 'gap-1.5 px-2.5 py-1.5 text-xs',
  md: 'gap-2 px-4 py-2 text-sm',
  lg: 'gap-2 px-5 py-2.5 text-sm',
}

const Boton = forwardRef(function Boton({
    variante = 'primario',
    tamano = 'md',
    cargando = false,
    icono = null,
    className = '',
    disabled = false,
    children,
    ...propiedades
  }, ref) {
  return (
    <button
      ref={ref}
      {...propiedades}
      type={propiedades.type || 'button'}
      className={`inline-flex items-center justify-center rounded-lg font-semibold transition-[background-color,color,box-shadow,transform] duration-150 ease-out active:scale-[0.98] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-corporativo-600 disabled:active:scale-100 disabled:cursor-not-allowed disabled:opacity-60 motion-reduce:transform-none motion-reduce:transition-none ${
        VARIANTES[variante] || VARIANTES.primario
      } ${TAMANOS[tamano] || TAMANOS.md} ${className}`}
      disabled={cargando || disabled}
    >
      {cargando ? <Indicador /> : icono}
      {children}
    </button>
  )
})

export default Boton
