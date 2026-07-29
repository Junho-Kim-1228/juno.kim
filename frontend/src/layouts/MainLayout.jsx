import { Link, NavLink, useHistory } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'

export function MainLayout({ children }) {
  const { user, logout } = useAuth()
  const history = useHistory()
  const handleLogout = async () => { await logout(); history.push('/') }

  return <div className="site-shell">
    <header className="site-header">
      <Link className="brand" to="/">juno.kim</Link>
      <nav aria-label="주요 메뉴">
        <NavLink exact to="/" activeClassName="active">홈</NavLink>
        <NavLink to="/board" activeClassName="active">게시판</NavLink>
        <NavLink to="/guestbook" activeClassName="active">방명록</NavLink>
        <NavLink to="/developer" activeClassName="active">개발자</NavLink>
      </nav>
      <div className="account-nav">
        {user ? <>{user.is_staff && <a className="admin-page-link" href="/admin/">관리</a>}<Link to="/profile">{user.profile?.display_name || user.username}</Link><button className="text-button" type="button" onClick={handleLogout}>로그아웃</button></> : <Link className="admin-link" to="/login">로그인</Link>}
      </div>
    </header>
    <main>{children}</main>
    <footer className="site-footer"><span>© {new Date().getFullYear()} juno.kim</span></footer>
  </div>
}
