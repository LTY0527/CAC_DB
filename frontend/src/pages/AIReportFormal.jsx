import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Col, Empty, Row, Select, Space, Spin, Tag } from 'antd'
import { DownloadOutlined, PrinterOutlined, ReloadOutlined } from '@ant-design/icons'
import { buildReportSummary, formatNumber } from '../utils/dataAdapter'
import { generateReport } from '../services/dataService'
import {
  designTokens,
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  sectionTitleStyle,
} from '../utils/uiTheme'

const TOPIC_OPTIONS = {
  school: [
    { value: 'major-construction', label: '专业建设分析' },
    { value: 'training-adjustment', label: '培养调整分析' },
    { value: 'employment-status', label: '就业情况分析' },
    { value: 'comprehensive', label: '综合分析' },
  ],
  gov: [
    { value: 'major-construction', label: '专业建设分析' },
    { value: 'employment-status', label: '就业情况分析' },
    { value: 'comprehensive', label: '综合分析' },
  ],
}

const FOCUS_OPTIONS = {
  school: [
    { value: 'major-change', label: '专业建设情况' },
    { value: 'training-change', label: '培养调整情况' },
    { value: 'employment-quality', label: '就业表现情况' },
  ],
  gov: [
    { value: 'school-comparison', label: '院校对比情况' },
    { value: 'major-structure', label: '专业结构情况' },
    { value: 'employment-quality', label: '就业表现情况' },
  ],
}

const LENGTH_OPTIONS = [
  { value: 'short', label: '精简版' },
  { value: 'standard', label: '标准版' },
  { value: 'long', label: '详细版' },
]

function safeList(value) {
  return Array.isArray(value) ? value.filter(Boolean) : []
}

function firstUsefulLines(text = '', limit = 2) {
  return String(text || '')
    .split('\n')
    .map((item) => item.trim())
    .filter((item) => item && !/^[一二三四五六七八九十]+、|^\d+\./.test(item))
    .slice(0, limit)
}

function buildWarningItems(regionalWarningsData = {}, trainingProgramData = []) {
  const sourceWarnings = safeList(regionalWarningsData?.items)
  if (sourceWarnings.length) {
    return sourceWarnings.slice(0, 4).map((item, index) => ({
      key: item.key || `${index}`,
      level: item.warning_level || '中',
      title: item.warning_title || '重点指标波动',
      metric: item.metric_value || item.metric_change || '-',
      reason: item.trigger_reason || '相关指标出现波动',
      action: item.suggestion_action || '纳入后续跟踪',
    }))
  }

  return safeList(trainingProgramData).slice(0, 4).map((item, index) => ({
    key: `${item.major_name || 'major'}-${index}`,
    level: Number(item.priority_score || 0) >= 85 ? '高' : Number(item.priority_score || 0) >= 72 ? '中' : '低',
    title: `${item.major_name || '重点专业'}优化提示`,
    metric: `${Number(item.employment_rate_estimate || 0).toFixed(1)}%`,
    reason: item.evidence_summary || item.explanation || '培养与就业结果需要持续校验',
    action: item.action_type || '进入优化议程',
  }))
}

function levelColor(level = '') {
  if (level === '高') return 'red'
  if (level === '中') return 'gold'
  return 'green'
}

function getTopicLabel(optionKey, topicMode) {
  return TOPIC_OPTIONS[optionKey].find((item) => item.value === topicMode)?.label || TOPIC_OPTIONS[optionKey][0].label
}

