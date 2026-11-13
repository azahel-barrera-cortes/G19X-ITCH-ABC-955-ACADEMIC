import { useCallback, useEffect, useMemo, useState } from 'react'
import BarraLateral from './components/layout/BarraLateral.jsx'
import Encabezado from './components/layout/Encabezado.jsx'
import AdministracionActas from './pages/AdministracionActas.jsx'
import AdministracionUsuarios from './pages/AdministracionUsuarios.jsx'
import Administrador from './pages/Administrador.jsx'
import AsistenteChat from './components/asistente/AsistenteChat.jsx'
import Ayuda from './pages/Ayuda.jsx'
import BandejaActas from './pages/BandejaActas.jsx'
import BibliotecaActas from './pages/BibliotecaActas.jsx'
import ControlGeneraActa from './pages/ControlGeneraActa.jsx'
import GenerarActa from './pages/GenerarActa.jsx'
import GenerarActaConIA from './pages/GenerarActaConIA.jsx'
import InformacionEmpresa from './pages/InformacionEmpresa.jsx'
import Acceso from './pages/Acceso.jsx'
import Perfil from './pages/Perfil.jsx'
import UsuariosSuperAdmin from './pages/UsuariosSuperAdmin.jsx'
import VitacoraSuperAdmin from './pages/VitacoraSuperAdmin.jsx'
import EstadisticasSuperAdmin from './pages/EstadisticasSuperAdmin.jsx'
import SeguridadSuperAdmin from './pages/SeguridadSuperAdmin.jsx'
import GuiaSuperAdmin from './pages/GuiaSuperAdmin.jsx'
import UsuarioInactivo from './pages/UsuarioInactivo.jsx'
import Alerta from './components/ui/Alerta.jsx'
import { mensajeDeError, obtenerActa, obtenerCatalogos } from './api/client.js'
import { obtenerInfoEmpresa } from './api/auth.js'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import { seccionesPermitidas, SECCIONES_SISTEMA } from './constants/roles.js'

const CLAVE_INFO_EMPRESA = 'pgac_info_empresa'
const CLAVE_SECCION = 'pgac_seccion'

/** IDs de sección válidas (espejo de las secciones del sistema). */
const SECCIONES_SUPERADMIN_IDS = [
  'usuarios',
  'vitacora',
  'estadisticas',
  'seguridad',
  'guia-super-admin',
]
const SECCIONES_VALIDAS = [
  ...SECCIONES_SISTEMA.map((seccion) => seccion.id),
  ...SECCIONES_SUPERADMIN_IDS,
]

/**
 * Lee el hash de la URL (`#/asistente`) y devuelve el id de sección si es
 * válido, o `null` si no hay hash o el id no es válido.
 */
