import type { HostAction, HostQueue, HostRow, LocationPublic, TicketPublic } from './types'

/** Error del servidor con mensaje ya redactado en español: se muestra tal cual. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly fields: Record<string, string> = {},
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** La petición no llegó a salir o no volvió: se reintenta, no se muestra como fallo. */
export class OfflineError extends Error {
  constructor() {
    super('Sin conexión. Seguimos intentando.')
    this.name = 'OfflineError'
  }
}

const GENERIC: Record<number, string> = {
  401: 'Esta tablet no tiene una sesión válida. Vuelve a abrir el enlace del local.',
  404: 'No encontramos lo que buscas.',
  409: 'Este turno ya cambió. Actualiza la pantalla.',
  503: 'El servicio no responde. Inténtalo de nuevo en unos segundos.',
}

// 422 lo genera Pydantic: el front lo traduce a un mensaje por campo.
const FIELD_MESSAGES: Record<string, string> = {
  name: 'Escribe el nombre con el que te llamamos (máximo 40 caracteres).',
  phone: 'Introduce un teléfono válido con su código de país.',
  party_size: 'Indica cuántas personas son.',
  request_id: 'No pudimos identificar el envío. Recarga la página e inténtalo otra vez.',
}

type ValidationDetail = { loc?: unknown[]; msg?: string; type?: string }

function translateFields(detail: unknown): Record<string, string> {
  if (!Array.isArray(detail)) return {}
  const fields: Record<string, string> = {}
  for (const item of detail as ValidationDetail[]) {
    const field = String(item.loc?.[1] ?? 'general')
    // `value_error` viene del dominio y ya está redactado en español; el resto
    // son mensajes genéricos de Pydantic, en inglés, que no se muestran.
    fields[field] =
      item.type === 'value_error' && item.msg
        ? item.msg
        : (FIELD_MESSAGES[field] ?? 'Revisa este dato.')
  }
  return fields
}

type Options = {
  method?: 'GET' | 'POST'
  body?: unknown
  token?: string
  signal?: AbortSignal
  onStatus?: (status: number) => void
}

async function request<T>(path: string, options: Options = {}): Promise<T> {
  const { method = 'GET', body, token, signal, onStatus } = options
  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response: Response
  try {
    response = await fetch(path, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (cause) {
    if (signal?.aborted) throw cause
    throw new OfflineError()
  }

  onStatus?.(response.status)
  const payload = await response.json().catch(() => null)

  if (response.ok) return payload as T
  if (response.status === 422) {
    const fields = translateFields((payload as { detail?: unknown })?.detail)
    throw new ApiError(422, 'validation_error', 'Revisa los datos del formulario.', fields)
  }

  const error = payload as { error?: string; message?: string } | null
  throw new ApiError(
    response.status,
    error?.error ?? 'error',
    error?.message ?? GENERIC[response.status] ?? 'No pudimos completar la operación.',
    {},
  )
}

export type JoinBody = {
  request_id: string
  name: string
  phone: string
  party_size: number
}

export const api = {
  location: (code: string, signal?: AbortSignal) =>
    request<LocationPublic>(`/api/public/locations/${encodeURIComponent(code)}`, { signal }),

  /** 201 alta nueva, 200 reintento del mismo request_id: la pantalla trata igual a las dos. */
  join: (code: string, body: JoinBody) =>
    request<TicketPublic>(`/api/public/locations/${encodeURIComponent(code)}/tickets`, {
      method: 'POST',
      body,
    }),

  lookup: (code: string, phone: string) =>
    request<TicketPublic>(`/api/public/locations/${encodeURIComponent(code)}/lookup`, {
      method: 'POST',
      body: { phone },
    }),

  ticket: (token: string, signal?: AbortSignal) =>
    request<TicketPublic>(`/api/public/tickets/${encodeURIComponent(token)}`, { signal }),

  cancelTicket: (token: string) =>
    request<TicketPublic>(`/api/public/tickets/${encodeURIComponent(token)}/cancel`, {
      method: 'POST',
    }),

  hostQueue: (token: string, signal?: AbortSignal) =>
    request<HostQueue>('/api/host/queue', { token, signal }),

  hostAction: (token: string, ticketId: number, action: HostAction) =>
    request<HostRow>(`/api/host/tickets/${ticketId}/${action}`, { method: 'POST', token }),
}
