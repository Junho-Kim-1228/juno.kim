import { apiClient } from './client'

export const gamesApi = {
  async leaderboard() {
    const { data } = await apiClient.get('/games/reaction/leaderboard/')
    return data
  },
  async startReactionChallenge() {
    const { data } = await apiClient.post('/games/reaction/challenge/')
    return data
  },
  async submitReaction(challengeId) {
    const { data } = await apiClient.post('/games/reaction/submit/', { challenge_id: challengeId })
    return data
  },
  async aimLeaderboard() { const { data } = await apiClient.get('/games/aim/leaderboard/'); return data },
  async startAim() { const { data } = await apiClient.post('/games/aim/challenge/'); return data },
  async submitAim(challengeId, scoreMs) { const { data } = await apiClient.post('/games/aim/submit/', { challenge_id: challengeId, score_ms: scoreMs }); return data },
}
