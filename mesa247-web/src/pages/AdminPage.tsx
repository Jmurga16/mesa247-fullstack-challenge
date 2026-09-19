import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cityOf, demoLocations, openDemoTablet } from '../lib/demo'
import { readLocal, storageKeys, writeLocal } from '../lib/storage'
import type { DemoLocation } from '../lib/types'

/**
 * Back office: solo la tablet del anfitrión.
 *
 * A la lista de espera no se entra desde aquí. La abre el comensal escaneando
 * el QR de la puerta, y esa es la parte que el piloto tiene que demostrar; un
 * atajo para probarla vive en `/`, no en administración.
 *
 * Lo de esta pantalla es el otro atajo: abrir la tablet de un local sin copiar
 * el token de la consola. Quien prueba la aplicación no tiene por qué manejar
 * credenciales, y encadenar locales desde un mismo equipo es un clic.
 */
export default function AdminPage() {
  const navigate = useNavigate()
  const [locations, setLocations] = useState<DemoLocation[] | null>(null)
  const [opening, setOpening] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const hasTablet = Boolean(readLocal(storageKeys.hostToken))

  useEffect(() => {
    const controller = new AbortController()
    demoLocations(controller.signal)
      .then((rows) => !controller.signal.aborted && setLocations(rows))
      .catch(() => !controller.signal.aborted && setLocations([]))
    return () => controller.abort()
  }, [])

  const open = async (location: DemoLocation) => {
    if (opening) return
    setOpening(location.code)
    setError(null)
    try {
      const tablet = await openDemoTablet(location.code)
      // Misma puerta que el enlace del seed: el token queda guardado en el
      // dispositivo y la sesión se abre desde ahí.
      writeLocal(storageKeys.hostToken, tablet.token)
      navigate('/host')
    } catch {
      setError('No pudimos abrir esa tablet. Revisa que la API esté levantada.')
      setOpening(null)
    }
  }

  return (
    <main className="screen screen-narrow">
      <section className="card">
        <header className="card-header">
          <p className="eyebrow">Operación</p>
          <h1>La tablet del anfitrión</h1>
        </header>

        <p>
          La tablet se abre una vez con el enlace de su local, que incluye el token del dispositivo.
          Queda guardado en la tablet y desaparece de la barra de direcciones.
        </p>

        {hasTablet && (
          <button
            type="button"
            className="button button-primary button-block"
            onClick={() => navigate('/host')}
          >
            Volver a la cola de esta tablet
          </button>
        )}

        <div className="demo-box">
          <p className="eyebrow">Atajo de la prueba</p>
          <p className="muted">
            Aquí no hay tablets repartidas ni tokens que copiar. Elige un local y entra como si
            hubieras abierto su enlace; al elegir otro, cambias de tablet.
          </p>

          {locations === null && <p className="muted" role="status">Buscando locales…</p>}

          {locations !== null && locations.length === 0 && (
            <p className="banner banner-warn" role="alert">
              No hay locales disponibles. Levanta la API y ejecuta <code>python seed.py</code>. Si
              el modo demo está apagado (<code>DEMO_MODE=false</code>), abre la tablet con su enlace{' '}
              <code>/host?token=…</code>.
            </p>
          )}

          {error && <p className="banner banner-warn" role="alert">{error}</p>}

          <ul className="demo-list">
            {locations?.map((location) => (
              <li key={location.code}>
                <div>
                  <p className="demo-name">{location.name}</p>
                  <p className="muted">{cityOf(location.timezone)}</p>
                </div>
                <button
                  type="button"
                  className="button button-secondary"
                  onClick={() => open(location)}
                  disabled={opening !== null}
                >
                  {opening === location.code ? 'Abriendo…' : 'Abrir su tablet'}
                </button>
              </li>
            ))}
          </ul>
        </div>

        <p className="muted">
          El comensal no pasa por aquí: entra escaneando el QR de la puerta, que lleva a la lista de
          su local.
        </p>
      </section>
    </main>
  )
}
