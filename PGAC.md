### ROL Y CONTEXTO DEL PROYECTO
Actúa como un Arquitecto de Software Full Stack y Desarrollador Senior en Python y React.js.
Necesito que me ayudes a desarrollar la estructura base de código para una plataforma web LegalTech denominada **GICORP / PluriActas** ("Plataforma de Generación Inteligente de Actas Corporativas").

#### Objetivo de la Plataforma:
Automatizar la redacción, estructuración y exportación en PDF de actas corporativas (asambleas ordinarias, extraordinarias, aumentos de capital, etc.) cumpliendo con la legislación mercantil (ej. Ley General de Sociedades Mercantiles en México). La plataforma utiliza Inteligencia Artificial para redactar contenido legal complejo y validar consistencia, mientras que el renderizado final a PDF se ejecuta de forma determinista y estricta usando ReportLab.

---

### ARQUITECTURA TÉCNICA
1. **Backend**: Python 3.10+ con FastAPI.
2. **Base de Datos**: PostgreSQL (ORM con SQLAlchemy / Pydantic).
3. **Generación de PDF**: Python con ReportLab.
4. **Frontend**: React.js (Vite o Next.js) con Tailwind CSS para una interfaz limpia, profesional y moderna.
5. **Integración IA**: Servicio en Python que interactúa con API de LLM (ej. Azure OpenAI / Gemini API) para redactar cláusulas y validar consistencia documental.

---

### ENTREGABLES REQUERIDOS

Genera el código modular y bien documentado para los siguientes módulos:

#### 1. BACKEND (Python + FastAPI)
- **Estructura de Modelos (Pydantic / SQLAlchemy)**:
  - Modelo `Acta` (ID, Tipo de Asamblea, Fecha, Sociedad/Empresa, Asistentes, Orden del Día, Acuerdos, Estatus, Versión).
- **Endpoint Principal (`POST /api/v1/actas/generar-pdf`)**:
  - Endpoint que recibe los datos estructurados del formulario, solicita a la IA la redacción/validación del cuerpo legal, y ejecuta un script de **ReportLab** para compilar y retornar el archivo PDF binario.
- **Módulo de ReportLab (`pdf_generator.py`)**:
  - Una función `build_acta_pdf(data: dict) -> bytes` utilizando `SimpleDocTemplate`, `Paragraph`, `Table` y `Spacer` de ReportLab para maquetar un documento legal formal con encabezados, márgenes profesionales, firmas y número de página.
- **Módulo de Integración IA (`ai_service.py`)**:
  - Una función que reciba el resumen del acuerdo y genere la redacción legal adecuada usando un prompt estructurado.

#### 2. FRONTEND (React.js + Tailwind CSS)
- **Formulario Dinámico para Generación de Actas**:
  - Un componente React con formulario por pasos (Wizard) o pestañas:
    1. Datos Generales (Empresa, Fecha, Hora, Tipo de Asamblea).
    2. Asistentes y Quórum.
    3. Orden del Día y Acuerdos.
  - Botón de "Vista Previa / Generar borrador con IA".
  - Botón de "Descargar PDF Final".
- **Estado y Peticiones API**:
  - Uso de `fetch` / `axios` para enviar los datos al backend de FastAPI y recibir la respuesta del PDF en formato Blob para visualización/descarga directa en el navegador.

---

### INSTRUCCIONES DE ESTILO DE CÓDIGO
- Escribe código limpio, moderno y siguiendo las mejores prácticas (type hints en Python, componentes funcionales con Hooks en React).
- Incluye comentarios explicativos en puntos clave.
- Asegúrate de separar la responsabilidad de la IA (redacción textual) del maquetado del PDF (ReportLab).

Por favor, genera primero la estructura de carpetas sugerida y posteriormente el código correspondiente a cada archivo clave del Backend y Frontend.