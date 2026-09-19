import { useEffect, useState } from 'react'
import { ApiError, api } from '../lib/api'
import type { LocationPublic } from '../lib/types'

type State = {
  location: LocationPublic | null
  error: string | null
}

/** Carga los datos públicos del local: los comparten el registro y la recuperación. */
export function useLocationInfo(code: string): State {
  const [state, setState] = useState<State>({ location: null, error: null })

  useEffect(() => {
    const controller = new AbortController()
    setState({ location: null, error: null })
    api
      .location(code, controller.signal)
      .then((location) => setState({ location, error: null }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        const message =
          error instanceof ApiError
            ? error.status === 404
              ? 'Este código no corresponde a ningún local activo. Revisa el QR de la puerta.'
              : error.message
            : 'No pudimos cargar el local. Revisa tu conexión e inténtalo otra vez.'
        setState({ location: null, error: message })
      })
    return () => controller.abort()
  }, [code])

  return state
}
