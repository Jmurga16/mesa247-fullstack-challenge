/**
 * Andamiaje de la prueba, no producto.
 *
 * A `/q/{code}` se llega escaneando el QR de la puerta, y la tablet se abre una
 * vez con el enlace de su local. Ninguna de las dos cosas se puede enseñar en
 * una demo: no hay cámara, y quien prueba la aplicación no tiene por qué
 * manejar tokens. Estos atajos los sustituyen, y viven detrás de `DEMO_MODE`
 * en el backend: apagado, desaparecen y el producto sigue entero.
 */
import type { DemoLocation, DemoTablet } from './types'

/** La lista sale de la base, así que nunca ofrece un local que no existe. */
export async function demoLocations(signal?: AbortSignal): Promise<DemoLocation[]> {
  const response = await fetch('/api/demo/locations', { signal })
  if (!response.ok) return []
  return (await response.json()) as DemoLocation[]
}

export async function openDemoTablet(code: string): Promise<DemoTablet> {
  const response = await fetch(`/api/demo/locations/${encodeURIComponent(code)}/tablet`, {
    method: 'POST',
  })
  if (!response.ok) throw new Error('demo_tablet_failed')
  return (await response.json()) as DemoTablet
}

/** Etiqueta de ciudad para el selector; sale de la zona horaria del local. */
export function cityOf(timezone: string): string {
  return (timezone.split('/')[1] ?? timezone).replace(/_/g, ' ')
}
