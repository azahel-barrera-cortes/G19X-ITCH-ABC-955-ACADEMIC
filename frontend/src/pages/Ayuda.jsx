import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'

const ENDPOINTS = [
  ['GET', '/api/v1/actas/catalogos', 'Catálogos de tipos de asamblea, mayorías, caracteres y estatus.'],
  ['POST', '/api/v1/actas/redactar', 'Genera el borrador con IA y la validación (no persiste ni exporta).'],
  ['POST', '/api/v1/actas/generar-pdf', 'Endpoint principal: redacta, guarda y devuelve el PDF binario.'],
  ['GET', '/api/v1/actas', 'Historial de actas con filtros y paginación.'],
  ['GET', '/api/v1/actas/{id}', 'Acta completa, con sus cláusulas y su validación.'],
  ['PUT', '/api/v1/actas/{id}', 'Reemplaza el contenido del acta e incrementa su versión.'],
  ['PATCH', '/api/v1/actas/{id}/estatus', 'Cambia el estatus del expediente del acta.'],
  ['GET', '/api/v1/actas/{id}/pdf', 'Regenera el PDF desde la base de datos (sin IA).'],
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

/** Sección «Guía de uso»: flujo de trabajo, API y notas legales. */
export default function Ayuda({ catalogos }) {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">Guía de uso</h1>
        <p className="text-sm text-slate-500">
          Cómo generar un acta, qué hace la IA y qué revisa el motor de validación antes de la firma.
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
          descripcion="Las cuatro secciones están en la barra lateral izquierda (en móvil aparecen arriba)."
        />
        <TarjetaCuerpo>
          <ul className="grid gap-2 text-sm text-slate-700 sm:grid-cols-2">
            <li>
              <strong>Generar acta:</strong> formulario por pasos, redacción con IA y PDF.
            </li>
            <li>
              <strong>Biblioteca de actas:</strong> historial, estatus, descarga de PDF y edición.
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
          descripcion="Cuatro pasos desde la captura hasta el PDF firmable"
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
              <strong>Revisión y PDF:</strong> se muestra la validación de consistencia (puntaje
              y hallazgos), se genera el borrador con IA y se descarga el PDF final con encabezado,
              quórum, firmas y numeración de páginas.
            </li>
          </ol>
          <p className="mt-3 text-xs text-slate-500">
            En el paso 4, el botón <strong>"Generar borrador con IA"</strong> devuelve las cláusulas
            y la validación sin guardar; <strong>"Descargar PDF final"</strong> compila el PDF,
            guarda el acta y devuelve el folio, versión, páginas y proveedor de IA.
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
              <strong>Acciones rápidas:</strong> validar una acta, cambiar su estatus, consultar
              versiones, descargar el PDF y restaurar versiones desde el chat.
            </li>
            <li>
              <strong>Borrador organizable:</strong> genera un texto estructurado del acta que
              puedes copiar al formulario manual.
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
              opciones: S.A., S. de R.L., S. en C., S.A.S., S. en C. por A., S.C., S. en N.C.),
              logo de la empresa y firma electrónica opcional.
            </li>
            <li>
              <strong>Uso automático:</strong> activa el toggle "Usar esta información al generar
              el acta" para que la sociedad, tipo de sociedad, logo y firma se incluyan en cada
              acta generada.
            </li>
            <li>
              <strong>Redacción asistida:</strong> la IA puede incorporar los datos de la sociedad
              al redactar las cláusulas y el encabezado del PDF.
            </li>
            <li>
              <strong>Persistencia:</strong> la información se guarda en el navegador
              (localStorage) y está disponible sin necesidad de autenticación.
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
            La redacción de cláusulas se resuelve con Azure OpenAI o Google Gemini cuando existen
            credenciales; en caso contrario —o si el servicio falla— la plataforma utiliza sus plantillas
            legales deterministas, por lo que <strong>nunca deja de funcionar sin conexión</strong>. El
            maquetado del PDF se ejecuta siempre con ReportLab, de forma reproducible y sin intervención
            del modelo.
          </p>
          <p className="mt-3 text-sm text-slate-700">
            Proveedor activo: <strong>{catalogos?.proveedor_ia || 'plantillas'}</strong>{' '}
            {catalogos?.ia_habilitada ? '(IA externa habilitada)' : '(modo plantillas locales)'}.
          </p>
          <p className="mt-3 text-xs text-slate-500">
            Para habilitar IA externa configura en <code>backend/.env</code>:{' '}
            <code>AZURE_OPENAI_ENDPOINT</code>, <code>AZURE_OPENAI_API_KEY</code> y{' '}
            <code>AZURE_OPENAI_DEPLOYMENT</code>; o bien <code>GEMINI_API_KEY</code> y{' '}
            <code>GEMINI_MODEL</code>.
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
    </div>
  )
}
