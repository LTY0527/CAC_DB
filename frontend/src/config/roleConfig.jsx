import {
  DashboardOutlined,
  FileTextOutlined,
  GlobalOutlined,
  LineChartOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'

export const ROLE_CONFIGS = {
  teacher: {
    label: '学校教师',
    title: '高校人才培养与就业大数据平台',
    subtitle: '围绕招生、培养、就业与动态监测的一体化分析平台',
    headerTitle: (school) => `${school} 人才培养与就业联动分析`,
    headerSubtitle: '支持专业建设、招生优化、培养调整与就业质量跟踪',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '平台总览' },
      { key: '/employment', icon: <LineChartOutlined />, label: '动态监测看板' },
      { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测（LSTM）' },
      { key: '/enrollment', icon: <TeamOutlined />, label: '招生匹配（协同过滤）' },
      { key: '/rules', icon: <ThunderboltOutlined />, label: '规则证据库' },
      { key: '/major-optimization', icon: <TeamOutlined />, label: '培养方案优化' },
      { key: '/job-recommendation', icon: <ThunderboltOutlined />, label: '就业推荐（余弦）' },
      { key: '/report', icon: <FileTextOutlined />, label: '分析专报' },
    ],
  },
  gov: {
    label: '政府管理人员',
    title: '高校人才培养与就业大数据平台',
    subtitle: '面向区域高校治理与专业结构优化的决策支持平台',
    headerTitle: () => '上海市高校人才培养与就业治理驾驶舱',
    headerSubtitle: '关注高校结构、产业需求、培养质量与就业流向变化',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '平台总览' },
      { key: '/employment', icon: <LineChartOutlined />, label: '动态监测看板' },
      { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测（LSTM）' },
      { key: '/rules', icon: <ThunderboltOutlined />, label: '规则证据库' },
      { key: '/major-optimization', icon: <TeamOutlined />, label: '培养方案优化' },
      { key: '/job-recommendation', icon: <ThunderboltOutlined />, label: '就业推荐（余弦）' },
      { key: '/report', icon: <FileTextOutlined />, label: '治理专报' },
    ],
  },
  public: {
    label: '社会公众',
    title: '高校人才培养与就业大数据平台',
    subtitle: '面向考生与社会公众展示高校专业发展与就业结果',
    headerTitle: () => '上海高校专业发展公开展示平台',
    headerSubtitle: '公开展示就业质量、专业结构与高校对比信息',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <GlobalOutlined />, label: '门户首页' },
      { key: '/school-compare', icon: <TeamOutlined />, label: '院校对比' },
    ],
  },
}

export function getDefaultPathByRole(role) {
  return ROLE_CONFIGS[role]?.defaultPath || '/dashboard'
}
