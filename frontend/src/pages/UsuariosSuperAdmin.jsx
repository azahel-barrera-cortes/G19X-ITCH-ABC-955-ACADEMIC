import { Fragment, useEffect, useMemo, useState } from 'react'

import { ROLES, etiquetaRol } from '../constants/roles.js'
import { useAuth } from '../context/AuthContext.jsx'
import {
  actualizarUsuario,
  crearUsuario,
  eliminarUsuario,
  listarUsuarios,
} from '../api/client.js'

import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import Indicador from '../components/ui/Indicador.jsx'

const ESTATUS = [
  { valor: 'todos', etiqueta: 'Todos' },
  { valor: 'activo', etiqueta: 'Activo' },
  { valor: 'inactivo', etiqueta: 'No activo' },
]

const inicialesDe = (nombreCompleto = '') => {
  const partes = nombreCompleto.trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  return `${partes[0].charAt(0)}${partes[partes.length - 1].charAt(0)}`.toUpperCase()
}

const coincideFiltro = (usuario, { nombre, correo, rol, estatus }) => {
  const partes = usuario.nombre_completo.trim().split(/\s+/).filter(Boolean)
  const nombreOk =
    !nombre ||
    partes.some((parte) => parte.toLowerCase().includes(nombre.toLowerCase()))
  const correoOk =
    !correo || usuario.email.toLowerCase().includes(correo.toLowerCase())
  const rolOk = rol === 'todos' || usuario.rol === rol
  const estatusOk =
    estatus === 'todos' || (estatus === 'activo') === usuario.activo
  return nombreOk && correoOk && rolOk && estatusOk
}

const FORMULARIO_INICIAL = {
  email: '',
  nombre_completo: '',
  password: '',
  rol: 'capturista',
}

