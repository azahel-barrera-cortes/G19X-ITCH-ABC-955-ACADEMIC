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
    id: 'biblioteca',
    etiqueta: 'Biblioteca de actas',
    descripcion: 'Historial, estatus, PDF y edición',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 004 20.5V5.5z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 20.5A2.5 2.5 0 016.5 18H20" />
      </svg>
    ),
  },
  {
    id: 'administracion',
    etiqueta: 'Administración',
    descripcion: 'Versiones, vigencia y caducidad',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v3m0 12v3m9-9h-3M6 12H3m14.5-5.5l-2 2m-7 7l-2 2m11 0l-2-2m-7-7l-2-2" />
        <circle cx="12" cy="12" r="3.2" />
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
    id: 'empresa',
    etiqueta: 'Información de la empresa o sociedad',
    descripcion: 'Datos de la sociedad, tipo, logo y firma electrónica',
    icono: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
  },
]

export default function BarraLateral({ seccion, onCambiarSeccion, seccionesVisibles = null }) {
  // Solo se muestran las secciones que el rol del usuario tiene permitidas.
  const secciones = seccionesVisibles
    ? SECCIONES.filter((item) => seccionesVisibles.includes(item.id))
    : SECCIONES
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

      <div className="border-t border-slate-200 px-5 py-3">
        <p className="text-[11px] leading-snug text-slate-400">
          La IA asiste la redacción; la revisión legal final corresponde al abogado responsable.
        </p>
      </div>
    </aside>
  )
}