function seccionDesdeHash() {
  const hash = window.location.hash
  if (!hash) return null
  const id = hash.replace(/^#\//, '')
  return SECCIONES_VALIDAS.includes(id) ? id : null
}

/**
 * Raíz de la aplicación: envuelve todo en el proveedor de autenticación.
 *
 * La compuerta de acceso vive en `Aplicacion`: sin sesión iniciada solo se
 * muestra la interfaz de acceso (`Acceso`), completamente separada del sistema
 * de actas; con sesión se abre el panel inicial correspondiente al rol y la navegación queda
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
  const { autenticado, usuario, token, cerrarSesion } = useAuth()
  const [seccion, setSeccion] = useState(() => {
    const desdeHash = seccionDesdeHash()
    if (desdeHash) return desdeHash
    try {
      const guardado = sessionStorage.getItem(CLAVE_SECCION)
      if (guardado && SECCIONES_VALIDAS.includes(guardado)) return guardado
    } catch {
      /* silent */
    }
    return 'perfil'
  })
  const [vistaGenerar, setVistaGenerar] = useState('panel')
  const [plantillaTipo, setPlantillaTipo] = useState(null)
  const [actaEnEdicion, setActaEnEdicion] = useState(null)
  const [cambiosActaIniciales, setCambiosActaIniciales] = useState(null)
  const [cargandoActaEdicion, setCargandoActaEdicion] = useState(false)
  const [errorActaEdicion, setErrorActaEdicion] = useState(null)
  const [versionActaInicial, setVersionActaInicial] = useState(null)
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
    if (!autenticado || !token) return undefined
    let activo = true
    obtenerInfoEmpresa(token)
      .then((datos) => {
        if (activo) setInfoEmpresa(datos || null)
      })
      .catch(() => {
        // El valor local solo se usa como respaldo si el endpoint no está disponible.
      })
    return () => {
      activo = false
    }
  }, [autenticado, token])

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

  useEffect(() => {
    if (!autenticado || !token) return undefined
    let activo = true
    obtenerInfoEmpresa(token)
      .then((datos) => {
        if (!activo) return
        setInfoEmpresa(datos)
        try {
          localStorage.setItem(CLAVE_INFO_EMPRESA, JSON.stringify(datos))
        } catch {
          /* El backend sigue siendo la fuente de verdad. */
        }
      })
      .catch((fallo) => {
        console.error('No se pudo cargar la información empresarial:', fallo)
      })
    return () => {
      activo = false
    }
  }, [autenticado, token])

  // Guarda de navegación: si la sección activa no está permitida para el rol,
  // se regresa al perfil (p. ej. un capturista no puede quedarse en Biblioteca).
  const esSuperAdmin = usuario?.rol === 'SuperAdministrador'
  const esAdministrador = usuario?.rol === 'Administrador'

  useEffect(() => {
    if (autenticado && esSuperAdmin && seccion === 'perfil') {
      setSeccion('usuarios')
      setVistaGenerar('panel')
      return
    }

    const seccionPermitida =
      seccionesVisibles.includes(seccion) ||
      (seccion === 'generar' && Boolean(actaEnEdicion)) ||
      (esSuperAdmin && SECCIONES_SUPERADMIN_IDS.includes(seccion))
    if (autenticado && seccion !== 'perfil' && !seccionPermitida) {
      setSeccion('perfil')
      setVistaGenerar('panel')
    }
  }, [actaEnEdicion, autenticado, seccion, seccionesVisibles, esSuperAdmin])

  // Mantiene la URL (`#/seccion`) y el sessionStorage sincronizados con la
  // sección actual para que al refrescar la página el usuario se quede en
  // la misma sección en la que estaba.
  useEffect(() => {
    if (!autenticado) return
    const hash = seccionDesdeHash()
    if (hash !== seccion) {
      history.pushState(null, '', `#/${seccion}`)
    }
    try {
      sessionStorage.setItem(CLAVE_SECCION, seccion)
    } catch {
      /* silent */
    }
  }, [seccion, autenticado])

  // Navegación con Atrás / Adelante del navegador entre secciones de la app.
  useEffect(() => {
    const manejarPopstate = () => {
      const desdeHash = seccionDesdeHash()
      if (desdeHash) {
        setSeccion(desdeHash)
      }
    }
    window.addEventListener('popstate', manejarPopstate)
    return () => {
      window.removeEventListener('popstate', manejarPopstate)
    }
  }, [])

  const editarActa = useCallback(async (acta) => {
    setCargandoActaEdicion(true)
    setErrorActaEdicion(null)
    try {
      const datosCompletos = await obtenerActa(acta.id)
      const datosAsistente = datosCompletos.datos_asistente || {}
      const generadaConAsistente = Boolean(
        Object.keys(datosAsistente).length ||
        datosCompletos.observaciones?.includes('Borrador creado con acompañamiento del asistente.'),
      )
      setActaEnEdicion(datosCompletos)
      setCambiosActaIniciales(null)
      setPlantillaTipo(null)
      setVistaGenerar(generadaConAsistente ? 'ia' : 'formulario')
      setSeccion('generar')
    } catch (fallo) {
      setErrorActaEdicion(await mensajeDeError(fallo))
    } finally {
      setCargandoActaEdicion(false)
    }
  }, [])
  const editarDesdeAsistente = useCallback((actaId) => {
    editarActa({ id: actaId })
  }, [editarActa])

  const editarDesdeBandeja = useCallback((acta) => {
    setActaEnEdicion(acta)
    setCambiosActaIniciales(null)
    setPlantillaTipo(null)
    setVistaGenerar(Object.keys(acta.datos_asistente || {}).length ? 'ia' : 'formulario')
    setSeccion('generar')
  }, [])

  const aplicarCambiosAsistidos = useCallback(({ cambios }) => {
    setCambiosActaIniciales(cambios || {})
    setVistaGenerar('formulario')
  }, [])

  const cerrarEdicion = useCallback((actaGuardadaId = null) => {
    setActaEnEdicion(null)
    setCambiosActaIniciales(null)
    setVistaGenerar('panel')
    setSeccion(usuario?.rol === 'capturista' ? 'mis-actas' : 'administracion')
    setErrorActaEdicion(null)
    if (actaGuardadaId) setVersionActaInicial(actaGuardadaId)
  }, [usuario?.rol])

  const irAMisActas = useCallback(() => {
    setActaEnEdicion(null)
    setCambiosActaIniciales(null)
    setVistaGenerar('panel')
    setSeccion('mis-actas')
  }, [])

  const limpiarVersionActaInicial = useCallback(() => setVersionActaInicial(null), [])

  const volverAlPanel = useCallback(() => {
    setActaEnEdicion(null)
    setCambiosActaIniciales(null)
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
    setCambiosActaIniciales(null)
    setPlantillaTipo(tipo)
    setVistaGenerar('formulario')
    setSeccion('generar')
  }, [])

  const abrirVistaIA = useCallback(() => {
    setVistaGenerar('ia')
    setSeccion('generar')
  }, [])

  /** Tras un acceso correcto se abre el panel inicial correspondiente al rol. */
  const manejarAccesoExitoso = useCallback(() => {
    volverAlPanel()
    setSeccion(usuario?.rol === 'SuperAdministrador' ? 'usuarios' : 'perfil')
  }, [usuario?.rol, volverAlPanel])

  /** Cerrar sesión limpia el token; la compuerta vuelve a mostrar `Acceso`. */
  const manejarCerrarSesion = useCallback(async () => {
    await cerrarSesion()
    volverAlPanel()
    setSeccion('perfil')
    history.replaceState(null, '', '')
    sessionStorage.removeItem(CLAVE_SECCION)
  }, [cerrarSesion, volverAlPanel])

  // ── Compuerta de acceso ─────────────────────────────────────────────────
  // Sin sesión NO se renderiza nada del sistema de actas: únicamente la
  // interfaz de acceso (iniciar sesión / crear cuenta / recuperar contraseña).
  if (!autenticado) {
    return <Acceso onAccesoExitoso={manejarAccesoExitoso} />
  }

  if (usuario?.activo === false) {
    return <UsuarioInactivo onCerrarSesion={manejarCerrarSesion} />
  }

  return (
    <div className="flex min-h-full">
      <BarraLateral
        seccion={seccion}
        onCambiarSeccion={cambiarSeccion}
        onCerrarSesion={manejarCerrarSesion}
        seccionesVisibles={seccionesVisibles}
        esSuperAdmin={esSuperAdmin}
        rol={usuario?.rol}
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
          {cargandoActaEdicion ? (
            <Alerta tono="info">Cargando el acta completa para editarla…</Alerta>
          ) : null}
          {errorActaEdicion ? (
            <Alerta tono="error" titulo="No se pudo abrir el acta">
              {errorActaEdicion}
            </Alerta>
          ) : null}
          {seccion === 'generar' && (vistaGenerar === 'panel' && !actaEnEdicion) ? (
            <ControlGeneraActa
              onGenerarNueva={() => abrirFormulario(null)}
              onGenerarConIA={abrirVistaIA}
              onUsarPlantilla={(tipo) => abrirFormulario(tipo)}
            />
          ) : null}
          {seccion === 'generar' && (vistaGenerar !== 'panel' || actaEnEdicion) ? (
            vistaGenerar === 'ia' ? (
              <GenerarActaConIA
                key={actaEnEdicion ? 'edicion-ia-' + actaEnEdicion.id : 'generar-ia'}
                infoEmpresa={infoEmpresa}
                actaInicial={actaEnEdicion}
                onVolver={actaEnEdicion ? () => cerrarEdicion() : volverAlPanel}
                onEditarActa={editarDesdeAsistente}
                onIrAMisActas={irAMisActas}
                onAplicarCambiosEdicion={aplicarCambiosAsistidos}
              />
            ) : (
              <GenerarActa
                key={actaEnEdicion ? 'edicion-' + actaEnEdicion.id : 'plantilla-' + (plantillaTipo || 'nueva')}
                actaInicial={actaEnEdicion}
                cambiosIniciales={cambiosActaIniciales}
                plantillaTipo={plantillaTipo}
                infoEmpresa={infoEmpresa}
                onVolver={volverAlPanel}
                onCerrarEdicion={cerrarEdicion}
                onSolicitudEnviada={irAMisActas}
              />
            )
          ) : null}
          {seccion === 'asistente' ? (
            <AsistenteChat
              modo="pagina"
              onEditarActa={editarDesdeAsistente}
              onIrAMisActas={irAMisActas}
            />
          ) : null}
          {seccion === 'biblioteca' ? (
            <BibliotecaActas catalogos={catalogos} />
          ) : null}
          {seccion === 'mis-actas' ? (
            <BandejaActas modo="capturista" onEditar={editarDesdeBandeja} />
          ) : null}
          {seccion === 'revision' ? <BandejaActas modo="revisor" /> : null}
          {seccion === 'aprobacion' ? <BandejaActas modo="abogado" /> : null}
          {seccion === 'administracion' ? (
            <AdministracionActas
              versionActaInicial={versionActaInicial}
              onVersionActaInicialMostrada={limpiarVersionActaInicial}
            />
          ) : null}
          {seccion === 'ayuda' ? <Ayuda catalogos={catalogos} rol={usuario?.rol} /> : null}
          {seccion === 'empresa' ? (
            <InformacionEmpresa
              infoGuardada={infoEmpresa}
              onGuardar={setInfoEmpresa}
              puedeEditar={usuario?.rol === 'Administrador'}
            />
          ) : null}
          {seccion === 'perfil' ? <Perfil onCambiarVista={cambiarSeccion} /> : null}
          {seccion === 'administrador' ? <Administrador /> : null}
          {seccion === 'usuarios' &&
            (esAdministrador ? <AdministracionUsuarios /> : <UsuariosSuperAdmin />)}
          {seccion === 'vitacora' && <VitacoraSuperAdmin />}
          {seccion === 'estadisticas' && <EstadisticasSuperAdmin />}
          {seccion === 'seguridad' && <SeguridadSuperAdmin />}
          {seccion === 'guia-super-admin' && <GuiaSuperAdmin />}
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

