import { Link } from 'react-router-dom'

export function PostCard({ post }) {
  return (
    <article className="card">
      <div className="card-meta">
        <span>{post.category?.name || '기술 기록'}</span>
        <span>댓글 {post.comment_count}</span>
      </div>
      <h3><Link to={`/blog/${post.slug}`}>{post.title}</Link></h3>
      <p>{post.excerpt}</p>
      <div className="chip-row">
        {post.tags.map((tag) => <span className="chip" key={tag.id}>#{tag.name}</span>)}
      </div>
    </article>
  )
}
