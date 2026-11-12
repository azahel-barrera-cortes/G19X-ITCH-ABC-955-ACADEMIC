import { useCallback, useEffect, useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import { TIPOS_SOCIEDAD } from '../constants/catalogos.js'
import { actualizarInfoEmpresa, obtenerInfoEmpresa } from '../api/auth.js'
import { useAuth } from '../context/AuthContext.jsx'

const CLAVE_LOCALSTORAGE = 'pgac_info_empresa'

const INFO_VACIA = {
  nombre_sociedad: '',
  rfc_sociedad: '',
  tipo_sociedad: '',
  logo_empresa: '',
  firma_electronica: false,
  usar_info_empresa: false,
}

export default function InformacionEmpresa({
  infoGuardada = null,
  onGuardar = null,
  onUsarInfo = null,
  puedeEditar = false,
}) {
  const { token } = useAuth()
  const [info, setInfo] = useState(INFO_VACIA)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [cargando, setCargando] = useState(false)
  const [actualizandoUso, setActualizandoUso] = useState(false)

  useEffect(() => {
    if (!token) return undefined
    let montado = true
    setError(null)
    obtenerInfoEmpresa(token)
      .then((datos) => {
        if (!montado) return
        const completa = { ...INFO_VACIA, ...datos }
        setInfo(completa)
        if (onGuardar) onGuardar(completa)
      })
      .catch((fallo) => {
        if (!montado) return
        const endpointNoDisponible =
          fallo.message === 'Not Found' || fallo.message.includes('404')
        if (endpointNoDisponible) {
          const almacenada = infoGuardada ?? cargarDesdeLocalStorage()
          if (almacenada) {
            const completa = { ...INFO_VACIA, ...almacenada }
            setInfo(completa)
            if (onGuardar) onGuardar(completa)
          }
          return
        }
        setError(fallo.message || 'No se pudo cargar la información empresarial.')
      })
    return () => {
      montado = false
    }
  }, [token, infoGuardada])

  const cargarDesdeLocalStorage = () => {
    try {
      const raw = localStorage.getItem(CLAVE_LOCALSTORAGE)
      return raw ? JSON.parse(raw) : null
    } catch {
      return null
    }
  }

  const guardarEnLocalStorage = (datos) => {
    try {
      localStorage.setItem(CLAVE_LOCALSTORAGE, JSON.stringify(datos))
    } catch {
      /* silent */
    }
  }

  const actualizarCampo = useCallback((campo, valor) => {
    if (!puedeEditar) return
    setInfo((previo) => ({ ...previo, [campo]: valor }))
  }, [puedeEditar])

  const toggleUsarInfo = useCallback(async () => {
    if (!puedeEditar || actualizandoUso) return
    const siguiente = !info.usar_info_empresa
    if (!String(info.nombre_sociedad || '').trim() || !String(info.tipo_sociedad || '').trim()) {
      setError('Completa la razón social y el tipo de sociedad antes de activar esta opción.')
      return
    }
    setActualizandoUso(true)
    setError(null)
    try {
      const actualizada = await actualizarInfoEmpresa(token, {
        ...info,
        usar_info_empresa: siguiente,
      })
      const completa = { ...INFO_VACIA, ...actualizada }
      setInfo(completa)
      guardarEnLocalStorage(completa)
      if (onGuardar) onGuardar(completa)
      setAviso(siguiente
        ? 'La información de la empresa se usará automáticamente en las actas.'
        : 'La información de la empresa ya no se usará automáticamente en las actas.')
    } catch (fallo) {
      setError(fallo.message || 'No se pudo actualizar el uso de la información empresarial.')
    } finally {
      setActualizandoUso(false)
    }
  }, [actualizandoUso, info, onGuardar, puedeEditar, token])

  const manejarLogo = useCallback((evento) => {
    if (!puedeEditar) return
    const archivo = evento.target.files?.[0]
    if (!archivo) return
    if (!archivo.type.startsWith('image/')) {
      setError('Selecciona un archivo de imagen válido (PNG, JPG, SVG, WebP).')
      return
    }
    const lector = new FileReader()
    lector.onload = () => {
      setInfo((previo) => ({ ...previo, logo_empresa: lector.result }))
      setAviso('Logo cargado. Se mostrará en el encabezado del acta.')
    }
    lector.readAsDataURL(archivo)
  }, [puedeEditar])

  const eliminarLogo = useCallback(() => {
    if (!puedeEditar) return
    setInfo((previo) => ({ ...previo, logo_empresa: '' }))
    setAviso('Logo eliminado.')
  }, [puedeEditar])

  const handleGuardar = async () => {
    if (!puedeEditar) {
      setError('Solo el Administrador puede modificar la información de la empresa o sociedad.')
      return
    }
    if (!String(info.nombre_sociedad || '').trim() || !String(info.tipo_sociedad || '').trim()) {
      setError('Completa la razón social y el tipo de sociedad antes de guardar.')
      return
    }
    setCargando(true)
    setError(null)
    try {
      const actualizada = await actualizarInfoEmpresa(token, info)
      guardarEnLocalStorage(actualizada)
      setInfo({ ...INFO_VACIA, ...actualizada })
      setAviso('Información de la sociedad guardada correctamente.')
      if (onGuardar) onGuardar(actualizada)
    } catch (fallo) {
      if (fallo.message === 'Not Found' || fallo.message.includes('404')) {
        setError('El backend en ejecución no tiene habilitado el guardado empresarial. Reinicia el servidor backend.')
      } else {
        setError(fallo.message || 'No se pudo guardar la información de la sociedad.')
      }
    } finally {
      setCargando(false)
    }
  }

  const tipoSeleccionado = TIPOS_SOCIEDAD.find((t) => t.valor === info.tipo_sociedad)

  if (!puedeEditar) {
    const hayInformacionEmpresarial = Boolean(
      info.nombre_sociedad ||
      info.rfc_sociedad ||
      info.tipo_sociedad ||
      info.logo_empresa,
    )

    return (
      <div className="space-y-5">
        <header className="rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-tarjeta">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-corporativo-50 text-corporativo-600">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 21h18M5 21V5.8a1 1 0 0 1 .7-.95l6-2a1 1 0 0 1 .6 0l6 2a1 1 0 0 1 .7.95V21M8 8h1m-1 4h1m6-4h1m-1 4h1M9 21v-4h6v4" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-semibold leading-6 text-slate-800">Información de la empresa o sociedad</h1>
              <p className="mt-1 text-sm leading-5 text-slate-500">
                Consulta la información empresarial configurada por el Administrador.
              </p>
            </div>
          </div>
        </header>

        {error && <Alerta tono="error" titulo="Error">{error}</Alerta>}
        {aviso && <Alerta tono="exito">{aviso}</Alerta>}
        {!hayInformacionEmpresarial && (
          <Alerta tono="info" titulo="Información empresarial">
            No especificada. El Administrador aún no ha guardado los datos de la sociedad.
          </Alerta>
        )}

        <Tarjeta className="space-y-5 p-5">
          <section className="rounded-xl border border-slate-200 bg-slate-50/40 p-5">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Datos de la sociedad
            </h2>
            <dl className="mt-5 space-y-4">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Razón social / Nombre de la sociedad
                </dt>
                <dd className="mt-1 text-sm font-medium text-slate-800">
                  {info.nombre_sociedad || 'No especificada'}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Tipo de sociedad
                </dt>
                <dd className="mt-1 text-sm font-medium text-slate-800">
                  {tipoSeleccionado?.etiqueta || 'No especificado'}
                </dd>
              </div>
            </dl>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Logo de la empresa
            </h2>
            <div className="mt-4 flex min-h-24 items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4">
              {info.logo_empresa ? (
                <img
                  src={info.logo_empresa}
                  alt="Logo de la empresa"
                  className="max-h-20 w-auto rounded object-contain"
                />
              ) : (
                <p className="text-sm text-slate-500">No hay un logo registrado.</p>
              )}
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
                Firma electrónica
              </h2>
              <p className={`mt-3 text-sm font-semibold ${
                info.firma_electronica ? 'text-emerald-700' : 'text-slate-500'
              }`}>
                {info.firma_electronica ? 'Activa' : 'Inactiva'}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Estado configurado por el Administrador.
              </p>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-corporativo-600">
                Uso en la generación de actas
              </h2>
              <p className={`mt-3 text-sm font-semibold ${
                info.usar_info_empresa ? 'text-emerald-700' : 'text-slate-500'
              }`}>
                {info.usar_info_empresa ? 'Activo' : 'Inactivo'}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Estado configurado por el Administrador.
              </p>
            </div>
          </section>
        </Tarjeta>
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <header className="rounded-2xl border border-slate-200 bg-white px-5 py-5 shadow-tarjeta">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-corporativo-50 text-corporativo-600">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 21h18M5 21V5.8a1 1 0 0 1 .7-.95l6-2a1 1 0 0 1 .6 0l6 2a1 1 0 0 1 .7.95V21M8 8h1m-1 4h1m6-4h1m-1 4h1M9 21v-4h6v4" />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-semibold leading-6 text-slate-800">Información de la empresa o sociedad</h1>
            <p className="mt-1 text-sm leading-5 text-slate-500">
          Captura aquí los datos de la sociedad que comparece en las actas. Esta información
          se usará para completar el encabezado y, si lo deseas, la IA podrá incorporarla
          al redactar las cláusulas.
            </p>
          </div>
        </div>
      </header>

      {error && <Alerta tono="error" titulo="Error">{error}</Alerta>}
      {aviso && <Alerta tono="exito">{aviso}</Alerta>}
      {(!info.nombre_sociedad || !info.tipo_sociedad) && (
        <Alerta tono="info" titulo="Completa los datos de la sociedad">
          Captura la razón social y el tipo de sociedad para compartir esta información
          con los usuarios vinculados mediante tu código de empresa.
        </Alerta>
      )}

      <Tarjeta className="space-y-5 p-5">
        <fieldset className="rounded-xl border border-slate-200 bg-slate-50/40 p-5">
          <legend className="px-2 text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Datos de la sociedad
          </legend>
          <div className="space-y-5">
            <Campo etiqueta="Razón social / Nombre de la sociedad" requerido ayuda="Nombre legal con el que se constituye y aparece en los estatutos." htmlFor="nombre_sociedad">
                <input
                  id="nombre_sociedad"
                  className="campo"
                  value={info.nombre_sociedad}
                  onChange={(e) => actualizarCampo('nombre_sociedad', e.target.value)}
                  placeholder="Comercializadora del Norte, S.A. de C.V."
                  required
                  disabled={!puedeEditar}
                />
            </Campo>

            <Campo etiqueta="R.F.C." ayuda="Clave del Registro Federal de Contribuyentes (opcional)." htmlFor="rfc_sociedad">
                <input
                  id="rfc_sociedad"
                  className="campo uppercase"
                  maxLength={13}
                  value={info.rfc_sociedad}
                  onChange={(e) => actualizarCampo('rfc_sociedad', e.target.value.toUpperCase())}
                  placeholder="CDN950101ABC"
                  disabled={!puedeEditar}
                />
            </Campo>

            <Campo etiqueta="Tipo de sociedad" requerido ayuda="Determina qué actas corporativas pueden generarse estrictamente." htmlFor="tipo_sociedad">
                <select
                  id="tipo_sociedad"
                  className="campo"
                  value={info.tipo_sociedad}
                  onChange={(e) => actualizarCampo('tipo_sociedad', e.target.value)}
                  required
                  disabled={!puedeEditar}
                >
                  <option value="">Selecciona un tipo de sociedad</option>
                  {TIPOS_SOCIEDAD.map((tipo) => (
                    <option key={tipo.valor} value={tipo.valor}>
                      {tipo.etiqueta}
                    </option>
                  ))}
                </select>
                {tipoSeleccionado && (
                  <p className="mt-1 text-xs text-slate-500">{tipoSeleccionado.etiqueta}</p>
                )}
            </Campo>

            <Campo etiqueta="Logo de la empresa" ayuda="Imagen que se mostrará en el encabezado del acta (PNG, JPG, SVG, WebP)." htmlFor="logo_empresa">
                <input
                  id="logo_empresa"
                  type="file"
                  accept="image/*"
                  className="campo"
                  onChange={manejarLogo}
                  disabled={!puedeEditar}
                />
                {info.logo_empresa && (
                  <div className="mt-2 flex items-center gap-3">
                    <img src={info.logo_empresa} alt="Logo" className="h-10 w-auto rounded border border-slate-200" />
                    {puedeEditar && (
                      <Boton variante="secundario" tamano="sm" onClick={eliminarLogo}>Eliminar logo</Boton>
                    )}
                  </div>
                )}
            </Campo>
          </div>
        </fieldset>

        <fieldset className={`rounded-xl border p-5 transition-colors ${
          info.usar_info_empresa
            ? 'border-corporativo-300 bg-corporativo-50'
            : 'border-slate-200 bg-white'
        }`}>
          <div className="flex items-start gap-4">
            <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
              info.usar_info_empresa ? 'bg-white text-corporativo-600' : 'bg-slate-100 text-slate-600'
            }`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-5 w-5" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 12.5 12 4l9 8.5M5.5 10.5V20h13v-9.5M9 20v-5h6v5" />
              </svg>
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-corporativo-700">Usar en la generación de actas</h3>
                  <p className="mt-1 text-xs font-medium text-corporativo-600">Configuración automática</p>
                </div>
                <Boton
                  variante={info.usar_info_empresa ? 'secundario' : 'primario'}
                  tamano="sm"
                  onClick={toggleUsarInfo}
                  cargando={actualizandoUso}
                  disabled={!puedeEditar || actualizandoUso}
                >
                  {info.usar_info_empresa ? 'Desactivar' : 'Activar'}
                </Boton>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-600">
                La sociedad, el tipo y el logo se incluirán automáticamente en cada acta
                cuando esta opción esté activa. El cambio se guarda inmediatamente.
              </p>
            </div>
          </div>
        </fieldset>
      </Tarjeta>

      {puedeEditar ? (
        <div className="flex justify-end px-1">
          <Boton variante="primero" onClick={handleGuardar} cargando={cargando}>
            Guardar información de la sociedad
          </Boton>
        </div>
      ) : (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-5 text-amber-800">
          Solo el Administrador puede editar o guardar la información de la empresa o sociedad.
        </div>
      )}
    </div>
  )
}