import Alerta from '../ui/Alerta.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import Boton from '../ui/Boton.jsx'
import PanelValidacion from '../actas/PanelValidacion.jsx'
import VistaPreviaActa from '../actas/VistaPreviaActa.jsx'
import { abrirBlob, descargarBlob } from '../../utils/archivos.js'
import { fechaCorta, numero, porcentaje } from '../../utils/formato.js'

const OPCIONES_DOCUMENTO = [
  ['guardar', 'Guardar el acta en el historial'],
  ['generar_clausulas', 'Redactar cláusulas con IA / plantillas'],
  ['incluir_validacion', 'Ejecutar validación de consistencia'],
  ['incluir_tabla_asistentes', 'Incluir tabla de asistentes'],
  ['incluir_hoja_firmas', 'Incluir hoja de firmas'],
  ['incluir_anexo_validacion', 'Incluir anexo de validación'],
]

/**
 * Paso 4: revisión, validación de IA y exportación a PDF.
 *
 * Reúne las dos acciones clave del flujo del PGAC:
 *   · «Generar borrador con IA» -> POST /actas/redactar
 *   · «Descargar PDF final»     -> POST /actas/generar-pdf (respuesta Blob)
 */
export default function PasoRevision({
  estado,
  calculos,
  actualizarCampo,
  borrador,
  advertencias = [],
  metadatosPdf = null,
  aviso = null,
  redaccionEnVivo = null,
  cargandoRedaccion = false,
  cargandoPdf = false,
  error = null,
  onRedactar,
  onRedactarEnVivo,
  onDescargarPdf,
  onNuevaActa,
  actaId = null,
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
            Opciones del documento
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
          disabled={cargandoPdf}
          onClick={onRedactar}
        >
          Generar borrador con IA
        </Boton>
        <Boton
          variante="fantasma"
          cargando={cargandoRedaccion}
          disabled={cargandoPdf}
          onClick={onRedactarEnVivo}
        >
          Ver redacción en vivo
        </Boton>
        <Boton
          variante="primario"
          cargando={cargandoPdf}
          disabled={cargandoRedaccion}
          onClick={onDescargarPdf}
        >
          Descargar PDF final
        </Boton>
        {metadatosPdf ? (
          <>
            <Boton
              variante="fantasma"
              onClick={() => descargarBlob(metadatosPdf.blob, metadatosPdf.nombreArchivo)}
            >
              Volver a descargar
            </Boton>
            <Boton variante="fantasma" onClick={() => abrirBlob(metadatosPdf.blob)}>
              Abrir en otra pestaña
            </Boton>
          </>
        ) : null}
        <span className="flex-1" />
        <Boton variante="fantasma" onClick={onNuevaActa}>
          Empezar otra acta
        </Boton>
      </section>

      {metadatosPdf ? (
        <Alerta tono="exito" titulo={`PDF generado: ${metadatosPdf.nombreArchivo}`}>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs">
            <span>Folio: {metadatosPdf.folio || '—'}</span>
            <span>Versión: {metadatosPdf.version || '—'}</span>
            <span>Páginas: {metadatosPdf.paginas || '—'}</span>
            <span>Proveedor IA: {metadatosPdf.proveedorIa || '—'}</span>
            <span className="inline-flex items-center gap-1">
              Guardada:
              <Etiqueta tono={metadatosPdf.guardada ? 'exito' : 'neutral'}>
                {metadatosPdf.guardada ? 'sí' : 'no'}
              </Etiqueta>
            </span>
          </div>
        </Alerta>
      ) : null}

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
          Pulsa «Generar borrador con IA» para que la plataforma redacte las cláusulas legales y valide
          la consistencia del acta; después podrás descargar el PDF final.
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
