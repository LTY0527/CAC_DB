import { useState } from 'react'
import { Button, Card, Empty, Space, Spin } from 'antd'
import { FileTextOutlined, ReloadOutlined } from '@ant-design/icons'
import { fetchAutoReport } from '../services/dataService'
import { designTokens, panelStyle, primaryButtonStyle, sectionTitleStyle } from '../utils/uiTheme'

export default function AIReportFormal({ loading }) {
  const [report, setReport] = useState('')
  const [reportLoading, setReportLoading] = useState(false)

  const handleGenerate = async () => {
    setReportLoading(true)
    try {
      const data = await fetchAutoReport()
      setReport(data.report || '')
    } catch (error) {
      setReport(`分析专报生成失败：${error?.response?.data?.message || error.message}`)
    } finally {
      setReportLoading(false)
    }
  }

  if (loading) return <div style={{ color: designTokens.textSecondary }}>数据加载中...</div>

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Card style={panelStyle}>
        <div style={sectionTitleStyle}>分析专报自动生成</div>
        <Button
          type="primary"
          icon={<FileTextOutlined />}
          onClick={handleGenerate}
          loading={reportLoading}
          style={{ marginTop: 16, ...primaryButtonStyle }}
        >
          生成分析专报
        </Button>
        <Button
          icon={<ReloadOutlined />}
          onClick={handleGenerate}
          disabled={reportLoading}
          style={{ marginTop: 16, marginLeft: 12 }}
        >
          刷新
        </Button>
      </Card>

      <Card title={<span style={sectionTitleStyle}>专报内容</span>} style={panelStyle}>
        {reportLoading ? (
          <div style={{ minHeight: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Spin size="large" />
          </div>
        ) : report ? (
          <pre
            style={{
              whiteSpace: 'pre-wrap',
              color: '#111827',
              background: '#ffffff',
              lineHeight: 1.9,
              padding: 24,
              borderRadius: 8,
              minHeight: 360,
              fontFamily: 'inherit',
            }}
          >
            {report}
          </pre>
        ) : (
          <Empty description={null} />
        )}
      </Card>
    </Space>
  )
}
