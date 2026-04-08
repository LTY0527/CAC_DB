import { Card, Col, Row, Statistic, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getDisciplineDistribution,
  getForecastData,
  getGovDashboardSummary,
  getSchoolDashboardSummary,
  getTieredRules,
  getTopSchoolsByEmployment,
} from '../utils/dataAdapter'
import {
  darkTooltip,
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

function cleanRuleLabel(text = '') {
  return String(text).replace(/[[\]"]/g, '').replace(/,/g, ' / ').replace(/\s+/g, ' ').trim()
}

function compactRuleLabel(text = '') {
  const label = cleanRuleLabel(text)
  if (label.length <= 8) return label
  if (label.length <= 16) return `${label.slice(0, 8)}\n${label.slice(8)}`
  return `${label.slice(0, 8)}\n${label.slice(8, 16)}...`
}

function buildForecastOverviewOption(forecast) {
  const palette = ['#34d3ff', '#8b6cff', '#67e8f9']
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    legend: { top: 8, textStyle: { color: '#b7dfff' } },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: forecast.months,
      axisLabel: { color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      min: forecast.min,
      max: forecast.max,
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: (forecast.series || []).map((item, index) => ({
      ...item,
      smooth: true,
      lineStyle: { width: 3, color: palette[index % palette.length] },
      itemStyle: { color: palette[index % palette.length] },
    })),
  }
}

function buildRulesLiftOption(rules) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const index = params?.[0]?.dataIndex ?? 0
        const matched = rules[index] || {}
        return [
          cleanRuleLabel(matched.antecedent),
          `结果：${cleanRuleLabel(matched.consequent)}`,
          `支持度：${(Number(matched.support || 0) * 100).toFixed(1)}%`,
          `置信度：${(Number(matched.confidence || 0) * 100).toFixed(1)}%`,
          `提升度：${Number(matched.lift || 0).toFixed(2)}`,
        ].join('<br/>')
      },
    },
    grid: { left: '8%', right: '4%', bottom: '24%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rules.map((item, index) => compactRuleLabel(item.antecedent || `规则${index + 1}`)),
      axisLabel: {
        color: '#b7dfff',
        interval: 0,
        lineHeight: 18,
        fontSize: 12,
        margin: 18,
      },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      min: 1,
      max: 5,
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        name: 'Lift',
        type: 'bar',
        barWidth: 18,
        data: rules.map((item) => Number(item.lift || 0)),
        itemStyle: { color: '#5b7be0', borderRadius: [6, 6, 0, 0] },
      },
    ],
  }
}

function buildGovTopSchoolOption(topSchools) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    grid: { left: '8%', right: '4%', bottom: '10%', top: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: topSchools.map((item) => item.school),
      axisLabel: { color: '#b7dfff', interval: 0 },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        type: 'bar',
        barWidth: 24,
        data: topSchools.map((item) => item.value),
        itemStyle: { color: '#4cc9f0', borderRadius: [6, 6, 0, 0] },
      },
    ],
  }
}

function buildDisciplineOption(disciplineData) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', ...darkTooltip },
    legend: { bottom: 0, textStyle: { color: '#b7dfff' } },
    series: [
      {
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '45%'],
        data: disciplineData,
        label: { color: '#d9eeff', formatter: '{b}' },
      },
    ],
  }
}

export default function Dashboard({
  employmentData = [],
  forecastData = [],
  rulesData = [],
  loading,
  error,
  roleMode = 'school',
  currentSchool = '上海大学',
}) {
  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !employmentData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  const schoolSummary = getSchoolDashboardSummary(employmentData, currentSchool)
  const govSummary = getGovDashboardSummary(employmentData)
  const forecast = getForecastData(forecastData)
  const rules = getTieredRules(rulesData, 10)
  const topSchools = getTopSchoolsByEmployment(employmentData, 5)
  const disciplineData = getDisciplineDistribution(employmentData)

  const summaryCards =
    roleMode === 'gov'
      ? [
          { title: '覆盖高校数', value: formatNumber(govSummary.schoolCount), style: statValuePrimary },
          { title: '全市样本人数', value: formatNumber(govSummary.totalEmp), style: statValueBlue },
          { title: '全市平均薪资', value: `￥${formatNumber(govSummary.weightedSalary, 0)}`, style: statValueCyan },
          { title: '重点产业吸纳人数', value: formatNumber(govSummary.topIndustryEmp), style: statValuePurple },
        ]
      : [
          { title: '本校样本人数', value: formatNumber(schoolSummary.totalEmp), style: statValuePrimary },
          { title: '本校平均薪资', value: `￥${formatNumber(schoolSummary.weightedSalary, 0)}`, style: statValueBlue },
          { title: '重点产业吸纳人数', value: formatNumber(schoolSummary.topIndustryEmp), style: statValueCyan },
          { title: '覆盖专业数', value: formatNumber(schoolSummary.majorCount), style: statValuePurple },
        ]

  return (
    <Row gutter={[16, 16]}>
      {summaryCards.map((item) => (
        <Col xs={24} sm={12} xl={6} key={item.title}>
          <Card style={panelStyle}>
            <Statistic title={item.title} value={item.value} styles={{ title: statTitleStyle, content: item.style }} />
          </Card>
        </Col>
      ))}

      <Col xs={24} xl={14}>
        <Card title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '全市需求侧薪资趋势' : '需求预测趋势对比'}</span>} style={panelStyle}>
          <ReactECharts option={buildForecastOverviewOption(forecast)} style={{ height: 380 }} />
        </Card>
      </Col>

      <Col xs={24} xl={10}>
        <Card title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? 'Top 高校就业规模对比' : '高提升度规则分层展示'}</span>} style={panelStyle}>
          <ReactECharts
            option={roleMode === 'gov' ? buildGovTopSchoolOption(topSchools) : buildRulesLiftOption(rules)}
            style={{ height: 380 }}
          />
        </Card>
      </Col>

      {roleMode === 'gov' ? (
        <Col span={24}>
          <Card title={<span style={sectionTitleStyle}>全市学科门类结构分布</span>} style={panelStyle}>
            <ReactECharts option={buildDisciplineOption(disciplineData)} style={{ height: 400 }} />
          </Card>
        </Col>
      ) : (
        <Col span={24}>
          <Card title={<span style={sectionTitleStyle}>十条分层规则明细</span>} style={panelStyle}>
            <Table
              rowKey="key"
              pagination={false}
              dataSource={rules}
              columns={[
                { title: '前置条件', dataIndex: 'antecedent', render: (value) => cleanRuleLabel(value) },
                { title: '就业结果', dataIndex: 'consequent', render: (value) => cleanRuleLabel(value) },
                { title: '支持度', dataIndex: 'support', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
                { title: '置信度', dataIndex: 'confidence', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
                { title: '提升度', dataIndex: 'lift', render: (value) => Number(value || 0).toFixed(2) },
              ]}
            />
          </Card>
        </Col>
      )}
    </Row>
  )
}
