"""Plantillas legales deterministas (modo sin IA / respaldo de la IA).

Este módulo concentra el conocimiento jurídico-mercantil mexicano utilizado para
redactar cláusulas cuando no hay un proveedor de IA disponible (o cuando éste
falla). Es también la referencia que se envía al LLM como contexto del *prompt*,
de modo que ambas rutas producen documentos homogéneos.

Referencias normativas: Ley General de Sociedades Mercantiles (LGSM).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple

from app.models.enums import MateriaAcuerdo, TipoAsamblea

# Ordinales usados para numerar los párrafos de cada cláusula.
ORDINALES: Tuple[str, ...] = (
    "PRIMERO",
    "SEGUNDO",
    "TERCERO",
    "CUARTO",
    "QUINTO",
    "SEXTO",
    "SÉPTIMO",
    "OCTAVO",
    "NOVENO",
    "DÉCIMO",
)

# Expresión regular para extraer marcadores {clave} de un texto de plantilla.
_PATRON_MARCADOR = re.compile(r"\{(\w+)\}")


@dataclass(frozen=True)
class ParametroPlantilla:
    """Declaración de un parámetro que una plantilla acepta o requiere.

    ``requerido`` indica si el valor debe venir del contexto de entrada;
    cuando es ``False`` y falta el valor, se usa ``valor_predeterminado``.
    """

    nombre: str
    requerido: bool = True
    valor_predeterminado: Optional[str] = None
    descripcion: Optional[str] = None


@dataclass(frozen=True)
class PlantillaLegal:
    """Estructura de la cláusula correspondiente a una materia determinada.

    ``parametros`` declara los marcadores {clave} que la plantilla usa,
    indicando cuáles son obligatorios y cuáles tienen valor por defecto.
    Esto permite validar el contexto antes de renderizar y exponer al
    frontend qué datos debe capturar para cada materia.
    """

    materia: MateriaAcuerdo
    titulo: str
    accion: str
    articulos: Tuple[str, ...]
    parrafos: Tuple[str, ...] = field(default_factory=tuple)
    parametros: Tuple[ParametroPlantilla, ...] = field(default_factory=tuple)

    def parametros_requeridos(self) -> Tuple[str, ...]:
        """Nombres de los parámetros obligatorios (sin valor por defecto o sin clave en el contexto)."""
        return tuple(p.nombre for p in self.parametros if p.requerido)

    def parametros_opcionales(self) -> Tuple[str, ...]:
        """Nombres de los parámetros opcionales (con valor por defecto)."""
        return tuple(p.nombre for p in self.parametros if not p.requerido)

    def valores_por_defecto(self) -> Dict[str, str]:
        """Diccionario de parámetros opcionales con su valor predeterminado."""
        return {
            p.nombre: p.valor_predeterminado or ""
            for p in self.parametros
            if not p.requerido and p.valor_predeterminado is not None
        }

    def marcador_nombres(self) -> Tuple[str, ...]:
        """Todos los nombres de marcadores {clave} que aparecen en los párrafos."""
        nombres: set[str] = set()
        for parrafo in self.parrafos:
            nombres.update(_PATRON_MARCADOR.findall(parrafo))
        return tuple(sorted(nombres))


_P_CAPITAL: Dict[MateriaAcuerdo, PlantillaLegal] = {
    MateriaAcuerdo.CONSTITUCION: PlantillaLegal(
        materia=MateriaAcuerdo.CONSTITUCION,
        titulo="Constitución de la sociedad",
        accion="Se aprueba la constitución de la sociedad y la adopción de sus estatutos sociales",
        articulos=("Art. 5º", "Art. 6º", "Art. 89"),
        parrafos=(
            "Se aprueba por unanimidad la constitución de {sociedad}, sociedad mercantil que se regirá por los estatutos sociales que forman parte de la presente acta y por la Ley General de Sociedades Mercantiles.",
            "Se declara suscrito y pagado el capital social conforme al artículo 89 de la Ley General de Sociedades Mercantiles, quedando las acciones debidamente suscritas por los accionistas fundadores en la proporción que se hace constar en la tabla de suscripción.",
            "Se designan como administradores y comisario a las personas señaladas en el punto correspondiente del orden del día, quienes aceptan sus cargos en este acto.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.AUMENTO_CAPITAL: PlantillaLegal(
        materia=MateriaAcuerdo.AUMENTO_CAPITAL,
        titulo="Aumento del capital social",
        accion="Se aprueba el aumento del capital social y la reforma de la cláusula relativa al capital",
        articulos=("Art. 182, fracción II", "Art. 132", "Art. 209"),
        parrafos=(
            "Se aprueba el aumento del capital social de {sociedad} en la cantidad de {monto}, quedando el capital social resultante en {capital}, con la emisión de las acciones que correspondan.",
            "Las acciones emitidas se ofrecerán a los accionistas en proporción a su tenencia accionaria, respetando el derecho de preferencia que concede el artículo 132 de la Ley General de Sociedades Mercantiles.",
            "Se aprueba la reforma del contrato social en la cláusula relativa al capital social y a las acciones representativas, en los términos del proyecto que se tiene a la vista.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
            ParametroPlantilla("monto", requerido=True, descripcion="Monto del aumento de capital"),
            ParametroPlantilla("capital", requerido=True, descripcion="Capital social resultante tras el aumento"),
        ),
    ),
    MateriaAcuerdo.REDUCCION_CAPITAL: PlantillaLegal(
        materia=MateriaAcuerdo.REDUCCION_CAPITAL,
        titulo="Reducción del capital social",
        accion="Se aprueba la reducción del capital social y la reforma estatutaria correspondiente",
        articulos=("Art. 134", "Art. 135", "Art. 182, fracción II"),
        parrafos=(
            "Se aprueba la reducción del capital social de {sociedad} en la cantidad de {monto}, mediante reembolso a los accionistas o amortización de acciones, quedando el capital resultante en {capital}.",
            "Se hace constar que la reducción se realiza con la responsabilidad solidaria prevista por el artículo 135 de la Ley General de Sociedades Mercantiles a cargo de los accionistas beneficiados, por el término de cinco años.",
            "Se aprueba la reforma del contrato social en las cláusulas relativas al capital social y a las acciones en circulación.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
            ParametroPlantilla("monto", requerido=True, descripcion="Monto de la reducción de capital"),
            ParametroPlantilla("capital", requerido=True, descripcion="Capital social resultante tras la reducción"),
        ),
    ),
}

_P_ADMIN_Y_FINANZAS: Dict[MateriaAcuerdo, PlantillaLegal] = {
    MateriaAcuerdo.NOMBRAMIENTO_ADMINISTRADORES: PlantillaLegal(
        materia=MateriaAcuerdo.NOMBRAMIENTO_ADMINISTRADORES,
        titulo="Nombramiento de administradores",
        accion="Se aprueba el nombramiento de los administradores de la sociedad",
        articulos=("Art. 154", "Art. 156", "Art. 181"),
        parrafos=(
            "Se aprueba el nombramiento de los administradores de {sociedad} por el periodo estatutario correspondiente, quienes deberán otorgar la garantía que en su caso exijan los estatutos sociales.",
            "Los nombramientos se realizan con base en el artículo 154 de la Ley General de Sociedades Mercantiles y con la aceptación expresa de los designados, cuyos datos se hacen constar en la presente acta.",
            "Se instruye a los administradores designados para que procedan a la aceptación y, en su caso, inscripción de sus nombramientos conforme a derecho.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.REMOCION_ADMINISTRADORES: PlantillaLegal(
        materia=MateriaAcuerdo.REMOCION_ADMINISTRADORES,
        titulo="Revocación de administradores",
        accion="Se aprueba la revocación del nombramiento de los administradores vigentes",
        articulos=("Art. 155", "Art. 181"),
        parrafos=(
            "Se aprueba la revocación del nombramiento de los administradores de {sociedad} designados con anterioridad, dejando a salvo los derechos que pudieran corresponderles conforme a la ley o a los estatutos sociales.",
            "Se faculta a quien corresponda para realizar las anotaciones, avisos y publicaciones que la revocación requiera ante las autoridades y registros aplicables.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.APROBACION_ESTADOS_FINANCIEROS: PlantillaLegal(
        materia=MateriaAcuerdo.APROBACION_ESTADOS_FINANCIEROS,
        titulo="Aprobación de estados financieros y resultado del ejercicio",
        accion="Se aprueban los estados financieros y el resultado del ejercicio social concluido",
        articulos=("Art. 172", "Art. 176", "Art. 177"),
        parrafos=(
            "Se aprueban los estados financieros de {sociedad} y el informe del comisario correspondientes al ejercicio social concluido, documentos que fueron puestos a disposición de los accionistas con la anticipación prevista por los estatutos sociales.",
            "Se aprueba la aplicación del resultado del ejercicio en los términos propuestos por el órgano de administración, previa integración de la reserva legal a que se refiere el artículo 20 de la Ley General de Sociedades Mercantiles.",
            "Se hace constar que el informe del comisario se dio a conocer a la asamblea y que el mismo no contiene salvedades que impidan la aprobación de los estados financieros.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.DISTRIBUCION_DIVIDENDOS: PlantillaLegal(
        materia=MateriaAcuerdo.DISTRIBUCION_DIVIDENDOS,
        titulo="Decreto y pago de dividendos",
        accion="Se decreta el pago de dividendos a cargo de las utilidades acumuladas de la sociedad",
        articulos=("Art. 19", "Art. 20", "Art. 113"),
        parrafos=(
            "Se decreta el pago de dividendos a cargo de las utilidades acumuladas de {sociedad}, una vez integrada la reserva legal prevista por el artículo 20 de la Ley General de Sociedades Mercantiles y el proyecto presentado por el órgano de administración.",
            "El pago se realizará a los accionistas con derecho, en proporción al número de acciones de que sean titulares, en la fecha, forma y medio de pago que se hacen constar en la presente acta.",
            "Se faculta al órgano de administración para ejecutar las medidas necesarias para el pago, incluyendo la retención y entero de las contribuciones que correspondan.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
}

_P_SOCIETARIAS: Dict[MateriaAcuerdo, PlantillaLegal] = {
    MateriaAcuerdo.REFORMA_ESTATUTOS: PlantillaLegal(
        materia=MateriaAcuerdo.REFORMA_ESTATUTOS,
        titulo="Reforma de los estatutos sociales",
        accion="Se aprueba la reforma del contrato social y de los estatutos sociales",
        articulos=("Art. 182, fracción I", "Art. 183", "Art. 184"),
        parrafos=(
            "Se aprueba la reforma del contrato social de {sociedad} en los términos del proyecto de estatutos que se tiene a la vista y que, firmado por la mesa directiva, forma parte integrante de la presente acta.",
            "La reforma cumple con los requisitos de forma y contenido previstos por el artículo 182 de la Ley General de Sociedades Mercantiles y será publicada e inscrita conforme a las disposiciones aplicables.",
            "Se instruye a los delegados especiales designados para que otorguen la escritura pública correspondiente y realicen su inscripción en el Registro Público de Comercio.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.CAMBIO_DOMICILIO: PlantillaLegal(
        materia=MateriaAcuerdo.CAMBIO_DOMICILIO,
        titulo="Cambio del domicilio social",
        accion="Se aprueba el cambio del domicilio social de la sociedad",
        articulos=("Art. 182, fracción V", "Art. 184"),
        parrafos=(
            "Se aprueba el cambio del domicilio social de {sociedad} al que se precisa en el proyecto de reforma estatutaria que forma parte de esta acta, considerándose por tanto reformada la cláusula relativa al domicilio.",
            "Se faculta a los delegados especiales para que realicen los avisos, publicaciones e inscripciones que el cambio de domicilio requiera ante las autoridades fiscales, registrales y de cualquier otra índole.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.FUSION: PlantillaLegal(
        materia=MateriaAcuerdo.FUSION,
        titulo="Fusión de sociedades",
        accion="Se aprueba la fusión de la sociedad en los términos del proyecto de fusión presentado",
        articulos=("Art. 222", "Art. 223", "Art. 224", "Art. 225"),
        parrafos=(
            "Se aprueba la fusión de {sociedad} con las sociedades que se identifican en el proyecto de fusión, en el carácter de sociedad fusionante o fusionada que en el mismo se precisa, así como los estatutos de la sociedad que subsista o que se constituya.",
            "Se aprueban como bases de la fusión el balance general, el proyecto de estatutos y los demás documentos que se tienen a la vista; el acuerdo se publicará en el sistema electrónico previsto por el artículo 223 de la Ley General de Sociedades Mercantiles.",
            "Los accionistas disidentes podrán ejercer el derecho de separación que les concede el artículo 225 de la Ley General de Sociedades Mercantiles, dentro de los quince días siguientes a la fecha de la asamblea.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.ESCISION: PlantillaLegal(
        materia=MateriaAcuerdo.ESCISION,
        titulo="Escisión de la sociedad",
        accion="Se aprueba la escisión de la sociedad y el proyecto de escisión presentado",
        articulos=("Art. 228 bis"),
        parrafos=(
            "Se aprueba la escisión de {sociedad} con la constitución de la sociedad o sociedades escindidas y la asignación del patrimonio que se precisa en el proyecto aprobado, conforme al artículo 228 bis de la Ley General de Sociedades Mercantiles.",
            "La asamblea de la sociedad escindente y los órganos de gobierno de la escindida aprueban los estados financieros y el proyecto de escisión que servirán de base para el acta de escisión, así como los estatutos sociales de la sociedad beneficiaria.",
            "Se designan representantes para formalizar la escisión mediante escritura pública e inscribirla en el Registro Público de Comercio.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.DISOLUCION_LIQUIDACION: PlantillaLegal(
        materia=MateriaAcuerdo.DISOLUCION_LIQUIDACION,
        titulo="Disolución y liquidación de la sociedad",
        accion="Se aprueba la disolución anticipada de la sociedad",
        articulos=("Art. 229", "Art. 230", "Art. 232", "Art. 247"),
        parrafos=(
            "Se aprueba la disolución anticipada de {sociedad} y, en su caso, la designación de los liquidadores por el periodo que la asamblea determine, de conformidad con el artículo 229 de la Ley General de Sociedades Mercantiles.",
            "Los liquidadores deberán protocolizar la disolución e inscribirla en el Registro Público de Comercio, practicar el balance final de liquidación y distribuir el haber social conforme a los artículos 242 a 247 de la Ley General de Sociedades Mercantiles.",
            "Se instruye a los liquidadores para que realicen la publicación del balance final y las demás publicaciones que la ley exige.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
}

_P_OTRAS: Dict[MateriaAcuerdo, PlantillaLegal] = {
    MateriaAcuerdo.EMISION_TITULOS: PlantillaLegal(
        materia=MateriaAcuerdo.EMISION_TITULOS,
        titulo="Emisión de obligaciones o títulos de crédito",
        accion="Se aprueba la emisión de obligaciones o títulos de crédito por la sociedad",
        articulos=("Art. 208", "Art. 209", "Art. 210", "Art. 217"),
        parrafos=(
            "Se aprueba la emisión de obligaciones o títulos de crédito hasta por la cantidad de {monto}, con las bases, garantías, intereses y condiciones que se hacen constar en la presente acta, conforme a los artículos 208 a 210 de la Ley General de Sociedades Mercantiles.",
            "Se designa representante común de los tenedores de obligaciones en los términos del artículo 217 de la Ley General de Sociedades Mercantiles, con las facultades que se precisan en el acta de emisión.",
            "Se instruye a los delegados especiales para que formalicen la emisión ante fedatario público y realicen las inscripciones correspondientes.",
        ),
        parametros=(
            ParametroPlantilla("monto", requerido=True, descripcion="Monto de la emisión de obligaciones o títulos de crédito"),
        ),
    ),
    MateriaAcuerdo.DESIGNACION_DELEGADOS: PlantillaLegal(
        materia=MateriaAcuerdo.DESIGNACION_DELEGADOS,
        titulo="Designación de delegados especiales",
        accion="Se designan delegados especiales de la asamblea para el cumplimiento de los acuerdos",
        articulos=("Art. 178", "Art. 181"),
        parrafos=(
            "Se designan como delegados especiales de la asamblea a la o las personas que se identifican en el punto correspondiente del orden del día, para que en nombre y representación de {sociedad} soliciten y realicen todos los actos necesarios para dar cumplimiento a los acuerdos adoptados, incluyendo su protocolización e inscripción.",
            "Los delegados especiales comparecerán ante fedatario público y suscribirán los documentos que correspondan al cumplimiento total o parcial de los acuerdos adoptados por la asamblea.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.INFORME_CONSEJO: PlantillaLegal(
        materia=MateriaAcuerdo.INFORME_CONSEJO,
        titulo="Informes del órgano de administración y del comisario",
        accion="Se tienen por presentados los informes del órgano de administración y del comisario",
        articulos=("Art. 166", "Art. 172", "Art. 173"),
        parrafos=(
            "Se hace constar que el órgano de administración presentó a la asamblea su informe sobre la marcha de {sociedad} y que el comisario hizo constar las observaciones que estimó pertinentes sobre la política de la sociedad y los resultados obtenidos, en términos del artículo 166 de la Ley General de Sociedades Mercantiles.",
            "Los informes quedan a disposición de los accionistas y se tienen por conocidos por la asamblea, quien los hace constar en la presente acta sin que se requiera votación al respecto.",
        ),
        parametros=(
            ParametroPlantilla("sociedad", requerido=True, descripcion="Nombre o razón social de la sociedad"),
        ),
    ),
    MateriaAcuerdo.GENERICA: PlantillaLegal(
        materia=MateriaAcuerdo.GENERICA,
        titulo="Acuerdo de la asamblea",
        accion="Se aprueba el asunto sometido a la consideración de la asamblea",
        articulos=("Art. 178", "Art. 179", "Art. 181"),
        parrafos=(
            "Se aprueba el asunto sometido a la consideración de la asamblea en los términos que a continuación se precisan: {resumen}",
            "El acuerdo se adopta con base en las facultades que la Ley General de Sociedades Mercantiles concede a la asamblea de accionistas y se hace constar con la finalidad de darle plena eficacia jurídica frente a terceros.",
            "Se facultan a los delegados especiales designados, o en su defecto al órgano de administración, para ejecutar y formalizar el presente acuerdo conforme a derecho.",
        ),
        parametros=(
            ParametroPlantilla("resumen", requerido=True, descripcion="Resumen del asunto sometido a consideración de la asamblea"),
        ),
    ),
}

# Diccionario consolidado de plantillas legales disponibles.
PLANTILLAS: Dict[MateriaAcuerdo, PlantillaLegal] = {
    **_P_CAPITAL,
    **_P_ADMIN_Y_FINANZAS,
    **_P_SOCIETARIAS,
    **_P_OTRAS,
}

# ---------------------------------------------------------------------------
# Detección automática de la materia del acuerdo
# ---------------------------------------------------------------------------
# Palabras clave (en minúsculas y sin acentos) que sugieren cada materia.
PALABRAS_CLAVE: Dict[MateriaAcuerdo, Tuple[str, ...]] = {
    MateriaAcuerdo.CONSTITUCION: ("constitucion", "escritura constitutiva", "accionistas fundadores"),
    MateriaAcuerdo.AUMENTO_CAPITAL: (
        "aumento de capital",
        "aumento del capital",
        "suscripcion de acciones",
        "prima de acciones",
        "capitalizacion de pasivos",
        "nuevas acciones",
    ),
    MateriaAcuerdo.REDUCCION_CAPITAL: (
        "reduccion de capital",
        "reduccion del capital",
        "amortizacion de acciones",
        "reembolso de aportaciones",
    ),
    MateriaAcuerdo.NOMBRAMIENTO_ADMINISTRADORES: (
        "nombramiento",
        "designacion de administradores",
        "consejo de administracion",
        "administrador unico",
        "gerente general",
        "apoderados",
    ),
    MateriaAcuerdo.REMOCION_ADMINISTRADORES: (
        "revocacion",
        "remocion",
        "destitucion",
        "separacion del cargo",
    ),
    MateriaAcuerdo.APROBACION_ESTADOS_FINANCIEROS: (
        "estados financieros",
        "balance general",
        "resultado del ejercicio",
        "ejercicio social",
        "informe del comisario",
        "dictamen",
    ),
    MateriaAcuerdo.DISTRIBUCION_DIVIDENDOS: ("dividendo", "utilidades", "reparto de utilidades"),
    MateriaAcuerdo.REFORMA_ESTATUTOS: (
        "reforma de estatutos",
        "reforma estatutaria",
        "reforma del contrato social",
        "modificacion de estatutos",
        "objeto social",
        "denominacion social",
    ),
    MateriaAcuerdo.CAMBIO_DOMICILIO: ("cambio de domicilio", "nuevo domicilio", "domicilio social"),
    MateriaAcuerdo.FUSION: ("fusion", "sociedad fusionante", "sociedad fusionada"),
    MateriaAcuerdo.ESCISION: ("escision", "escindente", "escindida"),
    MateriaAcuerdo.DISOLUCION_LIQUIDACION: (
        "disolucion",
        "liquidacion",
        "liquidadores",
        "balance final",
    ),
    MateriaAcuerdo.EMISION_TITULOS: (
        "emision de obligaciones",
        "obligaciones",
        "titulos de credito",
        "debentures",
        "representante comun",
    ),
    MateriaAcuerdo.DESIGNACION_DELEGADOS: (
        "delegados especiales",
        "delegado especial",
        "protocolizacion",
        "comparezcan ante notario",
    ),
    MateriaAcuerdo.INFORME_CONSEJO: ("informe", "informes", "marcha de la sociedad"),
}

# Materias que se presuponen por el tipo de asamblea seleccionado.
_MATERIA_POR_TIPO: Dict[str, MateriaAcuerdo] = {
    TipoAsamblea.CONSTITUTIVA.value: MateriaAcuerdo.CONSTITUCION,
    TipoAsamblea.AUMENTO_CAPITAL.value: MateriaAcuerdo.AUMENTO_CAPITAL,
    TipoAsamblea.REDUCCION_CAPITAL.value: MateriaAcuerdo.REDUCCION_CAPITAL,
    TipoAsamblea.FUSION.value: MateriaAcuerdo.FUSION,
    TipoAsamblea.ESCISION.value: MateriaAcuerdo.ESCISION,
    TipoAsamblea.DISOLUCION_LIQUIDACION.value: MateriaAcuerdo.DISOLUCION_LIQUIDACION,
}


def _normalizar(texto: str) -> str:
    """Minúsculas y sin acentos, para comparar palabras clave de forma robusta."""
    if not texto:
        return ""
    descompuesto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))


def detectar_materia(texto: str, tipo_asamblea: Optional[str] = None) -> MateriaAcuerdo:
    """Determina la materia del acuerdo a partir de su redacción y del tipo de asamblea.

    Estrategia: se cuentan coincidencias de palabras clave; el tipo de asamblea
    actúa como desempate/presunción cuando no hay coincidencias concluyentes.
    """
    normalizado = _normalizar(texto)
    puntajes: Dict[MateriaAcuerdo, int] = {
        materia: sum(1 for palabra in palabras if palabra in normalizado)
        for materia, palabras in PALABRAS_CLAVE.items()
    }

    mejor = max(puntajes, key=lambda materia: puntajes[materia])
    clave_tipo = str(getattr(tipo_asamblea, "value", tipo_asamblea))
    presuncion = _MATERIA_POR_TIPO.get(clave_tipo)

    # Si la materia presumida por el tipo de asamblea tiene respaldo textual, se prefiere.
    if presuncion and puntajes.get(presuncion, 0) > 0:
        return presuncion
    if puntajes.get(mejor, 0) > 0:
        return mejor
    return presuncion or MateriaAcuerdo.GENERICA


def obtener_plantilla(materia: Optional[MateriaAcuerdo | str]) -> PlantillaLegal:
    """Devuelve la plantilla de una materia (o la genérica si no existe)."""
    if isinstance(materia, str):
        try:
            materia = MateriaAcuerdo(materia)
        except ValueError:
            materia = MateriaAcuerdo.GENERICA
    return PLANTILLAS.get(materia, PLANTILLAS[MateriaAcuerdo.GENERICA])


class _ContextoSeguro(dict):
    """Diccionario de formato tolerante: las claves ausentes se resuelven a texto vacío."""

    def __missing__(self, clave: str) -> str:  # pragma: no cover - defensivo
        return ""


def plantillas_para_prompt() -> List[str]:
    """Resumen textual de las plantillas, usado como contexto del *prompt* de IA."""
    return [
        f"- {plantilla.titulo}: {plantilla.accion} (fundamento: {', '.join(plantilla.articulos)})."
        for plantilla in PLANTILLAS.values()
    ]

# ---------------------------------------------------------------------------
# Redacción determinista de una cláusula
# ---------------------------------------------------------------------------
class DatosPlantillaIncompletosError(Exception):
    """Se lanza cuando faltan parámetros requeridos para renderizar una plantilla."""


def obtener_parametros_plantilla(materia: MateriaAcuerdo | str) -> List[Dict[str, Any]]:
    """Devuelve la declaración de parámetros de una plantilla, útil para que el
    frontend sepa qué campos debe capturar al usuario.

    Cada entrada tiene: ``nombre``, ``requerido``, ``valor_predeterminado``,
    ``descripcion``.
    """
    plantilla = obtener_plantilla(materia)
    return [
        {
            "nombre": p.nombre,
            "requerido": p.requerido,
            "valor_predeterminado": p.valor_predeterminado,
            "descripcion": p.descripcion,
        }
        for p in plantilla.parametros
    ]


def parametros_requeridos_por_materia() -> Dict[str, List[str]]:
    """Devuelve, para cada materia, la lista de nombres de parámetros requeridos."""
    return {
        materia.value: list(plantilla.parametros_requeridos())
        for materia, plantilla in PLANTILLAS.items()
    }


def redactar_con_plantilla(
    materia: Optional[MateriaAcuerdo | str],
    contexto: Mapping[str, str],
) -> Dict[str, str]:
    """Redacta la cláusula legal de un acuerdo usando la plantilla de su materia.

    Valida que los parámetros requeridos estén presentes en el contexto,
    aplica valores por defecto a los opcionales y sustituye los marcadores
    ``{clave}`` de los párrafos.

    Devuelve un diccionario con ``clausula_legal``, ``fundamento_legal``,
    ``materia`` y ``titulo`` listo para poblar el modelo ``Acuerdo``.
    """

    plantilla = obtener_plantilla(materia)

    # Validamos parámetros requeridos faltantes.
    faltantes: List[str] = []
    for nombre in plantilla.parametros_requeridos():
        if nombre not in contexto or contexto[nombre] is None or str(contexto[nombre]).strip() == "":
            faltantes.append(nombre)
    if faltantes:
        raise DatosPlantillaIncompletosError(
            f"Faltan parámetros requeridos para la plantilla de {materia}: {', '.join(faltantes)}"
        )

    # Construimos el contexto de valores: defaults primero, luego el contexto del usuario.
    valores: Dict[str, str] = {}
    valores.update(plantilla.valores_por_defecto())
    for clave in plantilla.marcador_nombres():
        if clave in contexto:
            valores[clave] = str(contexto[clave])

    parrafos: List[str] = []
    resumen = (contexto.get("resumen") or "").strip()
    if resumen:
        parrafos.append(f"Se tiene por reproducido el asunto en los siguientes términos: {resumen}")
    parrafos.extend(parrafo.format_map(valores) for parrafo in plantilla.parrafos)

    cuerpo = "\n".join(
        f"{ORDINALES[indice] if indice < len(ORDINALES) else f'({indice + 1})'}.- {parrafo}"
        for indice, parrafo in enumerate(parrafos)
    )

    votacion = (
        f"\nAsimismo, se hace constar que el presente acuerdo fue aprobado por {valores.get('mayoria') or 'la mayoría aplicable'} "
        f"de las acciones representadas, computándose {valores.get('acciones') or 'la totalidad de las acciones presentes'}."
    )

    return {
        "materia": plantilla.materia.value,
        "titulo": plantilla.titulo,
        "clausula_legal": f"{cuerpo}{votacion}",
        "fundamento_legal": ", ".join(plantilla.articulos)
        + " de la Ley General de Sociedades Mercantiles",
    }


# ---------------------------------------------------------------------------
# Textos fijos que integran el cuerpo del acta
# ---------------------------------------------------------------------------
TEXTOS_FIJOS: Dict[str, str] = {
    "encabezado": (
        "En {lugar}, siendo las {hora} del día {fecha_larga}, se reunieron los accionistas de "
        "{sociedad} que al final de la presente acta se identifican, con el objeto de celebrar "
        "{tipo_asamblea_texto}, previamente convocada por {quien_convoca} mediante "
        "{medio_convocatoria} de fecha {fecha_convocatoria}."
    ),
    "declaracion_quorum": (
        "El Presidente de la asamblea declaró que se encontraban representadas {acciones_presentes} "
        "acciones, equivalentes al {quorum}% del capital social de la sociedad, por lo que existe "
        "quórum legal para que la asamblea sesione y delibere válidamente en términos del artículo "
        "{articulo_quorum} de la Ley General de Sociedades Mercantiles y de los estatutos sociales."
    ),
    "declaracion_instalacion": (
        "Acto seguido, se procedió a la instalación formal de la asamblea y se aprobó por unanimidad "
        "el orden del día que previamente se dio a conocer a los accionistas, el cual se transcribe "
        "en el punto correspondiente de la presente acta."
    ),
    "cierre": (
        "No habiendo otro asunto que tratar, el Presidente dio por terminada la asamblea y se "
        "levantó la presente acta, que firman los asistentes que en la hoja de firmas se indican, "
        "haciéndose constar que los acuerdos se tienen por aprobados en los términos precisados y "
        "que la misma se protocolizará ante fedatario público para su inscripción en el Registro "
        "Público de Comercio cuando así proceda."
    ),
    "declaracion_protocolizacion": (
        "Se faculta a los delegados especiales de la asamblea, así como al órgano de administración "
        "y a las personas que acrediten representación suficiente, para ejecutar los acuerdos "
        "contenidos en la presente acta, otorgar las escrituras públicas y realizar las "
        "publicaciones, avisos e inscripciones que conforme a derecho procedan."
    ),
}


def formatear(texto: str, contexto: Mapping[str, str]) -> str:
    """Aplica los valores del contexto a un texto con marcadores ``{clave}``.

    Las claves ausentes se sustituyen por texto vacío en lugar de provocar error,
    lo que mantiene la redacción robusta ante contextos incompletos.
    """
    return texto.format_map(_ContextoSeguro(contexto))






