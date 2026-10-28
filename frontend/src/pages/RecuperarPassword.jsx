import { useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import { solicitarResetPassword, confirmarResetPassword } from '../api/auth.js'

/** Página para recuperar contraseña (paso 1: enviar correo). */
export default function RecuperarPassword({ onCambiarVista = null }) {
  const [etapa, setEtapa] = useState('enviar') // enviar | confirmar
  const [formulario, setFormulario] = useState({ email: '', token: '', nuevo_password: '', confirmar: '' })
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [cargando, setCargando] = useState(false)

  const manejarCambio = (campo, valor) => setFormulario((previo) => ({ ...previo, [campo]: valor }))

  const manejarEnviar = async (evento) => {
    evento.preventDefault()
    setError(null)
    setAviso(null)
    setCargando(true)
    try {
      const respuesta = await solicitarResetPassword(formulario.email)
      // Mientras no haya servicio de correo, el backend (en modo DEBUG) puede
      // devolver el token en `detalle` para probar el flujo completo.
      setAviso(
        respuesta.detalle
          ? `${respuesta.mensaje} ${respuesta.detalle}`
          : respuesta.mensaje || 'Si el correo está registrado, se generó un token de recuperación.',
      )
      setEtapa('confirmar')
    } catch (fallo) {
      setError(fallo.message || 'No se pudo enviar el token de recuperación.')
    } finally {
      setCargando(false)
    }
  }

  const manejarConfirmar = async (evento) => {
    evento.preventDefault()
    setError(null)

    if (formulario.nuevo_password !== formulario.confirmar) {
      setError('Las contraseñas no coinciden.')
      return
    }

    setCargando(true)
    try {
      await confirmarResetPassword({
        token: formulario.token,
        nuevo_password: formulario.nuevo_password,
      })
      setAviso('Contraseña actualizada. Ya puedes iniciar sesión.')
      setEtapa('enviar')
      if (onCambiarVista) onCambiarVista('login')
    } catch (fallo) {
      setError(fallo.message || 'El token no es válido o ha expirado.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-slate-50 py-12 px-4">
      <Tarjeta className="w-full max-w-md">
        <header className="mb-6 text-center">
          <h1 className="text-xl font-semibold text-corporativo-700">Recuperar contraseña</h1>
          <p className="text-sm text-slate-500">Genera un token para cambiar tu contraseña</p>
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

        {etapa === 'enviar' ? (
          <form onSubmit={manejarEnviar} className="space-y-4">
            <Campo etiqueta="Correo electrónico" htmlFor="email">
              <input
                id="email"
                type="email"
                className="campo"
                value={formulario.email}
                onChange={(e) => manejarCambio('email', e.target.value)}
                placeholder="tu-correo@empresa.com"
                required
              />
            </Campo>
            <div className="flex justify-between text-sm">
              <button
                type="button"
                onClick={() => onCambiarVista && onCambiarVista('login')}
                className="text-corporativo-600 hover:underline"
              >
                ← Volver al inicio de sesión
              </button>
              <Boton type="submit" variante="primario" cargando={cargando}>
                Enviar token
              </Boton>
            </div>
          </form>
        ) : (
          <form onSubmit={manejarConfirmar} className="space-y-4">
            <Campo etiqueta="Token de recuperación" htmlFor="token" ayuda="Código que recibiste por correo.">
              <input
                id="token"
                type="text"
                className="campo"
                value={formulario.token}
                onChange={(e) => manejarCambio('token', e.target.value)}
                placeholder="Token de 32 caracteres"
                required
              />
            </Campo>

            <Campo etiqueta="Nueva contraseña" htmlFor="nuevo_password">
              <input
                id="nuevo_password"
                type="password"
                className="campo"
                value={formulario.nuevo_password}
                onChange={(e) => manejarCambio('nuevo_password', e.target.value)}
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
                placeholder="Repite la nueva contraseña"
                autoComplete="new-password"
                required
              />
            </Campo>

            <div className="flex justify-between text-sm">
              <button
                type="button"
                onClick={() => setEtapa('enviar')}
                className="text-corporativo-600 hover:underline"
              >
                ← Enviar otro token
              </button>
              <Boton type="submit" variante="primario" cargando={cargando}>
                Cambiar contraseña
              </Boton>
            </div>
          </form>
        )}
      </Tarjeta>
    </div>
  )
}
