import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:5000/api',
  timeout: 120000,
})

export const fetchEmploymentSummary = () => api.get('/employment-summary')
export const fetchSalaryForecast = () => api.get('/salary-forecast')
export const fetchEnrollmentMatching = () => api.get('/enrollment-matching')
export const fetchMajorMatchingRules = () => api.get('/major-matching-rules')
export const fetchJobRecommendation = () => api.get('/job-recommendation')

export const generateEmploymentInsight = (payload) => api.post('/llm/employment-insight', payload)
export const generateReport = (payload) => api.post('/report/generate', payload)

export default api