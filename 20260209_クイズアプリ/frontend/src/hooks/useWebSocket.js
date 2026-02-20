import { useEffect, useRef } from 'react'

const RECONNECT_DELAY = 1500

/**
 * WebSocket 接続フック。
 * url が変わると再接続。アンマウント時はクリーンアップ。
 * 1.5 秒後に自動再接続。
 */
export function useWebSocket(url, { onMessage, onOpen, onClose } = {}) {
  const wsRef = useRef(null)
  const timerRef = useRef(null)
  // コールバックを ref に保持して再接続を防ぐ
  const onMessageRef = useRef(onMessage)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)

  useEffect(() => { onMessageRef.current = onMessage }, [onMessage])
  useEffect(() => { onOpenRef.current = onOpen }, [onOpen])
  useEffect(() => { onCloseRef.current = onClose }, [onClose])

  useEffect(() => {
    if (!url) return

    function connect() {
      if (wsRef.current) return
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[WS] open')
        if (timerRef.current) { clearTimeout(timerRef.current); timerRef.current = null }
        try { ws.send('hello from client') } catch (e) { console.debug(e) }
        onOpenRef.current?.()
      }

      ws.onmessage = (ev) => {
        let parsed
        try { parsed = JSON.parse(ev.data) } catch {
          console.debug('[WS] text:', ev.data)
          return
        }
        console.log('[WS] msg', parsed)
        onMessageRef.current?.(parsed)
      }

      ws.onclose = () => {
        console.log('[WS] close')
        wsRef.current = null
        onCloseRef.current?.()
        timerRef.current = setTimeout(connect, RECONNECT_DELAY)
      }

      ws.onerror = (e) => { console.error('[WS] error', e) }
    }

    connect()

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (wsRef.current) {
        wsRef.current.onclose = null  // アンマウント時は再接続しない
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [url])
}
