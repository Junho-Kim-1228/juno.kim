import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { GuestbookSection } from '../components/GuestbookSection'
import { PostCard } from '../components/PostCard'
import { useAuth } from '../hooks/useAuth'

export function HomePage() {
  const { user } = useAuth()
  const [posts, setPosts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    postApi.list({ kind: 'board', public_only: 'true' }).then((items) => setPosts(items.slice(0, 5))).catch(setError).finally(() => setLoading(false))
    postApi.categories().then(setCategories).catch(setError)
  }, [])

  return <>
    <section className="home-intro page-section">
      <h1>김준호 개인공간</h1>
      <div className="home-actions">
        {user?.is_staff || user?.email_verified ? <Link className="button-link" to="/board/new">게시판 글쓰기</Link> : <Link className="button-link" to="/board">게시판 둘러보기</Link>}
        <a className="button-link secondary" href="#guestbook">방명록 남기기</a>
      </div>
      {categories.length > 0 && <div className="category-links" aria-label="글 분류">
        {categories.map((category) => <Link key={category.id} to={`/board?category=${encodeURIComponent(category.slug)}`}>{category.name}</Link>)}
      </div>}
    </section>

    <section className="page-section home-feed">
      <div className="section-heading"><div><p className="eyebrow">최근 게시글</p><h2>새로 남긴 이야기</h2></div><Link to="/board">게시판 전체 보기</Link></div>
      {error && <ErrorState error={error} />}
      {loading ? <LoadingState /> : posts.length > 0 ? <div className="card-grid">{posts.map((post) => <PostCard key={post.id} post={post} />)}</div> : <p className="empty-row">아직 게시글이 없습니다. 첫 글을 남겨 보세요.</p>}
    </section>

    <GuestbookSection compact />
  </>
}
