import { useCallback, useEffect, useMemo, useState } from 'react'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import ActasWizard from '../components/wizard/ActasWizard.jsx'
import {
  construirPayload,
  estadoDesdeActa,
  useActaWizard,
  validarPaso,
} from '../hooks/useActaWizard.js'
import {
  generarPdf,
  mensajeDeError,
  redactarActa,
  redactarEnVivo,
} from '../api/client.js'
import { descargarBlob } from '../utils/archivos.js'

const PASOS_A_EXPORTAR = [1, 2, 3]

/**
 * Arma el cuerpo de ``POST /actas/generar-pdf``.
 *
 * Si ya existe un borrador revisado por el usuario se envía con
 * ``generar_clausulas: false`` para que el PDF reproduzca exactamente el texto
 * revisado (sin volver a redactarlo) y, si se edita un acta guardada, se pide al
 * backend que incremente la versión.
 */
function payloadParaPdf(estado, borrador, actaInicial) {
  const base = construirPayload(estado)
  const extra = actaInicial?.id ? { actualizar_acta_id: actaInicial.id } : {}

  if (!borrador) return { ...base, ...extra }

  return {
    ...base,
    ...extra,
    generar_clausulas: false,
    acuerdos: (borrador.acuerdos || []).map((acuerdo, indice) => ({
      ...acuerdo,
      numero: indice + 1,
    })),
  }
}

