import Indicador from './Indicador.jsx'

/**
 * Botón del sistema de diseño.
 *
 * variantes: primario | secundario | acento | peligro | fantasma
 * tamaños:   sm | md | lg
 */
const VARIANTES = {
  primario:
    'bg-corporativo-500 text-white shadow-sm hover:bg-corporativo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-corporativo-500',
  secundario:
    'bg-white text-corporativo-600 ring-1 ring-inset ring-corporativo-200 hover:bg-corporativo-50',
  acento: 'bg-acento-500 text-white shadow-sm hover:bg-acento-600',
  peligro: 'bg-red-600 text-white shadow-sm hover:bg-red-700',
  fantasma: 'bg-transparent text-slate-600 hover:bg-slate-100',
}

const TAMANOS = {
  sm: 'gap-1.5 px-2.5 py-1.5 text-xs',
  md: 'gap-2 px-4 py-2 text-sm',
  lg: 'gap-2 px-5 py-2.5 text-sm',
}

export default function Boton({
  variante = 'primario',
  tamano = 'md',
  cargando = false,
  icono = null,
  className = '',
  children,
  ...propiedades
}) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center rounded-lg font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${
        VARIANTES[variante] || VARIANTES.primario
      } ${TAMANOS[tamano] || TAMANOS.md} ${className}`}
      disabled={cargando || propiedades.disabled}
      {...propiedades}
    >
      {cargando ? <Indicador /> : icono}
      {children}
    </button>
  )
}
