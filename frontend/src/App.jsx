import { useCallback, useEffect, useMemo, useState } from 'react'
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
import Acceso from './pages/Acceso.jsx'
import Perfil from './pages/Perfil.jsx'
import { obtenerCatalogos } from './api/client.js'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import { seccionesPermitidas } from './constants/roles.js'

const CLAVE_INFO_EMPRESA = 'pgac_info_empresa'

/**
 * Raíz de la aplicación: envuelve todo en el proveedor de autenticación.
 *
 * La compuerta de acceso vive en `Aplicacion`: sin sesión iniciada solo se
 * muestra la interfaz de acceso (`Acceso`), completamente separada del sistema
 * de actas; con sesión se abre el perfil del usuario y la navegación queda
 * limitada a las funciones permitidas por su rol.
 */
export default function App() {
  return (
    <AuthProvider>
      <Aplicacion />
    </AuthProvider>
  )
}

function Aplicacion() {
  const { autenticado, usuario, cerrarSesion } = useAuth()
  const [seccion, setSeccion] = useState('perfil')
  const [vistaGenerar, setVistaGenerar] = useState('panel')
  const [plantillaTipo, setPlantillaTipo] = useState(null)
  const [actaEnEdicion, setActaEnEdicion] = useState(null)
  const [catalogos, setCatalogos] = useState(null)
  const [infoEmpresa, setInfoEmpresa] = useState(null)

  // Secciones que el rol del usuario puede ver (espejo del RBAC del backend).
  const seccionesVisibles = useMemo(
    () => (autenticado ? seccionesPermitidas(usuario?.rol) : []),
    [autenticado, usuario?.rol],
  )

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CLAVE_INFO_EMPRESA)
      if (raw) setInfoEmpresa(JSON.parse(raw))
    } catch {
      /* silent */
    }
  }, [])

  useEffect(() => {
    if (!autenticado) return undefined
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
  }, [autenticado])

  // Guarda de navegación: si la sección activa no está permitida para el rol,
  // se regresa al perfil (p. ej. un capturista no puede quedarse en Biblioteca).
  useEffect(() => {
    if (autenticado && seccion !== 'perfil' && !seccionesVisibles.includes(seccion)) {
      setSeccion('perfil')
      setVistaGenerar('panel')
    }
  }, [autenticado, seccion, seccionesVisibles])

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

  /** Tras un acceso correcto se abre el perfil del usuario. */
  const manejarAccesoExitoso = useCallback(() => {
    volverAlPanel()
    setSeccion('perfil')
  }, [volverAlPanel])

  /** Cerrar sesión limpia el token; la compuerta vuelve a mostrar `Acceso`. */
  const manejarCerrarSesion = useCallback(() => {
    cerrarSesion()
    volverAlPanel()
    setSeccion('perfil')
  }, [cerrarSesion, volverAlPanel])

  // ── Compuerta de acceso ─────────────────────────────────────────────────
  // Sin sesión NO se renderiza nada del sistema de actas: únicamente la
  // interfaz de acceso (iniciar sesión / crear cuenta / recuperar contraseña).
  if (!autenticado) {
    return <Acceso onAccesoExitoso={manejarAccesoExitoso} />
  }

  return (
    <div className="flex min-h-full">
      <BarraLateral
        seccion={seccion}
        onCambiarSeccion={cambiarSeccion}
        seccionesVisibles={seccionesVisibles}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Encabezado
          seccion={seccion}
          onCambiarSeccion={cambiarSeccion}
          onIrAPerfil={cambiarSeccion}
          onCerrarSesion={manejarCerrarSesion}
          seccionesVisibles={seccionesVisibles}
        />

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
                key={actaEnEdicion ? 'edicion-' + actaEnEdicion.id : 'plantilla-' + (plantillaTipo || 'nueva')}
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
          {seccion === 'perfil' ? <Perfil onCambiarVista={cambiarSeccion} /> : null}
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

