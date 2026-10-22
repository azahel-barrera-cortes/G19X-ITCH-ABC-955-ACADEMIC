import Campo from '../ui/Campo.jsx'
import { TIPOS_ASAMBLEA, TIPOS_SOCIEDAD } from '../../constants/catalogos.js'
import { fechaLarga, moneda } from '../../utils/formato.js'

/** Paso 1 del formulario: empresa, fecha, hora y tipo de asamblea. */
export default function PasoDatosGenerales({ estado, actualizarCampo, errores = {}, infoEmpresa = null }) {
  const tipoSeleccionado = TIPOS_ASAMBLEA.find((tipo) => tipo.valor === estado.tipo_asamblea)
  const tipoSociedadSeleccionado = TIPOS_SOCIEDAD.find((t) => t.valor === (estado.tipo_sociedad || (infoEmpresa?.tipo_sociedad || '')))
  const hayInfoGuardada = infoEmpresa && infoEmpresa.nombre_sociedad
  const usaInfo = Boolean(estado.usar_info_empresa)

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

        {hayInfoGuardada && !usaInfo && (
          <div className="rounded-xl border border-corporativo-200 bg-corporativo-50 p-4">
            <p className="text-sm font-medium text-corporativo-700">¿Usar información de la sociedad guardada?</p>
            <p className="text-xs text-slate-600 mt-1">
              Se encontró información guardada en «Información de la empresa o sociedad»:
              <strong className="text-corporativo-700">{infoEmpresa.nombre_sociedad}</strong>
              ({tipoSociedadSeleccionado?.etiqueta || 'tipo no especificado'}).
              ¿Desea usarla para esta acta? La IA y el PDF podrán incluirla automáticamente.
            </p>
            <div className="flex items-center gap-2 mt-2">
              <input
                id="usar_info_empresa"
                type="checkbox"
                checked={usaInfo}
                onChange={() => actualizarCampo('usar_info_empresa', true)}
                className="campo"
              />
              <label htmlFor="usar_info_empresa" className="text-sm font-medium text-corporativo-700">
                Sí, usar esta información para generar el acta
              </label>
            </div>
          </div>
        )}

        {usaInfo && hayInfoGuardada && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-sm font-medium text-emerald-700">
              ✓ Usando información de la sociedad guardada: <strong>{infoEmpresa.nombre_sociedad}</strong>
            </p>
            <p className="text-xs text-emerald-600 mt-1">
              Se aplicará al encabezado, al tipo de sociedad y al logo del acta. Puedes desactivarlo en «Información de la empresa o sociedad».
            </p>
          </div>
        )}

        {!usaInfo && (
          <Campo etiqueta="Tipo de sociedad" ayuda="Tipo de sociedad mercantil (determina qué actas corporativas pueden generarse)." htmlFor="tipo_sociedad_wizard">
            <select
              id="tipo_sociedad_wizard"
              className="campo"
              value={estado.tipo_sociedad || ''}
              onChange={(evento) => actualizarCampo('tipo_sociedad', evento.target.value)}
            >
              <option value="">Selecciona un tipo de sociedad</option>
              {TIPOS_SOCIEDAD.map((tipo) => (
                <option key={tipo.valor} value={tipo.valor}>
                  {tipo.etiqueta}
                </option>
              ))}
            </select>
          </Campo>
        )}

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
