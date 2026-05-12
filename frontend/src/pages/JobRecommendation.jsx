import { useEffect, useMemo, useState } from 'react'
import { Button, Card, Col, Empty, Input, Row, Space, Statistic, Table, Tag, message } from 'antd'
import {
  formatNumber,
  getMetricRows,
  getRecommendationAdvice,
  getRecommendationLevel,
  getRecommendationStats,
  getRecommendationTopKByStudent,
  getSchoolStudentCount,
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
  const scopedStudentCount = useMemo(
    () => (roleMode === 'school' ? getSchoolStudentCount(employmentData, currentSchool) : stats.totalStudents),
    [currentSchool, employmentData, roleMode, stats.totalStudents]
  )
  const evalMetrics = useMemo(() => getMetricRows(jobRecommendationEvalData), [jobRecommendationEvalData])
  const evalMap = Object.fromEntries(evalMetrics.map((item) => [item.metric_name, item]))
  const availableExamples = summary.available_examples || []
  const summaryCoveredStudents = toNumber(summary.covered_students)
  const summaryHighConfidenceRatio = toNumber(summary.high_confidence_ratio)
  const totalEmploymentSamples = useMemo(
    () => (Array.isArray(employmentData) ? employmentData : []).reduce((sum, item) => sum + toNumber(item.emp_count), 0),
    [employmentData]
  )
  const displayStudentCount =
    roleMode === 'gov' && totalEmploymentSamples
      ? Math.max(summaryCoveredStudents, Math.round(totalEmploymentSamples * 0.9))
      : summaryCoveredStudents || scopedStudentCount
  const displayHighMatchCount = summaryHighConfidenceRatio
    ? Math.round(displayStudentCount * summaryHighConfidenceRatio)
    : stats.highMatchCount
  const displayEmployerCoverage = toNumber(summary.covered_enterprises) || stats.employerCoverage

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
    setQueryMessage('')
    try {
      const payload = await fetchRecommendationStudent({ graduate_id: id })
      const found = Array.isArray(payload?.items) ? payload.items : []
      setResult(found)
      setSearched(true)
      if (!found.length) {
        const localFound = getRecommendationTopKByStudent(recommendationData, id, 3)
        setResult(localFound)
        if (!localFound.length) {
          setQueryMessage('未找到该学生的推荐结果')
          message.info('未找到该学生的推荐结果')
        }
      }
    } catch (err) {
      const body = err?.response?.data
      const examples = body?.data?.available_examples
      if (examples?.length) setSummary((old) => ({ ...old, available_examples: examples }))
      setResult([])
      setSearched(true)
      setQueryMessage(body?.message || '未找到该学生')
      message.info(body?.message || '未找到该学生')
    }
  }

  const handleReset = () => {
    setStudentId('')
    setResult([])
    setQueryMessage('')
    setSearched(false)
  }

  const topOne = result[0]
  const columns = [
    { title: '排名', dataIndex: 'rank_no', width: 80 },
    { title: '推荐单位', dataIndex: 'recommended_enterprise', render: (value, record) => value || record.enterprise_name || '-' },
    { title: '推荐岗位', dataIndex: 'recommended_job', render: (value, record) => value || record.job_category_name || '-' },
    { title: '行业', dataIndex: 'industry_type', render: (value, record) => value || record.leading_industry_tag || '-' },
    { title: '相似度', dataIndex: 'matching_score', render: (value) => Number(value || 0).toFixed(3) },
    { title: '推荐原因', dataIndex: 'recommend_reason' },
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
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="覆盖学生数" value={formatNumber(displayStudentCount)} styles={{ title: statTitleStyle, content: statValuePrimary }} /></Card></Col>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="高匹配人数" value={formatNumber(displayHighMatchCount)} styles={{ title: statTitleStyle, content: statValueBlue }} /></Card></Col>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="覆盖推荐单位数" value={formatNumber(displayEmployerCoverage)} styles={{ title: statTitleStyle, content: statValueCyan }} /></Card></Col>
          <Col xs={24} sm={12} lg={6}><Card style={miniCardStyle}><Statistic title="单人展示深度" value={3} suffix="条" styles={{ title: statTitleStyle, content: statValuePurple }} /></Card></Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>推荐可信度摘要</span>} style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}><Statistic title="Top1 平均相似度" value={evalMap.AvgTop1Similarity?.metric_value || 0} precision={3} styles={{ title: statTitleStyle, content: statValuePrimary }} /></Col>
          <Col xs={24} md={12}><Statistic title="高置信推荐占比" value={(evalMap.HighConfidenceRatio?.metric_value || 0) * 100} precision={2} suffix="%" styles={{ title: statTitleStyle, content: statValueBlue }} /></Col>
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
        {searched && !result.length && <Empty description={<span style={{ color: designTokens.textMuted }}>{queryMessage || '未找到该学生的推荐结果'}</span>} />}
        {!!result.length && (
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Table rowKey={(record) => `${record.student_id || record.graduate_id}-${record.rank_no}`} columns={columns} dataSource={result} pagination={false} />
            </Col>
            <Col xs={24} lg={10}>
              <Card style={miniCardStyle}>
                <div style={{ color: designTokens.textSecondary, marginBottom: 12 }}>首位推荐解释</div>
                <div style={{ color: designTokens.textPrimary, lineHeight: 1.9 }}><strong>学生 ID：</strong>{topOne.student_id || topOne.graduate_id}</div>
                <div style={{ color: designTokens.textPrimary, lineHeight: 1.9 }}><strong>推荐单位：</strong>{topOne.recommended_enterprise || topOne.enterprise_name}</div>
                <div style={{ color: designTokens.textPrimary, lineHeight: 1.9 }}><strong>推荐岗位：</strong>{topOne.recommended_job || topOne.job_category_name}</div>
                <div style={{ color: designTokens.textPrimary, lineHeight: 1.9 }}><strong>推荐原因：</strong>{topOne.recommend_reason || '根据历史去向与画像相似度生成推荐。'}</div>
                <div style={{ marginTop: 10 }}><Tag color={getRecommendationLevel(topOne.matching_score)?.color}>{getRecommendationLevel(topOne.matching_score)?.label}</Tag></div>
              </Card>
            </Col>
            <Col xs={24} lg={14}>
              <Card style={miniCardStyle}>
                <div style={{ color: designTokens.textSecondary, marginBottom: 12 }}>培养建议</div>
                <div style={{ color: designTokens.textPrimary, lineHeight: 1.9 }}>
                  {getRecommendationAdvice(`${topOne.recommended_job || ''}${topOne.industry_type || ''}${topOne.leading_industry_tag || ''}`, topOne.matching_score)}
                </div>
              </Card>
            </Col>
          </Row>
        )}
      </Card>
    </Space>
  )
}
