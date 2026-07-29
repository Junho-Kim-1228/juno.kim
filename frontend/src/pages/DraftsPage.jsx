import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { PostCard } from '../components/PostCard'

export function DraftsPage() {
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    postApi.list({ scope: 'drafts' }).then(setPosts).catch(setError).finally(() => setLoading(false))
  }, [])

  return <section className="page-section board-page">
    <div className="section-heading">
      <div><p className="eyebrow">내 글</p><h1>임시저장 보관함</h1><p className="page-description">작성 중인 글은 이곳에만 보관되며 다른 사용자에게 공개되지 않습니다.</p></div>
      <div className="section-actions"><Link className="button-link secondary small" to="/board">게시판으로</Link><Link className="button-link small" to="/board/new">새 글 작성</Link></div>
    </div>
    {error && <ErrorState error={error} />}
    {loading ? <LoadingState /> : posts.length ? <div className="card-grid">{posts.map((post) => <PostCard key={post.id} post={post} />)}</div> : <p className="empty-row">임시저장한 글이 없습니다.</p>}
  </section>
}
