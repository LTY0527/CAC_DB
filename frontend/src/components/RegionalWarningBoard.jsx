import { Card, Col, Empty, Row, Tag } from 'antd'
import {
  getRegionalWarningsOverview,
  getRegionalWarningTagColor,
} from '../utils/dataAdapter'
import {
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
  sectionTitleStyle,
  designTokens,
} from '../utils/uiTheme'

export default function RegionalWarningBoard({ data = {} }) {
  const { items, summary } = getRegionalWarningsOverview(data, 6)

  return (
    <Card style={panelStyle}>
      <Row gutter={[16, 16]} align="middle" style={{ marginBottom: 4 }}>
        <Col xs={24} xl={16}>
          <div style={sectionTitleStyle}>区域预警看板</div>
        </Col>
        <Col xs={24} xl={8}>
          <div style={metaLabelStyle}>最近更新时间</div>
          <div style={metaValueStyle}>{summary.updated_at || '当前会话未记录'}</div>
        </Col>
      </Row>

      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        <Col>
          <Tag color="red">高风险 {summary.high}</Tag>
        </Col>
        <Col>
          <Tag color="gold">中风险 {summary.medium}</Tag>
        </Col>
        <Col>
          <Tag color="blue">低风险 {summary.low}</Tag>
        </Col>
        <Col>
          <Tag color="default">预警总数 {summary.total}</Tag>
        </Col>
      </Row>

      {items.length ? (
        <Row gutter={[16, 16]}>
          {items.map((item) => (
            <Col xs={24} md={12} xl={8} key={item.key}>
              <Card
                style={{
                  ...panelStyle,
                  minHeight: 220,
                  borderColor:
                    item.warning_level === '高'
                      ? 'rgba(220, 38, 38, 0.2)'
                      : item.warning_level === '中'
                        ? 'rgba(217, 119, 6, 0.2)'
                        : panelStyle.borderColor,
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                  <Tag color={getRegionalWarningTagColor(item.warning_level)}>{item.warning_level}风险</Tag>
                  <span style={{ color: designTokens.textMuted, fontSize: 12 }}>{item.warning_type}</span>
                </div>
                <div
                  style={{
                    color: designTokens.textPrimary,
                    fontSize: 17,
                    fontWeight: 700,
                    lineHeight: 1.5,
                    marginTop: 14,
                  }}
                >
                  {item.warning_title}
                </div>
                <div style={{ color: designTokens.textMuted, fontSize: 12, marginTop: 10 }}>
                  预警对象：{item.target_scope} / {item.target_name}
                </div>
                <div style={{ color: designTokens.textSecondary, lineHeight: 1.8, marginTop: 14 }}>
                  {item.trigger_reason}
                </div>
                <div style={{ marginTop: 16, color: designTokens.textPrimary, fontWeight: 600 }}>
                  {item.metric_value}
                </div>
                <div style={{ marginTop: 6, color: designTokens.textSecondary }}>{item.metric_change}</div>
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Empty description="暂无可展示的区域预警" />
      )}
    </Card>
  )
}
