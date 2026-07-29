import { useEffect, useState } from 'react'
import { Link, useHistory, useParams } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { CommentSection } from '../components/CommentSection'
import { useAuth } from '../hooks/useAuth'

export function PostDetailPage() {
  const { slug } = useParams()
  const history = useHistory()
  const { user } = useAuth()
  const [post, setPost] = useState(null)
  const [error, setError] = useState(null)
  const [deleting, setDeleting] = useState(false)
  useEffect(() => { postApi.detail(slug).then(setPost).catch(setError) }, [slug])
  if (error) return <ErrorState error={error} />
  if (!post) return <LoadingState />
  const canEdit = user?.is_staff || (user?.email_verified && user.id === post.author.id)
  const basePath = post.kind === 'technical' ? '/blog' : '/board'
  const removePost = async () => {
    if (!window.confirm('게시글을 삭제할까요? 삭제 후에는 복구할 수 없습니다.')) return
    setDeleting(true)
    try {
      await postApi.remove(post.slug)
      history.replace(post.kind === 'technical' ? '/developer' : '/board')
    } catch (requestError) {
      setError(requestError)
      setDeleting(false)
    }
  }
  return <article className="detail-page page-section"><p className="eyebrow">{post.kind === 'technical' ? '기술 기록' : post.category?.name || '게시판'}</p><h1>{post.is_featured && <span className="notice-prefix">[공지]</span>}{post.title}</h1><p className="lead">{post.excerpt}</p><div className="post-byline"><span>{post.author.display_name || post.author.username}</span><time>{post.published_at ? new Date(post.published_at).toLocaleDateString('ko-KR') : '초안'}</time>{canEdit && <><Link to={`${basePath}/${post.slug}/edit`}>수정</Link><button type="button" className="text-button danger" disabled={deleting} onClick={removePost}>{deleting ? '삭제 중…' : '삭제'}</button></>}</div>{post.cover_image && <img className="cover-image" src={post.cover_image} alt="" />}<div className="prose">{post.content}</div><CommentSection postSlug={post.slug} /></article>
}
