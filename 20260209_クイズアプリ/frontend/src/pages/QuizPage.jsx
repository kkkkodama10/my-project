import { useEffect, useCallback, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { post } from '../api/client'

const EVENT_ID = 'demo'
import { useWebSocket } from '../hooks/useWebSocket'
import { useEvent, EventProvider } from '../contexts/EventContext'
import ChoiceButton from '../components/ChoiceButton'
import Timer from '../components/Timer'

const POLL_INTERVAL_MS = 3000  // WS切断時のポーリング間隔

function QuizContent() {
  const { eventId } = useParams()
  const navigate = useNavigate()
  const { eventState, currentQuestion, myAnswer, me, fetchState } = useEvent()
  const [wsConnected, setWsConnected] = useState(false)

  // WS URL（プロキシ経由）
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/api/ws?event_id=${eventId}`

  const handleMessage = useCallback((msg) => {
    if (
      msg.type === 'question.shown' ||
      msg.type === 'question.revealed' ||
      msg.type === 'event.state_changed' ||
      msg.type === 'question.closed' ||
      msg.type === 'event.finished'
    ) {
      fetchState(eventId)
    }
  }, [eventId, fetchState])

  useWebSocket(wsUrl, {
    onMessage: handleMessage,
    onOpen:  () => setWsConnected(true),
    onClose: () => setWsConnected(false),
  })

  // T-081: WS切断時はポーリングでフォールバック
  useEffect(() => {
    if (wsConnected) return
    const id = setInterval(() => fetchState(eventId), POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [wsConnected, eventId, fetchState])

  // 初回取得
  useEffect(() => {
    fetchState(eventId)
  }, [eventId, fetchState])

  // finished → 結果ページへ
  useEffect(() => {
    if (eventState?.state === 'finished') {
      navigate(`/results/${eventId}`)
    }
  }, [eventState, eventId, navigate])

  async function handleSwitchUser() {
    try {
      await post(`/api/events/${EVENT_ID}/logout`)
    } catch (_) { /* Cookie 削除できなくても遷移する */ }
    navigate('/', { replace: true })
  }

  async function submitAnswer(choice_index) {
    try {
      const res = await post(
        `/api/events/${eventId}/questions/${encodeURIComponent(currentQuestion.question_id)}/answers`,
        { choice_index }
      )
      if (res.status === 409) return
      await fetchState(eventId)
    } catch (e) {
      console.error('submitAnswer', e)
    }
  }

  // T-082: abort 状態
  if (eventState?.state === 'aborted') {
    return (
      <div>
        <h1>Quiz</h1>
        <div style={{
          marginTop: 24,
          padding: 16,
          background: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: 6,
          color: '#856404',
        }}>
          <strong>イベントが中止されました</strong>
          <p style={{ margin: '8px 0 0' }}>
            管理者によってイベントが中止されました。
          </p>
        </div>
      </div>
    )
  }

  const deadline = eventState?.answer_deadline_at || null
  const now = new Date()
  const deadlinePassed = deadline ? now > new Date(deadline) : false
  const alreadyAnswered = !!myAnswer
  const isRevealed = currentQuestion?.correct_choice_index != null
  const correctIdx = currentQuestion?.correct_choice_index

  function getAnswerStatus() {
    if (isRevealed && myAnswer) {
      return myAnswer.is_correct
        ? { text: '正解!', cls: 'status-correct' }
        : { text: '不正解...', cls: 'status-incorrect' }
    }
    if (isRevealed && !myAnswer) return { text: '未回答', cls: 'status-noanswer' }
    if (deadlinePassed && myAnswer)  return { text: '回答受付終了 — あなたの回答は送信済みです', cls: 'status-closed' }
    if (deadlinePassed && !myAnswer) return { text: '回答受付終了', cls: 'status-closed' }
    if (myAnswer) return { text: '回答済み — 結果発表をお待ちください', cls: '' }
    return null
  }

  const answerStatus = getAnswerStatus()

  return (
    <div>
      <h1>Quiz</h1>

      {/* WS切断インジケータ */}
      {!wsConnected && (
        <div style={{ fontSize: '0.8em', color: '#888', marginBottom: 8 }}>
          ⚠ リアルタイム接続を再試行中... (ポーリングで更新中)
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        {me && <span style={{ color: '#555' }}>参加者: {me.display_name}</span>}
        <button
          onClick={handleSwitchUser}
          style={{ fontSize: '0.8em', color: '#888', background: 'none', border: '1px solid #ccc', borderRadius: 4, padding: '2px 8px', cursor: 'pointer' }}
        >
          ログアウト
        </button>
      </div>

      {currentQuestion ? (
        <div>
          {currentQuestion.question_image && (
            <img
              src={currentQuestion.question_image}
              alt="問題画像"
              style={{ maxHeight: 200, marginBottom: 8 }}
            />
          )}
          <pre className="question-text">{currentQuestion.question_text}</pre>

          <Timer deadline={deadline} onExpire={() => fetchState(eventId)} />

          <div style={{ marginTop: 12 }}>
            {currentQuestion.choices.map(c => {
              const btnDisabled = deadlinePassed || alreadyAnswered || isRevealed
              const selected  = myAnswer?.choice_index === c.choice_index
              const correct   = isRevealed && c.choice_index === correctIdx
              const incorrect = isRevealed && myAnswer?.choice_index === c.choice_index && !correct

              return (
                <ChoiceButton
                  key={c.choice_index}
                  choice={c}
                  selected={selected}
                  correct={correct}
                  incorrect={incorrect}
                  disabled={btnDisabled}
                  onClick={btnDisabled ? undefined : submitAnswer}
                />
              )
            })}
          </div>

          {answerStatus && (
            <div style={{ marginTop: 8 }} className={answerStatus.cls}>
              {answerStatus.text}
            </div>
          )}
        </div>
      ) : (
        <div style={{ color: '#555', marginTop: 16 }}>
          {eventState?.state === 'waiting'
            ? 'イベント開始をお待ちください...'
            : '次の問題をお待ちください...'}
        </div>
      )}
    </div>
  )
}

export default function QuizPage() {
  return (
    <EventProvider>
      <QuizContent />
    </EventProvider>
  )
}
