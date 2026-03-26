export function formatNumber(num, digits = 0) {
  const value = Number(num || 0)
  return value.toLocaleString('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function getEmploymentOverview(data = []) {
  if (!Array.isArray(data) || data.length === 0) {
    return {
      totalEmpCount: 0,
      avgSalaryWeighted: 0,
      leadEmpCount: 0,
      normalEmpCount: 0,
      majorCount: 0,
    }
  }

  const totalEmpCount = data.reduce((sum, item) => sum + Number(item.emp_count || 0), 0)
  const totalSalaryWeighted = data.reduce(
    (sum, item) => sum + Number(item.avg_salary || 0) * Number(item.emp_count || 0),
    0
  )

  const leadEmpCount = data
    .filter(item => item.leading_industry_tag === '三大先导')
    .reduce((sum, item) => sum + Number(item.emp_count || 0), 0)

  const normalEmpCount = data
    .filter(item => item.leading_industry_tag === '常规产业')
    .reduce((sum, item) => sum + Number(item.emp_count || 0), 0)

  const majorCount = new Set(data.map(item => item.major_name)).size

  return {
    totalEmpCount,
    avgSalaryWeighted: totalEmpCount ? totalSalaryWeighted / totalEmpCount : 0,
    leadEmpCount,
    normalEmpCount,
    majorCount,
  }
}

export function getEmploymentFilterOptions(data = []) {
  return {
    majors: [...new Set(data.map(item => item.major_name))],
    eduLevels: [...new Set(data.map(item => item.edu_level))],
    industries: [...new Set(data.map(item => item.leading_industry_tag))],
  }
}


export function getEmploymentBarSeries(
  data = [],
  {
    selectedIndustry = '全部',
    selectedEduLevels = [],
    metric = 'avg_salary',
  } = {}
) {
  const majors = [...new Set(data.map(item => item.major_name))]

  // const filtered = data.filter(item => {
  //   const matchIndustry =
  //     selectedIndustry === '全部' || item.leading_industry_tag === selectedIndustry

  //   const matchEdu =
  //     selectedEduLevels.length === 0 || selectedEduLevels.includes(item.edu_level)

  //   return matchIndustry && matchEdu
  // })

  const eduLevels =
    selectedEduLevels.length > 0
      ? selectedEduLevels
      : [...new Set(data.map(item => item.edu_level))]

  const series = eduLevels.map(level => ({
    name: level,
    type: 'bar',
    barMaxWidth: 28,
    data: majors.map(major => {
      // 先找到“这个专业 + 这个学历”的所有记录
      const rows = data.filter(item => {
        const matchMajor = item.major_name === major
        const matchLevel = item.edu_level === level

        // 如果选了具体产业，就只取该产业
        // 如果是“全部”，就把两类产业都纳入
        const matchIndustry =
          selectedIndustry === '全部' || item.leading_industry_tag === selectedIndustry

        return matchMajor && matchLevel && matchIndustry
      })

      if (!rows.length) return 0

      // “全部产业”下要做聚合
      if (selectedIndustry === '全部') {
        // 平均起薪：按 emp_count 加权平均
        if (metric === 'avg_salary') {
          const totalCount = rows.reduce(
            (sum, row) => sum + Number(row.emp_count || 0),
            0
          )

          if (totalCount === 0) return 0

          const weightedSalary = rows.reduce(
            (sum, row) =>
              sum +
              Number(row.avg_salary || 0) * Number(row.emp_count || 0),
            0
          )

          return Number((weightedSalary / totalCount).toFixed(2))
        }

        // 入职人数：直接相加
        if (metric === 'emp_count') {
          return rows.reduce(
            (sum, row) => sum + Number(row.emp_count || 0),
            0
          )
        }
      }

      // 选中了具体产业时，只有一条，直接取值
      return Number(rows[0][metric] || 0)
    }),
  }))

  return { majors, eduLevels, series }
}
export function getSankeyData(data = []) {
  const nodeSet = new Set()
  const links = []

  data.forEach(item => {
    const major = item.major_name
    const edu = item.edu_level
    const industry = item.leading_industry_tag
    const count = Number(item.emp_count || 0)

    nodeSet.add(major)
    nodeSet.add(edu)
    nodeSet.add(industry)

    links.push({ source: major, target: edu, value: count })
    links.push({ source: edu, target: industry, value: count })
  })

  return {
    nodes: [...nodeSet].map(name => ({ name })),
    links,
  }
}

export function getForecastData(data = []) {
  const sorted = [...data].sort((a, b) => String(a.forecast_month).localeCompare(String(b.forecast_month)))
  return {
    months: sorted.map(item => item.forecast_month),
    values: sorted.map(item => Number(item.predicted_salary || 0)),
    updateTime: sorted[0]?.update_time || '',
  }
}

export function getRulesTableData(data = []) {
  return data.map((item, index) => ({
    key: index,
    antecedent: item.antecedent ?? '',
    consequent: item.consequent ?? '',
    confidence: Number(item.confidence || 0),
    lift: Number(item.lift || 0),
  }))
}

export function getRulesGraphData(data = []) {
  const nodeMap = new Map()
  const links = []

  const touchNode = (name, category) => {
    if (!nodeMap.has(name)) {
      nodeMap.set(name, {
        name,
        category,
        value: 1,
        symbolSize: 38,
      })
    } else {
      const old = nodeMap.get(name)
      old.value += 1
      old.symbolSize = Math.min(70, 30 + old.value * 3)
    }
  }

  data.forEach(item => {
    const from = String(item.antecedent || '').replace(/[\[\]']/g, '')
    const to = String(item.consequent || '').replace(/[\[\]']/g, '')
    const lift = Number(item.lift || 0)

    touchNode(from, 0)
    touchNode(to, 1)

    links.push({
      source: from,
      target: to,
      value: lift,
      lineStyle: {
        width: Math.max(1, lift * 2),
      },
    })
  })

  return {
    nodes: [...nodeMap.values()],
    links,
  }
}

export function getEnrollmentTopByMajor(
  data = [],
  major,
  topN = 10,
  minScore = 0
) {
  return data
    .filter(
      item =>
        item.target_major === major &&
        Number(item.matching_score || 0) >= minScore
    )
    .sort((a, b) => Number(b.matching_score || 0) - Number(a.matching_score || 0))
    .slice(0, topN)
}

export function getEnrollmentMajors(data = []) {
  return [...new Set(data.map(item => item.target_major))]
}

export function getRecommendationByStudent(data = [], studentId) {
  return data.find(item => String(item.student_id) === String(studentId))
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
  const topRules = getRulesTableData(rulesData)
    .sort((a, b) => b.lift - a.lift)
    .slice(0, 5)

  return {
    employmentSummary: {
      totalEmpCount: overview.totalEmpCount,
      avgSalaryWeighted: Number(overview.avgSalaryWeighted.toFixed(2)),
      leadEmpCount: overview.leadEmpCount,
      normalEmpCount: overview.normalEmpCount,
    },
    salaryForecast: forecast,
    topRules,
    enrollmentSample: enrollmentData.slice(0, 10),
    recommendationSample: recommendationData.slice(0, 10),
  }
}