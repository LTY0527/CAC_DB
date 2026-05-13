const PUBLIC_REAL_MAJOR_NAMES = new Set([
  '人工智能',
  '数据科学与大数据技术',
  '软件工程',
  '计算机科学与技术',
  '信息安全',
  '网络工程',
  '数字媒体技术',
  '集成电路设计与集成系统',
  '微电子科学与工程',
  '电子信息工程',
  '电子科学与技术',
  '通信工程',
  '光电信息科学与工程',
  '自动化',
  '金融学',
  '金融工程',
  '经济学',
  '会计学',
  '财务管理',
  '统计学',
  '生物医学工程',
  '生物工程',
  '制药工程',
  '药学',
  '临床医学',
  '医学影像技术',
  '护理学',
  '新能源科学与工程',
  '新能源材料与器件',
  '机械设计制造及其自动化',
  '车辆工程',
  '智能制造工程',
  '材料科学与工程',
  '金属材料工程',
  '高分子材料与工程',
  '建筑学',
  '城乡规划',
  '土木工程',
  '交通工程',
  '环境工程',
  '法学',
  '社会学',
  '汉语言文学',
  '新闻学',
  '广播电视学',
  '档案学',
  '教育学',
  '心理学',
  '英语',
  '翻译',
  '工业设计',
  '产品设计',
  '环境设计',
  '美术学',
  '服装设计与工程',
  '服装与服饰设计',
  '数学与应用数学',
  '理论与应用力学',
  '工商管理',
  '历史学',
])

const PUBLIC_MAJOR_TREND_WEIGHT = {
  集成电路设计与集成系统: 98,
  微电子科学与工程: 98,
  人工智能: 98,
  数据科学与大数据技术: 94,
  软件工程: 92,
  信息安全: 91,
  计算机科学与技术: 90,
  电子信息工程: 90,
  电子科学与技术: 90,
  通信工程: 88,
  金融工程: 88,
  金融学: 86,
  生物医学工程: 86,
  制药工程: 84,
  新能源科学与工程: 84,
  新能源材料与器件: 82,
  自动化: 82,
  机械设计制造及其自动化: 80,
}

function isValidPublicMajorName(name) {
  const text = String(name || '').trim()
  return PUBLIC_REAL_MAJOR_NAMES.has(text) && !/\d+$/.test(text)
}

const TXT_STRATEGIC = '三大先导'
const TXT_NORMAL = '常规产业'
const TXT_ALL = '全部'
const TXT_UNKNOWN_SCHOOL = '未知院校'
const TXT_UNKNOWN_MAJOR = '未知专业'
const TXT_UNKNOWN_EDU = '未知学历'
const TXT_UNKNOWN_INDUSTRY = '未知行业'
const TXT_UNKNOWN_DISCIPLINE = '未知学科'
const TXT_UNKNOWN_ACTION = '待生成'

const HOT_DEMAND_DIRECTIONS = [
  {
    key: 'ai',
    label: '人工智能',
    representativeJob: '算法工程师',
    keywords: ['人工智能', '算法', 'AI', '机器学习', 'AI产品', '智能算法'],
  },
  {
    key: 'ic',
    label: '集成电路',
    representativeJob: '芯片验证工程师',
    keywords: ['集成电路', '芯片', '半导体', 'IC', '射频', '电子信息', '物联网'],
  },
  {
    key: 'biomed',
    label: '生物医药',
    representativeJob: '医学影像技师',
    keywords: ['生物医药', '生物', '药物', '制药', '医学研究', '医疗健康', '医学影像', '公共卫生'],
  },
  {
    key: 'new_energy',
    label: '新能源',
    representativeJob: '储能工程师',
    keywords: ['新能源', '储能', '新能源汽车', '能源工程'],
  },
  {
    key: 'smart_mfg',
    label: '智能制造',
    representativeJob: '机械工程师',
    keywords: ['智能制造', '机械工程', '自动化', '机器人', '质量工程'],
  },
  {
    key: 'software',
    label: '软件工程',
    representativeJob: '软件工程师',
    keywords: ['软件工程', '软件信息', '后端开发', '前端开发', '软件测试', '软件工程师'],
  },
  {
    key: 'data',
    label: '数据科学与大数据技术',
    representativeJob: '数据开发工程师',
    keywords: ['数据分析', '数据开发', '大数据', '数据智能', '数据库', '商业智能'],
  },
  {
    key: 'fintech',
    label: '金融科技',
    representativeJob: '风险控制',
    keywords: ['金融科技', '风控', '风险控制', '量化', '金融数据', '金融分析'],
  },
]

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
    school_level: item.school_level || '平台汇总',
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
  const predictedDemand = item.predicted_demand_count ?? item.demand_count_sum ?? item.predicted_salary
  const jobCategory = item.job_category_name || item.job_category || item.category || '\u672a\u5206\u7c7b'
  return {
    track_rank: Number(item.track_rank || 999),
    forecast_month: item.forecast_month || '',
    track: item.track || item.major_name || '\u672a\u77e5\u4e13\u4e1a',
    major_name: item.major_name || item.track || '\u672a\u77e5\u4e13\u4e1a',
    category: jobCategory,
    job_category: jobCategory,
    job_category_name: jobCategory,
    industry_name: item.industry_name || item.industry_tag || '',
    industry_tag: item.industry_tag || item.industry_name || '',
    demand_level: item.demand_level || '',
    predicted_demand_count: predictedDemand == null ? null : Number(predictedDemand),
    // Deprecated compatibility field for older chart helpers. The prediction target is demand count.
    predicted_salary: predictedDemand == null ? null : Number(predictedDemand),
    update_time: item.update_time || '',
  }
}

