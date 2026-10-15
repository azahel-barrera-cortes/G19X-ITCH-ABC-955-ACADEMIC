/** Tarjeta contenedora y su encabezado de sección. */
export function Tarjeta({ className = '', children }) {
  return <section className={`tarjeta ${className}`}>{children}</section>
}

export function TarjetaEncabezado({ titulo, descripcion, acciones = null }) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-5 py-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">{titulo}</h2>
        {descripcion ? <p className="mt-1 text-xs text-slate-500">{descripcion}</p> : null}
      </div>
      {acciones ? <div className="flex items-center gap-2">{acciones}</div> : null}
    </header>
  )
}

export function TarjetaCuerpo({ className = '', children }) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>
}

export default Tarjeta
