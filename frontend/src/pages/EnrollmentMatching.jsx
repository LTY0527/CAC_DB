import { Card, Col, Row, Select, Statistic, Table } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { getEnrollmentMajors, getEnrollmentTopByMajor } from '../utils/dataAdapter'
import {
  algorithmTextStyle,
  darkTooltip,
  metaLabelStyle,
  metaValueStyle,
  noteTextStyle,
  panelStyle,
  riskTextStyle,
  sectionTitleStyle,
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
    xAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    yAxis: {
      type: 'category',
      data: topList.map((item) => String(item.top_potential_student_id)),
      axisLabel: { color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    series: [
      {
        name: '匹配分',
        type: 'bar',
        barWidth: 18,
        data: topList.map((item) => ({
          value: Number(item.matching_score || 0),
          raw: item,
          itemStyle: { color: '#30d6ff', borderRadius: [0, 6, 6, 0] },
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
  const avgScore = topList.length ? topList.reduce((sum, item) => sum + Number(item.matching_score || 0), 0) / topList.length : 0
  const avgSample = topList.length ? topList.reduce((sum, item) => sum + Number(item.sample_size || 0), 0) / topList.length : 0

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error) return <div style={{ color: '#ff7875' }}>{error}</div>

  const columns = [
    { title: '生源画像', dataIndex: 'top_potential_student_id' },
    { title: '匹配分', dataIndex: 'matching_score', render: (value) => Number(value || 0).toFixed(2) },
    { title: '样本量', dataIndex: 'sample_size' },
    {
      title: '推荐原因',
      render: (_, record) => `该画像下历史样本在 ${record.target_major} 的平均匹配分较高，可优先作为招生投放与宣传的重点人群。`,
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <div style={sectionTitleStyle}>招生匹配（协同过滤）</div>
              <div style={{ ...noteTextStyle, marginTop: 10 }}>
                业务价值：帮助学校识别“哪些生源画像更可能匹配某个专业”，把招生宣传、投放和咨询资源从经验判断转为数据支持。
              </div>
            </Col>
            <Col xs={24} xl={10}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={metaLabelStyle}>数据载入时间</div>
                  <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
                </Col>
                <Col span={12}>
                  <div style={metaLabelStyle}>当前专业</div>
                  <div style={metaValueStyle}>{currentMajor || '未选择'}</div>
                </Col>
                <Col span={24}>
                  <div style={algorithmTextStyle}>算法说明：当前结果基于协同过滤思想，按生源画像与专业之间的历史匹配分生成 Top-K 候选。</div>
                </Col>
                <Col span={24}>
                  <div style={riskTextStyle}>风险提示：当前“生源画像”字段来自画像维度聚合，不是单个真实考生 ID，适合做招生方向判断，不适合直接做个体录取决策。</div>
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="当前专业" value={currentMajor || '-'} styles={{ title: statTitleStyle, content: statValuePrimary }} />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="平均匹配分" value={avgScore} precision={2} styles={{ title: statTitleStyle, content: statValueBlue }} />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="平均样本量" value={avgSample} precision={0} styles={{ title: statTitleStyle, content: statValueCyan }} />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="Precision@K" value={Number(evalMap['Precision@K']?.metric_value || 0)} precision={3} styles={{ title: statTitleStyle, content: statValuePurple }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>筛选条件</span>} style={panelStyle}>
          <Row gutter={[12, 12]} style={{ marginBottom: 4 }}>
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
            <Col flex="auto">
              <div style={noteTextStyle}>建议答辩时先选择一个代表性专业，再说明“画像匹配分 + 样本量 + 推荐原因”三者如何共同支撑招生判断。</div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>{currentMajor || '专业'} 的高匹配生源画像</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>关键说明：图中每一条代表一个生源画像组合，不代表个体学生。</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildOption(topList)} style={{ height: 360 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>推荐明细</span>} style={panelStyle}>
          <Table rowKey="top_potential_student_id" columns={columns} dataSource={topList} pagination={false} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>评估口径说明</span>} style={panelStyle}>
          <div style={noteTextStyle}>
            当前 Precision@K、Recall@K、HitRate@K 为近似评估，用于说明推荐列表对历史真实专业选择的覆盖能力。
            这类指标适合课程设计和答辩展示，但仍需结合真实招生转化数据进一步校正。
          </div>
        </Card>
      </Col>
    </Row>
  )
}
