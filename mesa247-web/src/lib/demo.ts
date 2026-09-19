/**
 * Los locales del piloto, para el atajo de la prueba de `/`.
 *
 * En producción esto no existe: a `/q/{code}` se llega escaneando el QR pegado
 * en la puerta, y nadie elige un restaurante de una lista. La pantalla comprueba
 * cada código contra la API, así que un local que no esté sembrado o que esté
 * cerrado aparece como no disponible en vez de llevar a una pantalla muerta.
 */
export type DemoLocation = {
  code: string
  name: string
  city: string
}

export const DEMO_LOCATIONS: DemoLocation[] = [
  { code: 'terraza-lima', name: 'La Terraza Azul', city: 'Lima' },
  { code: 'vientos-lima', name: 'Cuatro Vientos', city: 'Lima' },
  { code: 'casa-santiago', name: 'Casa Mediterránea', city: 'Santiago' },
]
