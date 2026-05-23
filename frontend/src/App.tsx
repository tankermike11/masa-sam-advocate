import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import WelcomePage from './pages/WelcomePage'
import CasePage from './pages/CasePage'
import ScenariosPage from './pages/ScenariosPage'
import AdminQueuePage from './pages/AdminQueuePage'
import AdminCaseDetailPage from './pages/AdminCaseDetailPage'
import './styles/brand.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"                     element={<WelcomePage />} />
        <Route path="/case"                 element={<CasePage />} />
        <Route path="/scenarios"            element={<ScenariosPage />} />
        <Route path="/admin"                element={<AdminQueuePage />} />
        <Route path="/admin/cases/:caseId"  element={<AdminCaseDetailPage />} />
        <Route path="*"                     element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
