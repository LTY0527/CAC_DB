import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getDefaultPathByRole } from '../config/roleConfig.jsx'

export function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children || <Outlet />
}

export function RequireRole({ roles = [], children }) {
  const { session } = useAuth()

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (roles.length > 0 && !roles.includes(session.role)) {
    return <Navigate to={getDefaultPathByRole(session.role)} replace />
  }

  return children || <Outlet />
}
