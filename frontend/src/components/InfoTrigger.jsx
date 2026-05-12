import { Button, Tooltip } from 'antd'
import { InfoCircleOutlined } from '@ant-design/icons'
import { designTokens } from '../utils/uiTheme'

export default function InfoTrigger({ onClick, label = '查看指标详情' }) {
  return (
    <Tooltip title={label}>
      <Button
        type="text"
        size="small"
        icon={<InfoCircleOutlined />}
        onClick={(event) => {
          event.stopPropagation()
          onClick?.()
        }}
        style={{
          width: 24,
          height: 24,
          minWidth: 24,
          padding: 0,
          color: designTokens.textMuted,
          borderRadius: 999,
        }}
      />
    </Tooltip>
  )
}
