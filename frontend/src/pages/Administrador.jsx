import { useState } from 'react'

const APARTADOS = [
  {
    id: 'perfil',
    etiqueta: 'Perfil',
    descripcion: 'Mis datos, funciones y sesión',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
  {
    id: 'empresa',
    etiqueta: 'Información de la empresa',
    descripcion: 'Datos de la sociedad y logo',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    id: 'usuarios',
    etiqueta: 'Administración de usuarios',
    descripcion: 'Gestión de usuarios del sistema',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 8 4 4 0 010-8z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 21a3 3 0 100-6m-5 6a3 3 0 100-6m-3 6a3 3 0 100-6m9-6a3 3 0 100-6" />
      </svg>
    ),
  },
  {
    id: 'seguridad',
    etiqueta: 'Seguridad de usuarios',
    descripcion: 'Contraseñas, roles y accesos',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
]

export default function Administrador() {
  const [apartado, setApartado] = useState('perfil')

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Administrador
            </p>
            <h1 className="text-xl font-bold text-slate-900">Panel de administración</h1>
          </div>
          <span className="rounded-full bg-corporativo-50 px-3 py-1 text-xs font-medium text-corporativo-700 ring-1 ring-inset ring-corporativo-200">
            Vista de administrador
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
                  aria-current={activo ? 'page' : undefined}
                  className={`flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left transition ${
                    activo
                      ? 'bg-corporativo-50 text-corporativo-700 ring-1 ring-inset ring-corporativo-200'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <span className="mt-0.5 h-5 w-5 shrink-0">{item.icono}</span>
                  <span>
                    <span className="block text-sm font-semibold leading-tight">{item.etiqueta}</span>
                    <span className="mt-0.5 block text-[11px] leading-snug text-slate-500">
                      {item.descripcion}
                    </span>
                  </span>
                </button>
              )
            })}
          </nav>
        </aside>

        <main className="min-w-0 flex-1">
          {apartado === 'perfil' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Perfil</h2>
              <p className="mt-1 text-sm text-slate-500">
                Gestiona tu información personal, tu contraseña y los datos de la sociedad.
              </p>
              <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
                Apartado «Perfil» en construcción.
              </div>
            </section>
          )}

          {apartado === 'empresa' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Información de la empresa</h2>
              <p className="mt-1 text-sm text-slate-500">
                Captura los datos de la sociedad, tipo de sociedad y logo.
              </p>
              <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
                Apartado «Información de la empresa» en construcción.
              </div>
            </section>
          )}

          {apartado === 'usuarios' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Administración de usuarios</h2>
              <p className="mt-1 text-sm text-slate-500">
                Visualiza y gestiona los usuarios del sistema por categoría.
              </p>
              <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
                Apartado «Administración de usuarios» en construcción.
              </div>
            </section>
          )}

          {apartado === 'seguridad' && (
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">Seguridad de usuarios</h2>
              <p className="mt-1 text-sm text-slate-500">
                Configura contraseñas, roles y accesos de los usuarios.
              </p>
              <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
                Apartado «Seguridad de usuarios» en construcción.
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  )
}