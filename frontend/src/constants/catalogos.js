/**
 * Catálogos de respaldo del formulario.
 *
 * Los valores se sincronizan con `app/core/catalogos.py` del backend: se usan
 * para poblar los formularios de inmediato (sin esperar a la red) y como
 * contingencia si el endpoint `/actas/catalogos` no está disponible.
 */
export const TIPOS_ASAMBLEA = [
  { valor: 'constitutiva', etiqueta: 'Asamblea Constitutiva', descripcion: 'Aprobación de la escritura social, suscripción del capital y estatutos iniciales.', articulos: ['Art. 5º LGSM', 'Art. 6º LGSM'] },
  { valor: 'ordinaria', etiqueta: 'Asamblea General Ordinaria', descripcion: 'Nombramientos, informes, estados financieros y asuntos que no requieren reforma estatutaria.', articulos: ['Art. 178 LGSM', 'Art. 181 LGSM', 'Art. 189 LGSM'] },
  { valor: 'extraordinaria', etiqueta: 'Asamblea General Extraordinaria', descripcion: 'Modificación del contrato social, aumento o reducción de capital, fusión y disolución.', articulos: ['Art. 182 LGSM', 'Art. 190 LGSM'] },
  { valor: 'mixta', etiqueta: 'Asamblea General Mixta', descripcion: 'Asuntos ordinarios y extraordinarios en la misma sesión.', articulos: ['Art. 178 LGSM', 'Art. 182 LGSM'] },
  { valor: 'aumento_capital', etiqueta: 'Aumento de Capital Social', descripcion: 'Suscripción de nuevas acciones, capitalización de pasivos o primas de acciones.', articulos: ['Art. 182 LGSM', 'Art. 209 LGSM'] },
  { valor: 'reduccion_capital', etiqueta: 'Reducción de Capital Social', descripcion: 'Reembolso de aportaciones o amortización de acciones.', articulos: ['Art. 134 LGSM', 'Art. 135 LGSM'] },
  { valor: 'fusion', etiqueta: 'Fusión', descripcion: 'Incorporación o integración de sociedades conforme a las bases aprobadas.', articulos: ['Art. 222 LGSM', 'Art. 223 LGSM'] },
  { valor: 'escision', etiqueta: 'Escisión', descripcion: 'División del patrimonio social en dos o más sociedades.', articulos: ['Art. 228 bis LGSM'] },
  { valor: 'disolucion_liquidacion', etiqueta: 'Disolución y Liquidación', descripcion: 'Disolución anticipada y nombramiento de liquidadores.', articulos: ['Art. 229 LGSM', 'Art. 247 LGSM'] },
  { valor: 'sesion_consejo', etiqueta: 'Sesión del Consejo de Administración', descripcion: 'Actas de consejo con base en los estatutos sociales.', articulos: ['Estatutos sociales', 'Art. 158 LGSM'] },
]

export const TIPOS_MAYORIA = [
  { valor: 'unanimidad', etiqueta: 'Unanimidad', porcentaje_requerido: 100 },
  { valor: 'mayoria_calificada', etiqueta: 'Mayoría calificada (75%)', porcentaje_requerido: 75 },
  { valor: 'mayoria_especial', etiqueta: 'Mayoría especial (dos terceras partes)', porcentaje_requerido: 66.67 },
  { valor: 'mayoria_simple', etiqueta: 'Mayoría simple (50% + 1)', porcentaje_requerido: 50 },
  { valor: 'sin_votacion', etiqueta: 'Sin votación (informativo)', porcentaje_requerido: null },
]

export const CARACTERES_ASISTENTE = [
  { valor: 'presidente', etiqueta: 'Presidente de la asamblea' },
  { valor: 'secretario', etiqueta: 'Secretario de la asamblea' },
  { valor: 'escrutador', etiqueta: 'Escrutador' },
  { valor: 'propietario', etiqueta: 'Accionista propietario' },
  { valor: 'suplente', etiqueta: 'Accionista suplente (ad hoc)' },
  { valor: 'representante', etiqueta: 'Representante con carta poder' },
  { valor: 'comisario', etiqueta: 'Comisario' },
  { valor: 'invitado', etiqueta: 'Invitado (sin voz ni voto)' },
]

export const ESTATUS_ACTA = [
  { valor: 'borrador', etiqueta: 'Borrador' },
  { valor: 'en_revision', etiqueta: 'En revisión' },
  { valor: 'aprobada', etiqueta: 'Aprobada' },
  { valor: 'firmada', etiqueta: 'Firmada' },
  { valor: 'archivada', etiqueta: 'Archivada (protocolizada)' },
]

/** Clasificación de vigencia de un acta (caducidad). */
export const ESTADOS_VIGENCIA = [
  { valor: 'vencida', etiqueta: 'Vencida', tono: 'error' },
  { valor: 'por_vencer', etiqueta: 'Por vencer', tono: 'advertencia' },
  { valor: 'vigente', etiqueta: 'Vigente', tono: 'exito' },
  { valor: 'sin_fecha', etiqueta: 'Sin caducidad', tono: 'neutral' },
]

/** Estructura inicial del formulario por pasos. */
export const ACTA_VACIA = {
  sociedad: '',
  rfc_sociedad: '',
  tipo_asamblea: 'ordinaria',
  titulo: '',
  fecha: new Date().toISOString().slice(0, 10),
  hora: '10:00',
  lugar: '',
  convocatoria_fecha: '',
  convocatoria_medio: 'Publicación en el sistema electrónico de la Secretaría de Economía',
  convocatoria_quien: 'Consejo de Administración',
  capital_social: '',
  acciones_totales: '',
  capital_presente: '',
  quorum_porcentaje: '',
  presidente: '',
  secretario: '',
  asistentes: [],
  orden_del_dia: [{ numero: 1, titulo: '', descripcion: '', requiere_votacion: true }],
  acuerdos: [
    {
      numero: 1,
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
    },
  ],
  observaciones: '',
  guardar: true,
  generar_clausulas: true,
  incluir_validacion: true,
}

/** Nombre legible de un valor de catálogo (con respaldo automático). */
export function etiquetaDe(catalogo, valor) {
  const encontrado = catalogo.find((item) => item.valor === valor)
  if (encontrado) return encontrado.etiqueta
  return String(valor || '').replace(/_/g, ' ').replace(/^./, (letra) => letra.toUpperCase())
}
