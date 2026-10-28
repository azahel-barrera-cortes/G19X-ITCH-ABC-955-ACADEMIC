/**
 * Interfaz de acceso (puerta de entrada de PGAC).
 *
 * Es una pantalla NUEVA y SEPARADA del sistema de actas: no muestra la barra
 * lateral, el encabezado ni ninguna función de generación, biblioteca o
 * administración. Un visitante solo puede iniciar sesión, crear una cuenta
 * (rol capturista, asignado por el servidor) o recuperar su contraseña.
 *
 * Cuando el acceso es correcto se invoca `onAccesoExitoso` y la aplicación
 * abre el perfil del usuario con las funciones permitidas por su rol.
 */
import { useState } from 'react'
import Login from './Login.jsx'
import Registro from './Registro.jsx'
import RecuperarPassword from './RecuperarPassword.jsx'

const VISTAS = ['login', 'registro', 'recuperar']

export default function Acceso({ onAccesoExitoso }) {
  const [vista, setVista] = useState('login')

  /** Las páginas hijas piden cambios de vista; los destinos ajenos al acceso
   *  (p. ej. 'perfil' tras un login correcto) se delegan a la aplicación. */
  const cambiarVista = (destino) => {
    if (VISTAS.includes(destino)) {
      setVista(destino)
    } else if (onAccesoExitoso) {
      onAccesoExitoso(destino)
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-100">
      {/* Panel de marca: solo presentación, sin funciones del sistema. */}
      <aside className="hidden w-96 shrink-0 flex-col justify-between bg-corporativo-800 px-8 py-10 text-white lg:flex">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10 text-sm font-bold">
            PG
          </span>
          <div>
            <p className="text-sm font-semibold leading-tight">PGAC</p>
            <p className="text-[11px] leading-tight text-corporativo-200">
              Página de Gestión de Actas Corporativas
            </p>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className="text-2xl font-semibold leading-snug">
            Acceso seguro a la gestión de tus actas corporativas
          </h2>
          <p className="text-sm leading-relaxed text-corporativo-100">
            Redacción asistida por IA, validación de consistencia conforme a la
            LGSM y exportación a PDF. Las funciones disponibles dentro del
            sistema dependen del rol asignado a tu cuenta.
          </p>
          <ul className="space-y-2 text-xs text-corporativo-200">
            <li>• Capturista: crea y edita actas, genera el PDF.</li>
            <li>• Revisor: consulta biblioteca, administración y bitácora.</li>
            <li>• Abogado responsable: aprueba, valida y cambia estatus.</li>
            <li>• Administrador: gestiona usuarios y el repositorio completo.</li>
          </ul>
        </div>

        <p className="text-[11px] leading-snug text-corporativo-300">
          La IA asiste la redacción; la revisión legal final corresponde al
          abogado responsable.
        </p>
      </aside>

      {/* Panel de credenciales. */}
      <main className="flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <div className="mb-6 text-center lg:hidden">
            <span className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-corporativo-700 text-sm font-bold text-white">
              PG
            </span>
            <p className="text-sm font-semibold text-corporativo-700">PGAC</p>
            <p className="text-xs text-slate-500">Página de Gestión de Actas Corporativas</p>
          </div>

          {vista === 'login' ? <Login onCambiarVista={cambiarVista} /> : null}
          {vista === 'registro' ? <Registro onCambiarVista={cambiarVista} /> : null}
          {vista === 'recuperar' ? <RecuperarPassword onCambiarVista={cambiarVista} /> : null}

          <p className="mt-6 text-center text-[11px] leading-snug text-slate-400">
            Acceso restringido: las funciones del sistema solo se habilitan tras
            iniciar sesión y según el rol de tu cuenta.
          </p>
        </div>
      </main>
    </div>
  )
}
