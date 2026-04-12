import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Card, Col, Empty, Row, Space, Tag } from 'antd'
import * as echarts from 'echarts'
import ReactECharts from 'echarts-for-react'
import { EnvironmentOutlined } from '@ant-design/icons'
import { SHANGHAI_GEOJSON_URL, getSchoolGeoPointMap } from '../config/schoolGeo'
import { formatNumber, getSchoolMapStats } from '../utils/dataAdapter'
import {
  designTokens,
  metaLabelStyle,
  metaValueStyle,
  noteTextStyle,
  panelStyle,
  sectionTitleStyle,
} from '../utils/uiTheme'

const SHANGHAI_MAP_KEY = 'shanghai-city-map'
const DEFAULT_VIEWPORT = {
  zoom: 1.02,
  center: [121.46, 31.18],
}
const SURROUNDING_CITY_LABELS = [
  { name: '南通', value: [121.05, 32.08], position: 'top' },
  { name: '苏州', value: [120.62, 31.32], position: 'left' },
  { name: '嘉兴', value: [120.75, 30.76], position: 'left' },
  { name: '舟山海域', value: [122.18, 30.72], position: 'right' },
]

function buildMapOption(points = [], selectedSchool = '', viewport = DEFAULT_VIEWPORT) {
  const maxEmp = Math.max(...points.map((item) => Number(item.total_emp || 0)), 1)
  const zoom = Number(viewport.zoom || DEFAULT_VIEWPORT.zoom)
  const center = Array.isArray(viewport.center) ? viewport.center : DEFAULT_VIEWPORT.center

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.98)',
      borderColor: designTokens.border,
      borderWidth: 1,
      textStyle: { color: designTokens.textPrimary, fontSize: 12 },
      extraCssText: 'border-radius:12px;padding:10px 12px;',
      formatter(params) {
        const detail = params?.data?.detail
        if (!detail) return params?.name || ''
        return [
          `<strong>${detail.school_name}</strong>`,
          detail.school_level,
          `平均薪资：${formatNumber(detail.avg_salary, 0)} 元`,
          `就业样本：${formatNumber(detail.total_emp, 0)}`,
          `覆盖专业：${formatNumber(detail.major_count, 0)}`,
        ].join('<br/>')
      },
    },
    geo: {
      map: SHANGHAI_MAP_KEY,
      roam: true,
      zoom,
      center,
      layoutCenter: ['50%', '52%'],
      layoutSize: '102%',
      itemStyle: {
        areaColor: '#f7fbff',
        borderColor: '#7aa2f7',
        borderWidth: 1.25,
        shadowColor: 'rgba(37, 99, 235, 0.05)',
        shadowBlur: 10,
      },
      emphasis: {
        itemStyle: {
          areaColor: '#dbeafe',
        },
      },
      label: {
        show: false,
      },
    },
    series: [
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        silent: true,
        symbolSize: 1,
        zlevel: 1,
        label: {
          show: true,
          formatter: '{b}',
          position(params) {
            return params?.data?.position || 'top'
          },
          color: '#6b85b6',
          fontSize: 12,
          fontWeight: 600,
          distance: 8,
        },
        itemStyle: {
          color: 'transparent',
        },
        data: SURROUNDING_CITY_LABELS,
      },
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        symbol: 'pin',
        symbolSize(_, params) {
          const emp = Number(params?.data?.detail?.total_emp || 0)
          return 30 + Math.round((emp / maxEmp) * 16)
        },
        itemStyle: {
          color: '#2563eb',
          shadowColor: 'rgba(37, 99, 235, 0.25)',
          shadowBlur: 18,
        },
        emphasis: {
          itemStyle: {
            color: '#0f766e',
          },
          label: {
            show: true,
            formatter: '{b}',
            color: designTokens.textPrimary,
            backgroundColor: '#ffffff',
            borderColor: designTokens.border,
            borderWidth: 1,
            borderRadius: 8,
            padding: [4, 8],
          },
        },
        data: points.map((item) => ({
          name: item.school_name,
          value: [item.lng, item.lat, item.total_emp],
          detail: item,
          itemStyle: item.school_name === selectedSchool ? { color: '#0f766e' } : undefined,
        })),
      },
      {
        type: 'effectScatter',
        coordinateSystem: 'geo',
        rippleEffect: {
          scale: 4,
          brushType: 'stroke',
        },
        symbolSize: 11,
        itemStyle: {
          color: '#0f766e',
        },
        data: points
          .filter((item) => item.school_name === selectedSchool)
          .map((item) => ({
            name: item.school_name,
            value: [item.lng, item.lat, item.total_emp],
            detail: item,
          })),
      },
    ],
  }
}

