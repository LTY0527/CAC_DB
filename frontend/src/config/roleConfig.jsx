import {
  DashboardOutlined,
  FileTextOutlined,
  GlobalOutlined,
  LineChartOutlined,
  PartitionOutlined,
  TeamOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'

export const SHARED_PLATFORM_TITLE = '基于大数据高校“需求-招生-培养-就业-监测”一体化平台'
const SYSTEM_HEADER_TITLE = '“需求-招生-培养-就业-监测”一体化平台'

export const ROLE_CONFIGS = {
  teacher: {
    label: '学校教师',
    title: SHARED_PLATFORM_TITLE,
    subtitle: '',
    headerTitle: () => SYSTEM_HEADER_TITLE,
    headerSubtitle: '',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '总览' },
      { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测' },
      { key: '/enrollment', icon: <TeamOutlined />, label: '招生匹配' },
      { key: '/job-recommendation', icon: <ThunderboltOutlined />, label: '就业推荐' },
      { key: '/major-optimization', icon: <TeamOutlined />, label: '培养优化' },
      { key: '/rules', icon: <PartitionOutlined />, label: '关联规则' },
      { key: '/report', icon: <FileTextOutlined />, label: '分析专报' },
    ],
  },
  gov: {
    label: '政府管理人员',
    title: SHARED_PLATFORM_TITLE,
    subtitle: '',
    headerTitle: () => SYSTEM_HEADER_TITLE,
    headerSubtitle: '',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '总览' },
      { key: '/forecast', icon: <LineChartOutlined />, label: '需求趋势' },
      { key: '/rules', icon: <PartitionOutlined />, label: '规则证据' },
      { key: '/major-optimization', icon: <TeamOutlined />, label: '培养优化' },
      { key: '/job-recommendation', icon: <ThunderboltOutlined />, label: '就业推荐' },
      { key: '/report', icon: <FileTextOutlined />, label: '分析专报' },
    ],
  },
  public: {
    label: '社会公众',
    title: SHARED_PLATFORM_TITLE,
    subtitle: '',
    headerTitle: () => SYSTEM_HEADER_TITLE,
    headerSubtitle: '',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <GlobalOutlined />, label: '公开首页' },
      { key: '/school-compare', icon: <TeamOutlined />, label: '院校对比' },
    ],
  },
}

export function getDefaultPathByRole(role) {
  return ROLE_CONFIGS[role]?.defaultPath || '/dashboard'
}
