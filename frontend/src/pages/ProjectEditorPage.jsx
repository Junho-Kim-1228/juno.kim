import { useEffect, useState } from 'react'
import { useHistory, useParams } from 'react-router-dom'

import { projectApi } from '../api/projects'
import { ErrorState } from '../components/AsyncState'
import { MarkdownEditor } from '../components/MarkdownEditor'

const initialForm = { title: '', summary: '', description: '', technologies: '', repository_url: '', live_url: '', status: 'draft', is_featured: false, started_on: '', ended_on: '' }

export function ProjectEditorPage() {
  const { slug } = useParams()
  const history = useHistory()
  const [form, setForm] = useState(initialForm)
  const [thumbnail, setThumbnail] = useState(null)
  const [error, setError] = useState(null)
  const isEditing = Boolean(slug)

  useEffect(() => {
    if (!isEditing) return
    projectApi.detail(slug).then((project) => setForm({
      ...initialForm,
      ...project,
      technologies: project.technologies.join(', '),
      started_on: project.started_on || '',
      ended_on: project.ended_on || '',
    })).catch(setError)
  }, [isEditing, slug])

  const submit = async (event) => {
    event.preventDefault()
    const payload = new FormData()
    Object.entries(form).forEach(([key, value]) => {
      if (key === 'technologies') payload.append(key, JSON.stringify(value.split(',').map((item) => item.trim()).filter(Boolean)))
      else payload.append(key, value)
    })
    if (thumbnail) payload.append('thumbnail', thumbnail)
    try {
      const project = isEditing ? await projectApi.update(slug, payload) : await projectApi.create(payload)
      history.push(`/projects/${project.slug}`)
    } catch (requestError) { setError(requestError) }
  }

  return (
    <section className="form-page page-section"><p className="eyebrow">PROJECT EDITOR</p><h1>{isEditing ? '프로젝트 수정' : '프로젝트 추가'}</h1>
      <form className="stack-form" onSubmit={submit}>
        <label>제목<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required /></label>
        <label>요약<input maxLength="300" value={form.summary} onChange={(event) => setForm({ ...form, summary: event.target.value })} required /></label>
        <MarkdownEditor label="설명" rows={12} value={form.description} onChange={(description) => setForm({ ...form, description })} required />
        <label>기술 스택 (쉼표로 구분)<input value={form.technologies} onChange={(event) => setForm({ ...form, technologies: event.target.value })} /></label>
        <div className="form-row"><label>저장소 URL<input type="url" value={form.repository_url} onChange={(event) => setForm({ ...form, repository_url: event.target.value })} /></label><label>서비스 URL<input type="url" value={form.live_url} onChange={(event) => setForm({ ...form, live_url: event.target.value })} /></label></div>
        <div className="form-row"><label>시작일<input type="date" value={form.started_on} onChange={(event) => setForm({ ...form, started_on: event.target.value })} /></label><label>종료일<input type="date" value={form.ended_on} onChange={(event) => setForm({ ...form, ended_on: event.target.value })} /></label></div>
        <label>대표 이미지<input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setThumbnail(event.target.files[0])} /></label>
        <div className="form-row"><label>상태<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option value="draft">초안</option><option value="published">공개</option><option value="archived">보관</option></select></label><label className="check-label"><input type="checkbox" checked={form.is_featured} onChange={(event) => setForm({ ...form, is_featured: event.target.checked })} /> 대표 프로젝트</label></div>
        {error && <ErrorState error={error} />}<button type="submit">저장</button>
      </form>
    </section>
  )
}
