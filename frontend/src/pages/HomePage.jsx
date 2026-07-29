import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { GuestbookSection } from '../components/GuestbookSection'
import { PostCard } from '../components/PostCard'
import { useAuth } from '../hooks/useAuth'

const categories = ['일상', '취미', '사진', '개발']

export function HomePage() {
  const { user } = useAuth()
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    postApi.list().then((items) => setPosts(items.slice(0, 5))).catch(setError).finally(() => setLoading(false))
  }, [])

  return <>
    <section className="home-intro page-section">
      <p className="home-greeting">안녕하세요, 준호의 작은 홈페이지입니다.</p>
      <h1>생각나는 것들을<br />가볍게 남겨 둡니다.</h1>
      <p className="home-copy">일상에서 본 것, 좋아하는 것, 사진과 개발 기록을 천천히 모아 두는 공간입니다.</p>
      <div className="home-actions">
        {user?.is_staff ? <Link className="button-link" to="/board/new">게시판 글쓰기</Link> : <Link className="button-link" to="/board">게시판 둘러보기</Link>}
        <a className="button-link secondary" href="#guestbook">방명록 남기기</a>
      </div>
      <div className="category-links" aria-label="글 분류">
        {categories.map((category) => <Link key={category} to={`/board?category=${encodeURIComponent(category)}`}>{category}</Link>)}
      </div>
    </section>

    <section className="page-section home-feed">
      <div className="section-heading"><div><p className="eyebrow">최근 게시글</p><h2>새로 남긴 이야기</h2></div><Link to="/board">게시판 전체 보기</Link></div>
      {error && <ErrorState error={error} />}
      {loading ? <LoadingState /> : posts.length > 0 ? <div className="card-grid">{posts.map((post) => <PostCard key={post.id} post={post} />)}</div> : <p className="empty-row">아직 게시글이 없습니다. 첫 글을 남겨 보세요.</p>}
    </section>

    <GuestbookSection compact />
  </>
}
