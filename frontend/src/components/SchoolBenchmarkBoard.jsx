import { useEffect, useMemo, useState } from 'react'
import {
  Card,
  Col,
  Empty,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
} from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  fetchGovSchoolBenchmarkMajor,
  fetchGovSchoolBenchmarkOverview,
} from '../services/dataService'
import { formatNumber } from '../utils/dataAdapter'
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

function buildSchoolOverviewOption(rows = []) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const salary = params?.find((item) => item.seriesName === '平均薪资')
        const rate = params?.find((item) => item.seriesName === '就业率')
        const strategic = params?.find((item) => item.seriesName === '高质量就业占比')
        return [
          params?.[0]?.axisValue || '',
          salary ? `平均薪资：${formatNumber(salary.value, 0)} 元` : '',
          rate ? `就业率：${Number(rate.value || 0).toFixed(1)}%` : '',
          strategic ? `高质量就业占比：${Number(strategic.value || 0).toFixed(1)}%` : '',
        ]
          .filter(Boolean)
          .join('<br/>')
      },
    },
    legend: { top: 8, textStyle: legendTextStyle },
    grid: { left: '8%', right: '6%', top: '18%', bottom: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((item) => item.school_name),
      axisLabel: { ...axisLabelStyle, interval: 0 },
      axisLine: axisLineStyle,
    },
    yAxis: [
      {
        type: 'value',
        name: '平均薪资',
        axisLabel: {
          ...axisLabelStyle,
          formatter: (value) => `${Math.round(value / 1000)}k`,
        },
        axisLine: axisLineStyle,
        splitLine: splitLineStyle,
      },
      {
        type: 'value',
        name: '比率',
        min: 0,
        max: 100,
        axisLabel: {
          ...axisLabelStyle,
          formatter: '{value}%',
        },
        axisLine: axisLineStyle,
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '平均薪资',
        type: 'bar',
        barWidth: 22,
        data: rows.map((item) => Number(item.avg_salary || 0)),
        itemStyle: { color: chartPalette[0], borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '就业率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: rows.map((item) => Number(item.employment_rate || 0)),
        lineStyle: { width: 2.5, color: chartPalette[2] },
        itemStyle: { color: chartPalette[2] },
      },
      {
        name: '高质量就业占比',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: rows.map((item) => Number(item.strategic_ratio || 0)),
        lineStyle: { width: 2.5, color: chartPalette[3] },
        itemStyle: { color: chartPalette[3] },
      },
    ],
  }
}

function buildMajorBenchmarkOption(rows = [], majorName = '') {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params) {
        const salary = params?.find((item) => item.seriesName === '平均薪资')
        const rate = params?.find((item) => item.seriesName === '就业率')
        return [
          params?.[0]?.axisValue || '',
          majorName ? `专业：${majorName}` : '',
          salary ? `平均薪资：${formatNumber(salary.value, 0)} 元` : '',
          rate ? `就业率：${Number(rate.value || 0).toFixed(1)}%` : '',
        ]
          .filter(Boolean)
          .join('<br/>')
      },
    },
    legend: { top: 8, textStyle: legendTextStyle },
    grid: { left: '8%', right: '6%', top: '18%', bottom: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: rows.map((item) => item.school_name),
      axisLabel: { ...axisLabelStyle, interval: 0 },
      axisLine: axisLineStyle,
    },
    yAxis: [
      {
        type: 'value',
        name: '平均薪资',
        axisLabel: {
          ...axisLabelStyle,
          formatter: (value) => `${Math.round(value / 1000)}k`,
        },
        axisLine: axisLineStyle,
        splitLine: splitLineStyle,
      },
      {
        type: 'value',
        name: '就业率',
        min: 0,
        max: 100,
        axisLabel: {
          ...axisLabelStyle,
          formatter: '{value}%',
        },
        axisLine: axisLineStyle,
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '平均薪资',
        type: 'bar',
        barWidth: 22,
        data: rows.map((item) => Number(item.avg_salary || 0)),
        itemStyle: { color: chartPalette[1], borderRadius: [6, 6, 0, 0] },
      },
      {
        name: '就业率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        data: rows.map((item) => Number(item.employment_rate || 0)),
        lineStyle: { width: 2.5, color: chartPalette[4] },
        itemStyle: { color: chartPalette[4] },
      },
    ],
  }
}

