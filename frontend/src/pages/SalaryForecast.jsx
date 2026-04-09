import { Card, Col, Row, Statistic, Table } from 'antd'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getForecastData,
  getSalaryBacktestChartData,
  getSalaryForecastEvaluation,
} from '../utils/dataAdapter'
import {
  algorithmTextStyle,
  darkTooltip,
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  riskTextStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

function buildSalaryForecastOption(forecast) {
  const palette = ['#39c4ff', '#8b6cff', '#67e8f9']
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    legend: {
      top: 10,
      textStyle: { color: '#b7dfff' },
    },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: forecast?.months || [],
      axisLabel: { color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      min: forecast?.min || 0,
      max: forecast?.max || 20000,
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: (forecast?.series || []).map((item, index) => ({
      ...item,
      smooth: true,
      lineStyle: { width: 3, color: palette[index % palette.length] },
      itemStyle: { color: palette[index % palette.length] },
    })),
  }
}

function buildBacktestOption(chartData) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    legend: {
      top: 8,
      textStyle: { color: '#b7dfff' },
    },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      data: chartData.months,
      axisLabel: { color: '#b7dfff' },
      axisLine: { lineStyle: { color: '#3c6e91' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#b7dfff' },
      splitLine: { lineStyle: { color: 'rgba(80,130,170,0.18)' } },
    },
    series: [
      {
        name: '真实值',
        type: 'line',
        smooth: true,
        data: chartData.actual,
        lineStyle: { width: 3, color: '#67e8f9' },
        itemStyle: { color: '#67e8f9' },
      },
      {
        name: '预测值',
        type: 'line',
        smooth: true,
        data: chartData.predicted,
        lineStyle: { width: 3, color: '#f7c948' },
        itemStyle: { color: '#f7c948' },
      },
    ],
  }
}

export default function SalaryForecast({
  forecastData = [],
  forecastEvalData = {},
  dataLoadedAt = '',
  loading,
  error,
}) {
  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !forecastData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  const forecast = getForecastData(forecastData)
  const evaluation = getSalaryForecastEvaluation(forecastEvalData)
  const backtestChart = getSalaryBacktestChartData(forecastEvalData)
  const horizonMonths = forecast.horizonMonths || forecast.months.length || 0
  const allValues = forecast.series.flatMap((item) => item.data)
  const latest = allValues.length ? Math.max(...forecast.series.map((item) => item.data[item.data.length - 1] || 0)) : 0
  const growth =
    forecast.series?.[0]?.data?.length >= 2 && forecast.series[0].data[0] > 0
      ? Number((((forecast.series[0].data.at(-1) - forecast.series[0].data[0]) / forecast.series[0].data[0]) * 100).toFixed(2))
      : 0

  const metricColumns = [
    { title: '指标', dataIndex: 'metric_label' },
    {
      title: '数值',
      dataIndex: 'metric_value',
      render: (value, record) => `${Number(value || 0).toFixed(record.metric_name === 'MAPE' ? 2 : 0)}${record.metric_unit || ''}`,
    },
    { title: '说明', dataIndex: 'metric_desc' },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <div style={sectionTitleStyle}>需求预测（LSTM）</div>
              <div style={{ color: '#cfe9ff', lineHeight: 1.9, marginTop: 10 }}>
                业务价值：通过未来薪资趋势变化判断就业需求强弱，为专业规模调整、课程资源配置和校企合作方向提供前瞻信号。
              </div>
            </Col>
            <Col xs={24} xl={10}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={metaLabelStyle}>模型更新时间</div>
                  <div style={metaValueStyle}>{forecast.updateTime || '未返回'}</div>
                </Col>
                <Col span={12}>
                  <div style={metaLabelStyle}>页面载入时间</div>
                  <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
                </Col>
                <Col span={24}>
                  <div style={algorithmTextStyle}>算法说明：使用时间序列 LSTM，对历史月度薪资进行训练，并按时间顺序划分训练集与测试集做回测。</div>
                </Col>
                <Col span={24}>
                  <div style={riskTextStyle}>风险提示：当前预测更适合展示趋势和方向，不建议直接作为单月预算值或刚性指标使用。</div>
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic title="预测末期" value={forecast.months.at(-1) || '-'} styles={{ title: statTitleStyle, content: statValuePrimary }} />
        </Card>
      </Col>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic title="最高预测薪资" value={latest} precision={0} suffix="元" styles={{ title: statTitleStyle, content: statValueBlue }} />
        </Card>
      </Col>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic title="累计变化" value={growth} suffix="%" styles={{ title: statTitleStyle, content: statValueCyan }} />
        </Card>
      </Col>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic title="测试窗口数" value={evaluation.testWindowSize || 0} styles={{ title: statTitleStyle, content: statValuePurple }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>未来 {horizonMonths || '-'} 个月薪资趋势预测</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>关键说明：横轴即模型输出的真实预测月份，不是静态样例。</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildSalaryForecastOption(forecast)} style={{ height: 380 }} />
        </Card>
      </Col>

      <Col xs={24} xl={10}>
        <Card title={<span style={sectionTitleStyle}>模型评估</span>} style={panelStyle}>
          <Row gutter={[12, 12]}>
            <Col span={8}>
              <Statistic title="MAE" value={evaluation.mae} precision={0} suffix="元" styles={{ title: statTitleStyle, content: statValuePrimary }} />
            </Col>
            <Col span={8}>
              <Statistic title="RMSE" value={evaluation.rmse} precision={0} suffix="元" styles={{ title: statTitleStyle, content: statValueBlue }} />
            </Col>
            <Col span={8}>
              <Statistic title="MAPE" value={evaluation.mape} precision={2} suffix="%" styles={{ title: statTitleStyle, content: statValueCyan }} />
            </Col>
          </Row>
          <div style={{ color: '#8fb7d8', marginTop: 16, lineHeight: 1.8 }}>
            指标说明：MAE 反映平均误差，RMSE 对大误差更敏感，MAPE 用于描述相对误差水平。
            当前训练窗口数 {formatNumber(evaluation.trainWindowSize)}，测试窗口数 {formatNumber(evaluation.testWindowSize)}。
          </div>
          <div style={{ marginTop: 16 }}>
            <Table rowKey="key" size="small" pagination={false} columns={metricColumns} dataSource={evaluation.metrics} />
          </div>
        </Card>
      </Col>

      <Col xs={24} xl={14}>
        <Card
          title={<span style={sectionTitleStyle}>真实值 vs 预测值对比</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>用于答辩时直接说明“模型不是黑盒输出，已经做了测试集回测”。</span>}
          style={panelStyle}
        >
          <ReactECharts option={buildBacktestOption(backtestChart)} style={{ height: 320 }} />
        </Card>
      </Col>
    </Row>
  )
}

export { buildSalaryForecastOption }
