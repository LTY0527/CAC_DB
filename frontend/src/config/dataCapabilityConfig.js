export const baseDataCapabilityItems = [
  {
    key: 'student-basic',
    title: '学生基础',
    fields: ['学校', '学历', '专业', '生源地'],
    description: '支撑需求预测与招生匹配，便于查看样本来源和结构分布。',
  },
  {
    key: 'training-process',
    title: '培养过程',
    fields: ['学科门类', '技能等级', '课程方向'],
    description: '支撑培养优化，便于定位课程设置与能力结构的调整重点。',
  },
  {
    key: 'employment-result',
    title: '就业结果',
    fields: ['行业', '岗位', '起薪', '社保状态'],
    description: '支撑就业推荐与结果跟踪，便于判断就业质量和去向稳定性。',
  },
  {
    key: 'enterprise-profile',
    title: '企业画像',
    fields: ['企业类型', '企业规模', '区域', '产业标签'],
    description: '支撑区域监测与校企匹配，便于观察岗位吸纳结构和产业去向。',
  },
]

export const teacherDataCapabilityConfig = {
  title: '本校分析覆盖的数据能力',
  items: baseDataCapabilityItems,
}

export const governmentDataCapabilityConfig = {
  title: '区域监测覆盖的数据能力',
  items: baseDataCapabilityItems,
}
