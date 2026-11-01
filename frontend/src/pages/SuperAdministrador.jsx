import { useState } from 'react'

const APARTADOS = [
  { id: 'usuarios', etiqueta: 'Administración de usuarios' },
  { id: 'vitacora', etiqueta: 'Vitácora de acciones' },
  { id: 'estadisticas', etiqueta: 'Estadísticas' },
  { id: 'seguridad', etiqueta: 'Seguridad' },
]

const SUBSECCIONES_USUARIOS = [
  { id: 'empresas', etiqueta: 'Empresas' },
  { id: 'admin_empresa', etiqueta: 'Administrador de empresa' },
  { id: 'capturista', etiqueta: 'Capturista' },
  { id: 'revisor', etiqueta: 'Revisor' },
  { id: 'abogado', etiqueta: 'Abogado' },
]

export default function SuperAdministrador() {
  const [apartado, setApartado] = useState('usuarios')
  const [subseccion, setSubseccion] = useState('empresas')

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Superadministrador
            </p>
            <h1 className="text-xl font-bold text-slate-900">Panel de administración global</h1>
          </div>
          <span className="rounded-full bg-corporativo-50 px-3 py-1 text-xs font-medium text-corporativo-700 ring-1 ring-inset ring-corporativo-200">
            Vista separada
          </span>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-7xl gap-6 px-4 py-6 md:px-6">
        <aside className="hidden w-64 shrink-0 md:block">
          <nav className="space-y-1 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
            {APARTADOS.map((item) => {
              const activo = apartado === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setApartado(item.id)}
                  className={`flex w-full items-center rounded-xl px-3 py-2.5 text-left text-sm font-medium transition ${
                    activo
                      ? 'bg-corporativo-600 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  {item.etiqueta}
                </button>
              )
            })}
          </nav>
        </aside>

        <main className="min-w-0 flex-1">
          {apartado === 'usuarios' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Administración de usuarios</h2>
              <p className="mt-1 text-sm text-slate-500">
                Visualiza y gestiona todos los usuarios del sistema por categoría.
              </p>

              <nav className="mt-4 flex flex-wrap gap-2 border-b border-slate-200 pb-3">
                {SUBSECCIONES_USUARIOS.map((item) => {
                  const activa = subseccion === item.id
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setSubseccion(item.id)}
                      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                        activa
                          ? 'bg-corporativo-600 text-white'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {item.etiqueta}
                    </button>
                  )
                })}
              </nav>

              <div className="mt-4">
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
                  Apartado «{SUBSECCIONES_USUARIOS.find((s) => s.id === subseccion)?.etiqueta}»
                  en construcción.
                </div>
              </div>
            </section>
          )}

          {apartado === 'vitacora' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Vitácora de acciones</h2>
              <p className="mt-1 text-sm text-slate-500">En construcción.</p>
            </section>
          )}

          {apartado === 'estadisticas' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Estadísticas</h2>
              <p className="mt-1 text-sm text-slate-500">En construcción.</p>
            </section>
          )}

          {apartado === 'seguridad' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Seguridad</h2>
              <p className="mt-1 text-sm text-slate-500">En construcción.</p>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}
