import PanelHistorial from '../components/actas/PanelHistorial.jsx'

/** Sección «Biblioteca de actas»: consulta del historial y edición de una acta. */
export default function BibliotecaActas({ catalogos, onEditar }) {
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">Biblioteca de actas</h1>
        <p className="text-sm text-slate-500">
          Historial de actas generadas: descarga el PDF, cambia el estatus del expediente, revalida la
          consistencia o continúa la edición de un acta en el formulario.
        </p>
      </header>

      <PanelHistorial catalogos={catalogos} onEditar={onEditar} />
    </div>
  )
}
