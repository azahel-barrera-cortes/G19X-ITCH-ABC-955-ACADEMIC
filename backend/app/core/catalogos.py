"""Catálogos de dominio expuestos a la API y utilizados por el frontend.

Centralizan las etiquetas legibles (español) y las referencias normativas de cada
tipo de asamblea y de mayoría, evitando duplicar textos entre backend y frontend.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.models.enums import (
    CaracterAsistente,
    EstatusActa,
    MateriaAcuerdo,
    TipoAsamblea,
    TipoMayoria,
    TipoSociedad,
)

# ---------------------------------------------------------------------------
# Tipos societarios y marco normativo principal
# ---------------------------------------------------------------------------
TIPOS_SOCIEDAD: List[Dict[str, Any]] = [
    {"valor": TipoSociedad.SA.value, "etiqueta": "Sociedad Anónima (S.A.)", "abreviatura": "S.A.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SRL.value, "etiqueta": "Sociedad de Responsabilidad Limitada (S. de R.L.)", "abreviatura": "S. de R.L.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SCS.value, "etiqueta": "Sociedad en Comandita Simple (S. en C.)", "abreviatura": "S. en C.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SAS.value, "etiqueta": "Sociedad por Acciones Simplificada (S.A.S.)", "abreviatura": "S.A.S.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SCA.value, "etiqueta": "Sociedad en Comandita por Acciones (S. en C. por A.)", "abreviatura": "S. en C. por A.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.COOPERATIVA.value, "etiqueta": "Sociedad Cooperativa (S.Coop.)", "abreviatura": "S.Coop.", "ordenamiento": "LGSC"},
    {"valor": TipoSociedad.SNC.value, "etiqueta": "Sociedad en Nombre Colectivo (S. en N.C.)", "abreviatura": "S. en N.C.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SA_CV.value, "etiqueta": "Sociedad Anónima de Capital Variable (S.A. de C.V.)", "abreviatura": "S.A. de C.V.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SRL_CV.value, "etiqueta": "Sociedad de Responsabilidad Limitada de Capital Variable (S. de R.L. de C.V.)", "abreviatura": "S. de R.L. de C.V.", "ordenamiento": "LGSM"},
    {"valor": TipoSociedad.SAPI.value, "etiqueta": "Sociedad Anónima Promotora de Inversión (S.A.P.I.)", "abreviatura": "S.A.P.I.", "ordenamiento": "LMV y LGSM"},
    {"valor": TipoSociedad.SAPI_CV.value, "etiqueta": "Sociedad Anónima Promotora de Inversión de Capital Variable (S.A.P.I. de C.V.)", "abreviatura": "S.A.P.I. de C.V.", "ordenamiento": "LMV y LGSM"},
    {"valor": TipoSociedad.SAB.value, "etiqueta": "Sociedad Anónima Bursátil (S.A.B.)", "abreviatura": "S.A.B.", "ordenamiento": "LMV"},
    {"valor": TipoSociedad.SCIVIL.value, "etiqueta": "Sociedad Civil (S.C.)", "abreviatura": "S.C.", "ordenamiento": "Código Civil aplicable"},
]

_ACTA_ITEMS: Tuple[Tuple[TipoAsamblea, str, str], ...] = (
    (TipoAsamblea.CONSTITUTIVA, "Asamblea constitutiva", "Acto de constitución de la sociedad."),
    (TipoAsamblea.ORDINARIA, "Asamblea general ordinaria", "Asuntos ordinarios de la sociedad."),
    (TipoAsamblea.EXTRAORDINARIA, "Asamblea general extraordinaria", "Acuerdos de naturaleza extraordinaria."),
    (TipoAsamblea.MIXTA, "Asamblea general mixta", "Asuntos ordinarios y extraordinarios en una misma sesión."),
    (TipoAsamblea.AUMENTO_CAPITAL, "Aumento de capital social", "Aumento de capital o resolución de socios."),
    (TipoAsamblea.REDUCCION_CAPITAL, "Reducción de capital social", "Reducción con protección de acreedores."),
    (TipoAsamblea.FUSION, "Acta de fusión", "Acuerdo de fusión entre sociedades."),
    (TipoAsamblea.ESCISION, "Acta de escisión", "División o transmisión de patrimonio."),
    (TipoAsamblea.DISOLUCION_LIQUIDACION, "Acta de disolución y liquidación", "Disolución y etapas de liquidación."),
    (TipoAsamblea.SESION_CONSEJO, "Sesión del consejo de administración", "Actuaciones del consejo cuando exista."),
    (TipoAsamblea.MODIFICACION_ESTATUTOS, "Acta de modificación de estatutos", "Cambio de cláusulas del contrato social."),
    (TipoAsamblea.NOMBRAMIENTO_ADMINISTRADOR, "Nombramiento de administrador", "Designación de administrador único o consejo."),
    (TipoAsamblea.REMOCION_ADMINISTRADOR, "Remoción o revocación de administrador", "Terminación de un nombramiento."),
    (TipoAsamblea.OTORGAMIENTO_PODERES, "Otorgamiento de poderes", "Conferimiento de facultades de representación."),
    (TipoAsamblea.REVOCACION_PODERES, "Revocación de poderes", "Retiro de facultades previamente otorgadas."),
    (TipoAsamblea.TRANSMISION_ACCIONES, "Transmisión de acciones", "Registro de cambios de titularidad accionaria."),
    (TipoAsamblea.CESION_PARTES_SOCIALES, "Cesión de partes sociales", "Cambio de socios en sociedades de partes sociales."),
    (TipoAsamblea.ADMISION_NUEVOS_SOCIOS, "Admisión de nuevos socios", "Incorporación de integrantes."),
    (TipoAsamblea.SEPARACION_EXCLUSION_SOCIOS, "Separación o exclusión de socios", "Salida o exclusión cuando proceda."),
    (TipoAsamblea.NOMBRAMIENTO_LIQUIDADORES, "Nombramiento de liquidadores", "Designación de responsables de liquidación."),
    (TipoAsamblea.APROBACION_BALANCE_LIQUIDACION, "Aprobación del balance final de liquidación", "Aprobación del resultado final."),
    (TipoAsamblea.TRANSFORMACION_SOCIEDAD, "Transformación de sociedad", "Cambio de tipo societario."),
    (TipoAsamblea.EMISION_ACCIONES, "Emisión de acciones", "Emisión y condiciones de acciones."),
    (TipoAsamblea.APROBACION_ESTADOS_FINANCIEROS, "Aprobación de estados financieros", "Presentación y aprobación del ejercicio."),
    (TipoAsamblea.ASAMBLEA_ESPECIAL_ACCIONISTAS, "Asamblea especial de accionistas", "Asuntos que afectan una clase de acciones."),
    (TipoAsamblea.SESION_VIGILANCIA_COMISARIOS, "Sesión de vigilancia o comisarios", "Actuaciones del órgano de vigilancia."),
)

ACTAS_CORPORATIVAS: List[Dict[str, Any]] = [
    {"valor": tipo.value, "etiqueta": etiqueta, "descripcion": descripcion}
    for tipo, etiqueta, descripcion in _ACTA_ITEMS
]

REQUISITOS_ACTA: Dict[str, List[Dict[str, str]]] = {
    "constitutiva": [
        {"clave": "fundadores", "etiqueta": "socios o accionistas fundadores", "pregunta": "Indica fundadores, nacionalidad, domicilio y participación de cada uno."},
        {"clave": "capital_constitutivo", "etiqueta": "capital suscrito y forma de pago", "pregunta": "Indica capital, aportaciones, acciones o partes sociales y exhibición inicial."},
        {"clave": "estatutos_iniciales", "etiqueta": "estatutos y objeto social", "pregunta": "Describe objeto, domicilio, duración, administración y vigilancia inicial."},
    ],
    "ordinaria": [
        {"clave": "ejercicio_social", "etiqueta": "ejercicio social aprobado", "pregunta": "Indica el ejercicio al que corresponden los estados e informes."},
        {"clave": "informes_presentados", "etiqueta": "informes presentados", "pregunta": "Identifica los informes de administración, vigilancia y estados financieros presentados."},
    ],
    "extraordinaria": [
        {"clave": "acuerdo_extraordinario", "etiqueta": "acuerdo extraordinario", "pregunta": "Describe el acuerdo que requiere asamblea extraordinaria."},
        {"clave": "quorum_mayoria", "etiqueta": "quórum y mayoría aplicables", "pregunta": "Indica convocatoria, capital representado y mayoría efectivamente obtenida."},
    ],
    "mixta": [
        {"clave": "asuntos_ordinarios_extraordinarios", "etiqueta": "separación de asuntos", "pregunta": "Distingue qué puntos son ordinarios y cuáles extraordinarios."},
        {"clave": "quorum_mayoria", "etiqueta": "quórum y mayorías por asunto", "pregunta": "Indica el cómputo aplicable a cada acuerdo."},
    ],
    "aumento_capital": [
        {"clave": "capital_anterior_nuevo", "etiqueta": "capital anterior y aprobado", "pregunta": "Indica capital antes y después del aumento."},
        {"clave": "modalidad_aumento", "etiqueta": "modalidad y suscripción", "pregunta": "Explica aportaciones, capitalización, nuevas acciones o partes y derecho de preferencia."},
    ],
    "reduccion_capital": [
        {"clave": "capital_reduccion", "etiqueta": "capital a reducir y motivo", "pregunta": "Indica importe, acciones o partes afectadas y causa."},
        {"clave": "proteccion_acreedores", "etiqueta": "protección de acreedores", "pregunta": "Indica publicaciones, oposición, plazos y medidas aplicables."},
    ],
    "fusion": [
        {"clave": "sociedades_fusion", "etiqueta": "sociedades participantes", "pregunta": "Identifica fusionante, fusionadas y sociedad que subsiste o se constituye."},
        {"clave": "bases_fusion", "etiqueta": "bases, balance y efectos", "pregunta": "Resume proyecto, balances, canje y fecha prevista de efectos."},
    ],
    "escision": [
        {"clave": "sociedad_escindente", "etiqueta": "escindente y beneficiarias", "pregunta": "Identifica sociedades y patrimonio transmitido a cada una."},
        {"clave": "proyecto_escision", "etiqueta": "proyecto de escisión", "pregunta": "Indica activos, pasivos, acciones o partes y fecha de efectos."},
    ],
    "disolucion_liquidacion": [
        {"clave": "causa_disolucion", "etiqueta": "causa de disolución", "pregunta": "Indica causa legal o estatutaria y fecha en que se actualiza."},
        {"clave": "etapa_liquidacion", "etiqueta": "etapa documentada", "pregunta": "Distingue disolución, nombramiento, balance inicial o liquidación final."},
    ],
    "sesion_consejo": [
        {"clave": "integracion_consejo", "etiqueta": "integración y quórum del consejo", "pregunta": "Indica consejeros presentes, ausentes, secretario y quórum estatutario."},
        {"clave": "facultad_consejo", "etiqueta": "facultad estatutaria", "pregunta": "Indica la cláusula que habilita al consejo para resolver."},
    ],
    "modificacion_estatutos": [
        {"clave": "clausulas_modificadas", "etiqueta": "cláusulas modificadas", "pregunta": "Indica texto actual, texto aprobado y justificación de cada modificación."},
    ],
    "nombramiento_administrador": [
        {"clave": "persona_nombrada", "etiqueta": "persona y cargo", "pregunta": "Indica nombre, cargo, vigencia y aceptación."},
        {"clave": "facultades_cargo", "etiqueta": "facultades y límites", "pregunta": "Indica facultades estatutarias, poderes y restricciones."},
    ],
    "remocion_administrador": [
        {"clave": "persona_removida", "etiqueta": "persona y cargo removido", "pregunta": "Indica nombre, cargo, fecha efectiva y causa."},
        {"clave": "entrega_cargo", "etiqueta": "entrega y sustitución", "pregunta": "Indica entrega, revocación de poderes y sustitución, si aplica."},
    ],
    "otorgamiento_poderes": [
        {"clave": "apoderado_facultades", "etiqueta": "apoderado y facultades", "pregunta": "Indica nombre, tipo de poder, límites, vigencia y forma de ejercicio."},
    ],
    "revocacion_poderes": [
        {"clave": "poder_revocado", "etiqueta": "poder y apoderado revocados", "pregunta": "Indica instrumento, fecha, fedatario y facultades que se dejan sin efecto."},
    ],
    "transmision_acciones": [
        {"clave": "transmitente_adquirente", "etiqueta": "transmitente y adquirente", "pregunta": "Indica partes, número o serie de acciones, precio y fecha."},
        {"clave": "autorizaciones_acciones", "etiqueta": "autorizaciones y registro", "pregunta": "Indica consentimiento, derecho de preferencia y libro de registro."},
    ],
    "cesion_partes_sociales": [
        {"clave": "cedente_cesionario", "etiqueta": "cedente y cesionario", "pregunta": "Indica partes sociales, precio, fecha y consentimiento requerido."},
        {"clave": "consentimiento_socios", "etiqueta": "consentimiento de socios", "pregunta": "Indica mayoría o unanimidad exigida por ley y estatutos."},
    ],
    "admision_nuevos_socios": [
        {"clave": "nuevo_socio_aportacion", "etiqueta": "nuevo socio y aportación", "pregunta": "Indica identidad, aportación, participación y fecha de ingreso."},
        {"clave": "consentimiento_admision", "etiqueta": "consentimiento de admisión", "pregunta": "Indica mayoría y autorizaciones conforme a ley y estatutos."},
    ],
    "separacion_exclusion_socios": [
        {"clave": "socio_causa", "etiqueta": "socio y causa", "pregunta": "Indica socio, hechos, fundamento estatutario y fecha efectiva."},
        {"clave": "garantia_audiencia", "etiqueta": "procedimiento y audiencia", "pregunta": "Indica notificación, defensa y resolución adoptada."},
    ],
    "nombramiento_liquidadores": [
        {"clave": "liquidadores", "etiqueta": "liquidador o liquidadores", "pregunta": "Indica nombre, aceptación, facultades y remuneración, si aplica."},
    ],
    "aprobacion_balance_liquidacion": [
        {"clave": "balance_final", "etiqueta": "balance final y haber social", "pregunta": "Indica fecha, activos, pasivos y distribución del haber."},
        {"clave": "publicacion_balance", "etiqueta": "publicación y cancelación", "pregunta": "Indica formalidades pendientes de publicación, inscripción y cancelación."},
    ],
    "transformacion_sociedad": [
        {"clave": "tipo_origen_destino", "etiqueta": "tipo societario de origen y destino", "pregunta": "Indica ambos tipos y continuidad de derechos y obligaciones."},
        {"clave": "bases_transformacion", "etiqueta": "bases y estatutos", "pregunta": "Indica capital, socios, estatutos y fecha de efectos."},
    ],
    "emision_acciones": [
        {"clave": "serie_clase_acciones", "etiqueta": "serie, clase y derechos", "pregunta": "Indica número, valor nominal, serie, clase y restricciones."},
        {"clave": "precio_suscripcion", "etiqueta": "precio y suscripción", "pregunta": "Indica precio, plazo, forma de pago y derecho de preferencia."},
    ],
    "aprobacion_estados_financieros": [
        {"clave": "ejercicio_estados", "etiqueta": "ejercicio y estados", "pregunta": "Indica periodo, balance, resultados y notas aprobadas."},
        {"clave": "destino_utilidades", "etiqueta": "destino de utilidades o pérdidas", "pregunta": "Indica reserva legal, dividendos, pérdidas y saldos."},
    ],
    "asamblea_especial_accionistas": [
        {"clave": "clase_acciones", "etiqueta": "clase o serie afectada", "pregunta": "Indica clase, serie y número de acciones afectadas."},
        {"clave": "derechos_afectados", "etiqueta": "derechos y consentimiento", "pregunta": "Explica cambio de derechos y mayoría especial obtenida."},
    ],
    "sesion_vigilancia_comisarios": [
        {"clave": "organo_vigilancia", "etiqueta": "órgano y responsables", "pregunta": "Indica comisario, comité u órgano previsto en estatutos."},
        {"clave": "informe_vigilancia", "etiqueta": "informe y observaciones", "pregunta": "Resume periodo, hallazgos, recomendaciones y documentos revisados."},
    ],
}

REQUISITOS_COMUNES_ACTA = [
    {"clave": "base_estatutaria", "etiqueta": "base estatutaria y órgano competente", "pregunta": "Indica cláusula estatutaria y órgano facultado para resolver."},
    {"clave": "formalizacion_prevista", "etiqueta": "formalización y registro previstos", "pregunta": "Indica si requiere protocolización, publicación, inscripción o avisos, sin afirmar que ya se realizaron."},
]

def requisitos_acta(tipo_acta: str, tipo_sociedad: str | None = None) -> List[Dict[str, str]]:
    """Devuelve los datos jurídicos que deben capturarse para un acta concreta."""
    requisitos = list(REQUISITOS_ACTA.get(tipo_acta, [])) + list(REQUISITOS_COMUNES_ACTA)
    if tipo_sociedad in {TipoSociedad.COOPERATIVA.value, TipoSociedad.SCIVIL.value}:
        requisitos.append({
            "clave": "regimen_especial",
            "etiqueta": "régimen especial aplicable",
            "pregunta": "Indica la cláusula del contrato social o la disposición especial de la LGSC o Código Civil aplicable.",
        })
    return requisitos

ACTA_MATERIA: Dict[str, MateriaAcuerdo] = {
    TipoAsamblea.CONSTITUTIVA.value: MateriaAcuerdo.CONSTITUCION,
    TipoAsamblea.AUMENTO_CAPITAL.value: MateriaAcuerdo.AUMENTO_CAPITAL,
    TipoAsamblea.REDUCCION_CAPITAL.value: MateriaAcuerdo.REDUCCION_CAPITAL,
    TipoAsamblea.FUSION.value: MateriaAcuerdo.FUSION,
    TipoAsamblea.ESCISION.value: MateriaAcuerdo.ESCISION,
    TipoAsamblea.DISOLUCION_LIQUIDACION.value: MateriaAcuerdo.DISOLUCION_LIQUIDACION,
    TipoAsamblea.SESION_CONSEJO.value: MateriaAcuerdo.INFORME_CONSEJO,
    TipoAsamblea.MODIFICACION_ESTATUTOS.value: MateriaAcuerdo.MODIFICACION_ESTATUTOS,
    TipoAsamblea.NOMBRAMIENTO_ADMINISTRADOR.value: MateriaAcuerdo.NOMBRAMIENTO_ADMINISTRADORES,
    TipoAsamblea.REMOCION_ADMINISTRADOR.value: MateriaAcuerdo.REMOCION_ADMINISTRADORES,
    TipoAsamblea.OTORGAMIENTO_PODERES.value: MateriaAcuerdo.OTORGAMIENTO_PODERES,
    TipoAsamblea.REVOCACION_PODERES.value: MateriaAcuerdo.REVOCACION_PODERES,
    TipoAsamblea.TRANSMISION_ACCIONES.value: MateriaAcuerdo.TRANSMISION_ACCIONES,
    TipoAsamblea.CESION_PARTES_SOCIALES.value: MateriaAcuerdo.CESION_PARTES_SOCIALES,
    TipoAsamblea.ADMISION_NUEVOS_SOCIOS.value: MateriaAcuerdo.ADMISION_NUEVOS_SOCIOS,
    TipoAsamblea.SEPARACION_EXCLUSION_SOCIOS.value: MateriaAcuerdo.SEPARACION_EXCLUSION_SOCIOS,
    TipoAsamblea.NOMBRAMIENTO_LIQUIDADORES.value: MateriaAcuerdo.NOMBRAMIENTO_LIQUIDADORES,
    TipoAsamblea.APROBACION_BALANCE_LIQUIDACION.value: MateriaAcuerdo.APROBACION_BALANCE_LIQUIDACION,
    TipoAsamblea.TRANSFORMACION_SOCIEDAD.value: MateriaAcuerdo.TRANSFORMACION_SOCIEDAD,
    TipoAsamblea.EMISION_ACCIONES.value: MateriaAcuerdo.EMISION_ACCIONES,
    TipoAsamblea.APROBACION_ESTADOS_FINANCIEROS.value: MateriaAcuerdo.APROBACION_ESTADOS_FINANCIEROS,
    TipoAsamblea.ASAMBLEA_ESPECIAL_ACCIONISTAS.value: MateriaAcuerdo.ASAMBLEA_ESPECIAL_ACCIONISTAS,
    TipoAsamblea.SESION_VIGILANCIA_COMISARIOS.value: MateriaAcuerdo.SESION_VIGILANCIA_COMISARIOS,
}

_ACTAS_ACCIONES = {
    TipoAsamblea.TRANSMISION_ACCIONES.value,
    TipoAsamblea.EMISION_ACCIONES.value,
    TipoAsamblea.ASAMBLEA_ESPECIAL_ACCIONISTAS.value,
}
_ACTAS_PARTES_SOCIALES = {
    TipoAsamblea.CESION_PARTES_SOCIALES.value,
}
_ACTAS_CONSEJO = {TipoAsamblea.SESION_CONSEJO.value}
_ACTAS_LGSM_COMUNES = {
    tipo.value for tipo, _, _ in _ACTA_ITEMS
} - _ACTAS_ACCIONES - _ACTAS_PARTES_SOCIALES
_ACTAS_POR_SOCIEDAD: Dict[str, set[str]] = {
    TipoSociedad.SRL.value: _ACTAS_LGSM_COMUNES | _ACTAS_PARTES_SOCIALES,
    TipoSociedad.SRL_CV.value: _ACTAS_LGSM_COMUNES | _ACTAS_PARTES_SOCIALES,
    TipoSociedad.SCS.value: _ACTAS_LGSM_COMUNES | _ACTAS_PARTES_SOCIALES,
    TipoSociedad.SNC.value: _ACTAS_LGSM_COMUNES | _ACTAS_PARTES_SOCIALES,
    TipoSociedad.COOPERATIVA.value: {
        TipoAsamblea.CONSTITUTIVA.value,
        TipoAsamblea.ORDINARIA.value,
        TipoAsamblea.EXTRAORDINARIA.value,
        TipoAsamblea.MIXTA.value,
        TipoAsamblea.DISOLUCION_LIQUIDACION.value,
        TipoAsamblea.MODIFICACION_ESTATUTOS.value,
        TipoAsamblea.NOMBRAMIENTO_ADMINISTRADOR.value,
        TipoAsamblea.REMOCION_ADMINISTRADOR.value,
        TipoAsamblea.ADMISION_NUEVOS_SOCIOS.value,
        TipoAsamblea.SEPARACION_EXCLUSION_SOCIOS.value,
        TipoAsamblea.NOMBRAMIENTO_LIQUIDADORES.value,
        TipoAsamblea.APROBACION_BALANCE_LIQUIDACION.value,
        TipoAsamblea.APROBACION_ESTADOS_FINANCIEROS.value,
    },
    TipoSociedad.SCIVIL.value: {
        TipoAsamblea.CONSTITUTIVA.value,
        TipoAsamblea.ORDINARIA.value,
        TipoAsamblea.EXTRAORDINARIA.value,
        TipoAsamblea.MIXTA.value,
        TipoAsamblea.MODIFICACION_ESTATUTOS.value,
        TipoAsamblea.NOMBRAMIENTO_ADMINISTRADOR.value,
        TipoAsamblea.REMOCION_ADMINISTRADOR.value,
        TipoAsamblea.OTORGAMIENTO_PODERES.value,
        TipoAsamblea.REVOCACION_PODERES.value,
        TipoAsamblea.ADMISION_NUEVOS_SOCIOS.value,
        TipoAsamblea.SEPARACION_EXCLUSION_SOCIOS.value,
    },
}
for _tipo in (
    TipoSociedad.SA,
    TipoSociedad.SAS,
    TipoSociedad.SCA,
    TipoSociedad.SA_CV,
    TipoSociedad.SAPI,
    TipoSociedad.SAPI_CV,
    TipoSociedad.SAB,
):
    _ACTAS_POR_SOCIEDAD.setdefault(_tipo.value, _ACTAS_LGSM_COMUNES | _ACTAS_ACCIONES)


def acta_aplicable(tipo_sociedad: str | None, tipo_acta: str) -> bool:
    """Indica si el catálogo permite el acta para la sociedad seleccionada."""
    if not tipo_sociedad:
        return True
    return tipo_acta in _ACTAS_POR_SOCIEDAD.get(str(getattr(tipo_sociedad, "value", tipo_sociedad)), set())


def ordenamiento_sociedad(tipo_sociedad: str | None) -> str:
    """Devuelve el marco principal del tipo societario."""
    valor = str(getattr(tipo_sociedad, "value", tipo_sociedad or ""))
    for item in TIPOS_SOCIEDAD:
        if item["valor"] == valor:
            return str(item["ordenamiento"])
    return "Legislación aplicable y estatutos sociales"

# ---------------------------------------------------------------------------
# Tipos de asamblea: valor técnico -> etiqueta, descripción y fundamento
# ---------------------------------------------------------------------------
TIPOS_ASAMBLEA: List[Dict[str, Any]] = [
    {
        "valor": TipoAsamblea.CONSTITUTIVA.value,
        "etiqueta": "Asamblea Constitutiva",
        "descripcion": "Aprobación de la escritura social, suscripción del capital y estatutos iniciales.",
        "articulos": ["Art. 5º LGSM", "Art. 6º LGSM"],
    },
    {
        "valor": TipoAsamblea.ORDINARIA.value,
        "etiqueta": "Asamblea General Ordinaria",
        "descripcion": "Nombramientos, informes, estados financieros y asuntos que no requieren reforma estatutaria.",
        "articulos": ["Art. 178 LGSM", "Art. 181 LGSM", "Art. 189 LGSM"],
    },
    {
        "valor": TipoAsamblea.EXTRAORDINARIA.value,
        "etiqueta": "Asamblea General Extraordinaria",
        "descripcion": "Modificación del contrato social, aumento o reducción de capital, fusión, disolución y demás supuestos del artículo 182.",
        "articulos": ["Art. 182 LGSM", "Art. 190 LGSM"],
    },
    {
        "valor": TipoAsamblea.MIXTA.value,
        "etiqueta": "Asamblea General Mixta",
        "descripcion": "Celebración conjunta de asuntos ordinarios y extraordinarios en la misma sesión.",
        "articulos": ["Art. 178 LGSM", "Art. 182 LGSM"],
    },
    {
        "valor": TipoAsamblea.AUMENTO_CAPITAL.value,
        "etiqueta": "Aumento de Capital Social",
        "descripcion": "Suscripción de nuevas acciones, capitalización de pasivos o primas de acciones.",
        "articulos": ["Art. 182 LGSM", "Art. 189 LGSM", "Art. 190 LGSM", "Art. 209 LGSM"],
    },
    {
        "valor": TipoAsamblea.REDUCCION_CAPITAL.value,
        "etiqueta": "Reducción de Capital Social",
        "descripcion": "Reembolso de aportaciones o amortización de acciones con las consecuencias del artículo 135.",
        "articulos": ["Art. 134 LGSM", "Art. 135 LGSM", "Art. 182 LGSM"],
    },
    {
        "valor": TipoAsamblea.FUSION.value,
        "etiqueta": "Fusión",
        "descripcion": "Incorporación o integración de sociedades conforme a las bases aprobadas por las asambleas.",
        "articulos": ["Art. 222 LGSM", "Art. 223 LGSM", "Art. 224 LGSM"],
    },
    {
        "valor": TipoAsamblea.ESCISION.value,
        "etiqueta": "Escisión",
        "descripcion": "División del patrimonio social en dos o más sociedades.",
        "articulos": ["Art. 228 bis LGSM"],
    },
    {
        "valor": TipoAsamblea.DISOLUCION_LIQUIDACION.value,
        "etiqueta": "Disolución y Liquidación",
        "descripcion": "Acuerdos de disolución anticipada y nombramiento de liquidadores.",
        "articulos": ["Art. 229 LGSM", "Art. 230 LGSM", "Art. 249 LGSM"],
    },
    {
        "valor": TipoAsamblea.SESION_CONSEJO.value,
        "etiqueta": "Sesión del Consejo de Administración",
        "descripcion": "Actas de consejo (no de asamblea de accionistas) con base en los estatutos sociales.",
        "articulos": ["Estatutos sociales", "Art. 158 LGSM"],
    },
]

_VALORES_ASAMBLEA_DETALLADOS = {item["valor"] for item in TIPOS_ASAMBLEA}
TIPOS_ASAMBLEA.extend(
    {
        **item,
        "articulos": [],
    }
    for item in ACTAS_CORPORATIVAS
    if item["valor"] not in _VALORES_ASAMBLEA_DETALLADOS
)

# ---------------------------------------------------------------------------
# Tipos de mayoría
# ---------------------------------------------------------------------------
TIPOS_MAYORIA: List[Dict[str, Any]] = [
    {
        "valor": TipoMayoria.UNANIMIDAD.value,
        "etiqueta": "Unanimidad",
        "descripcion": "Voto favorable de la totalidad del capital representado en la asamblea.",
        "porcentaje_requerido": 100.0,
    },
    {
        "valor": TipoMayoria.MAYORIA_CALIFICADA.value,
        "etiqueta": "Mayoría calificada (75%)",
        "descripcion": "Tres cuartas partes del capital representado, según lo previsto por los estatutos sociales.",
        "porcentaje_requerido": 75.0,
    },
    {
        "valor": TipoMayoria.MAYORIA_ESPECIAL.value,
        "etiqueta": "Mayoría especial (dos terceras partes)",
        "descripcion": "Dos terceras partes del capital representado, cuando los estatutos lo exijan.",
        "porcentaje_requerido": 66.67,
    },
    {
        "valor": TipoMayoria.MAYORIA_SIMPLE.value,
        "etiqueta": "Mayoría simple (50% + 1)",
        "descripcion": "Más de la mitad de las acciones representadas con derecho a voto.",
        "porcentaje_requerido": 50.0,
    },
    {
        "valor": TipoMayoria.SIN_VOTACION.value,
        "etiqueta": "Sin votación (informativo)",
        "descripcion": "Asunto que solo se hace constar en el acta y no se somete a votación.",
        "porcentaje_requerido": None,
    },
]

# ---------------------------------------------------------------------------
# Carácter de cada asistente
# ---------------------------------------------------------------------------
CARACTERES_ASISTENTE: List[Dict[str, Any]] = [
    {"valor": CaracterAsistente.PRESIDENTE.value, "etiqueta": "Presidente de la asamblea"},
    {"valor": CaracterAsistente.SECRETARIO.value, "etiqueta": "Secretario de la asamblea"},
    {"valor": CaracterAsistente.ESCRUTADOR.value, "etiqueta": "Escrutador"},
    {"valor": CaracterAsistente.PROPIETARIO.value, "etiqueta": "Accionista propietario"},
    {"valor": CaracterAsistente.SUPLENTE.value, "etiqueta": "Accionista suplente (ad hoc)"},
    {"valor": CaracterAsistente.REPRESENTANTE.value, "etiqueta": "Representante con carta poder"},
    {"valor": CaracterAsistente.COMISARIO.value, "etiqueta": "Comisario"},
    {"valor": CaracterAsistente.INVITADO.value, "etiqueta": "Invitado (sin voz ni voto)"},
]

# ---------------------------------------------------------------------------
# Estatus del ciclo de vida del acta
# ---------------------------------------------------------------------------
ESTATUS_ACTA: List[Dict[str, Any]] = [
    {"valor": EstatusActa.BORRADOR.value, "etiqueta": "Borrador"},
    {"valor": EstatusActa.EN_REVISION.value, "etiqueta": "En revisión"},
    {"valor": EstatusActa.APROBADA.value, "etiqueta": "Aprobada"},
    {"valor": EstatusActa.FIRMADA.value, "etiqueta": "Firmada"},
    {
        "valor": EstatusActa.ARCHIVADA.value,
        "etiqueta": "Archivada (cierre administrativo; no acredita protocolización)",
    },
]

_ETIQUETAS_TIPO_ASAMBLEA: Dict[str, str] = {item["valor"]: item["etiqueta"] for item in TIPOS_ASAMBLEA}
_ETIQUETAS_MAYORIA: Dict[str, str] = {item["valor"]: item["etiqueta"] for item in TIPOS_MAYORIA}
_PORCENTAJE_MAYORIA: Dict[str, float] = {
    item["valor"]: item["porcentaje_requerido"]
    for item in TIPOS_MAYORIA
    if item.get("porcentaje_requerido") is not None
}


def _clave(valor: Any) -> str:
    """Clave de catálogo: admite el valor literal o el miembro de un enum."""
    return str(getattr(valor, "value", valor))


def etiqueta_tipo_asamblea(valor: str) -> str:
    """Etiqueta legible de un tipo de asamblea (tolerante a valores desconocidos)."""
    clave = _clave(valor)
    return _ETIQUETAS_TIPO_ASAMBLEA.get(clave, clave.replace("_", " ").capitalize())


def etiqueta_mayoria(valor: str) -> str:
    """Etiqueta legible de un tipo de mayoría."""
    clave = _clave(valor)
    return _ETIQUETAS_MAYORIA.get(clave, clave.replace("_", " ").capitalize())


def porcentaje_requerido_mayoria(valor: str) -> float | None:
    """Porcentaje de capital exigido por el tipo de mayoría (``None`` si no aplica)."""
    return _PORCENTAJE_MAYORIA.get(_clave(valor))


def articulos_tipo_asamblea(valor: str) -> List[str]:
    """Artículos de referencia del tipo de asamblea (lista vacía si es desconocido)."""
    clave = _clave(valor)
    for item in TIPOS_ASAMBLEA:
        if item["valor"] == clave:
            return list(item.get("articulos") or [])
    return []



def catalogos() -> Dict[str, Any]:
    """Catálogos completos con los que se pueblan los formularios del frontend."""
    return {
        "tipos_sociedad": TIPOS_SOCIEDAD,
        "actas_corporativas": ACTAS_CORPORATIVAS,
        "tipos_asamblea": TIPOS_ASAMBLEA,
        "tipos_mayoria": TIPOS_MAYORIA,
        "caracteres_asistente": CARACTERES_ASISTENTE,
        "estatus_acta": ESTATUS_ACTA,
    }


# ---------------------------------------------------------------------------
# Artículo de la LGSM que rige el quórum de instalación según el tipo de asamblea
# ---------------------------------------------------------------------------
ARTICULO_QUORUM: Dict[str, str] = {
    TipoAsamblea.CONSTITUTIVA.value: "5º y 89",
    TipoAsamblea.ORDINARIA.value: "189",
    TipoAsamblea.MIXTA.value: "189 y 190",
    TipoAsamblea.SESION_CONSEJO.value: "158 y los estatutos sociales",
}


def articulo_quorum(tipo_asamblea: str) -> str:
    """Artículo aplicable al quórum de instalación (por defecto el 190: extraordinarias)."""
    return ARTICULO_QUORUM.get(_clave(tipo_asamblea), "190")



