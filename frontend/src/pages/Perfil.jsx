import { useEffect, useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { actualizarPerfil, cambiarPassword } from '../api/auth.js'
import { ROLES, etiquetaRol, seccionesConAcceso } from '../constants/roles.js'

const ROLES_PERFIL = ROLES

export default function Perfil({ onCambiarVista = null }) {
  const { usuario, token, cerrarSesion, actualizarUsuario } = useAuth()
  const [perfil, setPerfil] = useState({ nombre_completo: '', rol: 'capturista' })
  const [password, setPassword] = useState({ actual: '', nueva: '', confirmar: '' })
  const [errorPerfil, setErrorPerfil] = useState(null)
  const [errorPassword, setErrorPassword] = useState(null)
  const [avisoPerfil, setAvisoPerfil] = useState(null)
  const [avisoPassword, setAvisoPassword] = useState(null)
  const [cargandoPerfil, setCargandoPerfil] = useState(false)
  const [cargandoPassword, setCargandoPassword] = useState(false)

  useEffect(() => {
    if (usuario) setPerfil({ nombre_completo: usuario.nombre_completo || '', rol: usuario.rol || 'capturista' })
  }, [usuario])

  const manejarCambioPerfil = (campo, valor) => setPerfil((p) => ({ ...p, [campo]: valor }))
  const manejarCambioPassword = (campo, valor) => setPassword((p) => ({ ...p, [campo]: valor }))

  const manejarGuardarPerfil = async (e) => {
    e.preventDefault()
    setErrorPerfil(null); setAvisoPerfil(null); setCargandoPerfil(true)
    try {
      const actualizado = await actualizarPerfil(token, perfil)
      actualizarUsuario(actualizado)
      setAvisoPerfil('Perfil actualizado.')
    } catch (fallo) { setErrorPerfil(fallo.message || 'Error al actualizar.') }
    finally { setCargandoPerfil(false) }
  }

  const manejarGuardarPassword = async (e) => {
    e.preventDefault()
    setErrorPassword(null); setAvisoPassword(null)
    if (password.nueva !== password.confirmar) { setErrorPassword('Las contraseñas no coinciden.'); return }
    setCargandoPassword(true)
    try {
      await cambiarPassword(token, password.nueva)
      setAvisoPassword('Contraseña actualizada. Inicia sesión de nuevo.')
      setPassword({ actual: '', nueva: '', confirmar: '' })
    } catch (fallo) { setErrorPassword(fallo.message || 'Error al cambiar contraseña.') }
    finally { setCargandoPassword(false) }
  }

  if (!usuario) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <Alerta tono="info" titulo="Acceso requerido">Inicia sesión para ver tu perfil.</Alerta>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 py-6">
      <header>
        <h1 className="text-xl font-semibold text-corporativo-700">Mi perfil</h1>
        <p className="text-sm text-slate-500">Gestiona tu información personal y tu contraseña.</p>
      </header>

      {/* Funciones permitidas al rol: es lo primero que ve el usuario al entrar. */}
      <Tarjeta>
        <header className="mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">
            Funciones disponibles para tu rol
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Tu rol actual es <strong>{etiquetaRol(usuario.rol)}</strong>. Estas son las
            secciones del sistema habilitadas para ti; el resto permanece oculto y
            protegido también en el servidor.
          </p>
        </header>
        <div className="grid gap-3 sm:grid-cols-2">
          {seccionesConAcceso(usuario.rol).map((seccion) => (
            <button
              key={seccion.id}
              type="button"
              onClick={() => onCambiarVista && onCambiarVista(seccion.id)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-left transition hover:border-corporativo-300 hover:bg-corporativo-50"
            >
              <span className="block text-sm font-semibold text-corporativo-700">
                {seccion.etiqueta}
              </span>
              <span className="mt-0.5 block text-xs text-slate-500">{seccion.descripcion}</span>
            </button>
          ))}
        </div>
      </Tarjeta>

      <Tarjeta>
        <header className="mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">Información personal</h2>
        </header>
        {errorPerfil && <Alerta tono="error" className="mb-4">{errorPerfil}</Alerta>}
        {avisoPerfil && <Alerta tono="exito" className="mb-4">{avisoPerfil}</Alerta>}
        <form onSubmit={manejarGuardarPerfil} className="grid gap-4 md:grid-cols-2">
          <Campo etiqueta="Correo electrónico" htmlFor="email">
            <input id="email" type="email" className="campo" value={usuario.email} disabled />
          </Campo>
          <Campo etiqueta="Nombre completo" htmlFor="nombre_completo">
            <input id="nombre_completo" type="text" className="campo" value={perfil.nombre_completo}
              onChange={(e) => manejarCambioPerfil('nombre_completo', e.target.value)}
              placeholder="Tu nombre completo" required />
          </Campo>
          <Campo etiqueta="Rol" htmlFor="rol">
            <select id="rol" className="campo" value={perfil.rol}
              onChange={(e) => manejarCambioPerfil('rol', e.target.value)}
              disabled={usuario.rol !== 'Administrador'}>
              {ROLES_PERFIL.map((rol) => (
                <option key={rol.valor} value={rol.valor}>{rol.etiqueta}</option>
              ))}
            </select>
          </Campo>
          <div className="md:col-span-2 flex justify-end">
            <Boton type="submit" variante="primario" cargando={cargandoPerfil}>Guardar cambios</Boton>
          </div>
        </form>
      </Tarjeta>

      <Tarjeta>
        <header className="mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600">Cambiar contraseña</h2>
        </header>
        {errorPassword && <Alerta tono="error" className="mb-4">{errorPassword}</Alerta>}
        {avisoPassword && <Alerta tono="exito" className="mb-4">{avisoPassword}</Alerta>}
        <form onSubmit={manejarGuardarPassword} className="space-y-4">
          <Campo etiqueta="Contraseña actual" htmlFor="password_actual">
            <input id="password_actual" type="password" className="campo"
              value={password.actual} onChange={(e) => manejarCambioPassword('actual', e.target.value)}
              placeholder="Tu contraseña actual" autoComplete="current-password" />
          </Campo>
          <Campo etiqueta="Nueva contraseña" htmlFor="password_nueva">
            <input id="password_nueva" type="password" className="campo"
              value={password.nueva} onChange={(e) => manejarCambioPassword('nueva', e.target.value)}
              placeholder="Mínimo 6 caracteres" autoComplete="new-password" minLength={6} required />
          </Campo>
          <Campo etiqueta="Confirmar nueva contraseña" htmlFor="password_confirmar">
            <input id="password_confirmar" type="password" className="campo"
              value={password.confirmar} onChange={(e) => manejarCambioPassword('confirmar', e.target.value)}
              placeholder="Repite la nueva contraseña" autoComplete="new-password" required />
          </Campo>
          <div className="flex justify-end">
            <Boton type="submit" variante="primario" cargando={cargandoPassword}>Cambiar contraseña</Boton>
          </div>
        </form>
      </Tarjeta>

      <Tarjeta className="border-red-200 bg-red-50">
        <header className="mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-red-700">Sesión</h2>
        </header>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-red-700">Cierra sesión de forma segura.</p>
          <Boton variante="peligro" onClick={() => { cerrarSesion() }}>
            Cerrar sesión
          </Boton>
        </div>
      </Tarjeta>
    </div>
  )
}
