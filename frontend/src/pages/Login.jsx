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
    <div className="flex min-h-full items-center justify-center bg-slate-50 py-12 px-4">
      <Tarjeta className="w-full max-w-md">
        <header className="mb-6 text-center">
          <h1 className="text-xl font-semibold text-corporativo-700">Iniciar sesión</h1>
          <p className="text-sm text-slate-500">Accede a tu cuenta de PGAC</p>
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

          <div className="flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={() => onCambiarVista && onCambiarVista('recuperar')}
              className="text-corporativo-600 hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </button>
            <Boton type="submit" variante="primario" cargando={cargando}>
              Entrar
            </Boton>
          </div>
        </form>

        <p className="mt-4 text-center text-xs text-slate-500">
          ¿No tienes cuenta?{' '}
          <button
            type="button"
            onClick={() => onCambiarVista && onCambiarVista('registro')}
            className="text-corporativo-600 hover:underline"
          >
            Regístrate
          </button>
        </p>
      </Tarjeta>
    </div>
  )
}
