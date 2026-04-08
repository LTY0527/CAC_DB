import { Card, Col, Row, Space, Tag } from 'antd'
import { getAdminStatus } from '../utils/dataAdapter'
import { noteTextStyle, panelStyle, sectionTitleStyle, statTitleStyle, statValueBlue, statValuePrimary } from '../utils/uiTheme'

export default function AdminWorkspace() {
  const status = getAdminStatus()

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card title={<span style={sectionTitleStyle}>工作台</span>} style={panelStyle}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12} xl={8}>
            <div style={statTitleStyle}>最近一次数据同步</div>
            <div style={{ ...statValuePrimary, marginTop: 12 }}>{status.lastSyncAt}</div>
            <div style={{ ...noteTextStyle, marginTop: 10 }}>当前仅保留管理员工作台主视图。</div>
          </Col>
          <Col xs={24} md={12} xl={8}>
            <div style={statTitleStyle}>抓取成功率</div>
            <div style={{ ...statValueBlue, marginTop: 12 }}>{status.successRate}%</div>
          </Col>
          <Col xs={24} xl={8}>
            <div style={statTitleStyle}>当前状态</div>
            <div style={{ marginTop: 14 }}>
              <Tag color="green">运行正常</Tag>
              <Tag color="blue">权限配置收敛为单工作台</Tag>
            </div>
          </Col>
        </Row>
      </Card>
    </Space>
  )
}
