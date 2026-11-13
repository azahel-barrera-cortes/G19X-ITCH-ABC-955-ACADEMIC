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
  { valor: 'aumento_capital', etiqueta: 'Aumento de Capital Social', descripcion: 'Suscripción de nuevas acciones, capitalización de pasivos o primas de acciones.', articulos: ['Art. 182, fracción III LGSM', 'Art. 132 LGSM'] },
  { valor: 'reduccion_capital', etiqueta: 'Reducción de Capital Social', descripcion: 'Reembolso de aportaciones o amortización de acciones.', articulos: ['Art. 9 LGSM', 'Art. 182, fracción III LGSM'] },
  { valor: 'fusion', etiqueta: 'Fusión', descripcion: 'Incorporación o integración de sociedades conforme a las bases aprobadas.', articulos: ['Art. 222 LGSM', 'Art. 223 LGSM'] },
  { valor: 'escision', etiqueta: 'Escisión', descripcion: 'División del patrimonio social en dos o más sociedades.', articulos: ['Art. 228 bis LGSM'] },
  { valor: 'disolucion_liquidacion', etiqueta: 'Disolución y Liquidación', descripcion: 'Disolución anticipada y nombramiento de liquidadores.', articulos: ['Art. 229 LGSM', 'Art. 247 LGSM'] },
  { valor: 'sesion_consejo', etiqueta: 'Sesión del Consejo de Administración', descripcion: 'Actas de consejo con base en los estatutos sociales.', articulos: ['Estatutos sociales', 'Art. 158 LGSM'] },
]

export const ACTAS_CORPORATIVAS = [
  ['constitutiva', 'Asamblea constitutiva', 'Acto de constitución de la sociedad.'],
  ['ordinaria', 'Asamblea general ordinaria', 'Asuntos ordinarios de la sociedad.'],
  ['extraordinaria', 'Asamblea general extraordinaria', 'Acuerdos de naturaleza extraordinaria.'],
  ['mixta', 'Asamblea general mixta', 'Asuntos ordinarios y extraordinarios en una misma sesión.'],
  ['aumento_capital', 'Aumento de capital social', 'Aumento de capital o resolución de socios.'],
  ['reduccion_capital', 'Reducción de capital social', 'Reducción con protección de acreedores.'],
  ['fusion', 'Acta de fusión', 'Acuerdo de fusión entre sociedades.'],
  ['escision', 'Acta de escisión', 'División o transmisión de patrimonio.'],
  ['disolucion_liquidacion', 'Acta de disolución y liquidación', 'Disolución y etapas de liquidación.'],
  ['sesion_consejo', 'Sesión del consejo de administración', 'Actuaciones del consejo cuando exista.'],
  ['modificacion_estatutos', 'Acta de modificación de estatutos', 'Cambio de cláusulas del contrato social.'],
  ['nombramiento_administrador', 'Nombramiento de administrador', 'Designación de administrador único o consejo.'],
  ['remocion_administrador', 'Remoción o revocación de administrador', 'Terminación de un nombramiento.'],
  ['otorgamiento_poderes', 'Otorgamiento de poderes', 'Conferimiento de facultades de representación.'],
  ['revocacion_poderes', 'Revocación de poderes', 'Retiro de facultades previamente otorgadas.'],
  ['transmision_acciones', 'Transmisión de acciones', 'Registro de cambios de titularidad accionaria.'],
  ['cesion_partes_sociales', 'Cesión de partes sociales', 'Cambio de socios en sociedades de partes sociales.'],
  ['admision_nuevos_socios', 'Admisión de nuevos socios', 'Incorporación de integrantes.'],
  ['separacion_exclusion_socios', 'Separación o exclusión de socios', 'Salida o exclusión cuando proceda.'],
  ['nombramiento_liquidadores', 'Nombramiento de liquidadores', 'Designación de responsables de liquidación.'],
  ['aprobacion_balance_liquidacion', 'Aprobación del balance final de liquidación', 'Aprobación del resultado final.'],
  ['transformacion_sociedad', 'Transformación de sociedad', 'Cambio de tipo societario.'],
  ['emision_acciones', 'Emisión de acciones', 'Emisión y condiciones de acciones.'],
  ['aprobacion_estados_financieros', 'Aprobación de estados financieros', 'Presentación y aprobación del ejercicio.'],
  ['asamblea_especial_accionistas', 'Asamblea especial de accionistas', 'Asuntos que afectan una clase de acciones.'],
  ['sesion_vigilancia_comisarios', 'Sesión de vigilancia o comisarios', 'Actuaciones del órgano de vigilancia.'],
].map(([valor, etiqueta, descripcion]) => ({ valor, etiqueta, descripcion }))

