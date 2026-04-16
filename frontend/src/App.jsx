import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Tenders from './pages/Tenders'
import TenderDetail from './pages/TenderDetail'
import Bidders from './pages/Bidders'
import Evaluations from './pages/Evaluations'
import AuditLog from './pages/AuditLog'
import ToastContainer from './components/ToastContainer'

export default function App() {
  const [toasts, setToasts] = useState([])

  const addToast = (message, type = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard addToast={addToast} />} />
          <Route path="/tenders" element={<Tenders addToast={addToast} />} />
          <Route path="/tenders/:id" element={<TenderDetail addToast={addToast} />} />
          <Route path="/bidders" element={<Bidders addToast={addToast} />} />
          <Route path="/evaluations" element={<Evaluations addToast={addToast} />} />
          <Route path="/evaluations/:tenderId" element={<Evaluations addToast={addToast} />} />
          <Route path="/audit" element={<AuditLog addToast={addToast} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <ToastContainer toasts={toasts} />
    </div>
  )
}
