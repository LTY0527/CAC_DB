import { useEffect, useState } from 'react'
import {
  fetchEmploymentSummary,
  fetchSalaryForecast,
  fetchEnrollmentMatching,
  fetchMajorMatchingRules,
  fetchJobRecommendation,
} from '../services/dataService'

export default function usePlatformData() {
  const [employmentData, setEmploymentData] = useState([])
  const [forecastData, setForecastData] = useState([])
  const [enrollmentData, setEnrollmentData] = useState([])
  const [rulesData, setRulesData] = useState([])
  const [recommendationData, setRecommendationData] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadAllData = async () => {
      try {
        setLoading(true)
        setError('')

        const [
          employmentRes,
          forecastRes,
          enrollmentRes,
          rulesRes,
          recommendationRes,
        ] = await Promise.all([
          fetchEmploymentSummary(),
          fetchSalaryForecast(),
          fetchEnrollmentMatching(),
          fetchMajorMatchingRules(),
          fetchJobRecommendation(),
        ])

        setEmploymentData(employmentRes.data.data || [])
        setForecastData(forecastRes.data.data || [])
        setEnrollmentData(enrollmentRes.data.data || [])
        setRulesData(rulesRes.data.data || [])
        setRecommendationData(recommendationRes.data.data || [])
      } catch (err) {
        console.error(err)
        setError('数据加载失败，请检查后端服务或 JSON 文件。')
      } finally {
        setLoading(false)
      }
    }

    loadAllData()
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