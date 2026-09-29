import React, { useState, useEffect, useCallback } from 'react'
import { AuthContext } from './authStore'
import { authApi, storeAuthTokens, clearAuthTokens, tokenStorage } from '../services/api'
import type { User } from '../types'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = tokenStorage.get()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }
    try {
      const resp = await authApi.me()
      setUser(resp.data)
    } catch {
      clearAuthTokens()
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const resp = await authApi.login(email, password)
    const { access_token, refresh_token } = resp.data
    storeAuthTokens(access_token, refresh_token)
    await refreshUser()
  }, [refreshUser])

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      clearAuthTokens()
      setUser(null)
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
