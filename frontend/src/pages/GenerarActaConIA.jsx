import Boton from '../components/ui/Boton.jsx'
import AsistenteChat from '../components/asistente/AsistenteChat.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'

export default function GenerarActaConIA({ onVolver = null }) {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-semibold text-corporativo-700">Generar acta con IA</h1>
          <p className="text-sm text-slate-500 mt-1">Describe tu asamblea y el asistente propone el borrador con fundamento LGSM.</p>
        </div>
        {onVolver ? <Boton variante="secundario" tamano="sm" onClick={onVolver}>Volver al panel</Boton> : null}
      </header>

      <div className="space-y-4">
        <Tarjeta className="rounded-xl border border-corporativo-100 bg-white p-6 shadow-sm">
          <TarjetaEncabezado
            titulo="Asistente de redacción"
            descripcion="Conversa con la IA para crear tu acta paso a paso"
          />
          <TarjetaCuerpo className="pt-0">
            <AsistenteChat modo="compacto" titulo="Generar acta con IA" />
          </TarjetaCuerpo>
        </Tarjeta>

        <Tarjeta className="rounded-xl border border-amber-100 bg-amber-50 p-6 shadow-sm">
          <TarjetaEncabezado
            titulo="Consejo importante"
            descripcion="Revisión humana obligatoria antes de firmar"
          />
          <TarjetaCuerpo className="pt-0">
            <div className="flex items-start gap-3">
              <span className="text-amber-600">⚠</span>
              <p className="text-sm text-amber-800 leading-relaxed">
                La IA asiste la redacción; <strong>copia el borrador al formulario manual</strong> y
                súmetelo a revisión legal antes de firmar o protocolizar.
              </p>
            </div>
          </TarjetaCuerpo>
        </Tarjeta>
      </div>
    </div>
  )
}
