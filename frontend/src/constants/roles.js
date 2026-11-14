/**
 * Roles y control de acceso del lado del cliente (espejo del RBAC del backend).
 *
 * La autoridad final es el backend (cada endpoint valida el JWT y el rol); este
 * módulo solo controla qué secciones de la interfaz se muestran al usuario,
 * para que nadie vea funciones que no le corresponden.
 *
 * Niveles de permisos de API (un número mayor incluye los permisos del menor):
 *   capturista (1) < revisor (2) < abogado_responsable (3) < Administrador (4) < SuperAdministrador (5)
 * La navegación de la interfaz, en cambio, se define con una lista exacta por rol.
 */
export const NIVEL_ROL = {
  capturista: 1,
  revisor: 2,
  abogado_responsable: 3,
  Administrador: 4,
  SuperAdministrador: 5,
}

export const ROLES = [
  {
    valor: 'capturista',
    etiqueta: 'Capturista',
    descripcion: 'Crea actas, corrige observaciones y consulta su seguimiento.',
  },
  {
    valor: 'revisor',
    etiqueta: 'Revisor',
    descripcion: 'Revisa borradores, devuelve correcciones y consulta el historial.',
  },
  {
    valor: 'abogado_responsable',
    etiqueta: 'Abogado responsable',
    descripcion: 'Aprueba actas revisadas y genera el PDF final.',
  },
  {
    valor: 'Administrador',
    etiqueta: 'Administrador',
    descripcion: 'Administra usuarios de la empresa y consulta el historial de actas.',
  },
  {
    valor: 'SuperAdministrador',
    etiqueta: 'Super Administrador',
    descripcion: 'Administra usuarios globales y consulta la bitácora del sistema.',
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
 * - generación y seguimiento: Capturista+.
 * - revisión: Revisor+; aprobación final: Abogado responsable+.
 * - biblioteca y administración: consulta del historial y versiones.
 */
export const SECCIONES_SISTEMA = [
  {
    id: 'generar',
    minimo: 'capturista',
    etiqueta: 'Generar acta',
    descripcion: 'Plantillas, formulario manual y modo IA',
  },
  {
    id: 'mis-actas',
    minimo: 'capturista',
    etiqueta: 'Mis actas',
    descripcion: 'Seguimiento de revisiones y correcciones',
  },
  {
    id: 'revision',
    minimo: 'revisor',
    etiqueta: 'Revisión de actas',
    descripcion: 'Revisa borradores y devuelve observaciones',
  },
  {
    id: 'aprobacion',
    minimo: 'abogado_responsable',
    etiqueta: 'Aprobación de actas',
    descripcion: 'Aprueba actas revisadas y genera el PDF final',
  },
  {
    id: 'asistente',
    minimo: 'capturista',
    etiqueta: 'Asistente IA',
    descripcion: 'Asistente por rol: redacción, validación, estatus y tiempos',
  },
  {
    id: 'perfil',
    minimo: 'capturista',
    etiqueta: 'Perfil',
    descripcion: 'Mis datos, funciones y sesión',
  },
  {
    id: 'biblioteca',
    minimo: 'revisor',
    etiqueta: 'Biblioteca de actas',
    descripcion: 'Historial y consulta de actas',
  },
  {
    id: 'administracion',
    minimo: 'revisor',
    etiqueta: 'Administración',
    descripcion: 'Versiones, vigencia y caducidad',
  },
  {
    id: 'ayuda',
    minimo: 'capturista',
    etiqueta: 'Guía de uso',
    descripcion: 'Flujo, API y notas legales',
  },
]

const MENU_POR_ROL = {
  SuperAdministrador: [
    'usuarios',
    'vitacora',
    'guia-super-admin',
  ],
  Administrador: ['perfil', 'usuarios', 'administracion', 'biblioteca', 'ayuda'],
  capturista: ['perfil', 'generar', 'asistente', 'mis-actas', 'ayuda'],
  revisor: ['perfil', 'revision', 'biblioteca', 'ayuda'],
  abogado_responsable: ['perfil', 'aprobacion', 'biblioteca', 'ayuda'],
}

/** Ids de las únicas secciones visibles para cada rol. */
export function seccionesPermitidas(rol) {
  return MENU_POR_ROL[rol] ? [...MENU_POR_ROL[rol]] : []
}

/** Fichas de secciones permitidas (para mostrar accesos en el perfil). */
export function seccionesConAcceso(rol) {
  const permitidas = new Set(seccionesPermitidas(rol))
  return SECCIONES_SISTEMA.filter((seccion) => permitidas.has(seccion.id))
}

/** Etiqueta legible del rol. */
export function etiquetaRol(rol) {
  return ROLES.find((item) => item.valor === rol)?.etiqueta || rol || 'Sin rol'
}

/** Nombre contextual de la guía mostrada a cada rol. */
export function etiquetaGuiaRol(rol) {
  const etiquetas = {
    SuperAdministrador: 'Guía de SuperAdministrador',
    Administrador: 'Guía de Administrador',
    capturista: 'Guía de Capturista',
    revisor: 'Guía de Revisor',
    abogado_responsable: 'Guía de Abogado',
  }
  return etiquetas[rol] || 'Guía de uso'
}
