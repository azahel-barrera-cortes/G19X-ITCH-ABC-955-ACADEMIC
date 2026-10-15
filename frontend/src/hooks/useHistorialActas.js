/**
 * Historial de actas: listado con filtros y operaciones sobre cada registro
 * (descargar PDF, validar, cambiar estatus y eliminar).
 */
import { useCallback, useEffect, useState } from 'react'
import {
  cambiarEstatus,
  descargarPdfGuardado,
  eliminarActa,
  listarActas,
  mensajeDeError,
  validarActaGuardada,
} from '../api/client.js'
import { descargarBlob } from '../utils/archivos.js'

const FILTROS_INICIALES = { texto: '', tipo_asamblea: '', estatus: '' }

export function useHistorialActas() {
  const [actas, setActas] = useState([])
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [operando, setOperando] = useState(null)
  const [filtros, setFiltros] = useState(FILTROS_INICIALES)

  /** Consulta el listado aplicando los filtros vigentes. */
  const cargar = useCallback(async (filtrosAplicar) => {
    setCargando(true)
    setError(null)
    try {
      const datos = await listarActas({
        texto: filtrosAplicar.texto || undefined,
        tipo_asamblea: filtrosAplicar.tipo_asamblea || undefined,
        estatus: filtrosAplicar.estatus || undefined,
        limite: 100,
      })
      setActas(datos)
    } catch (fallo) {
      setError(mensajeDeError(fallo))
      setActas([])
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    cargar(filtros)
  }, [cargar, filtros])

  const recargar = useCallback(() => cargar(filtros), [cargar, filtros])

  /** Descarga (o regenera) el PDF de un acta almacenada. */
  const descargar = useCallback(
    async (acta, opciones = {}) => {
      setOperando(acta.id)
      setError(null)
      try {
        const { blob, nombreArchivo } = await descargarPdfGuardado(acta.id, opciones)
        descargarBlob(blob, nombreArchivo)
        setAviso(`PDF del acta ${acta.folio} descargado.`)
      } catch (fallo) {
        setError(await mensajeDeError(fallo))
      } finally {
        setOperando(null)
      }
    },
    [],
  )

  /** Vuelve a validar la consistencia del acta y refresca el listado. */
  const validar = useCallback(
    async (acta) => {
      setOperando(acta.id)
      setError(null)
      try {
        const validacion = await validarActaGuardada(acta.id)
        setAviso(
          `Acta ${acta.folio}: puntaje de consistencia ${Number(validacion.puntaje).toFixed(2)}/100.`,
        )
        await cargar(filtros)
      } catch (fallo) {
        setError(mensajeDeError(fallo))
      } finally {
        setOperando(null)
      }
    },
    [cargar, filtros],
  )

  /** Cambia el estatus del acta dentro de su ciclo de vida. */
  const cambiarEstatusActa = useCallback(
    async (acta, estatus) => {
      setOperando(acta.id)
      setError(null)
      try {
        await cambiarEstatus(acta.id, estatus)
        setAviso(`Acta ${acta.folio} actualizada a «${estatus}».`)
        await cargar(filtros)
      } catch (fallo) {
        setError(mensajeDeError(fallo))
      } finally {
        setOperando(null)
      }
    },
    [cargar, filtros],
  )

  /** Elimina el acta del historial. */
  const borrar = useCallback(
    async (acta) => {
      setOperando(acta.id)
      setError(null)
      try {
        const confirmado =
          typeof window === 'undefined' ||
          window.confirm(`¿Eliminar el acta ${acta.folio}? Esta acción no se puede deshacer.`)
        if (!confirmado) return
        const respuesta = await eliminarActa(acta.id)
        setAviso(respuesta?.mensaje || `Acta ${acta.folio} eliminada.`)
        await cargar(filtros)
      } catch (fallo) {
        setError(mensajeDeError(fallo))
      } finally {
        setOperando(null)
      }
    },
    [cargar, filtros],
  )

  return {
    actas,
    cargando,
    error,
    aviso,
    operando,
    filtros,
    setFiltros,
    recargar,
    descargar,
    validar,
    cambiarEstatus: cambiarEstatusActa,
    borrar,
  }
}

export default useHistorialActas
