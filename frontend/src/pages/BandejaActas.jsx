import { useCallback, useEffect, useState } from 'react'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import PanelValidacion from '../components/actas/PanelValidacion.jsx'
import PanelVersiones from '../components/actas/PanelVersiones.jsx'
import VisorActa from '../components/actas/VisorActa.jsx'
import {
  analizarRevisionActa,
  decidirActa,
  descargarPdfGuardado,
  mensajeDeError,
  obtenerBandejaActas,
} from '../api/client.js'
import { TIPOS_ASAMBLEA, etiquetaFlujoActa, etiquetaDe } from '../constants/catalogos.js'
import { descargarBlob } from '../utils/archivos.js'
import { fechaCorta, marcaTiempo } from '../utils/formato.js'

const CONFIGURACION = {
  capturista: {
    titulo: 'Mis actas',
    descripcion: 'Consulta el avance de tus actas y corrige las que fueron devueltas.',
  },
  revisor: {
    titulo: 'Revisión de actas',
    descripcion: 'Revisa cada nueva versión y apruébala para el Abogado o devuélvela con observaciones.',
  },
  abogado: {
    titulo: 'Aprobación de actas',
    descripcion: 'Revisa las actas del Revisor y las correcciones enviadas directamente a esta etapa.',
  },
}

