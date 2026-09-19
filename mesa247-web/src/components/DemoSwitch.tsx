import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { demoLocations } from '../lib/demo'
import { readLocal, storageKeys } from '../lib/storage'

/**
 * Atajo de la prueba, no producto.
 *
 * En la puerta nadie cambia de papel: el comensal trae su celular y el anfitrión
 * su tablet. Quien prueba la aplicación tiene una sola pantalla y necesita las dos
 * mitades a un clic. Vive detrás de `DEMO_MODE`, como el resto del andamiaje:
 * apagado, `/api/demo` no responde y el conmutador no se dibuja.
 *
 * El lado del anfitrión lleva a su cola si esta pantalla ya abrió una tablet, y a
 * elegir local si todavía no.
 */
export default function DemoSwitch() {
  const { pathname } = useLocation()
  const [available, setAvailable] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    demoLocations(controller.signal)
      .then((rows) => !controller.signal.aborted && setAvailable(rows.length > 0))
      .catch(() => undefined)
    return () => controller.abort()
  }, [])

  if (!available) return null

  const onHostSide = pathname === '/admin' || pathname.startsWith('/host')
  const hostHref = readLocal(storageKeys.hostToken) ? '/host' : '/admin'

  return (
    <nav className="demo-switch" aria-label="Atajo de la prueba: cambiar de papel">
      <span className="demo-switch-tag">demo</span>
      <Link
        className={`demo-switch-side${onHostSide ? '' : ' is-current'}`}
        aria-current={onHostSide ? undefined : 'page'}
        to="/"
      >
        Comensal
      </Link>
      <Link
        className={`demo-switch-side${onHostSide ? ' is-current' : ''}`}
        aria-current={onHostSide ? 'page' : undefined}
        to={hostHref}
      >
        Anfitrión
      </Link>
    </nav>
  )
}
