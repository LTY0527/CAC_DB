import { Card, Col, Row, Statistic, Table, Tag } from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getDisciplineDistribution,
  getForecastData,
  getGovDashboardSummary,
  getModelMetricCards,
  getSchoolDashboardSummary,
  getTieredRules,
  getTopSchoolsByEmployment,
} from '../utils/dataAdapter'
import {
  algorithmTextStyle,
  darkTooltip,
  metaLabelStyle,
  metaValueStyle,
  noteTextStyle,
  panelStyle,
  riskTextStyle,
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
      axisLabel: { color: '#b7dfff', interval: 0, lineHeight: 18, fontSize: 12, margin: 18 },
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

const chainItems = [
  '动态监测',
  '需求预测',
  '招生匹配',
  '规则证据',
  '培养优化',
  '就业推荐',
]

export default function Dashboard({
  employmentData = [],
  forecastData = [],
  rulesData = [],
  modelMetricsData = [],
  dataLoadedAt = '',
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
  const modelMetricCards = getModelMetricCards(modelMetricsData)

  const summaryCards =
    roleMode === 'gov'
      ? [
        { title: '覆盖高校数', value: formatNumber(govSummary.schoolCount), style: statValuePrimary },
        { title: '全市就业样本', value: formatNumber(govSummary.totalEmp), style: statValueBlue },
        { title: '全市平均薪资', value: `¥${formatNumber(govSummary.weightedSalary, 0)}`, style: statValueCyan },
        { title: '先导产业吸纳人数', value: formatNumber(govSummary.topIndustryEmp), style: statValuePurple },
      ]
      : [
        { title: '本校就业样本', value: formatNumber(schoolSummary.totalEmp), style: statValuePrimary },
        { title: '本校平均薪资', value: `¥${formatNumber(schoolSummary.weightedSalary, 0)}`, style: statValueBlue },
        { title: '先导产业吸纳人数', value: formatNumber(schoolSummary.topIndustryEmp), style: statValueCyan },
        { title: '覆盖专业数', value: formatNumber(schoolSummary.majorCount), style: statValuePurple },
      ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <div style={sectionTitleStyle}>平台主链路总览</div>
              <div style={{ ...noteTextStyle, marginTop: 10 }}>
                该页面用于把五大模块放到一条完整业务链上看：先通过动态监测识别结构变化，再用需求预测判断趋势，用招生匹配和培养优化支持前端决策，最终落到就业推荐与质量反馈。
              </div>
              <div style={{ marginTop: 16, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {chainItems.map((item, index) => (
                  <Tag key={item} color={index % 2 === 0 ? 'processing' : 'cyan'}>
                    {index + 1}. {item}
                  </Tag>
                ))}
              </div>
            </Col>
            <Col xs={24} xl={10}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={metaLabelStyle}>数据载入时间</div>
                  <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
                </Col>
                <Col span={12}>
                  <div style={metaLabelStyle}>业务价值</div>
                  <div style={metaValueStyle}>为招生、培养、就业形成闭环决策入口</div>
                </Col>
                <Col span={24}>
                  <div style={algorithmTextStyle}>算法说明：总览页不单独训练模型，而是聚合 LSTM、协同过滤、关联规则、余弦相似度四类结果做管理层展示。</div>
                </Col>
                <Col span={24}>
                  <div style={riskTextStyle}>风险提示：总览页强调趋势与信号，具体专业调整和学生推荐仍需回到对应模块查看细项证据。</div>
                </Col>
              </Row>
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
        <Card
          title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '区域需求预测趋势' : '薪资需求预测趋势'}</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>业务价值：提前识别需求变化，为招生规模和培养侧资源投入提供前置信号。</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildForecastOverviewOption(forecast)} style={{ height: 380 }} />
        </Card>
      </Col>

      <Col xs={24} xl={10}>
        <Card
          title={<span style={sectionTitleStyle}>{roleMode === 'gov' ? '高校就业规模对比' : '高价值规则证据'}</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>{roleMode === 'gov' ? '业务价值：支持区域高校结构分析。' : '业务价值：为培养方案调整提供规则证据。'}</span>}
          style={panelStyle}
        >
          <ReactECharts
            option={roleMode === 'gov' ? buildGovTopSchoolOption(topSchools) : buildRulesLiftOption(rules)}
            style={{ height: 380 }}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>模型评估与算法可信度</span>} style={panelStyle}>
          <Row gutter={[16, 16]}>
            {modelMetricCards.map((item) => (
              <Col xs={24} md={12} xl={6} key={item.key}>
                <Card style={{ ...panelStyle, minHeight: 176 }}>
                  <Statistic
                    title={item.title}
                    value={item.value}
                    precision={item.title.includes('Precision') || item.title.includes('相似度') || item.title.includes('Lift') ? 3 : 0}
                    suffix={item.suffix}
                    styles={{ title: statTitleStyle, content: statValuePrimary }}
                  />
                  <div style={{ color: '#8fb7d8', marginTop: 10, lineHeight: 1.8 }}>{item.description}</div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      </Col>

      {roleMode === 'gov' ? (
        <Col span={24}>
          <Card
            title={<span style={sectionTitleStyle}>区域学科结构分布</span>}
            extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>用于观察专业布局是否与就业结构匹配。</span>}
            style={panelStyle}
          >
            <ReactECharts option={buildDisciplineOption(disciplineData)} style={{ height: 400 }} />
          </Card>
        </Col>
      ) : (
        <Col span={24}>
          <Card
            title={<span style={sectionTitleStyle}>高价值规则摘要</span>}
            extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>建议从 Lift 高且 Support 不低的规则开始解释。</span>}
            style={panelStyle}
          >
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
