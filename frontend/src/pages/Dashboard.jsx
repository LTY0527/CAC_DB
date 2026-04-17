import { useMemo, useState } from 'react'
import { Card, Col, Row, Statistic, Table, Tag } from 'antd'
import ReactECharts from 'echarts-for-react'
import { useSearchParams } from 'react-router-dom'
import DataCapabilityBand from '../components/DataCapabilityBand'
import GovernmentDrillBoard from '../components/GovernmentDrillBoard'
import GovernmentHeroSection from '../components/GovernmentHeroSection'
import InfoTrigger from '../components/InfoTrigger'
import MetricInsightDrawer from '../components/MetricInsightDrawer'
import RegionalWarningBoard from '../components/RegionalWarningBoard'
import SchoolMapExplorer from '../components/SchoolMapExplorer'
import SchoolBenchmarkBoard from '../components/SchoolBenchmarkBoard'
import TeacherHeroSection from '../components/TeacherHeroSection'
import { governmentDataCapabilityConfig, teacherDataCapabilityConfig } from '../config/dataCapabilityConfig'
import { getMetricInsight } from '../config/metricInsightMap'
import {
  formatNumber,
  getDisciplineDistribution,
  getForecastData,
  getGovDashboardSummary,
  getRegionalWarningsOverview,
  getSchoolDashboardSummary,
  getTopSchoolsByEmployment,
  getTieredRules,
} from '../utils/dataAdapter'
import {
  axisLabelStyle,
  axisLineStyle,
  chartPalette,
  darkTooltip,
  designTokens,
  legendTextStyle,
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
  return String(text).replace(/[\[\]"]/g, '').replace(/,/g, ' / ').replace(/\s+/g, ' ').trim()
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
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const row = params?.[0]
        return row ? `${row.axisValue}<br/>就业样本：${formatNumber(row.value)}` : ''
      },
    },
    grid: { left: '8%', right: '4%', bottom: '10%', top: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: topSchools.map((item) => item.school),
      axisLabel: { ...axisLabelStyle, interval: 0 },
      axisLine: axisLineStyle,
    },
    yAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    series: [
      {
        name: '就业样本',
        type: 'bar',
        barWidth: 24,
        data: topSchools.map((item) => ({ value: item.value, school: item.school })),
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
    series: [
      {
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['50%', '45%'],
        data: disciplineData,
        label: { color: designTokens.textSecondary, formatter: '{b}' },
      },
    ],
  }
}

const chainItems = ['动态监测', '需求预测', '招生匹配', '规则证据', '培养优化', '就业推荐']

export default function Dashboard({
  employmentData = [],
  forecastData = [],
  rulesData = [],
  regionalWarningsData = {},
  dataLoadedAt = '',
  loading,
  error,
  roleMode = 'school',
  currentSchool = '上海大学',
}) {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeMetricKey, setActiveMetricKey] = useState('')
  const selectedSchool = roleMode === 'gov' ? searchParams.get('school') || '' : ''
  const selectedMajor = roleMode === 'gov' ? searchParams.get('major') || '' : ''
  const inGovDrill = roleMode === 'gov' && Boolean(selectedSchool)

  const schoolChartEvents = useMemo(
    () =>
      roleMode === 'gov'
        ? {
            click: (params) => {
              const school = params?.data?.school || params?.name
              if (!school) return
              setSearchParams({ school })
            },
          }
        : undefined,
    [roleMode, setSearchParams]
  )

  const schoolSummary = getSchoolDashboardSummary(employmentData, currentSchool)
  const govSummary = getGovDashboardSummary(employmentData)
  const forecast = getForecastData(forecastData)
  const rules = getTieredRules(rulesData, 10)
  const topSchools = getTopSchoolsByEmployment(employmentData, 6)
  const disciplineData = getDisciplineDistribution(employmentData)
  const regionalWarningOverview = getRegionalWarningsOverview(regionalWarningsData, 20)
  const priorityWarningMajorCount = new Set(
    (regionalWarningOverview.items || [])
      .filter((item) => item.warning_level !== '低' && item.target_name && item.target_name !== '-')
      .map((item) => item.target_name)
  ).size
  const strategicTrendRatio = govSummary.totalEmp ? ((govSummary.topIndustryEmp / govSummary.totalEmp) * 100).toFixed(1) : '0.0'

  const summaryCards =
    roleMode === 'gov'
      ? [
          { title: '覆盖高校数', value: formatNumber(govSummary.schoolCount), style: statValuePrimary, metricKey: 'gov_school_coverage' },
          { title: '全市就业样本', value: formatNumber(govSummary.totalEmp), style: statValueBlue, metricKey: 'gov_employment_samples' },
          { title: '全市平均薪资', value: formatNumber(govSummary.weightedSalary, 0), suffix: '元', style: statValueCyan, metricKey: 'gov_avg_salary' },
          { title: '先导产业吸纳人数', value: formatNumber(govSummary.topIndustryEmp), style: statValuePurple, metricKey: 'gov_lead_industry_employment' },
        ]
      : [
          { title: '本校就业样本', value: formatNumber(schoolSummary.totalEmp), style: statValuePrimary, metricKey: 'school_employment_samples' },
          { title: '本校平均薪资', value: formatNumber(schoolSummary.weightedSalary, 0), suffix: '元', style: statValueBlue, metricKey: 'school_avg_salary' },
          { title: '先导产业吸纳人数', value: formatNumber(schoolSummary.topIndustryEmp), style: statValueCyan, metricKey: 'school_lead_industry_employment' },
          { title: '覆盖专业数', value: formatNumber(schoolSummary.majorCount), style: statValuePurple, metricKey: 'school_major_coverage' },
        ]

  const activeMetricInsight = useMemo(
    () =>
      getMetricInsight(roleMode, activeMetricKey, {
        dataLoadedAt,
        currentSchool,
      }),
    [activeMetricKey, currentSchool, dataLoadedAt, roleMode]
  )

  const goBackToCity = () => setSearchParams({})
  const handleSelectSchool = (school) => setSearchParams({ school })
  const handleSelectMajor = (major) => setSearchParams({ school: selectedSchool, major })
  const scrollToMain = () => {
    document.getElementById('dashboard-main-overview')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  const scrollToGovWarnings = () => {
    document.getElementById('gov-warning-board')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>
  if (error && !employmentData.length) return <div style={{ color: designTokens.danger }}>{error}</div>

  return (
    <Row gutter={[16, 16]}>
      {roleMode === 'gov' ? (
        <Col span={24}>
          <GovernmentHeroSection
            onAction={scrollToGovWarnings}
            summaryItems={[
              { label: '覆盖高校数', value: `${formatNumber(govSummary.schoolCount)} 所`, hint: '当前纳入区域监测与对比的院校范围' },
              { label: '重点预警专业数', value: `${formatNumber(priorityWarningMajorCount)} 个`, hint: '优先关注中高风险信号对应的专业对象' },
              { label: '先导产业吸纳趋势', value: `${strategicTrendRatio}%`, hint: '当前样本进入先导产业的占比水平' },
            ]}
          />
        </Col>
      ) : null}

      {roleMode === 'gov' ? (
        <Col span={24} id="dashboard-main-overview">
          <DataCapabilityBand
            title={governmentDataCapabilityConfig.title}
            items={governmentDataCapabilityConfig.items}
            flowItems={chainItems}
            loadedAt={dataLoadedAt}
          />
        </Col>
      ) : null}

      {roleMode !== 'gov' ? (
        <Col span={24}>
          <TeacherHeroSection
            schoolName={currentSchool}
            onAction={scrollToMain}
            summaryItems={[
              { label: '本校就业质量', value: `${formatNumber(schoolSummary.weightedSalary, 0)} 元`, hint: '结合去向结构与薪资水平综合观察' },
              { label: '专业结构优化', value: formatNumber(schoolSummary.majorCount), hint: '当前纳入分析的专业覆盖范围' },
              { label: '培养方案联动', value: formatNumber(schoolSummary.topIndustryEmp), hint: '重点行业吸纳人数可用于联动课程调整' },
            ]}
          />
        </Col>
      ) : null}

      {roleMode !== 'gov' ? (
        <Col span={24} id="dashboard-main-overview">
          <DataCapabilityBand
            title={teacherDataCapabilityConfig.title}
            items={teacherDataCapabilityConfig.items}
            flowItems={chainItems}
            loadedAt={dataLoadedAt}
          />
        </Col>
      ) : null}

      {summaryCards.map((item) => (
        <Col xs={24} sm={12} xl={6} key={item.metricKey}>
          <Card style={panelStyle}>
            <Statistic
              title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                  <span>{item.title}</span>
                  <InfoTrigger onClick={() => setActiveMetricKey(item.metricKey)} />
                </div>
              }
              value={item.value}
              suffix={item.suffix}
              styles={{ title: statTitleStyle, content: item.style }}
            />
          </Card>
        </Col>
      ))}

      {roleMode === 'gov' && !inGovDrill ? (
        <Col span={24}>
          <SchoolMapExplorer
            employmentData={employmentData}
            roleMode="gov"
            actionLabel="进入学校治理详情"
            onAction={handleSelectSchool}
          />
        </Col>
      ) : null}

      {roleMode === 'gov' ? (
        <Col span={24} id="gov-warning-board">
          <RegionalWarningBoard data={regionalWarningsData} />
        </Col>
      ) : null}

      {roleMode === 'gov' && !inGovDrill ? (
        <Col span={24}>
          <SchoolBenchmarkBoard />
        </Col>
      ) : null}

      {inGovDrill ? (
        <Col span={24}>
          <GovernmentDrillBoard
            schoolName={selectedSchool}
            majorName={selectedMajor}
            onBackToCity={goBackToCity}
            onSelectSchool={handleSelectSchool}
            onSelectMajor={handleSelectMajor}
          />
        </Col>
      ) : (
        <>
          <Col xs={24} xl={14}>
            <Card title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '区域需求预测趋势' : '薪资需求预测趋势'}</span>} style={panelStyle}>
              <ReactECharts option={buildForecastOverviewOption(forecast)} style={{ height: 380 }} />
            </Card>
          </Col>

          <Col xs={24} xl={10}>
            <Card
              title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '高校就业规模对比' : '高价值规则证据'}</span>}
              extra={
                roleMode === 'gov' ? <span style={{ color: designTokens.textMuted, fontSize: 12 }}>点击柱体查看学校层详情</span> : null
              }
              style={panelStyle}
            >
              <ReactECharts
                option={roleMode === 'gov' ? buildGovTopSchoolOption(topSchools) : buildRulesLiftOption(rules)}
                style={{ height: 380 }}
                onEvents={schoolChartEvents}
              />
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
        </>
      )}

      <MetricInsightDrawer
        open={Boolean(activeMetricInsight)}
        insight={activeMetricInsight}
        roleMode={roleMode}
        onClose={() => setActiveMetricKey('')}
      />
    </Row>
  )
}
