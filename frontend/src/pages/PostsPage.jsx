import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { PostCard } from '../components/PostCard'
import { useAuth } from '../hooks/useAuth'

export function PostsPage({ title = '게시판', eyebrow = '게시판', description = '일상과 생각을 편하게 남기는 공간입니다.', writePath = '/board/new', allowMemberWriting = false, kind = 'board' }) {
  const { user } = useAuth()
  const location = useLocation()
  const category = new URLSearchParams(location.search).get('category')
  const [categories, setCategories] = useState([])
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    postApi.categories().then(setCategories).catch(setError)
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    postApi.list({ kind, ...(category ? { category } : {}) }).then(setPosts).catch(setError).finally(() => setLoading(false))
  }, [category, kind])

  const selectedCategory = categories.find((item) => item.slug === category)
  const canWrite = user?.is_staff || (allowMemberWriting && user?.email_verified)

  return <section className="page-section board-page"><div className="section-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{selectedCategory ? `${selectedCategory.name} 이야기` : title}</h1><p className="page-description">{description}</p></div>{canWrite && <Link className="button-link small" to={writePath}>글쓰기</Link>}</div>
    <nav className="board-filters" aria-label="게시글 카테고리">
      <Link className={!category ? 'active' : ''} to={location.pathname}>전체</Link>
      {categories.map((item) => <Link className={category === item.slug ? 'active' : ''} key={item.id} to={`${location.pathname}?category=${encodeURIComponent(item.slug)}`}>{item.name}</Link>)}
    </nav>
    {error && <ErrorState error={error} />}{loading ? <LoadingState /> : posts.length ? <div className="card-grid">{posts.map((post) => <PostCard basePath={kind === 'technical' ? '/blog' : '/board'} key={post.id} post={post} />)}</div> : <p className="empty-row">아직 이 분류의 글이 없습니다.</p>}</section>
}
