import Boton from '../components/ui/Boton.jsx'
import AsistenteChat from '../components/asistente/AsistenteChat.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'

export default function GenerarActaConIA({
  onVolver = null,
  infoEmpresa = null,
  onEditarActa = null,
  actaInicial = null,
  onAplicarCambiosEdicion = null,
  onIrAMisActas = null,
}) {
  const esEdicion = Boolean(actaInicial?.id)
  const empresaAsignada = esEdicion || Boolean(infoEmpresa?.nombre_sociedad && infoEmpresa?.tipo_sociedad)
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-semibold text-corporativo-700">
            {esEdicion ? `Editar ${actaInicial.folio} con el asistente IA` : 'Generar acta con IA'}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {esEdicion
              ? 'Solicita cambios sobre los datos originales. Después podrás revisarlos en el formulario y guardar una nueva versión.'
              : 'Describe tu asamblea y el asistente propone el borrador con fundamento LGSM.'}
          </p>
        </div>
        {onVolver ? (
          <Boton variante="secundario" tamano="sm" onClick={onVolver}>
            {esEdicion ? 'Volver a Mis actas' : 'Volver al panel'}
          </Boton>
        ) : null}
      </header>

      <div className="space-y-4">
        {!empresaAsignada ? (
          <Alerta tono="error" titulo="Empresa requerida">No se ha asignado empresa</Alerta>
        ) : (
        <Tarjeta className="rounded-xl border border-corporativo-100 bg-white p-6 shadow-sm">
          <TarjetaEncabezado
            titulo={esEdicion ? 'Edición asistida' : 'Asistente de redacción'}
            descripcion={esEdicion
              ? 'Indica qué campos deseas modificar. El asistente preparará los cambios para revisarlos.'
              : 'Conversa con la IA para crear tu acta paso a paso'}
          />
          <TarjetaCuerpo className="pt-0">
            <AsistenteChat
              modo="compacto"
              titulo={esEdicion ? `Editar ${actaInicial.folio}` : 'Generar acta con IA'}
              onEditarActa={onEditarActa}
              onIrAMisActas={onIrAMisActas}
              actaId={actaInicial?.id}
              modoEdicion={esEdicion}
              datosAsistente={actaInicial?.datos_asistente}
              onAplicarCambios={esEdicion ? onAplicarCambiosEdicion : null}
            />
          </TarjetaCuerpo>
        </Tarjeta>
        )}

        {empresaAsignada ? <Tarjeta className="rounded-xl border border-amber-100 bg-amber-50 p-6 shadow-sm">
          <TarjetaEncabezado
            titulo="Consejo importante"
            descripcion="Revisión humana obligatoria antes de firmar"
          />
          <TarjetaCuerpo className="pt-0">
            <div className="flex items-start gap-3">
              <span className="text-amber-600">⚠</span>
              <p className="text-sm text-amber-800 leading-relaxed">
                La IA asiste la redacción y envía el borrador al Revisor. Al corregir una devolución,
                la nueva versión vuelve al rol que solicitó los cambios; el PDF final se habilita
                tras la aprobación del Abogado.
              </p>
            </div>
          </TarjetaCuerpo>
        </Tarjeta> : null}
      </div>
    </div>
  )
}