export default function SchoolBenchmarkBoard() {
  const [overview, setOverview] = useState([])
  const [majorOptions, setMajorOptions] = useState([])
  const [majorRows, setMajorRows] = useState([])
  const [selectedSchools, setSelectedSchools] = useState([])
  const [selectedMajor, setSelectedMajor] = useState('')
  const [updatedAt, setUpdatedAt] = useState('')
  const [loading, setLoading] = useState(true)
  const [majorLoading, setMajorLoading] = useState(false)

  useEffect(() => {
    let alive = true

    async function loadOverview() {
      setLoading(true)
      try {
        const payload = await fetchGovSchoolBenchmarkOverview()
        if (!alive) return
        const rows = Array.isArray(payload?.overview) ? payload.overview : []
        const options = Array.isArray(payload?.major_options) ? payload.major_options : []
        setOverview(rows)
        setMajorOptions(options)
        setSelectedSchools(rows.slice(0, 5).map((item) => item.school_name))
        setSelectedMajor(options[0]?.major_name || '')
        setUpdatedAt(payload?.updated_at || '')
      } finally {
        if (alive) setLoading(false)
      }
    }

    loadOverview()

    return () => {
      alive = false
    }
  }, [])

  useEffect(() => {
    let alive = true

    async function loadMajorRows() {
      if (!selectedMajor) {
        setMajorRows([])
        return
      }
      setMajorLoading(true)
      try {
        const payload = await fetchGovSchoolBenchmarkMajor(selectedMajor)
        if (!alive) return
        setMajorRows(Array.isArray(payload?.rows) ? payload.rows : [])
      } finally {
        if (alive) setMajorLoading(false)
      }
    }

    loadMajorRows()

    return () => {
      alive = false
    }
  }, [selectedMajor])

  const selectedSchoolSet = useMemo(() => new Set(selectedSchools), [selectedSchools])
  const visibleOverview = useMemo(() => {
    const baseRows = selectedSchools.length
      ? overview.filter((item) => selectedSchoolSet.has(item.school_name))
      : overview.slice(0, 5)
    return [...baseRows].sort((a, b) => Number(b.avg_salary || 0) - Number(a.avg_salary || 0))
  }, [overview, selectedSchoolSet, selectedSchools.length])

  const visibleMajorRows = useMemo(() => {
    const baseRows = selectedSchools.length
      ? majorRows.filter((item) => selectedSchoolSet.has(item.school_name))
      : majorRows.slice(0, 5)
    return [...baseRows].sort((a, b) => Number(b.avg_salary || 0) - Number(a.avg_salary || 0))
  }, [majorRows, selectedSchoolSet, selectedSchools.length])

  const overviewStats = useMemo(() => {
    if (!visibleOverview.length) {
      return {
        comparedSchoolCount: 0,
        avgEmploymentRate: 0,
        avgSalary: 0,
        totalStudents: 0,
      }
    }
    const total = visibleOverview.length
    return {
      comparedSchoolCount: total,
      avgEmploymentRate: visibleOverview.reduce((sum, item) => sum + Number(item.employment_rate || 0), 0) / total,
      avgSalary: visibleOverview.reduce((sum, item) => sum + Number(item.avg_salary || 0), 0) / total,
      totalStudents: visibleOverview.reduce((sum, item) => sum + Number(item.student_count || 0), 0),
    }
  }, [visibleOverview])

  const schoolOptions = overview.map((item) => ({
    label: item.school_name,
    value: item.school_name,
  }))

  const majorSelectOptions = majorOptions.map((item) => ({
    label: `${item.major_name}（覆盖 ${item.school_coverage} 校）`,
    value: item.major_name,
  }))

  const overviewColumns = [
    { title: '学校', dataIndex: 'school_name' },
    { title: '院校层次', dataIndex: 'school_level' },
    { title: '学生样本数', dataIndex: 'student_count', render: (value) => formatNumber(value) },
    { title: '就业率', dataIndex: 'employment_rate', render: (value) => `${Number(value || 0).toFixed(1)}%` },
    { title: '平均薪资', dataIndex: 'avg_salary', render: (value) => `${formatNumber(value, 0)} 元` },
    {
      title: '高质量就业占比',
      dataIndex: 'strategic_ratio',
      render: (value) => `${Number(value || 0).toFixed(1)}%`,
    },
    { title: '热门行业去向', dataIndex: 'top_industry', render: (value) => <Tag>{value || '未标注'}</Tag> },
  ]

  const majorColumns = [
    { title: '学校', dataIndex: 'school_name' },
    { title: '院校层次', dataIndex: 'school_level' },
    { title: '专业样本数', dataIndex: 'student_count', render: (value) => formatNumber(value) },
    { title: '就业率', dataIndex: 'employment_rate', render: (value) => `${Number(value || 0).toFixed(1)}%` },
    { title: '平均薪资', dataIndex: 'avg_salary', render: (value) => `${formatNumber(value, 0)} 元` },
    {
      title: '高质量就业占比',
      dataIndex: 'strategic_ratio',
      render: (value) => `${Number(value || 0).toFixed(1)}%`,
    },
    { title: '热门行业去向', dataIndex: 'top_industry', render: (value) => <Tag>{value || '未标注'}</Tag> },
  ]

  return (
    <Card style={panelStyle}>
      <Space direction="vertical" size={18} style={{ width: '100%' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} xl={16}>
            <div style={sectionTitleStyle}>学校对标分析</div>
            <div style={{ color: designTokens.textSecondary, marginTop: 10 }}>
              从就业率、平均薪资、高质量就业占比和热门行业去向四个维度，对不同高校和同一专业进行横向比较。
            </div>
          </Col>
          <Col xs={24} xl={8}>
            <div style={metaLabelStyle}>对标数据更新时间</div>
            <div style={metaValueStyle}>{updatedAt || '当前会话未记录'}</div>
          </Col>
        </Row>

        {loading ? (
          <div style={{ padding: '36px 0', textAlign: 'center' }}>
            <Spin />
          </div>
        ) : !overview.length ? (
          <Empty description="当前暂无可用的学校对标数据" />
        ) : (
          <Space direction="vertical" size={18} style={{ width: '100%' }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} xl={6}>
                <Card style={panelStyle}>
                  <Statistic title="对标学校数" value={overviewStats.comparedSchoolCount} styles={{ title: statTitleStyle, content: statValuePrimary }} />
                </Card>
              </Col>
              <Col xs={24} sm={12} xl={6}>
                <Card style={panelStyle}>
                  <Statistic title="平均就业率" value={Number(overviewStats.avgEmploymentRate.toFixed(1))} suffix="%" styles={{ title: statTitleStyle, content: statValueBlue }} />
                </Card>
              </Col>
              <Col xs={24} sm={12} xl={6}>
                <Card style={panelStyle}>
                  <Statistic title="平均薪资" value={formatNumber(overviewStats.avgSalary, 0)} suffix="元" styles={{ title: statTitleStyle, content: statValueCyan }} />
                </Card>
              </Col>
              <Col xs={24} sm={12} xl={6}>
                <Card style={panelStyle}>
                  <Statistic title="覆盖学生样本" value={formatNumber(overviewStats.totalStudents)} styles={{ title: statTitleStyle, content: statValuePurple }} />
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]} align="middle">
              <Col xs={24} xl={12}>
                <div style={metaLabelStyle}>对标学校</div>
                <Select
                  mode="multiple"
                  allowClear
                  maxTagCount={4}
                  style={{ width: '100%', marginTop: 8 }}
                  value={selectedSchools}
                  options={schoolOptions}
                  onChange={(values) => setSelectedSchools(values.slice(0, 6))}
                  placeholder="选择参与对标的学校"
                />
              </Col>
              <Col xs={24} xl={12}>
                <div style={metaLabelStyle}>跨校对比专业</div>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  value={selectedMajor || undefined}
                  options={majorSelectOptions}
                  onChange={setSelectedMajor}
                  placeholder="选择需要跨校比较的专业"
                />
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col xs={24} xl={12}>
                <Card title={<span style={sectionTitleStyle}>多学校总体对比</span>} style={panelStyle}>
                  <ReactECharts option={buildSchoolOverviewOption(visibleOverview)} style={{ height: 340 }} />
                </Card>
              </Col>
              <Col xs={24} xl={12}>
                <Card title={<span style={sectionTitleStyle}>同专业跨校对比</span>} style={panelStyle}>
                  {majorLoading ? (
                    <div style={{ padding: '36px 0', textAlign: 'center' }}>
                      <Spin />
                    </div>
                  ) : visibleMajorRows.length ? (
                    <ReactECharts option={buildMajorBenchmarkOption(visibleMajorRows, selectedMajor)} style={{ height: 340 }} />
                  ) : (
                    <Empty description="当前专业暂无足够的跨校对标样本" />
                  )}
                </Card>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col xs={24} xl={12}>
                <Card title={<span style={sectionTitleStyle}>学校总体排名</span>} style={panelStyle}>
                  <Table
                    rowKey={(row) => row.school_name}
                    pagination={false}
                    dataSource={visibleOverview}
                    columns={overviewColumns}
                    size="middle"
                  />
                </Card>
              </Col>
              <Col xs={24} xl={12}>
                <Card title={<span style={sectionTitleStyle}>{selectedMajor ? `${selectedMajor}跨校表现` : '专业跨校表现'}</span>} style={panelStyle}>
                  <Table
                    rowKey={(row) => `${row.school_name}-${row.major_name}`}
                    pagination={false}
                    dataSource={visibleMajorRows}
                    columns={majorColumns}
                    size="middle"
                  />
                </Card>
              </Col>
            </Row>
          </Space>
        )}
      </Space>
    </Card>
  )
}
