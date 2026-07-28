import { useEffect, useState } from 'react'

import { authApi } from '../api/auth'
import { ErrorState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function ProfilePage() {
  const { user, reloadUser } = useAuth()
  const [account, setAccount] = useState({ username: '', email: '', first_name: '', last_name: '' })
  const [profile, setProfile] = useState({ display_name: '', bio: '', website_url: '', github_url: '' })
  const [avatar, setAvatar] = useState(null)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!user) return
    setAccount({ username: user.username, email: user.email, first_name: user.first_name, last_name: user.last_name })
    setProfile({ display_name: user.profile?.display_name || '', bio: user.profile?.bio || '', website_url: user.profile?.website_url || '', github_url: user.profile?.github_url || '' })
  }, [user])

  const submit = async (event) => {
    event.preventDefault(); setError(null); setSaved(false)
    try {
      await authApi.updateMe(account)
      const formData = new FormData()
      Object.entries(profile).forEach(([key, value]) => formData.append(key, value))
      if (avatar) formData.append('avatar', avatar)
      await authApi.updateProfile(formData)
      await reloadUser()
      setSaved(true)
    } catch (requestError) { setError(requestError) }
  }

  return <section className="form-page page-section"><p className="eyebrow">ACCOUNT</p><h1>프로필</h1><form className="stack-form" onSubmit={submit}><div className="form-row"><label>아이디<input value={account.username} onChange={(event) => setAccount({ ...account, username: event.target.value })} required /></label><label>이메일<input type="email" value={account.email} onChange={(event) => setAccount({ ...account, email: event.target.value })} required /></label></div><div className="form-row"><label>이름<input value={account.first_name} onChange={(event) => setAccount({ ...account, first_name: event.target.value })} /></label><label>성<input value={account.last_name} onChange={(event) => setAccount({ ...account, last_name: event.target.value })} /></label></div><label>표시 이름<input value={profile.display_name} onChange={(event) => setProfile({ ...profile, display_name: event.target.value })} /></label><label>소개<textarea rows="6" value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} /></label><div className="form-row"><label>웹사이트<input type="url" value={profile.website_url} onChange={(event) => setProfile({ ...profile, website_url: event.target.value })} /></label><label>GitHub<input type="url" value={profile.github_url} onChange={(event) => setProfile({ ...profile, github_url: event.target.value })} /></label></div><label>프로필 이미지<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setAvatar(event.target.files[0])} /></label>{saved && <p className="success-message">저장했습니다.</p>}{error && <ErrorState error={error} />}<button type="submit">저장</button></form></section>
}
