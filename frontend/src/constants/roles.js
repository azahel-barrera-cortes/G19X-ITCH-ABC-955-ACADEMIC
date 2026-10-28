/**
 * Roles y control de acceso del lado del cliente (espejo del RBAC del backend).
 *
 * La autoridad final es el backend (cada endpoint valida el JWT y el rol); este
 * módulo solo controla qué secciones de la interfaz se muestran al usuario,
 * para que nadie vea funciones que no le corresponden.
 *
 * Niveles (un número mayor incluye los permisos del menor):
 *   capturista (1) < revisor (2) < abogado_responsable (3) < Administrador (4)
 */
export const NIVEL_ROL = {
  capturista: 1,
  revisor: 2,
  abogado_responsable: 3,
  Administrador: 4,
}

export const ROLES = [
  {
    valor: 'capturista',
    etiqueta: 'Capturista',
    descripcion: 'Crea y edita actas, redacta con IA, genera PDF y usa el asistente.',
  },
  {
    valor: 'revisor',
    etiqueta: 'Revisor',
    descripcion: 'Todo lo del capturista, además consulta la biblioteca, la administración y la bitácora.',
  },
  {
    valor: 'abogado_responsable',
    etiqueta: 'Abogado responsable',
    descripcion: 'Todo lo del revisor, además cambia estatus, aprueba y valida actas.',
  },
  {
    valor: 'Administrador',
    etiqueta: 'Administrador',
    descripcion: 'Acceso total: gestiona usuarios y puede eliminar actas.',
  },
]

/** Nivel numérico del rol (0 si es desconocido o no hay sesión). */
export function nivelDe(rol) {
  return NIVEL_ROL[rol] || 0
}

/** True si `rol` tiene al menos el nivel de `minimo`. */
export function tieneAcceso(rol, minimo) {
  return nivelDe(rol) >= nivelDe(minimo)
}

/**
 * Secciones del sistema de actas con el rol mínimo requerido, alineadas con el
 * RBAC del backend (`backend/app/api/v1/deps.py` y los endpoints):
 *
 * - generar / asistente / empresa / ayuda: cualquier usuario autenticado.
 * - biblioteca: revisor+ (GET /actas y /actas/{id} lo exigen).
 * - administracion: revisor+ (las consultas lo exigen; las mutaciones, capturista+).
 */
export const SECCIONES_SISTEMA = [
  {
    id: 'generar',
    minimo: 'capturista',
    etiqueta: 'Generar acta',
    descripcion: 'Plantillas, formulario manual y modo IA',
  },
  {
    id: 'asistente',
    minimo: 'capturista',
    etiqueta: 'Asistente IA',
    descripcion: 'Chat de actas: redacta, valida y crea guiado',
  },
  {
    id: 'biblioteca',
    minimo: 'revisor',
    etiqueta: 'Biblioteca de actas',
    descripcion: 'Historial, estatus, PDF y edición',
  },
  {
    id: 'administracion',
    minimo: 'revisor',
    etiqueta: 'Administración',
    descripcion: 'Versiones, vigencia y caducidad',
  },
  {
    id: 'empresa',
    minimo: 'capturista',
    etiqueta: 'Información de la empresa o sociedad',
    descripcion: 'Datos de la sociedad, tipo, logo y firma electrónica',
  },
  {
    id: 'ayuda',
    minimo: 'capturista',
    etiqueta: 'Guía de uso',
    descripcion: 'Flujo, API y notas legales',
  },
]

/** Ids de las secciones visibles para el rol indicado. */
export function seccionesPermitidas(rol) {
  return SECCIONES_SISTEMA.filter((seccion) => tieneAcceso(rol, seccion.minimo)).map(
    (seccion) => seccion.id,
  )
}

/** Fichas de secciones permitidas (para mostrar accesos en el perfil). */
export function seccionesConAcceso(rol) {
  return SECCIONES_SISTEMA.filter((seccion) => tieneAcceso(rol, seccion.minimo))
}

/** Etiqueta legible del rol. */
export function etiquetaRol(rol) {
  return ROLES.find((item) => item.valor === rol)?.etiqueta || rol || 'Sin rol'
}