TIPOS_ASAMBLEA.push(
  ...ACTAS_CORPORATIVAS.filter((acta) => !TIPOS_ASAMBLEA.some((tipo) => tipo.valor === acta.valor)),
)

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
  { valor: 'archivada', etiqueta: 'Archivada (cierre administrativo; no acredita protocolización)' },
]

export const ESTADOS_FLUJO_ACTA = [
  { valor: 'revision', etiqueta: 'En revisión' },
  { valor: 'abogado', etiqueta: 'Revisada · Pendiente de Abogado' },
  { valor: 'con_errores', etiqueta: 'Con errores' },
  { valor: 'aprobada', etiqueta: 'Aprobada por Abogado' },
  { valor: 'borrador', etiqueta: 'Borrador' },
]

export function etiquetaFlujoActa(estado) {
  return ESTADOS_FLUJO_ACTA.find((item) => item.valor === estado)?.etiqueta || estado || 'Sin estado'
}

/** Tipos de sociedad mercantil (Ley General de Sociedades Mercantiles, México). */
export const TIPOS_SOCIEDAD = [
  { valor: 'sociedad_anonima', etiqueta: 'Sociedad Anónima (S.A.)' },
  { valor: 'sociedad_responsabilidad_limitada', etiqueta: 'Sociedad de Responsabilidad Limitada (S. de R.L.)' },
  { valor: 'sociedad_comandita_simple', etiqueta: 'Sociedad en Comandita Simple (S. en C.)' },
  { valor: 'sociedad_acciones_simplificada', etiqueta: 'Sociedad por Acciones Simplificada (S.A.S.)' },
  { valor: 'sociedad_comandita_acciones', etiqueta: 'Sociedad en Comandita por Acciones (S. en C. por A.)' },
  { valor: 'sociedad_cooperativa', etiqueta: 'Sociedad Cooperativa (S.C.)' },
  { valor: 'sociedad_nombre_colectivo', etiqueta: 'Sociedad en Nombre Colectivo (S. en N.C.)' },
  { valor: 'sociedad_anonima_capital_variable', etiqueta: 'Sociedad Anónima de Capital Variable (S.A. de C.V.)' },
  { valor: 'sociedad_responsabilidad_limitada_capital_variable', etiqueta: 'Sociedad de Responsabilidad Limitada de Capital Variable (S. de R.L. de C.V.)' },
  { valor: 'sapi', etiqueta: 'Sociedad Anónima Promotora de Inversión (S.A.P.I.)' },
  { valor: 'sapi_capital_variable', etiqueta: 'Sociedad Anónima Promotora de Inversión de Capital Variable (S.A.P.I. de C.V.)' },
  { valor: 'sab', etiqueta: 'Sociedad Anónima Bursátil (S.A.B.)' },
  { valor: 'sociedad_civil', etiqueta: 'Sociedad Civil (S.C.)' },
]

const ACTAS_ACCIONES = new Set(['transmision_acciones', 'emision_acciones', 'asamblea_especial_accionistas'])
const ACTAS_PARTES_SOCIALES = new Set(['cesion_partes_sociales'])
const SOCIEDADES_ACCIONES = new Set([
  'sociedad_anonima', 'sociedad_acciones_simplificada', 'sociedad_comandita_acciones',
  'sociedad_anonima_capital_variable', 'sapi', 'sapi_capital_variable', 'sab',
])

export function actaAplicable(tipoSociedad, tipoActa) {
  if (!tipoSociedad) return true
  if (ACTAS_ACCIONES.has(tipoActa)) return SOCIEDADES_ACCIONES.has(tipoSociedad)
  if (ACTAS_PARTES_SOCIALES.has(tipoActa)) {
    return ['sociedad_responsabilidad_limitada', 'sociedad_responsabilidad_limitada_capital_variable',
      'sociedad_comandita_simple', 'sociedad_nombre_colectivo'].includes(tipoSociedad)
  }
  if (tipoSociedad === 'sociedad_cooperativa') {
    return !['sesion_consejo', 'transformacion_sociedad', 'emision_acciones'].includes(tipoActa)
  }
  if (tipoSociedad === 'sociedad_civil') {
    return ['constitutiva', 'ordinaria', 'extraordinaria', 'mixta', 'modificacion_estatutos',
      'nombramiento_administrador', 'remocion_administrador', 'otorgamiento_poderes',
      'revocacion_poderes', 'admision_nuevos_socios', 'separacion_exclusion_socios'].includes(tipoActa)
  }
  return true
}

