/** Etiqueta (badge) para estatus, severidades y conteos. */
const TONOS = {
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  info: 'bg-corporativo-50 text-corporativo-600 ring-corporativo-200',
  exito: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  advertencia: 'bg-amber-50 text-amber-800 ring-amber-200',
  error: 'bg-red-50 text-red-700 ring-red-200',
}

export default function Etiqueta({ tono = 'neutral', className = '', children }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${
        TONOS[tono] || TONOS.neutral
      } ${className}`}
    >
      {children}
    </span>
  )
}