function renderStatCard(label, value, accent = designTokens.accent) {
  return (
    <div
      style={{
        border: `1px solid ${designTokens.border}`,
        borderRadius: 14,
        padding: 14,
        background: '#ffffff',
        minHeight: 94,
      }}
    >
      <div style={metaLabelStyle}>{label}</div>
      <div
        style={{
          marginTop: 10,
          color: accent,
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: '-0.02em',
        }}
      >
        {value}
      </div>
    </div>
  )
}

function FallbackMap({ schools = [], selectedSchool = '', onSelectSchool }) {
  const maxLng = Math.max(...schools.map((item) => item.lng), 1)
  const minLng = Math.min(...schools.map((item) => item.lng), 0)
  const maxLat = Math.max(...schools.map((item) => item.lat), 1)
  const minLat = Math.min(...schools.map((item) => item.lat), 0)

  return (
    <div
      style={{
        position: 'relative',
        minHeight: 620,
        borderRadius: 20,
        overflow: 'hidden',
        background: 'linear-gradient(180deg, #eaf4ff 0%, #dcecff 100%)',
        border: `1px solid ${designTokens.border}`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          inset: '9% 16% 10% 12%',
          borderRadius: '46% 42% 50% 44% / 38% 44% 48% 54%',
          border: '1px solid rgba(122,162,247,0.22)',
          background: '#fbfdff',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'repeating-linear-gradient(0deg, transparent 0, transparent 42px, rgba(59,130,246,0.05) 42px, rgba(59,130,246,0.05) 43px), repeating-linear-gradient(90deg, transparent 0, transparent 42px, rgba(59,130,246,0.045) 42px, rgba(59,130,246,0.045) 43px)',
          opacity: 0.45,
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          top: '8%',
          right: '8%',
          color: '#6b85b6',
          fontSize: 12,
          letterSpacing: '0.08em',
          zIndex: 1,
        }}
      >
        上海周边示意
      </div>
      <div style={{ position: 'absolute', top: 24, left: 24, zIndex: 2 }}>
        <div style={sectionTitleStyle}>上海高校空间分布</div>
        <div style={{ ...noteTextStyle, marginTop: 6 }}>地图源不可用时自动切换为静态分布示意图。</div>
      </div>
      {schools.map((item) => {
        const left = ((item.lng - minLng) / (maxLng - minLng || 1)) * 78 + 7
        const top = (1 - (item.lat - minLat) / (maxLat - minLat || 1)) * 74 + 10
        const active = item.school_name === selectedSchool

        return (
          <button
            key={item.school_name}
            type="button"
            onClick={() => onSelectSchool(item.school_name)}
            style={{
              position: 'absolute',
              left: `${left}%`,
              top: `${top}%`,
              transform: 'translate(-50%, -50%)',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              zIndex: active ? 3 : 2,
            }}
          >
            <div
              style={{
                width: active ? 18 : 14,
                height: active ? 18 : 14,
                borderRadius: 999,
                background: active ? '#0f766e' : '#2563eb',
                boxShadow: active ? '0 0 0 8px rgba(15,118,110,0.12)' : '0 0 0 6px rgba(37,99,235,0.12)',
                margin: '0 auto',
              }}
            />
            <div
              style={{
                marginTop: 10,
                padding: '4px 8px',
                borderRadius: 999,
                background: 'rgba(255,255,255,0.92)',
                border: `1px solid ${active ? '#99f6e4' : designTokens.border}`,
                color: designTokens.textPrimary,
                fontSize: 12,
                fontWeight: 600,
                whiteSpace: 'nowrap',
              }}
            >
              {item.school_name}
            </div>
          </button>
        )
      })}
    </div>
  )
}

