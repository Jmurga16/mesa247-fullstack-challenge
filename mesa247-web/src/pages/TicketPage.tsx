import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ConnectionBanner from '../components/ConnectionBanner'
import ErrorBanner from '../components/ErrorBanner'
import { usePolling } from '../hooks/usePolling'
import { ApiError, OfflineError, api } from '../lib/api'
import { aheadLabel, clockSkewMs, clockTime, minutesLeft, partyLabel } from '../lib/format'
import { readLocal, storageKeys } from '../lib/storage'
import type { TicketPublic, TicketStatus } from '../lib/types'
import { isTerminal } from '../lib/types'

// Cerca del turno se consulta más seguido; el resto del tiempo, menos.
const NEAR_INTERVAL_MS = 10_000
const FAR_INTERVAL_MS = 15_000

const CLOSED: Record<string, { title: string; detail: string }> = {
  seated: {
    title: 'Ya estás en tu mesa',
    detail: 'Que lo disfrutes. Gracias por esperar con nosotros.',
  },
  cancelled: {
    title: 'Cancelaste tu turno',
    detail: 'Saliste de la lista de espera. Puedes volver a unirte cuando quieras.',
  },
  no_show: {
    title: 'El turno se cerró',
    detail: 'El anfitrión marcó que no llegaste a tiempo. Si sigues en el local, acércate a la puerta.',
  },
  removed: {
    title: 'El turno ya no está en la lista',
    detail: 'El anfitrión lo quitó. Si fue un error, habla con él en la puerta.',
  },
  expired: {
    title: 'El turno venció',
    detail: 'La lista de hoy ya se cerró. Si sigues en el local, acércate a la puerta.',
  },
}

