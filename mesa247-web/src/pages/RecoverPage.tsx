import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import PhoneField from '../components/PhoneField'
import { useLocationInfo } from '../hooks/useLocationInfo'
import { ApiError, OfflineError, api } from '../lib/api'
import { PHONE_INVALID, looksLikePhone } from '../lib/phone'
import { storageKeys, writeLocal } from '../lib/storage'

/**
 * «Ya estoy en la lista de espera»: pantalla propia con retorno al registro.
 * El teléfono es la credencial; el riesgo asumido está en 09 § 2.5.
 */
export default function RecoverPage() {
  const { code = '' } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { location, error: loadError } = useLocationInfo(code)

  const [phone, setPhone] = useState(params.get('phone') ?? '')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  // El número se busca tal como se escribió al anotarse: con su código de país.
  const prefilled = useRef(false)
  useEffect(() => {
    if (prefilled.current || !location) return
    prefilled.current = true
    setPhone((current) => current || `${location.phone_prefix} `)
  }, [location])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (busy) return
    setError(null)
    if (!looksLikePhone(phone)) {
      setError(PHONE_INVALID)
      return
    }
    setBusy(true)
    try {
      const ticket = await api.lookup(code, phone.trim())
      writeLocal(storageKeys.ticketToken(code), ticket.token)
      writeLocal(storageKeys.lastCode, code)
      navigate(`/t/${ticket.token}`, { replace: true })
    } catch (cause) {
      if (cause instanceof OfflineError) {
        setError('Sin conexión. Revisa tus datos e inténtalo otra vez.')
      } else if (cause instanceof ApiError) {
        setError(cause.status === 422 ? (cause.fields.phone ?? cause.message) : cause.message)
      } else {
        setError('No pudimos buscar tu turno. Inténtalo otra vez.')
      }
    } finally {
      setBusy(false)
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

  return (
    <main className="screen screen-narrow">
      <section className="card">
        <header className="card-header">
          <h1>{location ? location.name : 'Lista de espera'}</h1>
          <p className="eyebrow">Volver a mi turno</p>
        </header>

        <p className="muted">
          Escribe el teléfono con el que te anotaste y te llevamos a tu turno de hoy.
        </p>

        <form onSubmit={submit} noValidate>
          <PhoneField
            id="recovery-phone"
            label="Teléfono con el que te anotaste"
            value={phone}
            prefix={location?.phone_prefix ?? '+'}
            error={error ?? undefined}
            autoFocus
            onChange={setPhone}
          />
          <button
            type="submit"
            className="button button-primary button-block"
            disabled={busy || !location}
          >
            {busy ? 'Buscando…' : 'Ver mi turno'}
          </button>
        </form>

        <p className="back-link">
          <Link className="link" to={`/q/${code}`}>
            Todavía no me he anotado
          </Link>
        </p>
      </section>
    </main>
  )
}
