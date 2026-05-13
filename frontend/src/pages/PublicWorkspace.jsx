import { Card, Col, Empty, List, Row, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import PublicHeroBanner from '../components/PublicHeroBanner'
import SchoolMapExplorer from '../components/SchoolMapExplorer'
import UniversitySlider from '../components/UniversitySlider'
import {
  formatNumber,
  getPublicOverview,
  getPublicTopMajors,
} from '../utils/dataAdapter'
import { fetchPublicSchoolComparison } from '../services/dataService'
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
  statValuePrimary,
} from '../utils/uiTheme'

const PUBLIC_SCHOOL_DISPLAY_MAJOR_MAP = {
  上海交通大学: '计算机科学与技术',
  同济大学: '土木工程',
  复旦大学: '数学与应用数学',
  上海大学: '金属材料工程',
  华东师范大学: '教育学',
  上海理工大学: '能源与动力工程',
  华东理工大学: '化学工程与工艺',
  东华大学: '纺织科学与工程',
  上海外国语大学: '国际经济与贸易',
  上海财经大学: '会计学',
}

function buildPublicMajorBarOption(data = []) {
  const values = data.map((item) => Number(item.avg_salary || 0))
  const min = values.length ? Math.floor((Math.min(...values) - 500) / 500) * 500 : 0
  const max = values.length ? Math.ceil((Math.max(...values) + 500) / 500) * 500 : 20000

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const index = params?.[0]?.dataIndex ?? 0
        const item = data[index] || {}
        const tags = Array.isArray(item.industry_trend_tags)
          ? item.industry_trend_tags.join('、')
          : (item.industry_trend_tags || '')
        return `${item.major_name || '-'}<br/>平均薪资：${formatNumber(item.avg_salary, 0)} 元<br/>样本规模：${formatNumber(item.sample_count, 0)}${tags ? `<br/>趋势标签：${tags}` : ''}`
      },
    },
    grid: { left: '8%', right: '4%', bottom: '8%', top: '8%', containLabel: true },
    xAxis: {
      type: 'value',
      min,
      max,
      axisLabel: {
        color: designTokens.textMuted,
        formatter: (value) => `${Math.round(Number(value || 0) / 1000)}k`,
      },
      splitLine: splitLineStyle,
    },
    yAxis: {
      type: 'category',
      data: data.map((item) => item.major_name),
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
    },
    series: [
      {
        type: 'bar',
        data: data.map((item) => Number(item.avg_salary || 0)),
        barWidth: 16,
        itemStyle: {
          color: designTokens.accent,
          borderRadius: [0, 8, 8, 0],
        },
      },
    ],
  }
}

function buildSchoolCompareOption(data = []) {
  const labels = data.map((item) => `${item.school_name}\n${getDisplayMajorName(item)}`)
  const salaryValues = data.map((item) => Number(item.avg_salary || 0))
  const sampleValues = data.map((item) => Number(item.employment_sample_count || 0))
  const salaryMin = salaryValues.length ? Math.floor((Math.min(...salaryValues) - 500) / 500) * 500 : 0
  const salaryMax = salaryValues.length ? Math.ceil((Math.max(...salaryValues) + 500) / 500) * 500 : 20000

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const index = params?.[0]?.dataIndex ?? 0
        const item = data[index] || {}
        return [
          `学校：${item.school_name || '-'}`,
          `专业：${getDisplayMajorName(item)}`,
          `平均薪资：${formatNumber(item.avg_salary || 0, 0)} 元`,
          `样本规模：${formatNumber(item.employment_sample_count || 0, 0)}`,
          `高质量就业率：${(Number(item.high_quality_employment_rate || 0) * 100).toFixed(1)}%`,
          `先导产业占比：${(Number(item.leading_industry_rate || item.leading_industry_employment_rate || 0) * 100).toFixed(1)}%`,
        ].join('<br/>')
      },
    },
    grid: { left: '6%', right: '8%', bottom: '18%', top: '16%', containLabel: true },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { ...axisLabelStyle, interval: 0, lineHeight: 18, fontSize: 12 },
      axisLine: axisLineStyle,
    },
    yAxis: [
      {
        type: 'value',
        name: '平均薪资',
        min: salaryMin,
        max: salaryMax,
        axisLabel: axisLabelStyle,
        nameTextStyle: { color: designTokens.textMuted },
        splitLine: splitLineStyle,
      },
      {
        type: 'value',
        name: '样本规模',
        min: 0,
        axisLabel: axisLabelStyle,
        nameTextStyle: { color: designTokens.textMuted },
      },
    ],
    series: [
      {
        name: '平均薪资',
        type: 'bar',
        barMaxWidth: 24,
        data: salaryValues,
        itemStyle: { color: designTokens.accent, borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '样本规模',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: sampleValues,
        lineStyle: { width: 2.5, color: designTokens.accentSecondary },
        itemStyle: { color: designTokens.accentSecondary },
      },
    ],
  }
}

