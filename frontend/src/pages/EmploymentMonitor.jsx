import { Card, Col, Row, Statistic, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import employmentData from '../assets/mock/employment_summary.json'
import { getEmploymentOverview, getEmploymentBarSeries } from '../utils/dataAdapter'
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

export default function EmploymentMonitor() {
  const safeData = Array.isArray(employmentData) ? employmentData : []
  const overview = getEmploymentOverview(safeData)
  const { majors, series } = getEmploymentBarSeries(safeData)

  const barOption = {
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    ...darkTooltip,
  },
  legend: {
    top: 8,
    textStyle: { color: '#b7dfff' },
  },
  grid: { left: '6%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
  xAxis: {
    type: 'category',
    data: majors,
    axisLabel: {
      color: '#b7dfff',
      interval: 0,
      rotate: 20,
    },
    axisLine: { lineStyle: { color: '#3c6e91' } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#b7dfff' },
    splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
  },
  series: series.map((item, index) => ({
    ...item,
    itemStyle: {
      color: ['#5b8cff', '#b9d532', '#6f7697'][index] || '#5b8cff',
      borderRadius: [6, 6, 0, 0],
    },
  })),
}

  const columns = [
    {
      title: <span style={{ color: '#d9eeff' }}>专业</span>,
      dataIndex: 'major_name',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>学历</span>,
      dataIndex: 'edu_level',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>产业方向</span>,
      dataIndex: 'leading_industry_tag',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>平均起薪</span>,
      dataIndex: 'avg_salary',
      render: (v) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: <span style={{ color: '#d9eeff' }}>入职人数</span>,
      dataIndex: 'emp_count',
    },
  ]

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
      title="覆盖专业数"
      value={overview.majorCount}
      styles={{ title: statTitleStyle, content: statValuePurple }}
      />
    </Card>
  </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>专业 × 学历起薪对比（三大先导）</span>} style={panelStyle}>
          <ReactECharts option={barOption} style={{ height: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>原始数据预览</span>} style={panelStyle}>
          <Table
            rowKey={(record, index) => `${record.major_name}-${record.edu_level}-${index}`}
            columns={columns}
            dataSource={safeData.slice(0, 12)}
            pagination={false}
          />
        </Card>
      </Col>
    </Row>
  )
}