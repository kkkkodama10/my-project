import { createContext, useContext, useState, useCallback } from 'react'
import { get } from '../api/client'

const EventContext = createContext(null)

export function EventProvider({ children }) {
  const [eventState, setEventState] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [myAnswer, setMyAnswer] = useState(null)
  const [me, setMe] = useState(null)

  const fetchState = useCallback(async (eventId) => {
    try {
      const res = await get(`/api/events/${eventId}/me/state`)
      if (!res.ok) return null
      const data = await res.json()
      setEventState(data.event || null)
      setCurrentQuestion(data.current_question || null)
      setMyAnswer(data.my_answer || null)
      setMe(data.me || null)
      return data
    } catch (e) {
      console.debug('fetchState error', e)
      return null
    }
  }, [])

  return (
    <EventContext.Provider value={{ eventState, currentQuestion, myAnswer, me, fetchState }}>
      {children}
    </EventContext.Provider>
  )
}

export function useEvent() {
  return useContext(EventContext)
}
