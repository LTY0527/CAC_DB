import { Card, Col, Row, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import { getRulesGraphData, getStableRandomRules } from '../utils/dataAdapter'
import { darkTooltip, designTokens, panelStyle, sectionTitleStyle } from '../utils/uiTheme'

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
    legend: { top: 8, textStyle: { color: designTokens.textSecondary } },
    grid: { left: '6%', right: '5%', bottom: '18%', top: '16%', containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: designTokens.textSecondary, interval: 0 },
      axisLine: { lineStyle: { color: designTokens.borderStrong } },
    },
    yAxis: [
      {
        type: 'value',
        name: '比例',
        min: 0,
        max: 100,
        axisLabel: { color: designTokens.textSecondary, formatter: '{value}%' },
        nameTextStyle: { color: designTokens.textMuted },
        splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
      },
      {
        type: 'value',
        name: '提升度',
        min: 1,
        max: 5,
        axisLabel: { color: designTokens.textSecondary },
        nameTextStyle: { color: designTokens.textMuted },
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
          return `${cleanRuleLabel(params.data.source)} → ${cleanRuleLabel(params.data.target)}<br/>提升度：${Number(params.data.value || 0).toFixed(2)}`
        }
        return cleanRuleLabel(params.data.name)
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        force: { repulsion: 280, edgeLength: 140, gravity: 0.08 },
        categories: [{ name: '前项条件' }, { name: '结果项' }],
        data: graphData.nodes.map((node) => ({
          ...node,
          itemStyle: {
            color: node.category === 0 ? '#2563eb' : '#0f766e',
            borderColor: node.category === 0 ? '#93c5fd' : '#99f6e4',
            borderWidth: 2,
          },
          label: {
            show: true,
            color: '#0f172a',
            fontSize: node.category === 0 ? 13 : 12,
            fontWeight: node.category === 0 ? 700 : 600,
            backgroundColor: 'rgba(255,255,255,0.88)',
            borderRadius: 6,
            padding: [4, 6],
            textBorderColor: 'rgba(255,255,255,0.96)',
            textBorderWidth: 2,
          },
        })),
        links: graphData.links,
        lineStyle: {
          color: 'source',
          opacity: 0.8,
          curveness: 0.2,
          width: 2,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 3,
            opacity: 1,
          },
        },
      },
    ],
  }
}

export default function RuleAnalysis({ rulesData = [], loading, error }) {
  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>
  if (error && !rulesData.length) return <div style={{ color: designTokens.danger }}>{error}</div>

  const sampledRules = getStableRandomRules(rulesData, 20)
  const metricRules = sampledRules.slice(0, 12)
  const graphData = getRulesGraphData(sampledRules.slice(0, 10))

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
          <div style={sectionTitleStyle}>规则证据库</div>
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>关联规则指标对比</span>} style={panelStyle}>
          <ReactECharts option={buildRulesMetricsOption(metricRules)} style={{ height: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>规则关系网络</span>} style={panelStyle}>
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
