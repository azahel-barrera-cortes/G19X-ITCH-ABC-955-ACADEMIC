import { useCallback, useEffect, useMemo, useState } from 'react'
import { crearUsuario, listarUsuarios, actualizarUsuario, mensajeDeError } from '../api/client.js'
import { etiquetaRol } from '../constants/roles.js'
import { useAuth } from '../context/AuthContext.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Etiqueta from '../components/ui/Etiqueta.jsx'
import Indicador from '../components/ui/Indicador.jsx'

const ROLES_EMPRESA = [
  { valor: 'capturista', etiqueta: 'Capturista' },
  { valor: 'revisor', etiqueta: 'Revisor' },
  { valor: 'abogado_responsable', etiqueta: 'Abogado' },
]
const ESTADOS = [
  { valor: 'todos', etiqueta: 'Todos los estados' },
  { valor: 'activo', etiqueta: 'Activos' },
  { valor: 'inactivo', etiqueta: 'Inactivos' },
]
const FORMULARIO_INICIAL = {
  nombre_completo: '',
  email: '',
  password: '',
  rol: 'capturista',
}

export default function AdministracionUsuarios() {
  const { usuario: sesion } = useAuth()
  const [usuarios, setUsuarios] = useState([])
  const [cargando, setCargando] = useState(true)
  const [operando, setOperando] = useState(null)
  const [panel, setPanel] = useState(null)
  const [formulario, setFormulario] = useState(FORMULARIO_INICIAL)
  const [filtros, setFiltros] = useState({ busqueda: '', rol: 'todos', estado: 'todos' })
  const [alerta, setAlerta] = useState(null)

  const cargarUsuarios = useCallback(async () => {
    setCargando(true)
    try {
      const resultado = await listarUsuarios()
      setUsuarios(Array.isArray(resultado) ? resultado : [])
    } catch (fallo) {
      setAlerta({ tono: 'error', mensaje: await mensajeDeError(fallo) })
    } finally {
      setCargando(false)
    }
  }, [])

  useEffect(() => {
    cargarUsuarios()
  }, [cargarUsuarios])

  const filtrados = useMemo(() => {
    const termino = filtros.busqueda.trim().toLowerCase()
    return usuarios.filter((usuario) => {
      const coincideTexto =
        !termino ||
        `${usuario.nombre_completo} ${usuario.email}`.toLowerCase().includes(termino)
      const coincideRol = filtros.rol === 'todos' || usuario.rol === filtros.rol
      const coincideEstado =
        filtros.estado === 'todos' ||
        (filtros.estado === 'activo') === usuario.activo
      return coincideTexto && coincideRol && coincideEstado
    })
  }, [usuarios, filtros])

  const abrirCrear = () => {
    setFormulario(FORMULARIO_INICIAL)
    setPanel('crear')
    setAlerta(null)
  }

  const abrirEditar = (usuario) => {
    setFormulario({
      nombre_completo: usuario.nombre_completo,
      email: usuario.email,
      password: '',
      rol: usuario.rol,
    })
    setPanel({ tipo: 'editar', usuarioId: usuario.id })
    setAlerta(null)
  }

  const guardarFormulario = async (evento) => {
    evento.preventDefault()
    setOperando('formulario')
    setAlerta(null)
    try {
      if (panel === 'crear') {
        await crearUsuario({
          ...formulario,
          codigo_empresa: sesion?.codigo_empresa,
        })
        setAlerta({ tono: 'exito', mensaje: 'Usuario agregado a la empresa.' })
      } else {
        await actualizarUsuario(panel.usuarioId, {
          nombre_completo: formulario.nombre_completo,
          rol: formulario.rol,
          ...(formulario.password ? { password: formulario.password } : {}),
        })
        setAlerta({ tono: 'exito', mensaje: 'Usuario actualizado correctamente.' })
      }
      setPanel(null)
      await cargarUsuarios()
    } catch (fallo) {
      setAlerta({ tono: 'error', mensaje: await mensajeDeError(fallo) })
    } finally {
      setOperando(null)
    }
  }

  const cambiarAcceso = async (usuario) => {
    setOperando(usuario.id)
    setAlerta(null)
    try {
      await actualizarUsuario(usuario.id, { activo: !usuario.activo })
      await cargarUsuarios()
      setAlerta({
        tono: 'exito',
        mensaje: usuario.activo
          ? `Se desactivó el acceso de ${usuario.nombre_completo}.`
          : `Se activó el acceso de ${usuario.nombre_completo}.`,
      })
    } catch (fallo) {
      setAlerta({ tono: 'error', mensaje: await mensajeDeError(fallo) })
    } finally {
      setOperando(null)
    }
  }

  const cambiarRol = async (usuario, rol) => {
    setOperando(usuario.id)
    setAlerta(null)
    try {
      await actualizarUsuario(usuario.id, { rol })
      await cargarUsuarios()
      setAlerta({ tono: 'exito', mensaje: `Rol actualizado para ${usuario.nombre_completo}.` })
    } catch (fallo) {
      setAlerta({ tono: 'error', mensaje: await mensajeDeError(fallo) })
    } finally {
      setOperando(null)
    }
  }

  const usuariosActivos = usuarios.filter((usuario) => usuario.activo).length
  const usuariosInactivos = usuarios.length - usuariosActivos
  const enEdicion =
    panel && panel !== 'crear'
      ? usuarios.find((usuario) => usuario.id === panel.usuarioId)
      : null

  return (
    <div className="space-y-6">
      <header className="rounded-2xl bg-corporativo-700 px-6 py-6 text-white shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-corporativo-100">
          Espacio de trabajo · usuarios
        </p>
        <div className="mt-2 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Administración de usuarios</h1>
            <p className="mt-1 max-w-2xl text-sm text-corporativo-100">
              Administra los accesos, roles y datos de las personas vinculadas a tu empresa.
            </p>
          </div>
          <div className="rounded-xl border border-white/20 bg-white/10 px-4 py-2">
            <p className="text-[11px] uppercase tracking-wide text-corporativo-100">Código de empresa</p>
            <p className="font-mono text-sm font-semibold">{sesion?.codigo_empresa || 'Se asignará al cargar'}</p>
          </div>
        </div>
      </header>

      {alerta ? <Alerta tono={alerta.tono}>{alerta.mensaje}</Alerta> : null}

      <section className="grid gap-3 sm:grid-cols-3">
        <Resumen titulo="Personas en la empresa" valor={usuarios.length} />
        <Resumen titulo="Accesos activos" valor={usuariosActivos} tono="text-emerald-700" />
        <Resumen titulo="Accesos desactivados" valor={usuariosInactivos} tono="text-amber-700" />
      </section>

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="font-semibold text-slate-900">Directorio de la empresa</h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Los permisos se asignan por rol y pueden revocarse sin eliminar el perfil.
            </p>
          </div>
          <Boton onClick={abrirCrear}>Agregar usuario</Boton>
        </div>

        <div className="grid gap-3 border-b border-slate-100 bg-slate-50/70 p-4 md:grid-cols-[minmax(220px,1fr)_220px_220px]">
          <Campo etiqueta="Buscar persona" htmlFor="usuarios-busqueda">
            <input
              id="usuarios-busqueda"
              className="campo"
              value={filtros.busqueda}
              onChange={(evento) => setFiltros({ ...filtros, busqueda: evento.target.value })}
              placeholder="Nombre o correo"
            />
          </Campo>
          <Campo etiqueta="Rol" htmlFor="usuarios-rol">
            <select
              id="usuarios-rol"
              className="campo"
              value={filtros.rol}
              onChange={(evento) => setFiltros({ ...filtros, rol: evento.target.value })}
            >
              <option value="todos">Todos los roles</option>
              {ROLES_EMPRESA.map((rol) => (
                <option key={rol.valor} value={rol.valor}>{rol.etiqueta}</option>
              ))}
            </select>
          </Campo>
          <Campo etiqueta="Estado de acceso" htmlFor="usuarios-estado">
            <select
              id="usuarios-estado"
              className="campo"
              value={filtros.estado}
              onChange={(evento) => setFiltros({ ...filtros, estado: evento.target.value })}
            >
              {ESTADOS.map((estado) => (
                <option key={estado.valor} value={estado.valor}>{estado.etiqueta}</option>
              ))}
            </select>
          </Campo>
        </div>

        {cargando && !usuarios.length ? (
          <div className="flex items-center justify-center gap-2 px-5 py-12 text-sm text-slate-500">
            <Indicador /> Cargando el directorio…
          </div>
        ) : !filtrados.length ? (
          <p className="px-5 py-12 text-center text-sm text-slate-500">
            {usuarios.length
              ? 'No hay usuarios que coincidan con los filtros.'
              : 'Aún no hay usuarios registrados en esta empresa.'}
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {filtrados.map((usuario) => (
              <article
                key={usuario.id}
                className="grid gap-4 px-5 py-4 lg:grid-cols-[minmax(220px,1fr)_180px_140px_auto] lg:items-center"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-corporativo-50 text-sm font-bold text-corporativo-700">
                    {usuario.nombre_completo
                      .split(/\s+/)
                      .map((parte) => parte[0])
                      .slice(0, 2)
                      .join('')
                      .toUpperCase()}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-slate-900">{usuario.nombre_completo}</p>
                    <p className="truncate text-xs text-slate-500">{usuario.email}</p>
                  </div>
                </div>
                <label className="space-y-1 text-xs text-slate-500">
                  <span className="block">Rol del usuario</span>
                  <select
                    className="campo py-1.5 text-xs"
                    value={usuario.rol}
                    disabled={operando === usuario.id}
                    onChange={(evento) => cambiarRol(usuario, evento.target.value)}
                    aria-label={`Rol de ${usuario.nombre_completo}`}
                  >
                    {ROLES_EMPRESA.map((rol) => (
                      <option key={rol.valor} value={rol.valor}>{rol.etiqueta}</option>
                    ))}
                  </select>
                </label>
                <div>
                  <p className="mb-1 text-xs text-slate-500">Acceso</p>
                  <Etiqueta tono={usuario.activo ? 'exito' : 'error'}>
                    {usuario.activo ? 'Activo' : 'Desactivado'}
                  </Etiqueta>
                </div>
                <div className="flex flex-wrap gap-2 lg:justify-end">
                  <Boton
                    variante="secundario"
                    tamano="sm"
                    disabled={operando === usuario.id}
                    onClick={() => abrirEditar(usuario)}
                  >
                    Modificar
                  </Boton>
                  <Boton
                    variante={usuario.activo ? 'peligro' : 'secundario'}
                    tamano="sm"
                    cargando={operando === usuario.id}
                    onClick={() => cambiarAcceso(usuario)}
                  >
                    {usuario.activo ? 'Desactivar acceso' : 'Reactivar acceso'}
                  </Boton>
                </div>
              </article>
            ))}
          </div>
        )}

        <div className="border-t border-slate-100 px-5 py-3 text-xs text-slate-500">
          {filtrados.length} de {usuarios.length} usuarios · Rol asignado: {etiquetaRol(sesion?.rol)}
        </div>
      </section>

      {panel ? (
        <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/40 p-4">
          <form
            onSubmit={guardarFormulario}
            className="w-full max-w-lg space-y-4 rounded-2xl bg-white p-6 shadow-xl"
            aria-labelledby="formulario-usuario-titulo"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
                  {panel === 'crear' ? 'Nuevo acceso' : 'Seguridad de usuario'}
                </p>
                <h2 id="formulario-usuario-titulo" className="mt-1 text-lg font-bold text-slate-900">
                  {panel === 'crear' ? 'Agregar usuario' : `Modificar a ${enEdicion?.nombre_completo || 'usuario'}`}
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  {panel === 'crear'
                    ? 'El perfil quedará asociado al código de esta empresa.'
                    : 'Puedes actualizar el nombre, el rol o establecer una nueva contraseña.'}
                </p>
              </div>
              <button
                type="button"
                className="rounded-lg px-2 text-xl text-slate-400 hover:bg-slate-100"
                onClick={() => setPanel(null)}
                aria-label="Cerrar formulario"
              >
                ×
              </button>
            </div>
            <Campo etiqueta="Nombre completo" htmlFor="usuario-nombre" requerido>
              <input
                id="usuario-nombre"
                className="campo"
                value={formulario.nombre_completo}
                onChange={(evento) => setFormulario({ ...formulario, nombre_completo: evento.target.value })}
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
                onChange={(evento) => setFormulario({ ...formulario, email: evento.target.value })}
                disabled={panel !== 'crear'}
                required
              />
            </Campo>
            <Campo etiqueta="Rol" htmlFor="usuario-rol-form" requerido>
              <select
                id="usuario-rol-form"
                className="campo"
                value={formulario.rol}
                onChange={(evento) => setFormulario({ ...formulario, rol: evento.target.value })}
              >
                {ROLES_EMPRESA.map((rol) => (
                  <option key={rol.valor} value={rol.valor}>{rol.etiqueta}</option>
                ))}
              </select>
            </Campo>
            <Campo
              etiqueta={panel === 'crear' ? 'Contraseña temporal' : 'Nueva contraseña'}
              htmlFor="usuario-password"
              requerido={panel === 'crear'}
              ayuda={panel === 'crear' ? 'Mínimo 12 caracteres.' : 'Déjala vacía para conservar la contraseña actual.'}
            >
              <input
                id="usuario-password"
                type="password"
                className="campo"
                value={formulario.password}
                onChange={(evento) => setFormulario({ ...formulario, password: evento.target.value })}
                minLength={12}
                required={panel === 'crear'}
                autoComplete="new-password"
              />
            </Campo>
            <div className="flex justify-end gap-2 border-t border-slate-100 pt-4">
              <Boton type="button" variante="secundario" onClick={() => setPanel(null)}>
                Cancelar
              </Boton>
              <Boton type="submit" cargando={operando === 'formulario'}>
                Guardar cambios
              </Boton>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  )
}

function Resumen({ titulo, valor, tono = 'text-slate-900' }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{titulo}</p>
      <p className={`mt-2 text-2xl font-bold ${tono}`}>{valor}</p>
    </div>
  )
}