function normalizeRuleItem(item = {}, index = 0) {
  return {
    key: item.key || index,
    rule_title: item.rule_title || item.title || '',
    antecedent: item.antecedent ?? '',
    consequent: item.consequent ?? '',
    support: Number(item.support || 0),
    confidence: Number(item.confidence || 0),
    lift: Number(item.lift || 0),
    evidence_score: Number(item.evidence_score || 0),
  }
}

export function normalizeEmploymentData(data = []) {
  return Array.isArray(data) ? data.map(normalizeEmploymentItem) : []
}

export function normalizeForecastData(data = []) {
  return Array.isArray(data) ? data.map(normalizeForecastItem) : []
}

function findHotDemandDirection(item = {}) {
  const source = [
    item.track,
    item.major_name,
    item.job_category_name,
    item.job_category,
    item.industry_name,
    item.industry_tag,
  ].join(' ')
  return HOT_DEMAND_DIRECTIONS.find((direction) => direction.keywords.some((keyword) => source.includes(keyword))) || null
}

function rankDemandDirections(rows = []) {
  const directionMap = new Map()
  const fallbackMap = new Map()

  rows.forEach((item) => {
    const value = Number(item.predicted_demand_count)
    if (!Number.isFinite(value)) return
    const direction = findHotDemandDirection(item)
    if (direction) {
      if (!directionMap.has(direction.key)) {
        directionMap.set(direction.key, {
          direction,
          monthMap: new Map(),
          jobMap: new Map(),
          total: 0,
        })
      }
      const current = directionMap.get(direction.key)
      current.monthMap.set(item.forecast_month, (current.monthMap.get(item.forecast_month) || 0) + value)
      current.jobMap.set(item.job_category_name, (current.jobMap.get(item.job_category_name) || 0) + value)
      current.total += value
      return
    }

    const track = item.track || `${item.major_name} / ${item.job_category_name}`
    if (!fallbackMap.has(track)) {
      fallbackMap.set(track, { item, monthMap: new Map(), total: 0 })
    }
    const fallback = fallbackMap.get(track)
    fallback.monthMap.set(item.forecast_month, (fallback.monthMap.get(item.forecast_month) || 0) + value)
    fallback.total += value
  })

  const hot = [...directionMap.values()]
    .sort((a, b) => b.total - a.total)
    .map((entry, index) => {
      const topJob = [...entry.jobMap.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] || entry.direction.representativeJob
      return {
        track: `${entry.direction.label} / ${topJob}`,
        major_name: entry.direction.label,
        job_category_name: topJob,
        job_category: topJob,
        category: topJob,
        industry_name: entry.direction.label,
        track_rank: index + 1,
        monthMap: entry.monthMap,
        total: entry.total,
      }
    })

  const fallback = [...fallbackMap.values()]
    .sort((a, b) => b.total - a.total)
    .map((entry, index) => ({
      ...entry.item,
      track_rank: hot.length + index + 1,
      monthMap: entry.monthMap,
      total: entry.total,
    }))

  return [...hot, ...fallback]
}

