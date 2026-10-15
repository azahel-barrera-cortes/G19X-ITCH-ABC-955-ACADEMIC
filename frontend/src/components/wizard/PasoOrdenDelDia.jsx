import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import Campo from '../ui/Campo.jsx'
import EditorAcuerdo from './EditorAcuerdo.jsx'
import { numero } from '../../utils/formato.js'

/** Normaliza un texto para comparar títulos entre el orden del día y los acuerdos. */
const normalizar = (texto) =>
  String(texto || '')
    .trim()
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')

/**
 * Paso 3: orden del día y acuerdos.
 * Advierte cuando un acuerdo no corresponde a ningún punto del orden del día,
 * que es la inconsistencia más frecuente y ya la valida el backend.
 */
export default function PasoOrdenDelDia({ estado, actualizarCampo, despachar, calculos, errores = {} }) {
  const titulosPuntos = estado.orden_del_dia.map((punto) => normalizar(punto.titulo))
  const acuerdosHuerfanos = estado.acuerdos.filter(
    (acuerdo) =>
      normalizar(acuerdo.titulo).length >= 3 && !titulosPuntos.includes(normalizar(acuerdo.titulo)),
  )

  return (
    <div className="space-y-6">
      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-corporativo-700">Orden del día</h3>
            <p className="text-xs text-slate-500">
              Puntos sometidos a la asamblea, en el orden en que se desahogaron (art. 179 LGSM).
            </p>
          </div>
          <Boton variante="secundario" tamano="sm" onClick={() => despachar({ tipo: 'punto.agregar' })}>
            + Agregar punto
          </Boton>
        </div>

        {errores.orden_del_dia ? <Alerta tono="error">{errores.orden_del_dia}</Alerta> : null}

        <div className="space-y-3">
          {estado.orden_del_dia.map((punto, indice) => (
            <div
              key={punto.clave || `punto-${indice}`}
              className="flex flex-wrap items-start gap-3 rounded-xl border border-slate-200 bg-white p-4"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-corporativo-50 text-sm font-bold text-corporativo-600">
                {indice + 1}
              </span>
              <div className="grid min-w-[240px] flex-1 gap-3 md:grid-cols-2">
                <Campo etiqueta="Título del punto" requerido>
                  <input
                    className="campo"
                    value={punto.titulo}
                    onChange={(evento) =>
                      despachar({
                        tipo: 'punto.actualizar',
                        indice,
                        cambios: { titulo: evento.target.value },
                      })
                    }
                    placeholder="Aumento de capital social"
                  />
                </Campo>
                <Campo etiqueta="Descripción" ayuda="Opcional">
                  <input
                    className="campo"
                    value={punto.descripcion}
                    onChange={(evento) =>
                      despachar({
                        tipo: 'punto.actualizar',
                        indice,
                        cambios: { descripcion: evento.target.value },
                      })
                    }
                    placeholder="Suscripción de nuevas acciones y reforma estatutaria"
                  />
                </Campo>
              </div>
              <div className="flex flex-col items-start gap-2">
                <label className="inline-flex items-center gap-2 text-xs text-slate-600">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
                    checked={punto.requiere_votacion !== false}
                    onChange={(evento) =>
                      despachar({
                        tipo: 'punto.actualizar',
                        indice,
                        cambios: { requiere_votacion: evento.target.checked },
                      })
                    }
                  />
                  Requiere votación
                </label>
                <Boton
                  variante="fantasma"
                  tamano="sm"
                  onClick={() => despachar({ tipo: 'punto.eliminar', indice })}
                >
                  Quitar
                </Boton>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-corporativo-700">Acuerdos y resoluciones</h3>
            <p className="text-xs text-slate-500">
              Capital representado para el cómputo: {numero(calculos.accionesPresentes)} acciones.
            </p>
          </div>
          <Boton variante="secundario" tamano="sm" onClick={() => despachar({ tipo: 'acuerdo.agregar' })}>
            + Agregar acuerdo
          </Boton>
        </div>

        {errores.acuerdos ? <Alerta tono="error">{errores.acuerdos}</Alerta> : null}

        {acuerdosHuerfanos.length ? (
          <Alerta tono="advertencia" titulo="Acuerdos sin punto en el orden del día">
            {acuerdosHuerfanos.map((acuerdo) => acuerdo.titulo).join(' · ')}. Agrega el punto
            correspondiente para que el acta sea congruente.
          </Alerta>
        ) : null}

        <div className="space-y-3">
          {estado.acuerdos.map((acuerdo, indice) => (
            <EditorAcuerdo
              key={acuerdo.clave || `acuerdo-${indice}`}
              acuerdo={acuerdo}
              indice={indice}
              onCambiar={(posicion, cambios) =>
                despachar({ tipo: 'acuerdo.actualizar', indice: posicion, cambios })
              }
              onVotacion={(posicion, cambios) =>
                despachar({ tipo: 'acuerdo.votacion', indice: posicion, cambios })
              }
              onEliminar={(posicion) => despachar({ tipo: 'acuerdo.eliminar', indice: posicion })}
            />
          ))}
          {!estado.acuerdos.length ? (
            <p className="rounded-xl border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
              Aún no hay acuerdos registrados.
            </p>
          ) : null}
        </div>
      </section>

      <Campo
        etiqueta="Observaciones y salvedades"
        ayuda="Se imprimen al cierre del acta (opcional)."
        htmlFor="observaciones"
      >
        <textarea
          id="observaciones"
          rows={2}
          className="campo"
          value={estado.observaciones}
          onChange={(evento) => actualizarCampo('observaciones', evento.target.value)}
          placeholder="Se anexa el proyecto de reforma estatutaria firmado por la mesa directiva."
        />
      </Campo>

    </div>
  )
}
