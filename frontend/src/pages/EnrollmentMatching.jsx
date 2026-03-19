import { Card, Col, Row, Select, Table } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import enrollmentData from '../assets/mock/enrollment_matching.json'
import { getEnrollmentMajors, getEnrollmentTopByMajor } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  darkTooltip,
  noteTextStyle,
} from '../utils/uiTheme'

export default function EnrollmentMatching() {
  const majors = useMemo(() => getEnrollmentMajors(enrollmentData), [])
  const [major, setMajor] = useState(majors[0])
  const topList = getEnrollmentTopByMajor(enrollmentData, major)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    grid: { left: '6%', right: '4%', bottom: '12%', top: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: topList.map(item => String(item.top_potential_student_id)),
      axisLabel: { color: '#b7dfff', rotate: 25 },
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
        data: topList.map(item => Number(item.matching_score)),
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
      render: value => Number(value).toFixed(2),
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>专业匹配 Top10</span>} style={panelStyle}>
          <Select
            value={major}
            onChange={setMajor}
            options={majors.map(item => ({ label: item, value: item }))}
            style={{ width: 260, marginBottom: 16 }}
          />
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
        <Card title={<span style={sectionTitleStyle}>当前限制说明</span>} style={panelStyle}>
          <div style={noteTextStyle}>
            当前数据只有 target_major、top_potential_student_id、matching_score，
            适合先做 Top10 排行榜。若后续补充学生画像字段，再升级为雷达图。
          </div>
        </Card>
      </Col>
    </Row>
  )
}