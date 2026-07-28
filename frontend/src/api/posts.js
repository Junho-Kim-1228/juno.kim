import { apiClient } from './client'

const unwrap = (data) => data.results || data

export const postApi = {
  async list() {
    const { data } = await apiClient.get('/posts/')
    return unwrap(data)
  },
  async detail(slug) {
    const { data } = await apiClient.get(`/posts/${slug}/`)
    return data
  },
  async create(payload) {
    const { data } = await apiClient.post('/posts/', payload)
    return data
  },
  async update(slug, payload) {
    const { data } = await apiClient.patch(`/posts/${slug}/`, payload)
    return data
  },
  async categories() {
    const { data } = await apiClient.get('/categories/')
    return unwrap(data)
  },
  async tags() {
    const { data } = await apiClient.get('/tags/')
    return unwrap(data)
  },
}
