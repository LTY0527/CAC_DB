// import React from 'react'
// import { Card, Col, Row, Statistic } from 'antd'
// import ReactECharts from 'echarts-for-react'

// const panelStyle = {
//   background: 'linear-gradient(180deg, rgba(5,22,42,0.98) 0%, rgba(3,14,28,0.98) 100%)',
//   border: '1px solid #1e5d8f',
//   borderRadius: 10,
//   boxShadow: '0 0 18px rgba(0, 153, 255, 0.16), inset 0 0 20px rgba(0, 80, 160, 0.12)',
//   overflow: 'hidden',
// }

// const titleStyle = {
//   color: '#d9eeff',
//   fontSize: 16,
//   fontWeight: 700,
//   letterSpacing: 0.5,
// }

// const statCardStyle = {
//   ...panelStyle,
//   minHeight: 124,
// }

// export default function Dashboard() {
//   const trendOption = {
//     backgroundColor: 'transparent',
//     tooltip: {
//       trigger: 'axis',
//       backgroundColor: 'rgba(6, 21, 34, 0.96)',
//       borderColor: '#2b78b8',
//       textStyle: { color: '#d8f0ff' },
//     },
//     legend: {
//       top: 8,
//       textStyle: { color: '#b7dfff' },
//       data: ['就业率', '留沪率'],
//     },
//     grid: {
//       left: '5%',
//       right: '4%',
//       bottom: '8%',
//       top: '18%',
//       containLabel: true,
//     },
//     xAxis: {
//       type: 'category',
//       data: ['2021', '2022', '2023', '2024', '2025'],
//       axisLine: { lineStyle: { color: '#3c6e91' } },
//       axisTick: { show: false },
//       axisLabel: { color: '#b7dfff' },
//     },
//     yAxis: {
//       type: 'value',
//       min: 0,
//       max: 100,
//       axisLine: { show: false },
//       splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
//       axisLabel: { color: '#b7dfff' },
//     },
//     series: [
//       {
//         name: '就业率',
//         type: 'line',
//         smooth: true,
//         symbol: 'circle',
//         symbolSize: 8,
//         data: [88, 89, 91, 90, 92],
//         lineStyle: { width: 3, color: '#2fe1ff' },
//         itemStyle: { color: '#2fe1ff' },
//         areaStyle: { color: 'rgba(47, 225, 255, 0.10)' },
//       },
//       {
//         name: '留沪率',
//         type: 'line',
//         smooth: true,
//         symbol: 'circle',
//         symbolSize: 8,
//         data: [52, 55, 57, 58, 60],
//         lineStyle: { width: 3, color: '#4b86ff' },
//         itemStyle: { color: '#4b86ff' },
//         areaStyle: { color: 'rgba(75, 134, 255, 0.08)' },
//       },
//     ],
//   }

//   const salaryOption = {
//     backgroundColor: 'transparent',
//     tooltip: {
//       trigger: 'axis',
//       backgroundColor: 'rgba(6, 21, 34, 0.96)',
//       borderColor: '#2b78b8',
//       textStyle: { color: '#d8f0ff' },
//     },
//     grid: {
//       left: '10%',
//       right: '6%',
//       bottom: '12%',
//       top: '12%',
//       containLabel: true,
//     },
//     xAxis: {
//       type: 'category',
//       data: ['计算机', '金融', '管理', '机械', '外语', '设计'],
//       axisLine: { lineStyle: { color: '#3c6e91' } },
//       axisTick: { show: false },
//       axisLabel: {
//         color: '#b7dfff',
//         interval: 0,
//       },
//     },
//     yAxis: {
//       type: 'value',
//       axisLine: { show: false },
//       splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
//       axisLabel: { color: '#b7dfff' },
//     },
//     series: [
//       {
//         name: '平均月薪',
//         type: 'bar',
//         barWidth: 28,
//         data: [14500, 13200, 11800, 10900, 9800, 10100],
//         itemStyle: {
//           color: '#2cc8ff',
//           borderRadius: [6, 6, 0, 0],
//           shadowBlur: 10,
//           shadowColor: 'rgba(44,200,255,0.25)',
//         },
//       },
//     ],
//   }

