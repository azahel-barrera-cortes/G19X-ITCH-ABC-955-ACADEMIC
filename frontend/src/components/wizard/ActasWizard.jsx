import Boton from '../ui/Boton.jsx'
import Stepper from '../ui/Stepper.jsx'
import PasoDatosGenerales from './PasoDatosGenerales.jsx'
import PasoAsistentes from './PasoAsistentes.jsx'
import PasoOrdenDelDia from './PasoOrdenDelDia.jsx'
import PasoRevision from './PasoRevision.jsx'

/**
 * Contenedor del formulario por pasos (wizard).
 *
 * Orquesta la navegación —incluida la validación de cada paso— y delega la
 * captura en los componentes especializados. El paso final recibe las acciones
 * de redacción con IA y de exportación a PDF.
 */
export default function ActasWizard({
  pasos,
  pasoActual,
  onCambiarPaso,
  pasosCompletados = [],
  estado,
  calculos,
  despachar,
  actualizarCampo,
  errores = {},
  infoEmpresa = null,
  ...accionesRevision
}) {
  const paso = pasos.find((item) => item.id === pasoActual) || pasos[0]
  const esUltimo = paso.id === pasos.length

  const contenido =
    paso.id === 1 ? (
      <PasoDatosGenerales estado={estado} actualizarCampo={actualizarCampo} errores={errores} infoEmpresa={infoEmpresa} />
    ) : paso.id === 2 ? (
      <PasoAsistentes
        estado={estado}
        actualizarCampo={actualizarCampo}
        despachar={despachar}
        calculos={calculos}
        errores={errores}
      />
    ) : paso.id === 3 ? (
      <PasoOrdenDelDia
        estado={estado}
        actualizarCampo={actualizarCampo}
        despachar={despachar}
        calculos={calculos}
        errores={errores}
      />
    ) : (
      <PasoRevision
        estado={estado}
        calculos={calculos}
        actualizarCampo={actualizarCampo}
        errores={errores}
        {...accionesRevision}
      />
    )

  return (
    <div className="space-y-5">
      <Stepper
        pasos={pasos}
        pasoActual={paso.id}
        completados={pasosCompletados}
        onSeleccionar={onCambiarPaso}
      />

      <section className="tarjeta">
        <header className="flex flex-wrap items-baseline justify-between gap-2 border-b border-slate-200 px-5 py-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
            Paso {paso.id} de {pasos.length} · {paso.titulo}
          </h2>
          <p className="text-xs text-slate-500">{paso.descripcion}</p>
        </header>

        <div className="px-5 py-5">{contenido}</div>

        <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-3">
          <Boton
            variante="fantasma"
            disabled={paso.id === 1}
            onClick={() => onCambiarPaso(paso.id - 1)}
          >
            ← Atrás
          </Boton>

          {!esUltimo ? (
            <Boton onClick={() => onCambiarPaso(paso.id + 1)}>Siguiente →</Boton>
          ) : (
            <span className="text-xs text-slate-500">
              Genera el borrador, revisa la validación y descarga el PDF final.
            </span>
          )}
        </footer>
      </section>
    </div>
  )
}
