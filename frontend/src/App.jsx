import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import EmploymentMonitor from './pages/EmploymentMonitor'
import SalaryForecast from './pages/SalaryForecast'
import EnrollmentMatching from './pages/EnrollmentMatching'
import RuleAnalysis from './pages/RuleAnalysis'
import MajorOptimization from './pages/MajorOptimization'
import AIReport from './pages/AIReport'
import LoginPage from './pages/LoginPage'
import RoleWorkspace from './pages/RoleWorkspace'
import JobRecommendation from './pages/JobRecommendation'
import LayoutComponent from './layouts/LayoutComponent'
import { AuthProvider, useAuth } from './context/AuthContext'
import { RequireAuth, RequireRole } from './routes/RouteGuard'
import usePlatformPageData from './hooks/usePlatformPageData'
import { getDefaultPathByRole } from './config/roleConfig.jsx'

function RoleHomeRedirect() {
  const { session } = useAuth()
  return <Navigate to={getDefaultPathByRole(session?.role)} replace />
}

function DashboardRoute() {
  const pageData = usePlatformPageData()
  return pageData.roleMode === 'public'
    ? <RoleWorkspace {...pageData} />
    : <Dashboard {...pageData} />
}

function EmploymentRoute() {
  return <EmploymentMonitor {...usePlatformPageData()} />
}

function ForecastRoute() {
  return <SalaryForecast {...usePlatformPageData()} />
}

function EnrollmentRoute() {
  return <EnrollmentMatching {...usePlatformPageData()} />
}

function RulesRoute() {
  return <RuleAnalysis {...usePlatformPageData()} />
}

function JobRecommendationRoute() {
  return <JobRecommendation {...usePlatformPageData()} />
}

function MajorOptimizationRoute() {
  return <MajorOptimization {...usePlatformPageData()} />
}

function ReportRoute() {
  return <AIReport {...usePlatformPageData()} />
}

function WorkspaceRoute() {
  return <RoleWorkspace {...usePlatformPageData()} />
}

export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<RequireAuth />}>
            <Route element={<LayoutComponent />}>
              <Route index element={<RoleHomeRedirect />} />
              <Route path="/dashboard" element={<DashboardRoute />} />
              <Route
                path="/employment"
                element={
                  <RequireRole roles={['teacher', 'gov']}>
                    <EmploymentRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/forecast"
                element={
                  <RequireRole roles={['teacher', 'gov']}>
                    <ForecastRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/enrollment"
                element={
                  <RequireRole roles={['teacher']}>
                    <EnrollmentRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/rules"
                element={
                  <RequireRole roles={['teacher', 'gov']}>
                    <RulesRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/job-recommendation"
                element={
                  <RequireRole roles={['teacher', 'gov']}>
                    <JobRecommendationRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/major-optimization"
                element={
                  <RequireRole roles={['teacher', 'gov']}>
                    <MajorOptimizationRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/report"
                element={
                  <RequireRole roles={['teacher', 'gov']}>
                    <ReportRoute />
                  </RequireRole>
                }
              />
              <Route
                path="/school-compare"
                element={
                  <RequireRole roles={['public']}>
                    <WorkspaceRoute />
                  </RequireRole>
                }
              />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </HashRouter>
    </AuthProvider>
  )
}
