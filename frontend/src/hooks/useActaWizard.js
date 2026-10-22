/**
 * Estado del formulario por pasos (wizard) para la generación de actas.
 *
 * Toda la lógica de captura vive en un `useReducer`, de modo que los componentes
 * de cada paso solo despachan acciones y el estado se puede serializar para
 * enviarlo a la API (`construirPayload`).
 */
import { useCallback, useMemo, useReducer } from 'react'
import { ACTA_VACIA } from '../constants/catalogos.js'

/** Pasos del asistente de captura. */
export const PASOS = [
  { id: 1, titulo: 'Datos generales', descripcion: 'Empresa, fecha, hora y tipo de asamblea' },
  { id: 2, titulo: 'Asistentes y quórum', descripcion: 'Mesa directiva, tenencia accionaria y capital' },
  { id: 3, titulo: 'Orden del día y acuerdos', descripcion: 'Puntos, votaciones y fundamentos' },
  { id: 4, titulo: 'Revisión y PDF', descripcion: 'Borrador con IA, validación y descarga' },
]

let secuenciaAsistente = 0

/** Nuevo asistente vacío (con identificador temporal para las listas de React). */
export function nuevoAsistente() {
  secuenciaAsistente += 1
  return {
    clave: `asistente-${secuenciaAsistente}`,
    nombre: '',
    caracter: 'propietario',
    cargo: '',
    acciones: '',
    porcentaje_capital: '',
    rfc: '',
    email: '',
    es_presidente: false,
    es_secretario: false,
    es_escrutador: false,
    firma: true,
  }
}

/** Nuevo punto del orden del día. */
export function nuevoPunto(numero) {
  return { clave: `punto-${Date.now()}-${numero}`, numero, titulo: '', descripcion: '', requiere_votacion: true }
}

/** Nuevo acuerdo con su votación. */
export function nuevoAcuerdo(numero) {
  return {
    clave: `acuerdo-${Date.now()}-${numero}`,
    numero,
    titulo: '',
    resumen: '',
    votacion: {
      tipo_mayoria: 'mayoria_calificada',
      acciones_a_favor: '',
      acciones_en_contra: 0,
      abstenciones: 0,
      porcentaje_requerido: '',
      aprobado: true,
      comentario: '',
    },
  }
}

/** Estado inicial del formulario. */
export function crearEstadoInicial() {
  return {
    ...ACTA_VACIA,
    asistentes: [
      { ...nuevoAsistente(), caracter: 'presidente', es_presidente: true },
      { ...nuevoAsistente(), caracter: 'secretario', es_secretario: true },
    ],
    orden_del_dia: [{ numero: 1, clave: 'punto-inicial', titulo: '', descripcion: '', requiere_votacion: true }],
    acuerdos: [nuevoAcuerdo(1)],
  }
}

/** Renumera consecutivamente los elementos de una lista. */
const renumerar = (lista) => lista.map((item, indice) => ({ ...item, numero: indice + 1 }))

/** Reductor central del formulario. */
function reductor(estado, accion) {
  switch (accion.tipo) {
    case 'campo':
      return { ...estado, [accion.campo]: accion.valor }
    case 'campos':
      return { ...estado, ...accion.cambios }
    case 'reemplazar':
      return { ...accion.estado }
    case 'reiniciar':
      return crearEstadoInicial()

    case 'asistente.agregar':
      return { ...estado, asistentes: [...estado.asistentes, accion.asistente || nuevoAsistente()] }
    case 'asistente.actualizar':
      return {
        ...estado,
        asistentes: estado.asistentes.map((asistente, indice) =>
          indice === accion.indice ? { ...asistente, ...accion.cambios } : asistente,
        ),
      }
    case 'asistente.eliminar':
      return { ...estado, asistentes: estado.asistentes.filter((_, indice) => indice !== accion.indice) }

    case 'punto.agregar':
      return {
        ...estado,
        orden_del_dia: [...estado.orden_del_dia, nuevoPunto(estado.orden_del_dia.length + 1)],
      }
    case 'punto.actualizar':
      return {
        ...estado,
        orden_del_dia: estado.orden_del_dia.map((punto, indice) =>
          indice === accion.indice ? { ...punto, ...accion.cambios } : punto,
        ),
      }
    case 'punto.eliminar':
      return {
        ...estado,
        orden_del_dia: renumerar(estado.orden_del_dia.filter((_, indice) => indice !== accion.indice)),
      }

    case 'acuerdo.agregar':
      return { ...estado, acuerdos: [...estado.acuerdos, nuevoAcuerdo(estado.acuerdos.length + 1)] }
    case 'acuerdo.actualizar':
      return {
        ...estado,
        acuerdos: estado.acuerdos.map((acuerdo, indice) =>
          indice === accion.indice ? { ...acuerdo, ...accion.cambios } : acuerdo,
        ),
      }
    case 'acuerdo.votacion':
      return {
        ...estado,
        acuerdos: estado.acuerdos.map((acuerdo, indice) =>
          indice === accion.indice
            ? { ...acuerdo, votacion: { ...acuerdo.votacion, ...accion.cambios } }
            : acuerdo,
        ),
      }
    case 'acuerdo.eliminar':
      return { ...estado, acuerdos: renumerar(estado.acuerdos.filter((_, indice) => indice !== accion.indice)) }

    default:
      return estado
  }
}


