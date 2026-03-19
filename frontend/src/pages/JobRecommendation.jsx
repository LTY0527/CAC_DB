import { useState } from 'react'
import { Card, Input, Button, Space } from 'antd'
import recommendationData from '../assets/mock/job_recommendation.json'
import { getRecommendationByStudent } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  inputStyle,
  primaryButtonStyle,
  noteTextStyle,
  statValueBlue,
} from '../utils/uiTheme'


export default function JobRecommendation() {
  const [studentId, setStudentId] = useState('')
  const [result, setResult] = useState(null)

  const handleSearch = () => {
    const found = getRecommendationByStudent(recommendationData, studentId)
    setResult(found || null)
  }

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title={<span style={sectionTitleStyle}>按学生 ID 查询岗位推荐</span>} style={panelStyle}>
      <Input
      placeholder="请输入学生 ID，例如 4"
      value={studentId}
      onChange={e => setStudentId(e.target.value)}
      style={{ ...inputStyle, marginBottom: 12, height: 40 }}
      />
      <Button type="primary" onClick={handleSearch} style={primaryButtonStyle}>
    查询推荐
    </Button>
    </Card>

      <Card title={<span style={sectionTitleStyle}>推荐结果</span>} style={panelStyle}>
  {!result && (
    <div style={noteTextStyle}>
      当前显示单岗位推荐结果。若后续补充 Top3 推荐数据，可升级为卡片列表。
    </div>
  )}

  {result && (
    <div style={{ color: '#d9eeff', lineHeight: 2 }}>
      <div><strong>学生 ID：</strong>{result.student_id}</div>
      <div><strong>推荐岗位：</strong>{result.recommended_job}</div>
      <div>
        <strong>匹配率：</strong>
        <span style={{ ...statValueBlue, fontSize: 24 }}>
          {Number(result.matching_score).toFixed(3)}
        </span>
      </div>
    </div>
  )}
</Card>
    </Space>
  )
}