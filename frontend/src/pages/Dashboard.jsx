import { Card, Col, Row, Statistic, Table, Tag } from 'antd'
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
  axisLabelStyle,
  axisLineStyle,
  chartPalette,
  designTokens,
  darkTooltip,
  legendTextStyle,
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  sectionTitleStyle,
  splitLineStyle,
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
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    legend: { top: 8, textStyle: legendTextStyle },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
    xAxis: { type: 'category', data: forecast.months, axisLabel: axisLabelStyle, axisLine: axisLineStyle },
    yAxis: { type: 'value', min: forecast.min, max: forecast.max, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: (forecast.series || []).map((item, index) => ({
      ...item,
      smooth: true,
      lineStyle: { width: 2.5, color: chartPalette[index % chartPalette.length] },
      itemStyle: { color: chartPalette[index % chartPalette.length] },
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
          `结果项：${cleanRuleLabel(matched.consequent)}`,
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
      axisLabel: { color: designTokens.textMuted, interval: 0, lineHeight: 18, fontSize: 12, margin: 18 },
      axisLine: axisLineStyle,
    },
    yAxis: { type: 'value', min: 1, max: 5, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      {
        name: 'Lift',
        type: 'bar',
        barWidth: 18,
        data: rules.map((item) => Number(item.lift || 0)),
        itemStyle: { color: designTokens.accent, borderRadius: [6, 6, 0, 0] },
      },
    ],
  }
}

function buildGovTopSchoolOption(topSchools) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    grid: { left: '8%', right: '4%', bottom: '10%', top: '14%', containLabel: true },
    xAxis: { type: 'category', data: topSchools.map((item) => item.school), axisLabel: { ...axisLabelStyle, interval: 0 }, axisLine: axisLineStyle },
    yAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      {
        type: 'bar',
        barWidth: 24,
        data: topSchools.map((item) => item.value),
        itemStyle: { color: designTokens.accent, borderRadius: [6, 6, 0, 0] },
      },
    ],
  }
}

function buildDisciplineOption(disciplineData) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', ...darkTooltip },
    legend: { bottom: 0, textStyle: legendTextStyle },
    series: [{ type: 'pie', radius: ['38%', '68%'], center: ['50%', '45%'], data: disciplineData, label: { color: designTokens.textSecondary, formatter: '{b}' } }],
  }
}

const chainItems = ['动态监测', '需求预测', '招生匹配', '规则证据', '培养优化', '就业推荐']

export default function Dashboard({
  employmentData = [],
  forecastData = [],
  rulesData = [],
  dataLoadedAt = '',
  loading,
  error,
  roleMode = 'school',
  currentSchool = '上海大学',
}) {
  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>
  if (error && !employmentData.length) return <div style={{ color: designTokens.danger }}>{error}</div>

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
          { title: '全市就业样本', value: formatNumber(govSummary.totalEmp), style: statValueBlue },
          { title: '全市平均薪资', value: `${formatNumber(govSummary.weightedSalary, 0)} 元`, style: statValueCyan },
          { title: '先导产业吸纳人数', value: formatNumber(govSummary.topIndustryEmp), style: statValuePurple },
        ]
      : [
          { title: '本校就业样本', value: formatNumber(schoolSummary.totalEmp), style: statValuePrimary },
          { title: '本校平均薪资', value: `${formatNumber(schoolSummary.weightedSalary, 0)} 元`, style: statValueBlue },
          { title: '先导产业吸纳人数', value: formatNumber(schoolSummary.topIndustryEmp), style: statValueCyan },
          { title: '覆盖专业数', value: formatNumber(schoolSummary.majorCount), style: statValuePurple },
        ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} xl={16}>
              <div style={sectionTitleStyle}>平台主链路总览</div>
              <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {chainItems.map((item, index) => (
                  <Tag key={item} color={index % 2 === 0 ? 'processing' : 'cyan'}>
                    {index + 1}. {item}
                  </Tag>
                ))}
              </div>
            </Col>
            <Col xs={24} xl={8}>
              <div style={metaLabelStyle}>数据载入时间</div>
              <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
            </Col>
          </Row>
        </Card>
      </Col>

      {summaryCards.map((item) => (
        <Col xs={24} sm={12} xl={6} key={item.title}>
          <Card style={panelStyle}>
            <Statistic title={item.title} value={item.value} styles={{ title: statTitleStyle, content: item.style }} />
          </Card>
        </Col>
      ))}

      <Col xs={24} xl={14}>
        <Card title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '区域需求预测趋势' : '薪资需求预测趋势'}</span>} style={panelStyle}>
          <ReactECharts option={buildForecastOverviewOption(forecast)} style={{ height: 380 }} />
        </Card>
      </Col>

      <Col xs={24} xl={10}>
        <Card title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '高校就业规模对比' : '高价值规则证据'}</span>} style={panelStyle}>
          <ReactECharts option={roleMode === 'gov' ? buildGovTopSchoolOption(topSchools) : buildRulesLiftOption(rules)} style={{ height: 380 }} />
        </Card>
      </Col>

      {roleMode === 'gov' ? (
        <Col span={24}>
          <Card title={<span style={sectionTitleStyle}>区域学科结构分布</span>} style={panelStyle}>
            <ReactECharts option={buildDisciplineOption(disciplineData)} style={{ height: 400 }} />
          </Card>
        </Col>
      ) : (
        <Col span={24}>
          <Card title={<span style={sectionTitleStyle}>高价值规则摘要</span>} style={panelStyle}>
            <Table
              rowKey="key"
              pagination={false}
              dataSource={rules}
              columns={[
                { title: '前项条件', dataIndex: 'antecedent', render: (value) => cleanRuleLabel(value) },
                { title: '结果项', dataIndex: 'consequent', render: (value) => cleanRuleLabel(value) },
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
