import { Link } from 'react-router-dom'

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

export function PostCard({ post, basePath = '/board' }) {
  return (
    <article className="card post-card">
      <div className="card-meta">
        <span>{formatDate(post.published_at || post.created_at)}</span>
        <span>{post.category?.name || '기록'}</span>
      </div>
      <h3><Link to={`${basePath}/${post.slug}`}>{post.is_featured && <span className="notice-prefix">[공지]</span>}{post.title}</Link></h3>
      <p>{post.excerpt}</p>
    </article>
  )
}