// ---------------------------------------------------------------------------
// Conversión de valores del formulario al contrato de la API
// ---------------------------------------------------------------------------
const textoONulo = (valor) => {
  const texto = String(valor ?? '').trim()
  return texto === '' ? null : texto
}

const numeroONulo = (valor) => {
  const texto = String(valor ?? '').trim()
  if (texto === '') return null
  const convertido = Number(texto)
  return Number.isFinite(convertido) ? convertido : null
}

const numeroOCero = (valor) => {
  const convertido = Number(valor)
  return Number.isFinite(convertido) ? convertido : 0
}

/** Construye el cuerpo JSON que espera ``POST /actas/generar-pdf``. */
export function construirPayload(estado) {
  return {
    sociedad: String(estado.sociedad || '').trim(),
    rfc_sociedad: textoONulo(estado.rfc_sociedad),
    tipo_asamblea: estado.tipo_asamblea,
    titulo: textoONulo(estado.titulo),
    fecha: estado.fecha,
    hora: estado.hora ? String(estado.hora).slice(0, 5) : null,
    lugar: String(estado.lugar || '').trim(),
    convocatoria_fecha: textoONulo(estado.convocatoria_fecha),
    convocatoria_medio: textoONulo(estado.convocatoria_medio),
    convocatoria_quien: textoONulo(estado.convocatoria_quien),
    /** Información de la empresa / sociedad (sección lateral independiente). */
    tipo_sociedad: textoONulo(estado.tipo_sociedad),
    logo_empresa: textoONulo(estado.logo_empresa),
    firma_electronica: Boolean(estado.firma_electronica),
    usar_info_empresa: Boolean(estado.usar_info_empresa),
    capital_social: numeroONulo(estado.capital_social),
    acciones_totales: numeroONulo(estado.acciones_totales),
    capital_presente: numeroONulo(estado.capital_presente),
    quorum_porcentaje: numeroONulo(estado.quorum_porcentaje),
    presidente: String(estado.presidente || '').trim(),
    secretario: String(estado.secretario || '').trim(),
    asistentes: estado.asistentes
      .filter((asistente) => String(asistente.nombre || '').trim().length >= 3)
      .map((asistente) => ({
        nombre: String(asistente.nombre).trim(),
        cargo: textoONulo(asistente.cargo),
        caracter: asistente.caracter,
        acciones: numeroOCero(asistente.acciones),
        porcentaje_capital: numeroONulo(asistente.porcentaje_capital),
        rfc: textoONulo(asistente.rfc),
        email: textoONulo(asistente.email),
        es_presidente: Boolean(asistente.es_presidente),
        es_secretario: Boolean(asistente.es_secretario),
        es_escrutador: Boolean(asistente.es_escrutador),
        firma: asistente.firma !== false,
      })),
    orden_del_dia: estado.orden_del_dia
      .filter((punto) => String(punto.titulo || '').trim().length >= 3)
      .map((punto, indice) => ({
        numero: indice + 1,
        titulo: String(punto.titulo).trim(),
        descripcion: textoONulo(punto.descripcion),
        requiere_votacion: punto.requiere_votacion !== false,
      })),
    acuerdos: estado.acuerdos
      .filter((acuerdo) => String(acuerdo.titulo || '').trim().length >= 3)
      .map((acuerdo, indice) => ({
        numero: indice + 1,
        titulo: String(acuerdo.titulo).trim(),
        resumen: String(acuerdo.resumen || '').trim(),
        votacion: acuerdo.votacion
          ? {
              tipo_mayoria: acuerdo.votacion.tipo_mayoria,
              acciones_a_favor: numeroOCero(acuerdo.votacion.acciones_a_favor),
              acciones_en_contra: numeroOCero(acuerdo.votacion.acciones_en_contra),
              abstenciones: numeroOCero(acuerdo.votacion.abstenciones),
              porcentaje_requerido: numeroONulo(acuerdo.votacion.porcentaje_requerido),
              aprobado: acuerdo.votacion.aprobado !== false,
              comentario: textoONulo(acuerdo.votacion.comentario),
            }
          : null,
      })),
    observaciones: textoONulo(estado.observaciones),
    instrucciones_adicionales: textoONulo(estado.instrucciones_adicionales),
    guardar: estado.guardar !== false,
    generar_clausulas: estado.generar_clausulas !== false,
    incluir_validacion: estado.incluir_validacion !== false,
    incluir_tabla_asistentes: estado.incluir_tabla_asistentes !== false,
    incluir_hoja_firmas: estado.incluir_hoja_firmas !== false,
    incluir_anexo_validacion: estado.incluir_anexo_validacion === true,
  }
}

