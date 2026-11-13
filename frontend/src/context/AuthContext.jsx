/**
 * Contexto de autenticación: usuario actual, token y helpers de sesión.
 *
 * Persiste el JWT en localStorage y expone login, logout, register,
 * changePassword y resetPassword.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { obtenerPerfil, registrarCierreSesion } from '../api/auth.js'

const CLAVE_TOKEN = 'pgac_token'
const CLAVE_USUARIO = 'pgac_usuario'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(() => {
    try {
      const guardado = localStorage.getItem(CLAVE_USUARIO)
      return guardado ? JSON.parse(guardado) : null
    } catch {
      return null
    }
  })
  const [token, setToken] = useState(() => localStorage.getItem(CLAVE_TOKEN))

  const cargando = false

  // Detecta si un administrador desactivó una sesión que ya estaba abierta.
  useEffect(() => {
    if (!token) return undefined
    let montado = true

    const comprobarEstado = async () => {
      try {
        const perfil = await obtenerPerfil(token)
        if (!montado) return
        setUsuario(perfil)
        localStorage.setItem(CLAVE_USUARIO, JSON.stringify(perfil))
      } catch (fallo) {
        if (montado && fallo.message?.toLowerCase().includes('inactivo')) {
          setUsuario((previo) => (previo ? { ...previo, activo: false } : previo))
        }
      }
    }

    comprobarEstado()
    const intervalo = window.setInterval(comprobarEstado, 15000)
    return () => {
      montado = false
      window.clearInterval(intervalo)
    }
  }, [token])

  /** Guarda token y usuario en localStorage y en el estado. */
  const guardarSesion = useCallback((tokenJwt, datosUsuario) => {
    localStorage.setItem(CLAVE_TOKEN, tokenJwt)
    localStorage.setItem(CLAVE_USUARIO, JSON.stringify(datosUsuario))
    setToken(tokenJwt)
    setUsuario(datosUsuario)
  }, [])

  /** Registra y cierra la sesión, sin bloquear la salida si el backend no responde. */
  const cerrarSesion = useCallback(async (registrarEnServidor = true) => {
    const tokenActual = localStorage.getItem(CLAVE_TOKEN)
    try {
      if (registrarEnServidor && tokenActual) await registrarCierreSesion(tokenActual)
    } catch (fallo) {
      console.error('No se pudo registrar el cierre de sesión:', fallo)
    } finally {
      localStorage.removeItem(CLAVE_TOKEN)
      localStorage.removeItem(CLAVE_USUARIO)
      setToken(null)
      setUsuario(null)
    }
  }, [])

  /** Actualiza el usuario local (tras editar perfil). */
  const actualizarUsuario = useCallback((datos) => {
    setUsuario((previo) => {
      const nuevo = { ...previo, ...datos }
      localStorage.setItem(CLAVE_USUARIO, JSON.stringify(nuevo))
      return nuevo
    })
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      token,
      autenticado: Boolean(token),
      cargando,
      guardarSesion,
      cerrarSesion,
      actualizarUsuario,
    }),
    [usuario, token, cargando, guardarSesion, cerrarSesion, actualizarUsuario],
  )

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}
