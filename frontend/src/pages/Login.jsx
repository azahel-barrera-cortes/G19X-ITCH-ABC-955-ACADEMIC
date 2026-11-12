import { useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { iniciarSesion, obtenerPerfil } from '../api/auth.js'
import { useAuth } from '../context/AuthContext.jsx'

/** Página de inicio de sesión (dentro de la interfaz de acceso separada). */
export default function Login({ onCambiarVista = null }) {
  const { guardarSesion } = useAuth()
  const [formulario, setFormulario] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)

  const manejarCambio = (campo, valor) => setFormulario((previo) => ({ ...previo, [campo]: valor }))

  const manejarEnviar = async (evento) => {
    evento.preventDefault()
    setError(null)
    setCargando(true)
    try {
      const respuesta = await iniciarSesion(formulario)
      // El token no trae los datos del usuario: se consulta el perfil completo
      // (nombre, rol) para que la sesión y la compuerta por rol funcionen.
      const perfil = await obtenerPerfil(respuesta.access_token)
      guardarSesion(respuesta.access_token, perfil)
      // Acceso correcto: se abre el perfil con las funciones del rol.
      if (onCambiarVista) onCambiarVista('perfil')
    } catch (fallo) {
      setError(fallo.message || 'Error al iniciar sesión. Verifica tus credenciales.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center px-4 py-8 sm:px-8">
      <Tarjeta className="w-full max-w-lg border-slate-200/80 bg-white/95 p-7 shadow-[0_20px_60px_rgba(2,63,48,0.12)] sm:p-10">
        <header className="mb-8">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-corporativo-700 text-sm font-bold text-white shadow-lg shadow-corporativo-700/20">
            PG
          </div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-corporativo-500">
            Acceso al sistema
          </p>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-800">Iniciar sesión</h1>
          <p className="mt-2 text-sm text-slate-500">Accede a tu cuenta de PGAC para continuar.</p>
        </header>

        {error && (
          <Alerta tono="error" className="mb-4">
            {error}
          </Alerta>
        )}

        <form onSubmit={manejarEnviar} className="space-y-4">
          <Campo etiqueta="Correo electrónico" htmlFor="email">
            <input
              id="email"
              type="email"
              className="campo"
              value={formulario.email}
              onChange={(e) => manejarCambio('email', e.target.value)}
              placeholder="admin@empresa.com"
              autoComplete="email"
              required
            />
          </Campo>

          <Campo etiqueta="Contraseña" htmlFor="password">
            <input
              id="password"
              type="password"
              className="campo"
              value={formulario.password}
              onChange={(e) => manejarCambio('password', e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </Campo>

          <div className="flex flex-col-reverse items-stretch gap-4 pt-2 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={() => onCambiarVista && onCambiarVista('recuperar')}
              className="text-left text-sm font-medium text-corporativo-600 transition hover:text-corporativo-700 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
            <Boton type="submit" variante="primario" tamano="lg" cargando={cargando} className="sm:min-w-28">
              Entrar
            </Boton>
          </div>
        </form>

        <p className="mt-8 border-t border-slate-100 pt-6 text-center text-sm text-slate-500">
          ¿No tienes cuenta?{' '}
          <button
            type="button"
            onClick={() => onCambiarVista && onCambiarVista('registro')}
            className="font-semibold text-corporativo-600 transition hover:text-corporativo-700 hover:underline"
          >
            Regístrate
          </button>
        </p>
      </Tarjeta>
    </div>
  )
}