//   return (
//     <Row gutter={[16, 16]}>
//       <Col span={6}>
//         <Card variant="borderless" style={statCardStyle}>
//           <Statistic
//             title={<span style={titleStyle}>高校数量</span>}
//             value={42}
//             styles={{ content: { color: '#30d6ff' } }}
//           />
//         </Card>
//       </Col>

//       <Col span={6}>
//         <Card variant="borderless" style={statCardStyle}>
//           <Statistic
//             title={<span style={titleStyle}>平均就业率</span>}
//             value={91.2}
//             suffix="%"
//             styles={{ content: { color: '#30d6ff' } }}
//           />
//         </Card>
//       </Col>

//       <Col span={6}>
//         <Card variant="borderless" style={statCardStyle}>
//           <Statistic
//             title={<span style={titleStyle}>平均留沪率</span>}
//             value={58.4}
//             suffix="%"
//             styles={{ content: { color: '#30d6ff' } }}
//           />
//         </Card>
//       </Col>

//       <Col span={6}>
//         <Card variant="borderless" style={statCardStyle}>
//           <Statistic
//             title={<span style={titleStyle}>平均月薪</span>}
//             value={12680}
//             prefix="¥"
//             styles={{ content: { color: '#30d6ff' } }}
//           />
//         </Card>
//       </Col>

//       <Col span={17}>
//         <Card
//           title={<span style={titleStyle}>就业率 / 留沪率趋势</span>}
//           variant="borderless"
//           style={panelStyle}
//         >
//           <ReactECharts option={trendOption} style={{ height: 400 }} />
//         </Card>
//       </Col>

//       <Col span={7}>
//         <Card
//           title={<span style={titleStyle}>专业平均月薪对比</span>}
//           variant="borderless"
//           style={panelStyle}
//         >
//           <ReactECharts option={salaryOption} style={{ height: 400 }} />
//         </Card>
//       </Col>
//     </Row>
//   )
// }

import { Card, Col, Row, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import employmentData from '../assets/mock/employment_summary.json'
import forecastData from '../assets/mock/salary_forecast.json'
import rulesData from '../assets/mock/major_matching_rules.json'
import { getEmploymentOverview, getForecastData, getRulesTableData } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValuePrimary,
  statValueBlue,
  statValueCyan,
  statValuePurple,
  darkTooltip,
} from '../utils/uiTheme'

export default function Dashboard() {
  const overview = getEmploymentOverview(employmentData)
  const forecast = getForecastData(forecastData)
  const rules = getRulesTableData(rulesData).sort((a, b) => b.lift - a.lift).slice(0, 5)

  const overviewOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: forecast.months,
      axisLabel: { color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        name: '预测起薪',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 9,
        lineStyle: {
          width: 3,
          color: '#34d3ff',
        },
        itemStyle: {
          color: '#34d3ff',
        },
        areaStyle: {
          color: 'rgba(52, 211, 255, 0.10)',
        },
        data: forecast.values,
      },
    ],
  }

  const liftOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    grid: { left: '8%', right: '4%', bottom: '10%', top: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rules.map((_, i) => `规则${i + 1}`),
      axisLabel: { color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        name: 'Lift',
        type: 'bar',
        barWidth: 28,
        data: rules.map(item => item.lift),
        itemStyle: {
          color: '#5b7be0',
          borderRadius: [6, 6, 0, 0],
        },
      },
    ],
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="总入职人数"
            value={overview.totalEmpCount}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>

      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="加权平均起薪"
            value={Number(overview.avgSalaryWeighted.toFixed(2))}
            prefix="¥"
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>

      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="三大先导人数"
            value={overview.leadEmpCount}
            styles={{ title: statTitleStyle, content: statValueCyan }}
          />
        </Card>
      </Col>

      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="最高预测起薪"
            value={forecast.values[forecast.values.length - 1] || 0}
            prefix="¥"
            precision={2}
            styles={{ title: statTitleStyle, content: statValuePurple }}
          />
        </Card>
      </Col>

      <Col span={14}>
        <Card title={<span style={sectionTitleStyle}>起薪预测总览</span>} style={panelStyle}>
          <ReactECharts option={overviewOption} style={{ height: 380 }} />
        </Card>
      </Col>

      <Col span={10}>
        <Card title={<span style={sectionTitleStyle}>高提升度规则 Top5</span>} style={panelStyle}>
          <ReactECharts option={liftOption} style={{ height: 380 }} />
        </Card>
      </Col>
    </Row>
  )
}