export default function BandejaActas({ modo, onEditar = null }) {
  const [actas, setActas] = useState([])
  const [actaVisible, setActaVisible] = useState(null)
  const [versionesActaId, setVersionesActaId] = useState(null)
  const [comentarios, setComentarios] = useState({})
  const [analisisPorActa, setAnalisisPorActa] = useState({})
  const [analisisAbierto, setAnalisisAbierto] = useState({})
  const [cargando, setCargando] = useState(true)
  const [operando, setOperando] = useState(null)
  const [analizando, setAnalizando] = useState(null)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)

  const cargar = useCallback(async () => {
    setCargando(true)
    setError(null)
    try {
      setActas(await obtenerBandejaActas())
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    cargar()
  }, [cargar])

  const decidir = async (acta, accion) => {
    const comentario = comentarios[acta.id] || ''
    if (accion === 'devolver' && !comentario.trim()) {
      setError('Escribe las correcciones necesarias antes de devolver el acta.')
      return
    }
    setOperando(acta.id)
    setError(null)
    setAviso(null)
    try {
      const resultado = await decidirActa(acta.id, { accion, comentario })
      setAviso(
        accion === 'aprobar'
          ? `${acta.folio} pasó a ${etiquetaFlujoActa(resultado.estado_flujo)}.`
          : `${acta.folio} fue devuelta al Capturista con tus observaciones.`,
      )
      setComentarios((previo) => ({ ...previo, [acta.id]: '' }))
      await cargar()
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(null)
    }
  }

  const analizar = async (acta) => {
    if (analisisAbierto[acta.id]) {
      setAnalisisAbierto((previo) => ({ ...previo, [acta.id]: false }))
      return
    }
    if (analisisPorActa[acta.id]) {
      setAnalisisAbierto((previo) => ({ ...previo, [acta.id]: true }))
      return
    }

    setAnalizando(acta.id)
    setError(null)
    try {
      const resultado = await analizarRevisionActa(acta.id)
      setAnalisisPorActa((previo) => ({ ...previo, [acta.id]: resultado }))
      setAnalisisAbierto((previo) => ({ ...previo, [acta.id]: true }))
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setAnalizando(null)
    }
  }

  const agregarAnalisisAObservaciones = (acta, analisis) => {
    const validacion = analisis.validacion
    const texto = [
      `Análisis asistido de ${acta.folio} v${analisis.version_actual}: ${validacion.consistencia}`,
      ...validacion.hallazgos.map(
        (hallazgo) =>
          `- ${hallazgo.severidad}${hallazgo.campo ? ` · ${hallazgo.campo}` : ''}: ${hallazgo.mensaje}` +
          (hallazgo.sugerencia ? ` Sugerencia: ${hallazgo.sugerencia}` : ''),
      ),
      ...validacion.recomendaciones.map((recomendacion) => `- Recomendación: ${recomendacion}`),
    ].join('\n')
    setComentarios((previo) => ({
      ...previo,
      [acta.id]: [previo[acta.id], texto].filter(Boolean).join('\n\n').slice(0, 2000),
    }))
  }

  const descargar = async (acta) => {
    setOperando(acta.id)
    setError(null)
    try {
      const archivo = await descargarPdfGuardado(acta.id)
      descargarBlob(archivo.blob, archivo.nombreArchivo)
      setAviso(`PDF final de ${acta.folio} descargado.`)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(null)
    }
  }

  const filas = modo === 'revisor'
    ? actas.filter((acta) => acta.estado_flujo === 'revision')
    : modo === 'abogado'
      ? actas.filter((acta) => ['abogado', 'aprobada'].includes(acta.estado_flujo))
      : actas
  const configuracion = CONFIGURACION[modo]

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-corporativo-700">{configuracion.titulo}</h1>
          <p className="text-sm text-slate-500">{configuracion.descripcion}</p>
        </div>
        <Boton variante="secundario" cargando={cargando} onClick={cargar}>Actualizar</Boton>
      </header>

      {error ? <Alerta tono="error" titulo="No se pudo completar la operación">{error}</Alerta> : null}
      {aviso ? <Alerta tono="exito">{aviso}</Alerta> : null}

      {cargando && !actas.length ? (
        <section className="tarjeta p-6 text-sm text-slate-500">Cargando actas…</section>
      ) : !filas.length ? (
        <section className="tarjeta p-6 text-sm text-slate-500">
          No hay actas en esta bandeja por el momento.
        </section>
      ) : (
        <section className="space-y-3">
          {filas.map((acta) => {
            const pendienteRevision = modo === 'revisor' && acta.estado_flujo === 'revision'
            const pendienteAbogado = modo === 'abogado' && acta.estado_flujo === 'abogado'
            const puedeDecidir = pendienteRevision || pendienteAbogado
            const puedeAnalizar = modo === 'revisor' || modo === 'abogado'
            const analisis = analisisPorActa[acta.id]
            const estaAbierto = Boolean(analisisAbierto[acta.id])
            const ultimaDevolucion = [...(acta.historial_revision || [])]
              .reverse()
              .find((evento) => evento.accion === 'devolver')
            const devolvio = ultimaDevolucion?.etapa === 'abogado' ? 'Abogado' : 'Revisor'
            return (
              <article key={acta.id} className="tarjeta space-y-3 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-corporativo-600">{acta.folio} · v{acta.version}</p>
                    <h2 className="mt-1 font-semibold text-slate-800">{acta.sociedad}</h2>
                    <p className="text-sm text-slate-500">
                      {etiquetaDe(TIPOS_ASAMBLEA, acta.tipo_asamblea)} · {fechaCorta(acta.fecha)}
                    </p>
                  </div>
                  <Etiqueta tono={acta.estado_flujo === 'aprobada' ? 'exito' : acta.estado_flujo === 'con_errores' ? 'advertencia' : 'info'}>
                    {etiquetaFlujoActa(acta.estado_flujo)}
                  </Etiqueta>
                </div>

                {acta.comentario_revision ? (
                  <Alerta
                    tono="advertencia"
                    titulo={modo === 'capturista' ? `Observaciones del ${devolvio}` : 'Correcciones solicitadas'}
                  >
                    {acta.comentario_revision}
                  </Alerta>
                ) : null}

                {acta.historial_revision?.length ? (
                  <details className="rounded-lg border border-slate-200 px-3 py-2">
                    <summary className="cursor-pointer text-xs font-semibold text-corporativo-700">
                      Historial de revisión ({acta.historial_revision.length} movimientos)
                    </summary>
                    <ol className="mt-2 space-y-2">
                      {acta.historial_revision.map((evento, indice) => (
                        <li key={`${evento.version}-${indice}`} className="border-l-2 border-slate-200 pl-3 text-xs text-slate-600">
                          <p>
                            {evento.accion === 'aprobar' ? 'Aprobó' : evento.accion === 'devolver' ? 'Devolvió' : 'Reenvió'}
                            {' · '}{evento.rol} · {evento.usuario} · versión {evento.version}
                            {evento.creado_en ? ` · ${marcaTiempo(evento.creado_en)}` : ''}
                          </p>
                          {evento.comentario ? <p className="mt-1">{evento.comentario}</p> : null}
                        </li>
                      ))}
                    </ol>
                  </details>
                ) : null}

                {puedeDecidir ? (
                  <div>
                    <label className="etiqueta-campo" htmlFor={`comentario-${acta.id}`}>
                      Observaciones (obligatorias si devuelves el acta)
                    </label>
                    <textarea
                      id={`comentario-${acta.id}`}
                      className="campo"
                      rows={3}
                      maxLength={2000}
                      value={comentarios[acta.id] || ''}
                      onChange={(evento) =>
                        setComentarios((previo) => ({ ...previo, [acta.id]: evento.target.value }))
                      }
                      placeholder="Detalla los cambios que debe realizar el Capturista."
                    />
                  </div>
                ) : null}

                <div className="flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-3">
                  <Boton variante="secundario" onClick={() => setActaVisible(acta)}>Ver acta</Boton>
                  {puedeAnalizar ? (
                    <Boton
                      variante="secundario"
                      cargando={analizando === acta.id}
                      disabled={operando === acta.id}
                      aria-expanded={estaAbierto}
                      aria-controls={analisis ? `analisis-${acta.id}` : undefined}
                      onClick={() => analizar(acta)}
                    >
                      {estaAbierto ? 'Ocultar análisis' : analisis ? 'Mostrar análisis' : 'Analizar con IA'}
                    </Boton>
                  ) : null}
                  {modo === 'abogado' ? (
                    <Boton
                      variante="fantasma"
                      onClick={() => setVersionesActaId((actual) => actual === acta.id ? null : acta.id)}
                    >
                      {versionesActaId === acta.id ? 'Ocultar versiones' : 'Ver versiones'}
                    </Boton>
                  ) : null}
                  {modo === 'capturista' && acta.estado_flujo === 'con_errores' && onEditar ? (
                    <Boton variante="primario" onClick={() => onEditar(acta)}>Editar y corregir</Boton>
                  ) : null}
                  {puedeDecidir ? (
                    <>
                      <Boton
                        variante="peligro"
                        disabled={operando === acta.id}
                        onClick={() => decidir(acta, 'devolver')}
                      >
                        Devolver con errores
                      </Boton>
                      <Boton
                        variante="primario"
                        cargando={operando === acta.id}
                        onClick={() => decidir(acta, 'aprobar')}
                      >
                        {pendienteRevision
                          ? 'Marcar revisada y enviar al Abogado'
                          : 'Aprobar acta'}
                      </Boton>
                    </>
                  ) : null}
                  {modo === 'abogado' && acta.estado_flujo === 'aprobada' ? (
                    <Boton
                      variante="primario"
                      cargando={operando === acta.id}
                      onClick={() => descargar(acta)}
                    >
                      Descargar PDF final
                    </Boton>
                  ) : null}
                </div>
                {analisis && estaAbierto ? (
                  <section
                    id={`analisis-${acta.id}`}
                    className="space-y-3 rounded-xl border border-corporativo-100 bg-corporativo-50/40 p-4"
                  >
                    <div>
                      <h3 className="text-sm font-semibold text-corporativo-700">
                        Análisis asistido · versión {analisis.version_actual}
                      </h3>
                      <p className="mt-1 text-xs text-slate-600">
                        {analisis.version_comparada
                          ? `Comparada con la versión ${analisis.version_comparada}.`
                          : 'No hay una versión anterior para comparar.'}
                        {' '}El resultado es una ayuda y no sustituye la revisión profesional.
                      </p>
                    </div>
                    {analisis.cambios.length ? (
                      <p className="text-sm text-slate-700">
                        <span className="font-semibold">Secciones modificadas:</span>{' '}
                        {analisis.cambios.join(', ')}.
                      </p>
                    ) : null}
                    <PanelValidacion validacion={analisis.validacion} />
                    {puedeDecidir ? (
                      <div className="flex justify-end">
                        <Boton
                          tamano="sm"
                          variante="secundario"
                          onClick={() => agregarAnalisisAObservaciones(acta, analisis)}
                        >
                          Agregar análisis a observaciones
                        </Boton>
                      </div>
                    ) : null}
                  </section>
                ) : null}
                <p className="text-right text-xs text-slate-400">
                  Última actualización: {marcaTiempo(acta.updated_at)}
                </p>
                {modo === 'abogado' && versionesActaId === acta.id ? (
                  <PanelVersiones acta={acta} soloLectura />
                ) : null}
              </article>
            )
          })}
        </section>
      )}

      {actaVisible ? (
        <VisorActa
          acta={actaVisible}
          documentoInicial={actaVisible}
          onCerrar={() => setActaVisible(null)}
        />
      ) : null}
    </div>
  )
}
