import { useEffect, useState } from 'react'
import {
  fetchEmploymentSummary,
  fetchEnrollmentMatching,
  fetchEnrollmentMatchingEvaluation,
  fetchJobRecommendation,
  fetchJobRecommendationEvaluation,
  fetchMajorMatchingRules,
  fetchModelMetrics,
  fetchSalaryForecast,
  fetchSalaryForecastEvaluation,
  fetchTrainingProgramOptimization,
} from '../services/dataService'

function ensureList(value) {
  return Array.isArray(value) ? value : []
}

export default function usePlatformData() {
  const [employmentData, setEmploymentData] = useState([])
  const [forecastData, setForecastData] = useState([])
  const [enrollmentData, setEnrollmentData] = useState([])
  const [rulesData, setRulesData] = useState([])
  const [recommendationData, setRecommendationData] = useState([])
  const [trainingProgramData, setTrainingProgramData] = useState([])
  const [forecastEvalData, setForecastEvalData] = useState({})
  const [enrollmentEvalData, setEnrollmentEvalData] = useState([])
  const [jobRecommendationEvalData, setJobRecommendationEvalData] = useState([])
  const [modelMetricsData, setModelMetricsData] = useState([])
  const [dataLoadedAt, setDataLoadedAt] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true

    async function loadAllData() {
      setLoading(true)
      setError('')

      const results = await Promise.allSettled([
        fetchEmploymentSummary(),
        fetchSalaryForecast(),
        fetchSalaryForecastEvaluation(),
        fetchEnrollmentMatching(),
        fetchEnrollmentMatchingEvaluation(),
        fetchMajorMatchingRules(),
        fetchJobRecommendation(),
        fetchJobRecommendationEvaluation(),
        fetchTrainingProgramOptimization(),
        fetchModelMetrics(),
      ])

      if (!alive) return

      const [
        employmentRes,
        forecastRes,
        forecastEvalRes,
        enrollmentRes,
        enrollmentEvalRes,
        rulesRes,
        recommendationRes,
        recommendationEvalRes,
        trainingProgramRes,
        modelMetricsRes,
      ] = results

      setEmploymentData(ensureList(employmentRes.status === 'fulfilled' ? employmentRes.value : []))
      setForecastData(ensureList(forecastRes.status === 'fulfilled' ? forecastRes.value : []))
      setForecastEvalData(forecastEvalRes.status === 'fulfilled' ? (forecastEvalRes.value || {}) : {})
      setEnrollmentData(ensureList(enrollmentRes.status === 'fulfilled' ? enrollmentRes.value : []))
      setEnrollmentEvalData(ensureList(enrollmentEvalRes.status === 'fulfilled' ? enrollmentEvalRes.value : []))
      setRulesData(ensureList(rulesRes.status === 'fulfilled' ? rulesRes.value : []))
      setRecommendationData(
        ensureList(recommendationRes.status === 'fulfilled' ? recommendationRes.value : [])
      )
      setJobRecommendationEvalData(
        ensureList(recommendationEvalRes.status === 'fulfilled' ? recommendationEvalRes.value : [])
      )
      setTrainingProgramData(
        ensureList(trainingProgramRes.status === 'fulfilled' ? trainingProgramRes.value : [])
      )
      setModelMetricsData(
        ensureList(modelMetricsRes.status === 'fulfilled' ? modelMetricsRes.value : [])
      )
      setDataLoadedAt(
        new Date().toLocaleString('zh-CN', {
          hour12: false,
        })
      )

      const hasFailure = results.some((item) => item.status === 'rejected')
      if (hasFailure) {
        setError('部分数据加载失败，当前页面已使用可用数据继续渲染。')
      }

      setLoading(false)
    }

    loadAllData()

    return () => {
      alive = false
    }
  }, [])

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
    modelMetricsData,
    dataLoadedAt,
    loading,
    error,
  }
}
