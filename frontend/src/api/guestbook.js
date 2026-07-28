import { authApi } from './auth'
import { apiClient } from './client'

const unwrap = (data) => data.results || data

export const guestbookApi = {
  async list() {
    const { data } = await apiClient.get('/guestbook/')
    return unwrap(data)
  },
  async create(payload) {
    await authApi.csrf()
    const { data } = await apiClient.post('/guestbook/', payload)
    return data
  },
}
