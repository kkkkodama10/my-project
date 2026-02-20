import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { get } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import AdminLoginPage from './AdminLoginPage'
import QuestionForm from '../components/QuestionForm'
import QuestionList from '../components/QuestionList'

export default function AdminQuestionsPage() {
  const { isAdmin } = useAuth()
  if (!isAdmin) return <AdminLoginPage />
  return <QuestionsContent />
}

function QuestionsContent() {
  const [questions, setQuestions] = useState([])
  const [editTarget, setEditTarget] = useState(null) // null = 新規, question obj = 編集
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState('')

  async function loadQuestions() {
    try {
      const res = await get('/api/admin/questions')
      if (!res.ok) throw new Error('fetch failed')
      setQuestions(await res.json())
    } catch (e) {
      setError('問題一覧取得失敗: ' + e.message)
    }
  }

  useEffect(() => {
    loadQuestions()
  }, [])

  function handleEdit(question) {
    setEditTarget(question)
    setShowForm(true)
  }

  function handleNewQuestion() {
    setEditTarget(null)
    setShowForm(true)
  }

  function handleSaved(savedQuestion) {
    setShowForm(false)
    setEditTarget(null)
    // 一覧を再取得
    loadQuestions()
  }

  function handleCancel() {
    setShowForm(false)
    setEditTarget(null)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <h1>問題管理</h1>
        <Link to="/admin">← ダッシュボードへ</Link>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {showForm && (
        <QuestionForm
          initial={editTarget}
          onSaved={handleSaved}
          onCancel={handleCancel}
        />
      )}

      {!showForm && (
        <button onClick={handleNewQuestion} style={{ marginBottom: 12 }}>
          + 新規問題
        </button>
      )}

      <div>
        <p style={{ color: '#555', fontSize: '0.9em', margin: '0 0 8px' }}>
          ドラッグ&ドロップで並び替え可能です
        </p>
        <QuestionList
          questions={questions}
          onQuestionsChange={setQuestions}
          onEdit={handleEdit}
        />
        {questions.length === 0 && !error && (
          <p style={{ color: '#888' }}>問題がありません。新規作成してください。</p>
        )}
      </div>
    </div>
  )
}
