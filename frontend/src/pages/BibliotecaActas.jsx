import PanelHistorial from '../components/actas/PanelHistorial.jsx'

/** Sección «Biblioteca de actas»: consulta del historial de actas. */
export default function BibliotecaActas({ catalogos }) {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">Biblioteca de actas</h1>
        <p className="text-sm text-slate-500">
          Historial de actas y versiones. El Abogado puede consultar y descargar el PDF final de las
          actas aprobadas; las decisiones se realizan desde las bandejas de cada rol.
        </p>
      </header>

      <PanelHistorial catalogos={catalogos} />
    </div>
  )
}
