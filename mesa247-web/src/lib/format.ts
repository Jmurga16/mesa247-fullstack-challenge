const HOUR = new Intl.DateTimeFormat('es-PE', { hour: '2-digit', minute: '2-digit', hour12: false })
const WEEKDAY = new Intl.DateTimeFormat('es-PE', { weekday: 'long' })
const LONG_DATE = new Intl.DateTimeFormat('es-PE', { weekday: 'long', day: 'numeric', month: 'long' })

/** Hora local del navegador; el comensal y el anfitrión están en el local. */
export function clockTime(iso: string | null): string {
  if (!iso) return ''
  return HOUR.format(new Date(iso))
}

/** `service_date` llega como AAAA-MM-DD: se arma en local para no correr un día. */
export function weekdayOf(serviceDate: string): string {
  const [year, month, day] = serviceDate.split('-').map(Number)
  return WEEKDAY.format(new Date(year, month - 1, day))
}

/**
 * Desfase entre el reloj del servidor y el del dispositivo. La cuenta regresiva
 * del llamado no puede depender de la hora del celular.
 */
/** «Viernes 11 de septiembre»: el encabezado del reporte del día. */
export function longDateOf(serviceDate: string): string {
  const [year, month, day] = serviceDate.split('-').map(Number)
  const text = LONG_DATE.format(new Date(year, month - 1, day)).replace(',', '')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export function clockSkewMs(serverNow: string): number {
  return Date.parse(serverNow) - Date.now()
}

export function minutesLeft(deadline: string, skewMs: number): number {
  return Math.ceil((Date.parse(deadline) - (Date.now() + skewMs)) / 60000)
}

export function partyLabel(size: number): string {
  return size === 1 ? '1 persona' : `${size} personas`
}

export function waitLabel(minutes: number): string {
  if (minutes < 1) return 'menos de 1 min'
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`
}

export function aheadLabel(groupsAhead: number): string {
  if (groupsAhead === 0) return 'Eres el siguiente'
  if (groupsAhead === 1) return 'Hay 1 grupo antes que tú'
  return `Hay ${groupsAhead} grupos antes que tú`
}
