import { apiClient } from './client'

export const projectApi = {
  async list() {
    const { data } = await apiClient.get('/projects/')
    return data.results || data
  },
  async detail(slug) {
    const { data } = await apiClient.get(`/projects/${slug}/`)
    return data
  },
  async create(payload) {
    const { data } = await apiClient.post('/projects/', payload)
    return data
  },
  async update(slug, payload) {
    const { data } = await apiClient.patch(`/projects/${slug}/`, payload)
    return data
  },
}