export default function SchoolMapExplorer({
  employmentData = [],
  roleMode = 'public',
  onAction,
  actionLabel = '查看详情',
}) {
  const chartRef = useRef(null)
  const schoolStats = useMemo(() => getSchoolMapStats(employmentData), [employmentData])
  const pointMap = useMemo(() => getSchoolGeoPointMap(), [])
  const mapPoints = useMemo(
    () =>
      schoolStats
        .map((item) => {
          const geo = pointMap[item.school_name]
          if (!geo) return null
          return { ...geo, ...item }
        })
        .filter(Boolean),
    [pointMap, schoolStats]
  )
  const [selectedSchool, setSelectedSchool] = useState(mapPoints[0]?.school_name || '')
  const [mapReady, setMapReady] = useState(Boolean(echarts.getMap(SHANGHAI_MAP_KEY)))
  const [mapFailed, setMapFailed] = useState(false)
  const [viewport, setViewport] = useState(DEFAULT_VIEWPORT)

  useEffect(() => {
    if (!mapPoints.length) {
      setSelectedSchool('')
      return
    }
    if (!mapPoints.some((item) => item.school_name === selectedSchool)) {
      setSelectedSchool(mapPoints[0].school_name)
    }
  }, [mapPoints, selectedSchool])

  useEffect(() => {
    let alive = true

    async function loadMap() {
      if (echarts.getMap(SHANGHAI_MAP_KEY)) {
        setMapReady(true)
        return
      }

      try {
        const response = await fetch(SHANGHAI_GEOJSON_URL)
        if (!response.ok) {
          throw new Error(`map fetch failed: ${response.status}`)
        }
        const geoJson = await response.json()
        if (!alive) return
        echarts.registerMap(SHANGHAI_MAP_KEY, geoJson)
        setMapReady(true)
      } catch {
        if (!alive) return
        setMapFailed(true)
      }
    }

    loadMap()

    return () => {
      alive = false
    }
  }, [])

  const selectedDetail = mapPoints.find((item) => item.school_name === selectedSchool) || null
  const mapOption = useMemo(() => buildMapOption(mapPoints, selectedSchool, viewport), [mapPoints, selectedSchool, viewport])
  const roleDescription =
    roleMode === 'gov'
      ? '点击学校后先查看摘要，再进入学校治理钻取页，继续查看专业和预警详情。'
      : '点击学校后查看公开摘要信息，适合社会公众快速浏览上海高校画像。'

  const handleSelectSchool = (schoolName) => {
    setSelectedSchool(schoolName)
  }

  const handleGeoRoam = () => {
    const instance = chartRef.current?.getEchartsInstance?.()
    const nextGeo = instance?.getOption?.()?.geo?.[0]
    if (!nextGeo) return
    setViewport((prev) => ({
      zoom: Number(nextGeo.zoom || prev.zoom || DEFAULT_VIEWPORT.zoom),
      center: Array.isArray(nextGeo.center) ? nextGeo.center : prev.center,
    }))
  }

  return (
    <Card
      title={<span style={sectionTitleStyle}>上海高校地图窗口</span>}
      extra={<span style={{ color: designTokens.textMuted, fontSize: 12 }}>点击点位查看院校画像</span>}
      style={panelStyle}
    >
      {!mapPoints.length ? (
        <Empty description="当前暂无可展示的学校样本" />
      ) : (
        <Row gutter={[20, 20]}>
          <Col xs={24} xl={16}>
            {mapReady && !mapFailed ? (
              <div
                style={{
                  position: 'relative',
                  minHeight: 620,
                  borderRadius: 20,
                  overflow: 'hidden',
                  background: 'linear-gradient(180deg, #eaf4ff 0%, #dcecff 100%)',
                  border: `1px solid ${designTokens.border}`,
                }}
              >
                <div
                  style={{
                    position: 'absolute',
                    inset: 18,
                    borderRadius: 24,
                    background:
                      'radial-gradient(circle at 35% 38%, rgba(255,255,255,0.44), rgba(255,255,255,0) 54%)',
                    border: '1px solid rgba(122,162,247,0.15)',
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    background:
                      'repeating-linear-gradient(0deg, transparent 0, transparent 44px, rgba(59,130,246,0.045) 44px, rgba(59,130,246,0.045) 45px), repeating-linear-gradient(90deg, transparent 0, transparent 44px, rgba(59,130,246,0.04) 44px, rgba(59,130,246,0.04) 45px)',
                    opacity: 0.42,
                    pointerEvents: 'none',
                  }}
                />
                <div
                  style={{
                    position: 'absolute',
                    top: '8%',
                    right: '9%',
                    color: '#6b85b6',
                    fontSize: 12,
                    letterSpacing: '0.08em',
                    zIndex: 2,
                    pointerEvents: 'none',
                  }}
                >
                  上海周边
                </div>
                <ReactECharts
                  ref={chartRef}
                  option={mapOption}
                  notMerge
                  style={{ height: 620, position: 'relative', zIndex: 2 }}
                  onEvents={{
                    click: (params) => {
                      const schoolName = params?.data?.detail?.school_name || params?.name
                      if (schoolName) {
                        handleSelectSchool(schoolName)
                      }
                    },
                    georoam: handleGeoRoam,
                  }}
                />
              </div>
            ) : (
              <FallbackMap schools={mapPoints} selectedSchool={selectedSchool} onSelectSchool={handleSelectSchool} />
            )}
          </Col>

          <Col xs={24} xl={8}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, height: '100%' }}>
              <div
                style={{
                  border: `1px solid ${designTokens.border}`,
                  borderRadius: 18,
                  padding: 18,
                  background: 'linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)',
                }}
              >
                <div style={metaLabelStyle}>地图模式</div>
                <div style={{ ...sectionTitleStyle, marginTop: 8 }}>{selectedDetail?.school_name || '请选择学校'}</div>
                <div style={{ ...metaValueStyle, marginTop: 8 }}>
                  {selectedDetail?.campus_name ? `${selectedDetail.campus_name} · ` : ''}
                  {selectedDetail?.address || '暂无主校区地址'}
                </div>
                <div style={{ ...noteTextStyle, marginTop: 10 }}>{roleDescription}</div>
                <Space size={[8, 8]} wrap style={{ marginTop: 14 }}>
                  <Tag color="blue">{selectedDetail?.school_level || '未标注'}</Tag>
                  <Tag color="cyan">{selectedDetail?.top_industry || '未标注行业'}</Tag>
                  <Tag color="geekblue">上海市</Tag>
                </Space>
              </div>

              {selectedDetail ? (
                <>
                  <Row gutter={[12, 12]}>
                    <Col span={12}>{renderStatCard('平均薪资', `${formatNumber(selectedDetail.avg_salary, 0)}元`)}</Col>
                    <Col span={12}>{renderStatCard('就业样本', formatNumber(selectedDetail.total_emp, 0), '#0f766e')}</Col>
                    <Col span={12}>{renderStatCard('覆盖专业', formatNumber(selectedDetail.major_count, 0), designTokens.purple)}</Col>
                    <Col span={12}>
                      {renderStatCard('先导产业占比', `${Number(selectedDetail.strategic_ratio || 0).toFixed(1)}%`, '#d97706')}
                    </Col>
                  </Row>

                  <div
                    style={{
                      border: `1px solid ${designTokens.border}`,
                      borderRadius: 18,
                      padding: 18,
                      background: '#ffffff',
                    }}
                  >
                    <div style={metaLabelStyle}>优势专业</div>
                    <Space size={[8, 8]} wrap style={{ marginTop: 12 }}>
                      {(selectedDetail.top_majors || []).map((major) => (
                        <Tag key={major} color="processing">
                          {major}
                        </Tag>
                      ))}
                    </Space>
                    <div style={{ ...metaLabelStyle, marginTop: 18 }}>坐标信息</div>
                    <div style={{ ...metaValueStyle, marginTop: 8 }}>
                      <EnvironmentOutlined style={{ marginRight: 8, color: designTokens.accent }} />
                      {selectedDetail.lng}, {selectedDetail.lat}
                    </div>
                    {onAction ? (
                      <Button type="primary" style={{ marginTop: 18 }} onClick={() => onAction(selectedDetail.school_name)}>
                        {actionLabel}
                      </Button>
                    ) : null}
                  </div>
                </>
              ) : (
                <Empty description="点击地图中的学校点位查看摘要信息" />
              )}
            </div>
          </Col>
        </Row>
      )}
    </Card>
  )
}
