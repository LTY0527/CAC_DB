import { Card, Col, Row, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import { useLocation } from 'react-router-dom'
import {
  getPublicIndustryData,
  getPublicOverview,
  getPublicSchoolComparison,
  getPublicTopMajors,
} from '../utils/dataAdapter'
import {
  darkTooltip,
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValuePrimary,
} from '../utils/uiTheme'

function buildPublicIndustryOption(data = []) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', ...darkTooltip },
    legend: {
      bottom: 0,
      textStyle: { color: '#b7dfff' },
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '72%'],
        center: ['50%', '46%'],
        label: { color: '#d9eeff' },
        data,
      },
    ],
  }
}

function buildPublicMajorBarOption(data = []) {
  const values = data.map((item) => Number(item.avg_salary || 0))
  const min = values.length ? Math.floor((Math.min(...values) - 500) / 500) * 500 : 0
  const max = values.length ? Math.ceil((Math.max(...values) + 500) / 500) * 500 : 20000

  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    grid: { left: '8%', right: '4%', bottom: '10%', top: '12%', containLabel: true },
    xAxis: {
      type: 'value',
      min,
      max,
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    yAxis: {
      type: 'category',
      data: data.map((item) => item.major_name),
      axisLabel: { color: '#d9eeff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    series: [
      {
        type: 'bar',
        data: data.map((item) => Number(item.avg_salary || 0)),
        barWidth: 18,
        itemStyle: {
          color: '#39c4ff',
          borderRadius: [0, 8, 8, 0],
        },
      },
    ],
  }
}

function buildSchoolCompareOption(data = []) {
  const labels = data.map((item) => `${item.school_name}\n${item.major_name}`)
  const salaryValues = data.map((item) => Number(item.avg_salary || 0))
  const rateValues = data.map((item) => Number(item.employment_rate || 0))
  const salaryMin = salaryValues.length ? Math.floor((Math.min(...salaryValues) - 500) / 500) * 500 : 0
  const salaryMax = salaryValues.length ? Math.ceil((Math.max(...salaryValues) + 500) / 500) * 500 : 20000

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const index = params?.[0]?.dataIndex ?? 0
        const item = data[index] || {}
        return [
          `<strong>${item.school_name || '-'}</strong>`,
          `专业：${item.major_name || '-'}`,
          `就业率：${Number(item.employment_rate || 0).toFixed(1)}%`,
          `平均薪资：￥${Number(item.avg_salary || 0).toLocaleString('zh-CN')}`,
        ].join('<br/>')
      },
    },
    legend: {
      top: 8,
      textStyle: { color: '#b7dfff' },
    },
    grid: { left: '6%', right: '8%', bottom: '18%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { color: '#d9eeff', interval: 0, lineHeight: 18, fontSize: 12 },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '平均薪资',
        min: salaryMin,
        max: salaryMax,
        axisLabel: { color: '#b7dfff' },
        nameTextStyle: { color: '#b7dfff' },
        splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
      },
      {
        type: 'value',
        name: '就业率',
        min: 80,
        max: 100,
        axisLabel: { color: '#b7dfff', formatter: '{value}%' },
        nameTextStyle: { color: '#b7dfff' },
      },
    ],
    series: [
      {
        name: '平均薪资',
        type: 'bar',
        barMaxWidth: 24,
        data: salaryValues,
        itemStyle: { color: '#39c4ff', borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '就业率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: rateValues,
        lineStyle: { width: 3, color: '#67e8f9' },
        itemStyle: { color: '#67e8f9' },
      },
    ],
  }
}

function PublicHome({ employmentData = [] }) {
  const overview = getPublicOverview(employmentData)
  const industryData = getPublicIndustryData(employmentData)
  const topMajors = getPublicTopMajors(employmentData)

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12}>
        <Card style={panelStyle}>
          <Statistic
            title="当年全市平均就业率"
            value={overview.employmentRate}
            suffix="%"
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12}>
        <Card style={panelStyle}>
          <Statistic
            title="当年平均薪资"
            value={overview.avgSalary}
            prefix="￥"
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>

      <Col xs={24} xl={10}>
        <Card title={<span style={sectionTitleStyle}>热门行业去向</span>} style={panelStyle}>
          <ReactECharts option={buildPublicIndustryOption(industryData)} style={{ height: 360 }} />
        </Card>
      </Col>

      <Col xs={24} xl={14}>
        <Card title={<span style={sectionTitleStyle}>起薪 Top 5 专业</span>} style={panelStyle}>
          <ReactECharts option={buildPublicMajorBarOption(topMajors)} style={{ height: 360 }} />
        </Card>
      </Col>
    </Row>
  )
}

function PublicSchoolCompare({ employmentData = [] }) {
  const schoolComparison = getPublicSchoolComparison(employmentData)

  return (
    <Card title={<span style={sectionTitleStyle}>院校对比：高就业率且高薪资专业</span>} style={panelStyle}>
      <ReactECharts option={buildSchoolCompareOption(schoolComparison)} style={{ height: 460 }} />
    </Card>
  )
}

export default function PublicWorkspace({ employmentData = [] }) {
  const location = useLocation()

  if (location.pathname === '/school-compare') {
    return <PublicSchoolCompare employmentData={employmentData} />
  }

  return <PublicHome employmentData={employmentData} />
}

export { buildPublicIndustryOption, buildPublicMajorBarOption, buildSchoolCompareOption }
