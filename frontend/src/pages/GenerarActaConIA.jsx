import Boton from '../components/ui/Boton.jsx'
import AsistenteChat from '../components/asistente/AsistenteChat.jsx'
import { Tarjeta, TarjetaCuerpo, TarjetaEncabezado } from '../components/ui/Tarjeta.jsx'

export default function GenerarActaConIA({ onVolver = null }) {
  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-corporativo-700">Generar acta con IA</h1>
          <p className="text-sm text-slate-500">Describe tu asamblea y el asistente propone el borrador con fundamento LGSM.</p>
        </div>
        {onVolver ? <Boton variante="secundario" tamano="sm" onClick={onVolver}>Volver al panel</Boton> : null}
      </header>
      <AsistenteChat modo="compacto" titulo="Generar acta con IA" />
      <Tarjeta>
        <TarjetaEncabezado titulo="Consejo" descripcion="Revision humana obligatoria" />
        <TarjetaCuerpo>
          <p className="text-sm text-slate-600">La IA asiste la redaccion; copia el borrador al formulario manual y sometelo a revision legal antes de firmar.</p>
        </TarjetaCuerpo>
      </Tarjeta>
    </div>
  )
}
