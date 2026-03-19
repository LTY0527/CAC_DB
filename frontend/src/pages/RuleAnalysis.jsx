// import { Card, Table, Row, Col } from 'antd'
// import ReactECharts from 'echarts-for-react'
// import rules from '../assets/rules.json'

// const panelStyle = {
//   background: 'linear-gradient(180deg, rgba(7,26,47,0.96) 0%, rgba(4,18,34,0.96) 100%)',
//   border: '1px solid #1b4f7d',
//   borderRadius: 10,
//   boxShadow: '0 0 12px rgba(0, 153, 255, 0.12)',
// }

// const titleStyle = {
//   color: '#d9eeff',
//   fontSize: 16,
//   fontWeight: 600,
// }

// export default function RuleAnalysis() {
//   const tableData = rules.map((item, index) => ({
//     key: index,
//     antecedent: item.antecedent ?? '',
//     consequent: item.consequent ?? '',
//     confidence: Number(item.confidence),
//     lift: Number(item.lift),
//   }))

//   const columns = [
//     {
//       title: <span style={{ color: '#d9eeff' }}>前件</span>,
//       dataIndex: 'antecedent',
//     },
//     {
//       title: <span style={{ color: '#d9eeff' }}>后件</span>,
//       dataIndex: 'consequent',
//     },
//     {
//       title: <span style={{ color: '#d9eeff' }}>置信度</span>,
//       dataIndex: 'confidence',
//       render: (value) => <span style={{ color: '#8fd7ff' }}>{Number(value).toFixed(3)}</span>,
//     },
//     {
//       title: <span style={{ color: '#d9eeff' }}>提升度</span>,
//       dataIndex: 'lift',
//       render: (value) => <span style={{ color: '#30d6ff' }}>{Number(value).toFixed(3)}</span>,
//     },
//   ]

//   const chartOption = {
//     backgroundColor: 'transparent',
//     tooltip: {
//       trigger: 'axis',
//       backgroundColor: 'rgba(6, 21, 34, 0.95)',
//       borderColor: '#2b78b8',
//       textStyle: { color: '#d8f0ff' },
//     },
//     legend: {
//       top: 10,
//       textStyle: { color: '#b7dfff' },
//       data: ['置信度', '提升度'],
//     },
//     grid: {
//       left: '4%',
//       right: '4%',
//       bottom: '10%',
//       top: '18%',
//       containLabel: true,
//     },
//     xAxis: {
//       type: 'category',
//       axisLabel: {
//         rotate: 30,
//         color: '#b7dfff',
//       },
//       axisLine: { lineStyle: { color: '#3c6e91' } },
//       data: tableData.map((_, index) => `规则${index + 1}`),
//     },
//     yAxis: {
//       type: 'value',
//       axisLine: { lineStyle: { color: '#3c6e91' } },
//       splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
//       axisLabel: { color: '#b7dfff' },
//     },
//     series: [
//       {
//         name: '置信度',
//         type: 'bar',
//         barWidth: 20,
//         data: tableData.map(item => item.confidence),
//         itemStyle: {
//           color: '#1dd1ff',
//           borderRadius: [4, 4, 0, 0],
//         },
//       },
//       {
//         name: '提升度',
//         type: 'bar',
//         barWidth: 20,
//         data: tableData.map(item => item.lift),
//         itemStyle: {
//           color: '#4c8dff',
//           borderRadius: [4, 4, 0, 0],
//         },
//       },
//     ],
//   }

//   return (
//     <Row gutter={[16, 16]}>
//       <Col span={24}>
//         <Card title={<span style={titleStyle}>专业—就业关联规则分析图</span>} variant={false} style={panelStyle}>
//           <ReactECharts option={chartOption} style={{ height: 360 }} />
//         </Card>
//       </Col>

//       <Col span={24}>
//         <Card title={<span style={titleStyle}>关联规则明细表</span>} variant={false} style={panelStyle}>
//           <Table
//             columns={columns}
//             dataSource={tableData}
//             pagination={{ pageSize: 8 }}
//             bordered={false}
//             style={{ background: 'transparent' }}
//             rowClassName={() => 'dark-table-row'}
//           />
//         </Card>
//       </Col>
//     </Row>
//   )
// }

import { Card, Table, Row, Col } from 'antd'
import ReactECharts from 'echarts-for-react'
import rulesData from '../assets/mock/major_matching_rules.json'
import { getRulesTableData, getRulesGraphData } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  darkTooltip,
} from '../utils/uiTheme'

export default function RuleAnalysis() {
  const tableData = getRulesTableData(rulesData)
  const graphData = getRulesGraphData(rulesData)

  const columns = [
    {
      title: <span style={{ color: '#d9eeff' }}>前件</span>,
      dataIndex: 'antecedent',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>后件</span>,
      dataIndex: 'consequent',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>置信度</span>,
      dataIndex: 'confidence',
      render: (value) => <span style={{ color: '#8fd7ff' }}>{Number(value).toFixed(3)}</span>,
    },
    {
      title: <span style={{ color: '#d9eeff' }}>提升度</span>,
      dataIndex: 'lift',
      render: (value) => <span style={{ color: '#30d6ff' }}>{Number(value).toFixed(3)}</span>,
    },
  ]

  const barOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    legend: {
      top: 10,
      textStyle: { color: '#b7dfff' },
      data: ['置信度', '提升度'],
    },
    grid: { left: '4%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      axisLabel: { rotate: 25, color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
      data: tableData.map((_, index) => `规则${index + 1}`),
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        name: '置信度',
        type: 'bar',
        data: tableData.map(item => item.confidence),
        itemStyle: {
          color: '#2fe1ff',
          borderRadius: [5, 5, 0, 0],
        },
      },
      {
        name: '提升度',
        type: 'bar',
        data: tableData.map(item => item.lift),
        itemStyle: {
          color: '#4b86ff',
          borderRadius: [5, 5, 0, 0],
        },
      },
    ],
  }

  const graphOption = {
    backgroundColor: 'transparent',
    tooltip: {
      ...darkTooltip,
    },
    legend: [
      {
        top: 10,
        textStyle: { color: '#b7dfff' },
        data: ['前件', '后件'],
      },
    ],
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        label: {
          show: true,
          color: '#d9eeff',
        },
        force: {
          repulsion: 260,
          edgeLength: 140,
        },
        categories: [
          { name: '前件' },
          { name: '后件' },
        ],
        data: graphData.nodes,
        links: graphData.links,
        lineStyle: {
          color: 'source',
          curveness: 0.2,
          opacity: 0.7,
        },
      },
    ],
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>专业—产业关联网络图</span>} style={panelStyle}>
          <ReactECharts option={graphOption} style={{ height: 430 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>置信度 / 提升度对比</span>} style={panelStyle}>
          <ReactECharts option={barOption} style={{ height: 340 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>关联规则明细表</span>} style={panelStyle}>
          <Table
            columns={columns}
            dataSource={tableData}
            pagination={{ pageSize: 8 }}
            bordered={false}
          />
        </Card>
      </Col>
    </Row>
  )
}