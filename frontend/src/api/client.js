import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const axiosOptions = {
  baseURL,
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
}

export const apiClient = axios.create(axiosOptions)
const refreshClient = axios.create(axiosOptions)

let accessToken = null
let refreshPromise = null

export function setAccessToken(token) {
  accessToken = token || null
}

apiClient.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const requestUrl = originalRequest?.url || ''
    const isAuthRequest = ['/auth/login/', '/auth/register/', '/auth/refresh/'].some((path) =>
      requestUrl.includes(path),
    )

    if (error.response?.status !== 401 || originalRequest?._retry || isAuthRequest) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    if (!refreshPromise) {
      refreshPromise = refreshClient
        .post('/auth/refresh/')
        .then(({ data }) => {
          setAccessToken(data.access)
          return data.access
        })
        .catch((refreshError) => {
          setAccessToken(null)
          window.dispatchEvent(new Event('auth:expired'))
          throw refreshError
        })
        .finally(() => {
          refreshPromise = null
        })
    }

    const token = await refreshPromise
    originalRequest.headers.Authorization = `Bearer ${token}`
    return apiClient(originalRequest)
  },
)
