import { useEffect, useState } from 'react'
import { useHistory, useParams } from 'react-router-dom'

import { postApi } from '../api/posts'
import { ErrorState } from '../components/AsyncState'

const initialForm = { title: '', excerpt: '', content: '', category_id: '', tag_ids: [], status: 'draft', is_featured: false }

export function PostEditorPage() {
  const { slug } = useParams()
  const history = useHistory()
  const [form, setForm] = useState(initialForm)
  const [cover, setCover] = useState(null)
  const [options, setOptions] = useState({ categories: [], tags: [] })
  const [error, setError] = useState(null)
  const isEditing = Boolean(slug)

  useEffect(() => {
    Promise.all([postApi.categories(), postApi.tags()]).then(([categories, tags]) => setOptions({ categories, tags })).catch(setError)
    if (isEditing) postApi.detail(slug).then((post) => setForm({ ...initialForm, ...post, category_id: post.category?.id || '', tag_ids: post.tags.map((tag) => tag.id) })).catch(setError)
  }, [isEditing, slug])

  const submit = async (event) => {
    event.preventDefault()
    const payload = new FormData()
    ;['title', 'excerpt', 'content', 'status', 'is_featured'].forEach((key) => payload.append(key, form[key]))
    if (form.category_id) payload.append('category_id', form.category_id)
    form.tag_ids.forEach((id) => payload.append('tag_ids', id))
    if (cover) payload.append('cover_image', cover)
    try {
      const post = isEditing ? await postApi.update(slug, payload) : await postApi.create(payload)
      history.push(`/blog/${post.slug}`)
    } catch (requestError) { setError(requestError) }
  }

  const toggleTag = (id) => setForm({ ...form, tag_ids: form.tag_ids.includes(id) ? form.tag_ids.filter((tagId) => tagId !== id) : [...form.tag_ids, id] })

  return <section className="form-page page-section"><p className="eyebrow">POST EDITOR</p><h1>{isEditing ? '게시글 수정' : '새 글 작성'}</h1><form className="stack-form" onSubmit={submit}>
    <label>제목<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label><label>요약<input maxLength="320" value={form.excerpt} onChange={(event) => setForm({ ...form, excerpt: event.target.value })} required /></label><label>본문<textarea rows="18" value={form.content} onChange={(event) => setForm({ ...form, content: event.target.value })} required /></label>
    <label>카테고리<select value={form.category_id} onChange={(event) => setForm({ ...form, category_id: Number(event.target.value) || '' })}><option value="">선택 안 함</option>{options.categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
    <fieldset><legend>태그</legend><div className="chip-row">{options.tags.map((tag) => <label className="check-label" key={tag.id}><input type="checkbox" checked={form.tag_ids.includes(tag.id)} onChange={() => toggleTag(tag.id)} /> {tag.name}</label>)}</div></fieldset>
    <label>대표 이미지<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setCover(event.target.files[0])} /></label><div className="form-row"><label>상태<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option value="draft">초안</option><option value="published">공개</option><option value="archived">보관</option></select></label><label className="check-label"><input type="checkbox" checked={form.is_featured} onChange={(event) => setForm({ ...form, is_featured: event.target.checked })} /> 대표 게시글</label></div>{error && <ErrorState error={error} />}<button type="submit">저장</button>
  </form></section>
}
