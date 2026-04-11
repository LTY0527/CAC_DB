import axios from 'axios'
import { message } from 'antd'
import { clearStoredSession, getStoredSession } from '../utils/mockAuth'

const ERROR_DEBOUNCE_MS = 1800
let lastErrorAt = 0

function showGlobalError(content) {
  const now = Date.now()
  if (now - lastErrorAt < ERROR_DEBOUNCE_MS) return
  lastErrorAt = now
  message.error(content)
}

export const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const session = getStoredSession()
  if (session?.token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${session.token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearStoredSession()
    }

    if (error?.response?.status >= 500) {
      showGlobalError('后端服务异常，请检查 Flask 服务或数据库连接。')
    } else if (error?.code === 'ECONNABORTED') {
      showGlobalError('接口请求超时，请稍后重试。')
    } else if (!error?.response) {
      showGlobalError('网络连接失败，请确认前后端服务已启动。')
    }

    return Promise.reject(error)
  }
)

function ensurePayload(response) {
  return response?.data?.data || []
}

export async function login(payload) {
  const response = await api.post('/auth/login', payload)
  return response?.data?.data || null
}

export async function logout() {
  await api.post('/auth/logout')
}

export async function fetchAuthMe() {
  const response = await api.get('/auth/me')
  return response?.data?.data || null
}

export async function logModuleAccess(payload) {
  const response = await api.post('/auth/access-log', payload)
  return response?.data?.data || null
}

export async function fetchAuditLogs(params = {}) {
  const response = await api.get('/audit-logs', { params })
  return response?.data?.data || {}
}

export async function fetchEmploymentSummary() {
  const response = await api.get('/employment-summary')
  return ensurePayload(response)
}

export async function fetchSalaryForecast() {
  const response = await api.get('/salary-forecast')
  return ensurePayload(response)
}

export async function fetchSalaryForecastEvaluation() {
  const response = await api.get('/salary-forecast-evaluation')
  return ensurePayload(response)
}

export async function fetchEnrollmentMatching() {
  const response = await api.get('/enrollment-matching')
  return ensurePayload(response)
}

export async function fetchEnrollmentMatchingEvaluation() {
  const response = await api.get('/enrollment-matching-evaluation')
  return ensurePayload(response)
}

export async function fetchMajorMatchingRules() {
  const response = await api.get('/major-matching-rules')
  return ensurePayload(response)
}

export async function fetchTrainingProgramOptimization() {
  const response = await api.get('/training-program-optimization')
  return ensurePayload(response)
}

export async function fetchMajorStructureAdvice() {
  const response = await api.get('/major-structure-advice')
  return response?.data?.data || {}
}

export async function fetchJobRecommendation() {
  const response = await api.get('/job-recommendation')
  return ensurePayload(response)
}

export async function fetchJobRecommendationEvaluation() {
  const response = await api.get('/job-recommendation-evaluation')
  return ensurePayload(response)
}

export async function fetchModelMetrics() {
  const response = await api.get('/model-metrics')
  return ensurePayload(response)
}

export async function fetchRegionalWarnings() {
  const response = await api.get('/regional-warnings')
  return response?.data?.data || {}
}

export async function fetchGovSchoolDetail(schoolName) {
  const response = await api.get('/gov/school-detail', {
    params: { school_name: schoolName },
  })
  return response?.data?.data || {}
}

export async function fetchGovMajorDetail(schoolName, majorName) {
  const response = await api.get('/gov/major-detail', {
    params: { school_name: schoolName, major_name: majorName },
  })
  return response?.data?.data || {}
}

export async function fetchGovSchoolBenchmarkOverview() {
  const response = await api.get('/gov/school-benchmark-overview')
  return response?.data?.data || {}
}

export async function fetchGovSchoolBenchmarkMajor(majorName) {
  const response = await api.get('/gov/school-benchmark-major', {
    params: { major_name: majorName },
  })
  return response?.data?.data || {}
}

export const generateEmploymentInsight = (payload) => api.post('/llm/employment-insight', payload)
export const generateReport = (payload) => api.post('/report/generate', payload)

export default api
