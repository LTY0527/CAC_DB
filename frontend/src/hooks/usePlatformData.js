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
  fetchDemandForecast,
  fetchDemandForecastEvaluation,
  fetchSupplyDemandGap,
  fetchJobSkillsHeatmap,
  fetchTrainingProgramOptimization,
  fetchPublicSalaryRanking,
} from '../services/dataService'

function ensureList(value) {
  return Array.isArray(value) ? value : []
}

function buildRoleRequests(role) {
  const requests = [{ key: 'employmentData', loader: fetchEmploymentSummary }]

  if (role === 'teacher' || role === 'gov') {
    requests.push(
      { key: 'forecastData', loader: fetchDemandForecast },
      { key: 'forecastEvalData', loader: fetchDemandForecastEvaluation },
      { key: 'supplyDemandGapData', loader: fetchSupplyDemandGap },
      { key: 'jobSkillsHeatmapData', loader: fetchJobSkillsHeatmap },
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

  if (role === 'public') {
    requests.push({ key: 'publicSalaryRankingData', loader: () => fetchPublicSalaryRanking(10) })
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
  supplyDemandGapData: [],
  jobSkillsHeatmapData: [],
  publicSalaryRankingData: [],
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
  const [supplyDemandGapData, setSupplyDemandGapData] = useState([])
  const [jobSkillsHeatmapData, setJobSkillsHeatmapData] = useState([])
  const [publicSalaryRankingData, setPublicSalaryRankingData] = useState([])
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
            case 'supplyDemandGapData':
            case 'jobSkillsHeatmapData':
            case 'publicSalaryRankingData': {
              const payload = value?.items ?? value
              nextState[requestItem.key] = ensureList(payload)
              break
            }
            default:
              nextState[requestItem.key] = value || {}
          }
        } else {
          failedKeys.push(requestItem.key)
          console.warn(`${requestItem.key} 加载失败`, result?.reason)
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
      setSupplyDemandGapData(nextState.supplyDemandGapData)
      setJobSkillsHeatmapData(nextState.jobSkillsHeatmapData)
      setPublicSalaryRankingData(nextState.publicSalaryRankingData)
      setDataLoadedAt(
        new Date().toLocaleString('zh-CN', {
          hour12: false,
        })
      )

      setError(failedKeys.includes('employmentData') ? '核心数据暂未返回，请检查后端服务或数据库连接。' : '')

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
    supplyDemandGapData,
    jobSkillsHeatmapData,
    publicSalaryRankingData,
    dataLoadedAt,
    loading,
    error,
  }
}
