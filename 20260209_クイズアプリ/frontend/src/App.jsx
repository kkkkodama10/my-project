import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import JoinPage from './pages/JoinPage'
import QuizPage from './pages/QuizPage'
import ResultsPage from './pages/ResultsPage'
import AdminDashboard from './pages/AdminDashboard'
import AdminQuestionsPage from './pages/AdminQuestionsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<JoinPage />} />
          <Route path="/quiz/:eventId" element={<QuizPage />} />
          <Route path="/results/:eventId" element={<ResultsPage />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/questions" element={<AdminQuestionsPage />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
