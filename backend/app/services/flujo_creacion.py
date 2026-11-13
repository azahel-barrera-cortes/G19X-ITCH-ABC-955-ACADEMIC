"""Flujo guiado de creacion de actas desde el asistente (sesiones en memoria)."""
from __future__ import annotations
import re, uuid, unicodedata
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from app.core.catalogos import (
    TIPOS_ASAMBLEA,
    TIPOS_SOCIEDAD,
    acta_aplicable,
    requisitos_acta,
)
__all__ = ["TIPOS_GUIA", "CAMPOS_REQUERIDOS", "crear_sesion", "obtener_sesion",
 "reiniciar_sesion", "detectar_tipo_en_texto", "siguiente_faltante",
 "extraer_datos", "sesion_lista", "construir_payload_desde_sesion",
 "texto_catalogo_tipos", "detectar_tipo_sociedad_en_texto",
 "campos_requeridos_para_sesion"]
TIPOS_GUIA: List[Dict[str, Any]] = [
 {"valor": i["valor"], "etiqueta": i["etiqueta"],
  "descripcion": i.get("descripcion", ""),
  "articulos": list(i.get("articulos") or [])} for i in TIPOS_ASAMBLEA]
CAMPOS_REQUERIDOS: List[Dict[str, str]] = [
 {"clave": "tipo_sociedad", "etiqueta": "tipo de sociedad",
  "pregunta": "¿Qué tipo de sociedad es? Ej.: Sociedad Anónima de Capital Variable.",
  "ejemplo": "sociedad_anonima_capital_variable"},
 {"clave": "sociedad", "etiqueta": "sociedad (razon social)",
  "pregunta": "¿Cuál es la razón social completa? Ej.: Comercializadora del Norte, S.A. de C.V.",
  "ejemplo": "Comercializadora del Norte, S.A. de C.V."},
 {"clave": "fecha", "etiqueta": "fecha (AAAA-MM-DD)",
  "pregunta": "¿Qué día se celebró la asamblea? Ej.: 15 de marzo de 2026.",
  "ejemplo": "2026-03-15"},
 {"clave": "lugar", "etiqueta": "lugar",
  "pregunta": "¿En qué lugar se celebró? Incluye el domicilio.",
  "ejemplo": "Av. Reforma 1234, CDMX"},
 {"clave": "presidente", "etiqueta": "presidente",
  "pregunta": "¿Quién presidió la asamblea? (nombre completo).",
  "ejemplo": "Ana Maria Ruiz Salazar"},
 {"clave": "secretario", "etiqueta": "secretario",
  "pregunta": "¿Quién actuó como secretario? (nombre completo).",
  "ejemplo": "Carlos Pena Dominguez"},
 {"clave": "asistentes", "etiqueta": "asistentes y acciones",
  "pregunta": "Indica asistentes y acciones. Ej.: Ana Ruiz 50000, Carlos Peña 20000.",
  "ejemplo": "Ana Ruiz 50000, Carlos Pena 20000"},
 {"clave": "orden_y_acuerdos", "etiqueta": "orden del dia y acuerdos",
  "pregunta": "¿Qué puntos se trataron y qué se acordó? Puedes enumerarlos.",
  "ejemplo": "Aumento de capital en $500,000"},
]
_SESIONES: Dict[str, Dict[str, Any]] = {}
_MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
 "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9,
 "octubre": 10, "noviembre": 11, "diciembre": 12}
def _norm(t: str) -> str:
 d = unicodedata.normalize("NFKD", (t or "").lower())
 return "".join(c for c in d if not unicodedata.combining(c))
def texto_catalogo_tipos() -> str:
 lin = ["Te ayudo a elegir. Tipos de acta disponibles:"]
 for it in TIPOS_GUIA:
  arts = ", ".join(it["articulos"]) if it["articulos"] else ""
  ex = f" [{arts}]" if arts else ""
  lin.append(f"- {it['etiqueta']} ({it['valor']}): {it['descripcion']}{ex}")
 lin.append("Dime cual quieres crear (Ej. ordinaria o quiero un aumento de capital).")
 return "\n".join(lin)