function buildStructuredSections({ summary, filters, warnings, roleMode, topicLabel, rawReport }) {
  const employmentSummary = summary?.employmentSummary || {}
  const salaryForecast = summary?.salaryForecast || {}
  const topRules = safeList(summary?.topRules).slice(0, 3)
  const recommendationSample = safeList(summary?.recommendationSample).slice(0, 3)
  const extraLines = firstUsefulLines(rawReport, 2)

  const totalEmployment = Number(employmentSummary.totalEmpCount || 0)
  const avgSalary = Number(employmentSummary.avgSalaryWeighted || 0)
  const leadRatio = totalEmployment
    ? (Number(employmentSummary.leadEmpCount || 0) / totalEmployment) * 100
    : 0
  const trackNames = safeList(salaryForecast?.series).slice(0, 3).map((item) => item.name).filter(Boolean)

  return [
    {
      key: 'summary',
      title: '执行摘要',
      items: [
        `${filters.scopeLabel}纳入本次报告统计范围，就业样本 ${formatNumber(totalEmployment)} 条，加权平均薪资 ${formatNumber(avgSalary, 0)} 元。`,
        `本次报告主题为“${topicLabel}”，当前重点查看“${filters.focusLabel}”。`,
        ...(extraLines.length ? [extraLines[0]] : []),
      ],
    },
    {
      key: 'findings',
      title: '关键发现',
      items: [
        `高质量就业占比约 ${leadRatio.toFixed(1)}%，可作为判断专业建设成效和就业质量的重要依据。`,
        trackNames.length ? `需求预测当前主要关注 ${trackNames.join('、')} 等方向。` : '需求预测模块已形成可继续观察的趋势样本。',
        topRules.length ? `规则分析当前可引用 ${topRules.length} 条有效规则证据。` : '规则分析模块可继续补充有效规则样本。',
      ],
    },
    {
      key: 'warning',
      title: '监测预警',
      items: warnings.length
        ? warnings.map((item) => `${item.level}级：${item.title}；来源指标 ${item.metric}；原因 ${item.reason}；建议动作 ${item.action}。`)
        : ['当前未识别到高等级预警对象，建议继续按月复核重点指标。'],
    },
    {
      key: 'cause',
      title: '原因分析',
      items: roleMode === 'gov'
        ? [
            '不同学校、不同专业之间的样本规模与行业吸纳能力分布不均，是当前差异的重要来源。',
            '招生热度、培养结构与就业去向之间存在阶段性错位，导致局部指标出现明显波动。',
          ]
        : [
            '专业培养节奏、课程结构与岗位需求之间存在不同步现象，是就业表现分化的重要原因之一。',
            '样本规模、规则命中情况与行业吸纳能力在不同专业之间差异较大，放大了当前波动特征。',
          ],
    },
    {
      key: 'action',
      title: '建议动作',
      items: roleMode === 'gov'
        ? [
            '将重点预警对象纳入阶段性跟踪清单，按红黄绿等级安排复核频率。',
            '结合跨校比较结果，优先跟踪波动明显的专业门类和重点产业方向。',
            '将相关结果纳入后续治理分析和专题汇报材料。',
          ]
        : [
            '将重点预警对象纳入学院例会和专业建设讨论，形成月度跟踪清单。',
            '结合规则证据、培养优化建议和就业推荐结果，形成从问题识别到教学调整的闭环。',
            recommendationSample.length ? `优先跟踪 ${recommendationSample[0]?.recommended_job || '高匹配岗位'} 等岗位画像与实际转化表现。` : '结合报告结果补充后续教学与就业跟踪记录。',
          ],
    },
    {
      key: 'appendix',
      title: '附录指标',
      items: [
        `分析范围：${filters.scopeLabel}`,
        `报告主题：${topicLabel}`,
        `输出重点：${filters.focusLabel}`,
        `预测样本轨道数：${formatNumber(safeList(salaryForecast?.trackOptions).length)}`,
      ],
    },
  ]
}

function exportReportText(sections, meta) {
  const lines = [
    '分析报告',
    `生成时间：${meta.generatedAt || '-'}`,
    `报告主题：${meta.topicLabel || '-'}`,
    `输出重点：${meta.focusLabel || '-'}`,
    '',
    ...sections.flatMap((section, index) => [
      `${index + 1}. ${section.title}`,
      ...section.items.map((item) => `- ${item}`),
      '',
    ]),
  ]

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'analysis-report.txt'
  link.click()
  URL.revokeObjectURL(link.href)
}

