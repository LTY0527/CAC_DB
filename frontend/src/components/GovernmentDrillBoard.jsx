import { useEffect, useState } from 'react'
import {
  Breadcrumb,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
} from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  fetchGovMajorDetail,
  fetchGovSchoolDetail,
} from '../services/dataService'
import { formatNumber, getRegionalWarningTagColor } from '../utils/dataAdapter'
import {
  axisLabelStyle,
  axisLineStyle,
  chartPalette,
  darkTooltip,
  designTokens,
  legendTextStyle,
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

function buildIndustryOption(rows = []) {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    grid: { left: '8%', right: '4%', top: '10%', bottom: '10%', containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
      splitLine: splitLineStyle,
    },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.industry_name),
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
    },
    series: [
      {
        type: 'bar',
        data: rows.map((item) => item.employed_count),
        barWidth: 18,
        itemStyle: {
          color: designTokens.accent,
          borderRadius: [0, 6, 6, 0],
        },
      },
    ],
  }
}

function buildSalaryTrendOption(rows = [], title = '月度薪资走势') {
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', ...darkTooltip },
    legend: {
      top: 8,
      textStyle: legendTextStyle,
      data: [title],
    },
    grid: { left: '8%', right: '4%', top: '18%', bottom: '12%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((item) => item.stat_month),
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
    },
    yAxis: {
      type: 'value',
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
      splitLine: splitLineStyle,
    },
    series: [
      {
        name: title,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { width: 3, color: chartPalette[0] },
        itemStyle: { color: chartPalette[0] },
        data: rows.map((item) => item.avg_salary),
      },
    ],
  }
}

