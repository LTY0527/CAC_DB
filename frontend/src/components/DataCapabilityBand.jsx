import './dataCapabilityBand.css'

export default function DataCapabilityBand({
  title = '数据能力覆盖',
  items = [],
  flowTitle = '平台主链路',
  flowItems = [],
  loadedAtLabel = '数据载入时间',
  loadedAt = '',
}) {
  return (
    <section className="data-capability-band">
      <div className="data-capability-band__header">
        <div className="data-capability-band__title">{title}</div>
        <div className="data-capability-band__meta">
          <div className="data-capability-band__meta-label">{loadedAtLabel}</div>
          <div className="data-capability-band__meta-value">{loadedAt || '当前会话未记录'}</div>
        </div>
      </div>

      <div className="data-capability-band__grid">
        {items.map((item) => (
          <div className="data-capability-band__item" key={item.key || item.title}>
            <div className="data-capability-band__item-title">{item.title}</div>
            <div className="data-capability-band__tags">
              {(item.fields || []).map((field) => (
                <span className="data-capability-band__tag" key={field}>
                  {field}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {flowItems.length ? (
        <div className="data-capability-band__flow">
          <div className="data-capability-band__flow-title">{flowTitle}</div>
          <div className="data-capability-band__flow-list">
            {flowItems.map((item, index) => (
              <span className="data-capability-band__flow-tag" key={item}>
                {index + 1}. {item}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}
