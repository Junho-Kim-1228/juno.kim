import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { projectApi } from '../api/projects'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { PostCard } from '../components/PostCard'
import { ProjectCard } from '../components/ProjectCard'

export function HomePage() {
  const [data, setData] = useState({ projects: [], posts: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([projectApi.list(), postApi.list()])
      .then(([projects, posts]) => setData({ projects: projects.slice(0, 3), posts: posts.slice(0, 3) }))
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <section className="hero-section page-section">
        <p className="eyebrow">JUNO.KIM</p>
        <h1>프로젝트와 기록</h1>
        <div className="hero-actions">
          <Link className="button-link" to="/projects">프로젝트 보기</Link>
          <Link className="button-link secondary" to="/blog">기록 보기</Link>
        </div>
      </section>
      {error && <ErrorState error={error} />}
      {loading ? <LoadingState /> : (
        <>
          <section className="page-section">
            <div className="section-heading"><div><p className="eyebrow">SELECTED WORK</p><h2>프로젝트</h2></div><Link to="/projects">전체 보기</Link></div>
            <div className="card-grid">{data.projects.map((project) => <ProjectCard key={project.id} project={project} />)}</div>
          </section>
          <section className="page-section">
            <div className="section-heading"><div><p className="eyebrow">WRITING</p><h2>최근 기록</h2></div><Link to="/blog">전체 보기</Link></div>
            <div className="card-grid">{data.posts.map((post) => <PostCard key={post.id} post={post} />)}</div>
          </section>
        </>
      )}
    </>
  )
}
