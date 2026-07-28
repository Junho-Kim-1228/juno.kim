import { useCallback, useEffect, useState } from 'react'

import { commentApi } from '../api/comments'
import { useAuth } from '../hooks/useAuth'
import { ErrorState, LoadingState } from './AsyncState'

function CommentItem({ comment, user, onReply, onEdit, onDelete, isReply = false }) {
  const canManage = user && (user.is_staff || user.id === comment.author.id)
  return (
    <li className="comment">
      <div className="comment-head">
        <strong>{comment.author.display_name || comment.author.username}</strong>
        <time>{new Date(comment.created_at).toLocaleString('ko-KR')}</time>
      </div>
      <p>{comment.content}</p>
      {user && !isReply && <button className="text-button" type="button" onClick={() => onReply(comment.id)}>답글</button>}
      {canManage && <button className="text-button" type="button" onClick={() => onEdit(comment)}>수정</button>}
      {canManage && <button className="text-button danger" type="button" onClick={() => onDelete(comment.id)}>삭제</button>}
      {comment.replies?.length > 0 && (
        <ul className="reply-list">
          {comment.replies.map((reply) => (
            <CommentItem key={reply.id} comment={reply} user={user} onReply={onReply} onEdit={onEdit} onDelete={onDelete} isReply />
          ))}
        </ul>
      )}
    </li>
  )
}

export function CommentSection({ postSlug }) {
  const { user } = useAuth()
  const [comments, setComments] = useState([])
  const [content, setContent] = useState('')
  const [parent, setParent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const loadComments = useCallback(async () => {
    try {
      setError(null)
      setComments(await commentApi.list(postSlug))
    } catch (requestError) {
      setError(requestError)
    } finally {
      setLoading(false)
    }
  }, [postSlug])

  useEffect(() => { loadComments() }, [loadComments])

  const submit = async (event) => {
    event.preventDefault()
    if (!content.trim()) return
    try {
      await commentApi.create({ post_slug: postSlug, content, ...(parent ? { parent } : {}) })
      setContent('')
      setParent(null)
      await loadComments()
    } catch (requestError) {
      setError(requestError)
    }
  }

  const editComment = async (comment) => {
    const nextContent = window.prompt('수정할 댓글을 입력하세요.', comment.content)
    if (!nextContent?.trim()) return
    try {
      await commentApi.update(comment.id, nextContent)
      await loadComments()
    } catch (requestError) {
      setError(requestError)
    }
  }

  const deleteComment = async (id) => {
    if (!window.confirm('댓글을 삭제하시겠습니까?')) return
    try {
      await commentApi.remove(id)
      await loadComments()
    } catch (requestError) {
      setError(requestError)
    }
  }

  return (
    <section className="comments-section">
      <h2>댓글</h2>
      {user ? (
        <form className="stack-form" onSubmit={submit}>
          {parent && <p className="form-note">댓글 #{parent}에 답글 작성 중 <button className="text-button" type="button" onClick={() => setParent(null)}>취소</button></p>}
          <textarea value={content} onChange={(event) => setContent(event.target.value)} maxLength="3000" placeholder="서로에게 도움이 되는 댓글을 남겨주세요." required />
          <button type="submit">댓글 등록</button>
        </form>
      ) : <p className="muted">댓글을 작성하려면 로그인해 주세요.</p>}
      {error && <ErrorState error={error} />}
      {loading ? <LoadingState /> : (
        <ul className="comment-list">
          {comments.map((comment) => (
            <CommentItem key={comment.id} comment={comment} user={user} onReply={setParent} onEdit={editComment} onDelete={deleteComment} />
          ))}
        </ul>
      )}
    </section>
  )
}
