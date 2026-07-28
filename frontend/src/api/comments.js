import { apiClient } from './client'

export const commentApi = {
  async list(postSlug) {
    const { data } = await apiClient.get('/comments/', { params: { post: postSlug } })
    return data.results || data
  },
  async create(payload) {
    const { data } = await apiClient.post('/comments/', payload)
    return data
  },
  async update(id, content) {
    const { data } = await apiClient.patch(`/comments/${id}/`, { content })
    return data
  },
  async remove(id) {
    await apiClient.delete(`/comments/${id}/`)
  },
}