function getDisplayMajorName(item = {}) {
  const schoolName = String(item.school_name || item.schoolName || '').trim()
  const mapped = PUBLIC_SCHOOL_DISPLAY_MAJOR_MAP[schoolName]
  if (mapped) return mapped
  const name = item.display_major_name
    || item.displayMajorName
    || item.major_name
    || item.majorName
    || item.advantage_major?.major_name
    || item.advantageMajor?.majorName
    || item.advantage_major_name
  if (schoolName === '上海大学' && name === '轻化工程') return '金属材料工程'
  return name && name !== '数据不足' ? name : '数据不足'
}

function normalizeSchoolComparisonItems(payload = {}) {
  const rawItems = Array.isArray(payload?.items) ? payload.items : []
  const bySchool = new Map()
  rawItems.forEach((item) => {
    if (!item?.school_id || !item?.school_name) return
    if (!bySchool.has(item.school_id)) {
      const major = item?.advantage_major || null
      const displayMajorName = getDisplayMajorName(item)
      bySchool.set(item.school_id, {
        ...item,
        advantage_major: major,
        display_major_name: displayMajorName,
        major_name: displayMajorName,
        advantage_major_name: displayMajorName,
        advantage_major_status: major ? (item.advantage_major_status || 'verified') : (item.advantage_major_status || 'no_verified_relation'),
      })
    }
  })
  return [...bySchool.values()]
}

