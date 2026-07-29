import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { authApi } from '../api/auth'
import { ErrorState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function VerifyEmailPage() {
  const { reloadUser } = useAuth()
  const location = useLocation()
  const [error, setError] = useState(null)
  const [status, setStatus] = useState('인증 링크를 확인하고 있습니다.')

  useEffect(() => {
    const token = new URLSearchParams(location.search).get('token')
    if (!token) {
      setError(new Error('인증 토큰이 없습니다.'))
      return
    }
    authApi.verifyEmail(token)
      .then(async () => {
        setStatus('이메일 인증이 완료되었습니다. 이제 댓글과 방문록을 작성할 수 있습니다.')
        try { await reloadUser() } catch { /* The link may open in another browser. */ }
      })
      .catch(setError)
  }, [location.search, reloadUser])

  return <section className="auth-panel"><p className="eyebrow">EMAIL VERIFICATION</p><h1>이메일 인증</h1>{error ? <ErrorState error={error} /> : <p className="muted">{status}</p>}<p className="muted"><Link to="/login">로그인으로 이동</Link></p></section>
}
