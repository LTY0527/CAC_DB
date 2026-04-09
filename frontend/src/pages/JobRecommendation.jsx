import { useMemo, useState } from 'react'
import { Button, Card, Col, Empty, Input, Row, Space, Statistic, Table, Tag, message } from 'antd'
import {
  formatNumber,
  getMetricRows,
  getRecommendationAdvice,
  getRecommendationLevel,
  getRecommendationStats,
  getRecommendationTopKByStudent,
} from '../utils/dataAdapter'
import {
  algorithmTextStyle,
  inputStyle,
  metaLabelStyle,
  metaValueStyle,
  noteTextStyle,
  panelStyle,
  primaryButtonStyle,
  riskTextStyle,
  secondaryButtonStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

const miniCardStyle = {
  ...panelStyle,
  minHeight: 138,
  borderRadius: 14,
}

export default function JobRecommendation({
  recommendationData = [],
  jobRecommendationEvalData = [],
  dataLoadedAt = '',
  loading,
  error,
}) {
  const [studentId, setStudentId] = useState('')
  const [result, setResult] = useState([])
  const [searched, setSearched] = useState(false)

  const stats = useMemo(() => getRecommendationStats(recommendationData), [recommendationData])
  const evalMetrics = useMemo(() => getMetricRows(jobRecommendationEvalData), [jobRecommendationEvalData])
  const evalMap = Object.fromEntries(evalMetrics.map((item) => [item.metric_name, item]))

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !recommendationData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  const handleSearch = () => {
    if (!studentId.trim()) {
      message.warning('请先输入学生 ID')
      return
    }

    const found = getRecommendationTopKByStudent(recommendationData, studentId, 3)
    setResult(found)
    setSearched(true)

    if (!found.length) {
      message.info('未查询到该学生的推荐结果')
    }
  }

  const handleReset = () => {
    setStudentId('')
    setResult([])
    setSearched(false)
  }

  const topOne = result[0]
  const columns = [
    { title: '排名', dataIndex: 'rank_no', width: 80 },
    { title: '推荐单位', dataIndex: 'recommended_job' },
    { title: '行业', dataIndex: 'industry_type', render: (value, record) => value || record.leading_industry_tag || '-' },
    { title: '相似度', dataIndex: 'matching_score', render: (value) => Number(value || 0).toFixed(3) },
    { title: '推荐原因', dataIndex: 'recommend_reason' },
  ]

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} xl={14}>
            <div style={sectionTitleStyle}>就业推荐（余弦相似度）</div>
            <div style={{ ...noteTextStyle, marginTop: 10 }}>
              业务价值：将学生画像与岗位画像进行相似度匹配，给出更具针对性的就业去向建议，并反向提示学生需要补强的能力。
            </div>
          </Col>
          <Col xs={24} xl={10}>
            <Row gutter={[12, 12]}>
              <Col span={12}>
                <div style={metaLabelStyle}>数据载入时间</div>
                <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
              </Col>
              <Col span={12}>
                <div style={metaLabelStyle}>推荐口径</div>
                <div style={metaValueStyle}>展示数据库中的 Top-3 推荐结果</div>
              </Col>
              <Col span={24}>
                <div style={algorithmTextStyle}>算法说明：基于学生特征向量与岗位特征向量计算余弦相似度，再输出 Top-K 推荐列表和推荐原因。</div>
              </Col>
              <Col span={24}>
                <div style={riskTextStyle}>风险提示：推荐结果适合做就业方向辅助，不应替代学生个体意愿、岗位实时需求和人工咨询判断。</div>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>就业推荐总览</span>} style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <Statistic title="推荐学生数" value={formatNumber(stats.totalStudents)} styles={{ title: statTitleStyle, content: statValuePrimary }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <Statistic title="Top1 平均相似度" value={stats.avgScore} precision={3} styles={{ title: statTitleStyle, content: statValueBlue }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <Statistic title="高匹配人数" value={formatNumber(stats.highMatchCount)} styles={{ title: statTitleStyle, content: statValueCyan }} />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card style={miniCardStyle}>
              <Statistic title="最常见首荐单位" value={stats.topJob} styles={{ title: statTitleStyle, content: statValuePurple }} />
            </Card>
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>算法可信度</span>} style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Statistic title="AvgTop1Similarity" value={evalMap.AvgTop1Similarity?.metric_value || 0} precision={3} styles={{ title: statTitleStyle, content: statValuePrimary }} />
            <div style={{ ...noteTextStyle, marginTop: 8 }}>{evalMap.AvgTop1Similarity?.metric_desc || '衡量首位推荐与学生画像的平均相似度。'}</div>
          </Col>
          <Col xs={24} md={8}>
            <Statistic title="AvgTopKSimilarity" value={evalMap.AvgTopKSimilarity?.metric_value || 0} precision={3} styles={{ title: statTitleStyle, content: statValueBlue }} />
            <div style={{ ...noteTextStyle, marginTop: 8 }}>{evalMap.AvgTopKSimilarity?.metric_desc || '衡量 Top-K 推荐整体相似度水平。'}</div>
          </Col>
          <Col xs={24} md={8}>
            <Statistic title="HighConfidenceRatio" value={(evalMap.HighConfidenceRatio?.metric_value || 0) * 100} precision={2} suffix="%" styles={{ title: statTitleStyle, content: statValueCyan }} />
            <div style={{ ...noteTextStyle, marginTop: 8 }}>{evalMap.HighConfidenceRatio?.metric_desc || '相似度高于阈值的高置信推荐占比。'}</div>
          </Col>
        </Row>
      </Card>

      <Card title={<span style={sectionTitleStyle}>按学生 ID 查询 Top-K 推荐</span>} style={panelStyle}>
        <Space wrap size="middle" style={{ width: '100%' }}>
          <Input
            placeholder="请输入学生 ID，例如 14"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            onPressEnter={handleSearch}
            style={{ ...inputStyle, width: 280, height: 40 }}
          />
          <Button type="primary" onClick={handleSearch} style={primaryButtonStyle}>查询推荐</Button>
          <Button onClick={handleReset} style={secondaryButtonStyle}>清空</Button>
        </Space>
        <div style={{ ...noteTextStyle, marginTop: 12 }}>
          页面不仅显示推荐单位，还会给出相似度分数、推荐原因和培养建议，方便答辩时讲清“为什么推荐”。
        </div>
      </Card>

      <Card title={<span style={sectionTitleStyle}>推荐结果分析</span>} style={panelStyle}>
        {!searched && <div style={noteTextStyle}>请输入学生 ID 查看 Top-K 就业推荐结果。</div>}
        {searched && !result.length && (
          <Empty description={<span style={{ color: 'rgba(217,238,255,0.72)' }}>未查询到该学生推荐结果</span>} />
        )}
        {!!result.length && (
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Table rowKey={(record) => `${record.student_id}-${record.rank_no}`} columns={columns} dataSource={result} pagination={false} />
            </Col>
            <Col xs={24} lg={10}>
              <Card style={miniCardStyle}>
                <div style={{ color: '#b7dfff', marginBottom: 12 }}>首位推荐解释</div>
                <div style={{ color: '#d9eeff', lineHeight: 1.9 }}><strong>学生 ID：</strong>{topOne.student_id}</div>
                <div style={{ color: '#d9eeff', lineHeight: 1.9 }}><strong>推荐单位：</strong>{topOne.recommended_job}</div>
                <div style={{ color: '#d9eeff', lineHeight: 1.9 }}><strong>推荐原因：</strong>{topOne.recommend_reason || '根据历史去向与画像相似度生成推荐。'}</div>
                <div style={{ marginTop: 10 }}>
                  <Tag color={getRecommendationLevel(topOne.matching_score)?.color}>{getRecommendationLevel(topOne.matching_score)?.label}</Tag>
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={14}>
              <Card style={miniCardStyle}>
                <div style={{ color: '#b7dfff', marginBottom: 12 }}>培养建议</div>
                <div style={{ color: '#d9eeff', lineHeight: 1.9 }}>
                  {getRecommendationAdvice(
                    `${topOne.recommended_job || ''}${topOne.industry_type || ''}${topOne.leading_industry_tag || ''}`,
                    topOne.matching_score
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        )}
      </Card>
    </Space>
  )
}
