import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { guestbookApi } from '../api/guestbook'
import { useAuth } from '../hooks/useAuth'
import { ErrorState } from './AsyncState'

const initialForm = { message: '' }

export function GuestbookSection() {
  const { user, loading: authLoading } = useAuth()
  const [entries, setEntries] = useState([])
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    guestbookApi.list()
      .then(setEntries)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    if (!user || !form.message.trim()) return
    setSubmitting(true)
    setError(null)
    try {
      const entry = await guestbookApi.create(form)
      setEntries((current) => [entry, ...current].slice(0, 12))
      setForm(initialForm)
    } catch (requestError) {
      setError(requestError)
    } finally {
      setSubmitting(false)
    }
  }

  const updateField = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  return (
    <section className="guestbook-section page-section" id="guestbook">
      <div className="section-heading">
        <div>
          <p className="eyebrow">GUESTBOOK</p>
          <h2>한마디 남기기</h2>
        </div>
        <p className="section-note">로그인한 사용자만 작성할 수 있습니다.</p>
      </div>
      {authLoading ? <p className="guestbook-auth-note">로그인 상태를 확인하고 있습니다.</p> : user ? (
        <form className="guestbook-form" onSubmit={submit}>
          <label className="guestbook-message">
            <span>{user.profile?.display_name || user.username} 님으로 남기기</span>
            <textarea
              name="message"
              value={form.message}
              onChange={updateField}
              minLength="1"
              maxLength="500"
              rows="3"
              placeholder="가볍게 인사를 남겨주세요."
              required
            />
          </label>
          <button type="submit" disabled={submitting}>{submitting ? '등록 중' : '남기기'}</button>
        </form>
      ) : (
        <p className="guestbook-auth-note">방문록을 작성하려면 로그인해 주세요. <Link to="/login">로그인</Link></p>
      )}
      {error && <ErrorState error={error} />}
      {loading ? <p className="guestbook-state">방문록을 불러오는 중입니다.</p> : (
        entries.length > 0 ? (
          <ul className="guestbook-list">
            {entries.map((entry) => (
              <li key={entry.id}>
                <div className="guestbook-head">
                  <strong>{entry.name}</strong>
                  <time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleDateString('ko-KR')}</time>
                </div>
                <p>{entry.message}</p>
              </li>
            ))}
          </ul>
        ) : <p className="empty-row">아직 남겨진 글이 없습니다. 첫 인사를 남겨주세요.</p>
      )}
    </section>
  )
}