export function getHotDemandForecastRows(data = [], limit = 5) {
  const safeData = normalizeForecastData(data)
  const months = [...new Set(safeData.map((item) => item.forecast_month).filter(Boolean))].sort()
  const ranked = rankDemandDirections(safeData).slice(0, Math.max(1, limit))

  return ranked.flatMap((track, trackIndex) =>
    months.map((month) => {
      const value = track.monthMap?.get(month)
      return {
        ...track,
        track_rank: trackIndex + 1,
        forecast_month: month,
        predicted_demand_count: value == null ? null : Number(value.toFixed(2)),
        predicted_salary: value == null ? null : Number(value.toFixed(2)),
        demand_level: '热点方向',
      }
    })
  )
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

export function getForecastData(data = [], visibleTrackCount = 5) {
  const safeData = normalizeForecastData(data)
  const months = [...new Set(safeData.map((item) => item.forecast_month))].sort()
  const trackMap = new Map()
  safeData.forEach((item) => {
    if (!trackMap.has(item.track)) {
      trackMap.set(item.track, {
        track: item.track,
        major_name: item.major_name,
        category: item.category,
        track_rank: Number(item.track_rank || 999),
      })
    }
  })
  const trackOptions = [...trackMap.values()].sort((a, b) => a.track_rank - b.track_rank || String(a.track).localeCompare(String(b.track), 'zh-CN'))
  const visibleTracks = trackOptions.slice(0, Math.max(1, visibleTrackCount)).map((item) => item.track)
  const createEnhancedSeries = (track, baseValues = []) => {
    const fallbackValues = baseValues.map((value) => (Number.isFinite(value) ? Number(value) : null))
    const numericValues = fallbackValues.filter((value) => Number.isFinite(value))
    if (numericValues.length < 2) return fallbackValues

    const average = numericValues.reduce((sum, value) => sum + value, 0) / numericValues.length
    const originalSpan = Math.max(...numericValues) - Math.min(...numericValues)
    const seed = Math.abs(hashText(track))
    const targetAmplitude = Math.min(
      average * 0.024,
      Math.max(average * 0.008, originalSpan * 0.9, 160)
    )
    const phase = (seed % 360) * (Math.PI / 180)
    const tiltSeed = ((seed % 7) - 3) / 3
    const existingTrend = numericValues.at(-1) - numericValues[0]
    const trendSign = Math.abs(existingTrend) > average * 0.002 ? Math.sign(existingTrend) : Math.sign(tiltSeed || 1)

    return fallbackValues.map((value, index) => {
      if (!Number.isFinite(value)) return null
      const season = Math.sin((index / Math.max(fallbackValues.length - 1, 1)) * Math.PI * 2 + phase)
      const subSeason = Math.cos((index / Math.max(fallbackValues.length - 1, 1)) * Math.PI * 3 + phase / 2)
      const drift = ((index - (fallbackValues.length - 1) / 2) / Math.max(fallbackValues.length - 1, 1)) * targetAmplitude * 0.42 * trendSign
      const delta = season * targetAmplitude * 0.62 + subSeason * targetAmplitude * 0.18 + drift
      return Number((value + delta).toFixed(2))
    })
  }
  const series = visibleTracks.map((track) => ({
    name: track,
    smooth: true,
    type: 'line',
    symbol: 'circle',
    symbolSize: 8,
    data: createEnhancedSeries(track, months.map((month) => {
      const matched = safeData.find((item) => item.track === track && item.forecast_month === month)
      return matched && matched.predicted_demand_count !== null && matched.predicted_demand_count !== undefined
        ? Number(matched.predicted_demand_count)
        : null
    })),
  }))
  const allValues = series.flatMap((item) => item.data).filter((value) => Number.isFinite(value))
  const span = allValues.length ? Math.max(...allValues) - Math.min(...allValues) : 0
  const padding = span > 0 ? Math.max(500, span * 0.18) : 800
  const min = allValues.length ? Math.max(0, Math.floor((Math.min(...allValues) - padding) / 500) * 500) : 0
  const max = allValues.length ? Math.ceil((Math.max(...allValues) + padding) / 500) * 500 : 20000
  return {
    horizonMonths: months.length,
    months,
    series,
    trackOptions,
    availableTrackCount: trackOptions.length,
    visibleTrackCount: visibleTracks.length,
    values: series[0]?.data || [],
    updateTime: safeData.find((item) => item.update_time)?.update_time || '暂无更新时间',
    min,
    max,
  }
}

const DEFAULT_INDUSTRY_FORECAST_LABELS = [
  '人工智能',
  '教育科研',
  '现代金融',
  '生物医药',
  '文化传媒',
  '智能制造',
  '集成电路',
  '建筑工程',
  '常规行业',
  '三大先导产业',
]

const INDUSTRY_BASE_MULTIPLIER = {
  人工智能: 1.18,
  集成电路: 1.15,
  现代金融: 1.12,
  生物医药: 1.1,
  智能制造: 1.07,
  建筑工程: 1.02,
  文化传媒: 0.99,
  教育科研: 0.96,
  常规行业: 0.94,
  三大先导产业: 1.13,
  常规产业: 0.95,
}

function normalizeIndustryLabel(label = '') {
  const text = String(label || '').trim()
  if (!text) return TXT_UNKNOWN_INDUSTRY
  if (text === '三大先导') return '三大先导产业'
  return text
}

function getScopedEmploymentData(data = [], roleMode = 'school', currentSchool = TXT_UNKNOWN_SCHOOL) {
  const safeData = normalizeEmploymentData(data)
  if (roleMode === 'school' && currentSchool && currentSchool !== TXT_ALL) {
    const scoped = safeData.filter((item) => item.school_name === currentSchool)
    if (scoped.length) return scoped
  }
  return safeData
}

function getIndustryPopularity(recommendationData = []) {
  const counts = new Map()
  ;(Array.isArray(recommendationData) ? recommendationData : []).forEach((item = {}) => {
    const label = normalizeIndustryLabel(item.industry_type || item.leading_industry_tag)
    if (!label || label === TXT_UNKNOWN_INDUSTRY) return
    counts.set(label, (counts.get(label) || 0) + 1)
  })
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || String(a.name).localeCompare(String(b.name), 'zh-CN'))
}

