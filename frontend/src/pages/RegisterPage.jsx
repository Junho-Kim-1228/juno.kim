import { useState } from 'react'
import { Link, Redirect, useHistory } from 'react-router-dom'

import { ErrorState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function RegisterPage() {
  const { user, register } = useAuth()
  const history = useHistory()
  const [form, setForm] = useState({ username: '', email: '', password: '', first_name: '', last_name: '' })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Redirect to="/" />

  const submit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      await register(form)
      history.replace('/profile')
    } catch (requestError) {
      setError(requestError)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-panel">
      <p className="eyebrow">JOIN</p><h1>회원가입</h1>
      <form className="stack-form" onSubmit={submit}>
        <label>아이디<input autoComplete="username" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required /></label>
        <label>이메일<input type="email" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></label>
        <div className="form-row"><label>이름<input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} /></label><label>성<input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} /></label></div>
        <label>비밀번호<input type="password" autoComplete="new-password" minLength="8" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required /></label>
        {error && <ErrorState error={error} />}
        <button type="submit" disabled={submitting}>{submitting ? '가입 중…' : '회원가입'}</button>
      </form>
      <p className="muted">이미 계정이 있으신가요? <Link to="/login">로그인</Link></p>
    </section>
  )
}
