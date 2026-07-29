import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { authApi } from '../api/auth'
import { guestbookApi } from '../api/guestbook'
import { reportApi } from '../api/reports'
import { useAuth } from '../hooks/useAuth'
import { ErrorState } from './AsyncState'

const initialForm = { message: '' }

function EntryAuthor({ entry }) {
  if (!entry.author) return <strong>{entry.name} <span className="username">(@legacy)</span></strong>
  return <strong>{entry.author.is_staff && <span className="operator-badge before-author">사이트 운영자</span>}{entry.author.display_name || entry.author.username} <span className="username">(@{entry.author.username})</span></strong>
}

export function GuestbookSection({ compact = false, standalone = false }) {
  const { user, loading: authLoading, reloadUser } = useAuth()
  const [entries, setEntries] = useState([])
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [notice, setNotice] = useState(null)

  useEffect(() => { guestbookApi.list().then(setEntries).catch(setError).finally(() => setLoading(false)) }, [])
  const submit = async (event) => {
    event.preventDefault()
    if (!user || !user.email_verified || !form.message.trim()) return
    setSubmitting(true); setError(null)
    try { const entry = await guestbookApi.create(form); setEntries((current) => [entry, ...current].slice(0, 12)); setForm(initialForm) } catch (requestError) { setError(requestError) } finally { setSubmitting(false) }
  }
  const resend = async () => { setError(null); setNotice(null); try { setNotice((await authApi.resendVerification()).detail); await reloadUser() } catch (requestError) { setError(requestError) } }
  const report = async (id) => { const reason = window.prompt('사칭으로 의심되는 이유를 적어 주세요.'); if (reason === null) return; try { setNotice((await reportApi.impersonation('guestbook', id, reason)).detail) } catch (requestError) { setError(requestError) } }

  const shownEntries = compact ? entries.slice(0, 5) : entries
  return <section className={`guestbook-section page-section${standalone ? ' standalone-page' : ''}`} id="guestbook"><div className="section-heading"><div><p className="eyebrow">방명록</p><h2>{compact ? '잠시 들렀다 간 이야기' : '방명록'}</h2></div><p className="section-note">인증된 로그인 사용자만 작성할 수 있습니다.</p></div>{authLoading ? <p className="guestbook-auth-note">로그인 상태를 확인하고 있습니다.</p> : !user ? <p className="guestbook-auth-note">방명록을 작성하려면 로그인해 주세요. <Link to="/login">로그인</Link></p> : !user.email_verified ? <p className="guestbook-auth-note">이메일 인증이 필요합니다. 받은편지함을 확인하거나 <button className="text-button" type="button" onClick={resend}>인증 메일 재발송</button></p> : <form className="guestbook-form" onSubmit={submit}><label className="guestbook-message"><span>{user.profile?.display_name || user.username} (@{user.username}) 님으로 남기기</span><textarea name="message" value={form.message} onChange={(event) => setForm({ message: event.target.value })} maxLength="500" rows="3" placeholder="가볍게 인사를 남겨 주세요." required /></label><button type="submit" disabled={submitting}>{submitting ? '등록 중' : '남기기'}</button></form>}{notice && <p className="success-message">{notice}</p>}{error && <ErrorState error={error} />}{loading ? <p className="guestbook-state">방명록을 불러오는 중입니다.</p> : shownEntries.length > 0 ? <ul className="guestbook-list">{shownEntries.map((entry) => { const canReport = user?.email_verified && entry.author && user.id !== entry.author.id; return <li key={entry.id}><div className="guestbook-head"><EntryAuthor entry={entry} /><time dateTime={entry.created_at}>{new Date(entry.created_at).toLocaleDateString('ko-KR')}</time></div><div><p>{entry.message}</p>{canReport && <button className="text-button report-button" type="button" onClick={() => report(entry.id)}>사칭 신고</button>}</div></li> })}</ul> : <p className="empty-row">아직 남겨진 글이 없습니다.</p>}</section>
}
