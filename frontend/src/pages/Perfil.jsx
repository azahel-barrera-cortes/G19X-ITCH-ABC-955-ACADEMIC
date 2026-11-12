import { useEffect, useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { actualizarPerfil, cambiarPassword, obtenerCodigoEmpresa, obtenerPerfil } from '../api/auth.js'
import { ROLES } from '../constants/roles.js'
import InformacionEmpresa from './InformacionEmpresa.jsx'

const ROLES_PERFIL = ROLES

export default function Perfil() {
  const { usuario, token, cerrarSesion, actualizarUsuario } = useAuth()
  const [perfil, setPerfil] = useState({ nombre_completo: '', rol: 'capturista' })
  const [password, setPassword] = useState({ actual: '', nueva: '', confirmar: '' })
  const [errorPerfil, setErrorPerfil] = useState(null)
  const [errorPassword, setErrorPassword] = useState(null)
  const [avisoPerfil, setAvisoPerfil] = useState(null)
  const [avisoPassword, setAvisoPassword] = useState(null)
  const [cargandoPerfil, setCargandoPerfil] = useState(false)
  const [cargandoPassword, setCargandoPassword] = useState(false)
  const [codigoCopiado, setCodigoCopiado] = useState(false)
  const [errorCodigo, setErrorCodigo] = useState(null)

  useEffect(() => {
    if (usuario) setPerfil({ nombre_completo: usuario.nombre_completo || '', rol: usuario.rol || 'capturista' })
  }, [usuario])

  useEffect(() => {
    if (!usuario || usuario.rol !== 'Administrador' || usuario.codigo_empresa) return undefined
    let montado = true
    setErrorCodigo(null)
    obtenerCodigoEmpresa(token)
      .then((perfilActualizado) => {
        if (montado) actualizarUsuario(perfilActualizado)
      })
      .catch((fallo) => {
        if (!montado) return
        // Compatibilidad con un backend que ya genera el código desde /auth/me,
        // pero aún no expone el endpoint dedicado.
        if (fallo.message === 'Not Found' || fallo.message.includes('404')) {
          obtenerPerfil(token)
            .then((perfilActualizado) => {
              if (!montado) return
              actualizarUsuario(perfilActualizado)
              if (!perfilActualizado.codigo_empresa) {
                setErrorCodigo('El backend todavía no ha generado el código de esta empresa.')
              }
            })
            .catch((errorPerfil) => {
              if (montado) setErrorCodigo(errorPerfil.message || 'No se pudo obtener el código de la empresa.')
            })
          return
        }
        setErrorCodigo(fallo.message || 'No se pudo obtener el código de la empresa.')
      })
    return () => {
      montado = false
    }
  }, [usuario, token, actualizarUsuario])

  const manejarCambioPerfil = (campo, valor) => setPerfil((p) => ({ ...p, [campo]: valor }))
  const manejarCambioPassword = (campo, valor) => setPassword((p) => ({ ...p, [campo]: valor }))

  const copiarCodigoEmpresa = async () => {
    try {
      await navigator.clipboard.writeText(usuario.codigo_empresa)
      setCodigoCopiado(true)
      window.setTimeout(() => setCodigoCopiado(false), 2000)
    } catch {
      setCodigoCopiado(false)
    }
  }

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

  const iniciales = (perfil.nombre_completo || usuario.email || 'U')
    .split(/\s+/)
    .slice(0, 2)
    .map((parte) => parte[0])
    .join('')
    .toUpperCase()
  const puedeEditarPerfil = usuario.rol === 'SuperAdministrador'

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <header className="overflow-hidden rounded-2xl bg-gradient-to-br from-corporativo-700 via-corporativo-700 to-corporativo-800 px-6 py-7 text-white shadow-lg sm:px-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white/15 text-xl font-bold tracking-wide ring-1 ring-white/25">
              {iniciales}
            </div>
            <div>
              <p className="text-sm font-medium text-corporativo-100">Configuración de cuenta</p>
              <h1 className="mt-1 text-2xl font-semibold tracking-tight">Mi perfil</h1>
              <p className="mt-1 text-sm text-corporativo-100">{usuario.email}</p>
            </div>
          </div>
          <span className="w-fit rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white">
            {ROLES_PERFIL.find((rol) => rol.valor === usuario.rol)?.etiqueta || usuario.rol}
          </span>
        </div>
        <p className="mt-6 max-w-2xl text-sm leading-6 text-corporativo-100">
          Administra tus datos de acceso y la información que se utilizará en las actas de tu sociedad.
        </p>
      </header>

      {usuario.rol === 'Administrador' && (
        <Tarjeta className="border-corporativo-200 bg-corporativo-50/70 p-6">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-base font-semibold text-corporativo-800">Código de tu empresa</h2>
              <p className="mt-1 max-w-2xl text-sm leading-5 text-corporativo-700">
                Comparte este código con tus empleados para vincular sus cuentas a tu empresa
                cuando se registren.
              </p>
              {errorCodigo && <p className="mt-2 text-sm font-medium text-red-700">{errorCodigo}</p>}
            </div>
            {usuario.codigo_empresa ? (
              <div className="flex items-center gap-3">
                <code className="rounded-lg border border-corporativo-200 bg-white px-4 py-2.5 text-base font-bold tracking-wider text-corporativo-800 shadow-sm">
                  {usuario.codigo_empresa}
                </code>
                <Boton variante="secundario" tamano="sm" onClick={copiarCodigoEmpresa}>
                  {codigoCopiado ? 'Copiado' : 'Copiar'}
                </Boton>
              </div>
            ) : (
              <span className="text-sm font-medium text-corporativo-700">Generando código…</span>
            )}
          </div>
        </Tarjeta>
      )}

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1.08fr)_minmax(360px,0.92fr)]">
        <div className="space-y-6">
          <Tarjeta className="overflow-hidden">
            <header className="border-b border-slate-100 bg-slate-50/70 px-6 py-5">
              <h2 className="text-base font-semibold text-slate-800">Información personal</h2>
              <p className="mt-1 text-sm text-slate-500">Actualiza los datos visibles de tu cuenta.</p>
            </header>
            <div className="p-6">
              {errorPerfil && <Alerta tono="error" className="mb-5">{errorPerfil}</Alerta>}
              {avisoPerfil && <Alerta tono="exito" className="mb-5">{avisoPerfil}</Alerta>}
              <form onSubmit={manejarGuardarPerfil} className="grid gap-5 md:grid-cols-2">
                <Campo etiqueta="Nombre completo" htmlFor="nombre_completo">
                  <input id="nombre_completo" type="text" className="campo" value={perfil.nombre_completo}
                    onChange={(e) => manejarCambioPerfil('nombre_completo', e.target.value)}
                    placeholder="Tu nombre completo" required disabled={!puedeEditarPerfil} />
                </Campo>
                <Campo etiqueta="Correo electrónico" htmlFor="email">
                  <input id="email" type="email" className="campo" value={usuario.email} disabled />
                </Campo>
                <Campo etiqueta="Rol" htmlFor="rol">
                  <input
                    id="rol"
                    type="text"
                    className="campo"
                    value={ROLES_PERFIL.find((rol) => rol.valor === perfil.rol)?.etiqueta || perfil.rol}
                    disabled
                    readOnly
                  />
                </Campo>
                {puedeEditarPerfil ? (
                  <div className="flex items-end justify-end md:col-span-2">
                    <Boton type="submit" variante="primario" cargando={cargandoPerfil}>Guardar cambios</Boton>
                  </div>
                ) : (
                  <p className="text-xs leading-5 text-slate-500 md:col-span-2">
                    Esta información es administrada por el SuperAdministrador.
                  </p>
                )}
              </form>
            </div>
          </Tarjeta>

          <Tarjeta className="overflow-hidden">
            <header className="border-b border-slate-100 bg-slate-50/70 px-6 py-5">
              <h2 className="text-base font-semibold text-slate-800">Cambiar contraseña</h2>
              <p className="mt-1 text-sm text-slate-500">Mantén segura tu cuenta con una contraseña actualizada.</p>
            </header>
            <div className="p-6">
              {errorPassword && <Alerta tono="error" className="mb-5">{errorPassword}</Alerta>}
              {avisoPassword && <Alerta tono="exito" className="mb-5">{avisoPassword}</Alerta>}
              <form onSubmit={manejarGuardarPassword} className="space-y-5">
                <Campo etiqueta="Contraseña actual" htmlFor="password_actual">
                  <input id="password_actual" type="password" className="campo"
                    value={password.actual} onChange={(e) => manejarCambioPassword('actual', e.target.value)}
                    placeholder="Tu contraseña actual" autoComplete="current-password" />
                </Campo>
                <div className="grid gap-5 md:grid-cols-2">
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
                </div>
                <div className="flex justify-end">
                  <Boton type="submit" variante="primario" cargando={cargandoPassword}>Cambiar contraseña</Boton>
                </div>
              </form>
            </div>
          </Tarjeta>

          <Tarjeta className="border-red-200 bg-red-50/70 p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-sm font-semibold text-red-800">Sesión</h2>
                <p className="mt-1 text-sm text-red-700">Cierra sesión de forma segura en este dispositivo.</p>
              </div>
              <Boton variante="peligro" onClick={() => { cerrarSesion() }}>
                Cerrar sesión
              </Boton>
            </div>
          </Tarjeta>
        </div>

        <div className="rounded-2xl bg-white/60 p-1">
          <InformacionEmpresa puedeEditar={usuario.rol === 'Administrador'} />
        </div>
      </div>
    </div>
  )
}
