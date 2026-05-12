import { Card, Col, Row, Statistic, Table, Tag } from 'antd'
import { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { formatNumber, getHotDemandForecastRows } from '../utils/dataAdapter'
import {
  axisLabelStyle,
  axisLineStyle,
  chartPalette,
  darkTooltip,
  designTokens,
  legendTextStyle,
  panelStyle,
  sectionTitleStyle,
  splitLineStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

function buildForecastModel(rows = [], visibleLimit = 6) {
  const months = [...new Set(rows.map((item) => item.forecast_month).filter(Boolean))].sort()
  const tracks = new Map()
  rows.forEach((item) => {
    const jobCategory = item.job_category_name || item.job_category
    const track = item.track || `${item.major_name} / ${jobCategory}`
    if (!tracks.has(track)) {
      tracks.set(track, {
        track,
        rank: Number(item.track_rank || 999),
        major_name: item.major_name,
        job_category: jobCategory,
        industry_name: item.industry_name,
      })
    }
  })
  const trackList = [...tracks.values()].sort((a, b) => a.rank - b.rank).slice(0, visibleLimit)
  const series = trackList.map((track, index) => ({
    name: track.track,
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 7,
    data: months.map((month) => {
      const matched = rows.find((item) => (item.track || `${item.major_name} / ${item.job_category_name || item.job_category}`) === track.track && item.forecast_month === month)
      return matched && matched.predicted_demand_count !== null && matched.predicted_demand_count !== undefined
        ? Number(matched.predicted_demand_count)
        : null
    }),
    lineStyle: { width: 2.5, color: chartPalette[index % chartPalette.length] },
    itemStyle: { color: chartPalette[index % chartPalette.length] },
  }))
  const values = series.flatMap((item) => item.data).filter((value) => Number.isFinite(value))
  return {
    months,
    trackList,
    series,
    max: values.length ? Math.ceil(Math.max(...values) * 1.2) : 100,
    avg: values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0,
    highMajorCount: new Set(rows.filter((item) => item.demand_level === '高需求' || Number(item.predicted_demand_count || 0) >= 80).map((item) => item.major_name)).size,
    topJobCategory: rows.reduce((best, item) => Number(item.predicted_demand_count || 0) > Number(best.predicted_demand_count || 0) ? item : best, {}),
  }
}

function buildOption(model) {
  const shortLegend = (name = '') => (String(name).length > 16 ? `${String(name).slice(0, 16)}...` : name)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params = []) {
        const month = params[0]?.axisValue || '-'
        const visible = params.filter((item) => item.value !== null && item.value !== undefined && item.value !== '-')
        return [month, ...visible.map((item) => `${item.marker}${item.seriesName}: ${formatNumber(item.value, 0)} 人`)].join('<br/>')
      },
    },
    legend: { top: 8, type: 'scroll', textStyle: legendTextStyle, formatter: shortLegend },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '20%', containLabel: true },
    xAxis: { type: 'category', name: '月份', data: model.months, axisLabel: axisLabelStyle, axisLine: axisLineStyle },
    yAxis: {
      type: 'value',
      name: '岗位需求人数/人',
      min: 0,
      max: model.max,
      axisLabel: axisLabelStyle,
      splitLine: splitLineStyle,
    },
    series: model.series,
  }
}

