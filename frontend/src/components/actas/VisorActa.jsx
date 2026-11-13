import { useEffect, useState } from 'react'
import { obtenerActa, mensajeDeError } from '../../api/client.js'
import { ESTATUS_ACTA, TIPOS_ASAMBLEA, etiquetaDe } from '../../constants/catalogos.js'
import { fechaCorta } from '../../utils/formato.js'
import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import Indicador from '../ui/Indicador.jsx'

export default function VisorActa({
  acta,
  documentoVersion = null,
  documentoInicial = null,
  onCerrar,
}) {
  const [documento, setDocumento] = useState(documentoInicial)
  const [cargando, setCargando] = useState(!documentoVersion && !documentoInicial)
  const [error, setError] = useState('')

  useEffect(() => {
    if (documentoVersion) {
      setCargando(false)
      return
    }
    if (documentoInicial) {
      setDocumento(documentoInicial)
      setCargando(false)
      return
    }

    let montado = true
    obtenerActa(acta.id)
      .then((datos) => {
        if (montado) setDocumento(datos)
      })
      .catch(async (fallo) => {
        if (montado) setError(await mensajeDeError(fallo))
      })
      .finally(() => {
        if (montado) setCargando(false)
      })
    return () => {
      montado = false
    }
  }, [acta.id, documentoInicial, documentoVersion])

  const documentoMostrado = documentoVersion
    ? {
      ...documentoVersion.contenido,
      id: acta.id,
      folio: documentoVersion.contenido?.folio || acta.folio,
      version: documentoVersion.version,
      estatus: documentoVersion.contenido?.estatus || documentoVersion.estatus,
    }
    : documento

  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/50 p-3 sm:p-6">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="visor-acta-titulo"
        className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl bg-slate-100 shadow-2xl"
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 bg-white px-5 py-4">
          <div>
            <p className="font-mono text-xs font-semibold text-corporativo-600">{acta.folio}</p>
            <h2 id="visor-acta-titulo" className="mt-1 text-lg font-bold text-slate-900">
              {documentoVersion
                ? `Visualizador de acta · versión ${documentoVersion.version}`
                : 'Visualizador de acta'}
            </h2>
          </div>
          <Boton variante="secundario" tamano="sm" onClick={onCerrar}>Cerrar</Boton>
        </header>

        <div className="overflow-y-auto p-4 sm:p-6">
          {cargando ? (
            <div className="flex items-center justify-center gap-2 py-12 text-sm text-slate-500">
              <Indicador /> Cargando documento…
            </div>
          ) : error ? (
            <Alerta tono="error" titulo="No se pudo abrir el acta">{error}</Alerta>
          ) : documentoMostrado ? (
            <article className="mx-auto max-w-3xl border border-slate-300 bg-white p-6 font-serif text-sm leading-relaxed text-slate-800 shadow-sm sm:p-10">
              <header className="border-b border-slate-300 pb-5 text-center">
                <p className="font-mono text-xs text-slate-500">{documentoMostrado.folio}</p>
                <h3 className="mt-2 text-lg font-bold uppercase text-corporativo-700">
                  {documentoMostrado.titulo || etiquetaDe(TIPOS_ASAMBLEA, documentoMostrado.tipo_asamblea)}
                </h3>
                <p className="mt-2 font-semibold">{documentoMostrado.sociedad}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {fechaCorta(documentoMostrado.fecha)} · {documentoMostrado.lugar || 'Lugar no especificado'}
                </p>
                <div className="mt-3 flex flex-wrap justify-center gap-2 font-sans">
                  <Etiqueta tono="info">Versión {documentoMostrado.version}</Etiqueta>
                  <Etiqueta tono={documentoMostrado.estatus === 'aprobada' ? 'exito' : 'neutral'}>
                    {etiquetaDe(ESTATUS_ACTA, documentoMostrado.estatus)}
                  </Etiqueta>
                </div>
              </header>

              <section className="mt-5">
                <h4 className="font-bold uppercase text-corporativo-600">Datos de la sesión</h4>
                <dl className="mt-2 grid gap-x-6 gap-y-1 sm:grid-cols-2">
                  <Dato etiqueta="Presidente" valor={documentoMostrado.presidente} />
                  <Dato etiqueta="Secretario" valor={documentoMostrado.secretario} />
                  <Dato etiqueta="Quórum" valor={documentoMostrado.quorum_porcentaje != null ? `${documentoMostrado.quorum_porcentaje}%` : null} />
                  <Dato etiqueta="RFC" valor={documentoMostrado.rfc_sociedad} />
                </dl>
              </section>

              {documentoMostrado.asistentes?.length ? (
                <section className="mt-5">
                  <h4 className="font-bold uppercase text-corporativo-600">Asistentes</h4>
                  <ul className="mt-2 list-inside list-disc">
                    {documentoMostrado.asistentes.map((asistente, indice) => (
                      <li key={asistente.clave || `${asistente.nombre}-${indice}`}>
                        {asistente.nombre || 'Sin nombre'}
                        {asistente.caracter ? ` · ${String(asistente.caracter).replaceAll('_', ' ')}` : ''}
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {documentoMostrado.orden_del_dia?.length ? (
                <section className="mt-5">
                  <h4 className="font-bold uppercase text-corporativo-600">Orden del día</h4>
                  <ol className="mt-2 list-inside list-decimal space-y-1">
                    {documentoMostrado.orden_del_dia.map((punto, indice) => (
                      <li key={punto.clave || `${punto.titulo}-${indice}`}>
                        {punto.titulo || 'Punto sin título'}
                        {punto.descripcion ? ` — ${punto.descripcion}` : ''}
                      </li>
                    ))}
                  </ol>
                </section>
              ) : null}

              {documentoMostrado.acuerdos?.length ? (
                <section className="mt-5">
                  <h4 className="font-bold uppercase text-corporativo-600">Acuerdos y resoluciones</h4>
                  <div className="mt-2 space-y-4">
                    {documentoMostrado.acuerdos.map((acuerdo, indice) => (
                      <div key={acuerdo.clave || `${acuerdo.numero}-${indice}`}>
                        <p className="font-bold">
                          {acuerdo.numero ? `Acuerdo ${acuerdo.numero}. ` : ''}
                          {acuerdo.titulo || 'Resolución'}
                        </p>
                        <p className="mt-1 whitespace-pre-wrap text-justify">
                          {acuerdo.clausula_legal || acuerdo.resumen || 'Sin texto registrado.'}
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              ) : documentoMostrado.texto_legal ? (
                <section className="mt-5">
                  <h4 className="font-bold uppercase text-corporativo-600">Texto del acta</h4>
                  <p className="mt-2 whitespace-pre-wrap text-justify">{documentoMostrado.texto_legal}</p>
                </section>
              ) : null}
            </article>
          ) : null}
        </div>
      </section>
    </div>
  )
}

function Dato({ etiqueta, valor }) {
  return (
    <div className="flex justify-between gap-3 border-b border-slate-100 py-1">
      <dt className="text-slate-500">{etiqueta}</dt>
      <dd className="text-right font-medium">{valor || '—'}</dd>
    </div>
  )
}
