import { Button } from 'antd'
import { primaryButtonStyle } from '../utils/uiTheme'
import './governmentHeroSection.css'

export default function GovernmentHeroSection({
  title = '上海高校就业监测与治理总览',
  subtitle = '围绕区域监测、跨校对比和治理判断，集中查看重点信号、结构差异与风险变化。',
  actionLabel = '进入重点监测',
  onAction,
  image = '/assets/上海4.jpg',
  imageAlt = '上海城市治理场景',
  summaryItems = [],
}) {
  return (
    <section className="government-hero">
      <div className="government-hero__main">
        <div className="government-hero__visual">
          <img className="government-hero__image" src={image} alt={imageAlt} />
          <div className="government-hero__image-mask" />
        </div>

        <div className="government-hero__content">
          <div className="government-hero__eyebrow">区域治理工作台</div>
          <h1 className="government-hero__title">{title}</h1>
          <div className="government-hero__subtitle">{subtitle}</div>
          <div className="government-hero__actions">
            <Button type="primary" style={primaryButtonStyle} onClick={onAction}>
              {actionLabel}
            </Button>
          </div>
        </div>

        <div className="government-hero__summary">
          {summaryItems.map((item) => (
            <div className="government-hero__summary-item" key={item.label}>
              <div className="government-hero__summary-label">{item.label}</div>
              <div className="government-hero__summary-value">{item.value}</div>
              {item.hint ? <div className="government-hero__summary-hint">{item.hint}</div> : null}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