export default function UsuariosSuperAdmin() {
  const { usuario: sesion } = useAuth()
  const esYo = (id) => sesion && sesion.id === id

  const [usuarios, setUsuarios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [filtros, setFiltros] = useState({
    nombre: '',
    correo: '',
    rol: 'todos',
    estatus: 'todos',
  })
  const [actualizandoId, setActualizandoId] = useState(null)
  const [alerta, setAlerta] = useState(null)
  const [panel, setPanel] = useState(null)
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL)
  const [guardandoFormulario, setGuardandoFormulario] = useState(false)

  useEffect(() => {
    let montado = true
    setCargando(true)
    setAlerta(null)

    listarUsuarios()
      .then((data) => {
        if (montado) {
          console.log('Usuarios cargados:', data)
          setUsuarios(Array.isArray(data) ? data : [])
        }
      })
      .catch((error) => {
        if (montado) {
          setUsuarios([])
          const status = error.response?.status || 'desconocido'
          const detalle = error.response?.data?.detail || error.message || 'No se pudieron cargar los usuarios.'
          console.error('Error cargando usuarios:', {
            status,
            detalle,
            data: error.response?.data,
            url: error.config?.url,
            method: error.config?.method,
          })
          setAlerta({
            tono: 'error',
            mensaje: `Error ${status}: ${detalle}`,
          })
        }
      })
      .finally(() => {
        if (montado) setCargando(false)
      })

    return () => {
      montado = false
    }
  }, [])

  useEffect(() => {
    if (alerta && alerta.tono === 'exito') {
      const temporizador = setTimeout(() => setAlerta(null), 4000)
      return () => clearTimeout(temporizador)
    }
  }, [alerta])

  const usuariosFiltrados = useMemo(
    () => usuarios.filter((u) => coincideFiltro(u, filtros)),
    [usuarios, filtros]
  )

  const cambiarFiltro = (campo, valor) =>
    setFiltros((previo) => ({ ...previo, [campo]: valor }))

  const limpiarFiltros = () =>
    setFiltros({ nombre: '', correo: '', rol: 'todos', estatus: 'todos' })

  const guardarCambios = async (userId, cambios) => {
    setActualizandoId(userId)
    setAlerta(null)
    try {
      await actualizarUsuario(userId, cambios)
      const actualizados = await listarUsuarios()
      setUsuarios(Array.isArray(actualizados) ? actualizados : [])
      setAlerta({ tono: 'exito', mensaje: 'Usuario actualizado correctamente.' })
    } catch (error) {
      const detalle =
        error.response?.data?.detail || error.message || 'No se pudo actualizar el usuario.'
      setAlerta({ tono: 'error', mensaje: detalle })
    } finally {
      setActualizandoId(null)
    }
  }

  const cambiarEstatus = async (userId, usuario) => {
    await guardarCambios(userId, { activo: !usuario.activo })
  }

  const cambiarRol = async (userId, rol) => {
    await guardarCambios(userId, { rol })
  }

  const abrirCrear = () => {
    setFormulario(FORMULARIO_INICIAL)
    setPanel('crear')
    setAlerta(null)
  }

  const abrirEditar = (usuario) => {
    setFormulario({
      email: usuario.email,
      nombre_completo: usuario.nombre_completo,
      password: '',
      rol: usuario.rol,
    })
    setPanel({ tipo: 'editar', usuarioId: usuario.id })
    setAlerta(null)
  }

  const cerrarPanel = () => {
    if (!guardandoFormulario) setPanel(null)
  }

  const cambiarFormulario = (campo, valor) =>
    setFormulario((previo) => ({ ...previo, [campo]: valor }))

  const guardarFormulario = async (evento) => {
    evento.preventDefault()
    setGuardandoFormulario(true)
    setAlerta(null)
    try {
      if (panel === 'crear') {
        await crearUsuario(formulario)
        setAlerta({ tono: 'exito', mensaje: 'Usuario creado correctamente.' })
      } else {
        const { email, password, ...cambios } = formulario
        await actualizarUsuario(panel.usuarioId, {
          ...cambios,
          ...(password ? { password } : {}),
        })
        setAlerta({ tono: 'exito', mensaje: 'Información del usuario actualizada.' })
      }
      const actualizados = await listarUsuarios()
      setUsuarios(Array.isArray(actualizados) ? actualizados : [])
      setPanel(null)
    } catch (error) {
      const detalle =
        error.response?.data?.detail || error.message || 'No se pudo guardar el usuario.'
      setAlerta({ tono: 'error', mensaje: detalle })
    } finally {
      setGuardandoFormulario(false)
    }
  }

  const borrarUsuario = async (usuario) => {
    if (esYo(usuario.id)) return
    const confirmado = window.confirm(
      `¿Eliminar a ${usuario.nombre_completo}? Esta acción no se puede deshacer.`,
    )
    if (!confirmado) return

    setActualizandoId(usuario.id)
    setAlerta(null)
    try {
      await eliminarUsuario(usuario.id)
      setUsuarios((previos) => previos.filter((item) => item.id !== usuario.id))
      setAlerta({ tono: 'exito', mensaje: 'Usuario eliminado correctamente.' })
    } catch (error) {
      const detalle =
        error.response?.data?.detail || error.message || 'No se pudo eliminar el usuario.'
      setAlerta({ tono: 'error', mensaje: detalle })
    } finally {
      setActualizandoId(null)
    }
  }

  const rolesDisponiblesPara = (usuario) =>
    ROLES.filter(
      (rol) => rol.valor !== 'SuperAdministrador' || esYo(usuario.id),
    )

  const usuarioEnEdicion =
    panel && panel !== 'crear'
      ? usuarios.find((usuario) => usuario.id === panel.usuarioId)
      : null

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-semibold text-corporativo-600">
              Usuarios
            </p>
            <h1 className="text-xl font-bold text-slate-900">
              Gestión de Usuarios SuperAdmin
            </h1>
          </div>
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-[1480px] flex-col gap-8 px-4 py-8 md:px-8 lg:flex-row lg:items-start">
        <section className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-white p-7 shadow-sm ring-1 ring-slate-100 lg:p-8">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-4 mb-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                Gestión de Usuarios SuperAdmin
              </h2>
              <p className="mt-1 text-sm text-slate-500">
                Administra todos los usuarios del sistema. Usa los filtros para
                buscar por nombre, apellido, rol o estatus.
              </p>
            </div>
          </div>

          {alerta && <Alerta tono={alerta.tono}>{alerta.mensaje}</Alerta>}

          <div className="mb-10">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-corporativo-600 mb-3">
              Buscador y filtros
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Campo etiqueta="Nombre">
                <input
                  id="filtro-nombre"
                  type="text"
                  className="campo"
                  value={filtros.nombre}
                  onChange={(e) => cambiarFiltro('nombre', e.target.value)}
                  placeholder="Ej. Ana"
                />
              </Campo>
              <Campo etiqueta="Correo">
                <input
                  id="filtro-correo"
                  type="text"
                  className="campo"
                  value={filtros.correo}
                  onChange={(e) => cambiarFiltro('correo', e.target.value)}
                  placeholder="Ej. usuario@correo.com"
                />
              </Campo>
              <Campo etiqueta="Rol">
                <select
                  id="filtro-rol"
                  className="campo"
                  value={filtros.rol}
                  onChange={(e) => cambiarFiltro('rol', e.target.value)}
                >
                  <option value="todos">Todos los roles</option>
                  {ROLES.map((rol) => (
                    <option key={rol.valor} value={rol.valor}>
                      {rol.etiqueta}
                    </option>
                  ))}
                </select>
              </Campo>
              <Campo etiqueta="Estatus">
                <select
                  id="filtro-estatus"
                  className="campo"
                  value={filtros.estatus}
                  onChange={(e) => cambiarFiltro('estatus', e.target.value)}
                >
                  {ESTATUS.map((e) => (
                    <option key={e.valor} value={e.valor}>
                      {e.etiqueta}
                    </option>
                  ))}
                </select>
              </Campo>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <Boton variante="secundario" tamano="sm" onClick={limpiarFiltros}>
                Limpiar filtros
              </Boton>
              <span className="text-sm text-slate-600">
                {usuariosFiltrados.length} de {usuarios.length} perfil(es)
                encontrado(s)
              </span>
            </div>
          </div>

          {!cargando && usuarios.length === 0 && (
            <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
              No hay usuarios registrados en el sistema.
            </div>
          )}

          {cargando && usuarios.length === 0 && (
            <div className="mt-8 flex items-center justify-center gap-2 text-sm text-slate-500">
              <Indicador /> Cargando usuarios…
            </div>
          )}

          {!cargando && usuarios.length > 0 && usuariosFiltrados.length === 0 && (
            <div className="mt-8 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-sm text-slate-500">
              No hay usuarios que coincidan con los filtros seleccionados.
            </div>
          )}

          {!cargando && usuariosFiltrados.length > 0 && (
            <div className="rounded-xl border border-slate-100">
              <table className="w-full table-fixed text-left border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50">
                    <th className="w-[34%] px-5 py-4 text-xs font-semibold text-slate-500 uppercase">
                      Nombre
                    </th>
                    <th className="w-[28%] px-5 py-4 text-xs font-semibold text-slate-500 uppercase">
                      Correo
                    </th>
                    <th className="w-[20%] px-5 py-4 text-xs font-semibold text-slate-500 uppercase">
                      Rol
                    </th>
                    <th className="w-[18%] px-5 py-4 text-xs font-semibold text-slate-500 uppercase">
                      Estatus
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {usuariosFiltrados.map((usuario) => (
                    <Fragment key={usuario.id}>
                      <tr
                        className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                      >
                        <td className="px-5 py-5">
                          <div className="flex items-center gap-3">
                            <div
                              className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-corporativo-100 text-xs font-bold text-corporativo-700 shadow-sm"
                              aria-hidden="true"
                            >
                              {inicialesDe(usuario.nombre_completo)}
                            </div>
                            <div>
                              <div className="text-sm font-semibold leading-tight text-slate-900">
                                {usuario.nombre_completo}
                              </div>
                              <div className="text-xs text-slate-500">
                                {usuario.email}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-5 py-5">
                          <div className="text-sm text-slate-700">{usuario.email}</div>
                        </td>
                        <td className="px-5 py-5">
                          <Etiqueta
                            tono={
                              usuario.rol === 'SuperAdministrador' ||
                                usuario.rol === 'Administrador'
                                ? 'info'
                                : 'neutral'
                            }
                            className="text-xs px-2 py-1"
                          >
                            {etiquetaRol(usuario.rol)}
                          </Etiqueta>
                        </td>
                        <td className="px-5 py-5">
                          <Etiqueta
                            tono={usuario.activo ? 'exito' : 'error'}
                            className="text-xs px-2 py-1"
                          >
                            {usuario.activo ? 'Activo' : 'No activo'}
                          </Etiqueta>
                        </td>
                      </tr>
                      <tr className="border-b border-slate-100 bg-slate-50/50">
                        <td colSpan="4" className="px-5 pb-5 pt-1">
                          <div className="flex flex-wrap items-center gap-3">
                            <span className="mr-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                              Acciones
                            </span>
                          <select
                            value={usuario.rol}
                            onChange={(e) => cambiarRol(usuario.id, e.target.value)}
                            disabled={actualizandoId === usuario.id || esYo(usuario.id)}
                            title={
                              esYo(usuario.id)
                                ? 'El rol del SuperAdministrador actual no se puede cambiar'
                                : undefined
                            }
                            className="campo w-48 bg-white px-3 py-2 text-xs text-slate-700 focus:border-corporativo-400 focus:outline-none"
                          >
                            {rolesDisponiblesPara(usuario).map((rol) => (
                              <option key={rol.valor} value={rol.valor}>
                                {rol.etiqueta}
                              </option>
                            ))}
                          </select>
                          <Boton
                            variante="secundario"
                            tamano="sm"
                            className="min-w-[92px]"
                            cargando={actualizandoId === usuario.id}
                            disabled={
                              actualizandoId === usuario.id ||
                              (esYo(usuario.id) && usuario.activo)
                            }
                            onClick={() => cambiarEstatus(usuario.id, usuario)}
                            title={
                              esYo(usuario.id) && usuario.activo
                                ? 'No puedes desactivar tu propio usuario'
                                : undefined
                            }
                          >
                            {usuario.activo ? 'Desactivar' : 'Activar'}
                          </Boton>
                          <Boton
                            variante="secundario"
                            tamano="sm"
                            className="min-w-[64px]"
                            disabled={actualizandoId === usuario.id}
                            onClick={() => abrirEditar(usuario)}
                          >
                            Editar
                          </Boton>
                          <Boton
                            variante="peligro"
                            tamano="sm"
                            className="min-w-[78px]"
                            disabled={actualizandoId === usuario.id || esYo(usuario.id)}
                            onClick={() => borrarUsuario(usuario)}
                            title={esYo(usuario.id) ? 'No puedes eliminar tu propio usuario' : undefined}
                          >
                            Eliminar
                          </Boton>
                          </div>
                      </td>
                      </tr>
                    </Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <aside className="w-full shrink-0 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm ring-1 ring-slate-100 lg:w-[22rem]">
          <div className="mb-5 flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
                Administración
              </p>
              <h2 className="mt-1 text-lg font-bold text-slate-900">
                Usuarios
              </h2>
              <p className="mt-1 text-sm leading-5 text-slate-500">
                Crea nuevos accesos o actualiza la información de un usuario.
              </p>
            </div>
            {panel && (
              <button
                type="button"
                onClick={cerrarPanel}
                className="text-xl leading-none text-slate-400 hover:text-slate-700"
                aria-label="Cerrar formulario"
              >
                ×
              </button>
            )}
          </div>

          {!panel ? (
            <div className="rounded-xl border border-corporativo-100 bg-corporativo-50 p-4">
              <p className="text-sm font-semibold text-corporativo-800">
                Acciones rápidas
              </p>
              <p className="mt-1 text-xs leading-5 text-corporativo-700">
                Elige una acción para comenzar a administrar tus usuarios.
              </p>
              <Boton className="mt-4 w-full" onClick={abrirCrear}>
                + Registrar nuevo usuario
              </Boton>
            </div>
          ) : (
            <form onSubmit={guardarFormulario} className="space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h3 className="font-semibold text-slate-900">
                  {panel === 'crear' ? 'Registrar usuario' : 'Editar usuario'}
                </h3>
                <p className="mt-1 text-xs text-slate-500">
                  {panel === 'crear'
                    ? 'Completa los datos para crear un nuevo acceso.'
                    : 'Modifica los datos necesarios y guarda los cambios.'}
                </p>
              </div>
              <Campo etiqueta="Nombre completo" htmlFor="usuario-nombre" requerido>
                <input
                  id="usuario-nombre"
                  className="campo"
                  value={formulario.nombre_completo}
                  onChange={(e) => cambiarFormulario('nombre_completo', e.target.value)}
                  placeholder="Ana María Ruiz"
                  minLength={3}
                  required
                />
              </Campo>
              <Campo etiqueta="Correo electrónico" htmlFor="usuario-email" requerido>
                <input
                  id="usuario-email"
                  type="email"
                  className="campo"
                  value={formulario.email}
                  onChange={(e) => cambiarFormulario('email', e.target.value)}
                  placeholder="usuario@empresa.com"
                  disabled={panel !== 'crear'}
                  required
                />
              </Campo>
              <Campo etiqueta="Rol" htmlFor="usuario-rol" requerido>
                <select
                  id="usuario-rol"
                  className="campo"
                  value={formulario.rol}
                  onChange={(e) => cambiarFormulario('rol', e.target.value)}
                >
                  {ROLES.filter(
                    (rol) =>
                      rol.valor !== 'SuperAdministrador' ||
                      usuarioEnEdicion?.id === sesion?.id,
                  ).map((rol) => (
                    <option key={rol.valor} value={rol.valor}>
                      {rol.etiqueta}
                    </option>
                  ))}
                </select>
              </Campo>
              <Campo
                etiqueta={panel === 'crear' ? 'Contraseña' : 'Nueva contraseña'}
                htmlFor="usuario-password"
                requerido={panel === 'crear'}
                ayuda={panel === 'crear' ? 'Mínimo 6 caracteres.' : 'Déjalo vacío para conservarla.'}
              >
                <input
                  id="usuario-password"
                  type="password"
                  className="campo"
                  value={formulario.password}
                  onChange={(e) => cambiarFormulario('password', e.target.value)}
                  placeholder={panel === 'crear' ? 'Mínimo 6 caracteres' : 'Sin cambios'}
                  minLength={6}
                  required={panel === 'crear'}
                  autoComplete="new-password"
                />
              </Campo>
              <div className="flex gap-2 pt-2">
                <Boton
                  type="button"
                  variante="secundario"
                  className="flex-1"
                  onClick={cerrarPanel}
                >
                  Cancelar
                </Boton>
                <Boton type="submit" className="flex-1" cargando={guardandoFormulario}>
                  Guardar
                </Boton>
              </div>
            </form>
          )}
        </aside>
      </div>
    </div>
  )
}
