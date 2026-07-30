import { Link } from 'react-router-dom'

export function GamesPage() {
  return <section className="games-page page-section">
    <div className="section-heading">
      <div><p className="eyebrow">GAMES</p><h1>미니 게임</h1></div>
    </div>
    <div className="game-list">
      <Link className="game-card" to="/games/aim"><span className="game-card-mark">◎</span><span><strong>숫자 빨리 누르기</strong><small>1부터 20까지 빠르게 누르세요.</small></span></Link>
      <Link className="game-card" to="/games/reaction">
        <span className="game-card-mark" aria-hidden="true">●</span>
        <span><strong>반응속도 게임</strong><small>색이 바뀌는 순간 눌러 보세요. 최고 기록은 전체 랭킹에 남습니다.</small></span>
      </Link>
    </div>
  </section>
}
