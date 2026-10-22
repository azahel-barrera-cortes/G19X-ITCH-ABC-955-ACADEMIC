import { useCallback, useEffect, useState } from 'react'
import Boton from '../components/ui/Boton.jsx'
import Campo from '../components/ui/Campo.jsx'
import Alerta from '../components/ui/Alerta.jsx'
import Tarjeta from '../components/ui/Tarjeta.jsx'
import { TIPOS_SOCIEDAD } from '../constants/catalogos.js'

const CLAVE_LOCALSTORAGE = 'pgac_info_empresa'

const INFO_VACIA = {
  nombre_sociedad: '',
  rfc_sociedad: '',
  tipo_sociedad: '',
  logo_empresa: '',
  firma_electronica: false,
  usar_info_empresa: false,
}

export default function InformacionEmpresa({ infoGuardada = null, onGuardar = null, onUsarInfo = null }) {
  const [info, setInfo] = useState(INFO_VACIA)
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    const almacenada = infoGuardada ?? cargarDesdeLocalStorage()
    if (almacenada) setInfo(almacenada)
  }, [infoGuardada])

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
    setInfo((previo) => ({ ...previo, [campo]: valor }))
  }, [])

  const toggleFirmaElectronica = useCallback(() => {
    setInfo((previo) => ({ ...previo, firma_electronica: !previo.firma_electronica }))
  }, [])

  const toggleUsarInfo = useCallback(() => {
    setInfo((previo) => ({ ...previo, usar_info_empresa: !previo.usar_info_empresa }))
  }, [])

  const manejarLogo = useCallback((evento) => {
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
  }, [])

  const eliminarLogo = useCallback(() => {
    setInfo((previo) => ({ ...previo, logo_empresa: '' }))
    setAviso('Logo eliminado.')
  }, [])

  const handleGuardar = async () => {
    setCargando(true)
    setError(null)
    try {
      guardarEnLocalStorage(info)
      setAviso('Información de la sociedad guardada correctamente.')
      if (onGuardar) onGuardar(info)
    } catch (fallo) {
      setError('No se pudo guardar la información de la sociedad.')
    } finally {
      setCargando(false)
    }
  }

  const tipoSeleccionado = TIPOS_SOCIEDAD.find((t) => t.valor === info.tipo_sociedad)

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-lg font-semibold text-corporativo-700">Información de la empresa o sociedad</h1>
        <p className="text-sm text-slate-500">
          Captura aquí los datos de la sociedad que comparece en las actas. Esta información
          se usará para completar el encabezado y, si lo deseas, la IA podrá incorporarla
          al redactar las cláusulas.
        </p>
      </header>

      {error && <Alerta tono="error" titulo="Error" mensaje={error} />}
      {aviso && <Alerta tono="exito" mensaje={aviso} />}

      <Tarjeta>
        <div className="space-y-5">
          <fieldset className="rounded-xl border border-slate-200 p-4">
            <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Datos de la sociedad
            </legend>
            <div className="grid gap-4 md:grid-cols-2">
              <Campo etiqueta="Razón social / Nombre de la sociedad" requerido ayuda="Nombre legal con el que se constituye y aparece en los estatutos." htmlFor="nombre_sociedad">
                <input
                  id="nombre_sociedad"
                  className="campo"
                  value={info.nombre_sociedad}
                  onChange={(e) => actualizarCampo('nombre_sociedad', e.target.value)}
                  placeholder="Comercializadora del Norte, S.A. de C.V."
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
                />
              </Campo>

              <Campo etiqueta="Tipo de sociedad" requerido ayuda="Determina qué actas corporativas pueden generarse estrictamente." htmlFor="tipo_sociedad">
                <select
                  id="tipo_sociedad"
                  className="campo"
                  value={info.tipo_sociedad}
                  onChange={(e) => actualizarCampo('tipo_sociedad', e.target.value)}
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
                />
                {info.logo_empresa && (
                  <div className="mt-2 flex items-center gap-3">
                    <img src={info.logo_empresa} alt="Logo" className="h-10 w-auto rounded border border-slate-200" />
                    <Boton variante="secundario" tamano="sm" onClick={eliminarLogo}>Eliminar logo</Boton>
                  </div>
                )}
              </Campo>
            </div>
          </fieldset>

          <fieldset className="rounded-xl border border-slate-200 p-4">
            <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Firma electrónica (opcional)
            </legend>
            <div className="flex items-center gap-3">
              <input
                id="firma_electronica"
                type="checkbox"
                checked={info.firma_electronica}
                onChange={toggleFirmaElectronica}
                className="campo"
              />
              <label htmlFor="firma_electronica" className="text-sm font-medium">
                Generar acta ya firmada (firma electrónica)
              </label>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Si se activa, el PDF del acta se generará con indicación de firma electrónica.
              Esta función es opcional y puede habilitarse o deshabilitarse por acta.
            </p>
          </fieldset>

          <fieldset className="rounded-xl border border-slate-200 bg-corporativo-50 p-4">
            <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-corporativo-600">
              Usar en la generación de actas
            </legend>
            <div className="flex items-center gap-3">
              <input
                id="usar_info_empresa"
                type="checkbox"
                checked={info.usar_info_empresa}
                onChange={toggleUsarInfo}
                className="campo"
              />
              <label htmlFor="usar_info_empresa" className="text-sm font-medium text-corporativo-700">
                ¿Usar esta información al generar el acta?
              </label>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              Si se activa, la sociedad, el tipo de sociedad, el logo y la firma electrónica
              se incluirán automáticamente en cada acta que generes. La IA podrá usar estos
              datos para redactar las cláusulas y el encabezado del PDF.
            </p>
          </fieldset>
        </div>
      </Tarjeta>

      <div className="flex justify-end">
        <Boton variante="primero" onClick={handleGuardar} cargando={cargando}>
          Guardar información de la sociedad
        </Boton>
      </div>
    </div>
  )
}