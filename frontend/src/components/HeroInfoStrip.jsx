import { Space, Tag } from 'antd'
import { designTokens } from '../utils/uiTheme'

export default function HeroInfoStrip({ dataLoadedAt = '', schoolCount = 0 }) {
  return (
    <div className="hero-info-strip">
      <div className="hero-info-strip__item">
        <div className="hero-info-strip__label">数据更新时间</div>
        <div className="hero-info-strip__value">{dataLoadedAt || '当前会话未记录'}</div>
      </div>

      <div className="hero-info-strip__item">
        <div className="hero-info-strip__label">覆盖院校数</div>
        <div className="hero-info-strip__value">{schoolCount || 0} 所</div>
      </div>

      <div className="hero-info-strip__item hero-info-strip__item--wide">
        <div className="hero-info-strip__label">可查看内容</div>
        <Space size={[6, 6]} wrap>
          {['院校概况', '专业样本', '就业结果', '院校对比'].map((item) => (
            <Tag
              key={item}
              style={{
                marginInlineEnd: 0,
                borderRadius: 999,
                borderColor: designTokens.border,
                color: designTokens.textSecondary,
                background: '#ffffff',
              }}
            >
              {item}
            </Tag>
          ))}
        </Space>
      </div>

      <div className="hero-info-strip__item hero-info-strip__item--wide">
        <div className="hero-info-strip__label">公开信息说明</div>
        <div className="hero-info-strip__text">展示院校概况、专业样本与就业结果等公开信息，适合作为社会公众浏览入口。</div>
      </div>
    </div>
  )
}
