import { Link } from 'react-router-dom'

export function GamesPage() {
  return <section className="games-page page-section">
    <div className="section-heading">
      <div><p className="eyebrow">GAMES</p><h1>작은 게임</h1><p className="page-description">가끔 들러서 한 판 하고 가도 좋아요.</p></div>
    </div>
    <div className="game-list">
      <Link className="game-card" to="/games/reaction">
        <span className="game-card-mark" aria-hidden="true">●</span>
        <span><strong>반응속도 게임</strong><small>색이 바뀌는 순간 눌러 보세요. 최고 기록은 전체 랭킹에 남습니다.</small></span>
        <span className="game-card-arrow" aria-hidden="true">→</span>
      </Link>
    </div>
  </section>
}
