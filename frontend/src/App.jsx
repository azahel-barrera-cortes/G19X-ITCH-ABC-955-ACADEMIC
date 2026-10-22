import { useCallback, useEffect, useState } from 'react'
import BarraLateral from './components/layout/BarraLateral.jsx'
import Encabezado from './components/layout/Encabezado.jsx'
import AdministracionActas from './pages/AdministracionActas.jsx'
import AsistenteChat from './components/asistente/AsistenteChat.jsx'
import Ayuda from './pages/Ayuda.jsx'
import BibliotecaActas from './pages/BibliotecaActas.jsx'
import ControlGeneraActa from './pages/ControlGeneraActa.jsx'
import GenerarActa from './pages/GenerarActa.jsx'
import GenerarActaConIA from './pages/GenerarActaConIA.jsx'
import InformacionEmpresa from './pages/InformacionEmpresa.jsx'
import { obtenerCatalogos } from './api/client.js'

/**
 * Aplicación PGAC (Página de Gestión de Actas Corporativas).
 *
 * Mantiene la navegación entre secciones y el estado compartido mínimo: los
 * catálogos del dominio (cargados desde la API con respaldo local) y el acta que
 * se está editando en el formulario.
 */
export default function App() {
  const [seccion, setSeccion] = useState('generar')
  // Sub-vista dentro de «Generar acta»: panel | formulario | ia.
  const [vistaGenerar, setVistaGenerar] = useState('panel')
  // Tipo de asamblea precargado cuando se elige una plantilla del panel.
  const [plantillaTipo, setPlantillaTipo] = useState(null)
  const [actaEnEdicion, setActaEnEdicion] = useState(null)
  const [catalogos, setCatalogos] = useState(null)
  const [infoEmpresa, setInfoEmpresa] = useState(null)

  // Los catálogos se cargan una sola vez; si la API no responde se usan los locales.
  useEffect(() => {
    let activo = true
    obtenerCatalogos()
      .then((datos) => {
        if (activo) setCatalogos(datos)
      })
      .catch(() => {
        if (activo) setCatalogos(null)
      })
    return () => {
      activo = false
    }
  }, [])

  const editarActa = useCallback((acta) => {
    setActaEnEdicion(acta)
    setPlantillaTipo(null)
    setVistaGenerar('formulario')
    setSeccion('generar')
  }, [])

  const cerrarEdicion = useCallback(() => setActaEnEdicion(null), [])

  const volverAlPanel = useCallback(() => {
    setActaEnEdicion(null)
    setPlantillaTipo(null)
    setVistaGenerar('panel')
  }, [])

  // Botón lateral «Generar acta»: siempre abre el panel de plantillas.
  const cambiarSeccion = useCallback(
    (nueva) => {
      setSeccion(nueva)
      if (nueva === 'generar') volverAlPanel()
    },
    [volverAlPanel],
  )

  const abrirFormulario = useCallback((tipo = null) => {
    setActaEnEdicion(null)
    setPlantillaTipo(tipo)
    setVistaGenerar('formulario')
    setSeccion('generar')
  }, [])

  const abrirVistaIA = useCallback(() => {
    setVistaGenerar('ia')
    setSeccion('generar')
  }, [])

  return (
    <div className="flex min-h-full">
      <BarraLateral seccion={seccion} onCambiarSeccion={cambiarSeccion} />

      <div className="flex min-w-0 flex-1 flex-col">
        <Encabezado seccion={seccion} onCambiarSeccion={cambiarSeccion} />

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-6">
          {seccion === 'generar' && (vistaGenerar === 'panel' && !actaEnEdicion) ? (
            <ControlGeneraActa
              onGenerarNueva={() => abrirFormulario(null)}
              onGenerarConIA={abrirVistaIA}
              onUsarPlantilla={(tipo) => abrirFormulario(tipo)}
            />
          ) : null}
          {seccion === 'generar' && (vistaGenerar !== 'panel' || actaEnEdicion) ? (
            vistaGenerar === 'ia' && !actaEnEdicion ? (
              <GenerarActaConIA onVolver={volverAlPanel} />
            ) : (
              <GenerarActa
                key={actaEnEdicion ? `edicion-${actaEnEdicion.id}` : `plantilla-${plantillaTipo || 'nueva'}`}
                actaInicial={actaEnEdicion}
                plantillaTipo={plantillaTipo}
                infoEmpresa={infoEmpresa}
                onVolver={volverAlPanel}
                onCerrarEdicion={cerrarEdicion}
              />
            )
          ) : null}
          {seccion === 'asistente' ? <AsistenteChat modo="pagina" /> : null}
          {seccion === 'biblioteca' ? (
            <BibliotecaActas catalogos={catalogos} onEditar={editarActa} />
          ) : null}
          {seccion === 'administracion' ? <AdministracionActas onEditar={editarActa} /> : null}
          {seccion === 'ayuda' ? <Ayuda catalogos={catalogos} /> : null}
          {seccion === 'empresa' ? (
            <InformacionEmpresa
              infoGuardada={infoEmpresa}
              onGuardar={setInfoEmpresa}
            />
          ) : null}
        </main>

        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-4 text-xs text-slate-500 md:px-6">
            <span>PGAC · Página de Gestión de Actas Corporativas</span>
            <span>
              La IA asiste la redacción; la revisión legal final corresponde al abogado responsable.
            </span>
          </div>
        </footer>
      </div>
    </div>
  )
}
