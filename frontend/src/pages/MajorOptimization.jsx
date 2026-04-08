import { Card, Col, Empty, Row, Select, Space, Statistic, Table, Tag } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getEmploymentFilterOptions,
  getMajorActionColor,
  getMajorOptimizationOverview,
  getMajorOptimizationRows,
} from '../utils/dataAdapter'
import {
  darkTooltip,
  noteTextStyle,
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

function getActionColor(action = '') {
  if (action === '建议扩招') return '#37c66d'
  if (action === '建议缩招') return '#ff6b6b'
  if (action === '建议调优') return '#f7c948'
  return '#58a6ff'
}

function buildMajorOptimizationScatterOption(rows = []) {
  const quadrants = [
    { name: '高投入高产出', x0: 80, x1: 100, y0: 600, y1: 680, color: 'rgba(55, 198, 109, 0.08)' },
    { name: '高投入低产出', x0: 0, x1: 80, y0: 600, y1: 680, color: 'rgba(255, 107, 107, 0.08)' },
    { name: '低投入高产出', x0: 80, x1: 100, y0: 520, y1: 600, color: 'rgba(88, 166, 255, 0.08)' },
    { name: '低投入低产出', x0: 0, x1: 80, y0: 520, y1: 600, color: 'rgba(247, 201, 72, 0.08)' },
  ]

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      ...darkTooltip,
      formatter(params) {
        const item = params?.data?.raw || {}
        return [
          `<strong>${item.major_name || '-'}</strong>`,
          `学校：${item.school_name || '-'}`,
          `录取分：${Number(item.admission_score_avg || 0).toFixed(0)}`,
          `培养得分：${Number(item.training_quality_score || 0).toFixed(1)}`,
          `就业率：${Number(item.employment_rate || 0).toFixed(1)}%`,
          `产业匹配：${Number(item.industry_match_score || 0).toFixed(1)}`,
          `在校规模：${formatNumber(item.enrollment_count || 0)}`,
          `建议：${item.major_action || '-'}`,
        ].join('<br/>')
      },
    },
    xAxis: {
      name: '就业率 / 匹配度',
      min: 60,
      max: 100,
      axisLabel: { color: '#b7dfff', formatter: '{value}%' },
      nameTextStyle: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    yAxis: {
      name: '培养综合得分 / 录取分',
      min: 520,
      max: 680,
      axisLabel: { color: '#b7dfff' },
      nameTextStyle: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        type: 'scatter',
        data: rows.map((item) => ({
          value: [Number(item.employment_rate || 0), Number(item.admission_score_avg || 0)],
          symbolSize: Math.max(14, Math.min(58, Math.sqrt(Number(item.enrollment_count || 0)) * 1.25)),
          itemStyle: {
            color: getActionColor(item.major_action),
            opacity: 0.9,
            shadowBlur: 14,
            shadowColor: getActionColor(item.major_action),
          },
          raw: item,
        })),
        markArea: {
          silent: true,
          itemStyle: { opacity: 1 },
          data: quadrants.map((item) => [
            {
              name: item.name,
              itemStyle: { color: item.color },
              xAxis: item.x0,
              yAxis: item.y0,
            },
            {
              xAxis: item.x1,
              yAxis: item.y1,
            },
          ]),
          label: {
            color: 'rgba(217, 238, 255, 0.48)',
            fontSize: 12,
          },
        },
      },
    ],
  }
}

