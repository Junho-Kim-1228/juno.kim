import { Link } from 'react-router-dom'

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date(value))
}

export function PostCard({ post }) {
  return (
    <article className="card post-card">
      <div className="card-meta">
        <span>{formatDate(post.published_at || post.created_at)}</span>
        <span>{post.category?.name || '기록'}</span>
      </div>
      <h3><Link to={`/board/${post.slug}`}>{post.title}</Link></h3>
      <p>{post.excerpt}</p>
    </article>
  )
}
