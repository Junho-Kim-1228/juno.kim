import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { projectApi } from '../api/projects'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function ProjectDetailPage() {
  const { slug } = useParams()
  const { user } = useAuth()
  const [project, setProject] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => { projectApi.detail(slug).then(setProject).catch(setError) }, [slug])
  if (error) return <ErrorState error={error} />
  if (!project) return <LoadingState />
  const canEdit = user && (user.is_staff || user.id === project.owner.id)

  return (
    <article className="detail-page page-section">
      <p className="eyebrow">PROJECT</p><h1>{project.title}</h1><p className="lead">{project.summary}</p>
      <div className="chip-row">{project.technologies.map((item) => <span className="chip" key={item}>{item}</span>)}</div>
      {project.thumbnail && <img className="cover-image" src={project.thumbnail} alt="" />}
      <div className="prose">{project.description}</div>
      <div className="detail-actions">
        {project.repository_url && <a className="button-link secondary" href={project.repository_url} target="_blank" rel="noreferrer">저장소</a>}
        {project.live_url && <a className="button-link" href={project.live_url} target="_blank" rel="noreferrer">서비스 보기</a>}
        {canEdit && <Link className="button-link secondary" to={`/projects/${project.slug}/edit`}>수정</Link>}
      </div>
    </article>
  )
}
