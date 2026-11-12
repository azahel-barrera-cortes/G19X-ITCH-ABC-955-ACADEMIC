/**
 * Barra lateral izquierda para el rol Administrador.
 * Contiene las secciones específicas de administración de la empresa.
 */
const SECCIONES_ADMIN = [
  {
    id: 'usuarios',
    etiqueta: 'Usuarios',
    descripcion: 'Gestión de usuarios del sistema',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 8 4 4 0 010-8z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 21a3 3 0 100-6m-5 6a3 3 0 100-6m-3 6a3 3 0 100-6m9-6a3 3 0 100-6" />
      </svg>
    ),
  },
  {
    id: 'vitacora',
    etiqueta: 'Vitacora',
    descripcion: 'Vitácora de acciones del sistema',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 'estadisticas',
    etiqueta: 'Estadisticas',
    descripcion: 'Estadísticas del sistema',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
    ),
  },
  {
    id: 'seguridad',
    etiqueta: 'Seguridad',
    descripcion: 'Seguridad de usuarios y accesos',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4m8 0h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 'guia-super-usuario',
    etiqueta: 'Gia de uso de super usuario',
    descripcion: 'Flujo, API, Notas y seguridad del super usuario',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a4 4 0 000 8h12a4 4 0 000-8h-5a2 2 0 01-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

export default function BarraLateralAdmin({ seccion, onCambiarSeccion, onCerrarSesion }) {
  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
      <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-corporativo-700 text-sm font-bold text-white">
          PG
        </span>
        <div>
          <p className="text-sm font-semibold leading-tight text-corporativo-700">
            PGAC
          </p>
          <p className="text-[11px] leading-tight text-slate-500">
            Panel Administrador
          </p>
        </div>
      </div>

      <nav aria-label="Secciones Administrador" className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {SECCIONES_ADMIN.map((item) => {
          const activa = seccion === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onCambiarSeccion(item.id)}
              aria-current={activa ? 'page' : undefined}
              className={`flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left transition ${
                activa
                  ? 'bg-corporativo-50 text-corporativo-700 ring-1 ring-inset ring-corporativo-200'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <span
                className={`mt-0.5 h-5 w-5 shrink-0 ${
                  activa ? 'text-corporativo-600' : 'text-slate-400'
                }`}
              >
                {item.icono}
              </span>
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

      <div className="flex-1" />

      <div className="border-t border-slate-200 px-5 py-3 space-y-3">
        {onCerrarSesion && (
          <button
            type="button"
            onClick={() => onCerrarSesion()}
            className="w-full rounded-xl px-3 py-2.5 text-left text-red-600 font-medium hover:bg-red-50 transition border border-red-100"
          >
            Cerrar sesión
          </button>
        )}
        <p className="text-[11px] leading-snug text-slate-400">
          La IA asiste la redacción; la revisión legal final corresponde al abogado responsable.
        </p>
      </div>
    </aside>
  )
}