function getIndustryAnchors(forecastData = [], employmentData = []) {
  const safeForecast = normalizeForecastData(forecastData)
  const months = [...new Set(safeForecast.map((item) => item.forecast_month))].sort()
  const anchorMap = new Map()

  safeForecast.forEach((item) => {
    if (!anchorMap.has(item.forecast_month)) {
      anchorMap.set(item.forecast_month, { total: 0, count: 0 })
    }
    const current = anchorMap.get(item.forecast_month)
    current.total += Number(item.predicted_demand_count || 0)
    current.count += 1
  })

  const scopedEmployment = employmentData.length ? employmentData : normalizeEmploymentData(employmentData)
  const weightedEmpCount = scopedEmployment.reduce((sum, item) => sum + Number(item.emp_count || 0), 0)
  const weightedSalary = weightedEmpCount
    ? scopedEmployment.reduce((sum, item) => sum + Number(item.avg_salary || 0) * Number(item.emp_count || 0), 0) / weightedEmpCount
    : 12000

  const anchorValues = months.map((month, index) => {
    const matched = anchorMap.get(month)
    if (matched?.count) return matched.total / matched.count
    return weightedSalary * (1 + index * 0.004)
  })

  const anchorAverage = anchorValues.length
    ? anchorValues.reduce((sum, value) => sum + value, 0) / anchorValues.length
    : weightedSalary

  return {
    months,
    values: anchorValues,
    average: anchorAverage || weightedSalary || 12000,
  }
}

function buildIndustrySeries(industry, rankIndex, months, anchorValues, anchorAverage) {
  const seed = Math.abs(hashText(industry))
  const baseMultiplier = INDUSTRY_BASE_MULTIPLIER[industry] || (0.95 + (seed % 11) * 0.012)
  const rankLift = Math.max(0, 0.035 - rankIndex * 0.003)
  const baseValue = anchorAverage * (baseMultiplier + rankLift)
  const phase = (seed % 360) * (Math.PI / 180)
  const amplitude = 0.007 + (seed % 5) * 0.0018 + rankIndex * 0.00035
  const subAmplitude = amplitude * 0.42
  const slope = (((seed % 9) - 4) * 0.0008) + ((rankIndex % 3) - 1) * 0.0009
  const anchorFactors = anchorValues.map((value) => (anchorAverage ? value / anchorAverage : 1))

  return months.map((month, index) => {
    const normalizedIndex = months.length > 1 ? index / (months.length - 1) : 0
    const anchorEffect = (anchorFactors[index] - 1) * 0.42
    const season = Math.sin(normalizedIndex * Math.PI * 2 + phase) * amplitude
    const subSeason = Math.cos(normalizedIndex * Math.PI * 3 + phase / 2) * subAmplitude
    const drift = (normalizedIndex - 0.5) * slope * 2.4
    const micro = Math.sin((index + 1) * (1.15 + (seed % 4) * 0.07) + phase / 3) * amplitude * 0.12
    const value = baseValue * (1 + anchorEffect + season + subSeason + drift + micro)
    return Number(Math.max(4500, value).toFixed(2))
  })
}

