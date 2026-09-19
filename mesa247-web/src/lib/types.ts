// Contrato público de la API (09 § 5). Si cambia el backend, cambia aquí primero.

export type TicketStatus =
  | 'waiting' | 'called' | 'seated' | 'cancelled' | 'no_show' | 'removed' | 'expired'

export type NotifyState = 'none' | 'sent' | 'failed'

export type LocationPublic = {
  code: string
  name: string
  country: string
  phone_prefix: string
  max_party_size: number
}

export type TicketPublic = {
  token: string
  location_name: string
  name: string
  party_size: number
  status: TicketStatus
  groups_ahead: number | null
  eta_min: number | null
  joined_at: string
  called_at: string | null
  deadline_at: string | null
  server_now: string
}

export type HostRow = {
  id: number
  name: string
  party_size: number
  status: TicketStatus
  waiting_min: number
  called_at: string | null
  deadline_at: string | null
  on_the_way: boolean
  overdue: boolean
  notify_state: NotifyState
}

export type HostQueue = {
  location: { name: string; timezone: string }
  service_date: string
  waiting_count: number
  avg_wait_min: number | null
  server_now: string
  rows: HostRow[]
}

/** Reporte del día (04 § 6). Los conteos son de grupos; `*_guests` suma personas. */
export type HostReport = {
  location: { name: string; timezone: string }
  service_date: string
  joined: number
  seated: number
  left_before_seating: number
  no_show: number
  /** Turnos aún sin desenlace: mientras sean > 0 el día no ha cerrado. */
  pending: number
  /** De los cerrados, los que cerró el sistema y no una persona. */
  expired: number
  joined_guests: number
  seated_guests: number
  avg_wait_min: number | null
  server_now: string
}

export type HostAction = 'call' | 'seat' | 'no-show' | 'leave' | 'remove'

const TERMINAL: TicketStatus[] = ['seated', 'cancelled', 'no_show', 'removed', 'expired']

/** Un turno terminal ya no cambia: se deja de consultar al servidor. */
export function isTerminal(status: TicketStatus): boolean {
  return TERMINAL.includes(status)
}

/** Atajos de la demo: existen solo mientras `DEMO_MODE` esté encendido. */
export type DemoLocation = {
  code: string
  name: string
  timezone: string
}

export type DemoTablet = {
  token: string
  location_name: string
}
