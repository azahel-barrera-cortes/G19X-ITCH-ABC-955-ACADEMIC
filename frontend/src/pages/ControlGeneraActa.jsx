/**
 * Panel «Generar acta»: punto de entrada para la creación de actas.
 */
import { useMemo, useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import IconoAsistenteIA from '../components/ui/IconoAsistenteIA.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'
import { TIPOS_ASAMBLEA } from '../constants/catalogos.js'

const PLANTILLAS_SUGERIDAS = [
  'ordinaria',
  'extraordinaria',
  'constitutiva',
  'aumento_capital',
  'sesion_consejo',
  'mixta',
]

function normalizar(texto) {
  return String(texto || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function IconoDocumento({ className = 'h-6 w-6' }) {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 3.75h7l4 4v12.5H7a2 2 0 0 1-2-2v-12.5a2 2 0 0 1 2-2Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M14 3.75v4h4M8.5 12h7M8.5 15.5h7" />
    </svg>
  )
}

export default function ControlGeneraActa({ onGenerarNueva, onAbrirAsistente, onUsarPlantilla }) {
  const [busqueda, setBusqueda] = useState('')
  const [mostrarTodas, setMostrarTodas] = useState(false)

  const plantillas = useMemo(() => {
    const disponibles = mostrarTodas
      ? TIPOS_ASAMBLEA
      : PLANTILLAS_SUGERIDAS
        .map((valor) => TIPOS_ASAMBLEA.find((tipo) => tipo.valor === valor))
        .filter(Boolean)
    const criterio = normalizar(busqueda)
    if (!criterio) return disponibles
    return disponibles.filter((tipo) =>
      normalizar(`${tipo.etiqueta} ${tipo.descripcion} ${tipo.valor} ${(tipo.articulos || []).join(' ')}`)
        .includes(criterio),
    )
  }, [busqueda, mostrarTodas])

  const irFormulario = (tipo) => {
    if (tipo && onUsarPlantilla) {
      onUsarPlantilla(tipo)
      return
    }
    onGenerarNueva?.()
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3 border-b border-corporativo-200 pb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-corporativo-600">Creación documental</p>
          <h1 className="mt-1 text-2xl font-bold tracking-tight text-corporativo-800">Generar acta</h1>
          <p className="mt-1 text-sm text-slate-600">Elige cómo iniciar y continúa con una guía clara hasta la revisión.</p>
        </div>
        <Etiqueta tono="info">Plantillas y captura asistida</Etiqueta>
      </header>

      <section aria-labelledby="metodo-creacion">
        <div className="mb-3">
          <h2 id="metodo-creacion" className="text-base font-semibold text-slate-800">¿Cómo quieres comenzar?</h2>
          <p className="mt-1 text-sm text-slate-500">Puedes capturar los datos directamente o reunirlos con ayuda del asistente.</p>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <article className="flex flex-col rounded-2xl border border-corporativo-200 bg-white p-5 shadow-sm transition hover:border-corporativo-400 hover:shadow-tarjeta">
            <div className="flex items-start gap-4">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-corporativo-50 text-corporativo-700">
                <IconoDocumento />
              </span>
              <div>
                <h3 className="font-semibold text-corporativo-800">Formulario manual</h3>
                <p className="mt-1 text-sm leading-5 text-slate-600">
                  Captura por pasos, valida los campos y revisa el borrador antes de enviarlo.
                </p>
              </div>
            </div>
            <Boton variante="primario" tamano="lg" className="mt-5 w-full" onClick={() => irFormulario(null)}>
              Iniciar formulario
            </Boton>
          </article>

          <article className="flex flex-col rounded-2xl border border-corporativo-700 bg-corporativo-700 p-5 text-white shadow-sm transition hover:bg-corporativo-800 hover:shadow-tarjeta">
            <div className="flex items-start gap-4">
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/10 text-white ring-1 ring-inset ring-white/20">
                <IconoAsistenteIA className="h-6 w-6" />
              </span>
              <div>
                <h3 className="font-semibold">Redacción asistida</h3>
                <p className="mt-1 text-sm leading-5 text-corporativo-50">
                  Consulta actas o inicia una creación guiada desde el mismo asistente de la barra lateral.
                </p>
              </div>
            </div>
            <Boton variante="secundario" tamano="lg" className="mt-5 w-full" onClick={() => onAbrirAsistente?.()}>
              Abrir asistente IA
            </Boton>
          </article>
        </div>
      </section>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Plantillas de actas"
          descripcion="Busca por tipo o asunto, usa una sugerencia o explora el catálogo completo."
          acciones={
            <Etiqueta tono="info" aria-live="polite">
              {plantillas.length} {plantillas.length === 1 ? 'plantilla' : 'plantillas'}
            </Etiqueta>
          }
        />
        <TarjetaCuerpo>
          <div className="mb-5 flex flex-col gap-3 sm:flex-row">
            <label className="relative min-w-0 flex-1">
              <span className="sr-only">Buscar plantillas por tipo o asunto</span>
              <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400">
                <circle cx="10.8" cy="10.8" r="6.8" />
                <path strokeLinecap="round" d="m16 16 4.5 4.5" />
              </svg>
              <input
                type="search"
                value={busqueda}
                onChange={(evento) => setBusqueda(evento.target.value)}
                placeholder="Ej.: ordinaria, capital, consejo…"
                className="campo pl-10"
              />
            </label>
            <Boton
              type="button"
              variante="secundario"
              aria-pressed={mostrarTodas}
              onClick={() => setMostrarTodas((actual) => !actual)}
              className="shrink-0"
            >
              {mostrarTodas ? 'Mostrar sugeridas' : `Ver catálogo completo (${TIPOS_ASAMBLEA.length})`}
            </Boton>
          </div>

          {plantillas.length ? (
            <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {plantillas.map((plantilla) => (
                <li
                  key={plantilla.valor}
                  className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-4 transition hover:border-corporativo-300 hover:bg-corporativo-50/40 hover:shadow-tarjeta"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-corporativo-50 text-corporativo-700">
                      <IconoDocumento className="h-5 w-5" />
                    </span>
                    <div className="min-w-0">
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-corporativo-600">Plantilla de asamblea</p>
                      <h3 className="mt-0.5 text-sm font-semibold leading-5 text-corporativo-800">{plantilla.etiqueta}</h3>
                    </div>
                  </div>
                  <p className="mt-3 flex-1 text-sm leading-5 text-slate-600">{plantilla.descripcion}</p>
                  <Boton
                    variante="secundario"
                    tamano="sm"
                    className="mt-4 w-full"
                    onClick={() => irFormulario(plantilla.valor)}
                  >
                    Usar plantilla
                  </Boton>
                </li>
              ))}
            </ul>
          ) : (
            <div role="status" aria-live="polite" className="rounded-xl border border-dashed border-corporativo-200 bg-corporativo-50/50 px-4 py-8 text-center">
              <p className="font-semibold text-corporativo-800">No encontramos plantillas con esa búsqueda</p>
              <p className="mt-1 text-sm text-slate-600">Prueba con otro tipo de asamblea o tema.</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {!mostrarTodas ? (
                  <Boton
                    variante="primario"
                    tamano="sm"
                    onClick={() => setMostrarTodas(true)}
                  >
                    Buscar en el catálogo completo
                  </Boton>
                ) : null}
                <Boton variante="secundario" tamano="sm" onClick={() => setBusqueda('')}>
                  Limpiar búsqueda
                </Boton>
              </div>
            </div>
          )}
        </TarjetaCuerpo>
      </Tarjeta>
    </div>
  )
}
