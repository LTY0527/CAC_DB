import { Card, Col, Row, Statistic, Alert } from 'antd'
import ReactECharts from 'echarts-for-react'
// import forecastData from '../assets/mock/salary_forecast.json'
import { getForecastData } from '../utils/dataAdapter'
import {
  panelStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValuePrimary,
  statValueBlue,
  statValueCyan,
  darkTooltip,
} from '../utils/uiTheme'

export default function SalaryForecast({
  forecastData = [],
  loading,
  error,
}) {
  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error) return <div style={{ color: '#ff7875' }}>{error}</div>

  const { months, values, updateTime } = getForecastData(forecastData)
  const latest = values[values.length - 1] || 0
  const first = values[0] || 0
  const growth = first ? (((latest - first) / first) * 100).toFixed(2) : 0

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
    },
    grid: { left: '6%', right: '4%', bottom: '10%', top: '14%', containLabel: true },
    xAxis: {
      type: 'category',
      data: months,
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
        name: '预测起薪',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 9,
        lineStyle: {
          width: 3,
          type: 'dashed',
          color: '#34d3ff',
        },
        itemStyle: {
          color: '#34d3ff',
        },
        areaStyle: {
          color: 'rgba(52, 211, 255, 0.10)',
        },
        data: values,
      },
    ],
  }

  return (
    <Row gutter={[16, 16]}>
      <Col span={8}>
        <Card style={panelStyle}>
          <Statistic
            title="最新预测月份"
            value={months[months.length - 1] || '-'}
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>

      <Col span={8}>
        <Card style={panelStyle}>
          <Statistic
            title="预测最高起薪"
            value={latest}
            prefix="¥"
            precision={2}
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>

      <Col span={8}>
        <Card style={panelStyle}>
          <Statistic
            title="三个月累计涨幅"
            value={growth}
            suffix="%"
            styles={{ title: statTitleStyle, content: statValueCyan }}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>未来 3 个月起薪预测</span>} style={panelStyle}>
          <ReactECharts option={option} style={{ height: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Alert
          type="info"
          showIcon
          message="当前页面先采用“纯预测版”"
          description={`目前上传数据只有未来 3 个月预测值，可先完成虚线预测图。若后续补充历史 12 个月均薪表，再升级为“历史实线 + 未来虚线”的正式版本。当前预测数据包含 forecast_month、predicted_salary、update_time。更新时间：${updateTime}`}
        />
      </Col>
    </Row>
  )
}