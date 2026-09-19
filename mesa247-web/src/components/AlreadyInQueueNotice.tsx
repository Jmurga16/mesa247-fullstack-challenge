type Props = {
  locationName: string
  busy: 'ver' | 'nuevo' | null
  error: string | null
  confirming: boolean
  onSeeMyTurn: () => void
  onRegisterAgain: () => void
  onCancelRegisterAgain: () => void
  onBack: () => void
}

/**
 * Lo que ve quien vuelve a registrarse con un teléfono que ya está esperando.
 * Un 409 seco dejaba a esa persona sin saber qué hacer; aquí tiene las dos
 * salidas reales, y la que pierde el puesto en la cola lo dice antes.
 */
export default function AlreadyInQueueNotice({
  locationName, busy, error, confirming,
  onSeeMyTurn, onRegisterAgain, onCancelRegisterAgain, onBack,
}: Props) {
  return (
    <section className="card">
      <header className="card-header">
        <h1>Ya estás en la lista</h1>
        <p className="eyebrow">{locationName}</p>
      </header>

      <p>
        Este teléfono ya tiene un turno esperando en {locationName}. Puedes volver a él o empezar un
        registro nuevo.
      </p>
      {error && <p className="banner banner-warn" role="alert">{error}</p>}

      {confirming ? (
        <div className="confirm">
          <p>
            El registro nuevo <strong>cancela el que ya tienes</strong> y te deja al final de la
            cola, con un tiempo de espera mayor. ¿Seguimos?
          </p>
          <div className="confirm-buttons">
            <button
              type="button"
              className="button button-danger"
              onClick={onRegisterAgain}
              disabled={busy !== null}
            >
              {busy === 'nuevo' ? 'Registrando…' : 'Sí, empezar de nuevo'}
            </button>
            <button
              type="button"
              className="button button-secondary"
              onClick={onCancelRegisterAgain}
              disabled={busy !== null}
            >
              Mejor no
            </button>
          </div>
        </div>
      ) : (
        <div className="actions-stack">
          <button
            type="button"
            className="button button-primary button-block"
            onClick={onSeeMyTurn}
            disabled={busy !== null}
          >
            {busy === 'ver' ? 'Buscando…' : 'Ver mi turno'}
          </button>
          <button
            type="button"
            className="button button-quiet button-block"
            onClick={onRegisterAgain}
            disabled={busy !== null}
          >
            Registrarme de nuevo
          </button>
          <button type="button" className="link" onClick={onBack}>
            Volver al formulario
          </button>
        </div>
      )}
    </section>
  )
}
