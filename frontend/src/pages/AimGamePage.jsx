import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { gamesApi } from '../api/games'
import { ErrorState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

export function AimGamePage() {
  const { user } = useAuth(); const [numbers, setNumbers] = useState([]); const [next, setNext] = useState(1); const [challenge, setChallenge] = useState(null); const [started, setStarted] = useState(0); const [penalty, setPenalty] = useState(0); const [board, setBoard] = useState({results:[]}); const [error, setError] = useState(null)
  const load = async () => setBoard(await gamesApi.aimLeaderboard()); useEffect(() => { load().catch(setError) }, [])
  const start = async () => { try { setChallenge((await gamesApi.startAim()).challenge_id); setNumbers(Array.from({length:20}, (_,i)=>i+1).sort(()=>Math.random()-.5)); setNext(1); setPenalty(0); setStarted(performance.now()); setError(null) } catch(e) { setError(e) } }
  const hit = async (number) => { if (!challenge) return; if (number !== next) { setPenalty(p=>p+500); return }; if (number < 20) { setNext(number+1); return }; try { const data = await gamesApi.submitAim(challenge, Math.round(performance.now()-started)+penalty); setChallenge(null); await load(); alert(data.is_personal_best ? '내 최고 기록!' : '완료!') } catch(e) { setError(e); setChallenge(null) } }
  return <section className="reaction-page page-section"><div className="section-heading"><div><p className="eyebrow">GAME 02</p><h1>에임 연습</h1><p className="page-description">1부터 20까지 순서대로 누르세요. 오클릭은 0.5초 추가입니다.</p></div><Link to="/games">게임 목록</Link></div>{!user ? <p className="game-auth-note">랭킹에 참여하려면 <Link to="/login">로그인</Link>해 주세요.</p> : <><button className="button-link" onClick={start}>{challenge ? '진행 중' : '시작'}</button><p className="reaction-instruction">다음 숫자: <strong>{next}</strong> · 패널티 {penalty/1000}초</p><div className="aim-board">{numbers.map(n=><button key={n} onClick={()=>hit(n)} className={n < next ? 'done' : ''}>{n}</button>)}</div></>}{error && <ErrorState error={error}/>}<section className="reaction-ranking"><h2>전체 랭킹</h2><ol className="reaction-ranking-list">{board.results.map(s=><li key={s.user.username}><span>{s.rank}</span><span>{s.user.display_name} (@{s.user.username})</span><time>{(s.score_ms/1000).toFixed(2)}초</time></li>)}</ol></section></section>
}
