/**
 * Envoltura de campo de formulario: etiqueta, marca de obligatorio, ayuda y error.
 * Los controles se pasan como hijos (input, select, textarea) usando la clase `.campo`.
 */
export default function Campo({
  etiqueta,
  requerido = false,
  error = null,
  ayuda = null,
  htmlFor,
  className = '',
  children,
}) {
  return (
    <div className={className}>
      {etiqueta ? (
        <label className="etiqueta-campo" htmlFor={htmlFor}>
          {etiqueta}
          {requerido ? <span className="ml-1 text-red-500">*</span> : null}
        </label>
      ) : null}
      {children}
      {error ? <p className="mt-1 text-xs font-medium text-red-600">{error}</p> : null}
      {!error && ayuda ? <p className="mt-1 text-xs text-slate-500">{ayuda}</p> : null}
    </div>
  )
}
