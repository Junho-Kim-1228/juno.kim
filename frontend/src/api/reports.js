import { authApi } from './auth'
import { apiClient } from './client'

export const reportApi = {
  async impersonation(targetType, targetId, reason) {
    await authApi.csrf()
    const { data } = await apiClient.post('/reports/impersonation/', {
      target_type: targetType,
      target_id: targetId,
      reason,
    })
    return data
  },
}
