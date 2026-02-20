import { useState, useEffect, useRef } from 'react'

export default function Timer({ deadline, onExpire }) {
  const [remaining, setRemaining] = useState(null)
  const expiredRef = useRef(false)

  useEffect(() => {
    if (!deadline) {
      setRemaining(null)
      expiredRef.current = false
      return
    }

    expiredRef.current = false

    function tick() {
      const diff = Math.max(0, Math.floor((new Date(deadline) - new Date()) / 1000))
      setRemaining(diff)
      if (diff <= 0 && !expiredRef.current) {
        expiredRef.current = true
        onExpire?.()
      }
    }

    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [deadline, onExpire])

  if (remaining === null) return null

  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  return (
    <div style={{ marginTop: 6, fontSize: '0.95em', color: '#444' }}>
      締切: {mins}:{secs.toString().padStart(2, '0')}
    </div>
  )
}
