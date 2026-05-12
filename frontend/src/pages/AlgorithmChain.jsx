import { Card, Steps, Table, Tag } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { panelStyle, sectionTitleStyle, designTokens } from '../utils/uiTheme'

function statusColor(status = '') {
  if (status === 'SUCCESS') return 'green'
  if (status === 'FAILED') return 'red'
  return 'gold'
}

export default function AlgorithmChain({ algorithmChainLogData = [], loading }) {
  const rows = [...algorithmChainLogData].sort((a, b) => Number(a.stage_order || 0) - Number(b.stage_order || 0))
  const latestBatch = rows[0]?.batch_id || ''

  return (
    <Card style={panelStyle} title={<span style={sectionTitleStyle}>算法链路</span>}>
      <Steps
        direction="vertical"
        current={rows.filter((item) => item.status === 'SUCCESS').length - 1}
        items={rows.map((item) => ({
          title: `${item.stage_order}. ${item.stage_name}`,
          status: item.status === 'SUCCESS' ? 'finish' : item.status === 'FAILED' ? 'error' : 'process',
          icon: item.status === 'SUCCESS' ? <CheckCircleOutlined /> : item.status === 'FAILED' ? <CloseCircleOutlined /> : <ClockCircleOutlined />,
          description: (
            <div>
              <div>算法：{item.algorithm_name || '-'}</div>
              <div>输入表：{item.input_tables || '-'}</div>
              <div>输出表：{item.output_tables || '-'}</div>
              <div>耗时：{Number(item.cost_seconds || 0).toFixed(2)} 秒</div>
            </div>
          ),
        }))}
      />
      <div style={{ margin: '18px 0 10px', color: designTokens.textMuted }}>最近批次：{latestBatch || '暂无批次'}</div>
      <Table
        loading={loading}
        rowKey={(row) => `${row.batch_id}-${row.stage_order}`}
        dataSource={rows}
        pagination={{ pageSize: 10 }}
        columns={[
          { title: '阶段', dataIndex: 'stage_order', width: 70 },
          { title: '阶段名称', dataIndex: 'stage_name' },
          { title: '算法名称', dataIndex: 'algorithm_name' },
          { title: '运行状态', dataIndex: 'status', render: (value) => <Tag color={statusColor(value)}>{value}</Tag> },
          { title: '输出行数', dataIndex: 'row_count' },
          { title: '耗时秒数', dataIndex: 'cost_seconds', render: (value) => Number(value || 0).toFixed(2) },
        ]}
      />
    </Card>
  )
}
