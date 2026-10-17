"""Asistente conversacional interno de actas (IA sin dependencias externas).

Funciona en cualquier PC sin internet ni API keys: puerta tematica,
intenciones por reglas, redaccion LGSM con plantillas y validacion
determinista. Lee el estatus real desde la BD, nunca lo inventa.

Además acompaña la CREACIÓN guiada del acta: si el usuario pide un acta en
específico le pide los datos necesarios; si no sabe qué acta crear le ofrece
el catálogo con descripciones; al completar genera texto organizado + PDF
descargable y devuelve el control (folio, fecha, autor, caducidad, versión).
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.catalogos import etiqueta_tipo_asamblea
from app.models.acta import Acta
from app.models.enums import EstatusActa
from app.schemas.acta import ActaGenerarPdfRequest
from app.services import administracion, plantillas_legales
from app.services.acta_service import (
    actualizar_estatus,
    generar_pdf,
    obtener_acta,
    validar_acta_almacenada,
)
from app.services.flujo_creacion import (
    TIPOS_GUIA,
    construir_payload_desde_sesion,
    crear_sesion,
    detectar_tipo_en_texto,
    extraer_datos,
    obtener_sesion,
    reiniciar_sesion,
    siguiente_faltante,
    texto_catalogo_tipos,
)

logger = logging.getLogger(__name__)

__all__ = [
    "es_tema_valido", "detectar_intencion", "extraer_folio",
    "extraer_id", "procesar_mensaje", "texto_ayuda", "SUGERENCIAS",
    "TIPOS_GUIA",
]

PALABRAS_TEMA = (
    "acta", "actas", "asamblea", "consejo", "acuerdo", "acuerdos",
    "clausula", "quorum", "mayoria", "votacion", "folio", "estatus",
    "borrador", "revision", "aprobada", "aprobado", "firmada", "firmar",
    "archivada", "version", "versiones", "vigencia", "caducidad",
    "vencida", "validar", "validacion", "consistencia", "redactar",
    "redaccion", "lgsm", "sociedad", "estatutos", "capital", "acciones",
    "accionista", "presidente", "secretario", "escrutador", "comisario",
    "convocatoria", "orden del dia", "aumento", "reduccion", "fusion",
    "escision", "disolucion", "liquidacion", "protocolizar", "fedatario",
    "notario", "ordinaria", "extraordinaria", "constitutiva", "mixta",
    "restaurar", "historial", "hallazgo", "puntaje", "estado", "ayuda",
    "crear", "crea", "generar", "genera", "nueva", "nuevo", "necesito",
    "quiero", "elaborar", "hazme", "cual", "cuales", "tipos", "opciones",
    "elegir", "escoger", "pdf", "descargar", "descarga", "cancelar",
)

PALABRAS_FUERA = (
    "futbol", "mundial", "receta", "cocina", "videojuego", "pelicula",
    "cancion", "horoscopo", "bitcoin", "cripto", "dieta",
)

MENSAJE_FUERA = (
    "Solo puedo ayudarte con temas de actas administrativas y corporativas "
    "(redaccion, validacion, aprobacion, estatus y versiones). "
    "Ejemplos: «Estatus de PGAC-2026-0001», «Valida el acta 1», "
    "«Redacta un aumento de capital»."
)

SUGERENCIAS = [
    "Quiero crear un acta",
    "Qué tipos de acta hay?",
    "Crear acta ordinaria",
    "Estatus de PGAC-2026-0001",
    "Valida el acta 1",
    "Cuantas actas hay por estatus?",
    "Versiones del acta 1",
    "Ayuda",
]

ORDEN_ESTATUS = ["borrador", "en_revision", "aprobada", "firmada", "archivada"]
PATRON_FOLIO = re.compile(r"PGAC-\d{4}-\d{1,6}", re.IGNORECASE)


def _norm(t: str) -> str:
    if not t:
        return ""
    d = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in d if not unicodedata.combining(c))


def es_tema_valido(mensaje: str) -> bool:
    norm = _norm(mensaje or "")
    if not norm.strip():
        return False
    if any(_norm(p) in norm for p in PALABRAS_FUERA):
        if not any(k in norm for k in ("acta", "asamblea", "acuerdo", "folio")):
            return False
    return any(_norm(t) in norm for t in PALABRAS_TEMA)


def detectar_intencion(mensaje: str) -> str:
    n = _norm(mensaje or "")
    if any(k in n for k in ("restaurar", "recuperar version", "volver a la version")):
        return "restaurar"
    if any(k in n for k in ("cancelar", "olvida", "empezar de nuevo", "reiniciar")):
        return "cancelar_creacion"
    if any(k in n for k in ("que tipos hay", "que actas hay", "cuales actas",
                            "tipos de acta", "que acta", "cual acta",
                            "no se que acta", "no se cual", "ayudame a elegir",
                            "opciones de acta", "catalogo de actas")):
        return "catalogo_tipos"
    # Crear/generar ACTA completa -> flujo guiado. OJO: «redacta un acuerdo»
    # es solo un borrador de cláusula (intención redactar), no el acta entera.
    es_borrador_acuerdo = any(k in n for k in ("redacta", "redaccion", "redactar",
                                               "escribe", "genera un acuerdo",
                                               "acuerdo de", "clausula"))
    if not es_borrador_acuerdo:
        if (any(k in n for k in ("crear acta", "crea un acta", "creame un acta",
                                 "generar acta", "genera un acta", "nueva acta",
                                 "nuevo acta", "quiero un acta", "necesito un acta",
                                 "elaborar acta", "hazme un acta", "quiero crear",
                                 "crear un acta"))
                or (detectar_tipo_en_texto(mensaje) is not None
                    and "acta" in n)):
            return "crear"
    if any(k in n for k in ("validar", "valida", "consistencia", "hallazgo", "puntaje")):
        return "validar"
    if any(k in n for k in ("redacta", "redaccion", "redactar", "escribe", "genera un acuerdo")):
        return "redactar"
    if (any(k in n for k in ("aprueba", "aprobar", "aprobada", "aprobado", "autoriza",
                             "pasa a", "pasala a", "pasalo a", "cambia el estatus",
                             "cambiar estatus", "firmar", "firmada", "firmado",
                             "archivar", "archivada", "archivarla"))
            or re.search(r"\bpasa\b.*\bacta\b", n)
            or re.search(r"\ba\s+(revision|aprobada|firmada|archivada)\b", n)):
        return "aprobar"
    if any(k in n for k in ("vencida", "vigencia", "caducidad", "por vencer",
                            "cuantas actas", "resumen", "estadistica", "totales", "cuantas hay")):
        return "resumen"
    if re.search(r"\bversiones?\b", n) or "historial" in n or "que cambio" in n:
        return "versiones"
    if any(k in n for k in ("estatus", "estado", "en que va", "como va", "donde esta",
                            "busca el acta", "muestrame el acta", "muestra el acta")):
        return "estatus"
    if any(k in n for k in ("ayuda", "que puedes hacer", "que sabes hacer", "como funciona", "ejemplos")):
        return "ayuda"
    if extraer_folio(mensaje) or re.search(r"\bacta\s+\d+\b", n):
        return "estatus"
    return "ayuda"


def extraer_folio(mensaje: str) -> Optional[str]:
    m = PATRON_FOLIO.search(mensaje or "")
    return m.group(0).upper() if m else None


def extraer_id(mensaje: str) -> Optional[int]:
    m = re.search(r"\bacta\s+(?:numero\s+|n\.?\s*)?(\d{1,6})\b", _norm(mensaje or ""))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def extraer_num_version(mensaje: str) -> Optional[int]:
    m = re.search(r"version\s+(\d{1,4})", _norm(mensaje or ""))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def extraer_estatus_destino(mensaje: str) -> Optional[str]:
    n = _norm(mensaje or "")
    if re.search(r"\ba\s+revision\b", n) or "en revision" in n:
        return "en_revision"
    for est in EstatusActa:
        if _norm(est.value) in n or _norm(est.value.replace("_", " ")) in n:
            return est.value
    if "revision" in n:
        return "en_revision"
    if "protocoliz" in n:
        return "archivada"
    return None


def _buscar(db: Session, folio: Optional[str], acta_id: Optional[int]) -> Optional[Acta]:
    if acta_id is not None:
        try:
            return obtener_acta(db, acta_id)
        except Exception:
            pass
    if folio:
        return db.scalar(select(Acta).where(func.upper(Acta.folio) == folio.upper()))
    return None


def _linea(acta: Acta) -> str:
    tipo = etiqueta_tipo_asamblea(getattr(acta, "tipo_asamblea", ""))
    estatus = str(getattr(acta.estatus, "value", acta.estatus))
    return (f"{acta.folio} | {acta.sociedad} | {tipo} | estatus "
            f"{estatus} | v{acta.version} | vigencia {acta.estado_caducidad}")


def _dato_acta(acta: Acta) -> Dict[str, Any]:
    return {"id": acta.id, "folio": acta.folio, "sociedad": acta.sociedad,
            "estatus": str(getattr(acta.estatus, "value", acta.estatus)),
            "version": int(acta.version or 1),
            "tipo_asamblea": str(getattr(acta.tipo_asamblea, "value", acta.tipo_asamblea)),
            "fecha": acta.fecha.isoformat() if getattr(acta, "fecha", None) else None,
            "creado_por": getattr(acta, "creado_por", None)}


def _respuesta_sesion(sesion, texto, faltante_extra=None):
    falt = faltante_extra or siguiente_faltante(sesion)
    datos = sesion.get("datos", {})
    hechos = sum(1 for v in datos.values() if v not in (None, "", [], {}))
    base = {"respuesta": texto, "intencion": "crear", "tema_valido": True,
            "sesion_id": sesion["sesion_id"],
            "tipo_asamblea": sesion.get("tipo_asamblea"),
            "datos_recolectados": datos, "progreso": {"completados": hechos, "total": 7}}
    if falt is not None:
        base["campo_solicitado"] = falt["clave"]
    return base


def _cerrar_y_generar(db, sesion, autor):
    try:
        payload_dict = construir_payload_desde_sesion(sesion)
        payload_dict["creado_por"] = (autor or "asistente").strip()[:150] or "asistente"
        solicitud = ActaGenerarPdfRequest(**payload_dict)
        pdf_bytes, metadatos = generar_pdf(solicitud, db)
        acta = _buscar(db, metadatos.get("folio"), metadatos.get("acta_id"))
        reiniciar_sesion(sesion.get("sesion_id"))
        pdf_url = ("/api/v1/actas/%s/pdf" % metadatos.get("acta_id")) if metadatos.get("acta_id") else None
        control = {"folio": metadatos.get("folio"), "acta_id": metadatos.get("acta_id"),
            "version": metadatos.get("version", 1),
            "fecha_acta": payload_dict.get("fecha"),
            "fecha_creacion": acta.created_at.isoformat() if acta is not None and getattr(acta, "created_at", None) else None,
            "creado_por": payload_dict.get("creado_por"),
            "fecha_caducidad": acta.fecha_caducidad.isoformat() if acta is not None and getattr(acta, "fecha_caducidad", None) else None,
            "estado_caducidad": acta.estado_caducidad if acta is not None else "sin_fecha",
            "pdf_descarga": pdf_url, "pdf_nombre": metadatos.get("nombre_archivo"),
            "pdf_paginas": metadatos.get("paginas")}
        texto_org = str(getattr(acta, "texto_legal", "") or "")[:4000] if acta is not None else ""
        tipo_txt = etiqueta_tipo_asamblea(payload_dict.get("tipo_asamblea") or "")
        respuesta = ("Acta %s generada!\nCONTROL: folio %s | fecha %s | creada %s | por %s | "
                     "caducidad %s (%s) | v%s | PDF %s (%s pags) -> GET %s\n\nTEXTO:\n%s"
                     % (tipo_txt, control["folio"], control["fecha_acta"], control["fecha_creacion"],
                        control["creado_por"], control["fecha_caducidad"] or "sin fecha",
                        control["estado_caducidad"], control["version"],
                        control["pdf_nombre"], control["pdf_paginas"], pdf_url, texto_org))
        return {"respuesta": respuesta, "intencion": "crear", "tema_valido": True,
                "acta": _dato_acta(acta) if acta is not None else None,
                "control_acta": control, "acta_id": control["acta_id"],
                "folio": control["folio"], "pdf_descarga": pdf_url,
                "texto_organizado": texto_org,
                "acciones": ([{"etiqueta": "Descargar PDF", "accion": "descargar_pdf",
                               "acta_id": control["acta_id"]}] if control["acta_id"] else [])}
    except Exception as exc:
        logger.exception("Fallo generar acta desde asistente")
        falt = siguiente_faltante(sesion)
        return _respuesta_sesion(sesion, "No pude generarla: %s. %s"
                                 % (str(exc)[:300], falt["pregunta"] if falt else ""), falt)


def texto_ayuda() -> str:
    return ("Soy el Asistente de Actas de PGAC. "
            "Te acompano a CREAR el acta paso a paso: dime Quiero crear un acta. "
            "Si no sabes cual crear te muestro los tipos con su descripcion. "
            "Al terminar genero texto organizado + PDF y el control "
            "(folio, fecha, quien la realizo, caducidad, versiones). Tambien valido, "
            "informo estatus y muestro versiones. Prueba: Quiero crear un acta.")


def _puede_avanzar(origen: str, destino: str) -> bool:
    try:
        return ORDEN_ESTATUS.index(destino) >= ORDEN_ESTATUS.index(origen)
    except ValueError:
        return False


def _redactar_libre(mensaje: str) -> Dict[str, Any]:
    materia = plantillas_legales.detectar_materia(mensaje)
    plantilla = plantillas_legales.obtener_plantilla(materia)
    contexto = {"sociedad": "la sociedad", "resumen": mensaje.strip(),
                "mayoria": "la mayoria aplicable",
                "acciones": "las acciones presentes"}
    red = plantillas_legales.redactar_con_plantilla(materia, contexto)
    texto = ("Borrador con fundamento en " + red["fundamento_legal"]
             + ":\n\n" + red["clausula_legal"]
             + "\n\nAdaptalo con datos reales en Generar acta.")
    return {"respuesta": texto, "intencion": "redactar",
            "acciones": [{"etiqueta": "Ir a generar acta", "accion": "ir_generar"}],
            "texto_borrador": red["clausula_legal"],
            "fundamento": red["fundamento_legal"], "materia": red["materia"],
            "titulo_sugerido": plantilla.titulo}


def _flujo_creacion(db, texto, sesion_id, autor):
    ses = obtener_sesion(sesion_id) if sesion_id else None
    if ses is not None:
        # Si aún no hay tipo (venía del catálogo), el mensaje es la elección.
        if not ses.get("tipo_asamblea"):
            elegido = detectar_tipo_en_texto(texto)
            if elegido:
                ses["tipo_asamblea"] = elegido
                ses["etapa"] = "datos"
                etiqueta = etiqueta_tipo_asamblea(elegido)
                falt = siguiente_faltante(ses)
                return _respuesta_sesion(ses, "Perfecto, creamos %s paso a paso.\n\n%s"
                                         % (etiqueta, falt["pregunta"]), falt)
            return {"respuesta": texto_catalogo_tipos() + "\nSesion %s: dime cual crear." % ses["sesion_id"],
                    "intencion": "catalogo_tipos", "tema_valido": True,
                    "sesion_id": ses["sesion_id"], "tipos_acta": TIPOS_GUIA}
        nuevo = detectar_tipo_en_texto(texto)
        if nuevo and len((texto or "").strip()) < 40:
            ses["tipo_asamblea"] = nuevo
            ses["etapa"] = "datos"
        falt = siguiente_faltante(ses)
        if falt is not None:
            nuevos = extraer_datos(texto, falt["clave"])
            if nuevos:
                ses["datos"].update(nuevos)
                falt2 = siguiente_faltante(ses)
                if falt2 is None:
                    return _cerrar_y_generar(db, ses, autor)
                etiqueta = etiqueta_tipo_asamblea(ses.get("tipo_asamblea") or "")
                return _respuesta_sesion(ses, "Anotado. Seguimos con %s.\n\n%s"
                                         % (etiqueta, falt2["pregunta"]), falt2)
            return _respuesta_sesion(ses, "No entendi ese dato para %s. %s Ejemplo: %s"
                                     % (falt["etiqueta"], falt["pregunta"], falt.get("ejemplo", "")), falt)
        return _cerrar_y_generar(db, ses, autor)
    tipo = detectar_tipo_en_texto(texto)
    if tipo is None:
        # No sabe qué acta crear (o no dijo el tipo) -> catálogo con descripciones.
        ses2 = crear_sesion(None)
        return {"respuesta": texto_catalogo_tipos() + "\nSesion %s: dime cual crear." % ses2["sesion_id"],
                "intencion": "catalogo_tipos", "tema_valido": True,
                "sesion_id": ses2["sesion_id"], "tipos_acta": TIPOS_GUIA}
    ses3 = crear_sesion(tipo or "ordinaria")
    etiqueta = etiqueta_tipo_asamblea(tipo or "ordinaria")
    falt = siguiente_faltante(ses3)
    return _respuesta_sesion(ses3, "Creamos %s paso a paso. Sesion %s.\n\n%s"
                             % (etiqueta, ses3["sesion_id"], falt["pregunta"]), falt)


def procesar_mensaje(db: Session, mensaje: str, folio: Optional[str] = None,
                      acta_id: Optional[int] = None, sesion_id: Optional[str] = None,
                      autor: Optional[str] = None) -> Dict[str, Any]:
    texto = (mensaje or "").strip()
    # Sesión de creación en curso (incluye catálogo->elección de tipo).
    if sesion_id and obtener_sesion(sesion_id) is not None:
        return _flujo_creacion(db, texto, sesion_id, autor)
    if not es_tema_valido(texto):
        return {"respuesta": MENSAJE_FUERA, "intencion": "fuera_de_tema",
                "tema_valido": False,
                "acciones": [{"etiqueta": "Ver ayuda", "accion": "ayuda"}]}
    inten = detectar_intencion(texto)
    if inten in ("crear", "catalogo_tipos", "cancelar_creacion"):
        if inten == "cancelar_creacion":
            if sesion_id:
                reiniciar_sesion(sesion_id)
            return {"respuesta": "Creación cancelada. Dime «Quiero crear un acta» cuando quieras empezar.",
                    "intencion": "cancelar_creacion", "tema_valido": True}
        return _flujo_creacion(db, texto, sesion_id, autor)
    fol = folio or extraer_folio(texto)
    aid = acta_id if acta_id is not None else extraer_id(texto)
    if inten == "ayuda":
        return {"respuesta": texto_ayuda(), "intencion": "ayuda",
                "tema_valido": True,
                "acciones": [{"etiqueta": "Ver resumen", "accion": "resumen"}]}
    if inten == "resumen":
        r = administracion.resumen_administracion(db)
        lin = ["Total actas: %s (versiones: %s)." % (r["total_actas"], r["total_versiones"]),
               "Por estatus:"]
        lin += ["  - %s: %s" % (k, v) for k, v in r["por_estatus"].items()]
        v = r["vigencia"]
        lin.append("Vigencia: %s vigentes, %s por vencer, %s vencidas, %s sin fecha."
                   % (v["vigentes"], v["por_vencer"], v["vencidas"], v["sin_fecha"]))
        if v["vencidas"]:
            venc = administracion.actas_por_vigencia(db, estado="vencida", limite=5)
            lin.append("Vencidas: " + "; ".join(_linea(a) for a in venc))
        return {"respuesta": "\n".join(lin), "intencion": "resumen",
                "tema_valido": True, "resumen": r,
                "acciones": [{"etiqueta": "Ver administracion", "accion": "ir_admin"}]}
    if inten == "redactar" and fol is None and aid is None:
        out = _redactar_libre(texto)
        out["tema_valido"] = True
        return out
    acta = _buscar(db, fol, aid)
    if acta is None:
        if fol or aid:
            ref = fol or ("id %s" % aid)
            return {"respuesta": ("No encontre el acta " + str(ref) + ". Verifica el folio "
                                  "PGAC-AAAA-0001 o el id. Pideme el resumen general."),
                    "intencion": inten, "tema_valido": True,
                    "acciones": [{"etiqueta": "Ver resumen", "accion": "resumen"}]}
        if inten == "redactar":
            out = _redactar_libre(texto)
            out["tema_valido"] = True
            return out
        return {"respuesta": ("De que acta hablamos? Dame el folio (PGAC-2026-0001) "
                              "o el id (acta 1)."),
                "intencion": inten, "tema_valido": True, "requiere_acta": True,
                "acciones": [{"etiqueta": "Ver resumen", "accion": "resumen"}]}
    dato = _dato_acta(acta)
    if inten == "estatus":
        resp = ("El acta " + _linea(acta) + ". Titulo: "
                + str(acta.titulo or "(sin titulo)") + ". Acuerdos: "
                + str(len(acta.acuerdos or [])) + ".")
        return {"respuesta": resp, "intencion": "estatus", "tema_valido": True,
                "acta": dato,
                "acciones": [{"etiqueta": "Validar", "accion": "validar", "acta_id": acta.id},
                             {"etiqueta": "Versiones", "accion": "versiones", "acta_id": acta.id}]}
    if inten == "validar":
        val = validar_acta_almacenada(db, acta.id)
        crit = sum(1 for h in val.hallazgos if str(h.severidad) == "critico")
        adv = sum(1 for h in val.hallazgos if str(h.severidad) == "advertencia")
        resp = ("Validacion de %s: puntaje %s/100. %s Criticos: %s. Advertencias: %s."
                % (acta.folio, val.puntaje, val.consistencia, crit, adv))
        for h in val.hallazgos[:5]:
            resp += "\n- [%s] %s" % (h.severidad, h.mensaje)
            if h.sugerencia:
                resp += " Sugerencia: " + h.sugerencia
        return {"respuesta": resp, "intencion": "validar", "tema_valido": True,
                "acta": _dato_acta(acta), "validacion": val.model_dump(mode="json"),
                "acciones": [{"etiqueta": "Versiones", "accion": "versiones", "acta_id": acta.id}]}
    if inten == "aprobar":
        destino = extraer_estatus_destino(texto)
        origen = str(getattr(acta.estatus, "value", acta.estatus))
        if destino is None:
            return {"respuesta": ("El acta %s esta en %s. A que estatus la paso? "
                                  "Opciones: en_revision, aprobada, firmada, archivada."
                                  % (acta.folio, origen)),
                    "intencion": "aprobar", "tema_valido": True, "acta": dato,
                    "acciones": [{"etiqueta": "Pasar a revision", "accion": "aprobar",
                                  "acta_id": acta.id, "estatus": "en_revision"}]}
        if not _puede_avanzar(origen, destino):
            return {"respuesta": ("No puedo retroceder %s de %s a %s. El flujo solo avanza: %s."
                                  % (acta.folio, origen, destino, " > ".join(ORDEN_ESTATUS))),
                    "intencion": "aprobar", "tema_valido": True, "acta": dato}
        if destino in ("aprobada", "firmada", "archivada"):
            val = validar_acta_almacenada(db, acta.id)
            crit = [h for h in val.hallazgos if str(h.severidad) == "critico"]
            if crit:
                det = "; ".join(h.mensaje for h in crit)[:400]
                return {"respuesta": ("No puedo pasar %s a %s: tiene %s hallazgo(s) critico(s). "
                                      "Corrige: %s" % (acta.folio, destino, len(crit), det)),
                        "intencion": "aprobar", "tema_valido": True,
                        "acta": _dato_acta(acta), "validacion": val.model_dump(mode="json")}
        acta2 = actualizar_estatus(db, acta.id, destino)
        administracion.registrar_version(db, acta2, "Estatus a %s desde asistente" % destino)
        db.commit()
        db.refresh(acta2)
        return {"respuesta": ("Listo: %s ahora esta en %s (version %s)."
                              % (acta2.folio, destino, acta2.version)),
                "intencion": "aprobar", "tema_valido": True, "acta": _dato_acta(acta2),
                "acciones": [{"etiqueta": "Validar", "accion": "validar", "acta_id": acta2.id}]}
    if inten == "versiones":
        hist = administracion.listar_versiones(db, acta.id)
        lin = ["Historial de %s (%s versiones):" % (acta.folio, len(hist))]
        for v in hist[:8]:
            lin.append("  - v%s: %s [%s]" % (v.version, v.motivo, v.estatus))
        return {"respuesta": "\n".join(lin), "intencion": "versiones",
                "tema_valido": True, "acta": dato,
                "versiones": [{"version": v.version, "motivo": v.motivo,
                               "estatus": v.estatus} for v in hist],
                "acciones": [{"etiqueta": "Validar", "accion": "validar", "acta_id": acta.id}]}
    if inten == "restaurar":
        num = extraer_num_version(texto)
        if num is None:
            return {"respuesta": ("Que version restauro? Ejemplo: restaura %s a la version 1."
                                  % acta.folio),
                    "intencion": "restaurar", "tema_valido": True, "acta": dato}
        try:
            acta2 = administracion.restaurar_version(db, acta.id, num)
        except Exception as exc:
            return {"respuesta": "No pude restaurar: %s" % exc,
                    "intencion": "restaurar", "tema_valido": True, "acta": dato}
        return {"respuesta": ("Restaurada la version %s de %s: ahora es la version %s."
                              % (num, acta2.folio, acta2.version)),
                "intencion": "restaurar", "tema_valido": True, "acta": _dato_acta(acta2)}
    out = _redactar_libre(texto)
    out["tema_valido"] = True
    out["acta"] = dato
    return out


