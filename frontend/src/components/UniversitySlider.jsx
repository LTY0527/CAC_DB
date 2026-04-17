import { useState } from 'react'
import { Card, Col, Drawer, Empty, Row, Space } from 'antd'
import { publicUniversityCards } from './publicPortalData'
import { designTokens, panelStyle, sectionTitleStyle } from '../utils/uiTheme'
import './publicPortal.css'

function SummaryItem({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
      <span className="university-slider__drawer-label">{label}</span>
      <span className="university-slider__drawer-value">{value}</span>
    </div>
  )
}

export default function UniversitySlider() {
  const [activeItem, setActiveItem] = useState(null)

  return (
    <>
      <Card
        title={<span style={sectionTitleStyle}>院校专题展示</span>}
        extra={<span style={{ color: designTokens.textMuted, fontSize: 13 }}>横向滑动查看上海高校公开摘要</span>}
        style={panelStyle}
        className="public-section-fade"
      >
        <div style={{ color: designTokens.textSecondary, lineHeight: 1.8, marginBottom: 18 }}>
          结合院校图片与公开摘要信息，展示上海高校专业建设与就业表现的基础画像。
        </div>

        {publicUniversityCards.length ? (
          <div className="university-slider__track">
            {publicUniversityCards.map((item) => (
              <button key={item.key} type="button" className="university-slider__card" onClick={() => setActiveItem(item)}>
                <div className="university-slider__image" style={{ backgroundImage: `url(${item.image})` }} />
                <div className="university-slider__overlay" />
                <div className="university-slider__content">
                  <div className="university-slider__title">{item.name}</div>
                  <div className="university-slider__subtitle">{item.subtitle}</div>
                  <div className="university-slider__hint">点击查看公开摘要</div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <Empty description="暂无院校展示数据" />
        )}
      </Card>

      <Drawer
        title={activeItem?.name || '院校信息'}
        placement="right"
        width={420}
        open={Boolean(activeItem)}
        onClose={() => setActiveItem(null)}
      >
        {activeItem ? (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div
              style={{
                height: 180,
                borderRadius: 16,
                backgroundImage: `linear-gradient(180deg, rgba(15,23,42,0.06), rgba(15,23,42,0.18)), url(${activeItem.image})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }}
            />

            <div style={{ color: designTokens.textSecondary, lineHeight: 1.85 }}>{activeItem.subtitle}</div>

            <Card size="small" style={{ ...panelStyle, boxShadow: 'none' }}>
              <Row gutter={[0, 16]}>
                <Col span={24}>
                  <SummaryItem label="就业率" value={activeItem.employmentRate} />
                </Col>
                <Col span={24}>
                  <SummaryItem label="平均薪资" value={activeItem.avgSalary} />
                </Col>
                <Col span={24}>
                  <SummaryItem label="热门行业" value={activeItem.hotIndustry} />
                </Col>
                <Col span={24}>
                  <SummaryItem label="公开样本" value={activeItem.samples} />
                </Col>
              </Row>
            </Card>

            <div style={{ color: designTokens.textMuted, fontSize: 13, lineHeight: 1.8 }}>
              当前内容为首页专题展示摘要，可与下方公开统计、图表和院校对比信息结合查看。
            </div>
          </Space>
        ) : null}
      </Drawer>
    </>
  )
}
