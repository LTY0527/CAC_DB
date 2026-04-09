import { Card, Col, Row, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  getRuleMetricExplanations,
  getRulesGraphData,
  getStableRandomRules,
} from '../utils/dataAdapter'
import {
  algorithmTextStyle,
  darkTooltip,
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  riskTextStyle,
  sectionTitleStyle,
} from '../utils/uiTheme'

function cleanRuleLabel(text = '') {
  return String(text).replace(/[[\]"]/g, '').replace(/,/g, ' / ').replace(/\s+/g, ' ').trim()
}

function buildRulesMetricsOption(data = []) {
  const labels = data.map((item, index) => {
    const label = cleanRuleLabel(item.antecedent || `规则${index + 1}`)
    return label.length > 12 ? `${label.slice(0, 12)}...` : label
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const index = params?.[0]?.dataIndex ?? 0
        const item = data[index] || {}
        return [
          `<strong>${cleanRuleLabel(item.antecedent)}</strong>`,
          `结果项：${cleanRuleLabel(item.consequent)}`,
          `支持度：${(Number(item.support || 0) * 100).toFixed(1)}%`,
          `置信度：${(Number(item.confidence || 0) * 100).toFixed(1)}%`,
          `提升度：${Number(item.lift || 0).toFixed(2)}`,
        ].join('<br/>')
      },
    },
    legend: { top: 8, textStyle: { color: '#b7dfff' } },
    grid: { left: '6%', right: '5%', bottom: '18%', top: '16%', containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#b7dfff', interval: 0 },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '比例',
        min: 0,
        max: 100,
        axisLabel: { color: '#b7dfff', formatter: '{value}%' },
        nameTextStyle: { color: '#b7dfff' },
        splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
      },
      {
        type: 'value',
        name: '提升度',
        min: 1,
        max: 5,
        axisLabel: { color: '#b7dfff' },
        nameTextStyle: { color: '#b7dfff' },
      },
    ],
    series: [
      {
        name: '置信度',
        type: 'bar',
        barMaxWidth: 20,
        data: data.map((item) => Number((Number(item.confidence || 0) * 100).toFixed(1))),
        itemStyle: { color: '#39c4ff', borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '支持度',
        type: 'bar',
        barMaxWidth: 20,
        data: data.map((item) => Number((Number(item.support || 0) * 100).toFixed(1))),
        itemStyle: { color: '#67e8f9', borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '提升度',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: data.map((item) => Number(item.lift || 0)),
        lineStyle: { width: 3, color: '#f7c948' },
        itemStyle: { color: '#f7c948' },
      },
    ],
  }
}

function buildRulesGraphOption(graphData) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      ...darkTooltip,
      formatter(params) {
        if (params.dataType === 'edge') {
          return `${cleanRuleLabel(params.data.source)} -> ${cleanRuleLabel(params.data.target)}<br/>提升度：${Number(params.data.value || 0).toFixed(2)}`
        }
        return cleanRuleLabel(params.data.name)
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        label: { show: true, color: '#d9eeff' },
        force: { repulsion: 280, edgeLength: 140, gravity: 0.08 },
        categories: [{ name: '前项条件' }, { name: '结果项' }],
        data: graphData.nodes,
        links: graphData.links,
        lineStyle: { color: 'source', opacity: 0.55, curveness: 0.2 },
      },
    ],
  }
}

export default function RuleAnalysis({ rulesData = [], dataLoadedAt = '', loading, error }) {
  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !rulesData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  const sampledRules = getStableRandomRules(rulesData, 20)
  const metricRules = sampledRules.slice(0, 12)
  const graphData = getRulesGraphData(sampledRules.slice(0, 10))
  const explanations = getRuleMetricExplanations()

  const columns = [
    { title: '前项条件', dataIndex: 'antecedent', render: (value) => cleanRuleLabel(value) },
    { title: '结果项', dataIndex: 'consequent', render: (value) => cleanRuleLabel(value) },
    { title: '支持度', dataIndex: 'support', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
    { title: '置信度', dataIndex: 'confidence', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
    { title: '提升度', dataIndex: 'lift', render: (value) => Number(value || 0).toFixed(2) },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <div style={sectionTitleStyle}>规则证据库</div>
              <div style={{ color: '#cfe9ff', lineHeight: 1.9, marginTop: 10 }}>
                业务价值：把“哪些专业特征、技能特征、行业去向常常同时出现”沉淀为可解释的证据，为培养方案优化提供依据而不是只靠经验判断。
              </div>
            </Col>
            <Col xs={24} xl={10}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={metaLabelStyle}>数据载入时间</div>
                  <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
                </Col>
                <Col span={12}>
                  <div style={metaLabelStyle}>规则样本数</div>
                  <div style={metaValueStyle}>{sampledRules.length} 条展示规则</div>
                </Col>
                <Col span={24}>
                  <div style={algorithmTextStyle}>算法说明：通过 FP-Growth 挖掘高频项集，再从中生成支持度、置信度、提升度三类规则指标。</div>
                </Col>
                <Col span={24}>
                  <div style={riskTextStyle}>风险提示：关联规则反映的是统计共现关系，不直接等同于因果关系，需结合培养场景二次判断。</div>
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>关联规则指标对比</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>建议优先解释 Lift 高、Confidence 稳定且 Support 不低的规则。</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildRulesMetricsOption(metricRules)} style={{ height: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>指标业务解释</span>} style={panelStyle}>
          <Row gutter={[16, 16]}>
            {explanations.map((item) => (
              <Col xs={24} md={8} key={item.key}>
                <Card style={{ ...panelStyle, minHeight: 160 }}>
                  <div style={{ color: '#eef4ff', fontSize: 18, fontWeight: 600, marginBottom: 12 }}>{item.metric}</div>
                  <div style={{ color: '#b7dfff', lineHeight: 1.9 }}>{item.explanation}</div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>规则关系网络</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>适合在答辩时展示“从条件到结果”的规则传递关系。</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildRulesGraphOption(graphData)} style={{ height: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>规则明细</span>} style={panelStyle}>
          <Table rowKey="key" columns={columns} dataSource={sampledRules} pagination={{ pageSize: 10 }} />
        </Card>
      </Col>
    </Row>
  )
}

export { buildRulesMetricsOption, buildRulesGraphOption }
