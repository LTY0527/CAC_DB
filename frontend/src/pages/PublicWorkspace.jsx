import { Card, Col, Empty, List, Row, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import { useLocation } from 'react-router-dom'
import {
  formatNumber,
  getPublicOverview,
  getPublicSchoolComparison,
  getPublicTopMajors,
} from '../utils/dataAdapter'
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
        return `${item.major_name || '-'}<br/>平均薪资：${formatNumber(item.avg_salary, 0)} 元<br/>样本规模：${formatNumber(item.sample_count, 0)}`
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
  const labels = data.map((item) => `${item.school_name}\n${item.major_name}`)
  const salaryValues = data.map((item) => Number(item.avg_salary || 0))
  const sampleValues = data.map((item) => Number(item.sample_count || 0))
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
          `<strong>${item.school_name || '-'}</strong>`,
          `专业：${item.major_name || '-'}`,
          `平均薪资：${formatNumber(item.avg_salary, 0)} 元`,
          `样本规模：${formatNumber(item.sample_count, 0)}`,
          `先导产业占比：${Number(item.strategic_ratio || 0).toFixed(1)}%`,
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

function PublicHome({ employmentData = [], dataLoadedAt = '' }) {
  const overview = getPublicOverview(employmentData)
  const topMajors = getPublicTopMajors(employmentData)
  const hasOverview = overview.schoolCount > 0 && overview.avgSalary > 0

  if (!hasOverview) {
    return <PublicEmptyState dataLoadedAt={dataLoadedAt} />
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} xl={16}>
              <div style={sectionTitleStyle}>社会公众端</div>
            </Col>
            <Col xs={24} xl={8}>
              <div style={metaLabelStyle}>页面载入时间</div>
              <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
            </Col>
          </Row>
        </Card>
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
                        样本量 {formatNumber(item.sample_count, 0)}
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
  const schoolComparison = getPublicSchoolComparison(employmentData)

  if (!schoolComparison.length) {
    return <PublicEmptyState dataLoadedAt={dataLoadedAt} />
  }

  return (
    <Card title={<span style={sectionTitleStyle}>院校对比</span>} extra={<span style={{ color: designTokens.textMuted }}>{dataLoadedAt || '当前会话未记录'}</span>} style={panelStyle}>
      <ReactECharts option={buildSchoolCompareOption(schoolComparison)} style={{ height: 460 }} />
    </Card>
  )
}

export default function PublicWorkspace({ employmentData = [], dataLoadedAt = '' }) {
  const location = useLocation()

  if (location.pathname === '/school-compare') {
    return <PublicSchoolCompare employmentData={employmentData} dataLoadedAt={dataLoadedAt} />
  }

  return <PublicHome employmentData={employmentData} dataLoadedAt={dataLoadedAt} />
}
