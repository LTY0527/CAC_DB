import { Card, Col, Empty, Row, Segmented, Select, Space, Statistic, Table, Tag } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getMajorActionColor,
  getMajorStructureAdviceFilterOptions,
  getMajorStructureAdviceOverview,
  getMajorStructureAdviceRows,
  getStructureSuggestionColor,
  getSuggestionLevelColor,
  getTrainingProgramFilterOptions,
  getTrainingProgramOverview,
  getTrainingProgramRows,
  normalizeMajorStructureAdviceData,
} from '../utils/dataAdapter'
import {
  axisLabelStyle,
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

function getActionHex(action = '') {
  const text = String(action || '')
  if (text === 'expand' || text.includes('扩招')) return '#37c66d'
  if (text === 'stable' || text.includes('稳招')) return '#58a6ff'
  if (text === 'shrink' || text.includes('缩招')) return '#ff6b6b'
  if (text === 'practice' || text.includes('实践')) return '#f7c948'
  if (text === 'support' || text.includes('扶持')) return '#9b7bff'
  if (text === '重点调优') return '#ff6b6b'
  if (text === '补强就业导向') return '#f7c948'
  if (text === '强化优势方向') return '#37c66d'
  return '#58a6ff'
}

function firstFinite(...values) {
  for (const value of values) {
    const num = Number(value)
    if (Number.isFinite(num)) return num
  }
  return 0
}

function percentLike(value) {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  return num <= 1 ? num * 100 : num
}

function getOptimizationPriority(item = {}) {
  const direct = firstFinite(item.priority_score)
  if (direct > 0) return direct
  const policyHeat = percentLike(item.policy_heat)
  const demandGrowth = percentLike(item.demand_growth_rate)
  const skillGap = percentLike(item.skill_gap_score)
  const matchScore = percentLike(item.avg_match_score ?? item.match_score)
  const evidenceScore = firstFinite(item.evidence_score, item.top_rule_lift) * 20
  return policyHeat * 0.3 + demandGrowth * 0.25 + skillGap * 0.2 + matchScore * 0.15 + evidenceScore * 0.1
}

function getSuggestionScatterRows(rows = []) {
  return (Array.isArray(rows) ? rows : [])
    .map((item) => {
      const priority = getOptimizationPriority(item)
      const avgSalary = firstFinite(item.avg_salary, item.salary)
      const sampleSize = firstFinite(item.sample_count, item.evidence_count, item.rule_sample_count, item.priority_score, 30)
      const actionType = item.primary_suggestion_type || item.suggestion_type || item.action_type || item.gap_level || ''
      return {
        ...item,
        priority_score: priority,
        avg_salary: avgSalary,
        sample_size: sampleSize,
        action_type: actionType,
      }
    })
    .filter((item) => item.major_name && Number.isFinite(item.priority_score) && Number.isFinite(item.avg_salary))
    .sort((a, b) => b.priority_score - a.priority_score)
    .slice(0, 80)
}

function buildSuggestionScatterOption(rows = []) {
  const chartRows = getSuggestionScatterRows(rows)
  const priorities = chartRows.map((item) => item.priority_score)
  const salaries = chartRows.map((item) => item.avg_salary).filter((value) => value > 0)
  const minPriority = priorities.length ? Math.max(0, Math.floor((Math.min(...priorities) - 5) / 5) * 5) : 0
  const maxPriority = priorities.length ? Math.ceil((Math.max(...priorities) + 8) / 5) * 5 : 100
  const minSalary = salaries.length ? Math.max(0, Math.floor((Math.min(...salaries) - 1500) / 1000) * 1000) : 0
  const maxSalary = salaries.length ? Math.ceil((Math.max(...salaries) + 1500) / 1000) * 1000 : undefined

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
          `平均薪资：${formatNumber(item.avg_salary || 0, 0)} 元`,
          `样本量：${Number(item.sample_size || 0).toFixed(0)}`,
          `建议动作：${item.action_type || '-'}`,
          `技能缺口：${Number(item.skill_gap_score || 0).toFixed(2)}`,
          `政策热度：${Number(item.policy_heat || 0).toFixed(1)}`,
          item.explanation || item.suggestion_reason ? `建议原因：${item.explanation || item.suggestion_reason}` : '',
        ].join('<br/>')
      },
    },
    grid: { left: '7%', right: '6%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: {
      name: '培养优化优先级',
      min: minPriority,
      max: maxPriority,
      axisLabel: axisLabelStyle,
      nameTextStyle: { color: designTokens.textMuted },
      splitLine: splitLineStyle,
    },
    yAxis: {
      name: '平均薪资',
      min: minSalary,
      max: maxSalary,
      axisLabel: axisLabelStyle,
      nameTextStyle: { color: designTokens.textMuted },
      splitLine: splitLineStyle,
    },
    series: [
      {
        type: 'scatter',
        data: chartRows.map((item) => ({
          value: [item.priority_score, item.avg_salary, item.sample_size],
          symbolSize: Math.max(16, Math.min(58, Math.sqrt(Math.max(item.sample_size, 1)) * 4 + item.priority_score / 8)),
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
  majorStructureAdviceData = {},
  currentSchool = '上海大学',
  roleMode = 'school',
  dataLoadedAt = '',
  loading,
  error,
}) {
  const [selectedSchool, setSelectedSchool] = useState('全部')
  const [selectedDiscipline, setSelectedDiscipline] = useState('全部')
  const [selectedAction, setSelectedAction] = useState('全部')
  const [selectedSuggestionType, setSelectedSuggestionType] = useState('全部')

  const options = useMemo(() => getTrainingProgramFilterOptions(trainingProgramData), [trainingProgramData])
  const structureOptions = useMemo(
    () => getMajorStructureAdviceFilterOptions(majorStructureAdviceData),
    [majorStructureAdviceData]
  )
  const normalizedAdvice = useMemo(
    () => normalizeMajorStructureAdviceData(majorStructureAdviceData),
    [majorStructureAdviceData]
  )

  const allRows = useMemo(
    () => getTrainingProgramRows(trainingProgramData, { currentSchool, roleMode, selectedSchool }),
    [trainingProgramData, currentSchool, roleMode, selectedSchool]
  )
  const visibleRows = useMemo(
    () =>
      allRows.filter(
        (item) =>
          (selectedDiscipline === '全部' || item.discipline_category === selectedDiscipline) &&
          (selectedAction === '全部' || item.action_type === selectedAction)
      ),
    [allRows, selectedAction, selectedDiscipline]
  )
  const overview = useMemo(() => getTrainingProgramOverview(visibleRows), [visibleRows])
  const topSuggestions = visibleRows.slice(0, 3)
  const scatterRows = useMemo(() => getSuggestionScatterRows(visibleRows), [visibleRows])

  const structureRows = useMemo(
    () =>
      getMajorStructureAdviceRows(majorStructureAdviceData, {
        currentSchool,
        roleMode,
        selectedSchool,
        selectedType: selectedSuggestionType,
      }),
    [majorStructureAdviceData, currentSchool, roleMode, selectedSchool, selectedSuggestionType]
  )
  const structureOverview = useMemo(
    () => getMajorStructureAdviceOverview(structureRows, normalizedAdvice.summary),
    [structureRows, normalizedAdvice.summary]
  )
  const topStructureRows = structureRows.slice(0, 6)

  if (loading) return <div>数据加载中...</div>
  if (error && !trainingProgramData.length && !normalizedAdvice.items.length) {
    return <div style={{ color: '#ff4d4f' }}>{error}</div>
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card style={panelStyle}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} xl={16}>
            <div style={sectionTitleStyle}>培养方案优化</div>
          </Col>
          <Col xs={24} xl={8}>
            <div style={metaLabelStyle}>数据载入时间</div>
            <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>专业结构调整建议</span>} style={panelStyle}>
        <Space direction="vertical" size={18} style={{ width: '100%' }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12} xl={4}>
              <Card style={panelStyle}>
                <Statistic title="建议总数" value={structureOverview.total} styles={{ title: statTitleStyle, content: statValuePrimary }} />
              </Card>
            </Col>
            <Col xs={24} md={12} xl={4}>
              <Card style={panelStyle}>
                <Statistic title="扩招建议" value={structureOverview.expandCount} styles={{ title: statTitleStyle, content: statValueBlue }} />
              </Card>
            </Col>
            <Col xs={24} md={12} xl={4}>
              <Card style={panelStyle}>
                <Statistic title="稳招建议" value={structureOverview.maintainCount} styles={{ title: statTitleStyle, content: statValueCyan }} />
              </Card>
            </Col>
            <Col xs={24} md={12} xl={4}>
              <Card style={panelStyle}>
                <Statistic title="缩招建议" value={structureOverview.shrinkCount} styles={{ title: statTitleStyle, content: statValuePurple }} />
              </Card>
            </Col>
            <Col xs={24} md={12} xl={4}>
              <Card style={panelStyle}>
                <Statistic title="实践强化" value={structureOverview.practiceCount} styles={{ title: statTitleStyle, content: statValueBlue }} />
              </Card>
            </Col>
            <Col xs={24} md={12} xl={4}>
              <Card style={panelStyle}>
                <Statistic title="重点扶持方向" value={structureOverview.supportCount} styles={{ title: statTitleStyle, content: statValueCyan }} />
              </Card>
            </Col>
          </Row>

          <Row gutter={[12, 12]} align="middle">
            {roleMode === 'gov' ? (
              <Col xs={24} md={8}>
                <Select
                  value={selectedSchool}
                  onChange={setSelectedSchool}
                  style={{ width: '100%' }}
                  options={[
                    { label: '全部高校', value: '全部' },
                    ...(structureOptions.schools || []).map((item) => ({ label: item, value: item })),
                  ]}
                />
              </Col>
            ) : null}
            <Col xs={24} md={roleMode === 'gov' ? 16 : 24}>
              <Segmented
                block
                value={selectedSuggestionType}
                onChange={setSelectedSuggestionType}
                options={[
                  '全部',
                  '建议扩招',
                  '建议稳招',
                  '建议缩招',
                  '建议加强实践培养',
                  '建议重点扶持方向',
                ]}
              />
            </Col>
          </Row>

          {topStructureRows.length ? (
            <Row gutter={[16, 16]}>
              {topStructureRows.map((item) => (
                <Col xs={24} xl={8} key={item.key}>
                  <Card style={{ ...panelStyle, minHeight: 280, border: `1px solid ${designTokens.border}` }}>
                    <Space size={[8, 8]} wrap>
                      <Tag color={getStructureSuggestionColor(item.suggestion_type)}>{item.suggestion_type}</Tag>
                      <Tag color={getSuggestionLevelColor(item.suggestion_level)}>{item.suggestion_level}优先</Tag>
                      {item.scope_type === 'industry_direction' ? <Tag color="purple">行业方向</Tag> : <Tag>专业</Tag>}
                    </Space>
                    <div style={{ color: designTokens.textPrimary, fontSize: 18, fontWeight: 700, marginTop: 12 }}>
                      {item.scope_type === 'industry_direction' ? item.industry_name : item.major_name}
                    </div>
                    <div style={{ color: designTokens.textMuted, marginTop: 8 }}>
                      {item.school_name}
                      {item.discipline_category ? ` / ${item.discipline_category}` : ''}
                    </div>
                    <div style={{ color: designTokens.textSecondary, marginTop: 14, lineHeight: 1.8 }}>
                      {item.trigger_reason}
                    </div>
                    <div style={{ color: designTokens.textPrimary, fontWeight: 600, marginTop: 14 }}>
                      {item.metric_summary}
                    </div>
                    <div style={{ color: designTokens.textSecondary, marginTop: 12, lineHeight: 1.8 }}>
                      {item.explanation}
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Empty description="当前筛选下暂无结构调整建议" />
          )}

          <Table
            rowKey="key"
            dataSource={structureRows}
            pagination={{ pageSize: 8 }}
            scroll={{ x: 1600 }}
            columns={[
              ...(roleMode === 'gov' ? [{ title: '学校', dataIndex: 'school_name', width: 150, fixed: 'left' }] : []),
              {
                title: '建议类型',
                dataIndex: 'suggestion_type',
                width: 140,
                render: (value) => <Tag color={getStructureSuggestionColor(value)}>{value}</Tag>,
              },
              {
                title: '对象',
                width: 180,
                render: (_, record) => (record.scope_type === 'industry_direction' ? record.industry_name : record.major_name),
              },
              { title: '优先级', dataIndex: 'suggestion_level', width: 100, render: (value) => <Tag color={getSuggestionLevelColor(value)}>{value}</Tag> },
              { title: '主要依据', dataIndex: 'trigger_reason', width: 220 },
              { title: '核心指标', dataIndex: 'metric_summary', width: 320 },
              {
                title: '支撑信号',
                dataIndex: 'supporting_signals',
                width: 320,
                render: (value) => renderTagList(value, 'blue'),
              },
              { title: '简短解释', dataIndex: 'explanation', width: 360 },
            ]}
          />
        </Space>
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
            <Statistic title="平均薪资" value={overview.avgSalary} suffix="元" styles={{ title: statTitleStyle, content: statValuePurple }} />
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
                { label: '全部培养建议', value: '全部' },
                ...(options.actions || []).map((item) => ({ label: item, value: item })),
              ]}
            />
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>培养优化优先级分布</span>} style={panelStyle}>
        {scatterRows.length ? (
          <ReactECharts option={buildSuggestionScatterOption(scatterRows)} style={{ height: '58vh', minHeight: 420 }} />
        ) : (
          <Empty description="当前筛选下暂无培养方案建议" />
        )}
      </Card>

      <Card title={<span style={sectionTitleStyle}>建议样例预览</span>} style={panelStyle}>
        {topSuggestions.length ? (
          <Row gutter={[16, 16]}>
            {topSuggestions.map((item) => (
              <Col xs={24} xl={8} key={item.key}>
                <Card style={{ ...panelStyle, minHeight: 300, border: `1px solid ${getActionHex(item.action_type)}33` }}>
                  <div style={{ color: designTokens.textPrimary, fontSize: 18, fontWeight: 700 }}>{item.major_name}</div>
                  <div style={{ color: designTokens.textMuted, marginTop: 8 }}>
                    {item.school_name} / {item.discipline_category}
                  </div>
                  <div style={{ marginTop: 10 }}>
                    <Tag color={getMajorActionColor(item.action_type)}>{item.action_type}</Tag>
                    <Tag color="cyan">优先级 {Number(item.priority_score || 0).toFixed(1)}</Tag>
                  </div>
                  <div style={{ color: designTokens.textSecondary, marginTop: 14, lineHeight: 1.8 }}>{item.explanation}</div>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <Empty description="暂无培养优化样例" />
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
            {
              title: '估算就业率',
              dataIndex: 'employment_rate_estimate',
              width: 110,
              render: (value) => `${Number(value || 0).toFixed(1)}%`,
            },
            { title: '平均薪资', dataIndex: 'avg_salary', width: 120, render: (value) => `${formatNumber(value || 0, 0)} 元` },
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