/** Convierte un acta almacenada en el estado editable del formulario. */
export function estadoDesdeActa(acta) {
  const base = crearEstadoInicial()
  return {
    ...base,
    sociedad: acta.sociedad || '',
    rfc_sociedad: acta.rfc_sociedad || '',
    tipo_asamblea: acta.tipo_asamblea || base.tipo_asamblea,
    titulo: acta.titulo || '',
    fecha: acta.fecha || base.fecha,
    hora: acta.hora ? String(acta.hora).slice(0, 5) : base.hora,
    lugar: acta.lugar || '',
    convocatoria_fecha: acta.convocatoria_fecha || '',
    convocatoria_medio: acta.convocatoria_medio || '',
    convocatoria_quien: acta.convocatoria_quien || '',
    tipo_sociedad: acta.tipo_sociedad || '',
    logo_empresa: acta.logo_empresa || '',
    firma_electronica: acta.firma_electronica !== false,
    usar_info_empresa: acta.usar_info_empresa === true,
    capital_social: acta.capital_social ?? '',
    acciones_totales: acta.acciones_totales ?? '',
    capital_presente: acta.capital_presente ?? '',
    quorum_porcentaje: acta.quorum_porcentaje ?? '',
    presidente: acta.presidente || '',
    secretario: acta.secretario || '',
    estatus: acta.estatus || 'borrador',
    asistentes: (acta.asistentes || []).map((asistente, indice) => ({
      ...nuevoAsistente(),
      ...asistente,
      clave: `asistente-cargado-${indice}`,
      acciones: asistente.acciones ?? '',
      porcentaje_capital: asistente.porcentaje_capital ?? '',
    })),
    orden_del_dia: (acta.orden_del_dia || []).map((punto, indice) => ({
      ...punto,
      clave: `punto-cargado-${indice}`,
      descripcion: punto.descripcion || '',
    })),
    acuerdos: (acta.acuerdos || []).map((acuerdo, indice) => ({
      ...acuerdo,
      clave: `acuerdo-cargado-${indice}`,
      votacion: acuerdo.votacion || nuevoAcuerdo(indice + 1).votacion,
    })),
    observaciones: acta.observaciones || '',
  }
}

