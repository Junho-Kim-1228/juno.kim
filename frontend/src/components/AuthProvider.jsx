import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { authApi } from '../api/auth'
import { AuthContext } from '../hooks/authContext'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const didBootstrap = useRef(false)

  const reloadUser = useCallback(async () => {
    const currentUser = await authApi.me()
    setUser(currentUser)
    return currentUser
  }, [])

  useEffect(() => {
    if (didBootstrap.current) return
    didBootstrap.current = true

    const bootstrap = async () => {
      try {
        await authApi.refresh()
        await reloadUser()
      } catch {
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    const handleExpired = () => setUser(null)
    window.addEventListener('auth:expired', handleExpired)
    bootstrap()
    return () => window.removeEventListener('auth:expired', handleExpired)
  }, [reloadUser])

  const value = useMemo(
    () => ({
      user,
      loading,
      async login(credentials) {
        const currentUser = await authApi.login(credentials)
        setUser(currentUser)
        return currentUser
      },
      async register(payload) {
        await authApi.register(payload)
        const currentUser = await authApi.login({ username: payload.username, password: payload.password })
        setUser(currentUser)
        return currentUser
      },
      async logout() {
        await authApi.logout()
        setUser(null)
      },
      reloadUser,
    }),
    [loading, reloadUser, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
