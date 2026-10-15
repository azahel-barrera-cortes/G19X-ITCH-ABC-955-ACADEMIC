import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import Campo from '../ui/Campo.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import EditorAsistente from './EditorAsistente.jsx'
import { TIPOS_ASAMBLEA } from '../../constants/catalogos.js'
import { moneda, numero, porcentaje } from '../../utils/formato.js'

/**
 * Paso 2: capital social, quórum y asistentes.
 * Muestra en tiempo real el porcentaje representado y alerta si el quórum es
 * insuficiente conforme a los artículos 189 y 190 de la LGSM.
 */
export default function PasoAsistentes({ estado, actualizarCampo, despachar, calculos, errores = {} }) {
  const esExtraordinaria = Boolean(
    TIPOS_ASAMBLEA.find((tipo) => tipo.valor === estado.tipo_asamblea)?.articulos?.some(
      (articulo) => articulo.includes('190'),
    ),
  )
  const quorumInsuficiente = calculos.quorum > 0 && calculos.quorum < 50

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-4">
        <Campo etiqueta="Capital social" ayuda="Importe en pesos" htmlFor="capital_social">
          <input
            id="capital_social"
            type="number"
            min="0"
            step="0.01"
            className="campo"
            value={estado.capital_social}
            onChange={(evento) => actualizarCampo('capital_social', evento.target.value)}
            placeholder="100000"
          />
        </Campo>

        <Campo etiqueta="Acciones en circulación" ayuda="Total emitido" htmlFor="acciones_totales">
          <input
            id="acciones_totales"
            type="number"
            min="0"
            step="1"
            className="campo"
            value={estado.acciones_totales}
            onChange={(evento) => actualizarCampo('acciones_totales', evento.target.value)}
            placeholder="100000"
          />
        </Campo>

        <Campo etiqueta="Capital representado" ayuda="Importe presente" htmlFor="capital_presente">
          <input
            id="capital_presente"
            type="number"
            min="0"
            step="0.01"
            className="campo"
            value={estado.capital_presente}
            onChange={(evento) => actualizarCampo('capital_presente', evento.target.value)}
            placeholder="80000"
          />
        </Campo>

        <Campo etiqueta="Quórum declarado" ayuda="Déjalo vacío para calcularlo" htmlFor="quorum_porcentaje">
          <input
            id="quorum_porcentaje"
            type="number"
            min="0"
            max="100"
            step="0.01"
            className="campo"
            value={estado.quorum_porcentaje}
            onChange={(evento) => actualizarCampo('quorum_porcentaje', evento.target.value)}
            placeholder="80"
          />
        </Campo>
      </div>

      <div className="grid gap-4 md:grid-cols-12">
        <Campo
          etiqueta="Presidente de la asamblea"
          requerido
          error={errores.presidente}
          className="md:col-span-6"
        >
          <input
            className="campo"
            value={estado.presidente}
            onChange={(evento) => actualizarCampo('presidente', evento.target.value)}
            placeholder="Ana María Ruiz Salazar"
          />
        </Campo>
        <Campo
          etiqueta="Secretario de la asamblea"
          requerido
          error={errores.secretario}
          className="md:col-span-6"
        >
          <input
            className="campo"
            value={estado.secretario}
            onChange={(evento) => actualizarCampo('secretario', evento.target.value)}
            placeholder="Carlos Peña Domínguez"
          />
        </Campo>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50/60 px-4 py-3">
        <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
          <span className="text-slate-600">
            Acciones representadas:{' '}
            <strong className="text-slate-800">{numero(calculos.accionesPresentes)}</strong>
          </span>
          <span className="text-slate-600">
            Quórum:{' '}
            <strong className={quorumInsuficiente ? 'text-red-600' : 'text-emerald-700'}>
              {porcentaje(calculos.quorum, 2)}
            </strong>
          </span>
          {calculos.accionesTotales > 0 ? (
            <Etiqueta tono={quorumInsuficiente ? 'error' : 'exito'}>
              {quorumInsuficiente ? 'Quórum insuficiente' : 'Quórum suficiente'}
            </Etiqueta>
          ) : null}
          <span className="text-slate-600">
            Capital social: <strong className="text-slate-800">{moneda(estado.capital_social)}</strong>
          </span>
        </div>
        <Boton variante="secundario" tamano="sm" onClick={() => despachar({ tipo: 'asistente.agregar' })}>
          + Agregar asistente
        </Boton>
      </div>

      {quorumInsuficiente ? (
        <Alerta tono="advertencia" titulo="Quórum por debajo del mínimo">
          El capital representado es menor al 50% requerido para sesionar. Documenta que se trata de
          segunda convocatoria (art. 191 LGSM) o recaba las representaciones faltantes.
        </Alerta>
      ) : null}

      {esExtraordinaria && calculos.quorum > 0 && calculos.quorum < 75 ? (
        <Alerta tono="info" titulo="Asamblea extraordinaria">
          En primera convocatoria se requiere el 75% del capital social (art. 190 LGSM). Si se trata
          de segunda convocatoria, basta la mayoría de las acciones representadas.
        </Alerta>
      ) : null}

      {errores.asistentes ? <Alerta tono="error">{errores.asistentes}</Alerta> : null}

      <div className="space-y-3">
        {estado.asistentes.map((asistente, indice) => (
          <EditorAsistente
            key={asistente.clave || `asistente-${indice}`}
            asistente={asistente}
            indice={indice}
            porcentajeCalculado={calculos.porcentajes?.[indice] || 0}
            onCambiar={(posicion, cambios) =>
              despachar({ tipo: 'asistente.actualizar', indice: posicion, cambios })
            }
            onEliminar={(posicion) => despachar({ tipo: 'asistente.eliminar', indice: posicion })}
          />
        ))}
        {!estado.asistentes.length ? (
          <p className="rounded-xl border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-500">
            Aún no hay asistentes registrados. Utiliza «Agregar asistente» para comenzar.
          </p>
        ) : null}
      </div>

    </div>
  )
}