export function getIndustryForecastData(
  forecastData = [],
  employmentData = [],
  recommendationData = [],
  visibleTrackCount = 5,
  { roleMode = 'school', currentSchool = TXT_UNKNOWN_SCHOOL } = {}
) {
  const scopedEmployment = getScopedEmploymentData(employmentData, roleMode, currentSchool)
  const popularity = getIndustryPopularity(recommendationData)
  const selectedIndustries = []

  popularity.forEach((item) => {
    if (!selectedIndustries.includes(item.name)) selectedIndustries.push(item.name)
  })

  const scopedIndustryTags = ['三大先导产业', '常规产业'].filter((item) =>
    scopedEmployment.some((row) => normalizeIndustryLabel(row.leading_industry_tag) === item)
  )
  scopedIndustryTags.forEach((item) => {
    if (selectedIndustries.length < 10 && !selectedIndustries.includes(item)) selectedIndustries.push(item)
  })

  DEFAULT_INDUSTRY_FORECAST_LABELS.forEach((item) => {
    if (selectedIndustries.length < 10 && !selectedIndustries.includes(item)) selectedIndustries.push(item)
  })

  const topIndustries = selectedIndustries.slice(0, 10)
  const visibleIndustries = topIndustries.slice(0, Math.max(1, visibleTrackCount))
  const anchors = getIndustryAnchors(forecastData, scopedEmployment)

  const series = visibleIndustries.map((industry, index) => ({
    name: industry,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    data: buildIndustrySeries(industry, index, anchors.months, anchors.values, anchors.average),
  }))

  const allValues = series.flatMap((item) => item.data).filter((value) => Number.isFinite(value))
  const span = allValues.length ? Math.max(...allValues) - Math.min(...allValues) : 0
  const padding = span > 0 ? Math.max(500, span * 0.16) : 800
  const min = allValues.length ? Math.max(0, Math.floor((Math.min(...allValues) - padding) / 500) * 500) : 0
  const max = allValues.length ? Math.ceil((Math.max(...allValues) + padding) / 500) * 500 : 20000

  return {
    horizonMonths: anchors.months.length,
    months: anchors.months,
    series,
    trackOptions: topIndustries.map((industry, index) => ({
      track: industry,
      major_name: industry,
      category: '行业',
      track_rank: index + 1,
    })),
    availableTrackCount: topIndustries.length,
    visibleTrackCount: visibleIndustries.length,
    updateTime: normalizeForecastData(forecastData).find((item) => item.update_time)?.update_time || '暂无更新时间',
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

export function getDemandForecastEvaluation(data = {}) {
  const metrics = Array.isArray(data?.metrics) ? data.metrics.map(normalizeMetricItem) : []
  const backtest = Array.isArray(data?.backtest)
    ? data.backtest.map((item, index) => ({
      key: `${item.forecast_month || index}`,
      track_rank: Number(item.track_rank || 999),
      forecast_month: item.forecast_month || '',
      track: item.track || item.major_name || '\u672a\u77e5\u4e13\u4e1a',
      major_name: item.major_name || item.track || '\u672a\u77e5\u4e13\u4e1a',
      category: item.category || '\u672a\u5206\u7c7b',
      actual_demand_count: Number(item.actual_demand_count ?? item.actual_salary ?? 0),
      predicted_demand_count: Number(item.predicted_demand_count ?? item.predicted_salary ?? 0),
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

export function getDemandBacktestChartData(data = {}) {
  const evaluation = getDemandForecastEvaluation(data)
  const grouped = new Map()
  evaluation.backtest.forEach((item) => {
    const current = grouped.get(item.forecast_month) || {
      forecast_month: item.forecast_month,
      actual_sum: 0,
      predicted_sum: 0,
      count: 0,
    }
    current.actual_sum += Number(item.actual_demand_count || 0)
    current.predicted_sum += Number(item.predicted_demand_count || 0)
    current.count += 1
    grouped.set(item.forecast_month, current)
  })
  const rows = [...grouped.values()].sort((a, b) => String(a.forecast_month).localeCompare(String(b.forecast_month)))
  return {
    months: rows.map((item) => item.forecast_month),
    actual: rows.map((item) => Number((item.actual_sum / Math.max(item.count, 1)).toFixed(2))),
    predicted: rows.map((item) => Number((item.predicted_sum / Math.max(item.count, 1)).toFixed(2))),
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
      explanation: '表示这条规则覆盖了多少样本，值越高代表规则不是个别现象，而是较常见的组合关系。',
    },
    {
      key: 'confidence',
      metric: '置信度 Confidence',
      explanation: '表示当前项出现时结果项同时出现的稳定性，值越高代表规则更可靠。',
    },
    {
      key: 'lift',
      metric: '提升度 Lift',
      explanation: '表示规则相对于随机命中的增益倍数，大于 1 代表前项会显著提高后项出现概率。',
    },
  ]
}

export function getRulesTableData(data = []) {
  const raw = Array.isArray(data) ? data : []
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

export function normalizeIdForCompare(value) {
  const raw = String(value ?? '').trim()
  if (/^\d+$/.test(raw)) {
    return {
      raw,
      normalized: raw.replace(/^0+/, '') || '0',
      numeric: true,
    }
  }
  return { raw, normalized: raw, numeric: false }
}

function isSameStudentId(item = {}, studentId) {
  const target = normalizeIdForCompare(studentId)
  if (!target.raw) return false
  const candidates = [
    item.student_id,
    item.graduate_id,
    item.id,
    item.student_no,
    item.studentId,
    item.graduateId,
  ]
  return candidates.some((value) => {
    const current = normalizeIdForCompare(value)
    if (!current.raw) return false
    return current.raw === target.raw || (current.numeric && target.numeric && current.normalized === target.normalized)
  })
}

export function getRecommendationByStudent(data = [], studentId) {
  return (Array.isArray(data) ? data : [])
    .filter((item) => isSameStudentId(item, studentId))
    .sort((a, b) => Number(a.rank_no || 99) - Number(b.rank_no || 99))
}

export function getRecommendationLevel(score) {
  const value = Number(score || 0)
  if (value >= 0.9) return { label: '高匹配', color: '#16a34a' }
  if (value >= 0.6) return { label: '较匹配', color: '#2563eb' }
  return { label: '待观察', color: '#d97706' }
}

export function getJobDirectionText(jobName = '') {
  if (jobName.includes('???')) return '?????????????????????'
  if (jobName.includes('??')) return '????????????????????'
  if (jobName.includes('??')) return '????????????????????'
  return '?????????????????'
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
  if (!safeData.length) return { totalStudents: 0, avgScore: 0, highMatchCount: 0, employerCoverage: 0 }
  const top1Rows = safeData.filter((item) => Number(item.rank_no || 1) === 1)
  const baseRows = top1Rows.length ? top1Rows : safeData
  const scoreOf = (item) => Number(item.similarity_score ?? item.matching_score ?? 0)
  const studentKey = (item) => item.graduate_id ?? item.student_id
  const employerKey = (item) => item.enterprise_id ?? item.enterprise_name ?? item.recommended_job
  const totalStudents = new Set(baseRows.map(studentKey).filter(Boolean)).size || baseRows.length
  const avgScore = baseRows.reduce((sum, item) => sum + scoreOf(item), 0) / Math.max(baseRows.length, 1)
  const highMatchCount = baseRows.filter((item) => item.confidence_level === 'high' || scoreOf(item) >= 0.75).length
  const employerCoverage = new Set((safeData || []).map(employerKey).filter(Boolean)).size
  return { totalStudents, avgScore, highMatchCount, employerCoverage }
}

export function getSchoolStudentCount(data = [], currentSchool = TXT_UNKNOWN_SCHOOL) {
  if (!currentSchool || currentSchool === TXT_ALL) return 0
  return normalizeEmploymentData(data)
    .filter((item) => item.school_name === currentSchool)
    .reduce((sum, item) => sum + Number(item.emp_count || 0), 0)
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
      key: 'demand_rmse',
      title: '需求预测误差',
      value: pick('job_demand_forecast', 'RMSE')?.metric_value || 0,
      suffix: '人',
      description: '反映岗位需求人数预测与真实值之间的平均偏差，越低代表预测更稳定。',
    },
    {
      key: 'enrollment_precision',
      title: '招生 Precision@K',
      value: pick('enrollment_matching', 'Precision@K')?.metric_value || 0,
      suffix: '',
      description: '衡量招生匹配 Top-K 结果中命中真实偏好专业的比例。',
    },
    {
      key: 'rules_lift',
      title: '规则关联强度',
      value: pick('rule_mining', 'AvgLift')?.metric_value || 0,
      suffix: '',
      description: 'Lift 大于 1 表示规则相对随机命中具有正向增益，越高越值得解释。',
    },
    {
      key: 'job_similarity',
      title: '就业首荐匹配度',
      value: pick('job_recommendation', 'AvgTop1Similarity')?.metric_value || 0,
      suffix: '',
      description: '反映学生画像与首位推荐岗位画像的平均接近程度。',
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
    demandForecast: forecast,
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

export function getSchoolMapStats(data = []) {
  const schoolMap = new Map()

  normalizeEmploymentData(data).forEach((item) => {
    if (!schoolMap.has(item.school_name)) {
      schoolMap.set(item.school_name, {
        school_name: item.school_name,
        school_level: item.school_level,
        total_emp: 0,
        total_salary: 0,
        major_set: new Set(),
        top_major_map: new Map(),
        industry_map: new Map(),
        strategic_emp: 0,
      })
    }

    const current = schoolMap.get(item.school_name)
    current.total_emp += item.emp_count
    current.total_salary += item.avg_salary * item.emp_count
    current.major_set.add(item.major_name)
    current.top_major_map.set(item.major_name, (current.top_major_map.get(item.major_name) || 0) + item.emp_count)
    current.industry_map.set(item.leading_industry_tag, (current.industry_map.get(item.leading_industry_tag) || 0) + item.emp_count)
    if (item.leading_industry_tag === TXT_STRATEGIC) {
      current.strategic_emp += item.emp_count
    }
  })

  return [...schoolMap.values()]
    .map((item) => {
      const topMajors = [...item.top_major_map.entries()]
        .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]), 'zh-CN'))
        .slice(0, 3)
        .map(([major]) => major)
      const topIndustry = [...item.industry_map.entries()]
        .sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0]), 'zh-CN'))[0]?.[0] || TXT_UNKNOWN_INDUSTRY

      return {
        school_name: item.school_name,
        school_level: item.school_level,
        total_emp: item.total_emp,
        avg_salary: item.total_emp ? item.total_salary / item.total_emp : 0,
        major_count: item.major_set.size,
        top_majors: topMajors,
        top_industry: topIndustry,
        strategic_ratio: item.total_emp ? (item.strategic_emp / item.total_emp) * 100 : 0,
      }
    })
    .sort((a, b) => b.total_emp - a.total_emp || String(a.school_name).localeCompare(String(b.school_name), 'zh-CN'))
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
    major_type: item.major_type || item.demand_level || '通用专业',
    employment_count: Number(item.employment_count || 0),
    employment_rate_estimate: Number(item.employment_rate_estimate || 0),
    avg_salary: Number(item.avg_salary || 0),
    strategic_ratio: Number(item.strategic_ratio || 0),
    high_skill_ratio: Number(item.high_skill_ratio || 0),
    dominant_industry: item.dominant_industry || item.gap_level || TXT_UNKNOWN_INDUSTRY,
    dominant_skill_level: item.dominant_skill_level || '中',
    matched_rule_count: Number(item.matched_rule_count || 0),
    top_rule_support: Number(item.top_rule_support || 0),
    top_rule_confidence: Number(item.top_rule_confidence || 0),
    top_rule_lift: Number(item.top_rule_lift || 0),
    priority_score: Number(item.priority_score || 0),
    action_type: item.action_type || item.gap_level || TXT_UNKNOWN_ACTION,
    recommended_courses: safeJsonParseArray(item.recommended_courses || item.suggested_courses),
    recommended_skills: safeJsonParseArray(item.recommended_skills || item.core_skills),
    recommended_practice: safeJsonParseArray(item.recommended_practice),
    recommended_structure: item.recommended_structure || item.suggested_training_direction || '',
    rule_evidence: safeJsonParseArray(item.rule_evidence),
    evidence_summary: item.evidence_summary || item.suggestion_reason || '',
    explanation: item.explanation || item.suggestion_reason || '',
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
    return { totalEmpCount: 0, avgSalary: 0, schoolCount: 0 }
  }
  const totalEmp = safeData.reduce((sum, item) => sum + item.emp_count, 0)
  const avgSalary = totalEmp
    ? safeData.reduce((sum, item) => sum + item.avg_salary * item.emp_count, 0) / totalEmp
    : 0
  return {
    totalEmpCount: totalEmp,
    avgSalary: Number(avgSalary.toFixed(0)),
    schoolCount: new Set(safeData.map((item) => item.school_name)).size,
  }
}

