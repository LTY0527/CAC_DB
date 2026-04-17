import { useRef } from 'react'
import { Button, Carousel } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import HeroInfoStrip from './HeroInfoStrip'
import { publicHeroSlides } from './publicPortalData'
import { primaryButtonStyle } from '../utils/uiTheme'
import './publicPortal.css'

export default function PublicHeroBanner({ onAction, dataLoadedAt = '', schoolCount = 0 }) {
  const carouselRef = useRef(null)

  return (
    <section className="public-hero-banner public-section-fade">
      <div className="public-hero-banner__viewport">
        <Button
          type="text"
          aria-label="上一张"
          icon={<LeftOutlined />}
          className="public-hero-banner__arrow public-hero-banner__arrow--left"
          onClick={() => carouselRef.current?.prev()}
        />
        <Button
          type="text"
          aria-label="下一张"
          icon={<RightOutlined />}
          className="public-hero-banner__arrow public-hero-banner__arrow--right"
          onClick={() => carouselRef.current?.next()}
        />

        <Carousel ref={carouselRef} autoplay effect="fade" autoplaySpeed={5200} dots className="public-hero-banner__carousel">
          {publicHeroSlides.map((item) => (
            <div key={item.key}>
              <div className="public-hero-banner__slide">
                <div className="public-hero-banner__backdrop" style={{ backgroundImage: `url(${item.image})`, backgroundPosition: item.imagePosition || 'center' }} />
                <img className="public-hero-banner__photo" src={item.image} alt={item.title} loading="eager" />
                <div className="public-hero-banner__overlay" />
                <div className="public-hero-banner__content">
                  <div className="public-hero-banner__panel">
                    <div className="public-hero-banner__eyebrow">上海高校公开数据</div>
                    <h2 className="public-hero-banner__title">{item.title}</h2>
                    <div className="public-hero-banner__description">{item.description}</div>
                    <div style={{ marginTop: 22 }}>
                      <Button type="primary" style={primaryButtonStyle} onClick={() => onAction?.(item.actionType)}>
                        {item.actionLabel}
                      </Button>
                    </div>
                    <div className="public-hero-banner__meta">公开展示院校概况、专业样本、就业结果与院校对比信息。</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </Carousel>
      </div>

      <HeroInfoStrip dataLoadedAt={dataLoadedAt} schoolCount={schoolCount} />
    </section>
  )
}
