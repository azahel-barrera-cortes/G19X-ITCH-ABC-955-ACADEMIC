"""Generación determinista del PDF del acta con ReportLab.

Responsabilidad única: **maquetar** un documento legal formal a partir de un
diccionario ya validado (datos + texto legal redactado previamente por la IA o por
las plantillas locales). Aquí no se llama a ningún servicio de IA ni se accede a
la base de datos, lo que garantiza que el renderizado sea reproducible.

Contrato de datos aceptado por :func:`build_acta_pdf`
-----------------------------------------------------
``folio``, ``sociedad``, ``rfc_sociedad``, ``tipo_asamblea_texto``, ``titulo``,
``fecha_texto``, ``hora_texto``, ``lugar``, ``convocatoria_texto``,
``capital_social_texto``, ``capital_presente_texto``, ``acciones_totales_texto``,
``quorum_texto``, ``presidente``, ``secretario``, ``observaciones``,
``asistentes`` (``nombre``, ``caracter``, ``cargo``, ``acciones``, ``porcentaje``,
``firma``), ``orden_del_dia`` (``numero``, ``titulo``, ``descripcion``),
``acuerdos`` (``numero``, ``titulo``, ``clausula_legal``, ``fundamento_legal``,
``materia``, ``votacion_texto``, ``mayoria_texto``, ``aprobado``), ``clausulas``
(``encabezado``, ``declaracion_quorum``, ``declaracion_instalacion``, ``cuerpo``,
``cierre``, ``declaracion_protocolizacion``), ``validacion`` (``puntaje``,
``consistencia``, ``hallazgos``, ``recomendaciones``, ``proveedor``),
``opciones`` (``incluir_tabla_asistentes``, ``incluir_hoja_firmas``,
``incluir_anexo_validacion``, ``numerar_paginas``), ``meta`` (``generado_en``,
``proveedor_ia``, ``estatus``, ``version``), ``pie_confidencialidad`` y
``margen_cm``.
"""

from __future__ import annotations

import io
import logging
import re
import unicodedata
from functools import partial
from typing import Any, Dict, List, Mapping, Optional, Sequence
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as lienzo
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# --- Identidad y tipografía del documento -----------------------------------
TITULO_SISTEMA = "PGAC"
SUBTITULO_SISTEMA = "Página de Gestión de Actas Corporativas"
FUENTE_BASE = "Helvetica"
FUENTE_NEGRITA = "Helvetica-Bold"
FUENTE_CURSIVA = "Helvetica-Oblique"

COLOR_TITULO = colors.HexColor("#12213A")
COLOR_ACENTO = colors.HexColor("#1F4E79")
COLOR_LINEA = colors.HexColor("#9AA5B1")
COLOR_FONDO = colors.HexColor("#F1F4F8")
COLOR_TEXTO_TENUE = colors.HexColor("#5A6472")

COLOR_SEVERIDAD = {
    "critico": colors.HexColor("#B3261E"),
    "advertencia": colors.HexColor("#A15C00"),
    "informativo": colors.HexColor("#1F4E79"),
}


# ---------------------------------------------------------------------------
# Utilidades de texto
# ---------------------------------------------------------------------------
def _texto(valor: Any, predeterminado: str = "—") -> str:
    """Escapa el contenido para ReportLab y convierte los saltos de línea en ``<br/>``."""
    if valor is None:
        return predeterminado
    texto = str(valor).strip()
    if not texto:
        return predeterminado
    return escape(texto).replace("\r\n", "\n").replace("\n", "<br/>")


def _parrafos(clausula: Optional[str]) -> List[str]:
    """Divide una cláusula en párrafos no vacíos."""
    if not clausula:
        return []
    lineas = clausula.replace("\r\n", "\n").split("\n")
    return [linea.strip() for linea in lineas if linea.strip()]


def _lista(valor: Any) -> List[Any]:
    """Normaliza un valor iterable (tolera ``None``)."""
    if not valor:
        return []
    return list(valor)

