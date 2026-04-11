import { useMemo, useState } from 'react'
import { Button, Card, Empty, Input, Select, Space, Spin } from 'antd'
import { buildReportSummary } from '../utils/dataAdapter'
import { generateReport } from '../services/dataService'
import {
  designTokens,
  inputStyle,
  panelStyle,
  primaryButtonStyle,
  sectionTitleStyle,
} from '../utils/uiTheme'

const { TextArea } = Input

export default function AIReport({
  employmentData = [],
  forecastData = [],
  enrollmentData = [],
  rulesData = [],
  recommendationData = [],
  loading,
  error,
}) {
  const [report, setReport] = useState('')
  const [reportLoading, setReportLoading] = useState(false)
  const [promptText, setPromptText] = useState(
    '请基于动态监测、需求预测、招生匹配、培养优化、就业推荐五个模块，生成面向高校管理者的分析专报。'
  )
  const [reportLength, setReportLength] = useState('short')

  const summary = useMemo(
    () =>
      buildReportSummary({
        employmentData,
        forecastData,
        rulesData,
        enrollmentData,
        recommendationData,
      }),
    [employmentData, forecastData, rulesData, enrollmentData, recommendationData]
  )

  if (loading) {
    return <div style={{ color: '#d9eeff' }}>平台数据加载中...</div>
  }

  const hasSummaryData =
    Array.isArray(employmentData) && employmentData.length > 0 ||
    Array.isArray(forecastData) && forecastData.length > 0 ||
    Array.isArray(enrollmentData) && enrollmentData.length > 0 ||
    Array.isArray(rulesData) && rulesData.length > 0 ||
    Array.isArray(recommendationData) && recommendationData.length > 0

  const reportIntroStyle = {
    color: designTokens.textSecondary,
    marginBottom: 12,
    fontSize: 13,
    lineHeight: 1.8,
  }

  const reportTextStyle = {
    whiteSpace: 'pre-wrap',
    fontFamily: 'inherit',
    lineHeight: 1.9,
    color: designTokens.textPrimary,
    minHeight: 260,
    margin: 0,
  }

  const handleGenerate = async () => {
    try {
      setReportLoading(true)
      setReport('正在生成分析专报，请稍候...')

      const payload = {
        prompt: promptText,
        currentPage: 'report',
        reportType: 'management',
        reportLength,
        modules: ['employment', 'forecast', 'enrollment', 'rules', 'recommendation'],
        summary,
        chartData: {
          salaryForecast: summary?.salaryForecast || {},
          topRules: summary?.topRules || [],
          enrollmentSample: summary?.enrollmentSample || [],
          recommendationSample: summary?.recommendationSample || [],
        },
        filters: {
          region: '上海',
          version: 'v2-json-driven',
        },
      }

      const res = await generateReport(payload)

      if (res.data?.success) {
        setReport(res.data.report || '专报已生成，但返回内容为空。')
      } else {
        setReport('专报生成失败，请稍后重试。')
      }
    } catch (err) {
      console.error('生成专报失败：', err)
      setReport(
        `专报生成失败：${err?.response?.data?.message || err.message || '未知错误'}`
      )
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card
        title={<span style={sectionTitleStyle}>报告生成条件</span>}
        bordered={false}
        style={panelStyle}
      >
        <TextArea
          rows={6}
          value={promptText}
          onChange={(e) => setPromptText(e.target.value)}
          style={inputStyle}
        />

        <div style={{ marginTop: 16, marginBottom: 16 }}>
          <Select
            value={reportLength}
            onChange={setReportLength}
            style={{ width: 180 }}
            options={[
              { value: 'short', label: '精简版' },
              { value: 'standard', label: '标准版' },
              { value: 'long', label: '详细版' },
              { value: 'bullet', label: '汇报版' },
            ]}
          />
        </div>

        <Button
          type="primary"
          onClick={handleGenerate}
          loading={reportLoading}
          style={{ marginTop: 16, ...primaryButtonStyle }}
          disabled={!hasSummaryData}
        >
          生成分析专报
        </Button>
        {!hasSummaryData ? (
          <div style={{ marginTop: 12, color: 'rgba(210,225,245,0.68)', fontSize: 13 }}>
            当前暂无可用于生成专报的基础数据，请先确认平台数据链路是否已成功加载。
          </div>
        ) : null}
      </Card>

      <Card
        title={<span style={sectionTitleStyle}>专报内容</span>}
        bordered={false}
        style={panelStyle}
      >
        <div
          style={reportIntroStyle}
        >
          以下内容由系统基于当前平台数据与分析摘要自动生成，可作为管理研判与汇报参考。
        </div>

        {reportLoading ? (
          <div
            style={{
              minHeight: 260,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '32px 0',
            }}
          >
            <Spin size="large" />
            <div
              style={{
                marginTop: 16,
                color: designTokens.textPrimary,
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              正在生成分析专报，请稍候...
            </div>
          </div>
        ) : report ? (
          <pre style={reportTextStyle}>
            {report}
          </pre>
        ) : hasSummaryData ? (
          <pre style={reportTextStyle}>
            点击上方按钮后，系统将基于当前可用数据生成分析专报。
          </pre>
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={error ? '当前可用数据不足，分析专报暂不可生成。' : '暂无可用专报数据'}
            style={{ padding: '48px 0' }}
          />
        )}
      </Card>
    </Space>
  )
}