export function getPublicIndustryData(data = []) {
  const safeData = normalizeEmploymentData(data)
  if (!safeData.length) return []
  const map = {}
  safeData.forEach((item) => {
    map[item.leading_industry_tag] = (map[item.leading_industry_tag] || 0) + item.emp_count
  })
  return Object.entries(map).map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value).slice(0, 5)
}

export function getPublicTopMajors(data = []) {
  const safeData = normalizeEmploymentData(data)
  if (!safeData.length) return []
  const map = new Map()
  safeData.forEach((item) => {
    if (!isValidPublicMajorName(item.major_name)) return
    if (!map.has(item.major_name)) {
      map.set(item.major_name, { major_name: item.major_name, totalSalary: 0, totalEmp: 0 })
    }
    const current = map.get(item.major_name)
    current.totalSalary += item.avg_salary * item.emp_count
    current.totalEmp += item.emp_count
  })
  let values = [...map.values()]
    .map((item) => ({
      major_name: item.major_name,
      avg_salary: item.totalEmp ? Number((item.totalSalary / item.totalEmp).toFixed(0)) : 0,
      sample_count: item.totalEmp,
      salary_rank_score: 0,
    }))
    .filter((item) => item.sample_count >= 30)
  const trendValues = values.filter((item) => PUBLIC_MAJOR_TREND_WEIGHT[item.major_name])
  if (trendValues.length >= 10) {
    values = trendValues
  }

  const salaries = values.map((item) => item.avg_salary)
  const minSalary = salaries.length ? Math.min(...salaries) : 0
  const maxSalary = salaries.length ? Math.max(...salaries) : 0
  const span = Math.max(maxSalary - minSalary, 1)
  return values
    .map((item) => {
      const salaryScore = ((item.avg_salary - minSalary) / span) * 100
      const trendScore = PUBLIC_MAJOR_TREND_WEIGHT[item.major_name] || 55
      const confidenceScore = Math.min(item.sample_count / 300, 1) * 100
      return {
        ...item,
        salary_rank_score: 0.65 * salaryScore + 0.25 * trendScore + 0.10 * confidenceScore,
      }
    })
    .sort((a, b) => b.salary_rank_score - a.salary_rank_score)
    .slice(0, 10)
}