/** Página «Generar acta»: formulario por pasos + borrador con IA + PDF final. */
export default function GenerarActa({ actaInicial = null, plantillaTipo = null, onVolver = null, onCerrarEdicion = null }) {
  const { estado, despachar, actualizarCampo, reiniciar, cargarActa, calculos, pasos } =
    useActaWizard(actaInicial ? estadoDesdeActa(actaInicial) : undefined)

  const [pasoActual, setPasoActual] = useState(1)
  const [errores, setErrores] = useState({})
  const [borrador, setBorrador] = useState(null)
  const [metadatosPdf, setMetadatosPdf] = useState(null)
  const [advertencias, setAdvertencias] = useState([])
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [cargandoRedaccion, setCargandoRedaccion] = useState(false)
  const [cargandoPdf, setCargandoPdf] = useState(false)
  const [redaccionEnVivo, setRedaccionEnVivo] = useState(null)

  // Cuando se elige un acta en la biblioteca, se carga en el formulario.
  useEffect(() => {
    if (!actaInicial) return
    cargarActa(actaInicial)
    setBorrador(null)
    setMetadatosPdf(null)
    setAdvertencias([])
    setError(null)
    setErrores({})
    setPasoActual(1)
  }, [actaInicial, cargarActa])

  // Cuando se elige una plantilla en el panel, se precarga el tipo de asamblea.
  useEffect(() => {
    if (actaInicial || !plantillaTipo) return
    reiniciar()
    actualizarCampo('tipo_asamblea', plantillaTipo)
    setBorrador(null)
    setMetadatosPdf(null)
    setAdvertencias([])
    setError(null)
    setErrores({})
    setAviso(null)
    setPasoActual(1)
    // Solo al montar / cambiar de plantilla.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plantillaTipo])

  /** Pasos cuya validación ya se cumple (se muestran con palomita). */
  const completados = useMemo(
    () =>
      pasos
        .filter(
          (paso) => paso.id < pasoActual && !Object.keys(validarPaso(paso.id, estado)).length,
        )
        .map((paso) => paso.id),
    [pasos, pasoActual, estado],
  )

  /** Navegación: valida los pasos intermedios antes de avanzar. */
  const irAPaso = useCallback(
    (destino) => {
      const objetivo = Math.min(Math.max(destino, 1), pasos.length)
      if (objetivo > pasoActual) {
        for (let numero = pasoActual; numero < objetivo; numero += 1) {
          const fallos = validarPaso(numero, estado)
          if (Object.keys(fallos).length) {
            setErrores(fallos)
            setPasoActual(numero)
            return
          }
        }
      }
      setErrores({})
      setPasoActual(objetivo)
    },
    [pasoActual, pasos.length, estado],
  )

  /** «Generar borrador con IA»: POST /actas/redactar (no persiste ni exporta). */
  const handleRedactar = async () => {
    setCargandoRedaccion(true)
    setError(null)
    try {
      const respuesta = await redactarActa({ ...construirPayload(estado), guardar: false })
      setBorrador(respuesta)
      setAdvertencias(respuesta.advertencias || [])
      setMetadatosPdf(null)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setCargandoRedaccion(false)
    }
  }

  /** «Ver redacción en vivo»: POST /actas/redactar-stream (SSE, primer acuerdo). */
  const handleRedactarEnVivo = async () => {
    if (!estado.acuerdos.length) {
      setError('Agrega al menos un acuerdo en el paso 3 antes de generar la redacción.')
      setPasoActual(3)
      return
    }

    setCargandoRedaccion(true)
    setError(null)
    setRedaccionEnVivo({ texto: '', generando: true, proveedor: null, acuerdo: null })
    try {
      await redactarEnVivo(
        { ...construirPayload(estado), guardar: false },
        {
          alInicio: (datos) =>
            setRedaccionEnVivo({
              texto: '',
              generando: true,
              proveedor: datos.proveedor,
              acuerdo: datos.acuerdo,
            }),
          alFragmento: (_fragmento, acumulado) =>
            setRedaccionEnVivo((previo) => ({
              ...(previo || {}),
              texto: acumulado,
              generando: true,
            })),
        },
      )
      setRedaccionEnVivo((previo) => ({ ...(previo || {}), generando: false }))
    } catch (fallo) {
      setRedaccionEnVivo(null)
      setError(mensajeDeError(fallo))
    } finally {
      setCargandoRedaccion(false)
    }
  }

  /** «Descargar PDF final»: POST /actas/generar-pdf -> Blob + metadatos. */
  const handleDescargarPdf = async () => {
    for (const numero of PASOS_A_EXPORTAR) {
      const fallos = validarPaso(numero, estado)
      if (Object.keys(fallos).length) {
        setErrores(fallos)
        setPasoActual(numero)
        setError('Revisa los campos señalados antes de generar el PDF.')
        return
      }
    }

    setCargandoPdf(true)
    setError(null)
    try {
      const resultado = await generarPdf(payloadParaPdf(estado, borrador, actaInicial))
      setMetadatosPdf(resultado)
      setAdvertencias(resultado.advertencias ? [resultado.advertencias] : [])
      descargarBlob(resultado.blob, resultado.nombreArchivo)
      setAviso(`PDF descargado: ${resultado.nombreArchivo}`)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargandoPdf(false)
    }
  }

  /** Reinicia el formulario por completo y sale del modo edición. */
  const handleNuevaActa = () => {
    reiniciar()
    setBorrador(null)
    setMetadatosPdf(null)
    setAdvertencias([])
    setErrores({})
    setAviso(null)
    setError(null)
    setPasoActual(1)
    if (onCerrarEdicion) onCerrarEdicion()
  }

  return (
    <div className="space-y-5">
      <header>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-corporativo-700">
              {actaInicial ? `Editando el acta ${actaInicial.folio}` : 'Generar acta corporativa'}
            </h1>
            <p className="text-sm text-slate-500">
              Captura los datos en tres pasos; la plataforma redacta el cuerpo legal, valida su
              consistencia y exporta el PDF formal listo para firma.
            </p>
          </div>
          {onVolver ? (
            <Boton variante="secundario" tamano="sm" onClick={onVolver}>
              ← Volver al panel
            </Boton>
          ) : null}
        </div>
      </header>

      {actaInicial ? (
        <Alerta tono="info" titulo="Modo edición">
          Al exportar el PDF se guardará una nueva versión del acta {actaInicial.folio}.
        </Alerta>
      ) : null}

      <ActasWizard
        pasos={pasos}
        pasoActual={pasoActual}
        onCambiarPaso={irAPaso}
        pasosCompletados={completados}
        estado={estado}
        calculos={calculos}
        despachar={despachar}
        actualizarCampo={actualizarCampo}
        errores={errores}
        borrador={borrador}
        advertencias={advertencias}
        metadatosPdf={metadatosPdf}
        aviso={aviso}
        redaccionEnVivo={redaccionEnVivo}
        cargandoRedaccion={cargandoRedaccion}
        cargandoPdf={cargandoPdf}
        error={error}
        onRedactar={handleRedactar}
        onRedactarEnVivo={handleRedactarEnVivo}
        onDescargarPdf={handleDescargarPdf}
        onNuevaActa={handleNuevaActa}
        actaId={actaInicial?.id || null}
      />
    </div>
  )
}

