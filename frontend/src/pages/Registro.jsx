import { useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { registrar, iniciarSesion, obtenerPerfil } from '../api/auth.js'
import { useAuth } from '../context/AuthContext.jsx'

const ROLES_REGISTRO = [
  { valor: 'capturista', etiqueta: 'Capturista', descripcion: 'Crea y edita actas.' },
  { valor: 'revisor', etiqueta: 'Revisor', descripcion: 'Consulta y revisa actas.' },
  { valor: 'abogado_responsable', etiqueta: 'Abogado responsable', descripcion: 'Aprueba y valida actas.' },
]

/**
 * Página de creación de cuenta (dentro de la interfaz de acceso separada).
 */
export default function Registro({ onCambiarVista = null }) {
  const { guardarSesion } = useAuth()
  const [formulario, setFormulario] = useState({
    email: '',
    nombre_completo: '',
    rol: 'capturista',
    codigo_empresa: '',
    password: '',
    confirmar: '',
  })
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [cargando, setCargando] = useState(false)

  const manejarCambio = (campo, valor) => setFormulario((previo) => ({ ...previo, [campo]: valor }))

  const manejarEnviar = async (evento) => {
    evento.preventDefault()
    setError(null)
    setAviso(null)

    if (formulario.password !== formulario.confirmar) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setCargando(true)
    try {
      const { confirmar, ...datos } = formulario
      await registrar(datos)
      // Iniciar sesión automáticamente tras el registro y abrir el perfil.
      const login = await iniciarSesion({ email: formulario.email, password: formulario.password })
      const perfil = await obtenerPerfil(login.access_token)
      guardarSesion(login.access_token, perfil)
      if (onCambiarVista) onCambiarVista('perfil')
    } catch (fallo) {
      setError(fallo.message || 'Error al registrar. El correo puede estar ya registrado.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-8 sm:px-8">
      <Tarjeta className="w-full max-w-4xl border-slate-200/80 bg-white/95 p-7 shadow-[0_20px_60px_rgba(2,63,48,0.12)] sm:p-10 lg:p-12">
        <header className="mb-8 max-w-2xl">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-corporativo-700 text-sm font-bold text-white shadow-lg shadow-corporativo-700/20">
            PG
          </div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-corporativo-500">
            Acceso autorizado
          </p>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-800">Crear cuenta</h1>
          <p className="mt-2 text-sm text-slate-500">
            Vincula tu cuenta a una empresa para comenzar a trabajar.
          </p>
        </header>

        {error && (
          <Alerta tono="error" className="mb-4">
            {error}
          </Alerta>
        )}
        {aviso && (
          <Alerta tono="exito" className="mb-4">
            {aviso}
          </Alerta>
        )}

        <form onSubmit={manejarEnviar} className="space-y-5">
          <div className="rounded-2xl border border-corporativo-100 bg-corporativo-50/60 p-5 sm:p-6">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white text-corporativo-600 shadow-sm">
                <span className="text-sm font-bold">01</span>
              </div>
              <div>
                <h2 className="text-sm font-semibold text-corporativo-800">Código de empresa</h2>
                <p className="mt-1 text-xs leading-5 text-corporativo-700">
                  Solicítalo al Administrador de tu empresa. La información empresarial se vinculará automáticamente.
                </p>
              </div>
              </div>
              <div className="w-full lg:max-w-sm">
              <Campo etiqueta="Código de empresa" htmlFor="codigo_empresa">
                <input
                  id="codigo_empresa"
                  type="text"
                  className="campo uppercase tracking-wider"
                  value={formulario.codigo_empresa}
                  onChange={(e) => manejarCambio('codigo_empresa', e.target.value.toUpperCase())}
                  placeholder="PGAC-XXXXXXXXXX"
                  maxLength={15}
                  required
                />
              </Campo>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 sm:p-6">
              <div className="mb-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-corporativo-500">02</p>
                <h2 className="mt-1 text-base font-semibold text-slate-800">Datos de la cuenta</h2>
                <p className="mt-1 text-sm text-slate-500">Define cómo identificarte dentro de PGAC.</p>
              </div>
              <div className="space-y-5">
                <Campo etiqueta="Correo electrónico" htmlFor="email">
                  <input
                    id="email"
                    type="email"
                    className="campo"
                    value={formulario.email}
                    onChange={(e) => manejarCambio('email', e.target.value)}
                    placeholder="correo@empresa.com"
                    autoComplete="email"
                    required
                  />
                </Campo>

                <Campo etiqueta="Nombre completo" htmlFor="nombre_completo">
                  <input
                    id="nombre_completo"
                    type="text"
                    className="campo"
                    value={formulario.nombre_completo}
                    onChange={(e) => manejarCambio('nombre_completo', e.target.value)}
                    placeholder="Ana María Ruiz Salazar"
                    required
                  />
                </Campo>

                <Campo etiqueta="Rol" htmlFor="rol">
                  <select
                    id="rol"
                    className="campo"
                    value={formulario.rol}
                    onChange={(e) => manejarCambio('rol', e.target.value)}
                    required
                  >
                    {ROLES_REGISTRO.map((rol) => (
                      <option key={rol.valor} value={rol.valor}>
                        {rol.etiqueta}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-slate-500">
                    {ROLES_REGISTRO.find((rol) => rol.valor === formulario.rol)?.descripcion}
                  </p>
                </Campo>
              </div>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
              <div className="mb-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-corporativo-500">03</p>
                <h2 className="mt-1 text-base font-semibold text-slate-800">Seguridad de acceso</h2>
                <p className="mt-1 text-sm text-slate-500">Usa una contraseña de al menos 6 caracteres.</p>
              </div>
              <div className="space-y-5">
                <Campo etiqueta="Contraseña" htmlFor="password">
                  <input
                    id="password"
                    type="password"
                    className="campo"
                    value={formulario.password}
                    onChange={(e) => manejarCambio('password', e.target.value)}
                    placeholder="Mínimo 6 caracteres"
                    autoComplete="new-password"
                    minLength={6}
                    required
                  />
                </Campo>

                <Campo etiqueta="Confirmar contraseña" htmlFor="confirmar">
                  <input
                    id="confirmar"
                    type="password"
                    className="campo"
                    value={formulario.confirmar}
                    onChange={(e) => manejarCambio('confirmar', e.target.value)}
                    placeholder="Repite tu contraseña"
                    autoComplete="new-password"
                    required
                  />
                </Campo>
              </div>
            </section>
          </div>

          <div className="flex flex-col-reverse items-stretch gap-4 pt-2 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={() => onCambiarVista && onCambiarVista('login')}
              className="text-left text-sm font-medium text-corporativo-600 transition hover:text-corporativo-700 hover:underline"
            >
              ← Volver al inicio de sesión
            </button>
            <Boton type="submit" variante="primario" tamano="lg" cargando={cargando} className="sm:min-w-36">
              Registrarme
            </Boton>
          </div>
        </form>
      </Tarjeta>
    </div>
  )
}
