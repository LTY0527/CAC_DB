import { Card, Col, Empty, Row, Select, Space, Statistic, Table, Tag } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getMajorActionColor,
  getTrainingProgramFilterOptions,
  getTrainingProgramOverview,
  getTrainingProgramRows,
} from '../utils/dataAdapter'
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

function getActionHex(action = '') {
  if (action === '重点调优') return '#ff6b6b'
  if (action === '补强就业导向') return '#f7c948'
  if (action === '强化优势方向') return '#37c66d'
  return '#58a6ff'
}

function buildSuggestionScatterOption(rows = []) {
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
          `学科：${item.discipline_category || '-'}`,
          `优先级：${Number(item.priority_score || 0).toFixed(1)}`,
          `估算就业率：${Number(item.employment_rate_estimate || 0).toFixed(1)}%`,
          `平均薪资：¥${formatNumber(item.avg_salary || 0, 0)}`,
          `规则强度：S ${Number(item.top_rule_support || 0).toFixed(2)} / C ${Number(item.top_rule_confidence || 0).toFixed(2)} / L ${Number(item.top_rule_lift || 0).toFixed(2)}`,
          `主导行业：${item.dominant_industry || '-'}`,
          `建议动作：${item.action_type || '-'}`,
        ].join('<br/>')
      },
    },
    grid: { left: '7%', right: '6%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: {
      name: '估算就业率',
      min: 70,
      max: 100,
      axisLabel: { color: '#b7dfff', formatter: '{value}%' },
      nameTextStyle: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    yAxis: {
      name: '平均薪资',
      axisLabel: { color: '#b7dfff' },
      nameTextStyle: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        type: 'scatter',
        data: rows.map((item) => ({
          value: [Number(item.employment_rate_estimate || 0), Number(item.avg_salary || 0)],
          symbolSize: Math.max(16, Math.min(54, Number(item.priority_score || 0) / 2)),
          itemStyle: {
            color: getActionHex(item.action_type),
            opacity: 0.92,
            shadowBlur: 12,
            shadowColor: getActionHex(item.action_type),
          },
          raw: item,
        })),
      },
    ],
  }
}

function renderTagList(items = [], color = 'blue') {
  return (
    <Space size={[6, 6]} wrap>
      {(items || []).map((item) => (
        <Tag color={color} key={item}>
          {item}
        </Tag>
      ))}
    </Space>
  )
}

