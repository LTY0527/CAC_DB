import { useState } from 'react'
import { Card, Input, Button, Space, Spin ,Select } from 'antd'
import { buildReportSummary } from '../utils/dataAdapter'
import { generateReport } from '../services/dataService'
import {
  panelStyle,
  sectionTitleStyle,
  inputStyle,
  primaryButtonStyle,
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

  if (loading) {
    return <div style={{ color: '#d9eeff' }}>平台数据加载中...</div>
  }

  if (error) {
    return <div style={{ color: '#ff7875' }}>{error}</div>
  }

  const summary = buildReportSummary({
    employmentData,
    forecastData,
    rulesData,
    enrollmentData,
    recommendationData,
  })

  const handleGenerate = async () => {
    try {
      setReportLoading(true)
      setReport('正在调用大模型生成分析专报，请稍候...')

      const payload = {
        prompt: promptText,
        currentPage: 'report',
        reportType: 'management',
        reportLength, // 可选值：short, standard, long, bullet
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
        setReport(res.data.report || '报告生成成功，但返回内容为空。')
      } else {
        setReport('报告生成失败，请检查后端返回结果。')
      }
    } catch (err) {
      console.error('生成报告失败：', err)
      setReport(
        `请求后端失败：${err?.response?.data?.message || err.message || '未知错误'
        }`
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
        >
          生成分析专报
        </Button>
      </Card>

      <Card
        title={<span style={sectionTitleStyle}>专报内容</span>}
        bordered={false}
        style={panelStyle}
      >
        <div
        style={{
          color: 'rgba(210,225,245,0.68)',
          marginBottom: 12,
          fontSize: 13,
          lineHeight: 1.8,
        }}
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
              color: '#d9eeff',
              fontSize: 14,
            }}
          >
            正在调用大模型生成分析专报，请稍候...
          </div>
        </div>
      ) : (
        <pre
          style={{
            whiteSpace: 'pre-wrap',
            fontFamily: 'inherit',
            lineHeight: 1.9,
            color: '#d9eeff',
            minHeight: 260,
            margin: 0,
          }}
        >
          {report || '点击上方按钮后，系统将基于当前平台数据自动生成分析专报。'}
        </pre>
      )}
      </Card>
    </Space>
  )
}