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
        <p className="eyebrow">FULL-STACK DEVELOPER · CLOUD OPERATOR</p>
        <h1>제품을 만들고,<br />운영 가능한 시스템으로 다듬습니다.</h1>
        <p className="hero-copy">React와 Django로 사용자 경험을 만들고, AWS Linux에서 안전하게 운영한 과정과 배움을 기록합니다.</p>
        <div className="hero-actions">
          <Link className="button-link" to="/projects">프로젝트 보기</Link>
          <Link className="button-link secondary" to="/blog">기술 기록 읽기</Link>
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
