import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { post, get } from '../api/client'
import Leaderboard from '../components/Leaderboard'

const EVENT_ID = 'demo'

export default function JoinPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(null) // null=確認中 | 'join' | 'register' | 'quiz_finished'
  const [joinCode, setJoinCode] = useState('123456')
  const [displayBase, setDisplayBase] = useState('guest')
  const [joinStatus, setJoinStatus] = useState('')
  const [registerStatus, setRegisterStatus] = useState('')
  const [resultsData, setResultsData] = useState(null)

  // quiz_finished 中: 新クイズ開始を3秒ポーリングで検知
  useEffect(() => {
    if (step !== 'quiz_finished') return
    const id = setInterval(async () => {
      try {
        const res = await get(`/api/events/${EVENT_ID}/me/state`)
        if (!res.ok) return
        const data = await res.json()
        const s = data.event?.state
        if (s && s !== 'finished' && s !== 'aborted') {
          // 新クイズが始まった（waiting or running）→ セッション再確認へ
          navigate('/', { replace: true })
        }
      } catch (_) {}
    }, 3000)
    return () => clearInterval(id)
  }, [step, navigate])

  // マウント時: 既存セッション確認
  useEffect(() => {
    async function checkSession() {
      try {
        const res = await get(`/api/events/${EVENT_ID}/me/state`)
        if (res.ok) {
          const data = await res.json()
          if (data.me?.user_id) {
            // 登録済み → QuizPage へ（QuizPage 側で finished なら Results へ遷移）
            navigate(`/quiz/${EVENT_ID}`, { replace: true })
            return
          }
          // セッションはあるが未登録
          if (data.event?.state === 'finished' || data.event?.state === 'aborted') {
            await loadResults()
            setStep('quiz_finished')
          } else {
            setStep('register')
          }
          return
        }
      } catch (_) { /* 通信エラーは無視 */ }
      // 401 or エラー → 通常の参加フォームへ
      setStep('join')
    }
    checkSession()
  }, [navigate])

  async function handleLogout() {
    try {
      await post(`/api/events/${EVENT_ID}/logout`)
    } catch (_) {}
    // Cookie 削除後に再マウントさせる（step を 'join' に戻す）
    setStep('join')
  }

  async function loadResults() {
    try {
      const rRes = await get(`/api/events/${EVENT_ID}/results`)
      if (rRes.ok) setResultsData(await rRes.json())
    } catch (_) { /* サイレント */ }
  }

  async function handleJoin(e) {
    e.preventDefault()
    setJoinStatus('')
    try {
      const res = await post(`/api/events/${EVENT_ID}/join`, { join_code: joinCode })
      if (!res.ok) throw new Error('join failed')
      const data = await res.json()
      if (data.event?.state === 'finished' || data.event?.state === 'aborted') {
        await loadResults()
        setStep('quiz_finished')
      } else {
        setJoinStatus('参加しました')
        setStep('register')
      }
    } catch (err) {
      setJoinStatus('エラー: ' + err.message)
    }
  }

  async function handleRegister(e) {
    e.preventDefault()
    setRegisterStatus('')
    try {
      const res = await post(`/api/events/${EVENT_ID}/users/register`, {
        display_name_base: displayBase,
      })
      if (res.status === 409) {
        await loadResults()
        setStep('quiz_finished')
        return
      }
      if (!res.ok) throw new Error('register failed')
      const data = await res.json()
      setRegisterStatus('登録完了: ' + data.user.display_name)
      navigate(`/quiz/${EVENT_ID}`)
    } catch (err) {
      setRegisterStatus('エラー: ' + err.message)
    }
  }

  // セッション確認中はブランク表示
  if (step === null) return null

  return (
    <div>
      <h1>Quiz App</h1>

      {step === 'join' && (
        <section>
          <h2>イベントに参加</h2>
          <form onSubmit={handleJoin}>
            <label>
              参加コード:{' '}
              <input
                type="text"
                value={joinCode}
                onChange={e => setJoinCode(e.target.value)}
                required
              />
            </label>
            {' '}
            <button type="submit">参加</button>
            {joinStatus && <span style={{ marginLeft: 8, color: '#006' }}>{joinStatus}</span>}
          </form>
        </section>
      )}

      {step === 'register' && (
        <section>
          <h2>ニックネーム登録</h2>
          <form onSubmit={handleRegister}>
            <label>
              表示名ベース:{' '}
              <input
                type="text"
                value={displayBase}
                onChange={e => setDisplayBase(e.target.value)}
                required
              />
            </label>
            {' '}
            <button type="submit">登録</button>
            {registerStatus && <span style={{ marginLeft: 8 }}>{registerStatus}</span>}
          </form>
        </section>
      )}

      {step === 'quiz_finished' && (
        <section>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
            <p style={{
              fontSize: '1.1em',
              fontWeight: 'bold',
              color: '#555',
              margin: '16px 0',
              padding: '12px 16px',
              background: '#f3f4f6',
              borderRadius: 6,
              border: '1px solid #ddd',
              flex: 1,
            }}>
              クイズは終了しました。次の開始をお待ち下さい。
            </p>
            <button
              onClick={handleLogout}
              style={{ marginTop: 16, fontSize: '0.8em', color: '#888', background: 'none', border: '1px solid #ccc', borderRadius: 4, padding: '2px 8px', cursor: 'pointer', whiteSpace: 'nowrap' }}
            >
              ログアウト
            </button>
          </div>
          {resultsData
            ? (
              <>
                <h2 style={{ marginTop: 24 }}>前回の結果</h2>
                <Leaderboard data={resultsData} />
              </>
            )
            : <p>結果を読み込み中...</p>
          }
        </section>
      )}
    </div>
  )
}
