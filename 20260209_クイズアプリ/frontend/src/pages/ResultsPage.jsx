import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { get, post } from '../api/client'
import Leaderboard from '../components/Leaderboard'

export default function ResultsPage() {
  const { eventId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const res = await get(`/api/events/${eventId}/results`)
        if (!res.ok) throw new Error('results fetch failed')
        setData(await res.json())
      } catch (e) {
        setError(e.message)
      }
    }
    load()
  }, [eventId])

  async function handleLogout() {
    try {
      await post(`/api/events/${eventId}/logout`)
    } catch (_) {}
    navigate('/', { replace: true })
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <h1 style={{ margin: 0 }}>結果発表</h1>
        <button
          onClick={handleLogout}
          style={{ fontSize: '0.8em', color: '#888', background: 'none', border: '1px solid #ccc', borderRadius: 4, padding: '2px 8px', cursor: 'pointer' }}
        >
          ログアウト
        </button>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {data ? <Leaderboard data={data} /> : <p>読み込み中...</p>}
    </div>
  )
}