/** Validación del formulario por paso (se ejecuta antes de llamar a la API). */
export function validarPaso(paso, estado) {
  const errores = {}

  if (paso === 1) {
    if (String(estado.sociedad || '').trim().length < 3) {
      errores.sociedad = 'Indica la razón social de la sociedad (mínimo 3 caracteres).'
    }
    if (!estado.fecha) errores.fecha = 'La fecha de celebración es obligatoria.'
    if (String(estado.lugar || '').trim().length < 3) {
      errores.lugar = 'Indica el lugar donde se celebró la asamblea.'
    }
    if (estado.convocatoria_fecha && estado.fecha && estado.convocatoria_fecha > estado.fecha) {
      errores.convocatoria_fecha = 'La convocatoria no puede ser posterior a la fecha de la asamblea.'
    }
  }

  if (paso === 2) {
    if (!estado.asistentes.length) {
      errores.asistentes = 'Registra al menos un asistente.'
    } else if (estado.asistentes.some((a) => String(a.nombre || '').trim().length < 3)) {
      errores.asistentes = 'Todos los asistentes requieren nombre completo.'
    }
    if (String(estado.presidente || '').trim().length < 3) {
      errores.presidente = 'Indica quién preside la asamblea.'
    }
    if (String(estado.secretario || '').trim().length < 3) {
      errores.secretario = 'Indica quién funge como secretario.'
    }
    const sumaAcciones = estado.asistentes.reduce((total, a) => total + (Number(a.acciones) || 0), 0)
    const totalAcciones = Number(estado.acciones_totales) || Number(estado.capital_social) || 0
    if (totalAcciones > 0 && sumaAcciones > totalAcciones + 0.001) {
      errores.asistentes = 'La suma de acciones de los asistentes excede el total en circulación.'
    }
  }

  if (paso === 3) {
    if (!estado.orden_del_dia.some((p) => String(p.titulo || '').trim().length >= 3)) {
      errores.orden_del_dia = 'Agrega al menos un punto del orden del día con título.'
    }
    if (!estado.acuerdos.some((a) => String(a.titulo || '').trim().length >= 3)) {
      errores.acuerdos = 'Agrega al menos un acuerdo con título.'
    } else if (
      estado.acuerdos.some(
        (a) => String(a.titulo || '').trim().length >= 3 && String(a.resumen || '').trim().length < 5,
      )
    ) {
      errores.acuerdos = 'Cada acuerdo requiere un resumen de al menos 5 caracteres.'
    }
  }

  return errores
}

/** Hook principal del formulario por pasos. */
export function useActaWizard(estadoInicial) {
  const [estado, despachar] = useReducer(
    reductor,
    estadoInicial,
    (inicial) => inicial || crearEstadoInicial(),
  )

  const actualizarCampo = useCallback((campo, valor) => despachar({ tipo: 'campo', campo, valor }), [])
  const actualizarCampos = useCallback((cambios) => despachar({ tipo: 'campos', cambios }), [])
  const reiniciar = useCallback(() => despachar({ tipo: 'reiniciar' }), [])
  const cargarActa = useCallback(
    (acta) => despachar({ tipo: 'reemplazar', estado: estadoDesdeActa(acta) }),
    [],
  )

  // Valores derivados que se muestran en el paso de asistentes y en la revisión.
  const calculos = useMemo(() => {
    const accionesTotales = Number(estado.acciones_totales) || Number(estado.capital_social) || 0
    const accionesPresentes = estado.asistentes.reduce(
      (total, asistente) => total + (Number(asistente.acciones) || 0),
      0,
    )
    const explicito =
      estado.quorum_porcentaje !== '' && estado.quorum_porcentaje !== null
        ? Number(estado.quorum_porcentaje)
        : null
    const porCapital =
      Number(estado.capital_social) > 0 && Number(estado.capital_presente) > 0
        ? (Number(estado.capital_presente) / Number(estado.capital_social)) * 100
        : null
    const porAcciones = accionesTotales > 0 ? (accionesPresentes / accionesTotales) * 100 : 0
    const quorum = explicito ?? porCapital ?? porAcciones

    return {
      accionesTotales,
      accionesPresentes,
      accionesFaltantes: Math.max(accionesTotales - accionesPresentes, 0),
      quorum: Number.isFinite(quorum) ? quorum : 0,
      porcentajes: estado.asistentes.map((asistente) =>
        accionesTotales ? ((Number(asistente.acciones) || 0) / accionesTotales) * 100 : 0,
      ),
    }
  }, [
    estado.asistentes,
    estado.acciones_totales,
    estado.capital_social,
    estado.capital_presente,
    estado.quorum_porcentaje,
  ])

  return {
    estado,
    despachar,
    actualizarCampo,
    actualizarCampos,
    reiniciar,
    cargarActa,
    calculos,
    pasos: PASOS,
  }
}


