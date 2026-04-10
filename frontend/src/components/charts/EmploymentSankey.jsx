import { Empty } from 'antd'
import ReactECharts from 'echarts-for-react'
import { darkTooltip, noteTextStyle } from '../../utils/uiTheme'

function normalizeEmploymentFlows(data = []) {
  if (!Array.isArray(data)) return []

  return data.map((item) => ({
    originPlace: item?.origin_place || '未知生源地',
    schoolLevel: item?.school_level || '未知院校层级',
    industry: item?.leading_industry_tag || '未知就业行业',
    value: Number(item?.emp_count || 0),
  }))
}

function buildSankeyOption(data = []) {
  const rows = normalizeEmploymentFlows(data)
  const nodeMap = new Map()
  const linkMap = new Map()

  const touchNode = (name, depth) => {
    if (!nodeMap.has(name)) {
      nodeMap.set(name, { name, depth })
    }
  }

  const appendLink = (source, target, value) => {
    const key = `${source}__${target}`
    if (!linkMap.has(key)) {
      linkMap.set(key, { source, target, value: 0 })
    }
    linkMap.get(key).value += value
  }

  rows.forEach((item) => {
    if (!item.value) return
    touchNode(item.originPlace, 0)
    touchNode(item.schoolLevel, 1)
    touchNode(item.industry, 2)
    appendLink(item.originPlace, item.schoolLevel, item.value)
    appendLink(item.schoolLevel, item.industry, item.value)
  })

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      ...darkTooltip,
      formatter(params) {
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>人数：${params.data.value || 0}`
        }
        return `${params.name}`
      },
    },
    series: [
      {
        type: 'sankey',
        top: 20,
        bottom: 20,
        left: 16,
        right: 16,
        nodeAlign: 'justify',
        draggable: false,
        emphasis: { focus: 'adjacency' },
        data: [...nodeMap.values()],
        links: [...linkMap.values()],
        lineStyle: {
          color: 'gradient',
          opacity: 0.35,
          curveness: 0.5,
        },
        itemStyle: {
          borderWidth: 1,
          borderColor: 'rgba(190, 225, 255, 0.14)',
          color: '#2ec7ff',
        },
        label: {
          color: '#d9eeff',
          fontSize: 12,
        },
      },
    ],
  }
}

export default function EmploymentSankey({ data = [], style }) {
  const hasData = Array.isArray(data) && data.some((item) => Number(item?.emp_count || 0) > 0)

  if (!hasData) {
    return (
      <Empty
        description={<span style={noteTextStyle}>暂无可用于就业流向图的数据</span>}
      />
    )
  }

  return <ReactECharts option={buildSankeyOption(data)} style={style || { height: '100%', minHeight: 420 }} />
}
