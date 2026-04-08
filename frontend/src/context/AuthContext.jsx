import { createContext, useContext, useMemo, useState } from 'react'
import {
  clearStoredSession,
  getMockAccounts,
  getStoredSession,
  loginWithMockAccount,
  storeSession,
} from '../utils/mockAuth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(() => getStoredSession())

  const value = useMemo(
    () => ({
      session,
      isAuthenticated: Boolean(session),
      accounts: getMockAccounts(),
      login(username, password) {
        const nextSession = loginWithMockAccount(username, password)
        if (!nextSession) return null
        storeSession(nextSession)
        setSession(nextSession)
        return nextSession
      },
      logout() {
        clearStoredSession()
        setSession(null)
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
