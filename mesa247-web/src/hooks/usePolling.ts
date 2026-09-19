import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../lib/api'

type Options = {
  intervalMs: number
  /** Al llegar a un estado terminal se deja de consultar: batería y datos del comensal. */
  enabled?: boolean
  /** Cambiarla reinicia el ciclo y descarta el dato anterior (otro token, otro local). */
  key?: string
}

export type Polling<T> = {
  data: T | null
  error: ApiError | null
  offline: boolean
  loading: boolean
  refresh: () => void
}

const MAX_BACKOFF_MS = 60_000

/**
 * Consulta periódica con lo que pide el corte (09 § 6) y nada más:
 * pausa con la pestaña oculta, refresco al volver, backoff hasta 60 s y, ante
 * un corte de red, conserva el último dato en lugar de mostrar un error.
 */
export function usePolling<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  { intervalMs, enabled = true, key = '' }: Options,
): Polling<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [offline, setOffline] = useState(false)
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)

  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    setData(null)
    setError(null)
    setLoading(true)
  }, [key])

  useEffect(() => {
    if (!enabled) {
      setLoading(false)
      return
    }

    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    let stopped = false
    let running = false
    let failures = 0

    const cycle = async () => {
      if (stopped || running || document.hidden) return
      running = true
      try {
        const next = await fetcherRef.current(controller.signal)
        if (stopped) return
        failures = 0
        setData(next)
        setError(null)
        setOffline(false)
        setLoading(false)
      } catch (cause) {
        if (stopped || controller.signal.aborted) return
        setLoading(false)
        if (cause instanceof ApiError) {
          // Un 404 o un 401 no se arreglan repitiendo: el ciclo se detiene.
          setError(cause)
          return
        }
        failures += 1
        setOffline(true)
      } finally {
        running = false
      }
      if (stopped) return
      const wait = failures === 0 ? intervalMs : Math.min(MAX_BACKOFF_MS, intervalMs * 2 ** failures)
      timer = setTimeout(() => void cycle(), wait)
    }

    // Volver a la pestaña o recuperar la red reinicia el ciclo sin esperar al backoff.
    const resume = () => {
      clearTimeout(timer)
      if (document.hidden) return
      failures = 0
      void cycle()
    }

    document.addEventListener('visibilitychange', resume)
    window.addEventListener('online', resume)
    void cycle()

    return () => {
      stopped = true
      clearTimeout(timer)
      controller.abort()
      document.removeEventListener('visibilitychange', resume)
      window.removeEventListener('online', resume)
    }
  }, [enabled, intervalMs, key, reloadKey])

  const refresh = useCallback(() => setReloadKey((value) => value + 1), [])

  return { data, error, offline, loading, refresh }
}
