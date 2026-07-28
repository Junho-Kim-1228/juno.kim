import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { projectApi } from '../api/projects'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { ProjectCard } from '../components/ProjectCard'
import { useAuth } from '../hooks/useAuth'

export function ProjectsPage() {
  const { user } = useAuth()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => { projectApi.list().then(setProjects).catch(setError).finally(() => setLoading(false)) }, [])

  return (
    <section className="page-section">
      <div className="section-heading"><div><p className="eyebrow">ARCHIVE</p><h1>프로젝트</h1></div>{user && <Link className="button-link small" to="/projects/new">프로젝트 추가</Link>}</div>
      {error && <ErrorState error={error} />}
      {loading ? <LoadingState /> : <div className="card-grid">{projects.map((project) => <ProjectCard key={project.id} project={project} />)}</div>}
    </section>
  )
}
