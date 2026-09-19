import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import ConnectionBanner from '../components/ConnectionBanner'
import { usePolling } from '../hooks/usePolling'
import { ApiError, OfflineError, api } from '../lib/api'
import { clockTime, partyLabel, waitLabel, weekdayOf } from '../lib/format'
import { readLocal, removeLocal, storageKeys, writeLocal } from '../lib/storage'
import type { HostAction, HostQueue, HostRow } from '../lib/types'

const QUEUE_INTERVAL_MS = 5_000

export default function HostPage() {
  const [params, setParams] = useSearchParams()
  const [token, setToken] = useState(() => readLocal(storageKeys.hostToken) ?? '')
  const [busyId, setBusyId] = useState<number | null>(null)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  // El token llega por la URL del seed: se guarda y se limpia de la barra de direcciones.
  useEffect(() => {
    const fromUrl = params.get('token')
    if (!fromUrl) return
    writeLocal(storageKeys.hostToken, fromUrl)
    setToken(fromUrl)
    const next = new URLSearchParams(params)
    next.delete('token')
    setParams(next, { replace: true })
  }, [params, setParams])

  const polling = usePolling<HostQueue>((signal) => api.hostQueue(token, signal), {
    intervalMs: QUEUE_INTERVAL_MS,
    enabled: Boolean(token),
    key: token,
  })

  const forgetDevice = () => {
    removeLocal(storageKeys.hostToken)
    setToken('')
  }

  const run = async (row: HostRow, action: HostAction) => {
    if (busyId !== null) return
    setBusyId(row.id)
    setNotice(null)
    setConfirmingId(null)
    try {
      await api.hostAction(token, row.id, action)
      polling.refresh()
    } catch (error) {
      if (error instanceof OfflineError) {
        setNotice('Sin conexión: la acción no se registró. Inténtalo otra vez.')
      } else if (error instanceof ApiError && error.status === 409) {
        setNotice(`Otro anfitrión ya atendió a ${row.name}.`)
        polling.refresh()
      } else if (error instanceof ApiError) {
        setNotice(error.message)
        polling.refresh()
      } else {
        setNotice('No pudimos aplicar la acción. Inténtalo otra vez.')
      }
    } finally {
      setBusyId(null)
    }
  }

  if (!token || polling.error?.status === 401) {
    return (
      <main className="screen screen-wide">
        <section className="card">
          <h1>Esta tablet no tiene sesión</h1>
          <p>
            Abre el enlace del local que imprime el seed
            (<code>/host?token=…</code>). El token queda guardado en esta tablet y se limpia de la
            barra de direcciones.
          </p>
          <Link className="button button-primary" to="/admin">
            Abrir la tablet de un local
          </Link>
          {token && (
            <button type="button" className="button button-secondary" onClick={forgetDevice}>
              Olvidar el token guardado
            </button>
          )}
        </section>
      </main>
    )
  }

  const queue = polling.data

  return (
    <main className="screen screen-wide">
      <header className="host-header">
        <div>
          <h1>
            {queue
              ? `${queue.location.name} · ${weekdayOf(queue.service_date)}`
              : polling.error
                ? 'No pudimos cargar la cola'
                : 'Cargando la cola…'}
          </h1>
          {queue && (
            <p className="eyebrow">
              {queue.waiting_count} en cola ·{' '}
              {queue.avg_wait_min === null
                ? 'aún sin espera media de hoy'
                : `espera media ${Math.round(queue.avg_wait_min)} min`}
            </p>
          )}
        </div>
        <div className="host-header-actions">
          <Link className="button button-quiet" to="/host/reporte">
            Reporte del día
          </Link>
          <button type="button" className="button button-secondary" onClick={polling.refresh}>
            Actualizar
          </button>
        </div>
      </header>

      <ConnectionBanner offline={polling.offline} />
      {notice && <p className="banner banner-warn" role="alert">{notice}</p>}
      {polling.error && (
        <p className="banner banner-warn" role="alert">
          {polling.error.message}{' '}
          <button type="button" className="link" onClick={polling.refresh}>
            Reintentar
          </button>
        </p>
      )}

      {queue && queue.rows.length === 0 && (
        <p className="empty">
          Nadie en la lista todavía. Las altas entran por el QR de la puerta.
        </p>
      )}

      <ul className="queue">
        {queue?.rows.map((row, index) => (
          <li key={row.id} className={`queue-row${row.overdue ? ' is-overdue' : ''}`}>
            <span className="queue-position">{index + 1}</span>

            <div className="queue-main">
              <p className="queue-name">{row.name}</p>
              <p className="queue-meta">
                {partyLabel(row.party_size)} · esperando {waitLabel(row.waiting_min)}
              </p>
              <div className="chips">
                {row.status === 'called' && row.called_at && (
                  <span className="chip chip-called">Llamado {clockTime(row.called_at)}</span>
                )}
                {row.status === 'called' && row.deadline_at && (
                  <span className={`chip${row.overdue ? ' chip-danger' : ''}`}>
                    {row.overdue ? 'Venció' : 'Hasta'} {clockTime(row.deadline_at)}
                  </span>
                )}
                {row.on_the_way && <span className="chip chip-ok">Voy en camino</span>}
                {row.notify_state === 'failed' && (
                  <span className="chip chip-danger">Aviso no entregado</span>
                )}
                {row.notify_state === 'sent' && <span className="chip">Aviso enviado</span>}
              </div>
            </div>

            <div className="queue-actions">
              {row.status === 'waiting' && (
                <button
                  type="button"
                  className="button button-primary"
                  onClick={() => run(row, 'call')}
                  disabled={busyId !== null}
                >
                  {busyId === row.id ? 'Enviando…' : 'Llamar'}
                </button>
              )}
              <button
                type="button"
                className="button button-secondary"
                onClick={() => run(row, 'seat')}
                disabled={busyId !== null}
              >
                Sentar
              </button>
              {row.status === 'called' ? (
                <button
                  type="button"
                  className="button button-quiet"
                  onClick={() => run(row, 'no-show')}
                  disabled={busyId !== null}
                >
                  No vino
                </button>
              ) : (
                <button
                  type="button"
                  className="button button-quiet"
                  onClick={() => run(row, 'leave')}
                  disabled={busyId !== null}
                >
                  Se fue
                </button>
              )}

              {confirmingId === row.id ? (
                <span className="confirm-inline">
                  <button
                    type="button"
                    className="button button-danger"
                    onClick={() => run(row, 'remove')}
                    disabled={busyId !== null}
                  >
                    Confirmar
                  </button>
                  <button
                    type="button"
                    className="button button-quiet"
                    onClick={() => setConfirmingId(null)}
                  >
                    No
                  </button>
                </span>
              ) : (
                <button
                  type="button"
                  className="button button-quiet"
                  onClick={() => setConfirmingId(row.id)}
                  disabled={busyId !== null}
                  title="Quitar de la lista por error o duplicado"
                >
                  Borrar
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>

      <footer className="host-footer">
        <p className="muted">
          La lista se actualiza sola cada {QUEUE_INTERVAL_MS / 1000} segundos. «Llamar» dos veces no
          envía un segundo aviso.
        </p>
        <span className="host-links">
          <Link className="link" to="/admin">Cambiar de tablet</Link>
          <button type="button" className="link" onClick={forgetDevice}>
            Cerrar esta tablet
          </button>
        </span>
      </footer>
    </main>
  )
}
