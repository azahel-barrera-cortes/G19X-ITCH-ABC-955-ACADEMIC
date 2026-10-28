/** Encabezado superior: navegación compacta para móvil y estado del backend. */
import { useEffect, useState } from 'react'
import { consultarEstado } from '../../api/client.js'
import Etiqueta from '../ui/Etiqueta.jsx'
import { useAuth } from '../../context/AuthContext.jsx'

const SECCIONES = [
  { id: 'generar', etiqueta: 'Generar acta', titulo: 'Generar acta corporativa' },
  { id: 'asistente', etiqueta: 'Asistente IA', titulo: 'Asistente IA de actas' },
  { id: 'biblioteca', etiqueta: 'Biblioteca', titulo: 'Biblioteca de actas' },
  { id: 'administracion', etiqueta: 'Administración', titulo: 'Administración de actas' },
  { id: 'empresa', etiqueta: 'Empresa', titulo: 'Información de la empresa o sociedad' },
  { id: 'ayuda', etiqueta: 'Guía', titulo: 'Guía de uso' },
  { id: 'perfil', etiqueta: 'Mi perfil', titulo: 'Mi perfil y funciones disponibles' },
]

export default function Encabezado({ seccion, onCambiarSeccion, onIrAPerfil = null, onCerrarSesion = null, seccionesVisibles = null }) {
  const { usuario } = useAuth()
  const [estado, setEstado] = useState(null)
  const [error, setError] = useState(false)

  // Navegación móvil filtrada por las secciones permitidas al rol.
  const seccionesNav = seccionesVisibles
    ? SECCIONES.filter((item) => seccionesVisibles.includes(item.id))
    : SECCIONES

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
          {seccionesNav.map((item) => (
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
          {SECCIONES.find((item) => item.id === seccion)?.titulo || 'PGAC'}
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
            <button
              type="button"
              onClick={() => onIrAPerfil && onIrAPerfil('perfil')}
              className="rounded-lg px-3 py-1.5 text-xs font-medium text-corporativo-600 hover:bg-corporativo-50"
            >
              Mi perfil
            </button>
            <button
              type="button"
              onClick={() => onCerrarSesion && onCerrarSesion()}
              className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}