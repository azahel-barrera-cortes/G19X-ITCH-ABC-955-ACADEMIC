/**
 * Panel de versiones de un acta: historial completo con su motivo y contenido.
 *
 * Cada versión puede abrirse como documento y las versiones anteriores pueden
 * restaurarse. Restaurar **no** retrocede el contador: el backend emite una
 * versión nueva con el contenido recuperado, para no romper la auditoría.
 */
import { useCallback, useEffect, useState } from 'react'
import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import DialogoConfirmacion from '../ui/DialogoConfirmacion.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import VisorActa from './VisorActa.jsx'
import {
  mensajeDeError,
  obtenerVersion,
  obtenerVersiones,
  restaurarVersion,
} from '../../api/client.js'
import { marcaTiempo } from '../../utils/formato.js'

export default function PanelVersiones({ acta, onCambio = null, soloLectura = false }) {
  const [versiones, setVersiones] = useState([])
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [operando, setOperando] = useState(false)
  const [versionPendienteRestaurar, setVersionPendienteRestaurar] = useState(null)

  const cargar = useCallback(async () => {
    if (!acta?.id) return
    setCargando(true)
    setError(null)
    try {
      setVersiones(await obtenerVersiones(acta.id))
      setDetalle(null)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargando(false)
    }
  }, [acta?.id])

  useEffect(() => {
    cargar()
  }, [cargar])

  const verDetalle = async (numero) => {
    setOperando(true)
    setError(null)
    try {
      setDetalle(await obtenerVersion(acta.id, numero))
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(false)
    }
  }

  const restaurar = async () => {
    if (versionPendienteRestaurar === null) return
    const numero = versionPendienteRestaurar

    setOperando(true)
    setError(null)
    try {
      const restaurada = await restaurarVersion(acta.id, numero)
      setAviso(
        `Contenido restaurado desde la versión ${numero}; ahora es la v${restaurada.version}.`,
      )
      await cargar()
      onCambio?.(restaurada)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setOperando(false)
      setVersionPendienteRestaurar(null)
    }
  }

  return (
    <section className="tarjeta p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
          Historial de versiones · {acta.folio}
        </h3>
        <Boton tamano="sm" variante="fantasma" cargando={cargando} onClick={cargar}>
          Actualizar
        </Boton>
      </div>

      {error ? <Alerta tono="error">{error}</Alerta> : null}
      {aviso ? <Alerta tono="exito">{aviso}</Alerta> : null}

      {cargando ? (
        <p className="text-sm text-slate-500">Cargando historial…</p>
      ) : !versiones.length ? (
        <p className="text-sm text-slate-500">
          Este acta aún no tiene versiones registradas en el historial.
        </p>
      ) : (
        <ol className="space-y-2">
          {versiones.map((version) => {
            const vigente = version.version === acta.version
            return (
              <li
                key={version.id}
                className={`rounded-lg border px-3 py-2 ${
                  vigente ? 'border-corporativo-300 bg-corporativo-50/40' : 'border-slate-200'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Etiqueta tono={vigente ? 'info' : 'neutral'}>v{version.version}</Etiqueta>
                    <span className="text-sm text-slate-700">{version.motivo}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span>{marcaTiempo(version.created_at)}</span>
                    <Boton
                      tamano="sm"
                      variante="fantasma"
                      disabled={operando}
                      onClick={() => verDetalle(version.version)}
                    >
                      Ver
                    </Boton>
                    {!vigente && !soloLectura ? (
                      <Boton
                        tamano="sm"
                        variante="secundario"
                        cargando={operando && detalle?.version === version.version}
                        onClick={() => setVersionPendienteRestaurar(version.version)}
                      >
                        Restaurar
                      </Boton>
                    ) : vigente ? (
                      <Etiqueta tono="info">Vigente</Etiqueta>
                    ) : null}
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      )}

      {detalle ? (
        <VisorActa
          acta={acta}
          documentoVersion={detalle}
          onCerrar={() => setDetalle(null)}
        />
      ) : null}
      <DialogoConfirmacion
        abierto={versionPendienteRestaurar !== null}
        titulo="¿Restaurar esta versión?"
        descripcion={
          versionPendienteRestaurar !== null
            ? `Se creará una versión nueva del acta ${acta.folio} usando el contenido de la versión ${versionPendienteRestaurar}.`
            : ''
        }
        etiquetaConfirmar="Restaurar versión"
        varianteConfirmar="primario"
        cargando={operando}
        onCancelar={() => setVersionPendienteRestaurar(null)}
        onConfirmar={restaurar}
      />
    </section>
  )
}