function PublicEmptyState({ dataLoadedAt = '' }) {
  return (
    <Card style={panelStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <div style={sectionTitleStyle}>社会公众端</div>
        <div>
          <div style={metaLabelStyle}>页面载入时间</div>
          <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
        </div>
      </div>
      <Empty description="暂无可用于公开展示的就业样本" />
    </Card>
  )
}

function PublicHome({ employmentData = [], publicSalaryRankingData = [], dataLoadedAt = '' }) {
  const navigate = useNavigate()
  const overview = getPublicOverview(employmentData)
  const topMajors = Array.isArray(publicSalaryRankingData) && publicSalaryRankingData.length
    ? publicSalaryRankingData
    : getPublicTopMajors(employmentData)
  const hasOverview = overview.schoolCount > 0 && overview.avgSalary > 0

  if (!hasOverview) {
    return <PublicEmptyState dataLoadedAt={dataLoadedAt} />
  }

  const handleHeroAction = (actionType) => {
    if (actionType === 'navigate-compare') {
      navigate('/school-compare')
      return
    }

    const targetId = actionType === 'scroll-gallery' ? 'public-school-gallery' : 'public-data-overview'
    const targetNode = typeof document !== 'undefined' ? document.getElementById(targetId) : null
    if (targetNode) {
      targetNode.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={24} id="public-data-overview">
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col span={24}>
              <div style={sectionTitleStyle}>社会公众端</div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <PublicHeroBanner onAction={handleHeroAction} dataLoadedAt={dataLoadedAt} schoolCount={overview.schoolCount} />
      </Col>

      <Col span={24} id="public-school-gallery">
        <UniversitySlider />
      </Col>

      <Col xs={24} md={12}>
        <Card style={panelStyle}>
          <Statistic
            title="样本覆盖高校数"
            value={overview.schoolCount}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>
      <Col xs={24} md={12}>
        <Card style={panelStyle}>
          <Statistic
            title="公开样本平均薪资"
            value={overview.avgSalary}
            suffix="元"
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>

      <Col xs={24} xl={14}>
        <Card title={<span style={sectionTitleStyle}>薪资最高的前十个专业</span>} style={panelStyle}>
          {topMajors.length ? (
            <ReactECharts option={buildPublicMajorBarOption(topMajors)} style={{ height: 420 }} />
          ) : (
            <Empty description="暂无公开专业样本" />
          )}
        </Card>
      </Col>

      <Col xs={24} xl={10}>
        <Card title={<span style={sectionTitleStyle}>高薪专业 Top10 榜单</span>} style={panelStyle}>
          {topMajors.length ? (
            <List
              dataSource={topMajors}
              renderItem={(item, index) => (
                <List.Item style={{ paddingInline: 0 }}>
                  <div style={{ display: 'flex', width: '100%', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                    <div>
                      <div style={{ color: designTokens.textPrimary, fontWeight: 600 }}>
                        {index + 1}. {item.major_name}
                      </div>
                      <div style={{ color: designTokens.textMuted, fontSize: 12, marginTop: 4 }}>
                        样本量：{formatNumber(item.sample_count, 0)}
                      </div>
                    </div>
                    <div style={{ color: designTokens.accent, fontWeight: 700 }}>
                      {formatNumber(item.avg_salary, 0)} 元
                    </div>
                  </div>
                </List.Item>
              )}
            />
          ) : (
            <Empty description="暂无公开专业样本" />
          )}
        </Card>
      </Col>
    </Row>
  )
}

function PublicSchoolCompare({ employmentData = [], dataLoadedAt = '' }) {
  const [schoolComparison, setSchoolComparison] = useState([])

  useEffect(() => {
    let alive = true
    fetchPublicSchoolComparison()
      .then((payload) => {
        if (alive) setSchoolComparison(normalizeSchoolComparisonItems(payload))
      })
      .catch(() => {
        if (alive) setSchoolComparison([])
      })
    return () => {
      alive = false
    }
  }, [employmentData])

  if (!schoolComparison.length) {
    return (
      <Card style={panelStyle}>
        <Empty description="暂无院校对比基础数据" />
      </Card>
    )
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <SchoolMapExplorer employmentData={employmentData} schoolData={schoolComparison} roleMode="public" />
      </Col>
      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>院校对比</span>}
          extra={<span style={{ color: designTokens.textMuted }}>{dataLoadedAt || '当前会话未记录'}</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildSchoolCompareOption(schoolComparison)} style={{ height: 460 }} />
        </Card>
      </Col>
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>院校专业列表</span>} style={panelStyle}>
          <List
            dataSource={schoolComparison}
            renderItem={(item) => {
              return (
                <List.Item style={{ paddingInline: 0 }}>
                  <Row gutter={[12, 8]} style={{ width: '100%' }}>
                    <Col xs={24} md={6}><strong>{item.school_name}</strong></Col>
                    <Col xs={24} md={6}>专业：{getDisplayMajorName(item)}</Col>
                    <Col xs={12} md={4}>就业样本数：{formatNumber(item.employment_sample_count || 0, 0)}</Col>
                    <Col xs={12} md={4}>平均薪资：{formatNumber(item.avg_salary || 0, 0)} 元</Col>
                    <Col xs={12} md={4}>高质量就业率：{(Number(item.high_quality_employment_rate || 0) * 100).toFixed(1)}%</Col>
                  </Row>
                </List.Item>
              )
            }}
          />
        </Card>
      </Col>
    </Row>
  )
}

export default function PublicWorkspace({ employmentData = [], publicSalaryRankingData = [], dataLoadedAt = '' }) {
  const location = useLocation()

  if (location.pathname === '/school-compare') {
    return <PublicSchoolCompare employmentData={employmentData} dataLoadedAt={dataLoadedAt} />
  }

  return (
    <PublicHome
      employmentData={employmentData}
      publicSalaryRankingData={publicSalaryRankingData}
      dataLoadedAt={dataLoadedAt}
    />
  )
}

