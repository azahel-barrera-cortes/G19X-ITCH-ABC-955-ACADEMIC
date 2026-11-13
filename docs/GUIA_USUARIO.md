# Guía completa de usuario de PGAC

PGAC (Página de Gestión de Actas Corporativas) ayuda a capturar, redactar,
revisar y administrar actas corporativas. Esta guía describe el acceso, las
responsabilidades de cada rol, los dos caminos de creación y los límites que
deben considerarse al usar los documentos generados.

> PGAC es una herramienta de apoyo documental. No sustituye la revisión de un
> abogado ni la consulta de los documentos societarios originales.

## 1. Acceder al sistema

### Crear una cuenta vinculada a una empresa

1. En la pantalla de acceso, selecciona **Crear cuenta** o **Regístrate**.
2. Solicita al Administrador de tu empresa el código empresarial e introdúcelo
   en el formulario.
3. Registra tu correo, nombre completo, rol y una contraseña de al menos
   **12 caracteres**.
4. El registro público permite elegir **Capturista**, **Revisor** o
   **Abogado Responsable**. Elige el rol que te haya autorizado la empresa.
   **Administrador** y **SuperAdministrador** no están disponibles en el
   registro público; sus cuentas las asigna el SuperAdministrador.
5. Confirma la contraseña y selecciona **Registrarme**. Al completar el
   registro, PGAC inicia la sesión y abre el perfil.

El Administrador puede consultar el código de empresa en la administración de
usuarios o en su perfil, y puede crear cuentas operativas para su empresa. El
SuperAdministrador gestiona las cuentas globales, incluida la creación o
asignación de cuentas con roles administrativos.

### Iniciar sesión o recuperar el acceso

- En **Iniciar sesión**, introduce el correo registrado y la contraseña.
- Si olvidaste la contraseña, selecciona **¿Olvidaste tu contraseña?** y sigue
  las instrucciones enviadas al correo. La recuperación requiere que el correo
  del sistema esté configurado. Si no recibes el mensaje, contacta al
  administrador correspondiente.
- Las cuentas desactivadas no pueden iniciar sesión. Contacta al Administrador
  de tu empresa; para una cuenta de Administrador, contacta al
  SuperAdministrador.
- Para cambiar la contraseña desde **Mi perfil**, introduce la contraseña
  actual y una nueva de al menos 12 caracteres. El cambio cierra la sesión y
  tendrás que volver a iniciar sesión.
- En equipos compartidos, cierra la sesión al terminar.

Los usuarios operativos llegan a **Mi perfil** al acceder. El
**SuperAdministrador** llega directamente a la administración global. La barra
de navegación muestra únicamente las secciones correspondientes al rol; los
permisos también se comprueban en el servidor.

## 2. Actividades por rol

| Rol | Responsabilidades y secciones principales | Límites principales |
|---|---|---|
| **Capturista** | Crear actas desde **Generar acta** o **Asistente IA**; consultar el avance en **Mis actas**; atender observaciones y enviar versiones corregidas. | No decide la revisión ni la aprobación legal y no descarga el PDF final antes de la aprobación del Abogado Responsable. |
| **Revisor** | Atender **Revisión de actas**; consultar versiones; analizar consistencia; devolver con observaciones o marcar el acta como revisada para enviarla al Abogado. Puede consultar la **Biblioteca de actas**. | No realiza la aprobación legal final. La aprobación y descarga del PDF final corresponden al Abogado Responsable. |
| **Abogado Responsable** | Atender **Aprobación de actas**; revisar el documento, versiones y análisis; aprobarlo finalmente o devolverlo con observaciones. Después de aprobar, puede descargar el PDF final desde su bandeja o la Biblioteca. | La aprobación es una decisión profesional humana. El sistema no firma el documento ni lo protocoliza. |
| **Administrador** | Administrar usuarios de su empresa y sus roles operativos; mantener la información empresarial del perfil; consultar la Biblioteca y gestionar información de actas, versiones y caducidad. | Su administración es de ámbito empresarial. No sustituye las decisiones de revisión del Revisor ni la aprobación del Abogado. El SuperAdministrador gestiona el sistema globalmente. |
| **SuperAdministrador** | Administrar usuarios, roles y accesos globales; consultar la Bitácora y supervisar cuentas de todo el sistema. | Las secciones **Estadísticas** y **Seguridad** actualmente indican «En construcción» y no ofrecen controles operativos. |

### Ruta usual de revisión

1. El Capturista envía un borrador y este llega a **Revisión de actas**.
2. El Revisor puede devolverlo con observaciones o marcarlo como revisado para
   que pase a **Aprobación de actas**.
3. El Abogado Responsable puede aprobarlo o devolverlo al Capturista.
4. Si el Revisor devuelve el acta, la nueva versión vuelve al Revisor. Si la
   devolución fue del Abogado, la corrección vuelve directamente al Abogado.
5. Cada corrección guardada genera una nueva versión; el historial conserva las
   versiones anteriores.

## 3. Generar un acta con el formulario manual

1. En el menú, abre **Generar acta**.
2. En **Formulario manual**, selecciona **Iniciar formulario**. Si prefieres
   partir de una estructura, busca una plantilla sugerida o abre el catálogo
   completo y selecciona **Usar plantilla**. La plantilla precarga el tipo de
   asamblea, pero debes revisar y completar los datos.
3. Completa los cuatro pasos. Puedes volver a pasos anteriores para corregir
   información antes de enviar.

### Paso 1: Datos generales

- Verifica la razón social y el tipo de sociedad. Si el Administrador configuró
  el uso de la información empresarial, algunos datos se precargan y quedan en
  modo de consulta.
