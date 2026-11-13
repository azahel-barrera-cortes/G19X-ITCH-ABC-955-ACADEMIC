import Alerta from '../ui/Alerta.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import Boton from '../ui/Boton.jsx'
import PanelValidacion from '../actas/PanelValidacion.jsx'
import VistaPreviaActa from '../actas/VistaPreviaActa.jsx'
import { fechaCorta, numero, porcentaje } from '../../utils/formato.js'

const OPCIONES_DOCUMENTO = [
  ['generar_clausulas', 'Redactar cláusulas con IA / plantillas'],
  ['incluir_validacion', 'Ejecutar validación de consistencia'],
]

/**
 * Paso 4: revisión de la redacción y envío del acta al flujo de aprobación.
 */
export default function PasoRevision({
  estado,
  calculos,
  actualizarCampo,
  borrador,
  advertencias = [],
  aviso = null,
  redaccionEnVivo = null,
  cargandoRedaccion = false,
  cargandoEnvio = false,
  cargandoGuardar = false,
  error = null,
  onRedactar,
  onRedactarEnVivo,
  onEnviarRevision,
  onGuardarBorrador,
  onCancelarEdicion,
  onNuevaActa,
  actaId = null,
  esCorreccion = false,
}) {
  const validacion = borrador?.validacion || null

  return (
    <div className="space-y-5">
      {error ? (
        <Alerta tono="error" titulo="No se pudo completar la operación">
          {error}
        </Alerta>
      ) : null}

      {aviso ? (
        <Alerta tono="exito" titulo="Listo">
          {aviso}
        </Alerta>
      ) : null}

      {advertencias.length ? (
        <Alerta tono="advertencia" titulo="Avisos del servicio de IA">
          {advertencias.map((texto, indice) => (
            <p key={`advertencia-${indice}`}>{texto}</p>
          ))}
        </Alerta>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="tarjeta p-4 lg:col-span-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
            Resumen del acta
          </h3>
          <dl className="mt-3 grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
            <div className="sm:col-span-2">
              <dt className="text-xs uppercase text-slate-500">Sociedad</dt>
              <dd className="font-medium text-slate-800">{estado.sociedad || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-500">Fecha / hora</dt>
              <dd className="text-slate-700">
                {fechaCorta(estado.fecha)} · {estado.hora || '—'}
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-500">Lugar</dt>
              <dd className="text-slate-700">{estado.lugar || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-500">Asistentes</dt>
              <dd className="text-slate-700">
                {estado.asistentes.length} · {numero(calculos.accionesPresentes)} acciones ·{' '}
                {porcentaje(calculos.quorum, 2)} de quórum
              </dd>
            </div>
            <div>
              <dt className="text-xs uppercase text-slate-500">Cuerpo del acta</dt>
              <dd className="text-slate-700">
                {estado.orden_del_dia.length} punto(s) · {estado.acuerdos.length} acuerdo(s)
              </dd>
            </div>
            {actaId ? (
              <div className="sm:col-span-2">
                <dt className="text-xs uppercase text-slate-500">Acta en edición</dt>
                <dd className="text-slate-700">
                  Identificador {actaId}: se generará una nueva versión al guardar.
                </dd>
              </div>
            ) : null}
          </dl>
        </div>

        <div className="tarjeta p-4">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
            Opciones de redacción
          </h3>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            {OPCIONES_DOCUMENTO.map(([campo, etiqueta]) => (
              <label key={campo} className="flex items-start gap-2">
                <input
                  type="checkbox"
                  className="mt-0.5 h-4 w-4 rounded border-slate-300 text-corporativo-500 focus:ring-corporativo-200"
                  checked={estado[campo] !== false}
                  onChange={(evento) => actualizarCampo(campo, evento.target.checked)}
                />
                <span>{etiqueta}</span>
              </label>
            ))}
          </div>

          <div className="mt-4">
            <label className="etiqueta-campo" htmlFor="instrucciones_adicionales">
              Instrucciones para la IA (opcional)
            </label>
            <textarea
              id="instrucciones_adicionales"
              rows={3}
              className="campo"
              value={estado.instrucciones_adicionales || ''}
              onChange={(evento) => actualizarCampo('instrucciones_adicionales', evento.target.value)}
              placeholder="Ej.: menciona expresamente el derecho de preferencia del artículo 132 LGSM."
            />
          </div>
        </div>
      </section>

      <section className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
        <Boton
          variante="secundario"
          cargando={cargandoRedaccion}
          disabled={cargandoEnvio}
          onClick={onRedactar}
        >
          Generar borrador con IA
        </Boton>
        <Boton
          variante="fantasma"
          cargando={cargandoRedaccion}
          disabled={cargandoEnvio}
          onClick={onRedactarEnVivo}
        >
          Ver redacción en vivo
        </Boton>
        {actaId ? (
          <Boton
            variante="primario"
            cargando={cargandoGuardar}
            disabled={cargandoRedaccion || cargandoEnvio}
            onClick={onGuardarBorrador}
          >
            {esCorreccion ? 'Guardar cambios y reenviar' : 'Guardar cambios'}
          </Boton>
        ) : (
          <Boton
            variante="primario"
            cargando={cargandoEnvio}
            disabled={cargandoRedaccion}
            onClick={onEnviarRevision}
          >
            Enviar a revisión
          </Boton>
        )}
        <span className="flex-1" />
        {actaId ? (
          <Boton variante="fantasma" disabled={cargandoGuardar} onClick={onCancelarEdicion}>
            Cancelar edición
          </Boton>
        ) : (
          <Boton variante="fantasma" onClick={onNuevaActa}>
            Empezar otra acta
          </Boton>
        )}
      </section>

      {redaccionEnVivo ? (
        <section className="tarjeta p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
              Redacción en vivo
            </h3>
            <Etiqueta tono="info">
              {redaccionEnVivo.proveedor || 'plantillas'} · acuerdo {redaccionEnVivo.acuerdo}
            </Etiqueta>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
            {redaccionEnVivo.texto}
            {redaccionEnVivo.generando ? (
              <span className="ml-0.5 animate-pulse text-corporativo-600">▌</span>
            ) : null}
          </p>
          <p className="mt-3 text-xs text-slate-500">
            Vista en vivo del primer acuerdo. Para incorporar las cláusulas de todos los acuerdos
            al acta usa «Generar borrador con IA».
          </p>
        </section>
      ) : null}

      {borrador ? (
        <section className="tarjeta p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-corporativo-600">
            Validación de consistencia
          </h3>
          <PanelValidacion validacion={validacion} />
        </section>
      ) : (
        <Alerta tono="info" titulo="Aún no hay borrador redactado">
          Pulsa «Generar borrador con IA» para redactar las cláusulas legales y validar la consistencia
          antes de enviar el acta a revisión.
        </Alerta>
      )}

      <section>
        <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-corporativo-600">
          Vista previa del documento
        </h3>
        <VistaPreviaActa estado={estado} calculos={calculos} borrador={borrador} />
      </section>

    </div>
  )
}