export default function TicketPage() {
  const { token = '' } = useParams()
  const [override, setOverride] = useState<TicketPublic | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [confirmingCancel, setConfirmingCancel] = useState(false)
  const [cancelling, setCancelling] = useState(false)

  const [intervalMs, setIntervalMs] = useState(FAR_INTERVAL_MS)
  const closed = override ? isTerminal(override.status) : false

  const polling = usePolling<TicketPublic>((signal) => api.ticket(token, signal), {
    intervalMs,
    enabled: !closed,
    key: token,
  })

  const ticket = override ?? polling.data
  const lastCode = readLocal(storageKeys.lastCode)

  // Se deja de consultar en cuanto el turno llega a un estado final.
  useEffect(() => {
    if (polling.data && isTerminal(polling.data.status)) setOverride(polling.data)
  }, [polling.data])

  // Cerca del turno se pregunta más seguido.
  const ahead = polling.data?.groups_ahead
  useEffect(() => {
    setIntervalMs(ahead !== null && ahead !== undefined && ahead <= 3 ? NEAR_INTERVAL_MS : FAR_INTERVAL_MS)
  }, [ahead])

  // Cuenta regresiva del llamado: se apoya en server_now, no en el reloj del celular.
  const [, setTick] = useState(0)
  useEffect(() => {
    if (ticket?.status !== 'called') return
    const id = setInterval(() => setTick((value) => value + 1), 1000)
    return () => clearInterval(id)
  }, [ticket?.status])

  // El desfase con el servidor se fija con cada dato nuevo, no en cada render:
  // así el segundo que pasa en el celular es un segundo menos en la cuenta.
  const skewRef = useRef<{ serverNow: string; value: number }>({ serverNow: '', value: 0 })
  if (ticket && ticket.server_now !== skewRef.current.serverNow) {
    skewRef.current = { serverNow: ticket.server_now, value: clockSkewMs(ticket.server_now) }
  }

  // Animación solo cuando el número baja (07 § 4 punto 2).
  const previousAhead = useRef<number | null>(null)
  const [dropped, setDropped] = useState(false)
  useEffect(() => {
    const ahead = ticket?.groups_ahead ?? null
    const previous = previousAhead.current
    previousAhead.current = ahead
    if (previous === null || ahead === null || ahead >= previous) return
    setDropped(true)
    const id = setTimeout(() => setDropped(false), 900)
    return () => clearTimeout(id)
  }, [ticket?.groups_ahead])

  const cancel = async () => {
    if (cancelling) return
    setCancelling(true)
    setActionError(null)
    try {
      setOverride(await api.cancelTicket(token))
      setConfirmingCancel(false)
    } catch (error) {
      if (error instanceof OfflineError) {
        setActionError('Sin conexión. No pudimos cancelar; inténtalo otra vez.')
      } else if (error instanceof ApiError) {
        setActionError(error.message)
        polling.refresh()
      } else {
        setActionError('No pudimos cancelar tu turno. Inténtalo otra vez.')
      }
    } finally {
      setCancelling(false)
    }
  }

  if (polling.error && !ticket) {
    return (
      <main className="screen screen-narrow">
        <section className="card">
          <h1>No encontramos este turno</h1>
          <p>
            {polling.error.status === 404
              ? 'El enlace no corresponde a ningún turno. Si te anotaste hoy, vuelve al QR del local y usa «Ya estoy en la lista de espera».'
              : polling.error.message}
          </p>
          {lastCode && (
            <Link className="button button-secondary button-block" to={`/q/${lastCode}`}>
              Ir a la lista del local
            </Link>
          )}
        </section>
      </main>
    )
  }

  if (!ticket) {
    return (
      <main className="screen screen-narrow">
        <section className="card">
          {/* El aviso de red va antes del «cargando»: si la primera consulta no sale,
              el comensal tiene que saberlo y no quedarse mirando un spinner. */}
          <ConnectionBanner offline={polling.offline} />
          <p className="muted" role="status">Cargando tu turno…</p>
        </section>
      </main>
    )
  }

  const remaining = ticket.deadline_at
    ? minutesLeft(ticket.deadline_at, skewRef.current.value)
    : null

  return (
    <main className="screen screen-narrow">
      <section className={`card status-${ticket.status}`}>
        <header className="card-header">
          {lastCode && (
            <Link
              className="card-close"
              to={`/q/${lastCode}`}
              title="Volver a la lista del local"
              aria-label="Volver a la lista del local"
            >
              ×
            </Link>
          )}
          <h1>{ticket.location_name}</h1>
          <p className="eyebrow">
            {ticket.name} · {partyLabel(ticket.party_size)}
          </p>
        </header>

        <ConnectionBanner offline={polling.offline} />
        <ErrorBanner error={polling.error} />

        {ticket.status === 'waiting' && (
          <>
            <div className={`turn${dropped ? ' turn-dropped' : ''}`}>
              {/* Un «0» gigante no dice nada: cuando no queda nadie delante, manda el texto. */}
              {ticket.groups_ahead === 0 ? (
                <span className="turn-next">Eres el siguiente</span>
              ) : (
                <>
                  <span className="turn-number">{ticket.groups_ahead}</span>
                  <span className="turn-label">{aheadLabel(ticket.groups_ahead ?? 0)}</span>
                </>
              )}
            </div>
            <dl className="eta">
              <dt>Tiempo estimado</dt>
              <dd>≈ {ticket.eta_min} min</dd>
            </dl>
            <p className="muted">
              Es aproximado: depende de las mesas que se vayan liberando.
            </p>
            <p className="notice">
              Te avisaremos por WhatsApp cuando tu mesa esté lista. Quédate cerca del local.
            </p>
          </>
        )}

        {ticket.status === 'called' && (
          <>
            <p className="banner banner-ready" role="status">
              ¡{ticket.name}, tu mesa está lista!
            </p>
            {ticket.deadline_at && (
              <p className="deadline">
                Tienes hasta las <strong>{clockTime(ticket.deadline_at)}</strong> para acercarte a la
                entrada.{' '}
                {remaining !== null && remaining > 0
                  ? `Quedan ${remaining} min.`
                  : 'El tiempo se cumplió: acércate a la puerta.'}
              </p>
            )}
          </>
        )}

        {isTerminal(ticket.status) && (
          <div className="closed">
            <h2>{CLOSED[ticket.status]?.title ?? 'El turno se cerró'}</h2>
            <p>{CLOSED[ticket.status]?.detail ?? ''}</p>
            {lastCode && ticket.status !== 'seated' && (
              <Link className="button button-secondary button-block" to={`/q/${lastCode}`}>
                Volver a unirme
              </Link>
            )}
          </div>
        )}

        {actionError && <p className="banner banner-warn" role="alert">{actionError}</p>}

        {canLeave(ticket.status) && (
          <div className="actions">
            {confirmingCancel ? (
              <div className="confirm">
                <p>¿Seguro que sales de la lista? No se puede deshacer.</p>
                <div className="confirm-buttons">
                  <button
                    type="button"
                    className="button button-danger"
                    onClick={cancel}
                    disabled={cancelling}
                  >
                    {cancelling ? 'Cancelando…' : 'Sí, ya no voy'}
                  </button>
                  <button
                    type="button"
                    className="button button-secondary"
                    onClick={() => setConfirmingCancel(false)}
                    disabled={cancelling}
                  >
                    Sigo esperando
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                className="button button-quiet button-block"
                onClick={() => setConfirmingCancel(true)}
              >
                Ya no voy
              </button>
            )}
          </div>
        )}
      </section>
    </main>
  )
}

function canLeave(status: TicketStatus): boolean {
  return status === 'waiting' || status === 'called'
}
