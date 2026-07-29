import { apiClient } from './client'

export const todayStatusApi = {
  async get() {
    const { data } = await apiClient.get('/today-status/')
    return data
  },
}
