import { DashboardOutlined, FileTextOutlined, GlobalOutlined, LineChartOutlined, TeamOutlined, ThunderboltOutlined } from '@ant-design/icons'

export const ROLE_CONFIGS = {
  teacher: {
    label: '学校老师',
    title: '高校招生培养就业一体化分析平台',
    subtitle: '面向学校专业建设、招生调控与培养优化的校内决策视图',
    headerTitle: (school) => `${school}专业建设与就业联动分析平台`,
    headerSubtitle: '聚焦专业层面的招生、培养、就业与监测结果，服务于学校宏观调控',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '校内总览' },
      { key: '/employment', icon: <LineChartOutlined />, label: '就业监测' },
      { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测' },
      { key: '/enrollment', icon: <TeamOutlined />, label: '招生分析' },
      { key: '/rules', icon: <ThunderboltOutlined />, label: '培养关联' },
      { key: '/major-optimization', icon: <TeamOutlined />, label: '专业优化' },
      { key: '/report', icon: <FileTextOutlined />, label: '分析专报' },
    ],
  },
  gov: {
    label: '政府管理人员',
    title: '上海高校治理分析平台',
    subtitle: '面向全市高校结构调整与专业布局优化的治理视图',
    headerTitle: () => '上海市高校招生培养就业治理平台',
    headerSubtitle: '围绕全市高校、产业需求与专业布局，支撑政府宏观决策',
    defaultPath: '/dashboard',
    menuItems: [
      { key: '/dashboard', icon: <DashboardOutlined />, label: '全市总览' },
      { key: '/employment', icon: <LineChartOutlined />, label: '高校对比' },
      { key: '/forecast', icon: <LineChartOutlined />, label: '需求预测' },
      { key: '/rules', icon: <ThunderboltOutlined />, label: '培养关联' },
      { key: '/major-optimization', icon: <TeamOutlined />, label: '专业优化' },
      { key: '/report', icon: <FileTextOutlined />, label: '治理专报' },
    ],
  },
  public: {
    label: '社会公众',
    title: '上海高校专业发展公开门户',
    subtitle: '面向考生与公众展示高校专业发展与就业结果',
    headerTitle: () => '上海高校专业发展公开展示平台',
    headerSubtitle: '围绕宏观就业、热门行业和院校优势专业提供公开信息参考',
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
