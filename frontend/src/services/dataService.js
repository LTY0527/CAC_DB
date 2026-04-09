import axios from 'axios'
import { message } from 'antd'

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

api.interceptors.response.use(
  (response) => response,
  (error) => {
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

export const generateEmploymentInsight = (payload) => api.post('/llm/employment-insight', payload)
export const generateReport = (payload) => api.post('/report/generate', payload)

export default api
