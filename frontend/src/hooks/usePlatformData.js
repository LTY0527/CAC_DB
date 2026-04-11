import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  fetchEmploymentSummary,
  fetchEnrollmentMatching,
  fetchEnrollmentMatchingEvaluation,
  fetchJobRecommendation,
  fetchJobRecommendationEvaluation,
  fetchMajorStructureAdvice,
  fetchMajorMatchingRules,
  fetchModelMetrics,
  fetchRegionalWarnings,
  fetchSalaryForecast,
  fetchSalaryForecastEvaluation,
  fetchTrainingProgramOptimization,
} from '../services/dataService'

function ensureList(value) {
  return Array.isArray(value) ? value : []
}

function buildRoleRequests(role) {
  const requests = [{ key: 'employmentData', loader: fetchEmploymentSummary }]

  if (role === 'teacher' || role === 'gov') {
    requests.push(
      { key: 'forecastData', loader: fetchSalaryForecast },
      { key: 'forecastEvalData', loader: fetchSalaryForecastEvaluation },
      { key: 'rulesData', loader: fetchMajorMatchingRules },
      { key: 'recommendationData', loader: fetchJobRecommendation },
      { key: 'jobRecommendationEvalData', loader: fetchJobRecommendationEvaluation },
      { key: 'trainingProgramData', loader: fetchTrainingProgramOptimization },
      { key: 'majorStructureAdviceData', loader: fetchMajorStructureAdvice },
      { key: 'modelMetricsData', loader: fetchModelMetrics }
    )
  }

  if (role === 'teacher') {
    requests.push(
      { key: 'enrollmentData', loader: fetchEnrollmentMatching },
      { key: 'enrollmentEvalData', loader: fetchEnrollmentMatchingEvaluation }
    )
  }

  if (role === 'gov') {
    requests.push({ key: 'regionalWarningsData', loader: fetchRegionalWarnings })
  }

  return requests
}

const DEFAULT_STATE = {
  employmentData: [],
  forecastData: [],
  enrollmentData: [],
  rulesData: [],
  recommendationData: [],
  trainingProgramData: [],
  majorStructureAdviceData: {},
  forecastEvalData: {},
  enrollmentEvalData: [],
  jobRecommendationEvalData: [],
  modelMetricsData: [],
  regionalWarningsData: {},
}

export default function usePlatformData() {
  const { session } = useAuth()
  const role = session?.role
  const requests = useMemo(() => buildRoleRequests(role), [role])

  const [employmentData, setEmploymentData] = useState([])
  const [forecastData, setForecastData] = useState([])
  const [enrollmentData, setEnrollmentData] = useState([])
  const [rulesData, setRulesData] = useState([])
  const [recommendationData, setRecommendationData] = useState([])
  const [trainingProgramData, setTrainingProgramData] = useState([])
  const [majorStructureAdviceData, setMajorStructureAdviceData] = useState({})
  const [forecastEvalData, setForecastEvalData] = useState({})
  const [enrollmentEvalData, setEnrollmentEvalData] = useState([])
  const [jobRecommendationEvalData, setJobRecommendationEvalData] = useState([])
  const [modelMetricsData, setModelMetricsData] = useState([])
  const [regionalWarningsData, setRegionalWarningsData] = useState({})
  const [dataLoadedAt, setDataLoadedAt] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true

    async function loadAllData() {
      if (!role) {
        setLoading(false)
        return
      }

      setLoading(true)
      setError('')

      const results = await Promise.allSettled(requests.map((item) => item.loader()))
      if (!alive) return

      const nextState = { ...DEFAULT_STATE }
      const failedKeys = []

      requests.forEach((requestItem, index) => {
        const result = results[index]
        if (result?.status === 'fulfilled') {
          const value = result.value
          switch (requestItem.key) {
            case 'employmentData':
            case 'forecastData':
            case 'enrollmentData':
            case 'rulesData':
            case 'recommendationData':
            case 'trainingProgramData':
            case 'enrollmentEvalData':
            case 'jobRecommendationEvalData':
            case 'modelMetricsData':
              nextState[requestItem.key] = ensureList(value)
              break
            default:
              nextState[requestItem.key] = value || {}
          }
        } else {
          failedKeys.push(requestItem.key)
        }
      })

      setEmploymentData(nextState.employmentData)
      setForecastData(nextState.forecastData)
      setForecastEvalData(nextState.forecastEvalData)
      setEnrollmentData(nextState.enrollmentData)
      setEnrollmentEvalData(nextState.enrollmentEvalData)
      setRulesData(nextState.rulesData)
      setRecommendationData(nextState.recommendationData)
      setJobRecommendationEvalData(nextState.jobRecommendationEvalData)
      setTrainingProgramData(nextState.trainingProgramData)
      setMajorStructureAdviceData(nextState.majorStructureAdviceData)
      setModelMetricsData(nextState.modelMetricsData)
      setRegionalWarningsData(nextState.regionalWarningsData)
      setDataLoadedAt(
        new Date().toLocaleString('zh-CN', {
          hour12: false,
        })
      )

      if (failedKeys.length) {
        setError('部分模块数据暂未返回，当前页面已使用可用数据继续渲染。')
      }

      setLoading(false)
    }

    loadAllData()

    return () => {
      alive = false
    }
  }, [requests, role])

  return {
    employmentData,
    forecastData,
    forecastEvalData,
    enrollmentData,
    enrollmentEvalData,
    rulesData,
    recommendationData,
    jobRecommendationEvalData,
    trainingProgramData,
    majorStructureAdviceData,
    modelMetricsData,
    regionalWarningsData,
    dataLoadedAt,
    loading,
    error,
  }
}
