import { Card, Col, Row, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  getRulesGraphData,
  getStableRandomRules,
} from '../utils/dataAdapter'
import { darkTooltip, panelStyle, sectionTitleStyle } from '../utils/uiTheme'

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
          `就业结果：${cleanRuleLabel(item.consequent)}`,
          `支持度：${(Number(item.support || 0) * 100).toFixed(1)}%`,
          `置信度：${(Number(item.confidence || 0) * 100).toFixed(1)}%`,
          `提升度：${Number(item.lift || 0).toFixed(2)}`,
        ].join('<br/>')
      },
    },
    legend: {
      top: 8,
      textStyle: { color: '#b7dfff' },
    },
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
        categories: [{ name: '前置条件' }, { name: '就业去向' }],
        data: graphData.nodes,
        links: graphData.links,
        lineStyle: { color: 'source', opacity: 0.55, curveness: 0.2 },
      },
    ],
  }
}

export default function RuleAnalysis({ rulesData = [], loading, error }) {
  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !rulesData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  const sampledRules = getStableRandomRules(rulesData, 20)
  const metricRules = sampledRules.slice(0, 12)
  const graphData = getRulesGraphData(sampledRules.slice(0, 10))

  const columns = [
    { title: '前置条件', dataIndex: 'antecedent', render: (value) => cleanRuleLabel(value) },
    { title: '就业结果', dataIndex: 'consequent', render: (value) => cleanRuleLabel(value) },
    { title: '支持度', dataIndex: 'support', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
    { title: '置信度', dataIndex: 'confidence', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
    { title: '提升度', dataIndex: 'lift', render: (value) => Number(value || 0).toFixed(2) },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>培养关联规则指标对比</span>} style={panelStyle}>
          <ReactECharts option={buildRulesMetricsOption(metricRules)} style={{ height: 420 }} />
        </Card>
      </Col>
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>随机抽取规则网络</span>} style={panelStyle}>
          <ReactECharts option={buildRulesGraphOption(graphData)} style={{ height: 420 }} />
        </Card>
      </Col>
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>数据库随机抽取规则明细</span>} style={panelStyle}>
          <Table rowKey="key" columns={columns} dataSource={sampledRules} pagination={{ pageSize: 10 }} />
        </Card>
      </Col>
    </Row>
  )
}

export { buildRulesMetricsOption, buildRulesGraphOption }
