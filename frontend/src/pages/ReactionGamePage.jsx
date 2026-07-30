import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { gamesApi } from '../api/games'
import { ErrorState, LoadingState } from '../components/AsyncState'
import { useAuth } from '../hooks/useAuth'

function scoreLabel(score) {
  return `${score.reaction_ms}ms`
}

export function ReactionGamePage() {
  const { user } = useAuth()
  const [gameState, setGameState] = useState('idle')
  const [challengeId, setChallengeId] = useState(null)
  const [result, setResult] = useState(null)
  const [leaderboard, setLeaderboard] = useState({ results: [], my_score: null })
  const [loadingBoard, setLoadingBoard] = useState(true)
  const [error, setError] = useState(null)
  const timerRef = useRef(null)

  const loadLeaderboard = async () => {
    setLoadingBoard(true)
    try {
      setLeaderboard(await gamesApi.leaderboard())
    } catch (requestError) {
      setError(requestError)
    } finally {
      setLoadingBoard(false)
    }
  }

  useEffect(() => {
    loadLeaderboard()
    return () => window.clearTimeout(timerRef.current)
  }, [])

  const startGame = async () => {
    if (!user || !user.email_verified) return
    window.clearTimeout(timerRef.current)
    setError(null)
    setResult(null)
    setGameState('starting')
    try {
      const challenge = await gamesApi.startReactionChallenge()
      setChallengeId(challenge.challenge_id)
      setGameState('waiting')
      timerRef.current = window.setTimeout(() => setGameState('ready'), challenge.wait_ms)
    } catch (requestError) {
      setGameState('idle')
      setError(requestError)
    }
  }

  const react = async () => {
    if (gameState === 'waiting') {
      window.clearTimeout(timerRef.current)
      setChallengeId(null)
      setGameState('too-soon')
      return
    }
    if (gameState !== 'ready' || !challengeId) return

    setGameState('submitting')
    try {
      const response = await gamesApi.submitReaction(challengeId)
      setResult(response)
      setGameState('complete')
      await loadLeaderboard()
    } catch (requestError) {
      setGameState('idle')
      setError(requestError)
    }
  }

  const instruction = {
    idle: '시작을 누르면 1~10초 뒤 화면이 초록색으로 바뀝니다.',
    starting: '게임을 준비하고 있어요.',
    waiting: '아직이에요. 초록색이 될 때까지 기다려 주세요.',
    ready: '지금!',
    submitting: '기록을 확인하고 있어요.',
    'too-soon': '너무 빨랐어요. 다시 시작해 주세요.',
    complete: result?.is_personal_best ? '내 최고 기록을 갱신했어요!' : '이번 기록이에요. 다시 도전해 볼까요?',
  }[gameState]

  return <section className="reaction-page page-section">
    <div className="section-heading">
      <div><p className="eyebrow">GAME 01</p><h1>반응속도 게임</h1><p className="page-description">계정마다 가장 빠른 기록 하나만 전체 랭킹에 남아요.</p></div>
      <Link to="/games">게임 목록</Link>
    </div>

    <div className="reaction-layout">
      <section className="reaction-game" aria-labelledby="reaction-play-heading">
        <h2 id="reaction-play-heading">준비됐나요?</h2>
        {!user ? <p className="game-auth-note">랭킹에 참여하려면 <Link to="/login">로그인</Link>해 주세요.</p> : !user.email_verified ? <p className="game-auth-note">랭킹에 참여하려면 이메일 인증이 필요합니다.</p> : <>
          <button type="button" className={`reaction-pad ${gameState}`} onClick={react} disabled={gameState === 'starting' || gameState === 'submitting'}>
            <span>{gameState === 'ready' ? 'CLICK!' : gameState === 'waiting' ? '...' : gameState === 'too-soon' ? '앗' : '준비'}</span>
          </button>
          <p className="reaction-instruction" aria-live="polite">{instruction}</p>
          {result && <p className="reaction-result">이번 기록 <strong>{result.reaction_ms}ms</strong>{result.my_score && <> · 내 최고 <strong>{scoreLabel(result.my_score)}</strong></>}</p>}
          <button type="button" className="button-link" onClick={startGame} disabled={gameState === 'starting' || gameState === 'waiting' || gameState === 'ready' || gameState === 'submitting'}>{gameState === 'complete' || gameState === 'too-soon' ? '다시 하기' : '시작'}</button>
        </>}
        {error && <ErrorState error={error} />}
      </section>

      <section className="reaction-ranking" aria-labelledby="reaction-ranking-heading">
        <div><p className="eyebrow">LEADERBOARD</p><h2 id="reaction-ranking-heading">전체 최고 기록</h2></div>
        {loadingBoard ? <LoadingState label="랭킹을 불러오는 중입니다." /> : leaderboard.results.length ? <ol className="reaction-ranking-list">{leaderboard.results.map((score) => <li key={score.user.username} className={score.user.username === user?.username ? 'mine' : ''}><span className="rank-number">{score.rank}</span><span><strong>{score.user.display_name}</strong> <small>(@{score.user.username})</small></span><time>{scoreLabel(score)}</time></li>)}</ol> : <p className="empty-row">아직 첫 기록이 없습니다.</p>}
        {leaderboard.my_score && <p className="my-rank">내 순위 <strong>{leaderboard.my_score.rank}위</strong> · {scoreLabel(leaderboard.my_score)}</p>}
      </section>
    </div>
  </section>
}
