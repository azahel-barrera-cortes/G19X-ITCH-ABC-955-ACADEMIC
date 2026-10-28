import { useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { registrar, iniciarSesion, obtenerPerfil } from '../api/auth.js'
import { useAuth } from '../context/AuthContext.jsx'

/**
 * Página de creación de cuenta (dentro de la interfaz de acceso separada).
 *
 * El servidor decide el rol: el autoregistro público siempre crea la cuenta
 * como **capturista** (mínimo privilegio); solo un Administrador autenticado
 * puede asignar roles superiores desde la API.
 */
export default function Registro({ onCambiarVista = null }) {
  const { guardarSesion } = useAuth()
  const [formulario, setFormulario] = useState({
    email: '',
    nombre_completo: '',
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
      await registrar({ ...datos, rol: 'capturista' })
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
    <div className="flex min-h-full items-center justify-center bg-slate-50 py-12 px-4">
      <Tarjeta className="w-full max-w-md">
        <header className="mb-6 text-center">
          <h1 className="text-xl font-semibold text-corporativo-700">Crear cuenta</h1>
          <p className="text-sm text-slate-500">Regístrate en PGAC</p>
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

        <form onSubmit={manejarEnviar} className="space-y-4">
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

          <Alerta tono="info">
            Tu cuenta se creará con el rol <strong>Capturista</strong> (crear y
            editar actas). Un Administrador puede asignarte un rol superior
            (revisor, abogado responsable) cuando lo necesites.
          </Alerta>

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

          <div className="flex items-center justify-between text-sm">
            <button
              type="button"
              onClick={() => onCambiarVista && onCambiarVista('login')}
              className="text-corporativo-600 hover:underline"
            >
              ← Volver al inicio de sesión
            </button>
            <Boton type="submit" variante="primario" cargando={cargando}>
              Registrarme
            </Boton>
          </div>
        </form>
      </Tarjeta>
    </div>
  )
}
