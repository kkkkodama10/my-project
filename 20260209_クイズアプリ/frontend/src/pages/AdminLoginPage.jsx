import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function AdminLoginPage() {
  const { login } = useAuth()
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('')
    try {
      await login(password)
    } catch (err) {
      setStatus('ログイン失敗: ' + err.message)
    }
  }

  return (
    <div>
      <h1>管理者ログイン</h1>
      <form onSubmit={handleSubmit}>
        <label>
          パスワード:{' '}
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            autoFocus
          />
        </label>
        {' '}
        <button type="submit">ログイン</button>
        {status && (
          <span style={{ marginLeft: 8, color: '#d33' }}>{status}</span>
        )}
      </form>
    </div>
  )
}
