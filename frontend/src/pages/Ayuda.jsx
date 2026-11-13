import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'
import { etiquetaGuiaRol } from '../constants/roles.js'

const ENDPOINTS = [
  ['GET', '/api/v1/actas/catalogos', 'Catálogos de tipos de asamblea, mayorías, caracteres y estatus.'],
  ['POST', '/api/v1/actas/redactar', 'Genera el borrador con IA y la validación (no persiste ni exporta).'],
  ['POST', '/api/v1/actas', 'Guarda el borrador y lo envía a la bandeja del Revisor.'],
  ['GET', '/api/v1/actas/bandeja', 'Consulta las actas propias o pendientes según el rol.'],
  ['POST', '/api/v1/actas/{id}/decision', 'Aprueba o devuelve el acta en su etapa actual.'],
  ['POST', '/api/v1/actas/{id}/reenviar', 'Reenvía la nueva versión a la etapa que solicitó la corrección.'],
  ['POST', '/api/v1/actas/generar-pdf', 'Genera una vista previa no persistida.'],
  ['GET', '/api/v1/actas', 'Historial de actas con filtros y paginación.'],
  ['GET', '/api/v1/actas/{id}', 'Acta completa, con sus cláusulas y su validación.'],
  ['PUT', '/api/v1/actas/{id}', 'Guarda las correcciones del Capturista y crea una versión.'],
  ['PATCH', '/api/v1/actas/{id}/estatus', 'Registra estados posteriores a la aprobación final.'],
  ['GET', '/api/v1/actas/{id}/pdf', 'Genera el PDF final solo después de la aprobación legal.'],
  ['POST', '/api/v1/actas/{id}/validar', 'Vuelve a validar la consistencia del acta.'],
  ['DELETE', '/api/v1/actas/{id}', 'Elimina el acta del historial.'],
  ['GET', '/api/v1/administracion/resumen', 'Totales del repositorio, por estatus y por vigencia.'],
  ['GET', '/api/v1/administracion/vigencia', 'Actas por vigencia: vencida, por vencer, vigente o sin fecha.'],
  ['GET', '/api/v1/administracion/versiones/{id}', 'Historial de versiones de un acta (más reciente primero).'],
  ['GET', '/api/v1/administracion/versiones/{id}/{n}', 'Contenido completo de una versión concreta.'],
  ['POST', '/api/v1/administracion/versiones/{id}/{n}/restaurar', 'Restaura la versión y emite una nueva.'],
  ['PUT', '/api/v1/administracion/caducidad/{id}', 'Fija, amplía o elimina la fecha de caducidad.'],
  ['GET', '/api/v1/sistema/estado', 'Estado de la base de datos y del proveedor de IA.'],
]

function GuiaCuenta({ rol }) {
  const responsable = rol === 'Administrador'
    ? 'al SuperAdministrador'
    : 'al Administrador de tu empresa'

  return (
    <Tarjeta>
      <TarjetaEncabezado
        titulo="Acceso y seguridad de tu cuenta"
        descripcion="Protege tus credenciales y conserva el acceso a tu rol"
      />
      <TarjetaCuerpo>
        <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
          <li>Desde Mi perfil puedes cambiar tu contraseña; las nuevas contraseñas deben tener al menos 12 caracteres. Después del cambio, inicia sesión de nuevo.</li>
          <li>Si olvidaste la contraseña, usa ¿Olvidaste tu contraseña? en la pantalla de acceso. La recuperación depende de que el correo del sistema esté configurado.</li>
          <li>No compartas tu contraseña. Si no puedes acceder o tu cuenta está desactivada, contacta {responsable}.</li>
        </ul>
      </TarjetaCuerpo>
    </Tarjeta>
  )
}

