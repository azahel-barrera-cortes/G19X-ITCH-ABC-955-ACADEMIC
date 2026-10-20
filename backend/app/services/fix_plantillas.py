import sys

with open('plantillas_legales.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line number of 'def redactar_con_plantilla'
start_idx = None
for i, line in enumerate(lines):
    if line.strip() == 'def redactar_con_plantilla(':
        start_idx = i
        break

if start_idx is None:
    print('No se encontró la función redactar_con_plantilla')
    sys.exit(1)

# Find where the function body ends (next def or class or end of file)
end_idx = None
for i in range(start_idx + 1, len(lines)):
    stripped = lines[i].strip()
    if stripped.startswith('def ') or stripped.startswith('class '):
        end_idx = i
        break
if end_idx is None:
    end_idx = len(lines)

# Build the new content
new_lines = lines[:start_idx]

# Insert new code before the function
new_code = '''class DatosPlantillaIncompletosError(Exception):
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


'''

new_lines.extend(new_code.splitlines(keepends=True))

# Now add the updated redactar_con_plantilla function
updated_func = '''def redactar_con_plantilla(
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

'''

new_lines.extend(updated_func.splitlines(keepends=True))
new_lines.extend(lines[end_idx:])

with open('plantillas_legales.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Reemplazo exitoso')
sys.exit(0)