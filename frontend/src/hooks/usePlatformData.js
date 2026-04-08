import { useEffect, useState } from 'react'
import {
  fetchEmploymentSummary,
  fetchEnrollmentMatching,
  fetchJobRecommendation,
  fetchMajorMatchingRules,
  fetchSalaryForecast,
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
        fetchEnrollmentMatching(),
        fetchMajorMatchingRules(),
        fetchJobRecommendation(),
      ])

      if (!alive) return

      const [
        employmentRes,
        forecastRes,
        enrollmentRes,
        rulesRes,
        recommendationRes,
      ] = results

      setEmploymentData(ensureList(employmentRes.status === 'fulfilled' ? employmentRes.value : []))
      setForecastData(ensureList(forecastRes.status === 'fulfilled' ? forecastRes.value : []))
      setEnrollmentData(ensureList(enrollmentRes.status === 'fulfilled' ? enrollmentRes.value : []))
      setRulesData(ensureList(rulesRes.status === 'fulfilled' ? rulesRes.value : []))
      setRecommendationData(
        ensureList(recommendationRes.status === 'fulfilled' ? recommendationRes.value : [])
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
    enrollmentData,
    rulesData,
    recommendationData,
    loading,
    error,
  }
}