# ---------------------------------------------------------------------------
# Estilos tipográficos
# ---------------------------------------------------------------------------
def _estilos() -> Dict[str, ParagraphStyle]:
    """Estilos del documento: encabezados, cuerpo, celdas y firmas."""
    return {
        "sistema": ParagraphStyle(
            "sistema",
            fontName=FUENTE_BASE,
            fontSize=9.5,
            leading=12,
            textColor=COLOR_ACENTO,
            alignment=TA_LEFT,
        ),
        "titulo": ParagraphStyle(
            "titulo",
            fontName=FUENTE_NEGRITA,
            fontSize=14,
            leading=17,
            alignment=TA_CENTER,
            textColor=COLOR_TITULO,
            spaceAfter=2,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo",
            fontName=FUENTE_BASE,
            fontSize=9.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=COLOR_ACENTO,
        ),
        "seccion": ParagraphStyle(
            "seccion",
            fontName=FUENTE_NEGRITA,
            fontSize=10.5,
            leading=13,
            alignment=TA_LEFT,
            textColor=COLOR_ACENTO,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "subseccion": ParagraphStyle(
            "subseccion",
            fontName=FUENTE_NEGRITA,
            fontSize=9.5,
            leading=12,
            textColor=COLOR_TITULO,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "cuerpo": ParagraphStyle(
            "cuerpo",
            fontName=FUENTE_BASE,
            fontSize=9.5,
            leading=13.5,
            alignment=TA_JUSTIFY,
            spaceAfter=5,
        ),
        "fundamento": ParagraphStyle(
            "fundamento",
            fontName=FUENTE_CURSIVA,
            fontSize=8.5,
            leading=11,
            textColor=COLOR_TEXTO_TENUE,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "celda": ParagraphStyle("celda", fontName=FUENTE_BASE, fontSize=8.5, leading=11),
        "celda_centro": ParagraphStyle(
            "celda_centro",
            fontName=FUENTE_BASE,
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
        ),
        "celda_encabezado": ParagraphStyle(
            "celda_encabezado",
            fontName=FUENTE_NEGRITA,
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        ),
        "etiqueta": ParagraphStyle(
            "etiqueta", fontName=FUENTE_NEGRITA, fontSize=8.5, leading=11.5
        ),
        "firma": ParagraphStyle(
            "firma", fontName=FUENTE_BASE, fontSize=8.5, leading=11, alignment=TA_CENTER
        ),
        "firma_nombre": ParagraphStyle(
            "firma_nombre",
            fontName=FUENTE_NEGRITA,
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
        ),
        "nota": ParagraphStyle(
            "nota",
            fontName=FUENTE_BASE,
            fontSize=8,
            leading=10.5,
            textColor=COLOR_TEXTO_TENUE,
            alignment=TA_JUSTIFY,
        ),
    }


# ---------------------------------------------------------------------------
# Canvas con encabezado y numeración "Página X de Y"
# ---------------------------------------------------------------------------
class _CanvasActaLegal(lienzo.Canvas):
    """Canvas que dibuja el encabezado institucional y el pie de página numerado."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Los parámetros propios se extraen antes de invocar al Canvas de ReportLab.
        self._encabezado: str = kwargs.pop("encabezado", TITULO_SISTEMA)
        self._folio: str = kwargs.pop("folio", "")
        self._pie: str = kwargs.pop("pie", "")
        self._margen: float = kwargs.pop("margen", 2.5 * cm)
        self._numerar: bool = kwargs.pop("numerar", True)
        self._logo_empresa: Optional[str] = kwargs.pop("logo_empresa", None)
        self._firma_electronica: bool = kwargs.pop("firma_electronica", False)
        super().__init__(*args, **kwargs)
        self._estados: List[Dict[str, Any]] = []

    def showPage(self) -> None:  # noqa: N802 - API de ReportLab
        """Acumula el estado de la página para numerarla hasta conocer el total."""
        self._estados.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:  # noqa: N802 - API de ReportLab
        """Dibuja encabezado/pie en cada página ya compaginada y guarda el PDF."""
        total = len(self._estados)
        for estado in self._estados:
            self.__dict__.update(estado)
            self._dibujar_marco(total)
            lienzo.Canvas.showPage(self)
        lienzo.Canvas.save(self)

    def _dibujar_marco(self, total: int) -> None:
        """Encabezado con el sistema y el folio; pie con leyenda y numeración."""
        ancho, alto = self._pagesize
        self.saveState()
        self.setStrokeColor(COLOR_LINEA)
        self.setLineWidth(0.4)

        # Logo de la empresa en el encabezado (si se proporcionó).
        if self._logo_empresa:
            try:
                from reportlab.lib.utils import ImageReader
                datos_b64 = self._logo_empresa
                if "," in datos_b64:
                    datos_b64 = datos_b64.split(",", 1)[1]
                import base64
                imagen_bytes = base64.b64decode(datos_b64)
                img_reader = ImageReader(io.BytesIO(imagen_bytes))
                iw, ih = img_reader.getSize()
                alto_logo = 1.15 * cm
                ancho_logo = alto_logo * iw / ih
                self.drawImage(
                    img_reader,
                    self._margen,
                    alto - alto_logo - 0.25 * cm,
                    width=ancho_logo,
                    height=alto_logo,
                    preserveAspectRatio=True,
                    mask="auto",
                )
            except Exception:
                logger.warning("No se pudo renderizar el logo_empresa en el encabezado del PDF.")

        # Encabezado
        self.setFont(FUENTE_NEGRITA, 8)
        self.setFillColor(COLOR_ACENTO)
        self.drawString(self._margen, alto - 1.25 * cm, self._encabezado)
        self.setFont(FUENTE_BASE, 8)
        self.setFillColor(COLOR_TEXTO_TENUE)
        self.drawRightString(ancho - self._margen, alto - 1.25 * cm, self._folio)
        self.line(self._margen, alto - 1.42 * cm, ancho - self._margen, alto - 1.42 * cm)

        # Pie de página
        self.setFont(FUENTE_BASE, 7)
        self.drawString(self._margen, 1.05 * cm, self._pie[:150])
        if self._numerar:
            self.setFont(FUENTE_BASE, 7.5)
            self.drawRightString(
                ancho - self._margen,
                1.05 * cm,
                f"Página {self._pageNumber} de {total}",
            )
        if self._firma_electronica:
            self.setFont(FUENTE_CURSIVA, 7.5)
            self.setFillColor(COLOR_TEXTO_TENUE)
            self.drawCentredString(
                ancho / 2,
                0.65 * cm,
                "Este acta cuenta con firma electrónica avanzada conforme a la normativa aplicable.",
            )
        self.line(self._margen, 1.35 * cm, ancho - self._margen, 1.35 * cm)
        self.restoreState()

# ---------------------------------------------------------------------------
# Helpers de maquetación
# ---------------------------------------------------------------------------
def _tabla(
    filas: Sequence[Sequence[Any]],
    anchos: Sequence[float],
    estilos_extra: Optional[Sequence[tuple]] = None,
    repetir_encabezado: bool = False,
) -> Table:
    """Crea una tabla con el estilo institucional del documento."""
    tabla = Table(
        filas,
        colWidths=list(anchos),
        repeatRows=1 if repetir_encabezado else 0,
        hAlign="LEFT",
    )
    base: List[tuple] = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, COLOR_LINEA),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    tabla.setStyle(TableStyle(base + list(estilos_extra or [])))
    return tabla


def _regla() -> Table:
    """Línea horizontal fina que separa el encabezado del cuerpo del acta."""
    tabla = Table([[""]], colWidths=[LETTER[0] - 5.0 * cm], rowHeights=[2])
    tabla.setStyle(
        TableStyle(
            [
                ("LINEBELOW", (0, 0), (-1, -1), 1.1, COLOR_ACENTO),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tabla


# ---------------------------------------------------------------------------
# Secciones del acta
# ---------------------------------------------------------------------------
def _seccion_titulo(data: Mapping[str, Any], estilos: Mapping[str, ParagraphStyle]) -> List[Any]:
    """Encabezado del documento: título del acta, folio, versión y estado."""
    titulo_documento = data.get("titulo_documento") or (
        f"ACTA DE {str(data.get('tipo_asamblea_texto') or 'ASAMBLEA').upper()}"
    )
    meta = data.get("meta") or {}
    referencia = (
        f"Acta {data.get('folio') or ''} · versión {meta.get('version', 1)} · "
        f"estatus {meta.get('estatus', 'borrador')}"
    )
    tipo_sociedad = data.get("tipo_sociedad")
    subtitulo_texto = data.get("subtitulo_documento") or (
        f"{str(tipo_sociedad or '').replace('_', ' ').title()} · {referencia}"
        if tipo_sociedad
        else referencia
    )
    return [
        Paragraph(_texto(titulo_documento, "ACTA DE ASAMBLEA"), estilos["titulo"]),
        Paragraph(_texto(subtitulo_texto), estilos["subtitulo"]),
        Spacer(1, 6),
        _regla(),
        Spacer(1, 10),
    ]


def _seccion_datos_generales(
    data: Mapping[str, Any], estilos: Mapping[str, ParagraphStyle]
) -> List[Any]:
    """Cuadro de datos generales de la asamblea (dos columnas etiqueta/valor)."""
    anchos = [3.0 * cm, 5.30 * cm, 3.0 * cm, 5.29 * cm]
    filas: List[List[Any]] = []
    spans: List[tuple] = []

    def etiqueta(texto: str) -> Paragraph:
        return Paragraph(_texto(texto), estilos["etiqueta"])

    def valor(texto: Any) -> Paragraph:
        return Paragraph(_texto(texto), estilos["celda"])

    def fila(etiqueta_1: str, valor_1: Any, etiqueta_2: Optional[str] = None, valor_2: Any = None) -> None:
        indice = len(filas)
        if etiqueta_2 is None:
            filas.append([etiqueta(etiqueta_1), valor(valor_1), "", ""])
            spans.append(("SPAN", (1, indice), (3, indice)))
        else:
            filas.append([etiqueta(etiqueta_1), valor(valor_1), etiqueta(etiqueta_2), valor(valor_2)])

    fila("Sociedad", data.get("sociedad"), "R.F.C.", data.get("rfc_sociedad"))
    fila("Tipo de asamblea", data.get("tipo_asamblea_texto"), "Folio", data.get("folio"))
    fila("Fecha de celebración", data.get("fecha_texto"), "Hora", data.get("hora_texto"))
    fila("Lugar de la reunión", data.get("lugar"))
    fila("Convocatoria", data.get("convocatoria_texto"))
    fila(
        "Capital social",
        data.get("capital_social_texto"),
        "Capital representado",
        data.get("capital_presente_texto"),
    )
    fila(
        "Quórum acreditado",
        data.get("quorum_texto"),
        "Acciones en circulación",
        data.get("acciones_totales_texto"),
    )
    fila("Presidente", data.get("presidente"), "Secretario", data.get("secretario"))

    tabla = _tabla(
        filas,
        anchos,
        [
            *spans,
            ("BACKGROUND", (0, 0), (0, -1), COLOR_FONDO),
            ("BACKGROUND", (2, 0), (2, -1), COLOR_FONDO),
        ],
    )
    return [Paragraph("I. DATOS GENERALES DE LA ASAMBLEA", estilos["seccion"]), tabla]

def _seccion_asistentes(
    data: Mapping[str, Any],
    estilos: Mapping[str, ParagraphStyle],
    opciones: Mapping[str, Any],
) -> List[Any]:
    """Tabla de asistentes con su carácter, tenencia accionaria y firma."""
    asistentes = _lista(data.get("asistentes"))
    if not opciones.get("incluir_tabla_asistentes", True) or not asistentes:
        return []

    encabezados = ["No.", "Nombre del asistente", "Carácter", "Cargo", "Acciones", "% Capital", "Firma"]
    anchos = [0.90 * cm, 4.60 * cm, 2.60 * cm, 3.00 * cm, 1.90 * cm, 1.70 * cm, 1.89 * cm]

    filas: List[List[Any]] = [[Paragraph(encabezado, estilos["celda_encabezado"]) for encabezado in encabezados]]
    for indice, asistente in enumerate(asistentes, start=1):
        filas.append(
            [
                Paragraph(str(indice), estilos["celda_centro"]),
                Paragraph(_texto(asistente.get("nombre")), estilos["celda"]),
                Paragraph(_texto(asistente.get("caracter")), estilos["celda"]),
                Paragraph(_texto(asistente.get("cargo")), estilos["celda"]),
                Paragraph(_texto(asistente.get("acciones")), estilos["celda_centro"]),
                Paragraph(_texto(asistente.get("porcentaje")), estilos["celda_centro"]),
                Paragraph("Sí" if asistente.get("firma", True) else "No", estilos["celda_centro"]),
            ]
        )

    tabla = _tabla(
        filas,
        anchos,
        [
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACENTO),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
        ],
        repetir_encabezado=True,
    )
    return [Paragraph("II. ASISTENCIA Y QUÓRUM", estilos["seccion"]), tabla, Spacer(1, 4)]


def _seccion_orden_del_dia(
    data: Mapping[str, Any], estilos: Mapping[str, ParagraphStyle]
) -> List[Any]:
    """Lista numerada del orden del día aprobado por la asamblea."""
    puntos = _lista(data.get("orden_del_dia"))
    if not puntos:
        return []

    elementos: List[Any] = [Paragraph("III. ORDEN DEL DÍA", estilos["seccion"])]
    for punto in puntos:
        titulo = f"<b>{_texto(punto.get('numero'))}.</b> {_texto(punto.get('titulo'))}"
        elementos.append(Paragraph(titulo, estilos["cuerpo"]))
        if punto.get("descripcion"):
            elementos.append(Paragraph(_texto(punto.get("descripcion")), estilos["nota"]))
    elementos.append(Spacer(1, 4))
    return elementos

def _seccion_desarrollo(
    data: Mapping[str, Any], estilos: Mapping[str, ParagraphStyle]
) -> List[Any]:
    """Párrafos introductorios del acta: encabezado, declaración de quórum e instalación."""
    clausulas = data.get("clausulas") or {}
    elementos: List[Any] = [Paragraph("IV. DESARROLLO DE LA ASAMBLEA", estilos["seccion"])]

    for clave in ("encabezado", "declaracion_quorum", "declaracion_instalacion"):
        for parrafo in _parrafos(clausulas.get(clave)):
            elementos.append(Paragraph(_texto(parrafo), estilos["cuerpo"]))

    if len(elementos) == 1:
        elementos.append(
            Paragraph(
                "Se hace constar el desarrollo de la asamblea conforme a los datos registrados.",
                estilos["cuerpo"],
            )
        )
    return elementos


def _seccion_acuerdos(
    data: Mapping[str, Any], estilos: Mapping[str, ParagraphStyle]
) -> List[Any]:
    """Acuerdos adoptados: título, cláusula legal redactada, fundamento y votación."""
    acuerdos = _lista(data.get("acuerdos"))
    elementos: List[Any] = [Paragraph("V. ACUERDOS Y RESOLUCIONES", estilos["seccion"])]

    if not acuerdos:
        elementos.append(Paragraph("No se registraron acuerdos en la asamblea.", estilos["cuerpo"]))
        return elementos

    for acuerdo in acuerdos:
        encabezado = Paragraph(
            f"ACUERDO {_texto(acuerdo.get('numero'))}. {_texto(acuerdo.get('titulo'))}",
            estilos["subseccion"],
        )
        cuerpo: List[Any] = []
        parrafos = _parrafos(acuerdo.get("clausula_legal")) or [
            _texto(acuerdo.get("resumen"), "Sin descripción registrada.")
        ]
        for parrafo in parrafos:
            cuerpo.append(Paragraph(_texto(parrafo), estilos["cuerpo"]))

        # El encabezado viaja con el primer párrafo para no quedar huérfano al final de página.
        elementos.append(KeepTogether([encabezado, cuerpo[0]]))
        elementos.extend(cuerpo[1:])

        if acuerdo.get("fundamento_legal"):
            elementos.append(
                Paragraph(
                    f"Fundamento legal: {_texto(acuerdo.get('fundamento_legal'))}",
                    estilos["fundamento"],
                )
            )

        filas_votacion = [
            [
                Paragraph("Mayoría aplicable", estilos["celda_encabezado"]),
                Paragraph("Resultado de la votación", estilos["celda_encabezado"]),
            ],
            [
                Paragraph(_texto(acuerdo.get("mayoria_texto")), estilos["celda"]),
                Paragraph(_texto(acuerdo.get("votacion_texto")), estilos["celda"]),
            ],
        ]
        elementos.append(
            _tabla(
                filas_votacion,
                [6.0 * cm, 10.59 * cm],
                [("BACKGROUND", (0, 0), (-1, 0), COLOR_ACENTO)],
            )
        )
        elementos.append(Spacer(1, 12))

    return elementos

def _seccion_cierre(
    data: Mapping[str, Any], estilos: Mapping[str, ParagraphStyle]
) -> List[Any]:
    """Cierre formal del acta, facultades de ejecución y observaciones del usuario."""
    clausulas = data.get("clausulas") or {}
    elementos: List[Any] = [Paragraph("VI. DECLARACIÓN DE CIERRE", estilos["seccion"])]

    for clave in ("cierre", "declaracion_protocolizacion"):
        for parrafo in _parrafos(clausulas.get(clave)):
            elementos.append(Paragraph(_texto(parrafo), estilos["cuerpo"]))

    if data.get("observaciones"):
        elementos.append(Paragraph("Observaciones y salvedades", estilos["subseccion"]))
        for parrafo in _parrafos(data.get("observaciones")):
            elementos.append(Paragraph(_texto(parrafo), estilos["nota"]))

    return elementos


def _seccion_firmas(
    data: Mapping[str, Any],
    estilos: Mapping[str, ParagraphStyle],
    opciones: Mapping[str, Any],
) -> List[Any]:
    """Hoja de firmas: un bloque con línea, nombre y carácter por cada firmante."""
    if not opciones.get("incluir_hoja_firmas", True):
        return []

    asistentes = _lista(data.get("asistentes"))
    firmantes = [asistente for asistente in asistentes if asistente.get("firma", True)] or asistentes
    if not firmantes:
        return []

    elementos: List[Any] = [Paragraph("VII. FIRMAS", estilos["seccion"])]
    bloques: List[Table] = []

    for firmante in firmantes:
        caracter = firmante.get("caracter") or ""
        cargo = firmante.get("cargo") or ""
        detalle = " · ".join(texto for texto in (caracter, cargo) if texto)

        bloque = Table(
            [
                [Spacer(1, 26)],
                [Paragraph("________________________________", estilos["firma"])],
                [Paragraph(_texto(firmante.get("nombre")), estilos["firma_nombre"])],
                [Paragraph(_texto(detalle), estilos["firma"])],
            ],
            colWidths=[7.6 * cm],
        )
        bloque.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        bloques.append(bloque)

    # Los firmantes se distribuyen en dos columnas por fila.
    for indice in range(0, len(bloques), 2):
        par: List[Any] = list(bloques[indice : indice + 2])
        while len(par) < 2:
            par.append("")
        fila = Table([par], colWidths=[8.3 * cm, 8.29 * cm], hAlign="LEFT")
        fila.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        elementos.append(fila)

    return elementos

def _seccion_anexo_validacion(
    data: Mapping[str, Any],
    estilos: Mapping[str, ParagraphStyle],
    opciones: Mapping[str, Any],
) -> List[Any]:
    """Anexo opcional con el resultado de la validación de consistencia."""
    validacion = data.get("validacion") or {}
    if not opciones.get("incluir_anexo_validacion") or not validacion:
        return []

    elementos: List[Any] = [
        PageBreak(),
        Paragraph("ANEXO. VALIDACIÓN DE CONSISTENCIA", estilos["seccion"]),
        Paragraph(_texto(validacion.get("consistencia")), estilos["cuerpo"]),
    ]

    puntaje = validacion.get("puntaje")
    resumen = [
        [
            Paragraph("Puntaje", estilos["celda_encabezado"]),
            Paragraph("Proveedor", estilos["celda_encabezado"]),
            Paragraph("Validado con IA", estilos["celda_encabezado"]),
        ],
        [
            Paragraph(
                f"{float(puntaje):.2f} / 100" if isinstance(puntaje, (int, float)) else "—",
                estilos["celda_centro"],
            ),
            Paragraph(_texto(validacion.get("proveedor")), estilos["celda_centro"]),
            Paragraph("Sí" if validacion.get("generado_por_ia") else "No", estilos["celda_centro"]),
        ],
    ]
    elementos.append(
        _tabla(
            resumen,
            [5.53 * cm, 5.53 * cm, 5.53 * cm],
            [("BACKGROUND", (0, 0), (-1, 0), COLOR_ACENTO)],
        )
    )
    elementos.append(Spacer(1, 8))

    hallazgos = _lista(validacion.get("hallazgos"))
    if hallazgos:
        filas: List[List[Any]] = [
            [
                Paragraph("Severidad", estilos["celda_encabezado"]),
                Paragraph("Campo", estilos["celda_encabezado"]),
                Paragraph("Hallazgo", estilos["celda_encabezado"]),
            ]
        ]
        for hallazgo in hallazgos:
            severidad = str(hallazgo.get("severidad") or "informativo").lower()
            filas.append(
                [
                    Paragraph(_texto(severidad.capitalize()), estilos["celda_centro"]),
                    Paragraph(_texto(hallazgo.get("campo")), estilos["celda"]),
                    Paragraph(_texto(hallazgo.get("mensaje")), estilos["celda"]),
                ]
            )
        elementos.append(
            _tabla(
                filas,
                [2.6 * cm, 4.0 * cm, 9.99 * cm],
                [
                    ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACENTO),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FONDO]),
                    ("TEXTCOLOR", (0, 1), (0, -1), colors.black),
                ],
                repetir_encabezado=True,
            )
        )
        elementos.append(Spacer(1, 8))

    recomendaciones = _lista(validacion.get("recomendaciones"))
    if recomendaciones:
        elementos.append(Paragraph("Recomendaciones", estilos["subseccion"]))
        for indice, recomendacion in enumerate(recomendaciones, start=1):
            elementos.append(Paragraph(f"{indice}. {_texto(recomendacion)}", estilos["nota"]))

    elementos.append(Spacer(1, 8))
    elementos.append(
        Paragraph(
            "El presente anexo es informativo: recoge la revisión automática de consistencia y no "
            "forma parte de las declaraciones de voluntad de la asamblea.",
            estilos["nota"],
        )
    )
    return elementos

# ---------------------------------------------------------------------------
# API pública del módulo
# ---------------------------------------------------------------------------
def _construir_story(
    data: Mapping[str, Any],
    estilos: Mapping[str, ParagraphStyle],
    opciones: Mapping[str, Any],
) -> List[Any]:
    """Ensambla, en orden, todas las secciones del acta."""
    story: List[Any] = []
    story += _seccion_titulo(data, estilos)
    story += _seccion_datos_generales(data, estilos)
    story += _seccion_asistentes(data, estilos, opciones)
    story += _seccion_orden_del_dia(data, estilos)
    story += _seccion_desarrollo(data, estilos)
    story += _seccion_acuerdos(data, estilos)
    story += _seccion_cierre(data, estilos)
    story += _seccion_firmas(data, estilos, opciones)
    story += _seccion_anexo_validacion(data, estilos, opciones)
    return story


def build_acta_pdf(data: dict) -> bytes:
    """Compila el acta y devuelve el contenido binario del PDF.

    Es la única función que consume el resto de la plataforma: recibe el
    diccionario documentado al inicio del módulo (datos + texto legal ya
    redactado) y devuelve los bytes listos para su descarga.

    :raises TypeError: si ``data`` no es un diccionario.
    """
    if not isinstance(data, Mapping):
        raise TypeError("build_acta_pdf espera un diccionario con los datos del acta.")

    estilos = _estilos()
    opciones: Dict[str, Any] = dict(data.get("opciones") or {})
    opciones.setdefault("incluir_tabla_asistentes", True)
    opciones.setdefault("incluir_hoja_firmas", True)
    opciones.setdefault("incluir_anexo_validacion", False)
    numerar = bool(opciones.get("numerar_paginas", True))

    folio = data.get("folio") or "SIN-FOLIO"
    margen = float(data.get("margen_cm") or 2.5) * cm
    buffer = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=margen,
        rightMargin=margen,
        topMargin=2.05 * cm,
        bottomMargin=2.05 * cm,
        title=f"Acta {folio}",
        author=str(data.get("sociedad") or TITULO_SISTEMA),
        subject=f"Acta corporativa {folio}",
        creator=TITULO_SISTEMA,
        keywords="acta, asamblea, sociedades mercantiles, LGSM, corporativo",
    )

    documento.build(
        _construir_story(data, estilos, opciones),
        canvasmaker=partial(
            _CanvasActaLegal,
            encabezado=TITULO_SISTEMA,
            folio=f"Acta {folio}",
            pie=str(data.get("pie_confidencialidad") or ""),
            margen=margen,
            numerar=numerar,
            logo_empresa=data.get("logo_empresa"),
        firma_electronica=bool(data.get("firma_electronica")),
        ),
    )

    pdf = buffer.getvalue()
    buffer.close()
    logger.info("PDF del acta %s generado (%d bytes)", folio, len(pdf))
    return pdf


def nombre_archivo_acta(folio: str, sociedad: str = "", fecha: str = "") -> str:
    """Nombre de archivo seguro, descriptivo y sin acentos para la descarga."""
    def _limpio(valor: Any, longitud: int = 60) -> str:
        descompuesto = unicodedata.normalize("NFKD", str(valor or ""))
        sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
        return re.sub(r"[^A-Za-z0-9._-]+", "_", sin_acentos).strip("_")[:longitud]

    partes = [_limpio(folio, 32) or "acta", _limpio(sociedad, 40), _limpio(fecha, 12)]
    return "_".join(parte for parte in partes if parte) + ".pdf"







