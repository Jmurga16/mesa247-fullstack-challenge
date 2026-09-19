import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { DEMO_LOCATIONS } from '../lib/demo'
import type { DemoLocation } from '../lib/demo'

type Option = DemoLocation & { available: boolean }

/**
 * Entrada del producto. A la lista se llega por el QR de la puerta, así que lo
 * único que hay aquí además del mensaje es el atajo de la prueba: elegir un
 * local y entrar por donde entraría ese QR. Son dos puertas, no una: quien ya
 * está esperando no tiene por qué volver a la puerta del local (07 § 3.1 P3).
 */
export default function HomePage() {
  const navigate = useNavigate()
  const [options, setOptions] = useState<Option[] | null>(null)
  const [chosen, setChosen] = useState('')

  useEffect(() => {
    const controller = new AbortController()
    Promise.all(
      DEMO_LOCATIONS.map(async (demo): Promise<Option> => {
        try {
          const info = await api.location(demo.code, controller.signal)
          return { ...demo, name: info.name, available: true }
        } catch {
          return { ...demo, available: false }
        }
      }),
    ).then((rows) => {
      if (controller.signal.aborted) return
      setOptions(rows)
      setChosen(rows.find((row) => row.available)?.code ?? '')
    })
    return () => controller.abort()
  }, [])

  const available = options?.filter((option) => option.available) ?? []

  return (
    <main className="screen screen-narrow">
      <section className="card">
        <header className="card-header">
          <p className="eyebrow">Lista de espera</p>
          <h1>Mesa247</h1>
        </header>

        <p>
          Espera tu mesa desde el celular, sin dejar tu nombre en un cuaderno ni volver a la puerta
          a preguntar cuánto falta.
        </p>

        <p className="notice">
          Escanea el código QR de la entrada del local para unirte a la lista.
        </p>

        <p className="muted">
          ¿Ya te uniste y cerraste la página? No vuelvas a la puerta: en la lista del local, «Ya
          estoy en la lista de espera» te devuelve tu turno con tu teléfono.
        </p>

        <div className="demo-box">
          <p className="eyebrow">Atajo de la prueba</p>
          <p className="muted">
            Aquí no hay cámara. Elige un local y entra por donde entrarías con su QR: a unirte, o a
            recuperar tu turno con tu teléfono.
          </p>

          {options === null && <p className="muted" role="status">Buscando locales…</p>}

          {options !== null && available.length === 0 && (
            <p className="banner banner-warn" role="alert">
              Ningún local responde. Levanta la API y ejecuta <code>python seed.py</code>.
            </p>
          )}

          {options !== null && available.length > 0 && (
            <form
              onSubmit={(event) => {
                event.preventDefault()
                if (chosen) navigate(`/q/${chosen}`)
              }}
            >
              <div className="field">
                <label htmlFor="demo-location">Local</label>
                <select
                  id="demo-location"
                  value={chosen}
                  onChange={(event) => setChosen(event.target.value)}
                >
                  {options.map((option) => (
                    <option key={option.code} value={option.code} disabled={!option.available}>
                      {option.name} · {option.city}
                      {option.available ? '' : ' (no disponible)'}
                    </option>
                  ))}
                </select>
              </div>
              <div className="demo-actions">
                <button type="submit" className="button button-primary button-block">
                  Unirme a la lista
                </button>
                <button
                  type="button"
                  className="button button-secondary button-block"
                  onClick={() => chosen && navigate(`/q/${chosen}/mi-turno`)}
                >
                  Ya estoy en la lista
                </button>
              </div>
            </form>
          )}
        </div>
      </section>
    </main>
  )
}
