/**
 * Barra lateral izquierda con la navegación principal de la plataforma.
 *
 * Cada sección muestra icono, nombre y una descripción corta para que el usuario
 * encuentre rápido qué busca. En pantallas pequeñas la barra se oculta y la
 * navegación pasa a una fila horizontal sobre el contenido (ver `App.jsx`).
 */
const SECCIONES = [
  {
    id: 'generar',
    etiqueta: 'Generar acta',
    descripcion: 'Plantillas, formulario manual y modo IA',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m0 0l-6-6m6 6l6-6" />
        <path strokeLinecap="round" d="M4 20.5h16" />
      </svg>
    ),
  },
  {
    id: 'asistente',
    etiqueta: 'Asistente IA',
    descripcion: 'Chat de actas: redacta, valida y aprueba',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h8M8 14h5" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-13.2 8L3 21l1.1-4.4A9 9 0 1121 12z" />
      </svg>
    ),
  },
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
    id: 'ayuda',
    etiqueta: 'Guía de uso',
    descripcion: 'Flujo, API y notas legales',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.5 9.3a2.6 2.6 0 115 1.2c-.5 1-2 1.3-2 2.5" />
        <circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    id: 'administrador',
    etiqueta: 'Administrador',
    descripcion: 'Panel de administración de la empresa',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4m8 0h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
]

/**
 * Secciones exclusivas para el rol SuperAdministrador.
 * Solo se muestran cuando el usuario tiene ese rol.
 */
const SECCIONES_SUPERADMIN = [
  {
    id: 'usuarios',
    etiqueta: 'Administracion de Usuarios',
    descripcion: 'Gestion de usuarios del sistema',
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
    descripcion: 'Vitacora de acciones del sistema',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 'estadisticas',
    etiqueta: 'Estadisticas',
    descripcion: 'Estadisticas del sistema',
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
    id: 'guia-super-admin',
    etiqueta: 'Gia de super Administrador',
    descripcion: 'Flujo, API, Notas y seguridad del super administrador',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a4 4 0 000 8h12a4 4 0 000-8h-5a2 2 0 01-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
]

export default function BarraLateral({ seccion, onCambiarSeccion, onCerrarSesion = null, seccionesVisibles = null, esSuperAdmin = false }) {
  // Para SuperAdministrador se muestran exclusivamente sus 5 secciones.
  // Esas IDs no están en SECCIONES_SISTEMA, por lo que no se filtran por
  // seccionesVisibles; se muestran tal cual.
  const secciones = esSuperAdmin
    ? SECCIONES_SUPERADMIN
    : (seccionesVisibles
      ? SECCIONES.filter((item) => seccionesVisibles.includes(item.id))
      : SECCIONES)
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
            Página de Gestión de Actas Corporativas
          </p>
        </div>
      </div>

      <nav aria-label="Secciones" className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {secciones.map((item) => {
          const activa = seccion === item.id
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onCambiarSeccion(item.id)}
              aria-current={activa ? 'page' : undefined}
              className={`flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left transition ${activa
                ? 'bg-corporativo-50 text-corporativo-700 ring-1 ring-inset ring-corporativo-200'
                : 'text-slate-600 hover:bg-slate-100'
                }`}
            >
              <span
                className={`mt-0.5 h-5 w-5 shrink-0 ${activa ? 'text-corporativo-600' : 'text-slate-400'
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

      <div className="h-16" />

      <div className="border-t border-slate-200 px-5 py-3 space-y-3">
        {onCerrarSesion && (
          <button
            type="button"
            onClick={() => onCerrarSesion()}
            className="w-full rounded-xl px-3 py-2.5 text-left text-red-600 font-medium border border-red-100 background-color: red "
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