def detectar_tipo_en_texto(texto: str) -> Optional[str]:
 n = _norm(texto or "")
 for it in TIPOS_GUIA:
  if _norm(it["valor"]).replace("_", " ") in n or _norm(it["etiqueta"]) in n:
   return str(it["valor"])
 sin = {"aumento_capital": ("aumento de capital", "aumentar capital"),
  "reduccion_capital": ("reduccion de capital", "reducir capital"),
  "constitutiva": ("constitutiva", "constituir sociedad", "crear sociedad"),
  "ordinaria": ("ordinaria", "estados financieros", "informe anual"),
  "extraordinaria": ("extraordinaria", "reforma estatut"),
  "mixta": ("mixta",), "fusion": ("fusion",), "escision": ("escision",),
  "disolucion_liquidacion": ("disolucion", "liquidacion"),
  "sesion_consejo": ("consejo",)}
 for v, fs in sin.items():
  if any(_norm(f) in n for f in fs):
   return v
 return None

def detectar_tipo_sociedad_en_texto(texto: str) -> Optional[str]:
 n = _norm(texto or "")
 for it in TIPOS_SOCIEDAD:
  if (
   _norm(it["valor"]).replace("_", " ") in n
   or _norm(it["etiqueta"]) in n
   or _norm(it.get("abreviatura", "")) in n
  ):
   return str(it["valor"])
 return None
def crear_sesion(
 tipo=None,
 *,
 usuario_id: Optional[int] = None,
 empresa_codigo: Optional[str] = None,
) -> Dict[str, Any]:
 sid = uuid.uuid4().hex[:12]
 s = {"sesion_id": sid, "tipo_asamblea": tipo, "datos": {},
      "respuestas": [],
      "etapa": "tipo" if not tipo else "datos",
   "usuario_id": usuario_id,
   "empresa_codigo": empresa_codigo,
      "creada_en": datetime.utcnow().isoformat()}
 _SESIONES[sid] = s
 return s
