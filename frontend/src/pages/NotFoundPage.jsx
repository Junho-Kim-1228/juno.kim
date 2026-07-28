import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return <section className="auth-panel"><p className="eyebrow">404</p><h1>페이지를 찾을 수 없습니다.</h1><Link className="button-link" to="/">홈으로 돌아가기</Link></section>
}
