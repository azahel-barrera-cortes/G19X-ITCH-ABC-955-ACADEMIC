import { useCallback, useEffect, useMemo, useState } from 'react'
import Alerta from '../components/ui/Alerta.jsx'
import AsistenteChat from '../components/asistente/AsistenteChat.jsx'
import Boton from '../components/ui/Boton.jsx'
import ActasWizard from '../components/wizard/ActasWizard.jsx'
import {
  construirPayload,
  estadoDesdeActa,
  useActaWizard,
  validarPaso,
} from '../hooks/useActaWizard.js'
import {
  actaAplicable,
  requisitosParaActa,
  TIPOS_ASAMBLEA,
  TIPOS_SOCIEDAD,
} from '../constants/catalogos.js'
import {
  actualizarActa,
  crearActa,
  reenviarActa,
  mensajeDeError,
  redactarActa,
  redactarEnVivo,
} from '../api/client.js'

const PASOS_A_VALIDAR = [1, 2, 3]

/** Página «Generar acta»: captura, redacción asistida y envío a revisión. */
export default function GenerarActa({
  actaInicial = null,
  cambiosIniciales = null,
  plantillaTipo = null,
  infoEmpresa = null,
  onVolver = null,
  onCerrarEdicion = null,
  onSolicitudEnviada = null,
}) {
  const actaParaFormulario = useMemo(() => {
    if (!actaInicial) return null
    const cambios = Object.fromEntries(
      Object.entries(cambiosIniciales || {}).filter(
        ([campo]) => !['sociedad', 'tipo_asamblea', 'tipo_sociedad'].includes(campo),
      ),
    )
    if (cambios.datos_especificos) {
      cambios.datos_especificos = {
        ...(actaInicial.datos_especificos || {}),
        ...cambios.datos_especificos,
      }
    }
    return { ...actaInicial, ...cambios }
  }, [actaInicial, cambiosIniciales])
  const { estado, despachar, actualizarCampo, actualizarCampos, reiniciar, cargarActa, calculos, pasos } =
    useActaWizard(actaParaFormulario ? estadoDesdeActa(actaParaFormulario) : undefined)

  const actualizarCampoWizard = useCallback((campo, valor) => {
    setBorrador(null)
    actualizarCampo(campo, valor)
  }, [actualizarCampo])
  const despacharWizard = useCallback((accion) => {
    setBorrador(null)
    despachar(accion)
  }, [despachar])

  const [pasoActual, setPasoActual] = useState(1)
  const [errores, setErrores] = useState({})
  const [borrador, setBorrador] = useState(null)
  const [advertencias, setAdvertencias] = useState([])
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [cargandoRedaccion, setCargandoRedaccion] = useState(false)
  const [cargandoEnvio, setCargandoEnvio] = useState(false)
  const [cargandoGuardar, setCargandoGuardar] = useState(false)
  const [redaccionEnVivo, setRedaccionEnVivo] = useState(null)
  const empresaAsignada = Boolean(
    actaInicial || (infoEmpresa?.nombre_sociedad && infoEmpresa?.tipo_sociedad),
  )
  const usaInfoEmpresa = Boolean(infoEmpresa?.usar_info_empresa)
  const contextoActa = useMemo(() => {
    const tipo = TIPOS_ASAMBLEA.find((item) => item.valor === estado.tipo_asamblea)
    const sociedad = TIPOS_SOCIEDAD.find((item) => item.valor === estado.tipo_sociedad)
    return {
      acta: tipo,
      sociedad,
      requisitos: requisitosParaActa(estado.tipo_asamblea),
      aplicable: actaAplicable(estado.tipo_sociedad, estado.tipo_asamblea),
    }
  }, [estado.tipo_asamblea, estado.tipo_sociedad])

  useEffect(() => {
    if (actaInicial || !empresaAsignada || !usaInfoEmpresa) return
    actualizarCampos({
      sociedad: infoEmpresa.nombre_sociedad,
      rfc_sociedad: infoEmpresa.rfc_sociedad || '',
      tipo_sociedad: infoEmpresa.tipo_sociedad,
      logo_empresa: infoEmpresa.logo_empresa || '',
      usar_info_empresa: true,
    })
  }, [actaInicial, actualizarCampos, empresaAsignada, infoEmpresa, usaInfoEmpresa])

  // Cuando se elige un acta en la biblioteca, se carga en el formulario.
  useEffect(() => {
    if (!actaParaFormulario) return
    cargarActa(actaParaFormulario)
    setBorrador(null)
    setAdvertencias([])
    setError(null)
    setErrores({})
    setPasoActual(1)
  }, [actaParaFormulario, cargarActa])

  // Cuando se elige una plantilla en el panel, se precarga el tipo de asamblea.
  useEffect(() => {
    if (actaInicial || !plantillaTipo) return
    reiniciar()
    actualizarCampo('tipo_asamblea', plantillaTipo)
    setBorrador(null)
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
      if (!empresaAsignada) {
        setError('No se ha asignado empresa')
        return
      }
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
    [empresaAsignada, pasoActual, pasos.length, estado],
  )

  /** «Generar borrador con IA»: POST /actas/redactar (no persiste ni exporta). */
  const handleRedactar = async () => {
    if (!empresaAsignada) {
      setError('No se ha asignado empresa')
      return
    }
    setCargandoRedaccion(true)
    setError(null)
    try {
      const respuesta = await redactarActa({ ...construirPayload(estado), guardar: false })
      setBorrador(respuesta)
      setAdvertencias(respuesta.advertencias || [])
    } catch (fallo) {
      setError(mensajeDeError(fallo))
    } finally {
      setCargandoRedaccion(false)
    }
  }

  /** «Ver redacción en vivo»: POST /actas/redactar-stream (SSE, primer acuerdo). */
  const handleRedactarEnVivo = async () => {
    if (!empresaAsignada) {
      setError('No se ha asignado empresa')
      return
    }
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

  /** Guarda el acta con sus cláusulas y la envía a la bandeja del Revisor. */
  const handleEnviarRevision = async () => {
    if (!empresaAsignada) {
      setError('No se ha asignado empresa')
      return
    }
    for (const numero of PASOS_A_VALIDAR) {
      const fallos = validarPaso(numero, estado)
      if (Object.keys(fallos).length) {
        setErrores(fallos)
        setPasoActual(numero)
        setError('Revisa los campos señalados antes de enviar el acta a revisión.')
        return
      }
    }

    setCargandoEnvio(true)
    setError(null)
    try {
      const base = construirPayload(estado)
      const payload = {
        ...base,
        estatus: 'en_revision',
        generar_clausulas: !borrador,
        ...(borrador
          ? {
              acuerdos: (borrador.acuerdos || []).map((acuerdo, indice) => ({
                ...acuerdo,
                numero: indice + 1,
              })),
            }
          : {}),
      }
      const creada = await crearActa(payload)
      setAviso(`${creada.folio} fue enviado a revisión como versión ${creada.version}.`)
      onSolicitudEnviada?.(creada)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargandoEnvio(false)
    }
  }

  const handleGuardarBorrador = async () => {
    if (!actaInicial?.id) return
    for (const numero of PASOS_A_VALIDAR) {
      const fallos = validarPaso(numero, estado)
      if (Object.keys(fallos).length) {
        setErrores(fallos)
        setPasoActual(numero)
        setError('Revisa los campos señalados antes de guardar el borrador.')
        return
      }
    }

    setCargandoGuardar(true)
    setError(null)
    try {
      const payload = construirPayload(estado)
      const ultimaDevolucion = [...(actaInicial.historial_revision || [])]
        .reverse()
        .find((evento) => evento.accion === 'devolver')
      const etapaDevolucion = ultimaDevolucion?.etapa === 'abogado' ? 'Abogado' : 'Revisor'
      const actualizada = await actualizarActa(actaInicial.id, {
        ...payload,
        ...(borrador?.acuerdos?.length
          ? {
              acuerdos: borrador.acuerdos.map((acuerdo, indice) => ({
                ...acuerdo,
                numero: indice + 1,
              })),
            }
          : {}),
        estatus: 'borrador',
        regenerar_con_ia: false,
        motivo_cambio:
          actaInicial.estado_flujo === 'con_errores'
            ? `Corrección solicitada por el ${etapaDevolucion}`
            : 'Edición del borrador',
      })
      if (actaInicial.estado_flujo === 'con_errores') {
        const reenviada = await reenviarActa(actaInicial.id)
        const etapa = reenviada.estado_flujo === 'abogado' ? 'directamente al Abogado' : 'al Revisor'
        setAviso(`${reenviada.folio} fue corregida y enviada ${etapa} como versión ${reenviada.version}.`)
      } else {
        setAviso(`Borrador guardado como versión ${actualizada.version}.`)
      }
      onCerrarEdicion?.(actaInicial.id)
    } catch (fallo) {
      setError(await mensajeDeError(fallo))
    } finally {
      setCargandoGuardar(false)
    }
  }

  const aplicarCambiosAsistidos = ({ cambios }) => {
    const cambiosFormulario = Object.fromEntries(
      Object.entries(cambios || {}).map(([campo, valor]) => [
        campo,
        campo === 'datos_especificos'
          ? { ...estado.datos_especificos, ...valor }
          : typeof valor === 'number' ? String(valor) : valor,
      ]),
    )
    actualizarCampos(cambiosFormulario)
    setBorrador(null)
    setAviso('Cambios del asistente aplicados al formulario. Revísalos antes de guardar la nueva versión.')
  }

  const handleCancelarEdicion = () => {
    if (actaInicial && onCerrarEdicion) {
      onCerrarEdicion()
      return
    }
    onVolver?.()
  }

  /** Reinicia el formulario por completo y sale del modo edición. */
  const handleNuevaActa = () => {
    reiniciar()
    setBorrador(null)
    setAdvertencias([])
    setErrores({})
    setAviso(null)
    setError(null)
    setPasoActual(1)
    if (actaInicial && onCerrarEdicion) onCerrarEdicion()
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
              {actaInicial
                ? 'Corrige las observaciones y guarda una nueva versión; se enviará al rol que solicitó los cambios.'
                : 'Captura los datos, revisa el borrador y envía el acta a revisión. El PDF final se habilita después de la aprobación legal.'}
            </p>
          </div>
          {onVolver ? (
            <Boton variante="secundario" tamano="sm" onClick={handleCancelarEdicion}>
              {actaInicial ? '← Volver a Mis actas' : '← Volver al panel'}
            </Boton>
          ) : null}
        </div>
      </header>

      <section className="grid gap-3 md:grid-cols-3">
        <div className="tarjeta border-l-4 border-l-corporativo-500 p-4 md:col-span-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
            Configuración jurídica activa
          </p>
          <h2 className="mt-1 text-base font-semibold text-slate-800">
            {contextoActa.acta?.etiqueta || 'Selecciona un tipo de acta'}
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            {contextoActa.sociedad?.etiqueta || 'Selecciona el tipo societario para aplicar sus reglas.'}
          </p>
          {!contextoActa.aplicable ? (
            <p className="mt-2 text-sm font-medium text-red-600">
              Esta combinación no es aplicable. Selecciona otra acta o sociedad.
            </p>
          ) : null}
        </div>
        <div className="tarjeta p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
            Información requerida
          </p>
          <p className="mt-1 text-2xl font-semibold text-slate-800">
            {contextoActa.requisitos.length}
          </p>
          <p className="text-xs text-slate-500">
            campos jurídicos específicos que deben documentarse antes de emitir el acta.
          </p>
        </div>
      </section>

      {actaInicial ? (
        <Alerta tono="info" titulo="Modo edición">
          Guardar los cambios emitirá una nueva versión del borrador {actaInicial.folio}. El tipo de
          acta y la sociedad permanecen bloqueados.
        </Alerta>
      ) : null}
      {actaInicial?.estado_flujo === 'con_errores' && actaInicial.comentario_revision ? (
        <Alerta tono="advertencia" titulo="Correcciones solicitadas por el Revisor o el Abogado">
          {actaInicial.comentario_revision}
        </Alerta>
      ) : null}

      {actaInicial ? (
        <details className="tarjeta">
          <summary className="cursor-pointer px-5 py-4 text-sm font-semibold text-corporativo-700">
            Editar con el asistente IA
          </summary>
          <div className="border-t border-slate-200 px-5 py-4">
            <p className="mb-3 text-sm text-slate-600">
              Pide cambiar un campo y el asistente propondrá el nuevo valor. Después podrás
              revisarlo en el formulario y guardar una nueva versión. Los asistentes, el orden del
              día y los acuerdos se pueden modificar directamente en los pasos del formulario.
            </p>
            <AsistenteChat
              modo="compacto"
              titulo={`Editar ${actaInicial.folio}`}
              actaId={actaInicial.id}
              modoEdicion
              datosAsistente={actaInicial.datos_asistente}
              onAplicarCambios={aplicarCambiosAsistidos}
            />
          </div>
        </details>
      ) : null}

      <ActasWizard
        pasos={pasos}
        pasoActual={pasoActual}
        onCambiarPaso={irAPaso}
        pasosCompletados={completados}
        estado={estado}
        calculos={calculos}
        despachar={despacharWizard}
        actualizarCampo={actualizarCampoWizard}
        bloquearIdentidad={Boolean(actaInicial)}
        errores={errores}
        infoEmpresa={infoEmpresa}
        borrador={borrador}
        advertencias={advertencias}
        aviso={aviso}
        redaccionEnVivo={redaccionEnVivo}
        cargandoRedaccion={cargandoRedaccion}
        cargandoEnvio={cargandoEnvio}
        cargandoGuardar={cargandoGuardar}
        error={error}
        onRedactar={handleRedactar}
        onRedactarEnVivo={handleRedactarEnVivo}
        onEnviarRevision={handleEnviarRevision}
        onGuardarBorrador={handleGuardarBorrador}
        onCancelarEdicion={handleCancelarEdicion}
        onNuevaActa={handleNuevaActa}
        actaId={actaInicial?.id || null}
        esCorreccion={actaInicial?.estado_flujo === 'con_errores'}
      />
    </div>
  )
}

