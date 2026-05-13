import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Col, Empty, Input, Row, Space, Statistic, Table, message } from 'antd'
import {
  formatNumber,
  getMetricRows,
  getRecommendationStats,
} from '../utils/dataAdapter'
import {
  designTokens,
  inputStyle,
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'
import { fetchRecommendationStudent, fetchRecommendationSummary } from '../services/dataService'

const miniCardStyle = {
  ...panelStyle,
  minHeight: 138,
  borderRadius: 14,
}

function toNumber(value, fallback = 0) {
  const nextValue = Number(value)
  return Number.isFinite(nextValue) ? nextValue : fallback
}

export default function JobRecommendation({
  recommendationData = [],
  jobRecommendationEvalData = [],
  employmentData = [],
  currentSchool = '',
  roleMode = 'school',
  dataLoadedAt = '',
  loading,
  error,
}) {
  const [studentId, setStudentId] = useState('')
  const [result, setResult] = useState([])
  const [summary, setSummary] = useState({})
  const [queryMessage, setQueryMessage] = useState('')
  const [searched, setSearched] = useState(false)

  const stats = useMemo(() => getRecommendationStats(recommendationData), [recommendationData])
  const evalMetrics = useMemo(() => getMetricRows(jobRecommendationEvalData), [jobRecommendationEvalData])
  const evalMap = Object.fromEntries(evalMetrics.map((item) => [item.metric_name, item]))
  const availableExamples = summary.available_examples || []
  const displayCoveredStudents = toNumber(summary.covered_students)
  const rawSchoolStudentTotal = toNumber(summary.school_student_total)
  const hasTotalAnomaly = rawSchoolStudentTotal < displayCoveredStudents
  const displaySchoolStudentTotal = Math.max(rawSchoolStudentTotal, displayCoveredStudents)
  const displayCoverageRate = toNumber(summary.coverage_rate)
  const displaySafeCoverageRate = displaySchoolStudentTotal
    ? Math.min(displayCoveredStudents / displaySchoolStudentTotal, 1)
    : 0
  const displayHighMatchCount = summary.high_match_students == null
    ? stats.highMatchCount
    : toNumber(summary.high_match_students)
  const displayEmployerCoverage = toNumber(summary.covered_enterprises) || stats.employerCoverage
  const top1AvgSimilarity = summary.top1_avg_similarity == null
    ? toNumber(evalMap.AvgTop1Similarity?.metric_value)
    : toNumber(summary.top1_avg_similarity)
  const highConfidenceRatio = summary.high_confidence_ratio == null
    ? toNumber(evalMap.HighConfidenceRatio?.metric_value)
    : toNumber(summary.high_confidence_ratio)

  useEffect(() => {
    let alive = true
    fetchRecommendationSummary()
      .then((data) => {
        if (alive) setSummary(data || {})
      })
      .catch(() => {
        if (alive) setSummary({})
      })
    return () => {
      alive = false
    }
  }, [roleMode, currentSchool])

  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>
  if (error && !recommendationData.length) return <div style={{ color: designTokens.danger }}>{error}</div>

  const handleSearch = async (targetId = studentId) => {
    const id = String(targetId || '').trim()
    if (!id) {
      message.warning('请输入学生ID')
      return
    }
    setStudentId(id)
    setResult([])
    setSearched(false)
    setQueryMessage('')
    try {
      const payload = await fetchRecommendationStudent({ graduate_id: id })
      const found = Array.isArray(payload?.items) ? payload.items : []
      setResult(found)
      setSearched(true)
      if (!found.length) {
        if (payload?.available_examples?.length) {
          setSummary((old) => ({ ...old, available_examples: payload.available_examples }))
        }
        setQueryMessage(payload?.message || (payload?.student_exists === false ? '未找到该学生，请尝试示例 ID' : '该学生暂无推荐结果，请检查推荐任务是否已生成'))
      }
    } catch (err) {
      const body = err?.response?.data
      const examples = body?.data?.available_examples
      if (examples?.length) setSummary((old) => ({ ...old, available_examples: examples }))
      setResult([])
      setSearched(true)
      if (err?.response?.status >= 500 || !err?.response) {
        setQueryMessage('服务异常，请稍后再试')
        message.error('服务异常，请稍后再试')
        return
      }
      setQueryMessage(body?.message || '未找到该学生，请尝试示例 ID')
    }
  }

  const handleReset = () => {
    setStudentId('')
    setResult([])
    setQueryMessage('')
    setSearched(false)
  }

  const columns = [
    { title: '学生 ID', dataIndex: 'student_id', width: 110, render: (value, record) => value || record.graduate_id || '-' },
    { title: '排名', dataIndex: 'rank_no', width: 80 },
    { title: '推荐单位', dataIndex: 'recommended_enterprise', render: (value, record) => value || record.enterprise_name || '-' },
    { title: '推荐岗位', dataIndex: 'recommended_job', render: (value, record) => value || record.job_category_name || '-' },
    { title: '行业', dataIndex: 'industry_type', render: (value, record) => value || record.leading_industry_tag || '-' },
    { title: '相似度', dataIndex: 'matching_score', render: (value) => Number(value || 0).toFixed(3) },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card style={panelStyle}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} xl={16}>
            <div style={sectionTitleStyle}>就业推荐（余弦相似度）</div>
          </Col>
          <Col xs={24} xl={8}>
            <div style={metaLabelStyle}>数据载入时间</div>
            <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>就业推荐总览</span>} style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="学校毕业生总数" value={formatNumber(displaySchoolStudentTotal)} styles={{ title: statTitleStyle, content: statValuePrimary }} /></Card></Col>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="已覆盖推荐学生数" value={formatNumber(displayCoveredStudents)} styles={{ title: statTitleStyle, content: statValueBlue }} /></Card></Col>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="高匹配学生数" value={formatNumber(displayHighMatchCount)} styles={{ title: statTitleStyle, content: statValueCyan }} /></Card></Col>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="单人展示深度" value={3} suffix="条" styles={{ title: statTitleStyle, content: statValuePurple }} /></Card></Col>
        </Row>
        <div style={{ marginTop: 12, color: designTokens.textMuted }}>
          学校毕业生总数代表当前学校范围内毕业生规模；已覆盖推荐学生数代表推荐算法实际产出结果的人数。覆盖推荐单位数：{formatNumber(displayEmployerCoverage)}。
          {String(summary.school_student_total_source || '').includes('fallback') || String(summary.school_student_total_source || '').includes('reconciled') ? (
            <span> 毕业生总数使用推荐结果去重人数作为数据下限兜底，请检查 fact_graduate 数据链路。</span>
          ) : null}
          {hasTotalAnomaly ? (
            <span> 后端统计口径异常，已按推荐覆盖下限展示。</span>
          ) : null}
        </div>
      </Card>

      <Card title={<span style={sectionTitleStyle}>推荐可信度摘要</span>} style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}><Statistic title="推荐覆盖率" value={(hasTotalAnomaly ? displaySafeCoverageRate : displayCoverageRate) * 100} precision={2} suffix="%" styles={{ title: statTitleStyle, content: statValuePrimary }} /></Col>
          <Col xs={24} md={8}><Statistic title="Top1 平均相似度" value={top1AvgSimilarity} precision={3} styles={{ title: statTitleStyle, content: statValueBlue }} /></Col>
          <Col xs={24} md={8}><Statistic title="高置信推荐占比" value={highConfidenceRatio * 100} precision={2} suffix="%" styles={{ title: statTitleStyle, content: statValueCyan }} /></Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>按学生 ID 查询 Top-K 推荐</span>} style={panelStyle}>
        <Space wrap size="middle" style={{ width: '100%' }}>
          <Input placeholder={`请输入学生ID，例如 ${availableExamples[0] || '7'}`} value={studentId} onChange={(e) => setStudentId(e.target.value)} onPressEnter={() => handleSearch()} style={{ ...inputStyle, width: 280, height: 40 }} />
          <Button type="primary" onClick={() => handleSearch()} style={primaryButtonStyle}>查询推荐</Button>
          <Button onClick={handleReset} style={secondaryButtonStyle}>清空</Button>
        </Space>
        {availableExamples.length ? (
          <div style={{ marginTop: 12, color: designTokens.textMuted }}>
            示例：{availableExamples.map((id) => (
              <Button key={id} type="link" size="small" onClick={() => handleSearch(id)} style={{ paddingInline: 4 }}>{id}</Button>
            ))}
          </div>
        ) : null}
      </Card>

      <Card title={<span style={sectionTitleStyle}>推荐结果分析</span>} style={panelStyle}>
        {!searched && <div style={{ color: designTokens.textSecondary }}>请输入学生 ID 查看 Top-3 就业推荐结果。</div>}
        {searched && !result.length && <Empty description={<span style={{ color: designTokens.textMuted }}>{queryMessage || '未找到该学生的推荐结果，请尝试下方示例 ID'}</span>} />}
        {!!result.length && (
          <Table rowKey={(record) => `${record.student_id || record.graduate_id}-${record.rank_no}`} columns={columns} dataSource={result} pagination={false} />
        )}
      </Card>
    </Space>
  )
}