const REQUISITO = (clave, etiqueta, ayuda, placeholder = '', tipo = 'text') => ({
  clave,
  etiqueta,
  ayuda,
  placeholder,
  tipo,
  requerido: true,
})

const REQUISITOS_COMUNES = [
  REQUISITO('base_estatutaria', 'Base estatutaria y órgano competente', 'Indica la cláusula estatutaria y el órgano que tiene facultades para resolver.', 'Ej. Cláusulas 18 y 22; Asamblea General Extraordinaria'),
  REQUISITO('formalizacion_prevista', 'Formalización y registro previstos', 'Indica si requiere protocolización, publicación, inscripción o avisos, sin afirmar que ya se realizaron.', 'Ej. Protocolización ante fedatario e inscripción en RPC'),
]

const REQUISITOS_POR_ACTA = {
  constitutiva: [
    REQUISITO('fundadores', 'Socios o accionistas fundadores', 'Nombres, nacionalidad, domicilio y participación de cada fundador.', 'Ej. Ana Ruiz, mexicana, 60 acciones; Carlos Peña, mexicano, 40 acciones', 'textarea'),
    REQUISITO('capital_constitutivo', 'Capital suscrito y forma de pago', 'Capital, aportaciones, acciones o partes sociales y exhibición inicial.', 'Ej. $100,000; 1,000 acciones; 20% exhibido', 'textarea'),
    REQUISITO('estatutos_iniciales', 'Estatutos y objeto social', 'Objeto, domicilio, duración, administración y vigilancia inicial.', 'Describe las cláusulas aprobadas', 'textarea'),
  ],
  ordinaria: [
    REQUISITO('ejercicio_social', 'Ejercicio social aprobado', 'Periodo al que corresponden los estados e informes.', 'Ej. Ejercicio terminado el 31 de diciembre de 2025'),
    REQUISITO('informes_presentados', 'Informes presentados', 'Identifica informes de administración, vigilancia y estados financieros.', 'Ej. Informe del administrador, comisario y estados financieros'),
  ],
  extraordinaria: [
    REQUISITO('acuerdo_extraordinario', 'Acuerdo extraordinario', 'Describe la reforma, operación o decisión que requiere esta asamblea.', 'Ej. Reforma de objeto social'),
    REQUISITO('quorum_mayoria', 'Quórum y mayoría aplicables', 'Asienta convocatoria, capital representado y mayoría efectivamente obtenida.', 'Ej. Primera convocatoria; 80% representado; 75% a favor'),
  ],
  mixta: [
    REQUISITO('asuntos_ordinarios_extraordinarios', 'Separación de asuntos', 'Distingue qué puntos son ordinarios y cuáles extraordinarios.', 'Ej. Punto 1 ordinario; puntos 2 y 3 extraordinarios', 'textarea'),
    REQUISITO('quorum_mayoria', 'Quórum y mayorías por asunto', 'Indica el cómputo aplicable a cada tipo de acuerdo.', 'Describe quórum y votación', 'textarea'),
  ],
  aumento_capital: [
    REQUISITO('capital_anterior_nuevo', 'Capital anterior y capital aprobado', 'Importes antes y después del aumento.', 'Ej. Variable anterior $100,000; aumento $50,000; nuevo $150,000'),
    REQUISITO('modalidad_aumento', 'Modalidad y forma de suscripción', 'Aportaciones, capitalización, nuevas acciones/partes y derecho de preferencia.', 'Describe la modalidad y el plazo de pago', 'textarea'),
  ],
  reduccion_capital: [
    REQUISITO('capital_reduccion', 'Capital a reducir y motivo', 'Importe, serie o partes afectadas y causa de la reducción.', 'Ej. Reducción de $25,000 por reembolso'),
    REQUISITO('proteccion_acreedores', 'Protección de acreedores', 'Publicaciones, oposición, plazo y demás medidas aplicables.', 'Indica publicaciones y plazo legal', 'textarea'),
  ],
  fusion: [
    REQUISITO('sociedades_fusion', 'Sociedades participantes y carácter', 'Identifica fusionante, fusionadas y sociedad que subsiste o se constituye.', 'Describe las sociedades participantes', 'textarea'),
    REQUISITO('bases_fusion', 'Bases, balance y fecha de efectos', 'Incluye proyecto, balances, canje y fecha prevista de efectos.', 'Resume las bases de la fusión', 'textarea'),
  ],
  escision: [
    REQUISITO('sociedad_escindente', 'Sociedad escindente y beneficiarias', 'Identifica sociedades y patrimonio que se transmite a cada una.', 'Describe escindente y beneficiarias', 'textarea'),
    REQUISITO('proyecto_escision', 'Proyecto de escisión', 'Indica activos, pasivos, acciones o partes y fecha de efectos.', 'Resume el proyecto aprobado', 'textarea'),
  ],
  disolucion_liquidacion: [
    REQUISITO('causa_disolucion', 'Causa de disolución', 'Causa legal o estatutaria y fecha en que se actualiza.', 'Ej. Disolución anticipada aprobada por la asamblea'),
    REQUISITO('etapa_liquidacion', 'Etapa documentada', 'Distingue disolución, nombramiento, balance inicial o liquidación final.', 'Ej. Solo disolución y nombramiento de liquidador'),
  ],
  sesion_consejo: [
    REQUISITO('integracion_consejo', 'Integración y quórum del consejo', 'Consejeros presentes, ausentes, secretario y quórum estatutario.', 'Describe la integración y quórum', 'textarea'),
    REQUISITO('facultad_consejo', 'Facultad estatutaria del consejo', 'Cláusula que habilita al consejo para resolver el asunto.', 'Ej. Cláusula 28 de estatutos'),
  ],
  modificacion_estatutos: [
    REQUISITO('clausulas_modificadas', 'Cláusulas modificadas', 'Texto actual, texto aprobado y justificación de cada modificación.', 'Describe las cláusulas y nuevo texto', 'textarea'),
  ],
  nombramiento_administrador: [
    REQUISITO('persona_nombrada', 'Persona y cargo', 'Nombre completo, cargo, vigencia y aceptación.', 'Ej. Ana Ruiz, administradora única, periodo 2026-2028'),
    REQUISITO('facultades_cargo', 'Facultades y límites', 'Facultades estatutarias, poderes y restricciones aprobadas.', 'Describe facultades y límites', 'textarea'),
  ],
  remocion_administrador: [
    REQUISITO('persona_removida', 'Persona y cargo removido', 'Nombre, cargo, fecha efectiva y causa documentada.', 'Identifica a la persona y la causa', 'textarea'),
    REQUISITO('entrega_cargo', 'Entrega y sustitución', 'Actos de entrega, revocación de poderes y sustitución, si aplica.', 'Describe la entrega y sustitución', 'textarea'),
  ],
  otorgamiento_poderes: [
    REQUISITO('apoderado_facultades', 'Apoderado y facultades', 'Nombre, tipo de poder, límites, vigencia y forma de ejercicio.', 'Describe facultades, límites y vigencia', 'textarea'),
  ],
  revocacion_poderes: [
    REQUISITO('poder_revocado', 'Poder y apoderado revocados', 'Instrumento, fecha, fedatario y facultades que se dejan sin efecto.', 'Identifica el poder y apoderado', 'textarea'),
  ],
  transmision_acciones: [
    REQUISITO('transmitente_adquirente', 'Transmitente y adquirente', 'Identifica partes, número/serie de acciones, precio y fecha.', 'Describe transmitente, adquirente y acciones', 'textarea'),
    REQUISITO('autorizaciones_acciones', 'Autorizaciones y registro', 'Consentimiento estatutario, derecho de preferencia y libro de registro.', 'Indica autorizaciones y registro', 'textarea'),
  ],
  cesion_partes_sociales: [
    REQUISITO('cedente_cesionario', 'Cedente y cesionario', 'Identifica partes sociales, precio, fecha y consentimiento requerido.', 'Describe cedente, cesionario y partes', 'textarea'),
    REQUISITO('consentimiento_socios', 'Consentimiento de socios', 'Mayoría o unanimidad exigida por ley y estatutos.', 'Indica votación y consentimiento', 'textarea'),
  ],
  admision_nuevos_socios: [
    REQUISITO('nuevo_socio_aportacion', 'Nuevo socio y aportación', 'Identidad, aportación, participación y fecha de ingreso.', 'Describe persona, aportación y participación', 'textarea'),
    REQUISITO('consentimiento_admision', 'Consentimiento de admisión', 'Mayoría y autorizaciones conforme a ley y estatutos.', 'Indica votación y autorizaciones', 'textarea'),
  ],
  separacion_exclusion_socios: [
    REQUISITO('socio_causa', 'Socio y causa', 'Identifica socio, hechos, fundamento estatutario y fecha efectiva.', 'Describe hechos y causa', 'textarea'),
    REQUISITO('garantia_audiencia', 'Procedimiento y audiencia', 'Notificación, oportunidad de defensa y resolución adoptada.', 'Describe notificación y audiencia', 'textarea'),
  ],
  nombramiento_liquidadores: [
    REQUISITO('liquidadores', 'Liquidador o liquidadores', 'Nombre, aceptación, facultades y remuneración, si aplica.', 'Identifica liquidador(es) y facultades', 'textarea'),
  ],
  aprobacion_balance_liquidacion: [
    REQUISITO('balance_final', 'Balance final y haber social', 'Fecha del balance, activos, pasivos y distribución del haber.', 'Resume balance y distribución', 'textarea'),
    REQUISITO('publicacion_balance', 'Publicación y cancelación', 'Publicaciones, aprobación final y cancelación registral/fiscal prevista.', 'Indica formalidades pendientes', 'textarea'),
  ],
  transformacion_sociedad: [
    REQUISITO('tipo_origen_destino', 'Tipo societario de origen y destino', 'Identifica ambos tipos y continuidad de derechos y obligaciones.', 'Ej. S. de R.L. a S.A. de C.V.'),
    REQUISITO('bases_transformacion', 'Bases y estatutos de la transformación', 'Capital, socios/accionistas, estatutos y fecha de efectos.', 'Resume las bases aprobadas', 'textarea'),
  ],
  emision_acciones: [
    REQUISITO('serie_clase_acciones', 'Serie, clase y derechos', 'Número, valor nominal, serie, clase, derechos y restricciones.', 'Describe serie, clase y derechos', 'textarea'),
    REQUISITO('precio_suscripcion', 'Precio y forma de suscripción', 'Precio, plazo, forma de pago y derecho de preferencia.', 'Indica precio, plazo y pago', 'textarea'),
  ],
  aprobacion_estados_financieros: [
    REQUISITO('ejercicio_estados', 'Ejercicio y estados aprobados', 'Periodo, balance, resultados y notas que se someten a aprobación.', 'Identifica ejercicio y documentos', 'textarea'),
    REQUISITO('destino_utilidades', 'Destino de utilidades o pérdidas', 'Reserva legal, dividendos, pérdidas y saldos aprobados.', 'Describe el destino aprobado', 'textarea'),
  ],
  asamblea_especial_accionistas: [
    REQUISITO('clase_acciones', 'Clase o serie afectada', 'Identifica la clase, serie y número de acciones con derechos afectados.', 'Ej. Acciones Serie B'),
    REQUISITO('derechos_afectados', 'Derechos afectados y consentimiento', 'Explica el cambio y la mayoría especial obtenida.', 'Describe derechos y votación', 'textarea'),
  ],
  sesion_vigilancia_comisarios: [
    REQUISITO('organo_vigilancia', 'Órgano y responsables', 'Comisario, comité u órgano previsto en estatutos.', 'Identifica órgano y responsables'),
    REQUISITO('informe_vigilancia', 'Informe y observaciones', 'Periodo, hallazgos, recomendaciones y documentos revisados.', 'Resume el informe', 'textarea'),
  ],
}

export function requisitosParaActa(tipoActa) {
  return [...(REQUISITOS_POR_ACTA[tipoActa] || []), ...REQUISITOS_COMUNES]
}

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
  /** Información de la empresa / sociedad (sección lateral independiente). */
  tipo_sociedad: '',
  logo_empresa: '',
  firma_electronica: false,
  usar_info_empresa: false,
  datos_especificos: {},
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
