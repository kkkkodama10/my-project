import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import PersonListPage from './pages/PersonListPage'
import PersonDetailPage from './pages/PersonDetailPage'
import ComparePage from './pages/ComparePage'
import HistoryPage from './pages/HistoryPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<PersonListPage />} />
        <Route path="/persons/:id" element={<PersonDetailPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
    </Routes>
  )
}
