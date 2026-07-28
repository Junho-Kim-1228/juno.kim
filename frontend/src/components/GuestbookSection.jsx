import { useEffect, useState } from 'react'

import { guestbookApi } from '../api/guestbook'
import { ErrorState } from './AsyncState'

const initialForm = { name: '', message: '' }

export function GuestbookSection() {
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
    if (!form.name.trim() || !form.message.trim()) return
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
        <p className="section-note">로그인 없이 남길 수 있습니다.</p>
      </div>
      <form className="guestbook-form" onSubmit={submit}>
        <label>
          <span>이름</span>
          <input
            name="name"
            value={form.name}
            onChange={updateField}
            minLength="2"
            maxLength="40"
            placeholder="이름 또는 닉네임"
            required
          />
        </label>
        <label className="guestbook-message">
          <span>메시지</span>
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
