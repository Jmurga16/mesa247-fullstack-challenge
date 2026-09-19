/**
 * El número se escribe completo, con su código de país. El local solo aporta el
 * prefijo con el que se rellena el campo: quien llega con un número extranjero
 * lo cambia y el servidor lo valida igual (parse de E.164 por encima de la
 * región del local).
 */

export const PHONE_HINT = 'Con el código de país. Si tu número es de otro país, cámbialo (+34, +1, +56…).'

export const PHONE_INVALID = 'Escribe tu número con el código de país, por ejemplo +51 987 654 321.'

/** Se acepta lo que se teclea de verdad: dígitos, espacios, guiones y paréntesis. */
export function sanitizePhoneInput(value: string): string {
  const cleaned = value.replace(/[^\d+\s().-]/g, '')
  // Un solo «+», y solo al principio.
  const plus = cleaned.trimStart().startsWith('+')
  return (plus ? '+' : '') + cleaned.replace(/\+/g, '').replace(/^\s+/, '')
}

export function phoneDigits(value: string): string {
  return value.replace(/\D/g, '')
}

/**
 * Comprobación local antes de gastar una petición: E.164 admite hasta 15
 * dígitos y ningún país baja de 8 contando el código. Quién es válido de verdad
 * lo decide el servidor con la librería de numeración.
 */
export function looksLikePhone(value: string): boolean {
  const digits = phoneDigits(value)
  return digits.length >= 8 && digits.length <= 15
}

/** Placeholder coherente con el prefijo del local, sin inventar el resto. */
export function phonePlaceholder(prefix: string): string {
  return `${prefix} 987 654 321`
}