function WarningList({ items = [] }) {
  if (!items.length) {
    return <Empty description="当前层级暂无区域预警" />
  }

  return (
    <Space direction="vertical" size={12} style={{ width: '100%' }}>
      {items.slice(0, 4).map((item, index) => (
        <Card
          key={`${item.warning_title || 'warning'}-${index}`}
          style={{
            ...panelStyle,
            borderColor:
              item.warning_level === '高'
                ? 'rgba(220, 38, 38, 0.24)'
                : item.warning_level === '中'
                  ? 'rgba(217, 119, 6, 0.24)'
                  : designTokens.border,
            boxShadow: 'none',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
            <div style={{ color: designTokens.textPrimary, fontWeight: 700 }}>{item.warning_title}</div>
            <Tag color={getRegionalWarningTagColor(item.warning_level)}>{item.warning_level}风险</Tag>
          </div>
          <div style={{ color: designTokens.textMuted, marginTop: 8, fontSize: 12 }}>
            预警对象：{item.target_name}
          </div>
          <div style={{ color: designTokens.textSecondary, marginTop: 8, lineHeight: 1.75 }}>
            {item.trigger_reason}
          </div>
          <div style={{ color: designTokens.textPrimary, marginTop: 10, fontWeight: 600 }}>{item.metric_value}</div>
          <div style={{ color: designTokens.textSecondary, marginTop: 4 }}>{item.metric_change}</div>
        </Card>
      ))}
    </Space>
  )
}

function renderStats(cards = []) {
  return (
    <Row gutter={[16, 16]}>
      {cards.map((item) => (
        <Col xs={24} sm={12} xl={6} key={item.title}>
          <Card style={panelStyle}>
            <Statistic title={item.title} value={item.value} suffix={item.suffix} styles={{ title: statTitleStyle, content: item.style }} />
          </Card>
        </Col>
      ))}
    </Row>
  )
}

export default function GovernmentDrillBoard({
  schoolName = '',
  majorName = '',
  onBackToCity,
  onSelectMajor,
  onSelectSchool,
}) {
  const [schoolDetail, setSchoolDetail] = useState(null)
  const [majorDetail, setMajorDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true

    async function loadDetail() {
      if (!schoolName) {
        setSchoolDetail(null)
        setMajorDetail(null)
        return
      }

      setLoading(true)
      setError('')

      try {
        const schoolData = await fetchGovSchoolDetail(schoolName)
        if (!alive) return
        setSchoolDetail(schoolData || null)

        if (majorName) {
          const majorData = await fetchGovMajorDetail(schoolName, majorName)
          if (!alive) return
          setMajorDetail(majorData || null)
        } else {
          setMajorDetail(null)
        }
      } catch (err) {
        if (!alive) return
        setError(err?.response?.data?.message || '详情数据加载失败')
      } finally {
        if (alive) setLoading(false)
      }
    }

    loadDetail()

    return () => {
      alive = false
    }
  }, [schoolName, majorName])

  const schoolOverview = schoolDetail?.overview || {}
  const majorOverview = majorDetail?.overview || {}
  const isMajorLevel = Boolean(schoolName && majorName)

  const schoolStatCards = [
    { title: '学校覆盖学生数', value: formatNumber(schoolOverview.student_count), style: statValuePrimary },
    { title: '覆盖专业数', value: formatNumber(schoolOverview.major_count), style: statValueBlue },
    { title: '就业率', value: Number(schoolOverview.employment_rate || 0), suffix: '%', style: statValueCyan },
    { title: '平均薪资', value: formatNumber(schoolOverview.avg_salary, 0), suffix: '元', style: statValuePurple },
  ]

  const majorStatCards = [
    { title: '专业样本规模', value: formatNumber(majorOverview.student_count), style: statValuePrimary },
    { title: '就业人数', value: formatNumber(majorOverview.employed_students), style: statValueBlue },
    { title: '就业率', value: Number(majorOverview.employment_rate || 0), suffix: '%', style: statValueCyan },
    { title: '平均薪资', value: formatNumber(majorOverview.avg_salary, 0), suffix: '元', style: statValuePurple },
  ]

  const majorColumns = [
    {
      title: '专业名称',
      dataIndex: 'major_name',
      render: (value) => <Button type="link" style={{ padding: 0 }} onClick={() => onSelectMajor?.(value)}>{value}</Button>,
    },
    { title: '学科门类', dataIndex: 'discipline_category' },
    { title: '样本规模', dataIndex: 'student_count', render: (value) => formatNumber(value) },
    { title: '就业率', dataIndex: 'employment_rate', render: (value) => `${Number(value || 0).toFixed(1)}%` },
    { title: '平均薪资', dataIndex: 'avg_salary', render: (value) => `${formatNumber(value, 0)} 元` },
    { title: '先导产业占比', dataIndex: 'strategic_ratio', render: (value) => `${Number(value || 0).toFixed(1)}%` },
  ]

  const breadcrumbItems = [
    {
      title: <Button type="link" style={{ padding: 0 }} onClick={onBackToCity}>全市总览</Button>,
    },
    schoolName
      ? {
          title: majorName ? (
            <Button type="link" style={{ padding: 0 }} onClick={() => onSelectSchool?.(schoolName)}>
              {schoolName}
            </Button>
          ) : (
            schoolName
          ),
        }
      : null,
    majorName ? { title: majorName } : null,
  ].filter(Boolean)

  return (
    <Card style={panelStyle}>
      <Space direction="vertical" size={18} style={{ width: '100%' }}>
        <div>
          <Breadcrumb items={breadcrumbItems} />
          <div style={{ ...sectionTitleStyle, marginTop: 12 }}>
            {isMajorLevel ? `${majorName}专业视图` : `${schoolName}学校视图`}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
            <div style={{ color: designTokens.textSecondary }}>
              {isMajorLevel ? '查看专业层的招生、培养、就业和薪资细分信息。' : '查看学校层的学生规模、专业分布、就业与行业流向。'}
            </div>
          </div>
        </div>

        {loading ? (
          <div style={{ padding: '40px 0', textAlign: 'center' }}>
            <Spin />
          </div>
        ) : error ? (
          <Empty description={error} />
        ) : isMajorLevel ? (
          <Space direction="vertical" size={18} style={{ width: '100%' }}>
            {renderStats(majorStatCards)}
            <Row gutter={[16, 16]}>
              <Col xs={24} xl={14}>
                <Card title={<span style={sectionTitleStyle}>专业月度薪资走势</span>} style={panelStyle}>
                  <ReactECharts
                    option={buildSalaryTrendOption(majorDetail?.salary_trend || [], `${majorName}月均薪资`)}
                    style={{ height: 320 }}
                  />
                </Card>
              </Col>
              <Col xs={24} xl={10}>
                <Card title={<span style={sectionTitleStyle}>行业去向分布</span>} style={panelStyle}>
                  <ReactECharts option={buildIndustryOption(majorDetail?.industry_flow || [])} style={{ height: 320 }} />
                </Card>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col xs={24} xl={12}>
                <Card title={<span style={sectionTitleStyle}>招生与匹配信号</span>} style={panelStyle}>
                  <Space direction="vertical" size={14} style={{ width: '100%' }}>
                    <div>
                      <div style={metaLabelStyle}>专业名称</div>
                      <div style={metaValueStyle}>{majorOverview.major_name || '-'}</div>
                    </div>
                    <div>
                      <div style={metaLabelStyle}>学科门类</div>
                      <div style={metaValueStyle}>{majorOverview.discipline_category || '-'}</div>
                    </div>
                    <div>
                      <div style={metaLabelStyle}>招生匹配均分</div>
                      <div style={metaValueStyle}>
                        {Number(majorDetail?.enrollment_hint?.avg_match_score || 0).toFixed(3)}
                      </div>
                    </div>
                    <div>
                      <div style={metaLabelStyle}>匹配样本规模</div>
                      <div style={metaValueStyle}>{formatNumber(majorDetail?.enrollment_hint?.total_sample_size || 0)}</div>
                    </div>
                    <div>
                      <div style={metaLabelStyle}>先导产业占比</div>
                      <div style={metaValueStyle}>{Number(majorOverview.strategic_ratio || 0).toFixed(1)}%</div>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col xs={24} xl={12}>
                <Card title={<span style={sectionTitleStyle}>专业风险提示</span>} style={panelStyle}>
                  <WarningList items={majorDetail?.warnings || []} />
                </Card>
              </Col>
            </Row>
          </Space>
        ) : (
          <Space direction="vertical" size={18} style={{ width: '100%' }}>
            {renderStats(schoolStatCards)}
            <Row gutter={[16, 16]}>
              <Col xs={24} xl={14}>
                <Card title={<span style={sectionTitleStyle}>专业分布与就业表现</span>} style={panelStyle}>
                  <Table
                    rowKey={(row) => `${row.major_name}-${row.discipline_category}`}
                    columns={majorColumns}
                    dataSource={schoolDetail?.major_breakdown || []}
                    pagination={{ pageSize: 8 }}
                    onRow={(record) => ({
                      onClick: () => onSelectMajor?.(record.major_name),
                      style: { cursor: 'pointer' },
                    })}
                  />
                </Card>
              </Col>
              <Col xs={24} xl={10}>
                <Card title={<span style={sectionTitleStyle}>热门行业流向</span>} style={panelStyle}>
                  <ReactECharts option={buildIndustryOption(schoolDetail?.industry_flow || [])} style={{ height: 360 }} />
                </Card>
              </Col>
            </Row>
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <Card title={<span style={sectionTitleStyle}>学校层预警聚焦</span>} style={panelStyle}>
                  <WarningList items={schoolDetail?.warnings || []} />
                </Card>
              </Col>
            </Row>
          </Space>
        )}
      </Space>
    </Card>
  )
}
