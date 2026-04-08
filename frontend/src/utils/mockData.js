export const STATIC_RULES = [
  { antecedent: '["数据结构(>85分)", "Python编程", "算法设计"]', consequent: '["算法工程师"]', support: 0.34, confidence: 0.92, lift: 4.5 },
  { antecedent: '["机器学习", "概率统计", "线性代数"]', consequent: '["AI算法岗"]', support: 0.31, confidence: 0.89, lift: 4.1 },
  { antecedent: '["数据库系统", "JavaWeb", "软件工程"]', consequent: '["后端开发工程师"]', support: 0.29, confidence: 0.84, lift: 3.6 },
  { antecedent: '["数字电路", "嵌入式系统", "C语言"]', consequent: '["嵌入式开发工程师"]', support: 0.27, confidence: 0.82, lift: 3.3 },
  { antecedent: '["金融学", "计量经济学", "Python编程"]', consequent: '["金融数据分析师"]', support: 0.25, confidence: 0.8, lift: 3.1 },
  { antecedent: '["市场营销", "消费者行为", "数据分析"]', consequent: '["增长运营"]', support: 0.22, confidence: 0.77, lift: 2.8 },
  { antecedent: '["工业设计", "人机交互", "原型设计"]', consequent: '["UX设计师"]', support: 0.19, confidence: 0.74, lift: 2.5 },
  { antecedent: '["会计学", "审计学", "税法"]', consequent: '["审计专员"]', support: 0.16, confidence: 0.71, lift: 2.2 },
  { antecedent: '["机械原理", "制造工艺", "CAD设计"]', consequent: '["制造工程师"]', support: 0.12, confidence: 0.64, lift: 1.7 },
  { antecedent: '["新闻传播", "短视频运营", "新媒体写作"]', consequent: '["内容策划"]', support: 0.09, confidence: 0.58, lift: 1.4 },
  { antecedent: '["数据可视化", "商业分析", "SQL"]', consequent: '["BI分析师"]', support: 0.21, confidence: 0.76, lift: 2.7 },
  { antecedent: '["云计算", "Linux", "网络安全"]', consequent: '["云平台工程师"]', support: 0.18, confidence: 0.73, lift: 2.6 },
  { antecedent: '["药理学", "生物统计", "实验设计"]', consequent: '["医药研发助理"]', support: 0.14, confidence: 0.69, lift: 2.0 },
  { antecedent: '["建筑设计", "BIM", "工程制图"]', consequent: '["建筑设计师"]', support: 0.17, confidence: 0.67, lift: 1.9 },
  { antecedent: '["教育学", "课程设计", "数据分析"]', consequent: '["教育产品经理"]', support: 0.11, confidence: 0.61, lift: 1.6 },
  { antecedent: '["国际贸易", "商务英语", "Excel建模"]', consequent: '["跨境运营"]', support: 0.13, confidence: 0.63, lift: 1.7 },
  { antecedent: '["临床医学", "循证医学", "科研训练"]', consequent: '["医学研究助理"]', support: 0.08, confidence: 0.57, lift: 1.3 },
  { antecedent: '["法学", "合同法", "企业合规"]', consequent: '["法务专员"]', support: 0.15, confidence: 0.66, lift: 1.8 },
  { antecedent: '["视觉传达", "品牌策划", "AI制图"]', consequent: '["品牌设计师"]', support: 0.1, confidence: 0.6, lift: 1.5 },
  { antecedent: '["统计学", "A/B测试", "商业建模"]', consequent: '["策略分析师"]', support: 0.2, confidence: 0.78, lift: 2.9 },
]

const FORECAST_MONTHS = [
  '2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06',
  '2026-07', '2026-08', '2026-09', '2026-10', '2026-11', '2026-12',
]

export const STATIC_FORECAST_SERIES = [
  {
    track: '人工智能',
    values: [12000, 12180, 12650, 12880, 13120, 13400, 13650, 13820, 14220, 14580, 14850, 15120],
  },
  {
    track: '数据科学',
    values: [9800, 9920, 10150, 10360, 10540, 10720, 10880, 11050, 11360, 11520, 11740, 11920],
  },
  {
    track: '传统机械',
    values: [6000, 6070, 6180, 6110, 6200, 6290, 6210, 6280, 6400, 6460, 6380, 6520],
  },
]

export const STATIC_FORECAST_DATA = STATIC_FORECAST_SERIES.flatMap((series) =>
  FORECAST_MONTHS.map((month, index) => ({
    forecast_month: month,
    track: series.track,
    predicted_salary: series.values[index],
    update_time: '2026-04-08 18:00:00',
  }))
)

export const STATIC_ADMIN_STATUS = {
  lastSyncAt: '2026-04-08 17:42:00',
  successRate: 98.7,
  sources: [
    { name: '学生主数据', status: '已同步', updatedAt: '17:42:00' },
    { name: '就业事实表', status: '已同步', updatedAt: '17:40:00' },
    { name: '培养画像表', status: '校验中', updatedAt: '17:35:00' },
  ],
  logs: [
    '17:42 MySQL 抓取任务完成，新增 24 条专业画像记录。',
    '17:36 角色权限缓存刷新成功。',
    '17:22 AI 报告接口健康检查通过。',
    '17:10 前端静态资源发布成功。',
    '16:58 就业推荐表完成分块写入。',
  ],
}

export const STATIC_PUBLIC_INDUSTRIES = [
  { name: '现代金融', value: 28 },
  { name: '人工智能', value: 24 },
  { name: '智能制造', value: 18 },
  { name: '生物医药', value: 16 },
  { name: '其他行业', value: 14 },
]

export const STATIC_PUBLIC_TOP_MAJORS = [
  { major_name: '人工智能', avg_salary: 15120 },
  { major_name: '计算机科学与技术', avg_salary: 14580 },
  { major_name: '软件工程', avg_salary: 13850 },
  { major_name: '数据科学与大数据技术', avg_salary: 13220 },
  { major_name: '金融工程', avg_salary: 12860 },
]
