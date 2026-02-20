import { useState, useEffect, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import { post, get } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import AdminLoginPage from './AdminLoginPage'

const EVENT_ID = 'demo'

// ── フェーズ状態機械 ──────────────────────────────────
// backend state: waiting / running / finished / aborted
// frontend phase: waiting / started / question_shown / question_closed / question_revealed / finished / aborted

const BUTTON_STATES = {
  waiting:           { start: true,  next: false, close: false, reveal: false, finish: false, abort: false, reset: false },
  started:           { start: false, next: true,  close: false, reveal: false, finish: true,  abort: true,  reset: true  },
  question_shown:    { start: false, next: false, close: true,  reveal: false, finish: true,  abort: true,  reset: true  },
  question_closed:   { start: false, next: false, close: false, reveal: true,  finish: true,  abort: true,  reset: true  },
  question_revealed: { start: false, next: true,  close: false, reveal: false, finish: true,  abort: true,  reset: true  },
  finished:          { start: false, next: false, close: false, reveal: false, finish: false, abort: false, reset: true  },
  aborted:           { start: false, next: false, close: false, reveal: false, finish: false, abort: false, reset: true  },
}

// ── ログからフェーズを推定 ───────────────────────────
function inferFromLogs(logs) {
  const relevant = ['start', 'next', 'close', 'reveal', 'finish', 'abort', 'reset']
  const last = logs.find(l => relevant.includes(l.action))
  if (!last) return { phase: 'waiting', questionId: null }

  const qid = last.payload?.question_id || null

  switch (last.action) {
    case 'start':  return { phase: 'started',           questionId: null }
    case 'next':
      if (last.payload?.state === 'finished') return { phase: 'finished', questionId: null }
      return { phase: 'question_shown', questionId: qid }
    case 'close':  return { phase: 'question_closed',   questionId: qid }
    case 'reveal': return { phase: 'question_revealed', questionId: qid }
    case 'finish': return { phase: 'finished',          questionId: null }
    case 'abort':  return { phase: 'aborted',           questionId: null }
    case 'reset':  return { phase: 'waiting',           questionId: null }
    default:       return { phase: 'waiting',           questionId: null }
  }
}

export default function AdminDashboard() {
  const { isAdmin, checking } = useAuth()
  if (checking) return null  // セッション確認中はブランク（ちらつき防止）
  if (!isAdmin) return <AdminLoginPage />
  return <Dashboard />
}

function Dashboard() {
  const { logout } = useAuth()
  const [phase, setPhase] = useState('waiting')
  const [currentQuestionId, setCurrentQuestionId] = useState(null)
  const [actionStatus, setActionStatus] = useState('')
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)  // 初期ロード中はボタン全無効

  const [selectedMode, setSelectedMode] = useState('manual') // Start 前に選ぶ
  const [autoMode, setAutoMode] = useState(false)             // Start 後に確定
  const [autoTimes, setAutoTimes] = useState({ thinking: 2, close: 3, reveal: 2 })
  const [countdown, setCountdown] = useState(null)            // { label, sec } | null

  const autoTimerRef    = useRef(null)  // (将来拡張用 setTimeout id)
  const countdownRef    = useRef(null)  // setInterval id
  const handleNextRef   = useRef(null)  // stale closure 回避
  const handleCloseRef  = useRef(null)
  const handleRevealRef = useRef(null)
  const serverDeadlineRef = useRef(null) // handleNext が返す deadline_at

  const btns = loading
    ? {}
    : autoMode
      ? { ...(BUTTON_STATES[phase] || BUTTON_STATES.waiting), next: false, close: false, reveal: false }
      : (BUTTON_STATES[phase] || BUTTON_STATES.waiting)

  const clearAuto = useCallback(() => {
    clearTimeout(autoTimerRef.current)
    clearInterval(countdownRef.current)
    autoTimerRef.current = countdownRef.current = null
    setCountdown(null)
  }, [])

  const scheduleStep = useCallback((label, sec, onDone) => {
    clearAuto()
    let rem = sec
    setCountdown({ label, sec: rem })
    countdownRef.current = setInterval(() => {
      rem -= 1
      if (rem <= 0) {
        clearInterval(countdownRef.current)
        countdownRef.current = null
        setCountdown(null)
        onDone()
      } else {
        setCountdown({ label, sec: rem })
      }
    }, 1000)
  }, [clearAuto])

  const fetchLogs = useCallback(async () => {
    try {
      const res = await get('/api/admin/logs?limit=200')
      if (!res.ok) return
      const data = await res.json()
      setLogs(data)
      return data
    } catch (e) {
      console.debug('fetchLogs error', e)
    }
  }, [])

  // 初回マウント時にログからフェーズを復元
  useEffect(() => {
    fetchLogs().then(data => {
      if (data) {
        const { phase: inferred, questionId } = inferFromLogs(data)
        setPhase(inferred)
        if (questionId) setCurrentQuestionId(questionId)
      }
      setLoading(false)
    })
  }, [fetchLogs])

  // オート進行 useEffect
  useEffect(() => {
    if (!autoMode) return
    if (phase === 'started')
      scheduleStep('シンキングタイム', autoTimes.thinking, () => handleNextRef.current?.())
    else if (phase === 'question_shown') {
      // サーバーのdeadline_atに合わせてCloseをスケジュール（+1秒バッファ）
      let sec = 15 // fallback
      if (serverDeadlineRef.current) {
        const remaining = Math.round((new Date(serverDeadlineRef.current) - Date.now()) / 1000)
        sec = Math.max(1, remaining + 1)
      }
      scheduleStep('回答締切まで', sec, () => handleCloseRef.current?.())
    }
    else if (phase === 'question_closed')
      scheduleStep('締め切り待機', autoTimes.close, () => handleRevealRef.current?.())
    else if (phase === 'question_revealed')
      scheduleStep('解答表示', autoTimes.reveal, () => handleNextRef.current?.())
    else if (phase === 'finished' || phase === 'aborted') {
      clearAuto()
      setAutoMode(false)
    }
  }, [phase, autoMode, scheduleStep, clearAuto, autoTimes.thinking, autoTimes.close, autoTimes.reveal])

  // アンマウント時クリーンアップ
  useEffect(() => () => clearAuto(), [clearAuto])

  async function action(path) {
    try {
      const res = await post(path)
      const data = await res.json()
      setActionStatus(JSON.stringify(data))
      fetchLogs()
      return data
    } catch (e) {
      setActionStatus('error: ' + e.message)
      return null
    }
  }

  async function handleStart() {
    const data = await action(`/api/admin/events/${EVENT_ID}/start`)
    if (data?.status === 'ok') {
      setPhase('started')
      if (selectedMode === 'auto') setAutoMode(true)
    }
  }

  async function handleNext() {
    const data = await action(`/api/admin/events/${EVENT_ID}/questions/next`)
    if (data) {
      if (data.state === 'finished') {
        setPhase('finished')
      } else if (data.question_id) {
        serverDeadlineRef.current = data.deadline_at || null
        setCurrentQuestionId(data.question_id)
        setPhase('question_shown')
      }
    }
  }

  async function handleClose() {
    if (!currentQuestionId) return
    const data = await action(`/api/admin/events/${EVENT_ID}/questions/${encodeURIComponent(currentQuestionId)}/close`)
    if (data?.status === 'ok') setPhase('question_closed')
  }

  async function handleReveal() {
    if (!currentQuestionId) return
    const data = await action(`/api/admin/events/${EVENT_ID}/questions/${encodeURIComponent(currentQuestionId)}/reveal`)
    if (data?.status === 'ok') setPhase('question_revealed')
  }

  async function handleFinish() {
    const data = await action(`/api/admin/events/${EVENT_ID}/finish`)
    if (data?.status === 'ok') setPhase('finished')
  }

  async function handleAbort() {
    clearAuto()
    setAutoMode(false)
    const data = await action(`/api/admin/events/${EVENT_ID}/abort`)
    if (data?.status === 'ok') setPhase('aborted')
  }

  async function handleReset() {
    clearAuto()
    setAutoMode(false)
    const data = await action(`/api/admin/events/${EVENT_ID}/reset`)
    if (data?.status === 'ok') {
      setPhase('waiting')
      setCurrentQuestionId(null)
    }
  }

  // handler ref を毎レンダーで最新化
  handleNextRef.current   = handleNext
  handleCloseRef.current  = handleClose
  handleRevealRef.current = handleReveal

  const csvUrl = `/api/events/${EVENT_ID}/results/csv`

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1>管理ダッシュボード</h1>
        <div style={{ display: 'flex', gap: 12 }}>
          <Link to="/admin/questions">問題管理</Link>
          <button onClick={logout} style={{ fontSize: '0.85em' }}>ログアウト</button>
        </div>
      </div>

      <p style={{ color: '#555', margin: '4px 0 12px' }}>
        フェーズ: <strong>{loading ? '読み込み中...' : phase}</strong>
        {autoMode && <span style={{ marginLeft: 6, color: '#0ea5e9', fontWeight: 'bold', fontSize: '0.9em' }}>[オート]</span>}
        {currentQuestionId && (
          <span style={{ marginLeft: 8, color: '#888', fontSize: '0.9em' }}>
            問題ID: {currentQuestionId}
          </span>
        )}
      </p>

      {/* オート進行中カウントダウンバナー */}
      {autoMode && (
        <div style={{
          background: '#e0f2fe',
          border: '1px solid #7dd3fc',
          borderRadius: 6,
          padding: '8px 14px',
          marginBottom: 10,
          color: '#0369a1',
          fontWeight: 'bold',
          fontSize: '0.95em',
        }}>
          {countdown
            ? `オート進行中 — ${countdown.label}: ${countdown.sec}秒`
            : 'オート進行中...'}
        </div>
      )}

      {/* waiting フェーズ中のモード選択パネル */}
      {phase === 'waiting' && !loading && (
        <div style={{
          border: '1px solid #ddd',
          borderRadius: 6,
          padding: '10px 14px',
          marginBottom: 12,
          background: '#f9f9f9',
        }}>
          <strong style={{ marginRight: 12 }}>進行モード:</strong>
          <label style={{ marginRight: 16, cursor: 'pointer' }}>
            <input
              type="radio"
              name="mode"
              value="manual"
              checked={selectedMode === 'manual'}
              onChange={() => setSelectedMode('manual')}
              style={{ marginRight: 4 }}
            />
            マニュアル
          </label>
          <label style={{ cursor: 'pointer' }}>
            <input
              type="radio"
              name="mode"
              value="auto"
              checked={selectedMode === 'auto'}
              onChange={() => setSelectedMode('auto')}
              style={{ marginRight: 4 }}
            />
            オート
          </label>

          {selectedMode === 'auto' && (
            <div style={{ marginTop: 10, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center' }}>
              <label style={{ fontSize: '0.9em' }}>
                シンキングタイム (s):&nbsp;
                <input
                  type="number"
                  min={1}
                  value={autoTimes.thinking}
                  onChange={e => setAutoTimes(t => ({ ...t, thinking: Number(e.target.value) }))}
                  style={{ width: 60 }}
                />
              </label>
              <span style={{ fontSize: '0.85em', color: '#888' }}>
                回答時間: サーバー設定 (time_limit_sec) に連動
              </span>
              <label style={{ fontSize: '0.9em' }}>
                締め切り待機 (s):&nbsp;
                <input
                  type="number"
                  min={1}
                  value={autoTimes.close}
                  onChange={e => setAutoTimes(t => ({ ...t, close: Number(e.target.value) }))}
                  style={{ width: 60 }}
                />
              </label>
              <label style={{ fontSize: '0.9em' }}>
                解答表示 (s):&nbsp;
                <input
                  type="number"
                  min={1}
                  value={autoTimes.reveal}
                  onChange={e => setAutoTimes(t => ({ ...t, reveal: Number(e.target.value) }))}
                  style={{ width: 60 }}
                />
              </label>
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
        <button disabled={!btns.start}  onClick={handleStart}>Start</button>
        <button disabled={!btns.next}   onClick={handleNext}>Next Question</button>
        <button disabled={!btns.close}  onClick={handleClose}>Close Question</button>
        <button disabled={!btns.reveal} onClick={handleReveal}>Reveal Answer</button>
        <button disabled={!btns.finish} onClick={handleFinish}>Finish</button>
        <button
          disabled={!btns.abort}
          onClick={handleAbort}
          style={{ background: '#f97316', color: '#fff', border: 'none' }}
        >
          Abort
        </button>
        <button
          disabled={!btns.reset}
          onClick={handleReset}
          style={{ background: '#e55', color: '#fff', border: 'none', marginLeft: 16 }}
        >
          Reset
        </button>
      </div>

      {/* CSV ダウンロード（finished / aborted 時に表示） */}
      {(phase === 'finished' || phase === 'aborted') && (
        <div style={{ marginBottom: 12 }}>
          <a
            href={csvUrl}
            download={`results_${EVENT_ID}.csv`}
            style={{
              display: 'inline-block',
              padding: '5px 12px',
              background: '#22863a',
              color: '#fff',
              borderRadius: 4,
              textDecoration: 'none',
              fontSize: '0.9em',
            }}
          >
            結果 CSV ダウンロード
          </a>
        </div>
      )}

      {actionStatus && (
        <div className="admin-status">{actionStatus}</div>
      )}

      <h3 style={{ marginTop: 16 }}>Action log</h3>
      <div style={{
        background: '#fff',
        border: '1px solid #eee',
        padding: 8,
        maxHeight: 200,
        overflowY: 'auto',
      }}>
        {logs.map((entry, i) => (
          <div key={i} style={{
            borderBottom: '1px solid #f0f0f0',
            padding: '4px 2px',
            fontSize: '0.85em',
            fontFamily: 'monospace',
          }}>
            {entry.ts} {entry.action} {entry.event_id || ''} {JSON.stringify(entry.payload || {})}
          </div>
        ))}
      </div>
    </div>
  )
}
