const GuiaCard = ({ titulo, descripcion, children }) => (
  <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:p-6">
    <h2 className="text-lg font-semibold text-slate-900">{titulo}</h2>
    {descripcion && <p className="mt-1 text-sm text-slate-500">{descripcion}</p>}
    <div className="mt-4 text-sm leading-relaxed text-slate-700">{children}</div>
  </section>
)

export default function GuiaSuperAdmin() {
  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto w-full max-w-7xl px-4 py-5 md:px-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-corporativo-600">
            Centro de ayuda · Administración global
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">
            Guía de SuperAdministrador
          </h1>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-600">
            Instrucciones para gestionar usuarios de todo el sistema y consultar su actividad
            auditada.
          </p>
        </div>
      </header>

      <main className="mx-auto grid w-full max-w-7xl gap-5 px-4 py-6 md:px-6">
        <div className="grid gap-3 md:grid-cols-2">
          <article className="rounded-xl border border-corporativo-200 bg-corporativo-50/60 p-4">
            <h2 className="font-semibold text-corporativo-800">Administración de Usuarios</h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              Administra globalmente los perfiles, roles y accesos de todas las cuentas.
            </p>
          </article>
          <article className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="font-semibold text-corporativo-800">Bitácora</h2>
            <p className="mt-1 text-sm leading-relaxed text-slate-600">
              Consulta quién realizó una acción, cuándo ocurrió y qué información fue afectada.
            </p>
          </article>
        </div>

        <GuiaCard
          titulo="Administrar usuarios del sistema"
          descripcion="La tabla de usuarios permite buscar, filtrar y ejecutar acciones sobre cada cuenta."
        >
          <ol className="list-decimal space-y-2 pl-5">
            <li>Busca por nombre o correo y filtra por rol o estatus. Usa Limpiar filtros para volver a ver todos los perfiles.</li>
            <li>Para dar de alta a una persona, selecciona Registrar nuevo usuario y completa nombre, correo, rol y una contraseña de al menos 12 caracteres.</li>
            <li>Usa el selector de rol o el botón Editar para actualizar el rol, el nombre o la contraseña. Al editar, deja la contraseña vacía si no deseas cambiarla; el correo no se modifica desde esta pantalla.</li>
            <li>Usa Desactivar para impedir el acceso sin borrar el perfil; Activar restablece el acceso de una cuenta desactivada.</li>
            <li>Eliminar borra el perfil de forma permanente y solicita confirmación. Revisa antes que sea el usuario correcto.</li>
          </ol>
          <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            No puedes cambiar tu propio rol, desactivar tu propia cuenta ni eliminar tu propio
            usuario. La interfaz bloquea esas acciones para proteger el acceso administrativo.
          </p>
          <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
            Para cambiar tu nombre o contraseña, usa Editar en tu propio registro. Tu correo no se
            modifica desde esta pantalla; después de cambiar la contraseña, vuelve a iniciar sesión.
          </p>
        </GuiaCard>

        <GuiaCard
          titulo="Consultar la Bitácora"
          descripcion="El registro se sincroniza automáticamente y también puede actualizarse manualmente."
        >
          <ol className="list-decimal space-y-2 pl-5">
            <li>Revisa los indicadores de eventos registrados, eventos de hoy, cambios en actas y sesiones de usuario activas.</li>
            <li>Busca por usuario, rol, folio, entidad o acción; combina la búsqueda con filtros de tipo de acción, entidad y rango de fechas.</li>
            <li>Pulsa Ver detalle en un evento para comparar los datos anteriores y posteriores, así como consultar la IP de origen y el identificador de la entidad cuando estén disponibles.</li>
            <li>La bitácora consulta cambios recientes automáticamente cada cinco segundos. Usa Actualizar para solicitar la información de inmediato.</li>
          </ol>
          <p className="mt-4 text-xs text-slate-500">
            La bitácora es de consulta; los registros no se editan desde esta pantalla.
          </p>
        </GuiaCard>

        <GuiaCard titulo="Buenas prácticas">
          <ul className="list-disc space-y-2 pl-5">
            <li>Asigna a cada persona únicamente el rol que necesita para realizar su trabajo.</li>
            <li>Las contraseñas nuevas deben tener al menos 12 caracteres. Comparte las credenciales temporales de forma segura y pide al usuario que las cambie después de acceder.</li>
            <li>Desactiva accesos que ya no deban utilizarse y elimina perfiles solo cuando sea necesario.</li>
            <li>Consulta la Bitácora para dar seguimiento a cambios y verifica los detalles antes de tomar medidas administrativas.</li>
            <li>Las acciones de esta interfaz están sujetas a la autorización del backend; la visibilidad de un botón no sustituye los permisos del sistema.</li>
          </ul>
        </GuiaCard>
      </main>
    </div>
  )
}
