import { Link } from 'react-router-dom'

export function ProjectCard({ project }) {
  return (
    <article className="card">
      <div className="card-meta">
        <span>{project.status === 'published' ? '공개' : '초안'}</span>
        {project.is_featured && <span>대표</span>}
      </div>
      <h3><Link to={`/projects/${project.slug}`}>{project.title}</Link></h3>
      <p>{project.summary}</p>
      <div className="chip-row">
        {project.technologies.map((technology) => <span className="chip" key={technology}>{technology}</span>)}
      </div>
    </article>
  )
}
