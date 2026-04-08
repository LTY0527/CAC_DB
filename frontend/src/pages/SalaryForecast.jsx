import { Card, Col, Row, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import { getForecastData } from '../utils/dataAdapter'
import {
  darkTooltip,
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
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
      lineStyle: {
        width: 3,
        color: palette[index % palette.length],
      },
      itemStyle: {
        color: palette[index % palette.length],
      },
    })),
  }
}

export default function SalaryForecast({ forecastData = [], loading, error }) {
  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !forecastData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  const forecast = getForecastData(forecastData)
  const allValues = forecast.series.flatMap((item) => item.data)
  const latest = allValues.length
    ? Math.max(...forecast.series.map((item) => item.data[item.data.length - 1] || 0))
    : 0
  const growth =
    forecast.series?.[0]?.data?.length >= 2 && forecast.series[0].data[0] > 0
      ? Number(
          (((forecast.series[0].data.at(-1) - forecast.series[0].data[0]) / forecast.series[0].data[0]) * 100).toFixed(2)
        )
      : 0

  return (
    <Row gutter={[16, 16]}>
      <Col span={8}>
        <Card style={panelStyle}>
          <Statistic
            title="预测末期"
            value={forecast.months.at(-1) || '-'}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>
      <Col span={8}>
        <Card style={panelStyle}>
          <Statistic
            title="最高预测起薪"
            value={latest}
            prefix="¥"
            precision={0}
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>
      <Col span={8}>
        <Card style={panelStyle}>
          <Statistic
            title="主赛道累计增幅"
            value={growth}
            suffix="%"
            styles={{ title: statTitleStyle, content: statValueCyan }}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>未来 12 个月薪资趋势预测</span>} style={panelStyle}>
          <ReactECharts option={buildSalaryForecastOption(forecast)} style={{ height: 420 }} />
        </Card>
      </Col>
    </Row>
  )
}

export { buildSalaryForecastOption }
