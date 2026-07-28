import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { projectApi } from '../api/projects'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { GuestbookSection } from '../components/GuestbookSection'
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
        <p className="eyebrow">JUNO KIM</p>
        <h1>김준호</h1>
        <p className="hero-copy">재미로 만들고, 배우고, 기록합니다.</p>
        <div className="hero-actions">
          <Link to="/projects">Projects</Link>
          <Link to="/blog">Writing</Link>
          <a href="#about">About</a>
        </div>
      </section>
      {error && <ErrorState error={error} />}
      {loading ? <LoadingState /> : (
        <>
          <section className="page-section">
            <div className="section-heading"><div><p className="eyebrow">PROJECTS</p><h2>프로젝트</h2></div><Link to="/projects">모두 보기</Link></div>
            {data.projects.length > 0 ? (
              <div className="card-grid">{data.projects.map((project) => <ProjectCard key={project.id} project={project} />)}</div>
            ) : <p className="empty-row">정리 중인 프로젝트가 곧 추가됩니다.</p>}
          </section>
          <section className="page-section">
            <div className="section-heading"><div><p className="eyebrow">RECENT WRITING</p><h2>최근 기록</h2></div><Link to="/blog">모두 보기</Link></div>
            {data.posts.length > 0 ? (
              <div className="card-grid">{data.posts.map((post) => <PostCard key={post.id} post={post} />)}</div>
            ) : <p className="empty-row">첫 번째 기록을 준비하고 있습니다.</p>}
          </section>
        </>
      )}
      <section className="about-section page-section" id="about">
        <div>
          <p className="eyebrow">ABOUT ME</p>
          <h2>김준호입니다.</h2>
        </div>
        <div className="about-copy">
          <p>재미로 만든 프로젝트와 그 과정에서 배운 것들을 가볍게 기록하는 개인 공간입니다.</p>
          <div className="about-links">
            <a href="https://github.com/Junho-Kim-1228" target="_blank" rel="noreferrer">GitHub</a>
            <a href="mailto:wnsgh1228_@naver.com">Email</a>
          </div>
        </div>
      </section>
      <GuestbookSection />
    </>
  )
}
