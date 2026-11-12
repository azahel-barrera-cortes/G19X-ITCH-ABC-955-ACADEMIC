export default function UsuariosSuperAdmin() {
  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-semibold text-corporativo-600">
              Usuarios
            </p>
            <h1 className="text-xl font-bold text-slate-900">Gestión de Usuarios SuperAdmin</h1>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl gap-6 px-4 py-6 md:px-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Gestión de Usuarios SuperAdmin</h2>
          <p className="mt-1 text-sm text-slate-500">
            Administra los usuarios del sistema (capturista, revisor, abogado responsable).
          </p>
          <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
            En construcción.
          </div>
        </section>
      </div>
    </div>
  )
}