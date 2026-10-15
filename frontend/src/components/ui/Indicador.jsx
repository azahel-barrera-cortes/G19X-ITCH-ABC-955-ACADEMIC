/** Indicador de carga (spinner) reutilizable. */
export default function Indicador({ className = 'h-4 w-4', color = 'text-current' }) {
  return (
    <svg
      className={`animate-spin ${className} ${color}`}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      role="status"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}
