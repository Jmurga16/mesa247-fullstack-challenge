import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ConnectionBanner from '../components/ConnectionBanner'
import ErrorBanner from '../components/ErrorBanner'
import NoHostSession from '../components/NoHostSession'
import { usePolling } from '../hooks/usePolling'
import { api } from '../lib/api'
import { longDateOf, waitLabel } from '../lib/format'
import { readLocal, storageKeys } from '../lib/storage'
import type { HostReport } from '../lib/types'

// El reporte no es la cola: cambia poco y nadie lo mira esperando una fila.
const REPORT_INTERVAL_MS = 30_000

type Line = { label: string; value: string; warn?: boolean }

function groupsLabel(groups: number): string {
  return groups === 1 ? '1 grupo' : `${groups} grupos`
}

/**
 * Reporte del día del enunciado (punto 5), con las definiciones de 04 § 6.
 *
 * Tres cosas que la pantalla dice y el mockup no: los conteos son de **grupos**,
 * no de personas; mientras queden turnos sin resolver el día **no ha cerrado** y
 * la suma no cuadra todavía; y el correo del cierre no existe en esta versión.
 */
export default function ReportPage() {
  const token = readLocal(storageKeys.hostToken) ?? ''
  const [day, setDay] = useState('')
  const [today, setToday] = useState('')

  const polling = usePolling<HostReport>((signal) => api.hostReport(token, day || undefined, signal), {
    intervalMs: REPORT_INTERVAL_MS,
    enabled: Boolean(token),
    key: `${token}:${day}`,
  })

  const report = polling.data

  // El día de servicio en curso lo dice el servidor, no el reloj de la tablet:
  // se recuerda para que elegir un día pasado no impida volver a hoy.
  useEffect(() => {
    if (report && !day) setToday(report.service_date)
  }, [report, day])

  // Va después de los hooks: perder la sesión con el reporte abierto cambiaba el
  // número de hooks ejecutados y React tumbaba la pantalla.
  if (!token || polling.error?.status === 401) {
    return (
      <NoHostSession>
        <p>El reporte es del local de la tablet, así que necesita su sesión abierta.</p>
      </NoHostSession>
    )
  }

  const closed = report !== null && report.pending === 0
  const lines: Line[] = report ? [
    { label: 'Se unieron', value: String(report.joined) },
    { label: 'Se sentaron', value: String(report.seated) },
    { label: 'Se fueron sin sentarse', value: String(report.left_before_seating), warn: true },
    { label: 'No vinieron al ser llamados', value: String(report.no_show) },
    {
      label: 'Espera media',
      value: report.avg_wait_min === null ? 'sin datos' : waitLabel(Math.round(report.avg_wait_min)),
    },
  ] : []

  return (
    <main className="screen screen-wide">
      <header className="host-header">
        <div>
          <h1>
            {report
              ? longDateOf(report.service_date)
              : polling.error
                ? 'No pudimos cargar el reporte'
                : 'Cargando el reporte…'}
          </h1>
          {report && (
            <p className="eyebrow">
              {report.location.name} · {closed ? 'cierre del día' : 'día en curso'}
            </p>
          )}
        </div>
        <button type="button" className="button button-secondary" onClick={polling.refresh}>
          Actualizar
        </button>
      </header>

      <ConnectionBanner offline={polling.offline} />
      <ErrorBanner error={polling.error} onRetry={polling.refresh} />

      <label className="report-day">
        <span className="label">Día de servicio</span>
        <input
          type="date"
          value={day}
          max={today || undefined}
          onChange={(event) => setDay(event.target.value)}
        />
        {day && (
          <button type="button" className="link" onClick={() => setDay('')}>
            Volver a hoy
          </button>
        )}
      </label>

      {report && (
        <section className="report">
          <dl className="report-lines">
            {lines.map((line) => (
              <div className="report-line" key={line.label}>
                <dt>{line.label}</dt>
                <dd className={line.warn ? 'is-warn' : undefined}>{line.value}</dd>
              </div>
            ))}
          </dl>

          <p className="muted">
            Los cuatro primeros son <strong>grupos</strong>, no personas: {groupsLabel(report.joined)}{' '}
            suman {report.joined_guests} personas, y se sentaron {report.seated_guests}. La espera
            media solo mide a quienes se quedaron.
          </p>

          {!closed && (
            <p className="banner banner-warn" role="status">
              {groupsLabel(report.pending)} sin desenlace: el día no ha cerrado y la suma todavía no
              cuadra. Los números se cierran cuando el anfitrión resuelve el último turno.
            </p>
          )}

          {report.expired > 0 && (
            <p className="banner banner-info" role="status">
              {groupsLabel(report.expired)} los cerró el sistema al caducar, no una persona. Mucho
              cierre administrativo es un problema de uso de la tablet, no de comensales.
            </p>
          )}
        </section>
      )}

      <footer className="host-footer">
        <p className="muted">
          El envío por correo al cierre no está en esta versión: tampoco hay cierre automático del
          día, así que el reporte se lee aquí y se actualiza solo cada{' '}
          {REPORT_INTERVAL_MS / 1000} segundos.
        </p>
        <span className="host-links">
          <Link className="link" to="/host">Volver a la cola</Link>
        </span>
      </footer>
    </main>
  )
}
