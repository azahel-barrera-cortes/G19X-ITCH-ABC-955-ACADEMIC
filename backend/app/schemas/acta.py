"""Esquemas Pydantic: contratos de entrada y salida del módulo de actas.

Se utilizan para validar el formulario que envía el frontend, para tipar las
respuestas de la API y como *diccionario de datos* del documento que finalmente
consume el generador de PDF de ReportLab.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import (
    CaracterAsistente,
    EstatusActa,
    MateriaAcuerdo,
    ProveedorIA,
    SeveridadHallazgo,
    TipoAsamblea,
    TipoMayoria,
)


class BaseSchema(BaseModel):
    """Configuración común: orm_mode, enums como valores y alias tolerantes."""

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


# ---------------------------------------------------------------------------
# Piezas del acta
# ---------------------------------------------------------------------------
class ResultadoVotacion(BaseSchema):
    """Resultado de la votación de un acuerdo (acciones o votos computados)."""

    tipo_mayoria: TipoMayoria = TipoMayoria.MAYORIA_SIMPLE
    acciones_a_favor: float = Field(default=0, ge=0)
    acciones_en_contra: float = Field(default=0, ge=0)
    abstenciones: float = Field(default=0, ge=0)
    porcentaje_requerido: Optional[float] = Field(default=None, ge=0, le=100)
    aprobado: bool = True
    comentario: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _coherencia(self) -> "ResultadoVotacion":
        if self.tipo_mayoria == TipoMayoria.SIN_VOTACION:
            self.aprobado = True
        if self.aprobado and self.tipo_mayoria not in (
            TipoMayoria.SIN_VOTACION,
            TipoMayoria.UNANIMIDAD,
        ) and self.acciones_a_favor == 0:
            # Sin votos a favor registrados no puede tenerse por aprobado.
            self.aprobado = False
        return self


class Asistente(BaseSchema):
    """Persona que comparece a la asamblea (accionista, representante o invitado)."""

    nombre: str = Field(min_length=3, max_length=150)
    cargo: Optional[str] = Field(default=None, max_length=120)
    caracter: CaracterAsistente = CaracterAsistente.PROPIETARIO
    acciones: float = Field(default=0, ge=0)
    porcentaje_capital: Optional[float] = Field(default=None, ge=0, le=100)
    rfc: Optional[str] = Field(default=None, max_length=13)
    email: Optional[str] = Field(default=None, max_length=150)
    es_presidente: bool = False
    es_secretario: bool = False
    es_escrutador: bool = False
    firma: bool = Field(default=True, description="Si firma el acta al final del documento")


class OrdenDelDiaPunto(BaseSchema):
    """Punto del orden del día."""

    numero: int = Field(ge=1)
    titulo: str = Field(min_length=3, max_length=250)
    descripcion: Optional[str] = Field(default=None, max_length=1500)
    requiere_votacion: bool = True
    acuerdo_numero: Optional[int] = Field(default=None, ge=1)


class Acuerdo(BaseSchema):
    """Acuerdo sometido a la asamblea.

    ``resumen`` lo captura el usuario; ``clausula_legal`` y ``fundamento_legal``
    son el resultado de la redacción asistida por IA (o de las plantillas
    deterministas cuando no hay servicio de IA disponible).
    """

    numero: int = Field(ge=1)
    titulo: str = Field(min_length=3, max_length=250)
    resumen: str = Field(min_length=5, max_length=4000)
    materia: Optional[MateriaAcuerdo] = None
    clausula_legal: Optional[str] = None
    fundamento_legal: Optional[str] = None
    votacion: Optional[ResultadoVotacion] = None
    generado_por_ia: bool = False

# ---------------------------------------------------------------------------
# Acta: datos de entrada
# ---------------------------------------------------------------------------
class ActaBase(BaseSchema):
    """Datos completos de un acta capturados en el formulario por pasos."""

    # --- Paso 1: datos generales ---
    sociedad: str = Field(min_length=3, max_length=200)
    rfc_sociedad: Optional[str] = Field(default=None, max_length=13)
    tipo_asamblea: TipoAsamblea = TipoAsamblea.ORDINARIA
    titulo: Optional[str] = Field(default=None, max_length=200)
    fecha: date
    hora: Optional[time] = None
    lugar: str = Field(min_length=3, max_length=300)
    # Control: quién la realizó (hoy texto/asistente; mañana usuario autenticado).
    creado_por: Optional[str] = Field(default=None, max_length=150)

    # --- Información de la empresa / sociedad (RF-10) ---
    tipo_sociedad: Optional[str] = Field(default=None, max_length=60)
    logo_empresa: Optional[str] = Field(default=None, description="Logo de la empresa como data URL (base64), para el encabezado del PDF")
    firma_electronica: bool = Field(default=False, description="Incluir leyenda de firma electrónica en el acta")
    usar_info_empresa: bool = Field(default=False, description="Usar automáticamente tipo_sociedad, logo_empresa y firma_electronica al generar el acta")

    # --- Convocatoria (art. 186 LGSM) ---
    convocatoria_fecha: Optional[date] = None
    convocatoria_medio: Optional[str] = Field(default=None, max_length=120)
    convocatoria_quien: Optional[str] = Field(default=None, max_length=150)

    # --- Capital y quórum ---
    capital_social: Optional[float] = Field(default=None, ge=0)
    acciones_totales: Optional[float] = Field(default=None, ge=0)
    capital_presente: Optional[float] = Field(default=None, ge=0)
    quorum_porcentaje: Optional[float] = Field(default=None, ge=0, le=100)

    # --- Paso 2: mesa directiva y asistentes ---
    presidente: str = Field(min_length=3, max_length=150)
    secretario: str = Field(min_length=3, max_length=150)
    asistentes: List[Asistente] = Field(min_length=1)

    # --- Paso 3: orden del día y acuerdos ---
    orden_del_dia: List[OrdenDelDiaPunto] = Field(min_length=1)
    acuerdos: List[Acuerdo] = Field(min_length=1)
    observaciones: Optional[str] = Field(default=None, max_length=4000)
    estatus: EstatusActa = EstatusActa.BORRADOR

    @field_validator("rfc_sociedad")
    @classmethod
    def _normalizar_rfc(cls, valor: Optional[str]) -> Optional[str]:
        return valor.upper() if valor else valor

    @model_validator(mode="after")
    def _completar_calculos(self) -> "ActaBase":
        """Deriva datos que el usuario puede omitir para reducir errores de captura."""
        # 1) Quórum porcentual a partir del capital presente.
        if self.quorum_porcentaje is None and self.capital_presente is not None and self.capital_social:
            self.quorum_porcentaje = round(self.capital_presente / self.capital_social * 100, 4)

        # 2) Porcentaje de capital de cada asistente cuando se conoce su tenencia.
        base_acciones = self.acciones_totales or self.capital_social
        if base_acciones:
            for asistente in self.asistentes:
                if asistente.porcentaje_capital is None and asistente.acciones:
                    asistente.porcentaje_capital = round(asistente.acciones / base_acciones * 100, 4)

        # 3) Coherencia temporal de la convocatoria.
        if self.convocatoria_fecha and self.convocatoria_fecha > self.fecha:
            raise ValueError(
                "La fecha de convocatoria no puede ser posterior a la fecha de celebración "
                "de la asamblea."
            )

        # 4) Numeración única del orden del día y de los acuerdos.
        numeros_orden = [punto.numero for punto in self.orden_del_dia]
        if len(numeros_orden) != len(set(numeros_orden)):
            raise ValueError("El orden del día contiene números de punto repetidos.")

        numeros_acuerdos = [acuerdo.numero for acuerdo in self.acuerdos]
        if len(numeros_acuerdos) != len(set(numeros_acuerdos)):
            raise ValueError("Los acuerdos contienen números repetidos.")

        # 5) El capital representado no puede exceder al capital social.
        total_porcentaje = sum(
            asistente.porcentaje_capital or 0 for asistente in self.asistentes
        )
        if total_porcentaje > 100.5:
            raise ValueError(
                "La suma de los porcentajes de capital de los asistentes "
                f"({total_porcentaje:.2f}%) excede el 100% del capital social."
            )
        return self


# ---------------------------------------------------------------------------
# Peticiones
# ---------------------------------------------------------------------------
class ActaRedaccionRequest(ActaBase):
    """Petición de redacción asistida (borrador con IA) y/o validación."""

    generar_clausulas: bool = Field(
        default=True, description="Redactar las cláusulas legales de cada acuerdo"
    )
    incluir_validacion: bool = Field(
        default=True, description="Ejecutar la validación de consistencia documental"
    )
    instrucciones_adicionales: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Indicaciones específicas para la redacción (estilo, cláusulas obligatorias, etc.)",
    )


class ActaGenerarPdfRequest(ActaRedaccionRequest):
    """Petición del endpoint principal ``POST /actas/generar-pdf``."""

    guardar: bool = Field(default=True, description="Persistir el acta en la base de datos")
    actualizar_acta_id: Optional[int] = Field(
        default=None, ge=1, description="Al regenerar el PDF de un acta existente, su identificador"
    )
    incluir_tabla_asistentes: bool = True
    incluir_hoja_firmas: bool = True
    incluir_anexo_validacion: bool = Field(
        default=False, description="Añadir al PDF el anexo con los hallazgos de la validación"
    )


class ActaActualizarRequest(ActaBase):
    """Reemplaza íntegramente el contenido de un acta (PUT) y genera nueva versión."""

    regenerar_con_ia: bool = False
    motivo_cambio: Optional[str] = Field(default=None, max_length=300)

# ---------------------------------------------------------------------------
# Validación de consistencia
# ---------------------------------------------------------------------------
class Hallazgo(BaseSchema):
    """Observación detectada durante la validación del acta."""

    severidad: SeveridadHallazgo = SeveridadHallazgo.INFORMATIVO
    campo: Optional[str] = Field(default=None, description="Campo o sección afectada")
    mensaje: str
    sugerencia: Optional[str] = None


class ValidacionActa(BaseSchema):
    """Resultado de la validación documental (IA o reglas deterministas)."""

    puntaje: float = Field(ge=0, le=100, description="Calidad/consistencia de 0 a 100")
    consistencia: str = Field(description="Resumen ejecutivo del resultado")
    hallazgos: List[Hallazgo] = Field(default_factory=list)
    recomendaciones: List[str] = Field(default_factory=list)
    proveedor: ProveedorIA = ProveedorIA.PLANTILLAS
    generado_por_ia: bool = False
    fecha_validacion: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Respuestas
# ---------------------------------------------------------------------------
class ActaRedaccionResponse(BaseSchema):
    """Borrador redactado: cláusulas, acuerdos enriquecidos y validación."""

    folio: str
    sociedad: str
    tipo_asamblea: TipoAsamblea
    clausulas: Dict[str, str] = Field(default_factory=dict)
    acuerdos: List[Acuerdo] = Field(default_factory=list)
    texto_legal: str = ""
    validacion: Optional[ValidacionActa] = None
    proveedor_ia: ProveedorIA = ProveedorIA.PLANTILLAS
    ia_habilitada: bool = False
    advertencias: List[str] = Field(default_factory=list)


class ActaResumen(BaseSchema):
    """Vista ligera para los listados."""

    id: int
    folio: str
    sociedad: str
    tipo_asamblea: TipoAsamblea
    titulo: Optional[str] = None
    fecha: date
    estatus: EstatusActa
    version: int
    proveedor_ia: Optional[ProveedorIA] = None
    # Control: quién la realizó y cuándo (hoy texto/asistente; mañana usuario).
    creado_por: Optional[str] = None
    # Gobernanza: estado de vigencia calculado por el backend.
    fecha_caducidad: Optional[date] = None
    estado_caducidad: str = "sin_fecha"
    dias_para_caducar: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ActaRead(ActaBase):
    """Acta completa tal como se almacena en la base de datos."""

    id: int
    folio: str
    version: int
    clausulas: Dict[str, str] = Field(default_factory=dict)
    texto_legal: str = ""
    validacion_ia: Optional[ValidacionActa] = None
    proveedor_ia: Optional[ProveedorIA] = None
    # Control: quién la realizó y cuándo (listo para integración de usuarios).
    creado_por: Optional[str] = None
    # Gobernanza: vigencia y clasificación calculada del acta.
    fecha_caducidad: Optional[date] = None
    motivo_caducidad: Optional[str] = None
    estado_caducidad: str = "sin_fecha"
    dias_para_caducar: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MetadatosPdf(BaseSchema):
    """Metadatos del PDF generado (se devuelven como encabezados HTTP)."""

    folio: str
    acta_id: Optional[int] = None
    version: int = 1
    nombre_archivo: str
    bytes: int
    paginas: int
    proveedor_ia: ProveedorIA = ProveedorIA.PLANTILLAS
    puntaje_validacion: Optional[float] = None
    guardada: bool = False


class ApiMensaje(BaseSchema):
    """Respuesta simple para operaciones sin cuerpo de datos."""

    mensaje: str
    detalle: Optional[str] = None


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------
class CatalogOpcion(BaseSchema):
    """Opción de un catálogo (para ``<select>`` del formulario)."""

    valor: str
    etiqueta: str
    descripcion: Optional[str] = None
    articulos: Optional[List[str]] = None
    porcentaje_requerido: Optional[float] = None


class CatalogosResponse(BaseSchema):
    """Conjunto completo de catálogos consumidos por el frontend."""

    tipos_asamblea: List[CatalogOpcion] = Field(default_factory=list)
    tipos_mayoria: List[CatalogOpcion] = Field(default_factory=list)
    caracteres_asistente: List[CatalogOpcion] = Field(default_factory=list)
    estatus_acta: List[CatalogOpcion] = Field(default_factory=list)
    proveedor_ia: str = "plantillas"
    ia_habilitada: bool = False


# ---------------------------------------------------------------------------
# Administración: versiones y caducidad
# ---------------------------------------------------------------------------
class VersionActaResumen(BaseSchema):
    """Entrada del historial de versiones de un acta."""

    id: int
    acta_id: int
    version: int
    motivo: str
    estatus: str
    creado_por: Optional[str] = None
    created_at: Optional[datetime] = None


class VersionActaDetalle(VersionActaResumen):
    """Versión con su contenido completo (instantánea del acta en ese momento)."""

    contenido: Dict[str, Any] = Field(default_factory=dict)
    # Indica si esta versión es la vigente del acta.
    vigente: bool = False


class CaducidadRequest(BaseSchema):
    """Fija la vigencia de un acta; ``fecha_caducidad: null`` elimina el plazo."""

    fecha_caducidad: Optional[date] = Field(
        default=None, description="Fecha en la que el acta pasa a considerarse vencida"
    )
    motivo: Optional[str] = Field(default=None, max_length=300)


class VigenciaActa(BaseSchema):
    """Resumen de una acta para el módulo de caducidad."""

    id: int
    folio: str
    sociedad: str
    tipo_asamblea: TipoAsamblea
    titulo: Optional[str] = None
    fecha: date
    estatus: EstatusActa
    version: int
    fecha_caducidad: Optional[date] = None
    motivo_caducidad: Optional[str] = None
    estado_caducidad: str = "sin_fecha"
    dias_para_caducar: Optional[int] = None


class ResumenAdministracion(BaseSchema):
    """Estadísticas globales para el panel de administración de actas."""

    total_actas: int = 0
    total_versiones: int = 0
    por_estatus: Dict[str, int] = Field(default_factory=dict)
    vigencia: Dict[str, int] = Field(default_factory=dict)