/** Sección «Guía de uso»: flujo de trabajo, API y notas legales. */
export default function Ayuda({ catalogos, rol }) {
  const titulo = etiquetaGuiaRol(rol)

  if (rol === 'capturista') {
    return (
      <div className="space-y-5">
        <header className="rounded-2xl bg-gradient-to-r from-corporativo-700 to-corporativo-500 px-6 py-7 text-white shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">
            Centro de ayuda · Capturista
          </p>
          <h1 className="mt-2 text-2xl font-bold">{titulo}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/90">
            Guía para crear actas, dar seguimiento a su revisión y preparar nuevas versiones cuando
            el Revisor o el Abogado solicite cambios.
          </p>
        </header>

        <p className="rounded-lg border border-corporativo-100 bg-corporativo-50 px-4 py-3 text-sm leading-relaxed text-corporativo-800">
          El registro solicita el código de tu empresa y permite elegir Capturista, Revisor o
          Abogado Responsable. Los roles Administrador y SuperAdministrador requieren que el
          SuperAdministrador cree o actualice la cuenta. Si ya tienes acceso, inicia sesión con el
          correo registrado.
        </p>

        <section className="grid gap-3 md:grid-cols-3">
          {[
            ['Generar acta', 'Empieza desde una plantilla, con el formulario manual o con redacción asistida por IA.'],
            ['Mis actas', 'Consulta el estado, las observaciones y el historial de tus actas.'],
            ['Asistente IA', 'Recopila datos conversando y ayuda a crear o editar un borrador.'],
          ].map(([encabezado, descripcion]) => (
            <article key={encabezado} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="font-semibold text-corporativo-700">{encabezado}</h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">{descripcion}</p>
            </article>
          ))}
        </section>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Crear y enviar un acta"
            descripcion="Elige el modo de captura que se adapte al documento"
          />
          <TarjetaCuerpo>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-xl border border-corporativo-200 bg-corporativo-50/60 p-4">
                <h3 className="font-semibold text-corporativo-800">Formulario manual</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">
                  En Generar acta puedes iniciar desde cero o seleccionar una plantilla. Completa
                  los cuatro pasos: datos generales, asistentes y quórum, orden del día y acuerdos,
                  y revisión del borrador antes de enviarlo. Los requisitos jurídicos dependen del
                  tipo de asamblea.
                </p>
              </div>
              <div className="rounded-xl border border-acento-400/50 bg-acento-50 p-4">
                <h3 className="font-semibold text-corporativo-800">Asistente IA</h3>
                <p className="mt-1 text-sm leading-relaxed text-slate-600">
                  Describe la asamblea y responde las preguntas del chat. Revisa los datos propuestos
                  y las cláusulas antes de enviar el acta a revisión.
                </p>
              </div>
            </div>
            <ol className="mt-5 space-y-3">
              {[
                ['Completa los datos generales', 'Captura sociedad, fecha, lugar, convocatoria y los datos jurídicos específicos que solicita el tipo de acta.'],
                ['Registra asistentes y quórum', 'Verifica capital, acciones, representación y cargos de la mesa contra los documentos fuente.'],
                ['Agrega orden del día y acuerdos', 'Incluye cada punto, el resumen de la decisión y los datos de votación que correspondan.'],
                ['Revisa y envía', 'En Revisión y PDF genera o completa las cláusulas, consulta la validación y revisa la vista previa. Después de pulsar Enviar a revisión, consulta el avance en Mis actas.'],
              ].map(([encabezado, descripcion], indice) => (
                <li key={encabezado} className="flex gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-corporativo-100 text-sm font-bold text-corporativo-700">
                    {indice + 1}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800">{encabezado}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{descripcion}</p>
                  </div>
                </li>
              ))}
            </ol>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Corregir un acta devuelta"
            descripcion="Las correcciones se realizan desde Mis actas y siempre generan una versión nueva"
          />
          <TarjetaCuerpo>
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>En Mis actas, localiza el registro con estado Con errores y lee las observaciones del Revisor o del Abogado.</li>
              <li>Pulsa Editar y corregir. La edición está disponible cuando el acta fue devuelta con errores; la sociedad y el tipo de acta permanecen bloqueados.</li>
              <li>Corrige los campos necesarios en el formulario. Puedes aplicar propuestas del asistente IA, pero revísalas antes de guardar.</li>
              <li>Guarda los cambios para crear una versión nueva. Si te devolvió el Revisor, vuelve a su bandeja; si te devolvió el Abogado, se envía directamente a Aprobación.</li>
            </ol>
            <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              Cada versión conserva el historial. No envíes una corrección sin revisar que responda
              a las observaciones recibidas.
            </p>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Asistente IA y límites del rol"
            descripcion="Apoyo de captura sin reemplazar la verificación humana"
          />
          <TarjetaCuerpo>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>El asistente ayuda a recopilar datos y proponer redacción; verifica nombres, fechas, cifras, votaciones y fundamento legal.</li>
              <li>Si la IA externa no está configurada, PGAC puede usar plantillas y validaciones locales.</li>
              <li>No puedes aprobar un acta ni generar el PDF final oficial. El Revisor y luego el Abogado atienden esas etapas.</li>
              <li>El PDF final se habilita después de la aprobación del Abogado Responsable y queda listo para imprimir. PGAC no recaba firmas electrónicas; las firmas manuscritas y formalizaciones que correspondan se realizan fuera del sistema.</li>
            </ul>
            <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Proveedor configurado: <strong>{catalogos?.proveedor_ia || 'plantillas'}</strong>
              {' · '}
              {catalogos?.ia_habilitada ? 'IA externa habilitada' : 'modo de plantillas locales'}.
            </p>
          </TarjetaCuerpo>
        </Tarjeta>
        <GuiaCuenta rol={rol} />
      </div>
    )
  }

  if (rol === 'Administrador') {
    return (
      <div className="space-y-5">
        <header className="rounded-2xl bg-gradient-to-r from-corporativo-700 to-corporativo-500 px-6 py-7 text-white shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">
            Centro de ayuda · Administración de empresa
          </p>
          <h1 className="mt-2 text-2xl font-bold">{titulo}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/90">
            Guía para administrar los accesos de tu empresa y mantener ordenados los expedientes,
            versiones e información de vigencia de las actas.
          </p>
        </header>

        <section className="grid gap-3 md:grid-cols-3">
          {[
            ['Administración de usuarios', 'Crea cuentas vinculadas a la empresa y gestiona roles y accesos.'],
            ['Administración de actas', 'Consulta métricas, vigencia, caducidad y versiones del repositorio.'],
            ['Biblioteca de actas', 'Busca registros, consulta actas, valida su consistencia y descarga PDFs aprobados.'],
          ].map(([encabezado, descripcion]) => (
            <article key={encabezado} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="font-semibold text-corporativo-700">{encabezado}</h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">{descripcion}</p>
            </article>
          ))}
        </section>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Administrar los usuarios de la empresa"
            descripcion="Acciones disponibles en Administración de usuarios"
          />
          <TarjetaCuerpo>
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>Consulta el código de empresa y el resumen de usuarios activos y desactivados.</li>
              <li>Usa la búsqueda por nombre o correo y filtra por rol o estado de acceso.</li>
              <li>Con Agregar usuario registra nombre, correo, contraseña temporal de al menos 12 caracteres y rol. Los roles asignables en la empresa son Capturista, Revisor y Abogado.</li>
              <li>Con Modificar puedes actualizar nombre, rol o contraseña; el correo existente no se cambia desde esta pantalla.</li>
              <li>Usa Desactivar acceso o Reactivar acceso para revocar o restablecer el inicio de sesión sin eliminar el perfil.</li>
            </ol>
            <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Asigna cada rol según las responsabilidades de la persona y desactiva accesos que ya
              no deban utilizarse.
            </p>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Configurar la información de la empresa"
            descripcion="Los datos del perfil pueden reutilizarse en las actas de la empresa"
          />
          <TarjetaCuerpo>
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>Abre Mi perfil y revisa la sección Información de la empresa o sociedad.</li>
              <li>Captura la razón social y el tipo de sociedad; el RFC y el logo son opcionales.</li>
              <li>Guarda la información y activa Usar esta información al generar el acta si quieres precargarla en nuevos documentos. El resto de los usuarios puede consultarla, pero solo el Administrador puede modificarla.</li>
            </ol>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Administración de actas y vigencia"
            descripcion="Control de expedientes sin cambiar las decisiones de revisión"
          />
          <TarjetaCuerpo>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li><strong>Resumen:</strong> consulta total de actas, versiones registradas, vencidas y próximas a vencer.</li>
              <li><strong>Caducidad:</strong> filtra por estado de vigencia; fija, amplía o quita un plazo y registra el motivo.</li>
              <li><strong>Versiones:</strong> abre el historial para ver el contenido de cada versión o restaurar una anterior. Restaurar emite una versión nueva; no borra el historial ni retrocede el contador.</li>
              <li><strong>Bitácora de actas:</strong> consulta actividad reciente de creación, revisión y cambios sobre expedientes.</li>
            </ul>
            <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              Cambiar la vigencia o restaurar contenido genera una nueva versión. Verifica el
              expediente y el motivo antes de guardar el cambio.
            </p>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Biblioteca de actas"
            descripcion="Consulta del repositorio y acciones disponibles por registro"
          />
          <TarjetaCuerpo>
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>Busca por folio, sociedad o título; acota los resultados por tipo de asamblea y estatus.</li>
              <li>Usa Ver acta para abrir el documento y Analizar con IA para ejecutar o consultar la validación de consistencia.</li>
              <li>La tarjeta de análisis muestra proveedor, puntaje, hallazgos y recomendaciones; puedes contraerla y volverla a abrir.</li>
              <li>Las actas aprobadas permiten descargar el PDF final. La aprobación se realiza desde la bandeja del Abogado, no desde Biblioteca.</li>
              <li>Eliminar quita el acta del historial y no se puede deshacer. Confirma la selección antes de proceder.</li>
            </ol>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Límites y responsabilidades"
            descripcion="Administración del repositorio y accesos de la empresa"
          />
          <TarjetaCuerpo>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>La administración de usuarios se limita a las cuentas de la empresa; la superadministración global corresponde al SuperAdministrador.</li>
              <li>La validación asistida es orientativa; confirma la información contra los documentos societarios.</li>
              <li>Las decisiones de revisión y aprobación legal corresponden al Revisor y al Abogado Responsable.</li>
              <li>Puedes consultar y descargar actas aprobadas desde la Biblioteca, pero no aprobarlas ni emitir decisiones de revisión.</li>
            </ul>
          </TarjetaCuerpo>
        </Tarjeta>
        <GuiaCuenta rol={rol} />
      </div>
    )
  }

  if (rol === 'abogado_responsable') {
    return (
      <div className="space-y-5">
        <header className="rounded-2xl bg-gradient-to-r from-corporativo-700 to-corporativo-500 px-6 py-7 text-white shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">
            Centro de ayuda · Abogado Responsable
          </p>
          <h1 className="mt-2 text-2xl font-bold">{titulo}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/90">
            Guía para revisar las actas, solicitar correcciones, consultar versiones y aprobar el
            documento final desde las secciones de Aprobación y Biblioteca.
          </p>
        </header>

        <section className="grid gap-3 md:grid-cols-3">
          {[
            ['Aprobación de actas', 'Revisa las actas aprobadas por el Revisor y las correcciones enviadas directamente a tu etapa.'],
            ['Biblioteca de actas', 'Consulta el historial, abre documentos y revisa la consistencia desde el repositorio.'],
            ['PDF final', 'Al aprobar el acta se habilita su descarga en Aprobación y en Biblioteca.'],
          ].map(([encabezado, descripcion]) => (
            <article key={encabezado} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="font-semibold text-corporativo-700">{encabezado}</h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">{descripcion}</p>
            </article>
          ))}
        </section>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Proceso de aprobación"
            descripcion="Secuencia recomendada para revisar y resolver cada acta"
          />
          <TarjetaCuerpo>
            <ol className="space-y-4">
              {[
                {
                  titulo: 'Abre Aprobación de actas',
                  descripcion: 'La bandeja muestra las actas que el Revisor marcó como revisadas y las versiones corregidas que el Capturista envió directamente al Abogado.',
                },
                {
                  titulo: 'Examina el contenido y sus antecedentes',
                  descripcion: 'Usa Ver acta para consultar el documento. Ver versiones abre el historial de solo lectura y permite inspeccionar el contenido de cada versión.',
                },
                {
                  titulo: 'Apóyate en el análisis asistido',
                  descripcion: 'Pulsa Analizar con IA para revisar la consistencia y comparar la versión actual con la anterior. La tarjeta presenta secciones modificadas, hallazgos y recomendaciones; puedes agregar el análisis a las observaciones y editarlo antes de devolver.',
                },
                {
                  titulo: 'Aprueba o devuelve con observaciones',
                  descripcion: 'Si el acta está lista, pulsa Aprobar acta. Si necesita cambios, escribe observaciones concretas y pulsa Devolver con errores; las observaciones son obligatorias.',
                },
                {
                  titulo: 'Descarga el documento final',
                  descripcion: 'Después de aprobar, usa Descargar PDF final en la bandeja o consulta el registro en Biblioteca. El PDF queda listo para imprimir; PGAC no recaba firmas electrónicas y las firmas manuscritas se obtienen fuera del sistema.',
                },
              ].map((paso, indice) => (
                <li key={paso.titulo} className="flex gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-corporativo-100 text-sm font-bold text-corporativo-700">
                    {indice + 1}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800">{paso.titulo}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{paso.descripcion}</p>
                  </div>
                </li>
              ))}
            </ol>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Herramientas por pantalla"
            descripcion="Qué puedes hacer en cada sección de tu menú"
          />
          <TarjetaCuerpo className="grid gap-5 md:grid-cols-2">
            <div className="rounded-xl border border-slate-200 p-4">
              <h3 className="font-semibold text-corporativo-700">Aprobación de actas</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-600">
                <li>Ver acta: abre el contenido de la versión que estás revisando.</li>
                <li>Ver versiones: consulta las versiones anteriores sin modificarlas.</li>
                <li>Analizar con IA: despliega u oculta el análisis; al reabrirlo se conserva el resultado cargado.</li>
                <li>Agregar análisis a observaciones: copia hallazgos y recomendaciones al campo de retroalimentación para que los revises.</li>
                <li>Aprobar acta o Devolver con errores: registra tu decisión en el flujo.</li>
                <li>Descargar PDF final: aparece cuando el acta está aprobada.</li>
              </ul>
            </div>
            <div className="rounded-xl border border-slate-200 p-4">
              <h3 className="font-semibold text-corporativo-700">Biblioteca de actas</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-600">
                <li>Filtra el historial por folio, sociedad, tipo de asamblea o estatus.</li>
                <li>Ver acta abre el documento y Analizar con IA ejecuta la validación de consistencia.</li>
                <li>La tarjeta de validación muestra el puntaje, el proveedor, los hallazgos y las recomendaciones; el botón permite contraerla o volver a mostrarla.</li>
                <li>Descargar PDF final solo está disponible para actas aprobadas.</li>
              </ul>
            </div>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Cómo funciona el ciclo de correcciones"
            descripcion="El destino depende del rol que solicitó el último cambio"
          />
          <TarjetaCuerpo>
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <h3 className="text-sm font-semibold text-amber-900">Si tú devuelves el acta</h3>
                <p className="mt-1 text-sm leading-relaxed text-amber-800">
                  El Capturista recibe tus observaciones y crea una nueva versión. Esa versión vuelve
                  directamente a Aprobación de actas; el Revisor no repite su etapa.
                </p>
              </div>
              <div className="rounded-lg border border-corporativo-100 bg-corporativo-50 p-4">
                <h3 className="text-sm font-semibold text-corporativo-800">Si el Revisor la devuelve</h3>
                <p className="mt-1 text-sm leading-relaxed text-corporativo-700">
                  El Capturista corrige y envía una nueva versión al Revisor. Cuando este la marque
                  como revisada, llegará a tu bandeja para la aprobación legal.
                </p>
              </div>
            </div>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Alcance del análisis y responsabilidad profesional"
            descripcion="La IA apoya la revisión; no sustituye el criterio jurídico"
          />
          <TarjetaCuerpo>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>El análisis puede señalar inconsistencias en quórum, convocatoria, asistentes, orden del día, acuerdos, votaciones y cláusulas.</li>
              <li>Si hay un proveedor de IA configurado, este complementa las reglas locales. Sin proveedor, la aplicación informa resultados basados en reglas deterministas.</li>
              <li>Los hallazgos son sugerencias: confirma fechas, cifras, poderes, estatutos y anexos contra las fuentes societarias antes de decidir.</li>
              <li>La aprobación y la devolución son decisiones humanas. Verifica y ajusta la retroalimentación antes de enviarla al Capturista.</li>
              <li>PGAC no reemplaza la asesoría legal, la firma de las partes ni la protocolización ante fedatario cuando corresponda.</li>
            </ul>
            <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Proveedor configurado: <strong>{catalogos?.proveedor_ia || 'plantillas'}</strong>
              {' · '}
              {catalogos?.ia_habilitada ? 'IA externa habilitada' : 'validaciones con reglas locales'}.
            </p>
          </TarjetaCuerpo>
        </Tarjeta>
        <GuiaCuenta rol={rol} />
      </div>
    )
  }

  if (rol === 'revisor') {
    return (
      <div className="space-y-5">
        <header className="rounded-2xl bg-gradient-to-r from-corporativo-700 to-corporativo-500 px-6 py-7 text-white shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/75">
            Centro de ayuda · Revisor
          </p>
          <h1 className="mt-2 text-2xl font-bold">{titulo}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-white/90">
            Guía para analizar cada borrador, dar retroalimentación clara al Capturista y enviar al
            Abogado las actas que estén listas para su aprobación legal.
          </p>
        </header>

        <section className="grid gap-3 md:grid-cols-3">
          {[
            ['Revisión de actas', 'Atiende borradores nuevos y versiones corregidas que regresan a tu etapa.'],
            ['Análisis asistido', 'Compara la versión actual con la anterior y ayuda a localizar inconsistencias.'],
            ['Biblioteca de actas', 'Consulta el historial general y abre actas para su lectura.'],
          ].map(([encabezado, descripcion]) => (
            <article key={encabezado} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="font-semibold text-corporativo-700">{encabezado}</h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-600">{descripcion}</p>
            </article>
          ))}
        </section>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Proceso de revisión"
            descripcion="Pasos para atender un borrador en tu bandeja"
          />
          <TarjetaCuerpo>
            <ol className="space-y-4">
              {[
                {
                  titulo: 'Abre Revisión de actas',
                  descripcion: 'La bandeja muestra las actas pendientes de tu etapa. Revisa el folio, la versión, el estado y, si hay movimientos previos, consulta el historial de revisión.',
                },
                {
                  titulo: 'Lee y analiza el documento',
                  descripcion: 'Pulsa Ver acta para revisar el contenido. Analizar con IA despliega una validación de consistencia y, si existe una versión anterior, muestra qué secciones cambiaron. Si ya hay un resultado cargado, puedes contraerlo y volverlo a mostrar sin repetir el análisis.',
                },
                {
                  titulo: 'Prepara observaciones cuando haya errores',
                  descripcion: 'Describe correcciones concretas en el campo Observaciones. Puedes agregar los hallazgos del análisis como punto de partida y editar el texto. Las observaciones son obligatorias para devolver el acta.',
                },
                {
                  titulo: 'Devuelve o envía al Abogado',
                  descripcion: 'Pulsa Devolver con errores para que el Capturista corrija el documento, o Marcar revisada y enviar al Abogado si el borrador está listo para aprobación legal.',
                },
              ].map((paso, indice) => (
                <li key={paso.titulo} className="flex gap-3">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-corporativo-100 text-sm font-bold text-corporativo-700">
                    {indice + 1}
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-800">{paso.titulo}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600">{paso.descripcion}</p>
                  </div>
                </li>
              ))}
            </ol>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Acciones de la bandeja"
            descripcion="Funciones disponibles en cada registro"
          />
          <TarjetaCuerpo>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ['Ver acta', 'Abre el contenido del acta que está pendiente de revisión.'],
                ['Analizar con IA', 'Muestra u oculta puntaje, secciones modificadas, hallazgos y recomendaciones.'],
                ['Agregar análisis a observaciones', 'Copia el resumen y los hallazgos al campo de observaciones para revisarlos y ajustarlos antes de devolver.'],
                ['Devolver con errores', 'Envía el acta al Capturista; escribe observaciones específicas antes de confirmar.'],
                ['Marcar revisada y enviar al Abogado', 'Termina tu etapa y coloca el acta en la bandeja de aprobación legal.'],
                ['Historial de revisión', 'Consulta quién revisó, devolvió o reenvió cada versión y las observaciones registradas.'],
              ].map(([accion, descripcion]) => (
                <div key={accion} className="rounded-xl border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-corporativo-700">{accion}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">{descripcion}</p>
                </div>
              ))}
            </div>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Ciclo de correcciones y Biblioteca"
            descripcion="A dónde se dirige cada versión y qué puedes consultar"
          />
          <TarjetaCuerpo className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                <h3 className="text-sm font-semibold text-amber-900">Si tú devuelves el acta</h3>
                <p className="mt-1 text-sm leading-relaxed text-amber-800">
                  El Capturista corrige y crea una versión nueva que regresa a tu bandeja. Revisa
                  nuevamente el documento y sus cambios antes de decidir.
                </p>
              </div>
              <div className="rounded-lg border border-corporativo-100 bg-corporativo-50 p-4">
                <h3 className="text-sm font-semibold text-corporativo-800">Si el Abogado devuelve el acta</h3>
                <p className="mt-1 text-sm leading-relaxed text-corporativo-700">
                  La corrección del Capturista vuelve directamente al Abogado, porque tu etapa ya
                  fue completada.
                </p>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-800">Biblioteca de actas</h3>
              <ul className="mt-2 list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-600">
                <li>Busca en el historial por folio, sociedad, tipo de asamblea o estatus.</li>
                <li>Usa Ver acta para consultar un documento desde el registro.</li>
                <li>La Biblioteca es de consulta: las decisiones se toman desde Revisión de actas.</li>
                <li>La descarga del PDF final y la aprobación legal corresponden al Abogado Responsable.</li>
              </ul>
            </div>
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta>
          <TarjetaEncabezado
            titulo="Alcance de la asistencia con IA"
            descripcion="Los resultados apoyan tu revisión, pero no deciden por ti"
          />
          <TarjetaCuerpo>
            <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-slate-700">
              <li>El análisis puede señalar inconsistencias de quórum, convocatoria, asistentes, orden del día, acuerdos, votaciones y cláusulas.</li>
              <li>Con proveedor de IA configurado, el modelo complementa las reglas locales; sin proveedor se muestran validaciones deterministas.</li>
              <li>Comprueba los hallazgos contra el contenido del acta. La IA puede omitir problemas o sugerir cambios que no correspondan.</li>
              <li>Tu decisión de devolver o enviar al Abogado es humana; el análisis no cambia el estado del acta automáticamente.</li>
            </ul>
            <p className="mt-4 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Proveedor configurado: <strong>{catalogos?.proveedor_ia || 'plantillas'}</strong>
              {' · '}
              {catalogos?.ia_habilitada ? 'IA externa habilitada' : 'validaciones con reglas locales'}.
            </p>
          </TarjetaCuerpo>
        </Tarjeta>
        <GuiaCuenta rol={rol} />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">{titulo}</h1>
        <p className="text-sm text-slate-500">
          Funciones disponibles según tu rol, flujo de revisión y alcance del PDF listo para impresión.
        </p>
      </header>

 <Tarjeta>
        <TarjetaEncabezado titulo="Aviso legal" descripcion="Alcance del documento generado" />
        <TarjetaCuerpo>
          <p className="text-sm text-slate-700">
            PGAC es una herramienta de apoyo documental: estructura y redacta el acta,
            pero no sustituye la revisión de un abogado corporativo. Antes de la firma y, en su caso, de
            la protocolización ante fedatario público, verifica los datos societarios contra el acta
            constitutiva, los estatutos vigentes y el libro de registro de acciones.
          </p>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Navegación"
          descripcion="Las secciones visibles dependen del rol y aparecen en la barra lateral (en móvil, arriba)."
        />
        <TarjetaCuerpo>
          <ul className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
            <li>
              <strong>Generar acta:</strong> formulario manual o asistente IA; ambos envían a revisión.
            </li>
            <li>
              <strong>Mis actas:</strong> el Capturista consulta el avance y corrige las actas devueltas.
            </li>
            <li>
              <strong>Revisión y aprobación:</strong> el Revisor y el Abogado atienden sus respectivas bandejas.
            </li>
            <li>
              <strong>Biblioteca de actas:</strong> historial, versiones y descarga del PDF final
              aprobado para el Abogado.
            </li>
            <li>
              <strong>Administración:</strong> versiones, vigencia y caducidad de los expedientes.
            </li>
            <li>
              <strong>Guía de uso:</strong> esta sección.
            </li>
          </ul>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Flujo de trabajo"
          descripcion="Cuatro pasos de captura y revisión; después sigue el flujo de autorización"
        />
        <TarjetaCuerpo>
          <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-700">
            <li>
              <strong>Datos generales:</strong> sociedad, R.F.C., tipo de asamblea, fecha, hora,
              lugar y datos de la convocatoria.
            </li>
            <li>
              <strong>Asistentes y quórum:</strong> capital social, acciones totales, acciones
              presentes, presidente y secretario; el sistema calcula el quórum automáticamente.
            </li>
            <li>
              <strong>Orden del día y acuerdos:</strong> cada punto del orden del día con su
              resumen de acuerdo; la IA redacta la cláusula legal y el fundamento normativo (o se
              usan plantillas deterministas sin conexión).
            </li>
            <li>
              <strong>Revisión del borrador:</strong> genera las cláusulas, consulta la validación
              y envía el documento al Revisor. La revisión y aprobación legal ocurren después, en
              las bandejas de cada rol.
            </li>
          </ol>
          <p className="mt-3 text-xs text-slate-500">
            En el paso 4, <strong>"Generar borrador con IA"</strong> redacta las cláusulas antes
            de enviar. Las correcciones del Revisor regresan a su bandeja; las del Abogado vuelven
            directamente a su etapa. Cada corrección aumenta la versión. El PDF final solo se
            descarga después de la aprobación legal y queda listo para imprimir; la firma manuscrita
            se recaba fuera de PGAC.
          </p>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Administración de actas"
          descripcion="Versiones, vigencia y caducidad de los expedientes"
        />
        <TarjetaCuerpo>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
            <li>
              <strong>Resumen del repositorio:</strong> totales de actas agrupadas por estatus y
              clasificación de vigencia (vencida, por vencer, vigente, sin fecha).
            </li>
            <li>
              <strong>Vigencia:</strong> lista actas ordenadas por prioridad, con las vencidas
              primero, para atenderlas con anticipación.
            </li>
            <li>
              <strong>Historial de versiones:</strong> cada edición genera una nueva versión. Se
              pueden listar, ver el contenido de cualquier versión y restaurar una versión anterior
              (emitendo una nueva sin borrar el historial).
            </li>
            <li>
              <strong>Caducidad:</strong> fija, amplía o elimina la fecha de caducidad de un acta.
              El cambio queda registrado como nueva versión con su motivo.
            </li>
          </ul>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Asistente IA conversacional"
          descripcion="Creación guiada de actas mediante chat con lenguaje natural"
        />
        <TarjetaCuerpo>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
            <li>
              <strong>Creación guiada:</strong> escribe "Quiero crear un acta" y el asistente te
              solicita los datos faltantes paso a paso, mostrando el progreso de recopilación.
            </li>
            <li>
              <strong>Tipos de asamblea:</strong> el asistente ofrece un catálogo de tipos (ordinaria,
              extraordinaria, aumento de capital, fusión, disolución, etc.) para elegir.
            </li>
            <li>
              <strong>Envío al flujo:</strong> al completar la información, el asistente guarda el
              acta y la envía al Revisor; las correcciones posteriores vuelven al rol que las solicitó.
            </li>
          </ul>
          <p className="mt-3 text-xs text-slate-500">
            El asistente opera bajo <code>/api/v1/asistente/chat</code> y no requiere credenciales
            de IA externa: funciona con plantillas deterministas cuando no hay proveedor
            configurado.
          </p>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Información de la empresa o sociedad"
          descripcion="Datos de la sociedad que se usan en el encabezado de cada acta"
        />
        <TarjetaCuerpo>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
            <li>
              <strong>Datos capturables:</strong> razón social, R.F.C., tipo de sociedad (7
              opciones: S.A., S. de R.L., S. en C., S.A.S., S. en C. por A., S.C., S. en N.C.)
              y logo de la empresa.
            </li>
            <li>
              <strong>Uso automático:</strong> activa el toggle "Usar esta información al generar
              el acta" para que la sociedad, tipo de sociedad y logo se incluyan en cada
              acta generada.
            </li>
            <li>
              <strong>Redacción asistida:</strong> la IA puede incorporar los datos de la sociedad
              al redactar las cláusulas y el encabezado del PDF.
            </li>
            <li>
              <strong>Persistencia:</strong> el Administrador guarda la información en el perfil
              empresarial; los usuarios autorizados la consultan al iniciar sesión. La interfaz
              también conserva una copia local para precargar el formulario.
            </li>
          </ul>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Qué valida la plataforma"
          descripcion="Reglas deterministas siempre activas; el LLM las complementa cuando está configurado"
        />
        <TarjetaCuerpo>
          <ul className="list-disc space-y-2 pl-5 text-sm text-slate-700">
            <li>Quórum de instalación (arts. 189, 190 y 191 LGSM) contra el capital representado.</li>
            <li>Coherencia entre el quórum declarado y la suma de porcentajes de los asistentes.</li>
            <li>Convocatoria previa y medio de publicación (arts. 186 y 187 LGSM).</li>
            <li>Integración de la mesa directiva: presidente, secretario y escrutadores.</li>
            <li>Correspondencia entre los puntos del orden del día y los acuerdos adoptados.</li>
            <li>Mayorías declaradas frente al porcentaje requerido por cada acuerdo.</li>
            <li>Existencia de cláusula legal y fundamento normativo en cada acuerdo.</li>
          </ul>
          <p className="mt-3 text-xs text-slate-500">
            El puntaje final (0-100) se pondera con 15 puntos por hallazgo crítico, 7 por advertencia y 2
            por observación informativa.
          </p>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado
          titulo="Redacción con IA"
          descripcion="Separación estricta entre redacción textual y maquetado del PDF"
        />
        <TarjetaCuerpo>
          <p className="text-sm text-slate-700">
            La redacción puede usar Azure OpenAI, Google Gemini o un proveedor compatible con OpenAI
            cuando está configurado. Si no hay proveedor o falla, PGAC puede recurrir a plantillas
            deterministas. Esto no elimina la necesidad de que el backend y la base de datos estén
            disponibles. El PDF se maqueta de forma reproducible, sin intervención del modelo.
          </p>
          <p className="mt-3 text-sm text-slate-700">
            Proveedor activo: <strong>{catalogos?.proveedor_ia || 'plantillas'}</strong>{' '}
            {catalogos?.ia_habilitada ? '(IA externa habilitada)' : '(modo plantillas locales)'}.
          </p>
          <p className="mt-3 text-xs text-slate-500">
            Para habilitar IA externa configura en <code>backend/.env</code>:{' '}
            <code>AZURE_OPENAI_ENDPOINT</code>, <code>AZURE_OPENAI_API_KEY</code> y{' '}
            <code>AZURE_OPENAI_DEPLOYMENT</code>; <code>GEMINI_API_KEY</code> y{' '}
            <code>GEMINI_MODEL</code>; o configura <code>AI_BASE_URL</code> y <code>AI_MODEL</code>{' '}
            para un proveedor compatible con OpenAI.
          </p>
        </TarjetaCuerpo>
      </Tarjeta>

      <Tarjeta>
        <TarjetaEncabezado titulo="API REST" descripcion="Documentación interactiva en /docs" />
        <TarjetaCuerpo>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Método</th>
                  <th className="py-2 pr-4">Ruta</th>
                  <th className="py-2">Descripción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {ENDPOINTS.map(([metodo, ruta, descripcion]) => (
                  <tr key={`${metodo}-${ruta}`}>
                    <td className="py-2 pr-4 font-mono text-xs font-semibold text-corporativo-600">
                      {metodo}
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs text-slate-700">{ruta}</td>
                    <td className="py-2 text-slate-600">{descripcion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </TarjetaCuerpo>
      </Tarjeta>
      <GuiaCuenta rol={rol} />
    </div>
  )
}
