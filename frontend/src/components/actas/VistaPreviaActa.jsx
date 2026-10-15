import Etiqueta from '../ui/Etiqueta.jsx'
import { fechaCorta, horaCorta, moneda, numero, porcentaje } from '../../utils/formato.js'
import { TIPOS_ASAMBLEA } from '../../constants/catalogos.js'

/**
 * Vista previa en pantalla del acta.
 *
 * Refleja el mismo contenido que maquetará ReportLab en el PDF: datos generales,
 * asistentes, orden del día, cláusulas redactadas y hoja de firmas. Permite
 * revisar el documento antes de descargarlo.
 */
export default function VistaPreviaActa({ estado, calculos, borrador = null, className = '' }) {
  const acuerdos = borrador?.acuerdos?.length ? borrador.acuerdos : estado.acuerdos
  const tipoEtiqueta =
    TIPOS_ASAMBLEA.find((tipo) => tipo.valor === estado.tipo_asamblea)?.etiqueta || estado.tipo_asamblea

  return (
    <article
      className={`rounded-xl border border-slate-300 bg-white p-6 font-serif text-[13px] leading-relaxed text-slate-800 shadow-inner ${className}`}
    >
      <header className="border-b border-slate-300 pb-3 text-center">
        <h3 className="text-base font-bold uppercase tracking-wide text-corporativo-700">
          ACTA DE {String(tipoEtiqueta).toUpperCase()}
        </h3>
        <p className="mt-1 text-[12px] text-slate-500">
          {estado.sociedad || 'Sociedad no indicada'}
          {estado.rfc_sociedad ? ` · R.F.C. ${estado.rfc_sociedad}` : ''}
        </p>
        <p className="text-[12px] text-slate-500">
          Celebrada el {fechaCorta(estado.fecha)} a las {horaCorta(estado.hora)} en{' '}
          {estado.lugar || '—'}
        </p>
        {borrador?.folio ? (
          <p className="mt-1">
            <Etiqueta tono="info">Folio propuesto: {borrador.folio}</Etiqueta>
          </p>
        ) : null}
      </header>

      <section className="mt-4">
        <h4 className="text-[12px] font-bold uppercase text-corporativo-600">I. Datos generales</h4>
        <div className="mt-2 grid gap-x-6 gap-y-1 sm:grid-cols-2">
          <p>
            <strong>Capital social:</strong> {moneda(estado.capital_social)}
          </p>
          <p>
            <strong>Capital representado:</strong>{' '}
            {moneda(estado.capital_presente || calculos.accionesPresentes)}
          </p>
          <p>
            <strong>Acciones en circulación:</strong> {numero(estado.acciones_totales)}
          </p>
          <p>
            <strong>Quórum:</strong> {porcentaje(calculos.quorum, 2)}
          </p>
          <p>
            <strong>Presidente:</strong> {estado.presidente || '—'}
          </p>
          <p>
            <strong>Secretario:</strong> {estado.secretario || '—'}
          </p>
          <p className="sm:col-span-2">
            <strong>Convocatoria:</strong>{' '}
            {estado.convocatoria_fecha
              ? `${fechaCorta(estado.convocatoria_fecha)} · ${
                  estado.convocatoria_medio || 'medio no indicado'
                } · ${estado.convocatoria_quien || 'quien convoca no indicado'}`
              : 'Sin convocatoria registrada'}
          </p>
        </div>
      </section>

      <section className="mt-4">
        <h4 className="text-[12px] font-bold uppercase text-corporativo-600">II. Asistencia</h4>
        <table className="mt-2 w-full border-collapse text-[12px]">
          <thead>
            <tr className="bg-corporativo-50 text-left">
              <th className="border border-slate-300 px-2 py-1">No.</th>
              <th className="border border-slate-300 px-2 py-1">Nombre</th>
              <th className="border border-slate-300 px-2 py-1">Carácter</th>
              <th className="border border-slate-300 px-2 py-1 text-right">Acciones</th>
              <th className="border border-slate-300 px-2 py-1 text-right">% Capital</th>
            </tr>
          </thead>
          <tbody>
            {estado.asistentes.map((asistente, indice) => (
              <tr key={asistente.clave || `asistente-vista-${indice}`}>
                <td className="border border-slate-300 px-2 py-1">{indice + 1}</td>
                <td className="border border-slate-300 px-2 py-1">{asistente.nombre || '—'}</td>
                <td className="border border-slate-300 px-2 py-1">
                  {String(asistente.caracter || '').replace(/_/g, ' ')}
                </td>
                <td className="border border-slate-300 px-2 py-1 text-right">{numero(asistente.acciones)}</td>
                <td className="border border-slate-300 px-2 py-1 text-right">
                  {porcentaje(calculos.porcentajes?.[indice] || 0, 2)}
                </td>
              </tr>
            ))}
            {!estado.asistentes.length ? (
              <tr>
                <td className="border border-slate-300 px-2 py-2 text-center text-slate-500" colSpan={5}>
                  Sin asistentes registrados.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>

      <section className="mt-4">
        <h4 className="text-[12px] font-bold uppercase text-corporativo-600">III. Orden del día</h4>
        <ol className="mt-2 list-decimal space-y-1 pl-5">
          {estado.orden_del_dia.map((punto, indice) => (
            <li key={punto.clave || `punto-vista-${indice}`}>
              {punto.titulo || '—'}
              {punto.descripcion ? <span className="text-slate-500"> — {punto.descripcion}</span> : null}
            </li>
          ))}
        </ol>
      </section>

      <section className="mt-4">
        <h4 className="text-[12px] font-bold uppercase text-corporativo-600">
          IV. Acuerdos y resoluciones
        </h4>
        {acuerdos.map((acuerdo, indice) => (
          <div key={acuerdo.clave || `acuerdo-vista-${indice}`} className="mt-3">
            <p className="font-bold">
              ACUERDO {acuerdo.numero}. {acuerdo.titulo || 'Sin título'}
            </p>
            <p className="mt-1 whitespace-pre-wrap text-justify">
              {acuerdo.clausula_legal || acuerdo.resumen || 'Sin texto redactado.'}
            </p>
            {acuerdo.fundamento_legal ? (
              <p className="mt-1 text-[11px] italic text-slate-500">
                Fundamento legal: {acuerdo.fundamento_legal}
              </p>
            ) : null}
          </div>
        ))}
      </section>

      {estado.observaciones ? (
        <section className="mt-4">
          <h4 className="text-[12px] font-bold uppercase text-corporativo-600">
            V. Observaciones y salvedades
          </h4>
          <p className="mt-1 whitespace-pre-wrap text-justify">{estado.observaciones}</p>
        </section>
      ) : null}

      <section className="mt-6 border-t border-slate-300 pt-4">
        <h4 className="text-[12px] font-bold uppercase text-corporativo-600">VI. Firmas</h4>
        <div className="mt-8 grid gap-8 sm:grid-cols-2">
          {estado.asistentes
            .filter((asistente) => asistente.firma !== false)
            .map((asistente, indice) => (
              <div key={asistente.clave || `firma-${indice}`} className="text-center">
                <p className="border-t border-slate-400 pt-1 font-semibold">
                  {asistente.nombre || '—'}
                </p>
                <p className="text-[11px] text-slate-500">
                  {String(asistente.caracter || '').replace(/_/g, ' ')}
                  {asistente.cargo ? ` · ${asistente.cargo}` : ''}
                </p>
              </div>
            ))}
        </div>
      </section>

    </article>
  )
}
