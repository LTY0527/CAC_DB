/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { fetchAuthMe, login as loginRequest, logout as logoutRequest } from '../services/dataService'
import {
  clearStoredSession,
  getDemoAccounts,
  getStoredSession,
  storeSession,
} from '../utils/authStorage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => getStoredSession())

  const mergeSession = (baseSession, nextSession) => {
    if (!nextSession) return null
    return {
      ...baseSession,
      ...nextSession,
      token: nextSession.token || baseSession?.token || '',
    }
  }

  useEffect(() => {
    let alive = true

    async function validateStoredSession() {
      if (!session?.token) return
      try {
        const nextSession = await fetchAuthMe()
        if (!alive) return
        if (!nextSession) {
          clearStoredSession()
          setSession(null)
          return
        }
        setSession((previous) => {
          const mergedSession = mergeSession(previous, nextSession)
          if (!mergedSession?.token || !mergedSession?.role) {
            clearStoredSession()
            return null
          }
          storeSession(mergedSession)
          return mergedSession
        })
      } catch {
        if (!alive) return
        clearStoredSession()
        setSession(null)
      }
    }

    validateStoredSession()

    return () => {
      alive = false
    }
  }, [session?.token])

  const value = useMemo(
    () => ({
      session,
      isAuthenticated: Boolean(session?.token && session?.role),
      accounts: getDemoAccounts(),
      async login(username, password) {
        const nextSession = await loginRequest({ username, password })
        const mergedSession = mergeSession(null, nextSession)
        if (!mergedSession?.token || !mergedSession?.role) return null
        storeSession(mergedSession)
        setSession(mergedSession)
        return mergedSession
      },
      async logout() {
        try {
          if (session?.token) {
            await logoutRequest()
          }
        } catch {
          // ignore logout audit failures and still clear local session
        } finally {
          clearStoredSession()
          setSession(null)
        }
      },
      async refreshSession() {
        if (!session?.token) return null
        try {
          const nextSession = await fetchAuthMe()
          if (!nextSession) {
            clearStoredSession()
            setSession(null)
            return null
          }
          const mergedSession = mergeSession(session, nextSession)
          if (!mergedSession?.token || !mergedSession?.role) {
            clearStoredSession()
            setSession(null)
            return null
          }
          storeSession(mergedSession)
          setSession(mergedSession)
          return mergedSession
        } catch {
          clearStoredSession()
          setSession(null)
          return null
        }
      },
    }),
    [session]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
