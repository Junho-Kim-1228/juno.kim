import { Link } from 'react-router-dom'

function formatMonth(value) {
  return value ? value.slice(0, 7).replace('-', '.') : null
}

export function ProjectCard({ project }) {
  const start = formatMonth(project.started_on)
  const end = formatMonth(project.ended_on)
  const period = start ? `${start} – ${end || '진행 중'}` : '기간 미정'
  const status = project.status === 'archived'
    ? '보관'
    : end ? '완료' : start ? '진행 중' : '준비 중'

  return (
    <article className="card project-card">
      <div className="card-main">
        <h3><Link to={`/projects/${project.slug}`}>{project.title}</Link></h3>
        <p>{project.summary}</p>
      </div>
      <div className="project-details">
        <div className="chip-row">
          {project.technologies.map((technology) => <span className="chip" key={technology}>{technology}</span>)}
        </div>
        <div className="card-meta">
          <span>{period}</span>
          <span className="status-label">{status}</span>
        </div>
      </div>
    </article>
  )
}
