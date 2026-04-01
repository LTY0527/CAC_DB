import { Card, Col, Row, Statistic, Table, Select, Segmented } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
// import employmentData from '../assets/mock/employment_summary.json'
import {
  getEmploymentOverview,
  getEmploymentBarSeries,
  getEmploymentFilterOptions,
  getSankeyData,
} from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValuePrimary,
  statValueBlue,
  statValueCyan,
  statValuePurple,
  darkTooltip,
} from '../utils/uiTheme'

export default function EmploymentMonitor({
  employmentData = [],
  loading,
  error,
}) {
  const safeData = Array.isArray(employmentData) ? employmentData : []
  const overview = getEmploymentOverview(safeData)
  const filterOptions = useMemo(() => getEmploymentFilterOptions(safeData), [safeData])

  const [selectedIndustry, setSelectedIndustry] = useState('全部')
  const [selectedEduLevels, setSelectedEduLevels] = useState([])
  const [metric, setMetric] = useState('avg_salary')

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error) return <div style={{ color: '#ff7875' }}>{error}</div>

  const { majors, series } = getEmploymentBarSeries(safeData, {
    selectedIndustry,
    selectedEduLevels,
    metric,
   })


  const sankeyData = useMemo(() => {
    const filtered = safeData.filter(item => {
      const matchIndustry =
      selectedIndustry === '全部' || item.leading_industry_tag === selectedIndustry
    
      const matchEdu =
      selectedEduLevels.length === 0 || selectedEduLevels.includes(item.edu_level)
   
      return matchIndustry && matchEdu
    })
    return getSankeyData(filtered)
  }, [safeData, selectedIndustry, selectedEduLevels])

  // const eduColorMap = {
  //   博士: '#5b8cff',
  //   硕士: '#30d6ff',
  //   本科: '#b9d532',
  //   专科: '#6f7697',
  // }
  const eduColorMap = {
    博士: '#7db7ff',
    硕士: '#58d5ff',
    本科: '#7ee0c6',
    专科: '#b7c3d7',
  }
 
  const barOption = {
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    ...darkTooltip,
    formatter: params => {
      if (!params || !params.length) return ''

      const major = params[0].axisValueLabel || params[0].name
      const lines = params.map(item => {
        const value =
          metric === 'avg_salary'
            ? Number(item.value || 0).toLocaleString('zh-CN', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })
            : Number(item.value || 0).toLocaleString('zh-CN')

        return `${item.marker}${item.seriesName}　${value}`
      })

      return [major, ...lines].join('<br/>')
    },
  },
  legend: {
    top: 8,
    textStyle: { color: '#b7dfff' }
  },
  grid: { left: '6%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
  xAxis: {
    type: 'category',
    data: majors,
    axisLabel: {
      color: '#b7dfff',
      interval: 0,
      rotate: 0,
    },
    axisLine: { lineStyle: { color: '#3c6e91' } },
  },
  yAxis: {
    type: 'value',
    axisLabel: { color: '#b7dfff' },
    splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
  },
  series: series.map(item => ({
    ...item,
    itemStyle: {
      color: eduColorMap[item.name] || '#5b8cff',
      borderRadius: [6, 6, 0, 0],
    },
  })),
}
  
  const sankeyOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      ...darkTooltip,
    },
    series: [
      {
        type: 'sankey',
        data: sankeyData.nodes,
        links: sankeyData.links,
        emphasis: {
          focus: 'adjacency',
        },
        lineStyle: {
          color: 'gradient',
          curveness: 0.5,
        },
        label: {
          color: '#d9eeff',
        },
      },
    ],
  }

  const columns = [
    {
      title: <span style={{ color: '#d9eeff' }}>专业</span>,
      dataIndex: 'major_name',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>学历</span>,
      dataIndex: 'edu_level',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>产业方向</span>,
      dataIndex: 'leading_industry_tag',
    },
    {
      title: <span style={{ color: '#d9eeff' }}>平均起薪</span>,
      dataIndex: 'avg_salary',
      render: (v) => `¥${Number(v).toFixed(2)}`,
    },
    {
      title: <span style={{ color: '#d9eeff' }}>入职人数</span>,
      dataIndex: 'emp_count',
    },
  ]

   return (
    <Row gutter={[16, 16]}>
      <Col span={6}>
    <Card style={panelStyle}>
      <Statistic
      title="总入职人数"
            value={overview.totalEmpCount}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
      />
    </Card>
  </Col>

  <Col span={6}>
    <Card style={panelStyle}>
      <Statistic
      title="加权平均起薪"
      value={Number(overview.avgSalaryWeighted.toFixed(2))}
      prefix="¥"
      styles={{ title: statTitleStyle, content: statValueBlue }}
      />
    </Card>
  </Col>

  <Col span={6}>
    <Card style={panelStyle}>
      <Statistic
      title="三大先导人数"
       value={overview.leadEmpCount}
       styles={{ title: statTitleStyle, content: statValueCyan }}
       />
    </Card>
  </Col>

  <Col span={6}>
    <Card style={panelStyle}>
      <Statistic
      title="覆盖专业数"
      value={overview.majorCount}
      styles={{ title: statTitleStyle, content: statValuePurple }}
      />
    </Card>
  </Col>

  <Col span={24}>
    <Card
      title={<span style={sectionTitleStyle}>专业 × 学历对比分析</span>}
      style={panelStyle}
    >
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col>
          <Select
            value={selectedIndustry}
            onChange={setSelectedIndustry}
            style={{ width: 160 }}
            options={[
              { label: '全部产业', value: '全部' },
              ...filterOptions.industries.map(item => ({ label: item, value: item })),
            ]}
          />
        </Col>

        <Col>
          <Select
            mode="multiple"
            allowClear
            placeholder="选择学历"
            value={selectedEduLevels}
            onChange={setSelectedEduLevels}
            style={{ width: 220 }}
            options={filterOptions.eduLevels.map(item => ({
              label: item,
              value: item,
            }))}
          />
        </Col>

        <Col>
          <Segmented
            value={metric}
            onChange={setMetric}
            options={[
              { label: '平均起薪', value: 'avg_salary' },
              { label: '入职人数', value: 'emp_count' },
            ]}
          />
        </Col>
      </Row>

        <ReactECharts
          key={`${selectedIndustry}-${selectedEduLevels.join(',')}-${metric}`}
          option={barOption}
          notMerge={true}
          lazyUpdate={true}
          style={{ height: 420 }}
        />
    </Card>
  </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>专业 → 学历 → 产业分流图</span>}
          style={panelStyle}
        >
         <ReactECharts option={sankeyOption} style={{ height: 480 }} />
        </Card>
      </Col>
      
      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>原始数据预览</span>} style={panelStyle}>
          <Table
            rowKey={(record, index) => `${record.major_name}-${record.edu_level}-${index}`}
            columns={columns}
            dataSource={safeData.slice(0, 12)}
            pagination={false}
          />
        </Card>
      </Col>
    </Row>
  )
}