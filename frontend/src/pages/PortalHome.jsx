import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Space, Statistic } from 'antd'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import {
  designTokens,
  panelStyle,
  primaryButtonStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValuePrimary,
} from '../utils/uiTheme'
import './portalHome.css'

const HERO_SLIDES = [
  {
    key: 'skyline-1',
    title: '上海高校公开数据',
    description: '围绕院校概况、专业表现与公开就业结果，提供统一浏览入口。',
    image: '/assets/上海.jpg',
  },
  {
    key: 'skyline-2',
    title: '院校对比与公开观察',
    description: '结合首页图表与院校专题，查看上海高校专业发展与就业表现。',
    image: '/assets/上海2.jpg',
  },
  {
    key: 'skyline-3',
    title: '面向社会公众的高校信息展示',
    description: '以正式、清晰、可阅读的方式呈现公开数据。',
    image: '/assets/上海3.jpg',
  },
]

const UNIVERSITY_CARDS = [
  {
    key: 'shu',
    name: '上海大学',
    description: '综合性高校，专业覆盖较全，公开样本结构相对均衡。',
    image: '/assets/上海大学2.jpg',
  },
  {
    key: 'fudan',
    name: '复旦大学',
    description: '学科实力突出，科研与高端服务相关去向表现活跃。',
    image: '/assets/复旦大学.jpg',
  },
  {
    key: 'tongji',
    name: '同济大学',
    description: '工程类专业优势明显，建筑与智能制造方向辨识度较高。',
    image: '/assets/同济大学.png',
  },
  {
    key: 'ecnu',
    name: '华东师范大学',
    description: '教育与数据融合方向特色鲜明，就业结构较为稳定。',
    image: '/assets/华东师范大学.jpg',
  },
]

function pad(value) {
  return String(value).padStart(2, '0')
}

