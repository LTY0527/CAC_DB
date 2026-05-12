import { Collapse, Descriptions, Divider, Drawer, Space, Tag } from 'antd'
import { designTokens, sectionTitleStyle } from '../utils/uiTheme'

const labelStyle = {
  color: designTokens.textMuted,
  fontSize: 12,
  lineHeight: 1.7,
}

const valueStyle = {
  color: designTokens.textPrimary,
  fontSize: 14,
  lineHeight: 1.85,
}

function renderSimpleValue(value) {
  if (Array.isArray(value)) {
    return (
      <Space size={[6, 6]} wrap>
        {value.map((item) => (
          <Tag key={item} style={{ marginInlineEnd: 0 }}>
            {item}
          </Tag>
        ))}
      </Space>
    )
  }

  return value || '暂无内容'
}

export default function MetricInsightDrawer({ open, onClose, insight, roleMode = 'school' }) {
  const detailItems = insight
    ? [
        {
          key: 'definition',
          label: '统计口径',
          children: <div style={valueStyle}>{insight.definition || '暂无内容'}</div>,
        },
        {
          key: 'source',
          label: '数据来源',
          children: <div style={valueStyle}>{insight.dataSource || '暂无内容'}</div>,
        },
        {
          key: 'dimensions',
          label: '关联维度',
          children: <div style={valueStyle}>{renderSimpleValue(insight.dimensions)}</div>,
        },
        {
          key: 'api',
          label: '接口路径',
          children: <div style={{ ...valueStyle, fontFamily: 'Consolas, monospace', fontSize: 13 }}>{insight.apiPath || '暂无内容'}</div>,
        },
        {
          key: 'notes',
          label: '备注',
          children: <div style={valueStyle}>{insight.notes || '暂无内容'}</div>,
        },
      ]
    : []

  const roleLabel =
    roleMode === 'gov'
      ? '治理监测'
      : roleMode === 'public'
        ? '公开信息'
        : '校内分析'

  return (
    <Drawer
      title={<span style={sectionTitleStyle}>指标详情</span>}
      placement="right"
      width={480}
      open={open}
      onClose={onClose}
    >
      {insight ? (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <div style={{ ...labelStyle, textTransform: 'uppercase', letterSpacing: 0.6 }}>{roleLabel}</div>
            <div style={{ color: designTokens.textPrimary, fontSize: 24, fontWeight: 700, lineHeight: 1.4, marginTop: 6 }}>
              {insight.title}
            </div>
            <div style={{ ...valueStyle, marginTop: 10 }}>{insight.summary}</div>
          </div>

          <Descriptions
            column={1}
            size="small"
            colon={false}
            labelStyle={{ ...labelStyle, width: 96 }}
            contentStyle={valueStyle}
            items={[
              { key: 'scope', label: '统计范围', children: insight.scope || '暂无内容' },
              { key: 'interpretation', label: '如何理解', children: insight.interpretation || '暂无内容' },
              { key: 'updatedAt', label: '最近更新', children: insight.updatedAt || '暂无内容' },
              { key: 'decisionHint', label: '辅助判断', children: insight.decisionHint || '暂无内容' },
            ]}
          />

          <Divider style={{ marginBlock: 0 }} />

          <Collapse
            bordered={false}
            items={[
              {
                key: 'details',
                label: '详细口径',
                children: <Descriptions column={1} size="small" colon={false} labelStyle={{ ...labelStyle, width: 96 }} items={detailItems} />,
              },
            ]}
          />
        </Space>
      ) : null}
    </Drawer>
  )
}
