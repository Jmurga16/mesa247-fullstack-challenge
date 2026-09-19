import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import AlreadyInQueueNotice from '../components/AlreadyInQueueNotice'
import PartySizeField from '../components/PartySizeField'
import PhoneField from '../components/PhoneField'
import { useLocationInfo } from '../hooks/useLocationInfo'
import { ApiError, OfflineError, api } from '../lib/api'
import { PHONE_HINT, PHONE_INVALID, looksLikePhone } from '../lib/phone'
import { readLocal, storageKeys, uuid, writeLocal } from '../lib/storage'
import type { JoinBody } from '../lib/api'
import type { TicketPublic } from '../lib/types'
import { isTerminal } from '../lib/types'

const OFFLINE_MESSAGE = 'Sin conexión. Revisa tus datos e inténtalo otra vez.'

type Payload = Omit<JoinBody, 'request_id'>

/** Dos altas distintas no pueden compartir llave de idempotencia. */
function fingerprint(payload: Payload): string {
  return `${payload.name.toLowerCase()}|${payload.phone}|${payload.party_size}`
}

export default function JoinPage() {
  const { code = '' } = useParams()
  const navigate = useNavigate()
  const { location, error: loadError } = useLocationInfo(code)

  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [partySize, setPartySize] = useState(2)
  const [fields, setFields] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Estado de «este teléfono ya está esperando», con sus dos salidas.
  const [conflict, setConflict] = useState(false)
  const [conflictBusy, setConflictBusy] = useState<'ver' | 'nuevo' | null>(null)
  const [conflictError, setConflictError] = useState<string | null>(null)
  const [confirmingRestart, setConfirmingRestart] = useState(false)

  /**
   * El `request_id` identifica un envío, no un dispositivo: vive en memoria y
   * atado a los datos del formulario. Guardarlo por local hacía que el segundo
   * comensal de la misma pantalla reenviara la llave del primero, y el servidor
   * respondía —con razón— el turno ya creado en lugar de crear el suyo.
   */
  const request = useRef<{ key: string; id: string } | null>(null)

  const requestIdFor = (payload: Payload, rotate = false): string => {
    const key = fingerprint(payload)
    if (!rotate && request.current?.key === key) return request.current.id
    request.current = { key, id: uuid() }
    return request.current.id
  }

  const savedToken = readLocal(storageKeys.ticketToken(code))

  const goToTicket = (ticket: TicketPublic) => {
    // El envío terminó: la llave no debe sobrevivir a su propio turno.
    request.current = null
    writeLocal(storageKeys.ticketToken(code), ticket.token)
    writeLocal(storageKeys.lastCode, code)
    navigate(`/t/${ticket.token}`, { replace: true })
  }

  const describe = (error: unknown, fallback: string) => {
    if (error instanceof OfflineError) return OFFLINE_MESSAGE
    if (error instanceof ApiError) return error.message
    return fallback
  }

  const body = (): Payload => ({ name: name.trim(), phone: phone.trim(), party_size: partySize })

  // El prefijo del local es solo el punto de partida del campo, no un límite.
  const prefilled = useRef(false)
  useEffect(() => {
    if (prefilled.current || !location) return
    prefilled.current = true
    setPhone((current) => current || `${location.phone_prefix} `)
  }, [location])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (submitting) return
    setFields({})
    setFormError(null)
    const payload = body()
    if (!looksLikePhone(payload.phone)) {
      setFields({ phone: PHONE_INVALID })
      return
    }
    setSubmitting(true)
    try {
      let ticket = await api.join(code, { request_id: requestIdFor(payload), ...payload })
      if (isTerminal(ticket.status)) {
        // La llave apunta a un turno ya cerrado: se rota y se reenvía.
        ticket = await api.join(code, { request_id: requestIdFor(payload, true), ...payload })
      }
      goToTicket(ticket)
    } catch (error) {
      if (error instanceof ApiError && error.status === 422) {
        setFields(error.fields)
      } else if (error instanceof ApiError && error.code === 'already_in_queue') {
        // El mensaje del backend nombra la pantalla; aquí esa pantalla ya está delante.
        setConflict(true)
      } else {
        setFormError(describe(error, 'No pudimos unirte a la cola. Inténtalo otra vez.'))
      }
    } finally {
      setSubmitting(false)
    }
  }

  const seeMyTurn = async () => {
    setConflictBusy('ver')
    setConflictError(null)
    try {
      goToTicket(await api.lookup(code, phone.trim()))
    } catch (error) {
      setConflictError(
        describe(error, 'No pudimos abrir tu turno. Vuelve a intentarlo en unos segundos.'),
      )
    } finally {
      setConflictBusy(null)
    }
  }

  const registerAgain = async () => {
    if (!confirmingRestart) {
      setConfirmingRestart(true)
      return
    }
    setConflictBusy('nuevo')
    setConflictError(null)
    try {
      // No hay un alta que reemplace en una sola llamada: se cancela el turno
      // anterior y se crea el nuevo. Entre las dos, el teléfono queda libre.
      const previous = await api.lookup(code, phone.trim()).catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 404) return null
        throw error
      })
      if (previous) await api.cancelTicket(previous.token)
      const payload = body()
      goToTicket(await api.join(code, { request_id: requestIdFor(payload, true), ...payload }))
    } catch (error) {
      setConflictError(
        describe(error, 'No pudimos crear el registro nuevo. Inténtalo otra vez.'),
      )
      setConfirmingRestart(false)
    } finally {
      setConflictBusy(null)
    }
  }

  if (loadError) {
    return (
      <main className="screen screen-narrow">
        <section className="card">
          <h1>No encontramos este local</h1>
          <p>{loadError}</p>
        </section>
      </main>
    )
  }

  if (!location) {
    return (
      <main className="screen screen-narrow">
        <section className="card">
          <p className="muted" role="status">Cargando el local…</p>
        </section>
      </main>
    )
  }

  if (conflict) {
    return (
      <main className="screen screen-narrow">
        <AlreadyInQueueNotice
          locationName={location.name}
          busy={conflictBusy}
          error={conflictError}
          confirming={confirmingRestart}
          onSeeMyTurn={seeMyTurn}
          onRegisterAgain={registerAgain}
          onCancelRegisterAgain={() => setConfirmingRestart(false)}
          onBack={() => {
            setConflict(false)
            setConflictError(null)
            setConfirmingRestart(false)
          }}
        />
      </main>
    )
  }

  return (
    <main className="screen screen-narrow">
      <section className="card">
        <header className="card-header">
          <h1>{location.name}</h1>
          <p className="eyebrow">Lista de espera · hoy</p>
        </header>

        {savedToken && (
          <p className="banner banner-info">
            Ya tienes un turno guardado en este dispositivo.{' '}
            <button type="button" className="link" onClick={() => navigate(`/t/${savedToken}`)}>
              Volver a mi turno
            </button>
          </p>
        )}

        <form onSubmit={submit} noValidate>
          <div className="field">
            <label htmlFor="name">Nombre</label>
            <input
              id="name"
              value={name}
              maxLength={40}
              autoComplete="given-name"
              placeholder="Carla"
              aria-invalid={Boolean(fields.name)}
              onChange={(event) => setName(event.target.value)}
            />
            {fields.name && <p className="field-error" role="alert">{fields.name}</p>}
          </div>

          <PhoneField
            id="phone"
            value={phone}
            prefix={location.phone_prefix}
            error={fields.phone}
            hint={`Lo usamos para avisarte cuando tu mesa esté lista. ${PHONE_HINT}`}
            onChange={setPhone}
          />

          <PartySizeField
            value={partySize}
            max={location.max_party_size}
            error={fields.party_size}
            onChange={setPartySize}
          />

          {formError && <p className="banner banner-warn" role="alert">{formError}</p>}

          <p className="consent">
            Al unirte guardamos tu nombre y tu teléfono para avisarte de tu mesa. Nada más.
          </p>

          <button type="submit" className="button button-primary button-block" disabled={submitting}>
            {submitting ? 'Uniéndote…' : 'Unirme a la cola'}
          </button>
        </form>

        <p className="back-link">
          <Link className="link" to={`/q/${code}/mi-turno`}>
            Ya estoy en la lista de espera
          </Link>
        </p>
      </section>
    </main>
  )
}
