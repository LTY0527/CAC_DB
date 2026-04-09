import { Card, Col, Row, Select, Statistic, Table } from 'antd'
import { useMemo, useState } from 'react'
import EmploymentSankey from '../components/charts/EmploymentSankey'
import {
  formatNumber,
  getEmploymentFilterOptions,
  getEmploymentOverview,
} from '../utils/dataAdapter'
import {
  algorithmTextStyle,
  metaLabelStyle,
  metaValueStyle,
  noteTextStyle,
  panelStyle,
  riskTextStyle,
  sectionTitleStyle,
  statTitleStyle,
  statValueBlue,
  statValueCyan,
  statValuePrimary,
  statValuePurple,
} from '../utils/uiTheme'

function filterEmploymentData(data = [], { school, industry, roleMode, currentSchool }) {
  return (Array.isArray(data) ? data : []).filter((item) => {
    const safeSchool = item?.school_name || ''
    const safeIndustry = item?.leading_industry_tag || ''
    const scopedSchool = roleMode === 'school' ? currentSchool : school

    const matchSchool = scopedSchool === '全部' || !scopedSchool || safeSchool === scopedSchool
    const matchIndustry = industry === '全部' || !industry || safeIndustry === industry
    return matchSchool && matchIndustry
  })
}

export default function EmploymentMonitor({
  employmentData = [],
  currentSchool = '上海大学',
  roleMode = 'school',
  dataLoadedAt = '',
  loading,
  error,
}) {
  const [selectedSchool, setSelectedSchool] = useState('全部')
  const [selectedIndustry, setSelectedIndustry] = useState('全部')

  const options = useMemo(() => getEmploymentFilterOptions(employmentData), [employmentData])
  const filteredData = useMemo(
    () =>
      filterEmploymentData(employmentData, {
        school: selectedSchool,
        industry: selectedIndustry,
        roleMode,
        currentSchool,
      }),
    [employmentData, selectedIndustry, selectedSchool, roleMode, currentSchool]
  )
  const overview = useMemo(() => getEmploymentOverview(filteredData), [filteredData])

  const tableData = useMemo(
    () =>
      filteredData.slice(0, 12).map((item, index) => ({
        key: `${item?.school_name || 'school'}-${item?.major_name || 'major'}-${index}`,
        school_name: item?.school_name || '-',
        origin_place: item?.origin_place || '-',
        school_level: item?.school_level || '-',
        major_name: item?.major_name || '-',
        leading_industry_tag: item?.leading_industry_tag || '-',
        emp_count: Number(item?.emp_count || 0),
        avg_salary: Number(item?.avg_salary || 0),
      })),
    [filteredData]
  )

  const columns = [
    ...(roleMode === 'gov' ? [{ title: '学校', dataIndex: 'school_name' }] : []),
    { title: '生源地', dataIndex: 'origin_place' },
    { title: '院校层级', dataIndex: 'school_level' },
    { title: '专业', dataIndex: 'major_name' },
    { title: '就业行业', dataIndex: 'leading_industry_tag' },
    { title: '人数', dataIndex: 'emp_count', render: (value) => formatNumber(value) },
    { title: '平均薪资', dataIndex: 'avg_salary', render: (value) => `¥${formatNumber(value, 0)}` },
  ]

  if (loading) return <div style={{ color: '#d9eeff' }}>数据加载中...</div>
  if (error && !employmentData.length) return <div style={{ color: '#ff7875' }}>{error}</div>

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]}>
            <Col xs={24} xl={14}>
              <div style={sectionTitleStyle}>动态监测看板</div>
              <div style={{ ...noteTextStyle, marginTop: 10 }}>
                业务价值：持续跟踪“生源地 - 院校层级 - 行业去向”链路变化，帮助学校或主管部门及时发现结构性波动，而不是只看单一就业率。
              </div>
            </Col>
            <Col xs={24} xl={10}>
              <Row gutter={[12, 12]}>
                <Col span={12}>
                  <div style={metaLabelStyle}>数据载入时间</div>
                  <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
                </Col>
                <Col span={12}>
                  <div style={metaLabelStyle}>说明口径</div>
                  <div style={metaValueStyle}>当前页面按数据库实时聚合结果展示</div>
                </Col>
                <Col span={24}>
                  <div style={algorithmTextStyle}>算法说明：本模块采用后端聚合统计，不单独训练模型，重点展示就业流向结构和样本分布。</div>
                </Col>
                <Col span={24}>
                  <div style={riskTextStyle}>风险提示：页面反映的是已入库样本的结构变化，不等同于完整毕业生总体口径。</div>
                </Col>
              </Row>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="就业样本人数" value={overview.totalEmpCount} styles={{ title: statTitleStyle, content: statValuePrimary }} />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="加权平均薪资" value={Number(overview.avgSalaryWeighted.toFixed(2))} prefix="¥" styles={{ title: statTitleStyle, content: statValueBlue }} />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="先导产业人数" value={overview.leadEmpCount} styles={{ title: statTitleStyle, content: statValueCyan }} />
        </Card>
      </Col>
      <Col xs={24} md={12} xl={6}>
        <Card style={panelStyle}>
          <Statistic title="覆盖专业数" value={overview.majorCount} styles={{ title: statTitleStyle, content: statValuePurple }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>监测条件</span>} style={panelStyle}>
          <Row gutter={[12, 12]}>
            {roleMode === 'gov' ? (
              <Col xs={24} md={8}>
                <Select
                  value={selectedSchool}
                  onChange={setSelectedSchool}
                  style={{ width: '100%' }}
                  options={[
                    { label: '全部高校', value: '全部' },
                    ...(options?.schools || []).map((item) => ({ label: item, value: item })),
                  ]}
                />
              </Col>
            ) : null}
            <Col xs={24} md={roleMode === 'gov' ? 8 : 12}>
              <Select
                value={selectedIndustry}
                onChange={setSelectedIndustry}
                style={{ width: '100%' }}
                options={[
                  { label: '全部行业', value: '全部' },
                  ...(options?.industries || []).map((item) => ({ label: item, value: item })),
                ]}
              />
            </Col>
            <Col xs={24} md={roleMode === 'gov' ? 8 : 12}>
              <div style={noteTextStyle}>
                图中节点宽度代表样本人数，可用于解释“哪些学校层级和行业吸纳了更多学生”，适合在答辩时先讲结构，再讲指标。
              </div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>就业流向桑基图</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>关键说明：从左到右依次为生源地、院校层级、行业去向。</span>}
          style={panelStyle}
        >
          <EmploymentSankey data={filteredData} style={{ height: '58vh', minHeight: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={<span style={sectionTitleStyle}>样本明细</span>}
          extra={<span style={{ color: '#8fb7d8', fontSize: 12 }}>用于支撑图形解释，避免只有图没有落点。</span>}
          style={panelStyle}
        >
          <Table columns={columns} dataSource={tableData} pagination={{ pageSize: 8 }} />
        </Card>
      </Col>
    </Row>
  )
}