function buildClockText(date) {
  const year = date.getFullYear()
  const month = pad(date.getMonth() + 1)
  const day = pad(date.getDate())
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  const seconds = pad(date.getSeconds())
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

export default function PortalHome({ overview, dataLoadedAt = '', onNavigateCompare, onScrollOverview }) {
  const heroRef = useRef(null)
  const galleryRef = useRef(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [clockText, setClockText] = useState(() => buildClockText(new Date()))

  useEffect(() => {
    const timer = window.setInterval(() => setClockText(buildClockText(new Date())), 1000)
    return () => window.clearInterval(timer)
  }, [])

  useEffect(() => {
    const node = heroRef.current
    if (!node) return undefined

    const cards = Array.from(node.querySelectorAll('[data-hero-slide]'))
    if (!cards.length) return undefined

    const intervalId = window.setInterval(() => {
      const nextIndex = (activeIndex + 1) % cards.length
      cards[nextIndex]?.scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' })
    }, 5200)

    return () => window.clearInterval(intervalId)
  }, [activeIndex])

  useEffect(() => {
    const node = heroRef.current
    if (!node) return undefined

    const handleScroll = () => {
      const width = node.clientWidth || 1
      const nextIndex = Math.round(node.scrollLeft / width)
      setActiveIndex(nextIndex)
    }

    node.addEventListener('scroll', handleScroll, { passive: true })
    return () => node.removeEventListener('scroll', handleScroll)
  }, [])

  const summaryItems = useMemo(
    () => [
      { title: '样本覆盖高校数', value: overview?.schoolCount || 0, style: statValuePrimary },
      { title: '公开样本平均薪资', value: overview?.avgSalary || 0, suffix: '元', style: statValueBlue },
    ],
    [overview]
  )

  const scrollHero = (direction) => {
    const node = heroRef.current
    if (!node) return
    node.scrollBy({ left: direction * node.clientWidth, behavior: 'smooth' })
  }

  const scrollGallery = (direction) => {
    const node = galleryRef.current
    if (!node) return
    node.scrollBy({ left: direction * 360, behavior: 'smooth' })
  }

  return (
    <div className="portal-home">
      <section className="portal-home__hero-card">
        <div className="portal-home__hero-toolbar">
          <div>
            <div className="portal-home__hero-tag">Shanghai Higher Education</div>
            <div className="portal-home__hero-caption">公开展示院校概况、专业样本与就业结果</div>
          </div>
          <div className="portal-home__hero-clock">{clockText}</div>
        </div>

        <div ref={heroRef} className="portal-home__hero-track">
          {HERO_SLIDES.map((item) => (
            <article key={item.key} data-hero-slide className="portal-home__hero-slide">
              <div className="portal-home__hero-image" style={{ backgroundImage: `url("${item.image}")` }} />
              <div className="portal-home__hero-overlay" />
              <div className="portal-home__hero-content">
                <div className="portal-home__hero-inner">
                  <h2 className="portal-home__hero-title">{item.title}</h2>
                  <p className="portal-home__hero-description">{item.description}</p>
                  <Space wrap size="middle">
                    <Button type="primary" style={primaryButtonStyle} onClick={onScrollOverview}>
                      查看数据
                    </Button>
                    <Button onClick={onNavigateCompare}>查看院校对比</Button>
                  </Space>
                </div>
              </div>
            </article>
          ))}
        </div>

        <div className="portal-home__hero-controls">
          <div className="portal-home__dots">
            {HERO_SLIDES.map((item, index) => (
              <button
                key={item.key}
                type="button"
                className={`portal-home__dot${index === activeIndex ? ' is-active' : ''}`}
                onClick={() =>
                  heroRef.current?.querySelectorAll('[data-hero-slide]')[index]?.scrollIntoView({
                    behavior: 'smooth',
                    inline: 'start',
                    block: 'nearest',
                  })
                }
              />
            ))}
          </div>
          <div className="portal-home__nav">
            <button type="button" className="portal-home__nav-btn" onClick={() => scrollHero(-1)}>
              <LeftOutlined />
            </button>
            <button type="button" className="portal-home__nav-btn" onClick={() => scrollHero(1)}>
              <RightOutlined />
            </button>
          </div>
        </div>
      </section>

      <section className="portal-home__summary">
        {summaryItems.map((item) => (
          <Card key={item.title} style={panelStyle}>
            <Statistic title={item.title} value={item.value} suffix={item.suffix} styles={{ title: statTitleStyle, content: item.style }} />
          </Card>
        ))}
      </section>

      <section className="portal-home__section-head">
        <div>
          <div style={sectionTitleStyle}>院校专题</div>
          <div className="portal-home__section-desc">通过院校专题图片快速浏览上海高校公开信息，支持横向滑动查看。</div>
        </div>
        <div className="portal-home__nav">
          <button type="button" className="portal-home__nav-btn" onClick={() => scrollGallery(-1)}>
            <LeftOutlined />
          </button>
          <button type="button" className="portal-home__nav-btn" onClick={() => scrollGallery(1)}>
            <RightOutlined />
          </button>
        </div>
      </section>

      <section ref={galleryRef} className="portal-home__school-track">
        {UNIVERSITY_CARDS.map((item) => (
          <article key={item.key} className="portal-home__school-card">
            <div className="portal-home__school-image" style={{ backgroundImage: `url("${item.image}")` }} />
            <div className="portal-home__school-overlay" />
            <div className="portal-home__school-content">
              <div className="portal-home__school-name">{item.name}</div>
              <div className="portal-home__school-desc">{item.description}</div>
            </div>
          </article>
        ))}
      </section>

      <Card style={{ ...panelStyle, borderRadius: 8, boxShadow: designTokens.shadowSoft }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
          <div>
            <div style={sectionTitleStyle}>公开数据总览</div>
            <div className="portal-home__section-desc">继续查看下方图表、榜单和院校对比内容，形成从门户展示到数据浏览的自然衔接。</div>
          </div>
          <div className="portal-home__loaded-at">页面载入时间：{dataLoadedAt || '当前会话未记录'}</div>
        </div>
      </Card>
    </div>
  )
}
