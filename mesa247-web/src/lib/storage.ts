// localStorage puede lanzar en incógnito o con cookies bloqueadas: nunca debe
// tumbar la pantalla, así que todo acceso va envuelto.

export const storageKeys = {
  requestId: (code: string) => `mesa247:request:${code}`,
  ticketToken: (code: string) => `mesa247:ticket:${code}`,
  lastCode: 'mesa247:last-code',
  hostToken: 'mesa247:host-token',
}

export function readLocal(key: string): string | null {
  try {
    return window.localStorage.getItem(key)
  } catch {
    return null
  }
}

export function writeLocal(key: string, value: string): void {
  try {
    window.localStorage.setItem(key, value)
  } catch {
    // Sin almacenamiento el flujo sigue: se pierde la idempotencia del reintento.
  }
}

export function removeLocal(key: string): void {
  try {
    window.localStorage.removeItem(key)
  } catch {
    // Igual que arriba: no es un error que el comensal deba ver.
  }
}

/**
 * uuid v4 para `request_id`. `crypto.randomUUID` solo existe en contextos
 * seguros; el respaldo basta porque esto es una llave de idempotencia, no una
 * credencial (el token del turno lo genera el servidor).
 */
export function uuid(): string {
  const webCrypto: Crypto | undefined = globalThis.crypto
  if (webCrypto?.randomUUID) return webCrypto.randomUUID()
  const bytes = new Uint8Array(16)
  if (webCrypto?.getRandomValues) webCrypto.getRandomValues(bytes)
  else for (let index = 0; index < bytes.length; index += 1) bytes[index] = Math.floor(Math.random() * 256)
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
