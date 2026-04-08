import { useState, useMemo } from 'react'
import { Card, Input, Button, Space, Row, Col, Tag, Empty, message } from 'antd'
// import recommendationData from '../assets/mock/job_recommendation.json'
import {
  getRecommendationByStudent,
  getRecommendationLevel,
  getJobDirectionText,
  getRecommendationAdvice,
  getRecommendationStats,
  formatNumber,
} from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  inputStyle,
  primaryButtonStyle,
  secondaryButtonStyle,
  noteTextStyle,
  statValuePrimary,
  statValueBlue,
  statValueCyan,
  statValuePurple,
} from '../utils/uiTheme'

const miniCardStyle = {
  ...panelStyle,
  minHeight: 138,
  borderRadius: 14,
}

const labelStyle = {
  ...statTitleStyle,
  marginBottom: 10,
}

const textStyle = {
  color: '#d9eeff',
  lineHeight: 1.9,
  fontSize: 15,
}

export default function JobRecommendation({
  recommendationData = [],
  loading,
  error,
}) {
  const [studentId, setStudentId] = useState('')
  const [result, setResult] = useState(null)
  const [searched, setSearched] = useState(false)

  const stats = useMemo(() => {
    return getRecommendationStats(recommendationData)
  }, [recommendationData])

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error) return <div style={{ color: '#ff7875' }}>{error}</div>

  const handleSearch = () => {
    if (!studentId.trim()) {
      message.warning('请先输入学生 ID')
      return
    }

    const found = getRecommendationByStudent(recommendationData, studentId)
    setResult(found || null)
    setSearched(true)

    if (!found) {
      message.info('未查询到该学生的推荐结果')
    }
  }

  const handleReset = () => {
    setStudentId('')
    setResult(null)
    setSearched(false)
  }

  const level = result ? getRecommendationLevel(result.matching_score) : null

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card
        title={<span style={sectionTitleStyle}>就业推荐总览</span>}
        style={panelStyle}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <div style={labelStyle}>推荐样本数</div>
              <div style={statValuePrimary}>
                {formatNumber(stats.totalStudents)}
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <div style={labelStyle}>平均匹配率</div>
              <div style={statValueBlue}>
                {stats.avgScore ? stats.avgScore.toFixed(3) : '0.000'}
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <div style={labelStyle}>高匹配人数</div>
              <div style={statValueCyan}>
                {formatNumber(stats.highMatchCount)}
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <div style={labelStyle}>当前最常见推荐岗位</div>
              <div
                style={{
                  ...statValuePurple,
                  fontSize: 34,
                  lineHeight: 1.35,
                  whiteSpace: 'normal',
                  wordBreak: 'break-all',
                }}
              >
                {stats.topJob}
              </div>
            </Card>
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>按学生 ID 查询岗位推荐</span>} style={panelStyle}>
        <Space wrap size="middle" style={{ width: '100%' }}>
          <Input
            placeholder="请输入学生 ID，例如 4"
            value={studentId}
            onChange={e => setStudentId(e.target.value)}
            onPressEnter={handleSearch}
            style={{ ...inputStyle, width: 280, height: 40 }}
          />

          <Button type="primary" onClick={handleSearch} style={primaryButtonStyle}>
            查询推荐
          </Button>

          <Button onClick={handleReset} style={secondaryButtonStyle}>
            清空
          </Button>
        </Space>

        <div style={{ ...noteTextStyle, marginTop: 12 }}>
          当前版本基于已有推荐数据提供单岗位推荐结果，下一步可升级为 Top3 候选岗位与 AI 推荐解释。
        </div>
      </Card>

      <Card title={<span style={sectionTitleStyle}>推荐结果分析</span>} style={panelStyle}>
        {!searched && (
          <div style={noteTextStyle}>
            请输入学生 ID 进行查询。当前页面已从“单条结果展示”升级为“推荐分析展示”，支持展示匹配等级、推荐方向和培养建议。
          </div>
        )}

        {searched && !result && (
          <Empty
            description={<span style={{ color: 'rgba(217,238,255,0.72)' }}>未查询到该学生推荐结果</span>}
          />
        )}

        {result && (
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={10}>
              <Card style={miniCardStyle}>
                <div style={labelStyle}>基础结果</div>
                <div style={textStyle}><strong>学生 ID：</strong>{result.student_id}</div>
                <div style={textStyle}><strong>推荐岗位：</strong>{result.recommended_job}</div>
                <div style={textStyle}>
                  <strong>匹配率：</strong>
                  <span style={{ ...statValueBlue, fontSize: 24, marginLeft: 6 }}>
                    {Number(result.matching_score).toFixed(3)}
                  </span>
                </div>
                <div style={{ marginTop: 10 }}>
                  <Tag color={level?.color}>{level?.label}</Tag>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={14}>
              <Card style={miniCardStyle}>
                <div style={labelStyle}>推荐解释</div>
                <div style={textStyle}>
                  <strong>推荐方向：</strong>{getJobDirectionText(result.recommended_job)}
                </div>
                <div style={textStyle}>
                  <strong>岗位判断：</strong>
                  当前推荐结果表明，该学生与
                  <span style={{ color: '#91caff', margin: '0 4px' }}>
                    {result.recommended_job}
                  </span>
                  具有较高关联度，适合作为当前优先关注的就业方向。
                </div>
              </Card>
            </Col>

            <Col xs={24}>
              <Card style={miniCardStyle}>
                <div style={labelStyle}>培养建议</div>
                <div style={textStyle}>
                  {getRecommendationAdvice(result.recommended_job, result.matching_score)}
                </div>
              </Card>
            </Col>
          </Row>
        )}
      </Card>
    </Space>
  )
}