def obtener_sesion(
 sid: Optional[str],
 *,
 usuario_id: Optional[int] = None,
 empresa_codigo: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
 sesion = _SESIONES.get(sid) if sid else None
 if sesion is None:
  return None
 if usuario_id is not None and (
  sesion.get("usuario_id") != usuario_id
  or sesion.get("empresa_codigo") != empresa_codigo
 ):
  return None
 return sesion
def reiniciar_sesion(
 sid: Optional[str],
 *,
 usuario_id: Optional[int] = None,
 empresa_codigo: Optional[str] = None,
) -> None:
 if obtener_sesion(
  sid, usuario_id=usuario_id, empresa_codigo=empresa_codigo
 ) is not None:
  del _SESIONES[sid]
def siguiente_faltante(sesion: Dict[str, Any]) -> Optional[Dict[str, str]]:
 datos = sesion.get("datos", {})
 for c in campos_requeridos_para_sesion(sesion):
  v = datos.get(c["clave"])
  if v in (None, "", [], {}):
   return c
 return None

def campos_requeridos_para_sesion(sesion: Dict[str, Any]) -> List[Dict[str, str]]:
 """Combina captura común y requisitos del acta/sociedad seleccionados."""
 tipo = str(sesion.get("tipo_asamblea") or "ordinaria")
 sociedad = sesion.get("datos", {}).get("tipo_sociedad")
 comunes = list(CAMPOS_REQUERIDOS)
 especificos = [
     {
         "clave": requisito["clave"],
         "etiqueta": requisito["etiqueta"],
         "pregunta": requisito["pregunta"],
         "ejemplo": "Proporciona el dato completo y verificable.",
     }
     for requisito in requisitos_acta(tipo, sociedad)
 ]
 return comunes + especificos
def sesion_lista(sesion: Dict[str, Any]) -> bool:
 return bool(sesion.get("tipo_asamblea")) and siguiente_faltante(sesion) is None
def _extraer_fecha(t: str):
 m = re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", t or "")
 if m:
  try:
   return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
  except ValueError:
   pass
 m2 = re.search(r"(\d{1,2})\s+de\s+([a-z]+)\s+(?:de\s+)?(20\d{2})", _norm(t or ""))
 if m2:
  mes = _MESES.get(m2.group(2).strip())
  if mes:
   try:
    return date(int(m2.group(3)), mes, int(m2.group(1))).isoformat()
   except ValueError:
    return None
 return None
def _nombres_acciones(t: str):
 partes = re.split(r"[;\n]+", t or "")
 if len(partes) == 1 and "," in t and re.search(r"\d", t):
  partes = [p.strip() for p in t.split(",")]
 out = []
 for p in partes:
  p = p.strip(" .-")
  if len(p) < 3:
   continue
  m = re.search(r"([\d,]+)\s*(acciones?)?\s*$", p, re.IGNORECASE)
  acc, nom = 0.0, p
  if m:
   try:
    acc = float(m.group(1).replace(",", ""))
   except ValueError:
    acc = 0.0
   nom = p[: m.start()].strip(" ,-:")
  if len(nom) < 3 or re.search(r"\d{4}-\d{2}-\d{2}", nom):
   continue
  out.append({"nombre": nom.title(), "acciones": acc})
 return out
def extraer_datos(texto: str, clave: Optional[str] = None) -> Dict[str, Any]:
 t = (texto or "").strip()
 if not t:
  return {}
 if clave == "sociedad" and len(t) >= 3:
  return {"sociedad": t}
 if clave == "tipo_sociedad":
  tipo = detectar_tipo_sociedad_en_texto(t)
  return {"tipo_sociedad": tipo} if tipo else {}
 if clave == "fecha":
  f = _extraer_fecha(t)
  return {"fecha": f} if f else {}
 if clave == "lugar" and len(t) >= 3:
  return {"lugar": t}
 if clave in ("presidente", "secretario") and len(t) >= 3:
  nom = re.split(r":", t, maxsplit=1)[-1].strip()
  return {clave: nom.title()} if len(nom) >= 3 else {}
 if clave == "asistentes":
  a = _nombres_acciones(t)
  return {"asistentes": a} if a else {}
 if clave == "orden_y_acuerdos" and len(t) >= 5:
  return {"orden_y_acuerdos": t}
 if clave and clave not in {campo["clave"] for campo in CAMPOS_REQUERIDOS} and len(t) >= 3:
  return {clave: t}
 f = _extraer_fecha(t)
 return {"fecha": f} if f else {}
def _acuerdos_desde_texto(texto: str):
 frags = [p.strip(" .-") for p in re.split(r"[;\n]+", texto or "") if p.strip(" .-")]
 if len(frags) <= 1:
  frags = [p.strip() for p in re.split(r"(?=\b\d+\s*[.)\-]\s*)", texto or "") if p.strip()]
  frags = [re.sub(r"^\d+\s*[.)\-]\s*", "", f) for f in frags if len(f.strip()) > 3]
 if not frags:
  frags = [texto.strip()]
 orden, ac = [], []
 for i, fr in enumerate(frags[:6], start=1):
  tit = fr[:120]
  mm = re.search(r"\$\s*([\d,]+\.?\d*)", fr)
  res = fr
  if mm and "capital" in _norm(fr):
   res = f"Aumentar el capital social en ${mm.group(1)}: {fr}"
  orden.append({"numero": i, "titulo": tit, "descripcion": fr, "requiere_votacion": True})
  ac.append({"numero": i, "titulo": tit, "resumen": res,
             "votacion": {"tipo_mayoria": "unanimidad", "aprobado": True}})
 return orden, ac
def construir_payload_desde_sesion(sesion: Dict[str, Any]) -> Dict[str, Any]:
 datos = sesion.get("datos", {})
 tipo = sesion.get("tipo_asamblea") or "ordinaria"
 crudos = datos.get("asistentes") or []
 asist = []
 for i, a in enumerate(crudos):
  asist.append({"nombre": a.get("nombre", ""),
   "caracter": "presidente" if i == 0 else ("secretario" if i == 1 else "propietario"),
   "acciones": float(a.get("acciones") or 0),
   "es_presidente": i == 0, "es_secretario": i == 1})
 total = sum(float(a.get("acciones") or 0) for a in asist)
 orden, ac = _acuerdos_desde_texto(str(datos.get("orden_y_acuerdos") or ""))
 pres = str(datos.get("presidente") or "")
 sec = str(datos.get("secretario") or "")
 return {"sociedad": str(datos.get("sociedad") or ""),
  "tipo_asamblea": tipo,
  "tipo_sociedad": datos.get("tipo_sociedad"),
  "titulo": f"Acta de {tipo.replace('_', ' ')} - {datos.get('sociedad', '')}"[:200],
  "fecha": datos.get("fecha"), "lugar": str(datos.get("lugar") or ""),
  "presidente": pres, "secretario": sec, "asistentes": asist,
  "orden_del_dia": orden, "acuerdos": ac,
  "capital_social": total or None, "acciones_totales": total or None,
  "datos_especificos": {
      clave: valor
      for clave, valor in datos.items()
      if clave not in {campo["clave"] for campo in CAMPOS_REQUERIDOS}
      and valor not in (None, "", [], {})
   },
   "datos_asistente": {
       "tipo_asamblea": tipo,
       "datos": dict(datos),
       "respuestas": list(sesion.get("respuestas") or []),
    },
   "observaciones": (
       "Borrador creado con acompañamiento del asistente. "
       "Requiere revisión de abogado o notario antes de firma, protocolización o inscripción."
   ),
  "guardar": True}
