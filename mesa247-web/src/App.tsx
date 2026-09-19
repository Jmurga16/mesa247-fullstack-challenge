import { Suspense, lazy } from 'react'
import { Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage'
import JoinPage from './pages/JoinPage'
import NotFoundPage from './pages/NotFoundPage'
import RecoverPage from './pages/RecoverPage'
import TicketPage from './pages/TicketPage'

// Nadie carga la operación desde el celular del comensal: va en chunks aparte.
const AdminPage = lazy(() => import('./pages/AdminPage'))
const HostPage = lazy(() => import('./pages/HostPage'))

function Loading() {
  return (
    <main className="screen screen-narrow">
      <p className="muted" role="status">Cargando…</p>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/q/:code" element={<JoinPage />} />
      <Route path="/q/:code/mi-turno" element={<RecoverPage />} />
      <Route path="/t/:token" element={<TicketPage />} />
      <Route path="/admin" element={<Suspense fallback={<Loading />}><AdminPage /></Suspense>} />
      <Route path="/host" element={<Suspense fallback={<Loading />}><HostPage /></Suspense>} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
