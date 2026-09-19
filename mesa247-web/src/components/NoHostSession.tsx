import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Props = {
  children: ReactNode
  /** Solo la cola ofrece descartar un token guardado que ya no sirve. */
  onForget?: () => void
}

/**
 * La misma salida para la cola y para el reporte: sin sesión de tablet no se
 * enseña nada del local, y la única puerta es volver a abrirla.
 */
export default function NoHostSession({ children, onForget }: Props) {
  return (
    <main className="screen screen-wide">
      <section className="card">
        <h1>Esta tablet no tiene sesión</h1>
        {children}
        <Link className="button button-primary" to="/admin">
          Abrir la tablet de un local
        </Link>
        {onForget && (
          <button type="button" className="button button-secondary" onClick={onForget}>
            Olvidar el token guardado
          </button>
        )}
      </section>
    </main>
  )
}
