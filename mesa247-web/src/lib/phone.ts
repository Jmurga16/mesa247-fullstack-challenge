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
  // Un «+» escrito después del principio empieza un número nuevo: es lo que hace
  // quien teclea el suyo entero encima del prefijo que ya traía el campo. Antes se
  // borraba ese «+» y se conservaban sus dígitos, así que el código de país quedaba
  // duplicado sin que se notara y el servidor rechazaba un número correcto.
  const start = cleaned.lastIndexOf('+')
  const rest = (start === -1 ? cleaned : cleaned.slice(start + 1)).replace(/\+/g, '')
  return (start === -1 ? '' : '+') + rest.replace(/^\s+/, '')
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

/** El código de país del local escrito dos veces: el del campo más el tecleado. */
function repeatsCountryCode(value: string, prefix: string): boolean {
  const code = phoneDigits(prefix)
  return code.length > 0 && phoneDigits(value).startsWith(code + code)
}

/**
 * El 422 del servidor es el mismo para cualquier número inválido. Cuando además
 * el código de país aparece dos veces, se dice eso: el número ya está rechazado,
 * así que nombrarlo no bloquea a nadie y ahorra adivinar qué sobra.
 */
export function explainPhoneError(
  fields: Record<string, string>,
  value: string,
  prefix: string,
): Record<string, string> {
  if (!fields.phone || !repeatsCountryCode(value, prefix)) return fields
  return { ...fields, phone: `El código de país ${prefix} está dos veces. Déjalo una sola.` }
}
