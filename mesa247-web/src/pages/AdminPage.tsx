import { Link } from 'react-router-dom'
import { readLocal, storageKeys } from '../lib/storage'

/**
 * Back office: solo la tablet del anfitrión.
 *
 * A la lista de espera no se entra desde aquí. La abre el comensal escaneando
 * el QR de la puerta, y esa es la parte que el piloto tiene que demostrar; un
 * atajo para probarla vive en `/`, no en administración.
 */
export default function AdminPage() {
  const hasTablet = Boolean(readLocal(storageKeys.hostToken))

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

        {hasTablet ? (
          <Link className="button button-primary button-block" to="/host">
            Abrir la cola de esta tablet
          </Link>
        ) : (
          <p className="banner banner-info">
            Esta tablet todavía no tiene sesión. Ábrela con su enlace <code>/host?token=…</code>, el
            que imprime el seed del backend.
          </p>
        )}

        <p className="muted">
          El comensal no pasa por aquí: entra escaneando el QR de la puerta, que lleva a la lista de
          su local.
        </p>
      </section>
    </main>
  )
}
