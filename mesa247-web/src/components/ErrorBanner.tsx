import type { ApiError } from '../lib/api'

type Props = {
  error: ApiError | null
  /** Si la pantalla puede volver a intentarlo, el aviso lleva el botón. */
  onRetry?: () => void
}

/** El error del servidor llega ya redactado en español: se muestra tal cual. */
export default function ErrorBanner({ error, onRetry }: Props) {
  if (!error) return null
  return (
    <p className="banner banner-warn" role="alert">
      {error.message}
      {onRetry && (
        <>
          {' '}
          <button type="button" className="link" onClick={onRetry}>
            Reintentar
          </button>
        </>
      )}
    </p>
  )
}
