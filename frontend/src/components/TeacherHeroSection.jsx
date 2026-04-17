import { Button } from 'antd'
import { primaryButtonStyle } from '../utils/uiTheme'
import './teacherHeroSection.css'

const defaultCoverageGroups = [
  '学校 / 学历 / 专业 / 生源地',
  '学科门类 / 技能等级 / 课程方向',
  '行业 / 岗位 / 起薪 / 社保状态',
]

export default function TeacherHeroSection({
  schoolName = '上海大学',
  title = '本校培养与就业分析工作台',
  subtitle = '围绕本校就业质量、专业结构和培养联动情况，集中查看重点指标与分析结果。',
  actionLabel = '进入分析',
  onAction,
  image = '/assets/上海大学图书馆2.jpg',
  imageAlt = '校园场景',
  summaryItems = [],
  coverageGroups = defaultCoverageGroups,
}) {
  return (
    <section className="teacher-hero">
      <div className="teacher-hero__main">
        <div className="teacher-hero__content">
          <div className="teacher-hero__eyebrow">{schoolName}教师工作台</div>
          <h1 className="teacher-hero__title">{title}</h1>
          <div className="teacher-hero__subtitle">{subtitle}</div>
          <div className="teacher-hero__actions">
            <Button type="primary" style={primaryButtonStyle} onClick={onAction}>
              {actionLabel}
            </Button>
          </div>
        </div>

        <div className="teacher-hero__visual">
          <img className="teacher-hero__image" src={image} alt={imageAlt} />
          <div className="teacher-hero__image-mask" />
          <div className="teacher-hero__summary">
            {summaryItems.map((item) => (
              <div className="teacher-hero__summary-item" key={item.label}>
                <div className="teacher-hero__summary-label">{item.label}</div>
                <div className="teacher-hero__summary-value">{item.value}</div>
                {item.hint ? <div className="teacher-hero__summary-hint">{item.hint}</div> : null}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="teacher-hero__coverage">
        <div className="teacher-hero__coverage-title">数据覆盖能力</div>
        <div className="teacher-hero__coverage-list">
          {coverageGroups.map((item) => (
            <span key={item} className="teacher-hero__coverage-tag">
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
