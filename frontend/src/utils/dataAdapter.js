import {
  STATIC_ADMIN_STATUS,
  STATIC_FORECAST_DATA,
  STATIC_PUBLIC_INDUSTRIES,
  STATIC_PUBLIC_TOP_MAJORS,
  STATIC_RULES,
} from './mockData'

const TXT_STRATEGIC = '三大先导'
const TXT_NORMAL = '常规产业'
const TXT_ALL = '全部'
const TXT_UNKNOWN_SCHOOL = '上海大学'
const TXT_UNKNOWN_MAJOR = '未知专业'
const TXT_UNKNOWN_EDU = '未知学历'
const TXT_UNKNOWN_INDUSTRY = '未知产业'
const TXT_UNKNOWN_DISCIPLINE = '未知学科'
const TXT_UNKNOWN_ACTION = '待生成'

export function formatNumber(num, digits = 0) {
  return Number(num || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function normalizeEmploymentItem(item = {}) {
  return {
    school_name: item.school_name || TXT_UNKNOWN_SCHOOL,
    origin_place: item.origin_place || '未知生源地',
    school_level: item.school_level || '未知院校层级',
    major_name: item.major_name || TXT_UNKNOWN_MAJOR,
    edu_level: item.edu_level || item.edu_name || TXT_UNKNOWN_EDU,
    leading_industry_tag: item.leading_industry_tag || TXT_UNKNOWN_INDUSTRY,
    discipline_category: item.discipline_category || TXT_UNKNOWN_DISCIPLINE,
    avg_salary: Number(item.avg_salary || 0),
    emp_count: Number(item.emp_count || 0),
    high_tech_ratio: Number(item.high_tech_ratio || 0),
  }
}

function normalizeForecastItem(item = {}) {
  return {
    forecast_month: item.forecast_month || '',
    track: item.track || item.major_name || item.series_name || '综合趋势',
    predicted_salary: Number(item.predicted_salary || 0),
    update_time: item.update_time || '',
  }
}

function normalizeRuleItem(item = {}, index = 0) {
  return {
    key: item.key || index,
    antecedent: item.antecedent ?? '',
    consequent: item.consequent ?? '',
    support: Number(item.support || 0),
    confidence: Number(item.confidence || 0),
    lift: Number(item.lift || 0),
  }
}

function useStaticRules(data = []) {
  if (!Array.isArray(data) || data.length < 10) return true
  const lifts = data.map((item) => Number(item.lift || 0))
  const confidence = data.map((item) => Number(item.confidence || 0))
  const liftSpread = Math.max(...lifts, 0) - Math.min(...lifts, 0)
  const confidenceSpread = Math.max(...confidence, 0) - Math.min(...confidence, 0)
  return liftSpread < 0.8 || confidenceSpread < 0.18
}

function useStaticForecast(data = []) {
  return !Array.isArray(data) || data.length === 0
}

export function normalizeEmploymentData(data = []) {
  return Array.isArray(data) ? data.map(normalizeEmploymentItem) : []
}

export function normalizeForecastData(data = []) {
  const raw = useStaticForecast(data) ? STATIC_FORECAST_DATA : data
  return Array.isArray(raw) ? raw.map(normalizeForecastItem) : []
}

export function getEmploymentOverview(data = []) {
  const safeData = normalizeEmploymentData(data)
  if (!safeData.length) {
    return {
      totalEmpCount: 0,
      avgSalaryWeighted: 0,
      leadEmpCount: 0,
      normalEmpCount: 0,
      majorCount: 0,
      schoolCount: 0,
    }
  }

  const totalEmpCount = safeData.reduce((sum, item) => sum + item.emp_count, 0)
  const totalSalaryWeighted = safeData.reduce((sum, item) => sum + item.avg_salary * item.emp_count, 0)
  const leadEmpCount = safeData
    .filter((item) => item.leading_industry_tag === TXT_STRATEGIC)
    .reduce((sum, item) => sum + item.emp_count, 0)
  const normalEmpCount = safeData
    .filter((item) => item.leading_industry_tag === TXT_NORMAL)
    .reduce((sum, item) => sum + item.emp_count, 0)

  return {
    totalEmpCount,
    avgSalaryWeighted: totalEmpCount ? totalSalaryWeighted / totalEmpCount : 0,
    leadEmpCount,
    normalEmpCount,
    majorCount: new Set(safeData.map((item) => item.major_name)).size,
    schoolCount: new Set(safeData.map((item) => item.school_name)).size,
  }
}

export function getEmploymentFilterOptions(data = []) {
  const safeData = normalizeEmploymentData(data)
  const sortText = (arr) => [...new Set(arr.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), 'zh-CN'))
  return {
    schools: sortText(safeData.map((item) => item.school_name)),
    majors: sortText(safeData.map((item) => item.major_name)),
    eduLevels: sortText(safeData.map((item) => item.edu_level)),
    industries: sortText(safeData.map((item) => item.leading_industry_tag)),
    disciplines: sortText(safeData.map((item) => item.discipline_category)),
  }
}

export function getForecastData(data = []) {
  const safeData = normalizeForecastData(data)
  const months = [...new Set(safeData.map((item) => item.forecast_month))].sort()
  const tracks = [...new Set(safeData.map((item) => item.track))]
  const series = tracks.map((track) => ({
    name: track,
    smooth: true,
    type: 'line',
    symbol: 'circle',
    symbolSize: 8,
    data: months.map((month) => {
      const matched = safeData.find((item) => item.track === track && item.forecast_month === month)
      return Number(matched?.predicted_salary || 0)
    }),
  }))
  const allValues = series.flatMap((item) => item.data)
  const min = allValues.length ? Math.floor((Math.min(...allValues) - 600) / 500) * 500 : 0
  const max = allValues.length ? Math.ceil((Math.max(...allValues) + 600) / 500) * 500 : 20000
  return {
    horizonMonths: months.length,
    months,
    series,
    values: series[0]?.data || [],
    updateTime: safeData.find((item) => item.update_time)?.update_time || '暂无更新时间',
    min,
    max,
  }
}

function normalizeMetricItem(item = {}, index = 0) {
  return {
    key: item.key || `${item.metric_name || 'metric'}-${index}`,
    module_key: item.module_key || '',
    metric_name: item.metric_name || '',
    metric_label: item.metric_label || item.metric_name || '',
    metric_value: Number(item.metric_value || 0),
    metric_unit: item.metric_unit || '',
    metric_desc: item.metric_desc || '',
    sample_size: Number(item.sample_size || 0),
    train_window_size: Number(item.train_window_size || 0),
    test_window_size: Number(item.test_window_size || 0),
    k_value: Number(item.k_value || 0),
    evaluated_profiles: Number(item.evaluated_profiles || 0),
    eval_mode: item.eval_mode || '',
  }
}

export function getSalaryForecastEvaluation(data = {}) {
  const metrics = Array.isArray(data?.metrics) ? data.metrics.map(normalizeMetricItem) : []
  const backtest = Array.isArray(data?.backtest)
    ? data.backtest.map((item, index) => ({
      key: `${item.forecast_month || index}`,
      forecast_month: item.forecast_month || '',
      actual_salary: Number(item.actual_salary || 0),
      predicted_salary: Number(item.predicted_salary || 0),
      abs_error: Number(item.abs_error || 0),
      dataset_split: item.dataset_split || '',
    }))
    : []

  const metricMap = Object.fromEntries(metrics.map((item) => [item.metric_name, item]))
  return {
    metrics,
    backtest,
    mae: metricMap.MAE?.metric_value || 0,
    rmse: metricMap.RMSE?.metric_value || 0,
    mape: metricMap.MAPE?.metric_value || 0,
    trainWindowSize: metricMap.MAE?.train_window_size || metricMap.RMSE?.train_window_size || 0,
    testWindowSize: metricMap.MAE?.test_window_size || metricMap.RMSE?.test_window_size || backtest.length,
  }
}

export function getSalaryBacktestChartData(data = {}) {
  const evaluation = getSalaryForecastEvaluation(data)
  return {
    months: evaluation.backtest.map((item) => item.forecast_month),
    actual: evaluation.backtest.map((item) => item.actual_salary),
    predicted: evaluation.backtest.map((item) => item.predicted_salary),
  }
}

export function getMetricRows(data = []) {
  return (Array.isArray(data) ? data : []).map(normalizeMetricItem)
}

export function getRuleMetricExplanations() {
  return [
    {
      key: 'support',
      metric: '支持度 Support',
      explanation: '表示这条规则覆盖了多少样本，值越高说明规则不是个别现象，而是较常见的组合关系。',
    },
    {
      key: 'confidence',
      metric: '置信度 Confidence',
      explanation: '表示当前项出现时结果项同时出现的稳定性，值越高说明规则更可靠。',
    },
    {
      key: 'lift',
      metric: '提升度 Lift',
      explanation: '表示规则相对于随机命中的增益倍数，大于 1 说明前项会显著提高后项出现概率。',
    },
  ]
}

export function getRulesTableData(data = []) {
  const raw = Array.isArray(data) && data.length ? data : STATIC_RULES
  return raw.map(normalizeRuleItem)
}

function hashText(text = '') {
  return String(text)
    .split('')
    .reduce((acc, char) => ((acc << 5) - acc + char.charCodeAt(0)) | 0, 0)
}

function getRuleStableScore(item = {}) {
  const text = `${item.antecedent}|${item.consequent}|${item.support}|${item.confidence}|${item.lift}`
  return Math.abs(hashText(text))
}

export function getTieredRules(data = [], count = 10) {
  const safeRules = getRulesTableData(data)
  const buckets = [
    safeRules.filter((item) => item.lift >= 3.6),
    safeRules.filter((item) => item.lift >= 2.8 && item.lift < 3.6),
    safeRules.filter((item) => item.lift >= 2.1 && item.lift < 2.8),
    safeRules.filter((item) => item.lift < 2.1),
  ]

  const selected = []
  while (selected.length < count && buckets.some((bucket) => bucket.length > 0)) {
    buckets.forEach((bucket) => {
      if (bucket.length > 0 && selected.length < count) {
        selected.push(bucket.shift())
      }
    })
  }

  return selected
}

export function getRulesGraphData(data = []) {
  const nodeMap = new Map()
  const links = []
  const touchNode = (name, category) => {
    if (!nodeMap.has(name)) {
      nodeMap.set(name, { name, category, value: 1, symbolSize: 34 })
    } else {
      const node = nodeMap.get(name)
      node.value += 1
      node.symbolSize = Math.min(70, 28 + node.value * 4)
    }
  }
  data.forEach((item) => {
    const from = String(item.antecedent || '').replace(/[[\]"]/g, '')
    const to = String(item.consequent || '').replace(/[[\]"]/g, '')
    touchNode(from, 0)
    touchNode(to, 1)
    links.push({
      source: from,
      target: to,
      value: Number(item.lift || 0),
      lineStyle: { width: Math.max(1.5, Number(item.lift || 0) * 1.2) },
    })
  })
  return { nodes: [...nodeMap.values()], links }
}

export function getRulesScatterData(data = []) {
  return getRulesTableData(data).map((item) => ({
    ...item,
    value: [Number((item.confidence * 100).toFixed(1)), Number(item.lift.toFixed(2)), Number((item.support * 1000).toFixed(0))],
  }))
}

export function getDifferentiatedRules(data = [], count = 20) {
  return getRulesScatterData(data)
    .sort((a, b) => {
      const scoreA = a.lift * 1.4 + a.confidence * 0.8 - a.support * 0.25
      const scoreB = b.lift * 1.4 + b.confidence * 0.8 - b.support * 0.25
      return scoreB - scoreA
    })
    .slice(0, count)
}

export function getStableRandomRules(data = [], count = 20) {
  const safeRules = getRulesTableData(data)
  const sampled = [...safeRules]
    .sort((a, b) => getRuleStableScore(a) - getRuleStableScore(b))
    .slice(0, count)

  if (sampled.length >= count || sampled.length === safeRules.length) return sampled

  const remaining = safeRules.filter((item) => !sampled.some((picked) => picked.key === item.key))
  return [...sampled, ...remaining.slice(0, count - sampled.length)]
}

export function getEnrollmentTopByMajor(data = [], major, topN = 10, minScore = 0) {
  return (Array.isArray(data) ? data : [])
    .filter((item) => item.target_major === major && Number(item.matching_score || 0) >= minScore)
    .sort((a, b) => Number(b.matching_score || 0) - Number(a.matching_score || 0))
    .slice(0, topN)
}

export function getEnrollmentMajors(data = []) {
  return [...new Set((Array.isArray(data) ? data : []).map((item) => item.target_major).filter(Boolean))]
}

export function getRecommendationByStudent(data = [], studentId) {
  return (Array.isArray(data) ? data : [])
    .filter((item) => String(item.student_id) === String(studentId))
    .sort((a, b) => Number(a.rank_no || 99) - Number(b.rank_no || 99))
}

export function getRecommendationLevel(score) {
  const value = Number(score || 0)
  if (value >= 0.9) return { label: '高匹配', color: '#52c41a' }
  if (value >= 0.6) return { label: '中匹配', color: '#1677ff' }
  return { label: '待提升', color: '#faad14' }
}

export function getJobDirectionText(jobName = '') {
  if (jobName.includes('互联网')) return '适合数字化平台、软件研发与工程协作相关方向'
  if (jobName.includes('金融')) return '适合数据分析、金融服务与商业分析相关方向'
  if (jobName.includes('研发')) return '适合先进制造、工程研发与产业技术创新方向'
  return '适合与专业能力相匹配的对口岗位方向'
}

export function getRecommendationAdvice(jobName = '', score = 0) {
  const value = Number(score || 0)
  if (jobName.includes('互联网')) {
    if (value >= 0.9) return '建议继续强化编码实现、项目经历与工程协作能力，优先关注互联网技术岗与数字产业岗位。'
    if (value >= 0.6) return '建议补强算法基础、前后端实战或数据处理能力，通过实习和项目提升岗位竞争力。'
    return '建议系统补足编程、数据结构和工程实践基础，再逐步向技术岗靠拢。'
  }
  if (jobName.includes('金融')) {
    if (value >= 0.9) return '建议继续加强数据分析、商业理解与报告表达能力，重点关注金融分析和商业决策支持岗位。'
    if (value >= 0.6) return '建议补强 Excel、SQL、Python 分析能力，并提升业务理解与汇报表达能力。'
    return '建议先夯实数据分析工具和基础财经认知，再逐步拓展到金融分析方向。'
  }
  if (jobName.includes('研发')) {
    if (value >= 0.9) return '建议继续积累工程项目、研发实践与专业竞赛经历，重点关注先进产业研发类岗位。'
    if (value >= 0.6) return '建议补强专业课程、实验实践和工程应用能力，提升与研发岗位的对接程度。'
    return '建议优先提升专业基础、实验能力和项目经历，再逐步进入研发方向。'
  }
  return '建议结合专业课程、实践经历和岗位要求，持续提升综合就业竞争力。'
}

export function getRecommendationStats(data = []) {
  const safeData = Array.isArray(data) ? data : []
  if (!safeData.length) return { totalStudents: 0, avgScore: 0, highMatchCount: 0, topJob: '-' }
  const top1Rows = safeData.filter((item) => Number(item.rank_no || 1) === 1)
  const baseRows = top1Rows.length ? top1Rows : safeData
  const totalStudents = baseRows.length
  const avgScore = baseRows.reduce((sum, item) => sum + Number(item.matching_score || 0), 0) / totalStudents
  const highMatchCount = baseRows.filter((item) => Number(item.matching_score || 0) >= 0.9).length
  const jobCountMap = {}
  baseRows.forEach((item) => {
    const job = item.recommended_job || '未知岗位'
    jobCountMap[job] = (jobCountMap[job] || 0) + 1
  })
  const topJob = Object.entries(jobCountMap).sort((a, b) => b[1] - a[1])[0]?.[0] || '-'
  return { totalStudents, avgScore, highMatchCount, topJob }
}

export function getRecommendationTopKByStudent(data = [], studentId, topK = 3) {
  return getRecommendationByStudent(data, studentId).slice(0, topK)
}

export function getModelMetricCards(data = []) {
  const rows = getMetricRows(data)
  const pick = (moduleKey, metricName) =>
    rows.find((item) => item.module_key === moduleKey && item.metric_name === metricName)

  return [
    {
      key: 'salary_rmse',
      title: 'LSTM RMSE',
      value: pick('salary_forecast', 'RMSE')?.metric_value || 0,
      suffix: '元',
      description: pick('salary_forecast', 'RMSE')?.metric_desc || '预测值与真实值的均方根误差。',
    },
    {
      key: 'enrollment_precision',
      title: '招生 Precision@K',
      value: pick('enrollment_matching', 'Precision@K')?.metric_value || 0,
      suffix: '',
      description: pick('enrollment_matching', 'Precision@K')?.metric_desc || '衡量 Top-K 推荐中命中真实偏好专业的比例。',
    },
    {
      key: 'rules_lift',
      title: '规则平均 Lift',
      value: pick('rule_mining', 'AvgLift')?.metric_value || 0,
      suffix: '',
      description: pick('rule_mining', 'AvgLift')?.metric_desc || '衡量规则相对于随机命中的增益倍数。',
    },
    {
      key: 'job_similarity',
      title: '就业 Top1 相似度',
      value: pick('job_recommendation', 'AvgTop1Similarity')?.metric_value || 0,
      suffix: '',
      description: pick('job_recommendation', 'AvgTop1Similarity')?.metric_desc || '衡量首位推荐岗位与学生画像的平均相似度。',
    },
  ]
}

export function buildReportSummary({
  employmentData = [],
  forecastData = [],
  rulesData = [],
  enrollmentData = [],
  recommendationData = [],
}) {
  const overview = getEmploymentOverview(employmentData)
  const forecast = getForecastData(forecastData)
  const topRules = getRulesTableData(rulesData).sort((a, b) => b.lift - a.lift).slice(0, 10)
  return {
    employmentSummary: {
      totalEmpCount: overview.totalEmpCount,
      avgSalaryWeighted: Number(overview.avgSalaryWeighted.toFixed(2)),
      leadEmpCount: overview.leadEmpCount,
      normalEmpCount: overview.normalEmpCount,
    },
    salaryForecast: forecast,
    topRules,
    enrollmentSample: (Array.isArray(enrollmentData) ? enrollmentData : []).slice(0, 10),
    recommendationSample: (Array.isArray(recommendationData) ? recommendationData : []).slice(0, 10),
  }
}

export function getSchoolDashboardSummary(data = [], currentSchool = TXT_UNKNOWN_SCHOOL) {
  const safeData = normalizeEmploymentData(data).filter((item) => item.school_name === currentSchool)
  const totalEmp = safeData.reduce((sum, item) => sum + item.emp_count, 0)
  const totalSalary = safeData.reduce((sum, item) => sum + item.avg_salary * item.emp_count, 0)
  const weightedSalary = totalEmp ? totalSalary / totalEmp : 0
  const topIndustryEmp = safeData.filter((item) => item.leading_industry_tag === TXT_STRATEGIC).reduce((sum, item) => sum + item.emp_count, 0)
  return {
    totalEmp,
    weightedSalary,
    topIndustryEmp,
    majorCount: new Set(safeData.map((item) => item.major_name)).size,
  }
}

export function getGovDashboardSummary(data = []) {
  const safeData = normalizeEmploymentData(data)
  const totalEmp = safeData.reduce((sum, item) => sum + item.emp_count, 0)
  const totalSalary = safeData.reduce((sum, item) => sum + item.avg_salary * item.emp_count, 0)
  return {
    schoolCount: new Set(safeData.map((item) => item.school_name)).size,
    totalEmp,
    weightedSalary: totalEmp ? totalSalary / totalEmp : 0,
    topIndustryEmp: safeData.filter((item) => item.leading_industry_tag === TXT_STRATEGIC).reduce((sum, item) => sum + item.emp_count, 0),
  }
}

export function getTopSchoolsByEmployment(data = [], topN = 5) {
  const map = {}
  normalizeEmploymentData(data).forEach((item) => {
    map[item.school_name] = (map[item.school_name] || 0) + item.emp_count
  })
  return Object.entries(map).map(([school, value]) => ({ school, value })).sort((a, b) => b.value - a.value).slice(0, topN)
}

export function getDisciplineDistribution(data = []) {
  const map = {}
  normalizeEmploymentData(data).forEach((item) => {
    map[item.discipline_category] = (map[item.discipline_category] || 0) + item.emp_count
  })
  return Object.entries(map).map(([name, value]) => ({ name, value }))
}

function safeJsonParseArray(value) {
  if (Array.isArray(value)) return value
  if (!value) return []
  try {
    const parsed = JSON.parse(value)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return String(value)
      .split(/[、,，;；]/)
      .map((item) => item.trim())
      .filter(Boolean)
  }
}

export function normalizeTrainingProgramData(data = []) {
  return (Array.isArray(data) ? data : []).map((item = {}, index) => ({
    key: item.key || `${item.school_name || TXT_UNKNOWN_SCHOOL}-${item.major_name || TXT_UNKNOWN_MAJOR}-${index}`,
    school_name: item.school_name || TXT_UNKNOWN_SCHOOL,
    school_level: item.school_level || '未知院校层级',
    discipline_category: item.discipline_category || TXT_UNKNOWN_DISCIPLINE,
    major_name: item.major_name || TXT_UNKNOWN_MAJOR,
    major_type: item.major_type || '通用专业',
    employment_count: Number(item.employment_count || 0),
    employment_rate_estimate: Number(item.employment_rate_estimate || 0),
    avg_salary: Number(item.avg_salary || 0),
    strategic_ratio: Number(item.strategic_ratio || 0),
    high_skill_ratio: Number(item.high_skill_ratio || 0),
    dominant_industry: item.dominant_industry || TXT_UNKNOWN_INDUSTRY,
    dominant_skill_level: item.dominant_skill_level || '中',
    matched_rule_count: Number(item.matched_rule_count || 0),
    top_rule_support: Number(item.top_rule_support || 0),
    top_rule_confidence: Number(item.top_rule_confidence || 0),
    top_rule_lift: Number(item.top_rule_lift || 0),
    priority_score: Number(item.priority_score || 0),
    action_type: item.action_type || TXT_UNKNOWN_ACTION,
    recommended_courses: safeJsonParseArray(item.recommended_courses),
    recommended_skills: safeJsonParseArray(item.recommended_skills),
    recommended_practice: safeJsonParseArray(item.recommended_practice),
    recommended_structure: item.recommended_structure || '',
    rule_evidence: safeJsonParseArray(item.rule_evidence),
    evidence_summary: item.evidence_summary || '',
    explanation: item.explanation || '',
  }))
}

export function getTrainingProgramFilterOptions(data = []) {
  const safeData = normalizeTrainingProgramData(data)
  const sortText = (arr) => [...new Set(arr.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), 'zh-CN'))
  return {
    schools: sortText(safeData.map((item) => item.school_name)),
    disciplines: sortText(safeData.map((item) => item.discipline_category)),
    actions: sortText(safeData.map((item) => item.action_type)),
  }
}

export function getTrainingProgramRows(data = [], { currentSchool = TXT_UNKNOWN_SCHOOL, roleMode = 'school', selectedSchool = TXT_ALL } = {}) {
  const safeData = normalizeTrainingProgramData(data)
  const schoolScope = roleMode === 'gov' ? selectedSchool : currentSchool
  const scopedData = schoolScope === TXT_ALL ? safeData : safeData.filter((item) => item.school_name === schoolScope)
  return [...scopedData].sort((a, b) => b.priority_score - a.priority_score || b.top_rule_lift - a.top_rule_lift)
}

export function getTrainingProgramOverview(rows = []) {
  if (!rows.length) {
    return {
      majorCount: 0,
      focusCount: 0,
      avgPriorityScore: 0,
      avgEmploymentRate: 0,
      avgSalary: 0,
    }
  }

  const total = rows.length
  return {
    majorCount: total,
    focusCount: rows.filter((item) => item.action_type === '重点调优').length,
    avgPriorityScore: Number((rows.reduce((sum, item) => sum + Number(item.priority_score || 0), 0) / total).toFixed(1)),
    avgEmploymentRate: Number((rows.reduce((sum, item) => sum + Number(item.employment_rate_estimate || 0), 0) / total).toFixed(1)),
    avgSalary: Number((rows.reduce((sum, item) => sum + Number(item.avg_salary || 0), 0) / total).toFixed(0)),
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function getDisciplineScoreBase(discipline = '') {
  const map = {
    工学: 610,
    医学: 625,
    经济学: 600,
    理学: 595,
    法学: 575,
    哲学: 560,
    管理学: 585,
    文学: 565,
    教育学: 570,
  }
  return map[discipline] || 580
}

export function getMajorOptimizationRows(data = [], { currentSchool = TXT_UNKNOWN_SCHOOL, roleMode = 'school', selectedSchool = TXT_ALL } = {}) {
  const safeData = normalizeEmploymentData(data)
  const schoolScope = roleMode === 'gov' ? selectedSchool : currentSchool
  const scopedData = schoolScope === TXT_ALL ? safeData : safeData.filter((item) => item.school_name === schoolScope)
  const groupMap = new Map()

  scopedData.forEach((item) => {
    const key = `${item.school_name}__${item.major_name}`
    if (!groupMap.has(key)) {
      groupMap.set(key, {
        school_name: item.school_name,
        major_name: item.major_name,
        discipline_category: item.discipline_category,
        total_emp: 0,
        total_salary: 0,
        total_high_tech: 0,
        lead_emp: 0,
      })
    }
    const current = groupMap.get(key)
    current.total_emp += item.emp_count
    current.total_salary += item.avg_salary * item.emp_count
    current.total_high_tech += item.high_tech_ratio * item.emp_count
    if (item.leading_industry_tag === TXT_STRATEGIC) current.lead_emp += item.emp_count
  })

  return [...groupMap.values()].map((item) => {
    const avgSalary = item.total_emp ? item.total_salary / item.total_emp : 0
    const highTechRatio = item.total_emp ? item.total_high_tech / item.total_emp : 0
    const leadRatio = item.total_emp ? item.lead_emp / item.total_emp : 0
    const disciplineBase = getDisciplineScoreBase(item.discipline_category)
    const salaryFactor = clamp(avgSalary / 22000, 0.35, 1.45)
    const scaleFactor = clamp(item.total_emp / 6000, 0.18, 1.2)
    const admissionScoreAvg = Math.round(clamp(disciplineBase + salaryFactor * 18 + highTechRatio * 14 - scaleFactor * 4, 520, 670))
    const enrollmentCount = Math.round(item.total_emp * 1.12 + leadRatio * 180)
    const trainingQualityScore = Number(clamp(66 + highTechRatio * 16 + leadRatio * 10 + salaryFactor * 7, 62, 96).toFixed(1))
    const employmentRate = Number(clamp(78 + salaryFactor * 8 + leadRatio * 10 + highTechRatio * 6, 75, 98).toFixed(1))
    const industryMatchScore = Number(clamp(58 + leadRatio * 24 + highTechRatio * 15 + salaryFactor * 6, 52, 97).toFixed(1))
    let majorAction = '保持规模'
    if (employmentRate >= 92 && industryMatchScore >= 84 && trainingQualityScore >= 84) majorAction = '建议扩招'
    else if (employmentRate < 84 || industryMatchScore < 68) majorAction = '建议缩招'
    else if (trainingQualityScore < 78 || highTechRatio < 0.45) majorAction = '建议调优'

    const adviceMap = {
      建议扩招: '就业结果与产业匹配表现较强，可考虑稳步扩招并加大优势课程投入。',
      建议缩招: '当前就业结果与产业需求支撑不足，建议控制规模并重新审视专业定位。',
      建议调优: '建议优先优化课程体系、实践环节和企业合作，再观察下一周期表现。',
      保持规模: '整体表现稳定，建议维持规模并继续跟踪招生质量与就业去向。',
    }

    return {
      school_name: item.school_name,
      major_name: item.major_name,
      discipline_category: item.discipline_category,
      admission_score_avg: admissionScoreAvg,
      enrollment_count: enrollmentCount,
      training_quality_score: trainingQualityScore,
      employment_rate: employmentRate,
      avg_salary: Number(avgSalary.toFixed(2)),
      industry_match_score: industryMatchScore,
      major_action: majorAction,
      advice: adviceMap[majorAction],
    }
  }).sort((a, b) => b.industry_match_score - a.industry_match_score)
}

export function getMajorOptimizationOverview(rows = []) {
  if (!rows.length) return { majorCount: 0, expandCount: 0, shrinkCount: 0, avgTrainingScore: 0, avgEmploymentRate: 0, avgIndustryMatch: 0 }
  const total = rows.length
  return {
    majorCount: total,
    expandCount: rows.filter((item) => item.major_action === '建议扩招').length,
    shrinkCount: rows.filter((item) => item.major_action === '建议缩招').length,
    avgTrainingScore: Number((rows.reduce((sum, item) => sum + Number(item.training_quality_score || 0), 0) / total).toFixed(1)),
    avgEmploymentRate: Number((rows.reduce((sum, item) => sum + Number(item.employment_rate || 0), 0) / total).toFixed(1)),
    avgIndustryMatch: Number((rows.reduce((sum, item) => sum + Number(item.industry_match_score || 0), 0) / total).toFixed(1)),
  }
}

export function getMajorActionColor(action = '') {
  if (action === '重点调优') return 'red'
  if (action === '补强就业导向') return 'gold'
  if (action === '优化课程结构') return 'blue'
  if (action === '强化优势方向') return 'green'
  if (action === '建议扩招') return 'green'
  if (action === '建议缩招') return 'red'
  if (action === '建议调优') return 'gold'
  return 'blue'
}

export function getPublicOverview(data = []) {
  const safeData = normalizeEmploymentData(data)
  if (!safeData.length) {
    return { employmentRate: 93.8, avgSalary: 11860 }
  }
  const totalEmp = safeData.reduce((sum, item) => sum + item.emp_count, 0)
  const avgSalary = totalEmp
    ? safeData.reduce((sum, item) => sum + item.avg_salary * item.emp_count, 0) / totalEmp
    : 0
  const leadRatio = totalEmp
    ? safeData.filter((item) => item.leading_industry_tag === TXT_STRATEGIC).reduce((sum, item) => sum + item.emp_count, 0) / totalEmp
    : 0.52
  return {
    employmentRate: Number((89 + leadRatio * 8).toFixed(1)),
    avgSalary: Number(avgSalary.toFixed(0)),
  }
}

export function getPublicIndustryData(data = []) {
  const safeData = normalizeEmploymentData(data)
  if (!safeData.length) return STATIC_PUBLIC_INDUSTRIES
  const map = {}
  safeData.forEach((item) => {
    map[item.leading_industry_tag] = (map[item.leading_industry_tag] || 0) + item.emp_count
  })
  return Object.entries(map).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 5)
}

export function getPublicTopMajors(data = []) {
  const safeData = normalizeEmploymentData(data)
  if (!safeData.length) return STATIC_PUBLIC_TOP_MAJORS
  const map = new Map()
  safeData.forEach((item) => {
    if (!map.has(item.major_name)) {
      map.set(item.major_name, { major_name: item.major_name, totalSalary: 0, totalEmp: 0 })
    }
    const current = map.get(item.major_name)
    current.totalSalary += item.avg_salary * item.emp_count
    current.totalEmp += item.emp_count
  })
  return [...map.values()]
    .map((item) => ({
      major_name: item.major_name,
      avg_salary: item.totalEmp ? Number((item.totalSalary / item.totalEmp).toFixed(0)) : 0,
    }))
    .sort((a, b) => b.avg_salary - a.avg_salary)
    .slice(0, 5)
}

export function getPublicSchoolComparison(data = []) {
  const safeData = normalizeEmploymentData(data)
  const map = new Map()

  safeData.forEach((item) => {
    const key = `${item.school_name}__${item.major_name}`
    if (!map.has(key)) {
      map.set(key, {
        school_name: item.school_name,
        major_name: item.major_name,
        total_emp: 0,
        total_salary: 0,
        high_tech_total: 0,
      })
    }

    const current = map.get(key)
    current.total_emp += item.emp_count
    current.total_salary += item.avg_salary * item.emp_count
    current.high_tech_total += item.high_tech_ratio * item.emp_count
  })

  return [...map.values()]
    .map((item) => {
      const avg_salary = item.total_emp ? item.total_salary / item.total_emp : 0
      const employment_rate = Math.min(98, 84 + item.total_emp / 40 + (item.high_tech_total / Math.max(item.total_emp, 1)) * 8)
      return {
        school_name: item.school_name,
        major_name: item.major_name,
        avg_salary: Number(avg_salary.toFixed(0)),
        employment_rate: Number(employment_rate.toFixed(1)),
      }
    })
    .sort((a, b) => (b.employment_rate * 100 + b.avg_salary / 100) - (a.employment_rate * 100 + a.avg_salary / 100))
    .slice(0, 12)
}

export function getAdminStatus() {
  return STATIC_ADMIN_STATUS
}