export default function DemandForecast({
  forecastData = [],
  forecastEvalData = {},
  supplyDemandGapData = [],
  jobSkillsHeatmapData = [],
  dataLoadedAt = '',
  roleMode = 'school',
  loading,
  error,
}) {
  const displayLimit = roleMode === 'gov' ? 8 : 6
  const hotForecastRows = useMemo(() => getHotDemandForecastRows(forecastData, displayLimit), [forecastData, displayLimit])
  const model = useMemo(() => buildForecastModel(hotForecastRows, displayLimit), [hotForecastRows, displayLimit])
  const metrics = Array.isArray(forecastEvalData?.metrics) ? forecastEvalData.metrics : []
  const mape = Number(metrics.find((item) => item.metric_name === 'MAPE')?.metric_value || 0)
  const topSkills = [...jobSkillsHeatmapData].sort((a, b) => Number(b.skill_count || 0) - Number(a.skill_count || 0)).slice(0, 8)
  const gapRows = [...supplyDemandGapData].slice(0, 6)

  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>
  if (error && !forecastData.length) return <div style={{ color: designTokens.danger }}>{error}</div>

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <div style={sectionTitleStyle}>岗位需求人数预测</div>
          <div style={{ marginTop: 12 }}>
            {model.trackList.slice(0, displayLimit).map((item) => (
              <Tag key={item.track} color="blue">{item.major_name} / {item.job_category}</Tag>
            ))}
          </div>
        </Card>
      </Col>

      <Col xs={24} md={6}><Card style={panelStyle}><Statistic title="预测高需求专业数" value={model.highMajorCount} suffix="个" styles={{ title: statTitleStyle, content: statValuePrimary }} /></Card></Col>
      <Col xs={24} md={6}><Card style={panelStyle}><Statistic title="最高需求岗位类别" value={model.topJobCategory.job_category || '-'} styles={{ title: statTitleStyle, content: statValueBlue }} /></Card></Col>
      <Col xs={24} md={6}><Card style={panelStyle}><Statistic title="平均预测需求人数" value={model.avg} precision={0} suffix="人" styles={{ title: statTitleStyle, content: statValueCyan }} /></Card></Col>
      <Col xs={24} md={6}><Card style={panelStyle}><Statistic title="模型 MAPE" value={mape} precision={2} suffix="%" styles={{ title: statTitleStyle, content: statValuePurple }} /></Card></Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>未来 12 个月岗位需求人数预测</span>} style={panelStyle}>
          <ReactECharts option={buildOption(model)} style={{ height: 430 }} />
          <div style={{ color: designTokens.textMuted, marginTop: 8 }}>数据更新时间：{dataLoadedAt || '当前会话'}</div>
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>预测明细</span>} style={panelStyle}>
          <Table
            rowKey={(row) => `${row.track}-${row.forecast_month}`}
            dataSource={hotForecastRows.slice(0, displayLimit * 12)}
            pagination={{ pageSize: 10 }}
            columns={[
              { title: '专业', dataIndex: 'major_name' },
              { title: '岗位类别', dataIndex: 'job_category' },
              { title: '行业', dataIndex: 'industry_name' },
              { title: '预测月份', dataIndex: 'forecast_month' },
              { title: '预测需求人数', dataIndex: 'predicted_demand_count', render: (value) => `${formatNumber(value, 0)} 人` },
              { title: '需求等级', dataIndex: 'demand_level', render: (value) => <Tag color={value === '高需求' ? 'red' : value === '中需求' ? 'gold' : 'blue'}>{value}</Tag> },
              { title: '增长率', dataIndex: 'demand_growth_rate', render: (value) => `${(Number(value || 0) * 100).toFixed(1)}%` },
            ]}
          />
        </Card>
      </Col>

      <Col xs={24} xl={12}>
        <Card title={<span style={sectionTitleStyle}>专业供需信号</span>} style={panelStyle}>
          <Table
            rowKey="major_name"
            dataSource={gapRows}
            pagination={false}
            columns={[
              { title: '专业', dataIndex: 'major_name' },
              { title: '需求人数', dataIndex: 'demand_count', render: (value) => formatNumber(value, 0) },
              { title: '缺口等级', dataIndex: 'gap_level' },
            ]}
          />
        </Card>
      </Col>
      <Col xs={24} xl={12}>
        <Card title={<span style={sectionTitleStyle}>技能需求榜</span>} style={panelStyle}>
          {topSkills.map((item) => <Tag key={`${item.major_name}-${item.skill_name}`} color="cyan" style={{ marginBottom: 8 }}>{item.skill_name} {formatNumber(item.skill_count, 0)}</Tag>)}
        </Card>
      </Col>
    </Row>
  )
}
