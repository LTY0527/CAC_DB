import { Card, Col, Row, Select, Statistic, Table } from 'antd'
import { useMemo, useState } from 'react'
import EmploymentSankey from '../components/charts/EmploymentSankey'
import { formatNumber, getEmploymentFilterOptions, getEmploymentOverview } from '../utils/dataAdapter'
import {
  metaLabelStyle,
  metaValueStyle,
  panelStyle,
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
    () => filterEmploymentData(employmentData, { school: selectedSchool, industry: selectedIndustry, roleMode, currentSchool }),
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
    { title: '平均薪资', dataIndex: 'avg_salary', render: (value) => `￥${formatNumber(value, 0)}` },
  ]

  if (loading) return <div>数据加载中...</div>
  if (error && !employmentData.length) return <div style={{ color: '#ff4d4f' }}>{error}</div>

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card style={panelStyle}>
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} xl={16}><div style={sectionTitleStyle}>动态监测看板</div></Col>
            <Col xs={24} xl={8}>
              <div style={metaLabelStyle}>数据载入时间</div>
              <div style={metaValueStyle}>{dataLoadedAt || '当前会话未记录'}</div>
            </Col>
          </Row>
        </Card>
      </Col>

      <Col xs={24} md={12} xl={6}><Card style={panelStyle}><Statistic title="就业样本人数" value={overview.totalEmpCount} styles={{ title: statTitleStyle, content: statValuePrimary }} /></Card></Col>
      <Col xs={24} md={12} xl={6}><Card style={panelStyle}><Statistic title="加权平均薪资" value={Number(overview.avgSalaryWeighted.toFixed(2))} prefix="￥" styles={{ title: statTitleStyle, content: statValueBlue }} /></Card></Col>
      <Col xs={24} md={12} xl={6}><Card style={panelStyle}><Statistic title="先导产业人数" value={overview.leadEmpCount} styles={{ title: statTitleStyle, content: statValueCyan }} /></Card></Col>
      <Col xs={24} md={12} xl={6}><Card style={panelStyle}><Statistic title="覆盖专业数" value={overview.majorCount} styles={{ title: statTitleStyle, content: statValuePurple }} /></Card></Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>筛选条件</span>} style={panelStyle}>
          <Row gutter={[12, 12]}>
            {roleMode === 'gov' ? (
              <Col xs={24} md={8}>
                <Select value={selectedSchool} onChange={setSelectedSchool} style={{ width: '100%' }} options={[{ label: '全部高校', value: '全部' }, ...(options?.schools || []).map((item) => ({ label: item, value: item }))]} />
              </Col>
            ) : null}
            <Col xs={24} md={roleMode === 'gov' ? 8 : 12}>
              <Select value={selectedIndustry} onChange={setSelectedIndustry} style={{ width: '100%' }} options={[{ label: '全部行业', value: '全部' }, ...(options?.industries || []).map((item) => ({ label: item, value: item }))]} />
            </Col>
          </Row>
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>就业流向桑基图</span>} style={panelStyle}>
          <EmploymentSankey data={filteredData} style={{ height: '58vh', minHeight: 420 }} />
        </Card>
      </Col>

      <Col span={24}>
        <Card title={<span style={sectionTitleStyle}>样本明细</span>} style={panelStyle}>
          <Table columns={columns} dataSource={tableData} pagination={{ pageSize: 8 }} />
        </Card>
      </Col>
    </Row>
  )
}
