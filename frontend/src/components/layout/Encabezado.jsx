/** Encabezado superior: navegación compacta para móvil y estado del backend. */
import { useEffect, useState } from 'react'
import { consultarEstado } from '../../api/client.js'
import Boton from '../ui/Boton.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import { useAuth } from '../../context/AuthContext.jsx'
import { etiquetaGuiaRol } from '../../constants/roles.js'

const SECCIONES = [
  { id: 'generar', etiqueta: 'Generar acta', titulo: 'Generar acta corporativa' },
  { id: 'mis-actas', etiqueta: 'Mis actas', titulo: 'Mis actas' },
  { id: 'revision', etiqueta: 'Revisión', titulo: 'Revisión de actas' },
  { id: 'aprobacion', etiqueta: 'Aprobación', titulo: 'Aprobación de actas' },
  { id: 'asistente', etiqueta: 'Asistente IA', titulo: 'Asistente IA de actas' },
  { id: 'biblioteca', etiqueta: 'Biblioteca', titulo: 'Biblioteca de actas' },
  { id: 'administracion', etiqueta: 'Administración de Actas', titulo: 'Administración de actas' },
  { id: 'ayuda', etiqueta: 'Guía de uso', titulo: 'Guía de uso' },
  { id: 'guia-super-admin', etiqueta: 'Guía de SuperAdministrador', titulo: 'Guía de SuperAdministrador' },
  { id: 'perfil', etiqueta: 'Mi perfil', titulo: 'Mi perfil y funciones disponibles' },
  { id: 'usuarios', etiqueta: 'Administración de Usuarios', titulo: 'Administración de usuarios' },
  { id: 'vitacora', etiqueta: 'Bitácora', titulo: 'Bitácora de actas' },
]

export default function Encabezado({ seccion, onCambiarSeccion, onCerrarSesion = null, seccionesVisibles = null }) {
  const { usuario } = useAuth()
  const [estado, setEstado] = useState(null)
  const [error, setError] = useState(false)

  // Navegación móvil filtrada por las secciones permitidas al rol.
  const seccionesNav = seccionesVisibles
    ? seccionesVisibles
      .map((id) => SECCIONES.find((item) => item.id === id))
      .filter(Boolean)
    : SECCIONES
  const seccionesNavConEtiquetas = seccionesNav.map((item) =>
    item.id === 'ayuda' ? { ...item, etiqueta: etiquetaGuiaRol(usuario?.rol) } : item,
  )

  useEffect(() => {
    let activo = true
    consultarEstado()
      .then((datos) => {
        if (activo) setEstado(datos)
      })
      .catch(() => {
        if (activo) setError(true)
      })
    return () => {
      activo = false
    }
  }, [])

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 md:px-6">
        {/* En escritorio la marca vive en la barra lateral; aquí solo aparece en móvil. */}
        <div className="flex items-center gap-2.5 md:hidden">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-corporativo-700 text-xs font-bold text-white">
            PG
          </span>
          <p className="text-sm font-semibold leading-tight text-corporativo-700">
            PGAC
          </p>
        </div>

        {/* Navegación compacta: solo visible en móvil (la lateral la reemplaza en escritorio). */}
        <nav aria-label="Secciones" className="flex flex-wrap items-center gap-1 md:hidden">
          {seccionesNavConEtiquetas.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onCambiarSeccion(item.id)}
              aria-current={seccion === item.id ? 'page' : undefined}
              className={seccion === item.id
                ? 'rounded-lg px-2.5 py-1.5 text-xs font-medium bg-corporativo-50 text-corporativo-700'
                : 'rounded-lg px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100'}
            >
              {item.etiqueta}
            </button>
          ))}
        </nav>

        {/* En escritorio el encabezado muestra el contexto actual + estado. */}
        <p className="hidden text-sm font-semibold text-corporativo-700 md:block">
          {seccion === 'ayuda'
            ? etiquetaGuiaRol(usuario?.rol)
            : SECCIONES.find((item) => item.id === seccion)?.titulo || 'PGAC'}
        </p>

        <div className="flex items-center gap-2">
          {/* Estado del backend */}
          {error ? (
            <Etiqueta tono="error">Backend sin conexión</Etiqueta>
          ) : estado ? (
            <>
              <Etiqueta tono={estado.base_de_datos === 'disponible' ? 'exito' : 'advertencia'}>
                BD: {estado.base_de_datos}
              </Etiqueta>
              <Etiqueta tono={estado.ia_habilitada ? 'info' : 'neutral'}>
                IA: {estado.proveedor_ia}
              </Etiqueta>
            </>
          ) : (
            <Etiqueta>Consultando estado…</Etiqueta>
          )}

          {/* Sesión del usuario (este encabezado solo se muestra autenticado) */}
          <div className="flex items-center gap-2">
            <span className="hidden text-xs text-slate-600 sm:inline">
              {usuario?.nombre_completo || usuario?.email}
              {usuario?.rol && <span className="ml-1 text-slate-400">({usuario.rol})</span>}
            </span>
            {onCerrarSesion && (
              <Boton
                variante="peligro"
                tamano="sm"
                className="shrink-0 md:hidden"
                onClick={onCerrarSesion}
                aria-label="Cerrar sesión"
              >
                <span className="sm:hidden">Salir</span>
                <span className="hidden sm:inline">Cerrar sesión</span>
              </Boton>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}