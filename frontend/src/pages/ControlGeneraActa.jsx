/**
 * Panel «Generar acta»: punto de entrada para la creación de actas.
 * Muestra «Plantillas de actas» (las más usadas, como hojas) y debajo
 * las acciones «Generar nueva acta» y «Generar acta con IA».
 * Usa el sistema de diseño: tarjeta, Boton, Etiqueta y Tarjeta*.
 */
import Boton from '../components/ui/Boton.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'
import { TIPOS_ASAMBLEA } from '../constants/catalogos.js'

const PLANTILLAS_MAS_USADAS = [
  { tipo: 'ordinaria', usos: 124, destacada: true },
  { tipo: 'extraordinaria', usos: 86, destacada: false },
  { tipo: 'constitutiva', usos: 52, destacada: false },
  { tipo: 'aumento_capital', usos: 38, destacada: false },
  { tipo: 'sesion_consejo', usos: 31, destacada: false },
  { tipo: 'mixta', usos: 27, destacada: false },
]

function datosPlantilla(tipo) {
  return (
    TIPOS_ASAMBLEA.find((item) => item.valor === tipo) || {
      valor: tipo, etiqueta: tipo, descripcion: '', articulos: [],
    }
  )
}

function MiniHoja({ destacada }) {
  return (
    <div
      aria-hidden="true"
      className={`relative mx-auto h-44 w-full max-w-[180px] overflow-hidden rounded-md border bg-white shadow-sm transition group-hover:-translate-y-0.5 group-hover:shadow-tarjeta ${destacada ? 'border-acento-400' : 'border-slate-200'}`}
    >
      <div className="flex items-center gap-1.5 bg-corporativo-700 px-2.5 py-2">
        <span className="flex h-4 w-4 items-center justify-center rounded bg-white/15 text-[7px] font-bold text-white">GC</span>
        <div className="min-w-0 flex-1">
          <p className="h-1.5 w-16 rounded-full bg-white/80" />
          <p className="mt-1 h-1 w-10 rounded-full bg-white/40" />
        </div>
        <span className="h-3 w-3 rounded-full bg-acento-400" />
      </div>
      <div className="space-y-1.5 px-3 py-2.5">
        <p className="mx-auto h-1.5 w-3/4 rounded-full bg-corporativo-100" />
        <p className="h-1 w-full rounded-full bg-slate-200" />
        <p className="h-1 w-full rounded-full bg-slate-200" />
        <p className="h-1 w-11/12 rounded-full bg-slate-200" />
        <p className="h-1 w-full rounded-full bg-slate-100" />
        <p className="h-1 w-10/12 rounded-full bg-slate-100" />
        <div className="flex gap-1 pt-1">
          <span className="h-3 w-8 rounded bg-corporativo-50 ring-1 ring-inset ring-corporativo-100" />
          <span className="h-3 w-8 rounded bg-slate-50 ring-1 ring-inset ring-slate-200" />
        </div>
        <p className="h-1 w-full rounded-full bg-slate-100" />
        <p className="h-1 w-2/3 rounded-full bg-slate-100" />
      </div>
      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between border-t border-slate-100 bg-slate-50 px-2.5 py-1.5">
        <span className="h-1 w-12 rounded-full bg-slate-300" />
        <span className="h-3 w-10 rounded-full bg-acento-100 ring-1 ring-inset ring-acento-400/40" />
      </div>
    </div>
  )
}
export default function ControlGeneraActa({ onGenerarNueva, onGenerarConIA, onUsarPlantilla }) {
  const irFormulario = (tipo) => {
    if (tipo && onUsarPlantilla) { onUsarPlantilla(tipo); return }
    if (onGenerarNueva) onGenerarNueva()
  }
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">Generar acta</h1>
        <p className="text-sm text-slate-500">Elige una plantilla frecuente o inicia desde cero: manual o con IA.</p>
      </header>
      <Tarjeta>
        <TarjetaEncabezado titulo="Plantillas de actas" descripcion="Las actas establecidas en el proyecto mas usadas." acciones={<Etiqueta tono="info">6 plantillas frecuentes</Etiqueta>} />
        <TarjetaCuerpo>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {PLANTILLAS_MAS_USADAS.map(({ tipo, usos, destacada }) => {
              const info = datosPlantilla(tipo)
              return (
                <li key={tipo} className={`group flex flex-col rounded-xl border bg-slate-50/60 p-4 transition hover:border-corporativo-200 hover:bg-corporativo-50/40 hover:shadow-tarjeta ${destacada ? 'border-acento-400/60' : 'border-slate-200'}`}>
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <Etiqueta tono={destacada ? 'advertencia' : 'info'}>{destacada ? 'Mas usada' : `${usos} usos`}</Etiqueta>
                    {destacada ? <span className="text-[11px] text-slate-400">{usos} usos</span> : null}
                  </div>
                  <button type="button" onClick={() => irFormulario(info.valor)} title={`Usar: ${info.etiqueta}`} className="rounded-lg py-2">
                    <MiniHoja destacada={destacada} />
                  </button>
                  <h3 className="mt-3 text-sm font-semibold text-corporativo-700">{info.etiqueta}</h3>
                  <p className="mt-1 min-h-[2.5rem] text-xs text-slate-500">{info.descripcion}</p>
                  <div className="mt-3"><Boton variante={destacada ? 'acento' : 'secundario'} tamano="sm" className="w-full" onClick={() => irFormulario(info.valor)}>Usar plantilla</Boton></div>
                </li>
              )
            })}
          </ul>
        </TarjetaCuerpo>
      </Tarjeta>
      <Tarjeta>
        <TarjetaEncabezado titulo="Crear acta" descripcion="Elige como empezar tu documento" />
        <TarjetaCuerpo>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="flex flex-col rounded-xl border border-corporativo-200 bg-corporativo-50/60 p-4">
              <h3 className="text-sm font-semibold text-corporativo-700">Formulario manual</h3>
              <p className="mt-1 flex-1 text-xs text-slate-500">Captura por pasos con validacion y PDF.</p>
              <Boton variante="primario" tamano="lg" className="mt-3 w-full" onClick={() => irFormulario(null)}>Generar nueva acta</Boton>
            </div>
            <div className="flex flex-col rounded-xl border border-acento-400/50 bg-acento-100/40 p-4">
              <h3 className="text-sm font-semibold text-corporativo-700">Redaccion asistida</h3>
              <p className="mt-1 flex-1 text-xs text-slate-500">Describe tu asamblea y la IA propone el borrador.</p>
              <Boton variante="acento" tamano="lg" className="mt-3 w-full" onClick={() => onGenerarConIA && onGenerarConIA()}>Generar acta con IA</Boton>
            </div>
          </div>
        </TarjetaCuerpo>
      </Tarjeta>
    </div>
  )
}