export default function MajorOptimization({
  employmentData = [],
  currentSchool = '上海大学',
  roleMode = 'school',
  loading,
  error,
}) {
  const [selectedSchool, setSelectedSchool] = useState('全部')
  const [selectedDiscipline, setSelectedDiscipline] = useState('全部')
  const [selectedAction, setSelectedAction] = useState('全部')

  const options = useMemo(() => getEmploymentFilterOptions(employmentData), [employmentData])
  const allRows = useMemo(
    () =>
      getMajorOptimizationRows(employmentData, {
        currentSchool,
        roleMode,
        selectedSchool,
      }),
    [employmentData, currentSchool, roleMode, selectedSchool]
  )

  const visibleRows = useMemo(
    () =>
      allRows.filter((item) => {
        const matchDiscipline =
          selectedDiscipline === '全部' || item?.discipline_category === selectedDiscipline
        const matchAction = selectedAction === '全部' || item?.major_action === selectedAction
        return matchDiscipline && matchAction
      }),
    [allRows, selectedAction, selectedDiscipline]
  )

  const overview = useMemo(() => getMajorOptimizationOverview(visibleRows), [visibleRows])
  const columns = [
    ...(roleMode === 'gov' ? [{ title: '学校', dataIndex: 'school_name' }] : []),
    { title: '专业', dataIndex: 'major_name' },
    { title: '学科', dataIndex: 'discipline_category' },
    {
      title: '录取分',
      dataIndex: 'admission_score_avg',
      render: (value) => formatNumber(value),
    },
    {
      title: '培养得分',
      dataIndex: 'training_quality_score',
      render: (value) => Number(value || 0).toFixed(1),
    },
    {
      title: '就业率',
      dataIndex: 'employment_rate',
      render: (value) => `${Number(value || 0).toFixed(1)}%`,
    },
    {
      title: '在校规模',
      dataIndex: 'enrollment_count',
      render: (value) => formatNumber(value),
    },
    {
      title: '建议',
      dataIndex: 'major_action',
      render: (value) => <Tag color={getMajorActionColor(value)}>{value}</Tag>,
    },
  ]

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !employmentData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card style={panelStyle}>
        <div style={sectionTitleStyle}>招生-培养-就业 综合散点决策树</div>
        <div style={{ ...noteTextStyle, marginTop: 10 }}>
          横轴看结果指标，纵轴看输入指标，气泡大小代表专业规模，颜色代表建议动作。适合在教师和政府视角下快速做专业扩招、缩招与调优判断。
        </div>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic
              title="纳入诊断专业数"
              value={overview.majorCount}
              styles={{ title: statTitleStyle, content: statValuePrimary }}
            />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic
              title="建议扩招"
              value={overview.expandCount}
              styles={{ title: statTitleStyle, content: statValueBlue }}
            />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic
              title="建议缩招"
              value={overview.shrinkCount}
              styles={{ title: statTitleStyle, content: statValueCyan }}
            />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic
              title="平均产业匹配"
              value={Number(overview.avgIndustryMatch || 0).toFixed(1)}
              styles={{ title: statTitleStyle, content: statValuePurple }}
            />
          </Card>
        </Col>
      </Row>

      <Card title={<span style={sectionTitleStyle}>筛选条件</span>} style={panelStyle}>
        <Row gutter={[12, 12]}>
          {roleMode === 'gov' ? (
            <Col xs={24} md={8}>
              <Select
                value={selectedSchool}
                onChange={setSelectedSchool}
                style={{ width: '100%' }}
                options={[
                  { label: '全部高校', value: '全部' },
                  ...(options?.schools || []).map((item) => ({ label: item, value: item })),
                ]}
              />
            </Col>
          ) : null}
          <Col xs={24} md={roleMode === 'gov' ? 8 : 12}>
            <Select
              value={selectedDiscipline}
              onChange={setSelectedDiscipline}
              style={{ width: '100%' }}
              options={[
                { label: '全部学科', value: '全部' },
                ...(options?.disciplines || []).map((item) => ({ label: item, value: item })),
              ]}
            />
          </Col>
          <Col xs={24} md={roleMode === 'gov' ? 8 : 12}>
            <Select
              value={selectedAction}
              onChange={setSelectedAction}
              style={{ width: '100%' }}
              options={[
                { label: '全部建议', value: '全部' },
                { label: '建议扩招', value: '建议扩招' },
                { label: '建议调优', value: '建议调优' },
                { label: '建议缩招', value: '建议缩招' },
                { label: '保持规模', value: '保持规模' },
              ]}
            />
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>四象限专业决策图</span>} style={panelStyle}>
        {visibleRows.length ? (
          <ReactECharts
            option={buildMajorOptimizationScatterOption(visibleRows)}
            style={{ height: '62vh', minHeight: 460 }}
          />
        ) : (
          <Empty description={<span style={noteTextStyle}>当前筛选下暂无可展示专业</span>} />
        )}
      </Card>

      <Card title={<span style={sectionTitleStyle}>专业画像明细</span>} style={panelStyle}>
        <Table
          rowKey={(record) => `${record.school_name}-${record.major_name}`}
          dataSource={visibleRows}
          columns={columns}
          pagination={{ pageSize: 8 }}
        />
      </Card>
    </Space>
  )
}

export { buildMajorOptimizationScatterOption }