export default function MajorOptimization({
  trainingProgramData = [],
  currentSchool = '上海大学',
  roleMode = 'school',
  dataLoadedAt = '',
  loading,
  error,
}) {
  const [selectedSchool, setSelectedSchool] = useState('全部')
  const [selectedDiscipline, setSelectedDiscipline] = useState('全部')
  const [selectedAction, setSelectedAction] = useState('全部')

  const options = useMemo(() => getTrainingProgramFilterOptions(trainingProgramData), [trainingProgramData])
  const allRows = useMemo(
    () =>
      getTrainingProgramRows(trainingProgramData, {
        currentSchool,
        roleMode,
        selectedSchool,
      }),
    [trainingProgramData, currentSchool, roleMode, selectedSchool]
  )

  const visibleRows = useMemo(
    () =>
      allRows.filter((item) => {
        const matchDiscipline = selectedDiscipline === '全部' || item.discipline_category === selectedDiscipline
        const matchAction = selectedAction === '全部' || item.action_type === selectedAction
        return matchDiscipline && matchAction
      }),
    [allRows, selectedAction, selectedDiscipline]
  )

  const overview = useMemo(() => getTrainingProgramOverview(visibleRows), [visibleRows])
  const topSuggestions = visibleRows.slice(0, 3)

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !trainingProgramData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} xl={14}>
            <div style={sectionTitleStyle}>培养方案优化</div>
            <div style={{ ...noteTextStyle, marginTop: 10 }}>
              业务价值：把规则结果转成课程模块、技能培养、实践教学和课程结构调整建议，支撑专业建设从“看见问题”走向“给出动作”。
            </div>
          </Col>
          <Col xs={24} xl={10}>
            <Row gutter={[12, 12]}>
              <Col span={12}>
                <div style={metaLabelStyle}>数据载入时间</div>
                <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
              </Col>
              <Col span={12}>
                <div style={metaLabelStyle}>建议口径</div>
                <div style={metaValueStyle}>规则强度 + 就业表现 + 薪资表现</div>
              </Col>
              <Col span={24}>
                <div style={algorithmTextStyle}>算法说明：基于关联规则强度、估算就业率、平均薪资、行业与技能特征生成可解释培养建议。</div>
              </Col>
              <Col span={24}>
                <div style={riskTextStyle}>风险提示：当前建议适合做专业层面的结构优化，不应直接替代课程委员会或专家评审决策。</div>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic title="纳入建议专业数" value={overview.majorCount} styles={{ title: statTitleStyle, content: statValuePrimary }} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic title="重点调优专业" value={overview.focusCount} styles={{ title: statTitleStyle, content: statValueBlue }} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic title="平均优先级" value={overview.avgPriorityScore} styles={{ title: statTitleStyle, content: statValueCyan }} />
          </Card>
        </Col>
        <Col xs={24} md={12} xl={6}>
          <Card style={panelStyle}>
            <Statistic title="平均薪资" value={overview.avgSalary} prefix="¥" styles={{ title: statTitleStyle, content: statValuePurple }} />
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
                  ...(options.schools || []).map((item) => ({ label: item, value: item })),
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
                ...(options.disciplines || []).map((item) => ({ label: item, value: item })),
              ]}
            />
          </Col>
          <Col xs={24} md={roleMode === 'gov' ? 8 : 12}>
            <Select
              value={selectedAction}
              onChange={setSelectedAction}
              style={{ width: '100%' }}
              options={[
                { label: '全部建议动作', value: '全部' },
                ...(options.actions || []).map((item) => ({ label: item, value: item })),
              ]}
            />
          </Col>
        </Row>
      </Card>

      <Card
        title={<span style={sectionTitleStyle}>优化优先级分布</span>}
        extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>横轴看就业率，纵轴看薪资，气泡大小看优先级。</span>}
        style={panelStyle}
      >
        {visibleRows.length ? (
          <ReactECharts option={buildSuggestionScatterOption(visibleRows)} style={{ height: '58vh', minHeight: 420 }} />
        ) : (
          <Empty description={<span style={noteTextStyle}>当前筛选下暂无培养方案建议</span>} />
        )}
      </Card>

      <Card title={<span style={sectionTitleStyle}>建议样例预览</span>} style={panelStyle}>
        {topSuggestions.length ? (
          <Row gutter={[16, 16]}>
            {topSuggestions.map((item) => (
              <Col xs={24} xl={8} key={item.key}>
                <Card style={{ ...panelStyle, minHeight: 300, border: `1px solid ${getActionHex(item.action_type)}33` }}>
                  <div style={{ color: '#eef4ff', fontSize: 18, fontWeight: 700 }}>{item.major_name}</div>
                  <div style={{ color: '#8fb7d8', marginTop: 8 }}>{item.school_name} / {item.discipline_category}</div>
                  <div style={{ marginTop: 10 }}>
                    <Tag color={getMajorActionColor(item.action_type)}>{item.action_type}</Tag>
                    <Tag color="cyan">优先级 {Number(item.priority_score || 0).toFixed(1)}</Tag>
                  </div>
                  <div style={{ ...noteTextStyle, marginTop: 14 }}>{item.explanation}</div>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Empty description={<span style={noteTextStyle}>暂无建议样例</span>} />
        )}
      </Card>

      <Card title={<span style={sectionTitleStyle}>培养方案建议明细</span>} style={panelStyle}>
        <Table
          rowKey="key"
          dataSource={visibleRows}
          pagination={{ pageSize: 8 }}
          scroll={{ x: 1800 }}
          columns={[
            ...(roleMode === 'gov' ? [{ title: '学校', dataIndex: 'school_name', width: 150, fixed: 'left' }] : []),
            { title: '专业', dataIndex: 'major_name', width: 140, fixed: 'left' },
            { title: '学科', dataIndex: 'discipline_category', width: 110 },
            {
              title: '建议动作',
              dataIndex: 'action_type',
              width: 120,
              render: (value) => <Tag color={getMajorActionColor(value)}>{value}</Tag>,
            },
            { title: '优先级', dataIndex: 'priority_score', width: 100, render: (value) => Number(value || 0).toFixed(1) },
            { title: '估算就业率', dataIndex: 'employment_rate_estimate', width: 110, render: (value) => `${Number(value || 0).toFixed(1)}%` },
            { title: '平均薪资', dataIndex: 'avg_salary', width: 120, render: (value) => `¥${formatNumber(value || 0, 0)}` },
            {
              title: '规则强度',
              width: 180,
              render: (_, record) =>
                `S ${Number(record.top_rule_support || 0).toFixed(2)} / C ${Number(record.top_rule_confidence || 0).toFixed(2)} / L ${Number(record.top_rule_lift || 0).toFixed(2)}`,
            },
            { title: '推荐课程模块', dataIndex: 'recommended_courses', width: 260, render: (value) => renderTagList(value, 'blue') },
            { title: '推荐技能培养', dataIndex: 'recommended_skills', width: 260, render: (value) => renderTagList(value, 'cyan') },
            { title: '推荐实践教学', dataIndex: 'recommended_practice', width: 260, render: (value) => renderTagList(value, 'purple') },
            { title: '课程结构优化', dataIndex: 'recommended_structure', width: 360 },
            { title: '证据摘要', dataIndex: 'evidence_summary', width: 320 },
          ]}
        />
      </Card>
    </Space>
  )
}
