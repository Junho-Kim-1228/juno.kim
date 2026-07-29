import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { postApi } from '../api/posts'
import { projectApi } from '../api/projects'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { PostCard } from '../components/PostCard'
import { ProjectCard } from '../components/ProjectCard'

export function DeveloperPage() {
  const [data, setData] = useState({ projects: [], posts: [] })
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([projectApi.list(), postApi.list({ kind: 'technical' })]).then(([projects, posts]) => setData({ projects: projects.slice(0, 4), posts: posts.slice(0, 4) })).catch(setError).finally(() => setLoading(false))
  }, [])

  if (error) return <ErrorState error={error} />
  if (loading) return <LoadingState />
  return <>
    <section className="developer-intro page-section"><p className="eyebrow">개발자</p><h1>김준호</h1><p>개인적으로 만든 것과, 만들면서 정리한 기술 기록을 모아 둡니다.</p><a href="https://github.com/Junho-Kim-1228" target="_blank" rel="noreferrer">GitHub 바로가기</a></section>
    <section className="page-section"><div className="section-heading"><div><p className="eyebrow">프로젝트</p><h2>만든 것들</h2></div><Link to="/projects">전체 보기</Link></div>{data.projects.length ? <div className="card-grid">{data.projects.map((project) => <ProjectCard key={project.id} project={project} />)}</div> : <p className="empty-row">정리 중입니다.</p>}</section>
    <section className="page-section"><div className="section-heading"><div><p className="eyebrow">기술 기록</p><h2>개발하며 남긴 메모</h2></div><Link to="/records">전체 보기</Link></div>{data.posts.length ? <div className="card-grid">{data.posts.map((post) => <PostCard basePath="/blog" key={post.id} post={post} />)}</div> : <p className="empty-row">아직 기록이 없습니다.</p>}</section>
  </>
}
