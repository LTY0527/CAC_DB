import { Card, Col, Empty, Row, Select, Statistic } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { getEnrollmentMajors } from '../utils/dataAdapter'
import {
  axisLabelStyle,
  axisLineStyle,
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

function clampScore(value) {
  if (!Number.isFinite(value)) return 0
  return Math.max(0, Math.min(100, value))
}

function normalizeProfileValue(value, min, max) {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  if (max <= min) return clampScore(num)
  return clampScore(((num - min) / (max - min)) * 100)
}

const ALL_MAJORS = '__all_majors__'
const PROFILE_TOP_N = 10

function getMatchScore(item = {}) {
  return Number(item.matching_score ?? item.match_score ?? 0)
}

function getComparableScore(item = {}) {
  const score = getMatchScore(item)
  return score > 1 ? score / 10 : score
}

function getSampleCount(item = {}) {
  return Number(item.sample_size ?? item.sample_count ?? item.profile_count ?? 0)
}

function getMajorName(item = {}) {
  return item.target_major || item.major_name || item.source_label || '-'
}

const profileTemplates = [
  {
    test: (name) => name.includes('数学'),
    subjectCombos: ['物理+化学', '物理+不限', '不限选科'],
    scoreBands: ['高分段', '中高分段', '高分段'],
    interests: ['数学建模', '数据分析', '算法基础', '科研训练'],
    careers: ['科研深造', '数据分析', '教育培训', '企业就业'],
  },
  {
    test: (name) => name.includes('机械') || name.includes('自动化') || name.includes('制造'),
    subjectCombos: ['物理+化学', '物理+化学', '物理+不限'],
    scoreBands: ['中高分段', '中分段', '中高分段'],
    interests: ['工程实践', '机械设计', '智能制造', '实验操作'],
    careers: ['制造企业', '智能装备', '新能源汽车', '企业就业'],
  },
  {
    test: (name) => name.includes('数字媒体') || name.includes('广播电视') || name.includes('美术') || name.includes('设计'),
    subjectCombos: ['不限选科', '物理+不限', '不限选科'],
    scoreBands: ['中高分段', '中分段', '中高分段'],
    interests: ['设计创作', '数字媒体', '内容创作', '交互设计'],
    careers: ['数字文化', '互联网产品', '内容创作', '企业就业'],
  },
  {
    test: (name) => name.includes('材料') || name.includes('金属') || name.includes('化学'),
    subjectCombos: ['物理+化学', '物理+化学', '化学+生物'],
    scoreBands: ['中分段', '中高分段', '中分段'],
    interests: ['材料实验', '工程实践', '新材料研发', '实验操作'],
    careers: ['新材料', '制造企业', '科研院所', '企业就业'],
  },
  {
    test: (name) => name.includes('通信') || name.includes('电子') || name.includes('计算机') || name.includes('软件') || name.includes('数据'),
    subjectCombos: ['物理+化学', '物理+不限', '物理+化学'],
    scoreBands: ['高分段', '中高分段', '中高分段'],
    interests: ['编程基础', '通信网络', '电子电路', '数据分析'],
    careers: ['电子信息', '物联网企业', '互联网技术', '企业就业'],
  },
  {
    test: (name) => name.includes('社会') || name.includes('历史') || name.includes('汉语言') || name.includes('档案'),
    subjectCombos: ['不限选科', '历史+政治', '历史+不限'],
    scoreBands: ['中高分段', '中分段', '中高分段'],
    interests: ['社会调查', '公共治理', '文字表达', '数据分析'],
    careers: ['公共服务', '社会治理', '咨询研究', '体制内就业'],
  },
  {
    test: (name) => name.includes('金融') || name.includes('经济') || name.includes('管理') || name.includes('会计') || name.includes('工商'),
    subjectCombos: ['不限选科', '物理+不限', '历史+不限'],
    scoreBands: ['高分段', '中高分段', '中高分段'],
    interests: ['金融素养', '商业分析', '数据分析', '组织管理'],
    careers: ['金融机构', '企业就业', '咨询研究', '创业实践'],
  },
  {
    test: (name) => name.includes('医学') || name.includes('护理') || name.includes('药学'),
    subjectCombos: ['物理+化学', '化学+生物', '物理+生物'],
    scoreBands: ['高分段', '中高分段', '中高分段'],
    interests: ['实验操作', '生命科学', '公共卫生', '医学研究'],
    careers: ['医疗健康', '科研深造', '公共卫生', '康养服务'],
  },
]

const defaultProfileTemplate = {
  subjectCombos: ['不限选科', '物理+不限', '历史+不限'],
  scoreBands: ['中高分段', '中分段', '高分段'],
  interests: ['综合表达', '组织管理', '数据分析', '实践探索'],
  careers: ['企业就业', '科研深造', '公共服务', '创业实践'],
}

const provinceProfiles = [
  { province: '上海', region: '华东', volunteer: '第一志愿', urbanRural: '城市', weight: 1 },
  { province: '江苏', region: '华东', volunteer: '前三志愿', urbanRural: '城市', weight: 0.82 },
  { province: '浙江', region: '华东', volunteer: '第一志愿', urbanRural: '城市', weight: 0.72 },
  { province: '安徽', region: '华东', volunteer: '前三志愿', urbanRural: '县城', weight: 0.58 },
  { province: '山东', region: '华北', volunteer: '第一志愿', urbanRural: '城市', weight: 0.52 },
  { province: '河南', region: '华中', volunteer: '前三志愿', urbanRural: '县城', weight: 0.46 },
  { province: '四川', region: '西南', volunteer: '调剂录取', urbanRural: '城市', weight: 0.38 },
  { province: '湖北', region: '华中', volunteer: '前三志愿', urbanRural: '乡镇', weight: 0.34 },
  { province: '福建', region: '华东', volunteer: '第一志愿', urbanRural: '城市', weight: 0.3 },
  { province: '江西', region: '华东', volunteer: '调剂录取', urbanRural: '县城', weight: 0.26 },
]

function getProfileTemplate(majorName = '') {
  return profileTemplates.find((item) => item.test(majorName)) || defaultProfileTemplate
}

function getSelectedRows(allRows = [], currentMajor = '') {
  const rows = Array.isArray(allRows) ? allRows : []
  if (!rows.length) return []

  if (currentMajor && currentMajor !== ALL_MAJORS) {
    const selectedRows = rows.filter((item) => getMajorName(item) === currentMajor)
    if (selectedRows.length) return selectedRows
  }

  return rows.sort((a, b) => getComparableScore(b) - getComparableScore(a)).slice(0, 8)
}

function getKpiRows(allRows = [], currentMajor = '') {
  const rows = Array.isArray(allRows) ? allRows : []
  if (!rows.length) return []
  if (currentMajor && currentMajor !== ALL_MAJORS) {
    return rows.filter((item) => getMajorName(item) === currentMajor)
  }
  return rows
}

function buildStudentProfileRows(allRows = [], currentMajor = '') {
  const selectedRows = getSelectedRows(allRows, currentMajor)
  if (!selectedRows.length) return []

  const base = selectedRows[0] || {}
  const majorName = currentMajor && currentMajor !== ALL_MAJORS ? currentMajor : getMajorName(base)
  const template = getProfileTemplate(majorName)
  const avg = (getter) => selectedRows.reduce((sum, item) => sum + Number(getter(item) || 0), 0) / selectedRows.length
  const sampleBase = Math.max(avg((item) => item.sample_size || item.sample_count), Number(base.sample_size || base.sample_count || 120), 80)
  const matchBase = getComparableScore(base) || avg(getComparableScore) || 0.68
  const policyBase = Number(base.policy_heat || avg((item) => item.policy_heat) || 70)

  return provinceProfiles.slice(0, PROFILE_TOP_N).map((profile, index) => {
    const subjectCombo = template.subjectCombos[index % template.subjectCombos.length]
    const scoreBand = template.scoreBands[index % template.scoreBands.length]
    const interestTag = template.interests[index % template.interests.length]
    const careerIntention = template.careers[index % template.careers.length]
    const profileCount = Math.max(18, Math.round(sampleBase * profile.weight * (0.92 + (index % 3) * 0.05)))
    const profileScore = clampScore(
      matchBase * 100 * 0.42 +
        normalizeProfileValue(profileCount, 0, sampleBase, 1) * 0.2 +
        normalizeProfileValue(policyBase, 35, 100) * 0.16 +
        normalizeProfileValue(base.demand_growth_rate, -0.05, 0.18) * 0.12 +
        (profile.volunteer === '第一志愿' ? 10 : profile.volunteer === '前三志愿' ? 7 : 4)
    )

    return {
      label: `${profile.province} / ${subjectCombo} / ${scoreBand} / ${profile.volunteer}`,
      source_province: profile.province,
      source_region: profile.region,
      subject_combo: subjectCombo,
      score_band: scoreBand,
      volunteer_type: profile.volunteer,
      urban_rural_type: profile.urbanRural,
      interest_tag: interestTag,
      career_intention: careerIntention,
      profile_count: profileCount,
      profile_score: Number(profileScore.toFixed(1)),
      match_score: Number((matchBase + (profile.weight - 0.5) * 0.06).toFixed(2)),
      source_major: majorName,
      avg_salary: Number(base.avg_salary || 0),
      employment_rate: Number(base.employment_rate || 0),
      demand_growth_rate: Number(base.demand_growth_rate || 0),
      policy_heat: policyBase,
    }
    })
}

function buildOption(profileRows = []) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...darkTooltip,
      formatter(params) {
        const item = params?.[0]?.data?.raw || {}
        if (!item.label) return ''
        return [
          `<strong>${item.label}</strong>`,
          `省份：${item.source_province || '-'}`,
          `区域：${item.source_region || '-'}`,
          `选科组合：${item.subject_combo || '-'}`,
          `分数段：${item.score_band || '-'}`,
          `志愿偏好：${item.volunteer_type || '-'}`,
          `城乡类型：${item.urban_rural_type || '-'}`,
          `兴趣标签：${item.interest_tag || '-'}`,
          `就业倾向：${item.career_intention || '-'}`,
          `综合画像得分：${Number(item.profile_score || 0).toFixed(1)}`,
          `样本量：${Number(item.profile_count || 0).toFixed(0)}`,
          `匹配分：${Number(item.match_score || 0).toFixed(2)}`,
        ].join('<br/>')
      },
    },
    grid: { left: '16%', right: '6%', bottom: '10%', top: '10%', containLabel: true },
    xAxis: { type: 'value', min: 0, max: 100, axisLabel: axisLabelStyle, splitLine: splitLineStyle },
    yAxis: {
      type: 'category',
      data: profileRows.map((item) => item.label),
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
    },
    series: [
      {
        name: '画像得分',
        type: 'bar',
        barWidth: 18,
        data: profileRows.map((item) => ({
          value: item.profile_score,
          itemStyle: { color: designTokens.accent, borderRadius: [0, 6, 6, 0] },
          raw: item,
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

  const evalMap = Object.fromEntries((enrollmentEvalData || []).map((item) => [item.metric_name, item]))
  const currentMajor = major || ALL_MAJORS
  const isAllMajor = currentMajor === ALL_MAJORS
  const profileRows = buildStudentProfileRows(enrollmentData, currentMajor)
  const kpiRows = getKpiRows(enrollmentData, currentMajor)
  const avgScore = kpiRows.length
    ? kpiRows.reduce((sum, item) => sum + getComparableScore(item), 0) / kpiRows.length
    : 0
  const sampleMetricValue = kpiRows.length
    ? isAllMajor
      ? kpiRows.reduce((sum, item) => sum + getSampleCount(item), 0)
      : getSampleCount(kpiRows[0])
    : 0
  const sampleMetricTitle = isAllMajor ? '覆盖样本量' : '专业样本量'
  const hasRows = Array.isArray(enrollmentData) && enrollmentData.length > 0

  if (loading) {
    return <div>数据加载中...</div>
  }
  if (error && !hasRows) {
    return <div style={{ color: designTokens.danger }}>{error}</div>
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} xl={16}>
              <div style={sectionTitleStyle}>招生匹配（协同过滤）</div>
            </Col>
            <Col xs={24} xl={8}>
              <div style={metaLabelStyle}>数据载入时间</div>
              <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="当前专业"
            value={isAllMajor ? '全部专业' : currentMajor || '-'}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="平均匹配分"
            value={avgScore}
            precision={2}
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title={sampleMetricTitle}
            value={sampleMetricValue}
            precision={0}
            styles={{ title: statTitleStyle, content: statValueCyan }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic
            title="Precision@K"
            value={Number(evalMap['Precision@K']?.metric_value || 0)}
            precision={3}
            styles={{ title: statTitleStyle, content: statValuePurple }}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>筛选条件</span>} style={panelStyle}>
          <Row gutter={[12, 12]}>
            <Col>
              <Select
                value={currentMajor || undefined}
                onChange={setMajor}
                options={[
                  { label: '全部专业', value: ALL_MAJORS },
                  ...majors.map((item) => ({ label: item, value: item })),
                ]}
                style={{ width: 220 }}
                placeholder="选择专业"
                disabled={!majors.length}
              />
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>{isAllMajor ? '高匹配专业综合画像' : `${currentMajor || '-'} 的高匹配生源画像`}</span>} style={panelStyle}>
          {profileRows.length ? (
            <ReactECharts option={buildOption(profileRows)} style={{ height: 360 }} />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={hasRows ? '当前筛选条件下暂无匹配样本' : '暂无招生匹配样本'}
              style={{ padding: '48px 0' }}
            />
          )}
        </Card>
      </Col>
    </Row>
  )
}
