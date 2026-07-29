import { apiClient } from './client'

export const contentImageApi = {
  async upload(file) {
    const payload = new FormData()
    payload.append('image', file)
    const { data } = await apiClient.post('/content-images/', payload)
    return data
  },
}