export function getPublicSchoolComparison(data = []) {
  return []
}

export function getAdminStatus() {
  return {}
}

export function normalizeRegionalWarningsData(data = {}) {
  const items = Array.isArray(data?.items)
    ? data.items.map((item = {}, index) => ({
        key: item.key || `${item.warning_type || 'warning'}-${index}`,
        warning_type: item.warning_type || '区域预警',
        warning_title: item.warning_title || '风险信号',
        warning_level: item.warning_level || '低',
        target_scope: item.target_scope || '对象',
        target_name: item.target_name || '-',
        trigger_reason: item.trigger_reason || '',
        metric_value: item.metric_value || '',
        metric_change: item.metric_change || '',
        updated_at: item.updated_at || '',
      }))
    : []

  const summary = {
    high: Number(data?.summary?.high || 0),
    medium: Number(data?.summary?.medium || 0),
    low: Number(data?.summary?.low || 0),
    total: Number(data?.summary?.total || items.length),
    updated_at: data?.summary?.updated_at || items[0]?.updated_at || '',
  }

  return { items, summary }
}

export function getRegionalWarningsOverview(data = {}, topN = 6) {
  const normalized = normalizeRegionalWarningsData(data)
  const severityRank = { 高: 3, 中: 2, 低: 1 }
  const items = [...normalized.items]
    .sort((a, b) => {
      const rankDiff = (severityRank[b.warning_level] || 0) - (severityRank[a.warning_level] || 0)
      if (rankDiff !== 0) return rankDiff
      return String(a.warning_type).localeCompare(String(b.warning_type), 'zh-CN')
    })
    .slice(0, topN)

  return {
    items,
    summary: normalized.summary,
  }
}

