import Campo from '../ui/Campo.jsx'
import { TIPOS_ASAMBLEA } from '../../constants/catalogos.js'
import { fechaLarga, moneda } from '../../utils/formato.js'

/** Paso 1 del formulario: empresa, fecha, hora y tipo de asamblea. */
export default function PasoDatosGenerales({ estado, actualizarCampo, errores = {} }) {
  const tipoSeleccionado = TIPOS_ASAMBLEA.find((tipo) => tipo.valor === estado.tipo_asamblea)

  return (
    <div className="space-y-5">
      <div className="grid gap-4 md:grid-cols-2">
        <Campo
          etiqueta="Sociedad / Empresa"
          requerido
          error={errores.sociedad}
          ayuda="Razón social tal como aparece en el acta constitutiva."
          htmlFor="sociedad"
        >
          <input
            id="sociedad"
            className="campo"
            value={estado.sociedad}
            onChange={(evento) => actualizarCampo('sociedad', evento.target.value)}
            placeholder="Comercializadora del Norte, S.A. de C.V."
          />
        </Campo>

        <Campo etiqueta="R.F.C." ayuda="Opcional, se imprime en el encabezado del acta." htmlFor="rfc_sociedad">
          <input
            id="rfc_sociedad"
            className="campo uppercase"
            maxLength={13}
            value={estado.rfc_sociedad}
            onChange={(evento) => actualizarCampo('rfc_sociedad', evento.target.value.toUpperCase())}
            placeholder="CDN950101ABC"
          />
        </Campo>

        <Campo
          etiqueta="Tipo de asamblea"
          requerido
          ayuda={tipoSeleccionado?.descripcion}
          htmlFor="tipo_asamblea"
        >
          <select
            id="tipo_asamblea"
            className="campo"
            value={estado.tipo_asamblea}
            onChange={(evento) => actualizarCampo('tipo_asamblea', evento.target.value)}
          >
            {TIPOS_ASAMBLEA.map((tipo) => (
              <option key={tipo.valor} value={tipo.valor}>
                {tipo.etiqueta}
              </option>
            ))}
          </select>
        </Campo>

        <Campo
          etiqueta="Asunto principal"
          ayuda="Resumen del objeto de la asamblea (opcional)."
          htmlFor="titulo"
        >
          <input
            id="titulo"
            className="campo"
            value={estado.titulo}
            onChange={(evento) => actualizarCampo('titulo', evento.target.value)}
            placeholder="Aumento de capital y reforma estatutaria"
          />
        </Campo>

        <Campo etiqueta="Fecha de celebración" requerido error={errores.fecha} htmlFor="fecha">
          <input
            id="fecha"
            type="date"
            className="campo"
            value={estado.fecha}
            onChange={(evento) => actualizarCampo('fecha', evento.target.value)}
          />
        </Campo>

        <Campo etiqueta="Hora de inicio" htmlFor="hora">
          <input
            id="hora"
            type="time"
            className="campo"
            value={estado.hora}
            onChange={(evento) => actualizarCampo('hora', evento.target.value)}
          />
        </Campo>

        <Campo
          etiqueta="Lugar de la reunión"
          requerido
          error={errores.lugar}
          className="md:col-span-2"
          htmlFor="lugar"
        >
          <input
            id="lugar"
            className="campo"
            value={estado.lugar}
            onChange={(evento) => actualizarCampo('lugar', evento.target.value)}
            placeholder="Av. Paseo de la Reforma 1234, Ciudad de México"
          />
        </Campo>
      </div>

      <fieldset className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
        <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-corporativo-600">
          Convocatoria (arts. 186 y 187 LGSM)
        </legend>
        <div className="grid gap-4 md:grid-cols-3">
          <Campo etiqueta="Fecha de convocatoria" error={errores.convocatoria_fecha} htmlFor="convocatoria_fecha">
            <input
              id="convocatoria_fecha"
              type="date"
              className="campo"
              value={estado.convocatoria_fecha}
              onChange={(evento) => actualizarCampo('convocatoria_fecha', evento.target.value)}
            />
          </Campo>
          <Campo etiqueta="Quién convoca" htmlFor="convocatoria_quien">
            <input
              id="convocatoria_quien"
              className="campo"
              value={estado.convocatoria_quien}
              onChange={(evento) => actualizarCampo('convocatoria_quien', evento.target.value)}
            />
          </Campo>
          <Campo etiqueta="Medio de convocatoria" htmlFor="convocatoria_medio">
            <input
              id="convocatoria_medio"
              className="campo"
              value={estado.convocatoria_medio}
              onChange={(evento) => actualizarCampo('convocatoria_medio', evento.target.value)}
            />
          </Campo>
        </div>
      </fieldset>

      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-500">
        <span>
          Fecha interpretada: <strong className="text-slate-700">{fechaLarga(estado.fecha)}</strong>
        </span>
        {estado.capital_social ? (
          <span>
            Capital social capturado:{' '}
            <strong className="text-slate-700">{moneda(estado.capital_social)}</strong>
          </span>
        ) : null}
      </div>
    </div>
  )
}
