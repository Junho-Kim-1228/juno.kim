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
}