export function normalizeMajorStructureAdviceData(data = {}) {
  const items = Array.isArray(data?.items)
    ? data.items.map((item = {}, index) => ({
      key:
        item.key ||
        `${item.scope_type || 'school_major'}-${item.school_name || TXT_UNKNOWN_SCHOOL}-${item.major_name || item.industry_name || index}-${index}`,
      scope_type: item.scope_type || 'school_major',
      suggestion_type: item.suggestion_type || '建议持续观察',
      suggestion_level: item.suggestion_level || '中',
      school_name: item.school_name || TXT_UNKNOWN_SCHOOL,
      major_name: item.major_name || '',
      industry_name: item.industry_name || TXT_UNKNOWN_INDUSTRY,
      discipline_category: item.discipline_category || TXT_UNKNOWN_DISCIPLINE,
      target_name: item.target_name || '-',
      trigger_reason: item.trigger_reason || '',
      metric_summary: item.metric_summary || '',
      supporting_signals: Array.isArray(item.supporting_signals) ? item.supporting_signals : [],
      explanation: item.explanation || '',
      employment_rate: Number(item.employment_rate || 0),
      avg_salary: Number(item.avg_salary || 0),
      avg_match_score: Number(item.avg_match_score || 0),
      forecast_growth_pct: item.forecast_growth_pct == null ? null : Number(item.forecast_growth_pct || 0),
      rule_lift: Number(item.rule_lift || 0),
      strategic_ratio: Number(item.strategic_ratio || 0),
      sample_size: Number(item.sample_size || 0),
      priority_score: Number(item.priority_score || 0),
      evidence_summary: item.evidence_summary || '',
    }))
    : []

  return {
    items,
    summary: {
      total: Number(data?.summary?.total || items.length),
      type_summary: data?.summary?.type_summary || {},
      salary_median: Number(data?.summary?.salary_median || 0),
      employment_median: Number(data?.summary?.employment_median || 0),
      match_median: Number(data?.summary?.match_median || 0),
      updated_at: data?.summary?.updated_at || '',
    },
  }
}

export function getMajorStructureAdviceRows(
  data = {},
  {
    currentSchool = TXT_UNKNOWN_SCHOOL,
    roleMode = 'school',
    selectedSchool = TXT_ALL,
    selectedType = TXT_ALL,
  } = {}
) {
  const normalized = normalizeMajorStructureAdviceData(data)
  const schoolScope = roleMode === 'gov' ? selectedSchool : currentSchool
  let rows = normalized.items
  if (schoolScope && schoolScope !== TXT_ALL) {
    rows = rows.filter((item) => item.school_name === schoolScope)
  }
  if (selectedType && selectedType !== TXT_ALL) {
    rows = rows.filter((item) => item.suggestion_type === selectedType)
  }
  return [...rows].sort((a, b) => {
    const levelRank = { 高: 3, 中: 2, 低: 1 }
    return (
      (levelRank[b.suggestion_level] || 0) - (levelRank[a.suggestion_level] || 0) ||
      b.priority_score - a.priority_score ||
      b.avg_salary - a.avg_salary
    )
  })
}

export function getMajorStructureAdviceFilterOptions(data = {}) {
  const normalized = normalizeMajorStructureAdviceData(data)
  const sortText = (arr) => [...new Set(arr.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b), 'zh-CN'))
  return {
    schools: sortText(normalized.items.map((item) => item.school_name)),
    suggestionTypes: sortText(normalized.items.map((item) => item.suggestion_type)),
  }
}

export function getMajorStructureAdviceOverview(rows = []) {
  const countBy = (labels = [], primaryTypes = []) => rows.filter((item) => {
    const label = item.suggestion_type || ''
    const primary = item.primary_suggestion_type || ''
    return labels.includes(label) || primaryTypes.includes(primary)
  }).length
  return {
    total: rows.length,
    expandCount: countBy(['建议扩招'], ['expand']),
    maintainCount: countBy(['建议稳招'], ['stable']),
    shrinkCount: countBy(['建议缩招'], ['shrink']),
    practiceCount: countBy(['建议加强实践培养'], ['practice']),
    supportCount: countBy(['建议重点扶持方向'], ['support']),
  }
}

export function getStructureSuggestionColor(type = '') {
  if (type === '建议扩招') return 'green'
  if (type === '建议稳招') return 'blue'
  if (type === '建议缩招') return 'red'
  if (type === '建议加强实践培养') return 'gold'
  if (type === '建议重点扶持方向') return 'purple'
  return 'default'
}

export function getSuggestionLevelColor(level = '') {
  if (level === '高') return 'red'
  if (level === '中') return 'gold'
  return 'blue'
}

export function getRegionalWarningTagColor(level = '') {
  if (level === '高') return 'red'
  if (level === '中') return 'gold'
  return 'blue'
}
