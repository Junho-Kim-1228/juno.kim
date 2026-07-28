import { Link, NavLink, useHistory } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'

export function MainLayout({ children }) {
  const { user, logout } = useAuth()
  const history = useHistory()

  const handleLogout = async () => {
    await logout()
    history.push('/')
  }

  return (
    <div className="site-shell">
      <header className="site-header">
        <Link className="brand" to="/">juno.kim</Link>
        <nav aria-label="주요 메뉴">
          <NavLink exact to="/" activeClassName="active">홈</NavLink>
          <NavLink to="/projects" activeClassName="active">프로젝트</NavLink>
          <NavLink to="/blog" activeClassName="active">블로그</NavLink>
        </nav>
        <div className="account-nav">
          {user ? (
            <>
              <Link to="/profile">{user.profile?.display_name || user.username}</Link>
              <button className="text-button" type="button" onClick={handleLogout}>로그아웃</button>
            </>
          ) : (
            <>
              <Link to="/login">로그인</Link>
              <Link className="button-link small" to="/register">회원가입</Link>
            </>
          )}
        </div>
      </header>
      <main>{children}</main>
      <footer className="site-footer">
        <span>© {new Date().getFullYear()} juno.kim</span>
        <span>React · Django · AWS</span>
      </footer>
    </div>
  )
}
