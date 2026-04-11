import { Card, Col, Empty, Row, Select, Statistic, Table } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { getEnrollmentMajors, getEnrollmentTopByMajor } from '../utils/dataAdapter'
import {
  axisLabelStyle,
  axisLineStyle,
  designTokens,
  darkTooltip,
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  sectionTitleStyle,
  splitLineStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

function buildOption(topList = []) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...darkTooltip,
      formatter(params) {
        const item = params?.[0]?.data?.raw || {}
        return [
          `<strong>${item.target_major || '-'}</strong>`,
          `生源画像：${item.top_potential_student_id || '-'}`,
          `匹配分：${Number(item.matching_score || 0).toFixed(2)}`,
          `样本量：${item.sample_size || 0}`,
        ].join('<br/>')
      },
    },
    grid: { left: '16%', right: '6%', bottom: '10%', top: '10%', containLabel: true },
    xAxis: { type: 'value', axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    yAxis: {
      type: 'category',
      data: topList.map((item) => String(item.top_potential_student_id)),
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
    },
    series: [
      {
        name: '匹配分',
        type: 'bar',
        barWidth: 18,
        data: topList.map((item) => ({
          value: Number(item.matching_score || 0),
          raw: item,
          itemStyle: { color: designTokens.accent, borderRadius: [0, 6, 6, 0] },
        })),
      },
    ],
  }
}

export default function EnrollmentMatching({
  enrollmentData = [],
  enrollmentEvalData = [],
  dataLoadedAt = '',
  loading,
  error,
}) {
  const majors = useMemo(() => getEnrollmentMajors(enrollmentData), [enrollmentData])
  const [major, setMajor] = useState('')
  const [topN, setTopN] = useState(10)
  const [minScore, setMinScore] = useState(0)

  const evalMap = Object.fromEntries((enrollmentEvalData || []).map((item) => [item.metric_name, item]))
  const currentMajor = major || majors[0] || ''
  const topList = getEnrollmentTopByMajor(enrollmentData, currentMajor, topN, minScore)
  const avgScore = topList.length
    ? topList.reduce((sum, item) => sum + Number(item.matching_score || 0), 0) / topList.length
    : 0
  const avgSample = topList.length
    ? topList.reduce((sum, item) => sum + Number(item.sample_size || 0), 0) / topList.length
    : 0
  const hasRows = Array.isArray(enrollmentData) && enrollmentData.length > 0

  if (loading) {
    return <div>数据加载中...</div>
  }

  const columns = [
    { title: '生源画像', dataIndex: 'top_potential_student_id' },
    {
      title: '匹配分',
      dataIndex: 'matching_score',
      render: (value) => Number(value || 0).toFixed(2),
    },
    { title: '样本量', dataIndex: 'sample_size' },
    {
      title: '推荐原因',
      render: (_, record) => `该画像下历史样本在 ${record.target_major || '-'} 的平均匹配分较高。`,
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} xl={16}>
              <div style={sectionTitleStyle}>招生匹配（协同过滤）</div>
            </Col>
            <Col xs={24} xl={8}>
              <div style={metaLabelStyle}>数据载入时间</div>
              <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="当前专业"
            value={currentMajor || '-'}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="平均匹配分"
            value={avgScore}
            precision={2}
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="平均样本量"
            value={avgSample}
            precision={0}
            styles={{ title: statTitleStyle, content: statValueCyan }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="Precision@K"
            value={Number(evalMap['Precision@K']?.metric_value || 0)}
            precision={3}
            styles={{ title: statTitleStyle, content: statValuePurple }}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>筛选条件</span>} style={panelStyle}>
          <Row gutter={[12, 12]}>
            <Col>
              <Select
                value={currentMajor || undefined}
                onChange={setMajor}
                options={majors.map((item) => ({ label: item, value: item }))}
                style={{ width: 220 }}
                placeholder="选择专业"
                disabled={!majors.length}
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
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>{currentMajor || '专业'}的高匹配生源画像</span>} style={panelStyle}>
          {topList.length ? (
            <ReactECharts option={buildOption(topList)} style={{ height: 360 }} />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={hasRows ? '当前筛选条件下暂无匹配样本' : '暂无招生匹配样本'}
              style={{ padding: '48px 0' }}
            />
          )}
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>推荐明细</span>} style={panelStyle}>
          <Table
            rowKey="top_potential_student_id"
            columns={columns}
            dataSource={topList}
            pagination={false}
            locale={{
              emptyText: hasRows ? '当前筛选条件下暂无匹配样本' : '暂无招生匹配样本',
            }}
          />
          {!hasRows && error ? (
            <div style={{ marginTop: 12, color: designTokens.textMuted, fontSize: 12 }}>
              当前页已使用可用数据继续渲染，招生匹配结果暂未返回。
            </div>
          ) : null}
        </Card>
      </Col>
    </Row>
  )
}
