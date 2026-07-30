import { useEffect, useState } from 'react'

import { authApi } from '../api/auth'
import { ErrorState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function ProfilePage() {
  const { user, reloadUser } = useAuth()
  const [account, setAccount] = useState({ email: '', first_name: '', last_name: '' })
  const [profile, setProfile] = useState({ display_name: '', bio: '' })
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', new_password_confirm: '' })
  const [passwordError, setPasswordError] = useState(null)
  const [passwordSaved, setPasswordSaved] = useState(false)
  const [passwordSubmitting, setPasswordSubmitting] = useState(false)

  useEffect(() => {
    if (!user) return
    setAccount({ email: user.email, first_name: user.first_name, last_name: user.last_name })
    setProfile({ display_name: user.profile?.display_name || '', bio: user.profile?.bio || '' })
  }, [user])

  const submit = async (event) => {
    event.preventDefault(); setError(null); setSaved(false)
    try {
      await authApi.updateMe(account)
      await authApi.updateProfile(profile)
      await reloadUser()
      setSaved(true)
    } catch (requestError) { setError(requestError) }
  }

  const submitPassword = async (event) => {
    event.preventDefault()
    setPasswordError(null)
    setPasswordSaved(false)
    setPasswordSubmitting(true)
    try {
      await authApi.changePassword(passwordForm)
      setPasswordForm({ current_password: '', new_password: '', new_password_confirm: '' })
      setPasswordSaved(true)
    } catch (requestError) {
      setPasswordError(requestError)
    } finally {
      setPasswordSubmitting(false)
    }
  }

  return <section className="form-page page-section">
    <p className="eyebrow">ACCOUNT</p>
    <h1>프로필</h1>
    <form className="stack-form" onSubmit={submit}>
      <div className="form-row"><label>아이디 (변경 불가)<input value={user.username} readOnly /></label><label>이메일<input type="email" value={account.email} onChange={(event) => setAccount({ ...account, email: event.target.value })} required /></label></div>
      <div className="form-row"><label>이름<input value={account.first_name} onChange={(event) => setAccount({ ...account, first_name: event.target.value })} /></label><label>성<input value={account.last_name} onChange={(event) => setAccount({ ...account, last_name: event.target.value })} /></label></div>
      <label>표시 이름<input value={profile.display_name} onChange={(event) => setProfile({ ...profile, display_name: event.target.value })} /></label>
      <label>소개<textarea rows="6" value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} /></label>
      {saved && <p className="success-message">저장했습니다.</p>}
      {error && <ErrorState error={error} />}
      <button type="submit">저장</button>
    </form>
    <section className="password-settings" aria-labelledby="password-change-heading">
      <h2 id="password-change-heading">비밀번호 변경</h2>
      <p>현재 비밀번호를 확인한 뒤 새 비밀번호로 변경합니다.</p>
      <form className="stack-form" onSubmit={submitPassword}>
        <label>현재 비밀번호<input type="password" autoComplete="current-password" value={passwordForm.current_password} onChange={(event) => setPasswordForm({ ...passwordForm, current_password: event.target.value })} required /></label>
        <label>새 비밀번호<input type="password" autoComplete="new-password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} required /></label>
        <label>새 비밀번호 확인<input type="password" autoComplete="new-password" value={passwordForm.new_password_confirm} onChange={(event) => setPasswordForm({ ...passwordForm, new_password_confirm: event.target.value })} required /></label>
        {passwordSaved && <p className="success-message">비밀번호를 변경했습니다.</p>}
        {passwordError && <ErrorState error={passwordError} />}
        <button type="submit" disabled={passwordSubmitting}>{passwordSubmitting ? '변경 중…' : '비밀번호 변경'}</button>
      </form>
    </section>
  </section>
}
