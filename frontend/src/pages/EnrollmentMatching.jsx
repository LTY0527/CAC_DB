import { Card, Col, Row, Select, Table } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { getEnrollmentMajors, getEnrollmentTopByMajor } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  darkTooltip,
  noteTextStyle,
} from '../utils/uiTheme'

export default function EnrollmentMatching({
  enrollmentData = [],
  loading,
  error,
}) {
  const majors = useMemo(() => getEnrollmentMajors(enrollmentData), [enrollmentData])
  const [major, setMajor] = useState('')
  const [topN, setTopN] = useState(10)
  const [minScore, setMinScore] = useState(0)

  const currentMajor = major || majors[0] || ''
  const topList = getEnrollmentTopByMajor(enrollmentData, currentMajor, topN, minScore)

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error) return <div style={{ color: '#ff7875' }}>{error}</div>

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    grid: { left: '6%', right: '4%', bottom: '12%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: topList.map((item) => String(item.top_potential_student_id)),
      axisLabel: { color: '#b7dfff', rotate: 0 },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        name: '匹配分',
        type: 'bar',
        barWidth: 22,
        data: topList.map((item) => Number(item.matching_score)),
        itemStyle: {
          color: '#30d6ff',
          borderRadius: [6, 6, 0, 0],
        },
      },
    ],
  }

  const columns = [
    { title: '潜在生源ID', dataIndex: 'top_potential_student_id' },
    {
      title: '匹配分',
      dataIndex: 'matching_score',
      render: (value) => Number(value).toFixed(2),
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>{currentMajor || '专业'} 匹配结果（Top {topN}）</span>}
          style={panelStyle}
        >
          <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
            <Col>
              <Select
                value={currentMajor || undefined}
                onChange={setMajor}
                options={majors.map((item) => ({ label: item, value: item }))}
                style={{ width: 220 }}
                placeholder="选择专业"
              />
            </Col>

            <Col>
              <Select
                value={topN}
                onChange={setTopN}
                style={{ width: 140 }}
                options={[
                  { label: 'Top 5', value: 5 },
                  { label: 'Top 10', value: 10 },
                  { label: 'Top 15', value: 15 },
                ]}
              />
            </Col>

            <Col>
              <Select
                value={minScore}
                onChange={setMinScore}
                style={{ width: 180 }}
                options={[
                  { label: '全部候选', value: 0 },
                  { label: '优先关注', value: 7.5 },
                  { label: '重点跟进', value: 7.8 },
                  { label: '核心目标', value: 8.0 },
                ]}
              />
            </Col>
          </Row>

          <ReactECharts option={option} style={{ height: 340 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>明细表</span>} style={panelStyle}>
          <Table
            rowKey="top_potential_student_id"
            columns={columns}
            dataSource={topList}
            pagination={false}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>招生分析提示</span>} style={panelStyle}>
          <div style={noteTextStyle}>
            当前页面展示的是某个专业对应的高匹配潜在生源分布结果。后续可以继续补充录取分数、位次、生源地域、报名热度等字段，形成更完整的招生决策分析。
          </div>
        </Card>
      </Col>
    </Row>
  )
}
