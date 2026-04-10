import { Card, Col, Empty, Row, Segmented, Statistic, Tag } from 'antd'
import { useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  formatNumber,
  getIndustryForecastData,
  getSalaryForecastEvaluation,
} from '../utils/dataAdapter'
import {
  axisLabelStyle,
  axisLineStyle,
  chartPalette,
  designTokens,
  darkTooltip,
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

const TOP5_VISIBLE_TRACKS = 5
const TOP10_VISIBLE_TRACKS = 10

function buildSalaryForecastOption(forecast) {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      ...darkTooltip,
      formatter(params = []) {
        const month = params[0]?.axisValue || '-'
        const lines = params.map(
          (item) => `${item.marker}${item.seriesName}：${formatNumber(item.value, 0)} 元`
        )
        return [month, ...lines].join('<br/>')
      },
    },
    legend: { top: 10, type: 'scroll', textStyle: legendTextStyle },
    grid: { left: '6%', right: '4%', bottom: '12%', top: '20%', containLabel: true },
    xAxis: {
      type: 'category',
      data: forecast?.months || [],
      axisLabel: axisLabelStyle,
      axisLine: axisLineStyle,
    },
    yAxis: {
      type: 'value',
      min: forecast?.min || 0,
      max: forecast?.max || 20000,
      axisLabel: {
        color: designTokens.textMuted,
        formatter: (value) => `${Math.round(Number(value || 0) / 1000)}k`,
      },
      splitLine: splitLineStyle,
    },
    series: (forecast?.series || []).map((item, index) => ({
      ...item,
      smooth: true,
      connectNulls: false,
      lineStyle: { width: 2.5, color: chartPalette[index % chartPalette.length] },
      itemStyle: { color: chartPalette[index % chartPalette.length] },
    })),
  }
}

export default function SalaryForecast({
  forecastData = [],
  forecastEvalData = {},
  employmentData = [],
  recommendationData = [],
  currentSchool = '',
  roleMode = 'school',
  dataLoadedAt = '',
  loading,
  error,
}) {
  const [visibleTrackCount, setVisibleTrackCount] = useState(TOP10_VISIBLE_TRACKS)

  const forecast = useMemo(
    () =>
      getIndustryForecastData(
        forecastData,
        employmentData,
        recommendationData,
        visibleTrackCount,
        { roleMode, currentSchool }
      ),
    [forecastData, employmentData, recommendationData, visibleTrackCount, roleMode, currentSchool]
  )

  const evaluation = useMemo(
    () => getSalaryForecastEvaluation(forecastEvalData),
    [forecastEvalData]
  )

  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>
  if (error && !forecastData.length) return <div style={{ color: designTokens.danger }}>{error}</div>

  const horizonMonths = forecast.horizonMonths || 0
  const latest = forecast.series.length
    ? Math.max(...forecast.series.map((item) => item.data[item.data.length - 1] || 0))
    : 0
  const displayTags = forecast.trackOptions.slice(0, forecast.visibleTrackCount)
  const primarySeries =
    forecast.series?.[0]?.data?.filter((value) => Number.isFinite(value)) || []
  const growth =
    primarySeries.length >= 2 && primarySeries[0] > 0
      ? Number((((primarySeries.at(-1) - primarySeries[0]) / primarySeries[0]) * 100).toFixed(2))
      : 0
  const chartTitle =
    roleMode === 'gov'
      ? `未来${horizonMonths || '-'}个月热门行业薪资预测`
      : `未来${horizonMonths || '-'}个月热门行业薪资预测`

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} xl={16}>
              <div style={sectionTitleStyle}>需求预测（LSTM）</div>
              <div style={{ marginTop: 14, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {displayTags.map((item) => (
                  <Tag key={item.track} color="blue">
                    {item.track}
                  </Tag>
                ))}
              </div>
            </Col>
            <Col xs={24} xl={8}>
              <div style={metaLabelStyle}>数据载入时间</div>
              <div style={metaValueStyle}>
                {dataLoadedAt || forecast.updateTime || '当前会话未记录'}
              </div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="展示行业数"
            value={forecast.visibleTrackCount}
            suffix="个"
            styles={{ title: statTitleStyle, content: statValuePrimary }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="预测月份数"
            value={horizonMonths}
            suffix="个月"
            styles={{ title: statTitleStyle, content: statValueBlue }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="最高末期薪资"
            value={latest}
            precision={0}
            suffix="元"
            styles={{ title: statTitleStyle, content: statValueCyan }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card style={panelStyle}>
          <Statistic
            title="首条曲线累计变化"
            value={growth}
            suffix="%"
            styles={{ title: statTitleStyle, content: statValuePurple }}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>{chartTitle}</span>}
          extra={
            <Segmented
              options={[
                { label: '聚焦行业 Top 5', value: TOP5_VISIBLE_TRACKS },
                { label: '热门行业 Top 10', value: TOP10_VISIBLE_TRACKS },
              ]}
              value={visibleTrackCount}
              onChange={(value) => setVisibleTrackCount(Number(value))}
            />
          }
          style={panelStyle}
        >
          <div style={{ marginBottom: 12, color: designTokens.textSecondary, lineHeight: 1.8 }}>
            {displayTags.map((item) => (
              <Tag key={item.track} color="blue" style={{ marginBottom: 6 }}>
                {item.track}
              </Tag>
            ))}
          </div>
          {forecast.series.length ? (
            <ReactECharts
              key={`${roleMode}-${visibleTrackCount}`}
              notMerge
              option={buildSalaryForecastOption(forecast)}
              style={{ height: 420 }}
            />
          ) : (
            <Empty description="暂无薪资预测结果" />
          )}
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>模型评估</span>} style={panelStyle}>
          <Row gutter={[12, 12]}>
            <Col span={12}>
              <Statistic
                title="RMSE"
                value={evaluation.rmse}
                precision={0}
                suffix="元"
                styles={{ title: statTitleStyle, content: statValuePrimary }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="MAPE"
                value={evaluation.mape}
                precision={2}
                suffix="%"
                styles={{ title: statTitleStyle, content: statValueBlue }}
              />
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  )
}
