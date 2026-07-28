import { useState } from 'react'
import { Link, Redirect, useHistory, useLocation } from 'react-router-dom'

import { ErrorState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function LoginPage() {
  const { user, login } = useAuth()
  const history = useHistory()
  const location = useLocation()
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Redirect to="/" />

  const submit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await login(form)
      history.replace(location.state?.from || '/')
    } catch (requestError) {
      setError(requestError)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-panel">
      <p className="eyebrow">WELCOME BACK</p><h1>로그인</h1>
      <form className="stack-form" onSubmit={submit}>
        <label>아이디<input autoComplete="username" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required /></label>
        <label>비밀번호<input type="password" autoComplete="current-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required /></label>
        {error && <ErrorState error={error} />}
        <button type="submit" disabled={submitting}>{submitting ? '로그인 중…' : '로그인'}</button>
      </form>
      <p className="muted">계정이 없으신가요? <Link to="/register">회원가입</Link></p>
    </section>
  )
}
