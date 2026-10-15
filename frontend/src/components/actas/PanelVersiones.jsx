/**
 * Panel de versiones de un acta: historial completo con su motivo y contenido.
 *
 * Al seleccionar una versión se muestra un desglose de la instantánea y se ofrece
 * restaurarla. Restaurar **no** retrocede el contador: el backend emite una
 * versión nueva con el contenido recuperado, para no romper la auditoría.
 */
import { useCallback, useEffect, useState } from 'react'
import Alerta from '../ui/Alerta.jsx'
import Boton from '../ui/Boton.jsx'
import Etiqueta from '../ui/Etiqueta.jsx'
import {
  mensajeDeError,
  obtenerVersion,
  obtenerVersiones,
  restaurarVersion,
} from '../../api/client.js'
import { fechaCorta, marcaTiempo } from '../../utils/formato.js'

const CAMPOS_VISIBLES = [
  ['sociedad', 'Sociedad'],
  ['fecha', 'Fecha de la asamblea'],
  ['estatus', 'Estatus'],
  ['presidente', 'Presidente'],
  ['secretario', 'Secretario'],
  ['quorum_porcentaje', 'Quórum (%)'],
  ['texto_legal', 'Cuerpo legal'],
]

/** Muestra el valor de un campo de la instantánea en formato legible. */
function mostrarValor(campo, valor) {
  if (valor === null || valor === undefined || valor === '') return '—'
  if (Array.isArray(valor)) return `${valor.length} elemento(s)`
  if (typeof valor === 'object') return JSON.stringify(valor).slice(0, 80)
  if (['fecha', 'fecha_caducidad', 'convocatoria_fecha'].includes(campo)) {
    return fechaCorta(valor)
  }
  if (campo === 'texto_legal') return `${String(valor).length} caracteres`
  return String(valor)
}

export default function PanelVersiones({ acta, onCambio = null }) {
  const [versiones, setVersiones] = useState([])
  const [detalle, setDetalle] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [operando, setOperando] = useState(false)

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

  const restaurar = async (numero) => {
    const confirmado =
      typeof window === 'undefined' ||
      window.confirm(
        `¿Restaurar la versión ${numero} del acta ${acta.folio}? ` +
          'Se emitirá una versión nueva con ese contenido.',
      )
    if (!confirmado) return

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
                    {!vigente ? (
                      <Boton
                        tamano="sm"
                        variante="secundario"
                        cargando={operando && detalle?.version === version.version}
                        onClick={() => restaurar(version.version)}
                      >
                        Restaurar
                      </Boton>
                    ) : (
                      <Etiqueta tono="info">Vigente</Etiqueta>
                    )}
                  </div>
                </div>
              </li>
            )
          })}
        </ol>
      )}

      {detalle ? (
        <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-3">
          <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
            Contenido de la versión {detalle.version}
          </h4>
          <dl className="grid gap-x-6 gap-y-1 text-sm sm:grid-cols-2">
            {CAMPOS_VISIBLES.map(([campo, etiqueta]) => (
              <div key={campo} className="flex justify-between gap-2">
                <dt className="text-slate-500">{etiqueta}</dt>
                <dd className="text-right text-slate-700">
                  {mostrarValor(campo, detalle.contenido?.[campo])}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}
    </section>
  )
}
  }