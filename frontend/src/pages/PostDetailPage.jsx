import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { CommentSection } from '../components/CommentSection'
import { useAuth } from '../hooks/useAuth'

export function PostDetailPage() {
  const { slug } = useParams()
  const { user } = useAuth()
  const [post, setPost] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => { postApi.detail(slug).then(setPost).catch(setError) }, [slug])
  if (error) return <ErrorState error={error} />
  if (!post) return <LoadingState />
  const canEdit = user?.is_staff
  return <article className="detail-page page-section"><p className="eyebrow">{post.category?.name || 'TECH BLOG'}</p><h1>{post.title}</h1><p className="lead">{post.excerpt}</p><div className="post-byline"><span>{post.author.display_name || post.author.username}</span><time>{post.published_at ? new Date(post.published_at).toLocaleDateString('ko-KR') : '초안'}</time>{canEdit && <Link to={`/blog/${post.slug}/edit`}>수정</Link>}</div>{post.cover_image && <img className="cover-image" src={post.cover_image} alt="" />}<div className="prose">{post.content}</div><CommentSection postSlug={post.slug} /></article>
}