export default function AIReportFormal({
  employmentData = [],
  forecastData = [],
  enrollmentData = [],
  rulesData = [],
  recommendationData = [],
  trainingProgramData = [],
  regionalWarningsData = {},
  currentSchool = '',
  roleMode = 'school',
  dataLoadedAt = '',
  loading,
  error,
}) {
  const optionKey = roleMode === 'gov' ? 'gov' : 'school'
  const topicOptions = TOPIC_OPTIONS[optionKey]
  const focusOptions = FOCUS_OPTIONS[optionKey]

  const [reportLoading, setReportLoading] = useState(false)
  const [topicMode, setTopicMode] = useState(topicOptions[0].value)
  const [focusMode, setFocusMode] = useState(focusOptions[0].value)
  const [reportLength, setReportLength] = useState('standard')
  const [reportState, setReportState] = useState({
    fallback: false,
    generatedAt: '',
    sections: [],
  })

  useEffect(() => {
    setTopicMode(topicOptions[0].value)
    setFocusMode(focusOptions[0].value)
  }, [optionKey])

  const summary = useMemo(
    () =>
      buildReportSummary({
        employmentData,
        forecastData,
        rulesData,
        enrollmentData,
        recommendationData,
      }),
    [employmentData, forecastData, rulesData, enrollmentData, recommendationData]
  )

  const warnings = useMemo(
    () => buildWarningItems(regionalWarningsData, trainingProgramData),
    [regionalWarningsData, trainingProgramData]
  )

  const scopeLabel = useMemo(() => {
    if (roleMode === 'gov') return '上海市重点监测范围'
    if (currentSchool) return `${currentSchool}重点监测范围`
    return '当前数据范围'
  }, [currentSchool, roleMode])

  const topicLabel = getTopicLabel(optionKey, topicMode)
  const selectedFocusLabel = focusOptions.find((item) => item.value === focusMode)?.label || focusOptions[0].label

  const evidenceRows = useMemo(() => {
    const employmentSummary = summary?.employmentSummary || {}
    return [
      { label: '就业样本', value: `${formatNumber(employmentSummary.totalEmpCount || 0)} 条` },
      { label: '平均薪资', value: `${formatNumber(employmentSummary.avgSalaryWeighted || 0, 0)} 元` },
      { label: '规则证据', value: `${formatNumber(safeList(summary?.topRules).length)} 条` },
      { label: '推荐样本', value: `${formatNumber(safeList(summary?.recommendationSample).length)} 条` },
      { label: '预警条数', value: `${formatNumber(warnings.length)} 条` },
      { label: '数据载入', value: dataLoadedAt || '当前会话' },
    ]
  }, [dataLoadedAt, summary, warnings.length])

  const hasSummaryData =
    (Array.isArray(employmentData) && employmentData.length > 0) ||
    (Array.isArray(forecastData) && forecastData.length > 0) ||
    (Array.isArray(enrollmentData) && enrollmentData.length > 0) ||
    (Array.isArray(rulesData) && rulesData.length > 0) ||
    (Array.isArray(recommendationData) && recommendationData.length > 0)

  const handleGenerate = async () => {
    setReportLoading(true)
    try {
      const prompt = `请根据${scopeLabel}生成正式分析报告，报告主题为${topicLabel}，输出重点为${selectedFocusLabel}，语言自然、专业，适合老师查看和汇报使用。`
      const payload = {
        prompt,
        currentPage: 'report',
        reportType: 'management',
        reportLength,
        modules: ['employment', 'forecast', 'enrollment', 'rules', 'recommendation'],
        summary,
        chartData: {
          salaryForecast: summary?.salaryForecast || {},
          topRules: summary?.topRules || [],
          enrollmentSample: summary?.enrollmentSample || [],
          recommendationSample: summary?.recommendationSample || [],
        },
        filters: {
          region: '上海',
          school: currentSchool || '当前范围',
          topicMode,
          focusMode,
        },
      }

      const res = await generateReport(payload)
      const rawReport = res?.data?.report || ''
      const generatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
      const sections = buildStructuredSections({
        summary,
        filters: { scopeLabel, focusLabel: selectedFocusLabel },
        warnings,
        roleMode,
        topicLabel,
        rawReport,
      })

      setReportState({
        fallback: Boolean(res?.data?.fallback),
        generatedAt,
        sections,
      })
    } catch {
      const generatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
      setReportState({
        fallback: true,
        generatedAt,
        sections: buildStructuredSections({
          summary,
          filters: { scopeLabel, focusLabel: selectedFocusLabel },
          warnings,
          roleMode,
          topicLabel,
          rawReport: '',
        }),
      })
    } finally {
      setReportLoading(false)
    }
  }

  if (loading) {
    return <div style={{ color: designTokens.textSecondary }}>平台数据加载中...</div>
  }

  const headerExtra = (
    <Space size="small">
      <Button icon={<ReloadOutlined />} style={secondaryButtonStyle} onClick={handleGenerate} disabled={!hasSummaryData || reportLoading}>
        刷新内容
      </Button>
      <Button icon={<PrinterOutlined />} style={secondaryButtonStyle} onClick={() => window.print()} disabled={!reportState.sections.length}>
        打印视图
      </Button>
      <Button
        icon={<DownloadOutlined />}
        style={secondaryButtonStyle}
        onClick={() => exportReportText(reportState.sections, { generatedAt: reportState.generatedAt, topicLabel, focusLabel: selectedFocusLabel })}
        disabled={!reportState.sections.length}
      >
        导出文本
      </Button>
    </Space>
  )

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card style={panelStyle}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} xl={16}>
            <div style={sectionTitleStyle}>AI 专报</div>
            <div style={{ marginTop: 8, color: designTokens.textSecondary, lineHeight: 1.8 }}>
              根据当前数据生成分析报告，便于查看专业情况、培养调整和就业表现。
            </div>
          </Col>
          <Col xs={24} xl={8}>
            <div style={metaLabelStyle}>数据载入时间</div>
            <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]} align="stretch">
        <Col xs={24} xl={6}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card title={<span style={sectionTitleStyle}>报告参数</span>} style={panelStyle}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <div style={{ color: designTokens.textMuted, fontSize: 13, marginBottom: -4 }}>报告主题</div>
                <Select value={topicMode} onChange={setTopicMode} options={topicOptions} style={{ width: '100%' }} />
                <div style={{ color: designTokens.textMuted, fontSize: 13, marginBottom: -4 }}>输出重点</div>
                <Select value={focusMode} onChange={setFocusMode} options={focusOptions} style={{ width: '100%' }} />
                <div style={{ color: designTokens.textMuted, fontSize: 13, marginBottom: -4 }}>报告篇幅</div>
                <Select value={reportLength} onChange={setReportLength} options={LENGTH_OPTIONS} style={{ width: '100%' }} />
                <Button
                  type="primary"
                  onClick={handleGenerate}
                  loading={reportLoading}
                  style={{ ...primaryButtonStyle, width: '100%' }}
                  disabled={!hasSummaryData}
                >
                  生成分析报告
                </Button>
              </Space>
              {!hasSummaryData ? (
                <div style={{ marginTop: 12, color: designTokens.textMuted, fontSize: 13, lineHeight: 1.8 }}>
                  当前可用数据不足，暂无法生成报告内容。
                </div>
              ) : null}
            </Card>

            <Card title={<span style={sectionTitleStyle}>适用范围</span>} style={panelStyle}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: designTokens.textMuted }}>分析范围</span>
                  <span style={{ color: designTokens.textPrimary, fontWeight: 600 }}>{scopeLabel}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: designTokens.textMuted }}>报告主题</span>
                  <span style={{ color: designTokens.textPrimary, fontWeight: 600 }}>{topicLabel}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: designTokens.textMuted }}>输出重点</span>
                  <span style={{ color: designTokens.textPrimary, fontWeight: 600 }}>{selectedFocusLabel}</span>
                </div>
              </Space>
            </Card>
          </Space>
        </Col>

        <Col xs={24} xl={12}>
          <Card title={<span style={sectionTitleStyle}>报告正文</span>} extra={headerExtra} style={{ ...panelStyle, minHeight: 760 }}>
            {reportLoading ? (
              <div style={{ minHeight: 520, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Spin size="large" />
              </div>
            ) : reportState.sections.length ? (
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                  <Tag color="processing">{topicLabel}</Tag>
                  <Tag color="blue">{selectedFocusLabel}</Tag>
                  <Tag color={reportState.fallback ? 'gold' : 'green'}>{reportState.fallback ? '模板回退' : '已生成'}</Tag>
                </div>

                {reportState.sections.map((section, index) => (
                  <div
                    key={section.key}
                    style={{
                      paddingBottom: index === reportState.sections.length - 1 ? 0 : 16,
                      borderBottom: index === reportState.sections.length - 1 ? 'none' : `1px solid ${designTokens.border}`,
                    }}
                  >
                    <div style={{ color: designTokens.textPrimary, fontSize: 16, fontWeight: 700, marginBottom: 12 }}>
                      {index + 1}. {section.title}
                    </div>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                      {section.items.map((item, itemIndex) => (
                        <div key={`${section.key}-${itemIndex}`} style={{ color: designTokens.textSecondary, lineHeight: 1.9 }}>
                          {item}
                        </div>
                      ))}
                    </Space>
                  </div>
                ))}
              </Space>
            ) : hasSummaryData ? (
              <Empty description="请选择报告主题后生成内容" />
            ) : (
              <Empty description={error ? '当前可用数据不足，分析报告暂不可生成。' : '当前尚未生成报告内容'} />
            )}
          </Card>
        </Col>

        <Col xs={24} xl={6}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card title={<span style={sectionTitleStyle}>证据指标</span>} style={panelStyle}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {evidenceRows.map((row) => (
                  <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                    <span style={{ color: designTokens.textMuted }}>{row.label}</span>
                    <span style={{ color: designTokens.textPrimary, fontWeight: 600, textAlign: 'right' }}>{row.value}</span>
                  </div>
                ))}
              </Space>
            </Card>

            <Card title={<span style={sectionTitleStyle}>预警引用</span>} style={panelStyle}>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {warnings.length ? warnings.map((item) => (
                  <div key={item.key} style={{ paddingBottom: 10, borderBottom: `1px solid ${designTokens.border}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
                      <div style={{ color: designTokens.textPrimary, fontWeight: 600 }}>{item.title}</div>
                      <Tag color={levelColor(item.level)}>{item.level}</Tag>
                    </div>
                    <div style={{ color: designTokens.textSecondary, fontSize: 13, lineHeight: 1.8 }}>来源指标：{item.metric}</div>
                    <div style={{ color: designTokens.textSecondary, fontSize: 13, lineHeight: 1.8 }}>建议动作：{item.action}</div>
                  </div>
                )) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无预警引用" />}
              </Space>
            </Card>

            <Card title={<span style={sectionTitleStyle}>生成信息</span>} style={panelStyle}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: designTokens.textMuted }}>生成时间</span>
                  <span style={{ color: designTokens.textPrimary, fontWeight: 600 }}>{reportState.generatedAt || '未生成'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <span style={{ color: designTokens.textMuted }}>输出状态</span>
                  <span style={{ color: designTokens.textPrimary, fontWeight: 600 }}>
                    {reportState.sections.length ? (reportState.fallback ? '模板回退' : '正常完成') : '待生成'}
                  </span>
                </div>
              </Space>
            </Card>
          </Space>
        </Col>
      </Row>
    </Space>
  )
}
