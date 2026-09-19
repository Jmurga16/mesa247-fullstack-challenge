import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <main className="screen screen-narrow">
      <section className="card">
        <h1>Esta página no existe</h1>
        <p>
          Si buscas tu turno, vuelve al QR del local y usa «Ya estoy en la lista de espera».
        </p>
        <Link className="button button-secondary button-block" to="/">Ir al inicio</Link>
      </section>
    </main>
  )
}
