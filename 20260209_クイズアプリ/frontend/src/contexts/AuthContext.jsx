import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { post, get } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [isAdmin, setIsAdmin] = useState(false)
  const [checking, setChecking] = useState(true)  // リロード時のセッション確認中フラグ

  // マウント時: Cookie の admin_session が有効か確認
  useEffect(() => {
    get('/api/admin/verify')
      .then(res => { if (res.ok) setIsAdmin(true) })
      .catch(() => {})
      .finally(() => setChecking(false))
  }, [])

  const login = useCallback(async (password) => {
    const res = await post('/api/admin/login', { password })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'login failed')
    }
    setIsAdmin(true)
  }, [])

  const logout = useCallback(() => {
    setIsAdmin(false)
  }, [])

  return (
    <AuthContext.Provider value={{ isAdmin, checking, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