- Elige el tipo de acta compatible con la sociedad. Los requisitos jurídicos
  específicos cambian según el tipo seleccionado.
- Completa los datos requeridos, como fecha, lugar y los datos de convocatoria
  o materia que solicite el formulario. Revisa cuidadosamente nombres, fechas y
  referencias legales.

### Paso 2: Asistentes y quórum

- Registra el capital social, el total de acciones y el capital representado.
- Captura a cada asistente, su carácter o representación y las acciones o
  porcentaje que le corresponden. Registra la presidencia y secretaría de la
  asamblea.
- PGAC calcula el quórum con los valores capturados y muestra advertencias.
  Comprueba el cálculo contra los libros, poderes y documentos fuente; una
  cifra calculada no acredita por sí sola la validez de la asamblea.

### Paso 3: Orden del día y acuerdos

- Agrega los puntos en el orden en que se trataron, con título y descripción.
- Agrega los acuerdos correspondientes y captura la votación, la mayoría y los
  resultados aplicables.
- Atiende advertencias sobre acuerdos que no correspondan a un punto del orden
  del día. Añade observaciones o salvedades cuando proceda.

### Paso 4: Revisión y envío

- Revisa el resumen del acta, las opciones de redacción y validación y la vista
  previa.
- **Generar borrador con IA** redacta las cláusulas y muestra el resultado de
  validación para que lo revises. También puedes agregar instrucciones
  opcionales para la redacción.
- **Ver redacción en vivo** muestra una vista progresiva de la redacción del
  primer acuerdo; no sustituye la generación del borrador completo.
- Corrige los datos y hallazgos antes de seleccionar **Enviar a revisión**.
  Enviar guarda el acta y la coloca en la bandeja del Revisor. El borrador
  generado antes de enviarlo es una vista previa y no equivale al PDF final.

## 4. Generar un acta con el Asistente IA

1. Abre **Asistente IA** desde el menú de Capturista, o selecciona
   **Abrir asistente IA** en la pantalla **Generar acta**.
2. Inicia la creación con una instrucción como **«Quiero crear un acta»**.
   Responde las preguntas del asistente con información verificable de la
   sociedad y de la asamblea.
3. Cuando muestre el resumen, comprueba los datos antes de continuar. Usa
   **Corregir un dato** o describe en el chat qué debe cambiarse.
4. Selecciona **Confirmar y enviar a revisión** solo cuando el resumen sea
   correcto. La confirmación guarda el acta y la envía al flujo de revisión.
5. Da seguimiento desde **Mis actas**. Las observaciones y correcciones se
   atienden según el rol que devolvió el documento.

El asistente también presenta respuestas y acciones que dependen del rol y de
la solicitud; no todas las acciones están disponibles para todas las cuentas.
Cuando ofrece un borrador para llevar al formulario, revisa y completa los
campos restantes en el formulario antes de enviarlo.

## 5. PDF final y firmas

- El Capturista envía un **borrador**; ese envío no genera el PDF final.
- El PDF final se habilita después de la aprobación del Abogado Responsable.
  El Abogado puede descargarlo desde **Aprobación de actas** o desde la
  **Biblioteca de actas**.
- El PDF queda listo para imprimir. PGAC no recaba firmas electrónicas ni
  sustituye las firmas manuscritas, la formalización o la protocolización que
  correspondan; esos pasos se realizan fuera del sistema.

## 6. Limitaciones y buenas prácticas

1. **La IA puede equivocarse.** Puede producir texto incompleto, inexacto o
   inadecuado para el caso. Revisa cláusulas, nombres, fechas, cifras,
   votaciones y fundamento jurídico antes de enviar.
2. **La validación es de consistencia, no una opinión legal.** Las reglas y el
   análisis asistido pueden señalar problemas, pero no certifican la validez
   del acta ni sustituyen la revisión profesional.
3. **La redacción depende de la configuración.** PGAC puede usar un proveedor
   de IA configurado o recurrir a plantillas legales deterministas si no hay
   proveedor disponible o si falla. El respaldo con plantillas no significa
   que el sistema funcione sin backend o base de datos.
4. **Cuida la información sensible.** Si la empresa usa un proveedor externo
   de IA, confirma las políticas de tratamiento de datos antes de incluir
   información personal o confidencial que no sea necesaria.
5. **No se incorporan documentos fuente automáticamente.** Introduce y
   verifica los datos con base en el acta constitutiva, estatutos, libros,
   poderes, convocatorias y demás fuentes aplicables.
6. **No hay firma electrónica ni protocolización en PGAC.** La descarga del
   PDF no implica que las partes hayan firmado o que el documento se haya
   formalizado ante fedatario.
7. **La disponibilidad de algunas funciones depende de la configuración.**
   La recuperación de contraseña requiere correo configurado y las secciones
   globales de Estadísticas y Seguridad aún están en construcción.
8. **Las acciones administrativas pueden ser irreversibles.** Antes de
   eliminar un acta, restaurar una versión o cambiar su caducidad, confirma el
   expediente y el motivo. Restaurar una versión crea una versión nueva; no
   borra el historial.

## 7. Ayuda rápida

- **No puedo iniciar sesión:** confirma el correo, solicita recuperación o
  contacta al administrador si la cuenta está desactivada.
- **No aparece una sección:** confirma el rol asignado; el menú cambia según
  los permisos.
- **No puedo enviar el acta:** vuelve a los pasos marcados, completa los datos
  requeridos y corrige los errores de validación.
- **El borrador indica que se usaron plantillas:** la IA externa puede no estar
  configurada o no haber respondido. Revisa el texto igualmente; el respaldo
  no elimina la revisión humana.
- **Necesito descargar el PDF final:** verifica que el Abogado Responsable ya
  haya aprobado el acta.
