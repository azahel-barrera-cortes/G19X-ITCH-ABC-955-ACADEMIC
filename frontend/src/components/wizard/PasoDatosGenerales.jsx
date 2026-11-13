import Campo from '../ui/Campo.jsx'
import {
  actaAplicable,
  requisitosParaActa,
  TIPOS_ASAMBLEA,
  TIPOS_SOCIEDAD,
} from '../../constants/catalogos.js'
import { fechaLarga, moneda } from '../../utils/formato.js'

/** Paso 1 del formulario: empresa, fecha, hora y tipo de acta corporativa. */
export default function PasoDatosGenerales({
  estado,
  actualizarCampo,
  errores = {},
  infoEmpresa = null,
  bloquearIdentidad = false,
}) {
  const tipoSeleccionado = TIPOS_ASAMBLEA.find((tipo) => tipo.valor === estado.tipo_asamblea)
  const tipoSociedadSeleccionado = TIPOS_SOCIEDAD.find((t) => t.valor === (estado.tipo_sociedad || (infoEmpresa?.tipo_sociedad || '')))
  const tipoSociedad = estado.tipo_sociedad || infoEmpresa?.tipo_sociedad || ''
  const actasDisponibles = TIPOS_ASAMBLEA.filter((tipo) => actaAplicable(tipoSociedad, tipo.valor))
  const requisitos = requisitosParaActa(estado.tipo_asamblea)
  const hayInfoGuardada = Boolean(
    infoEmpresa?.nombre_sociedad && infoEmpresa?.tipo_sociedad,
  )
  const empresaAsignada = Boolean(bloquearIdentidad || (infoEmpresa && hayInfoGuardada))
  const usaInfo = Boolean(infoEmpresa?.usar_info_empresa)

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
            onChange={(evento) => {
              if (!usaInfo && !bloquearIdentidad) actualizarCampo('sociedad', evento.target.value)
            }}
            placeholder="Comercializadora del Norte, S.A. de C.V."
            readOnly={usaInfo || bloquearIdentidad}
          />
        </Campo>

        <Campo etiqueta="R.F.C." ayuda="Opcional, se imprime en el encabezado del acta." htmlFor="rfc_sociedad">
          <input
            id="rfc_sociedad"
            className="campo uppercase"
            maxLength={13}
            value={estado.rfc_sociedad}
            onChange={(evento) => {
              if (!usaInfo) actualizarCampo('rfc_sociedad', evento.target.value.toUpperCase())
            }}
            placeholder="CDN950101ABC"
            readOnly={usaInfo}
          />
        </Campo>

        {empresaAsignada && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
            <p className="text-sm font-medium text-emerald-700">Datos de la empresa asignados por el administrador.</p>
            <p className="text-xs text-emerald-700 mt-1">
              {usaInfo
                ? <>Se usarán automáticamente para esta acta: <strong>{infoEmpresa.nombre_sociedad}</strong>.</>
                : 'El administrador decidió no usar esta información automáticamente para las actas.'}
            </p>
            <p className="text-xs text-emerald-700 mt-1">El administrador de la empresa puede modificar esta configuración desde su perfil.</p>
          </div>
        )}

        {!empresaAsignada && (
          <div className="md:col-span-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
            No se ha asignado empresa
          </div>
        )}

        {!usaInfo && (
          <Campo
            etiqueta="Tipo de sociedad"
            requerido
            error={errores.tipo_sociedad}
            ayuda="Determina la legislación y las actas corporativas que pueden generarse."
            htmlFor="tipo_sociedad_wizard"
          >
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
          etiqueta="Tipo de acta corporativa"
          requerido
          error={errores.tipo_asamblea}
          ayuda={tipoSeleccionado?.descripcion}
          htmlFor="tipo_asamblea"
        >
          <select
            id="tipo_asamblea"
            className="campo"
            value={estado.tipo_asamblea}
            disabled={bloquearIdentidad}
            onChange={(evento) => actualizarCampo('tipo_asamblea', evento.target.value)}
          >
            {actasDisponibles.map((tipo) => (
              <option key={tipo.valor} value={tipo.valor}>
                {tipo.etiqueta}
              </option>
            ))}
          </select>
          {bloquearIdentidad ? (
            <p className="mt-1 text-xs text-slate-500">
              El tipo de acta no se puede cambiar al editar un expediente existente.
            </p>
          ) : null}
        </Campo>

        <div className="md:col-span-2 rounded-xl border border-corporativo-100 bg-corporativo-50/50 p-4">
          <div className="mb-3">
            <h3 className="text-sm font-semibold text-corporativo-700">Datos jurídicos del acta</h3>
            <p className="mt-1 text-xs text-slate-600">
              Estos datos son necesarios para que la redacción y la validación correspondan al
              tipo de acta seleccionado. La plataforma no los sustituye con valores predeterminados.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {requisitos.map((requisito) => (
              <Campo
                key={requisito.clave}
                etiqueta={requisito.etiqueta}
                requerido={requisito.requerido}
                ayuda={requisito.ayuda}
                error={errores[`datos_especificos.${requisito.clave}`]}
                className={requisito.tipo === 'textarea' ? 'md:col-span-2' : ''}
              >
                {requisito.tipo === 'textarea' ? (
                  <textarea
                    className="campo"
                    rows={3}
                    value={estado.datos_especificos?.[requisito.clave] || ''}
                    onChange={(evento) =>
                      actualizarCampo('datos_especificos', {
                        ...(estado.datos_especificos || {}),
                        [requisito.clave]: evento.target.value,
                      })
                    }
                    placeholder={requisito.placeholder}
                  />
                ) : (
                  <input
                    className="campo"
                    type={requisito.tipo}
                    value={estado.datos_especificos?.[requisito.clave] || ''}
                    onChange={(evento) =>
                      actualizarCampo('datos_especificos', {
                        ...(estado.datos_especificos || {}),
                        [requisito.clave]: evento.target.value,
                      })
                    }
                    placeholder={requisito.placeholder}
                  />
                )}
              </Campo>
            ))}
          </div>
        </div>

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
