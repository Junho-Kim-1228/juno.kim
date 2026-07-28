import { apiClient, setAccessToken } from './client'

export const authApi = {
  async csrf() {
    const { data } = await apiClient.get('/auth/csrf/')
    return data
  },
  async register(payload) {
    await this.csrf()
    const { data } = await apiClient.post('/auth/register/', payload)
    return data
  },
  async login(payload) {
    await this.csrf()
    const { data } = await apiClient.post('/auth/login/', payload)
    setAccessToken(data.access)
    return data.user
  },
  async refresh() {
    await this.csrf()
    const { data } = await apiClient.post('/auth/refresh/')
    setAccessToken(data.access)
    return data.access
  },
  async logout() {
    try {
      await this.csrf()
      await apiClient.post('/auth/logout/')
    } finally {
      setAccessToken(null)
    }
  },
  async me() {
    const { data } = await apiClient.get('/auth/me/')
    return data
  },
  async updateMe(payload) {
    const { data } = await apiClient.patch('/auth/me/', payload)
    return data
  },
  async updateProfile(payload) {
    const { data } = await apiClient.patch('/auth/profile/', payload)
    return data
  },
}
