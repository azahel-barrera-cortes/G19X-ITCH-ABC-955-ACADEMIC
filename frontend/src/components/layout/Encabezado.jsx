/** Encabezado superior: navegación compacta para móvil y estado del backend. */
import { useEffect, useState } from 'react'
import { consultarEstado } from '../../api/client.js'
import Etiqueta from '../ui/Etiqueta.jsx'

const SECCIONES = [
  { id: 'generar', etiqueta: 'Generar acta', titulo: 'Generar acta corporativa' },
  { id: 'asistente', etiqueta: 'Asistente IA', titulo: 'Asistente IA de actas' },
  { id: 'biblioteca', etiqueta: 'Biblioteca', titulo: 'Biblioteca de actas' },
  { id: 'administracion', etiqueta: 'Administración', titulo: 'Administración de actas' },
  { id: 'ayuda', etiqueta: 'Guía', titulo: 'Guía de uso' },
]

export default function Encabezado({ seccion, onCambiarSeccion }) {
  const [estado, setEstado] = useState(null)
  const [error, setError] = useState(false)

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
          {SECCIONES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onCambiarSeccion(item.id)}
              aria-current={seccion === item.id ? 'page' : undefined}
              className={`rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                seccion === item.id
                  ? 'bg-corporativo-50 text-corporativo-700'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
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
        </div>
      </div>
    </header>
  )
}
