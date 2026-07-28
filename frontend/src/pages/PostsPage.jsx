import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { PostCard } from '../components/PostCard'
import { useAuth } from '../hooks/useAuth'

export function PostsPage() {
  const { user } = useAuth()
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  useEffect(() => { postApi.list().then(setPosts).catch(setError).finally(() => setLoading(false)) }, [])
  return <section className="page-section"><div className="section-heading"><div><p className="eyebrow">TECH BLOG</p><h1>기술 기록</h1></div>{user && <Link className="button-link small" to="/blog/new">글쓰기</Link>}</div>{error && <ErrorState error={error} />}{loading ? <LoadingState /> : <div className="card-grid">{posts.map((post) => <PostCard key={post.id} post={post} />)}</div>}</section>
}
