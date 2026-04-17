export const metricInsightMap = {
  school: {
    school_employment_samples: {
      title: '本校就业样本',
      summary: '反映当前学校纳入分析的就业样本数量，是判断后续结论稳定性的基础指标。',
      scope: '当前学校纳入统计的就业样本',
      interpretation: '数值越大，说明当前学校可用于就业分析的样本越充分；如果样本偏少，结论更适合结合专业明细进一步查看。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断本校就业分析、专业画像和培养调整建议是否具有稳定参考价值。',
      definition: '按当前学校口径汇总已纳入平台分析的就业记录数量。',
      dataSource: '就业去向汇总数据与学校维度统计结果。',
      dimensions: ['学校', '专业', '毕业去向', '行业'],
      apiPath: '/api/employment-summary',
      notes: '适合与平均薪资、覆盖专业数一起综合判断，不建议单独解读。',
    },
    school_avg_salary: {
      title: '本校平均薪资',
      summary: '反映当前学校就业样本的整体薪资水平，可用于观察就业质量的总体表现。',
      scope: '当前学校就业样本',
      interpretation: '该指标适合看整体水平，不代表所有专业都处于同一薪资区间，建议结合专业分布和行业结构一起理解。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断本校专业培养与岗位需求匹配程度，以及不同专业群的就业质量差异。',
      definition: '按当前学校就业样本计算的平均薪资结果。',
      dataSource: '就业去向汇总数据中的薪资字段。',
      dimensions: ['学校', '专业', '行业', '地区'],
      apiPath: '/api/employment-summary',
      notes: '薪资受行业分布、地区流向和样本规模影响较大，适合做趋势和结构比较。',
    },
    school_lead_industry_employment: {
      title: '先导产业吸纳人数',
      summary: '反映本校毕业生进入重点产业方向的人数，帮助观察培养与重点产业需求的衔接情况。',
      scope: '当前学校就业样本中的重点产业去向',
      interpretation: '数值越高，通常说明学校与重点产业方向的衔接更紧密，但仍需结合专业结构和总样本一起看。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断学校重点专业建设、产教协同和就业导向是否有效支撑重点产业需求。',
      definition: '按先导产业目录筛选后统计当前学校对应就业人数。',
      dataSource: '就业去向汇总数据与重点产业分类结果。',
      dimensions: ['学校', '专业', '重点产业方向'],
      apiPath: '/api/employment-summary',
      notes: '更适合做专业群对比或年度趋势观察。',
    },
    school_major_coverage: {
      title: '覆盖专业数',
      summary: '反映当前学校已有就业样本支撑分析的专业数量。',
      scope: '当前学校纳入就业统计的专业范围',
      interpretation: '覆盖专业越多，说明学校层面的分析视角越完整；如果覆盖较少，部分专业可能暂未纳入充分观察。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断学校在专业建设、培养调整和就业监测上的观察覆盖面是否充分。',
      definition: '对当前学校就业样本中的专业名称去重后得到的数量。',
      dataSource: '就业去向汇总数据中的专业字段。',
      dimensions: ['学校', '专业'],
      apiPath: '/api/employment-summary',
      notes: '建议与就业样本数量结合解读，避免只看覆盖数不看样本基础。',
    },
  },
  gov: {
    gov_school_coverage: {
      title: '覆盖高校数',
      summary: '反映当前全市监测范围内已经纳入平台分析的高校数量。',
      scope: '当前全市高校监测范围',
      interpretation: '数值越高，说明平台对全市高校的覆盖越充分；如果覆盖不足，横向比较的完整性会受到影响。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断全市监测范围、结构比较和治理分析的覆盖基础是否完整。',
      definition: '对纳入就业统计的高校名称去重后得到的数量。',
      dataSource: '全市就业去向汇总数据。',
      dimensions: ['高校', '专业', '行业'],
      apiPath: '/api/employment-summary',
      notes: '适合与全市就业样本、高校对比结果一起查看。',
    },
    gov_employment_samples: {
      title: '全市就业样本',
      summary: '反映当前全市高校纳入监测分析的就业样本规模，是治理判断的重要基础。',
      scope: '全市高校监测样本',
      interpretation: '样本越充分，越适合用于观察结构差异、产业吸纳和区域比较；样本不足时应谨慎做横向判断。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断全市高校就业结构、专业布局与区域治理研判的分析可靠性。',
      definition: '按全市口径汇总已纳入平台分析的就业记录数量。',
      dataSource: '全市就业去向汇总数据。',
      dimensions: ['高校', '专业', '地区', '行业'],
      apiPath: '/api/employment-summary',
      notes: '适合与高校覆盖数、平均薪资、重点产业人数一起综合查看。',
    },
    gov_avg_salary: {
      title: '全市平均薪资',
      summary: '反映全市高校样本的整体薪资水平，可用于观察区域就业质量与结构变化。',
      scope: '全市高校就业样本',
      interpretation: '该指标更适合看整体趋势和结构比较，不宜直接替代单校或单专业的具体判断。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断全市就业质量变化、专业结构调整方向以及重点行业吸纳情况。',
      definition: '按全市就业样本计算的平均薪资结果。',
      dataSource: '全市就业去向汇总数据中的薪资字段。',
      dimensions: ['高校', '专业', '行业', '地区'],
      apiPath: '/api/employment-summary',
      notes: '建议与产业分布、高校差异和专业结构一起解读。',
    },
    gov_lead_industry_employment: {
      title: '先导产业吸纳人数',
      summary: '反映全市高校毕业生流向重点产业的人数，体现高校供给与重点产业需求的衔接情况。',
      scope: '全市高校重点产业去向样本',
      interpretation: '数值越高，通常说明重点产业对高校毕业生吸纳能力较强，但仍需结合产业结构和高校差异理解。',
      updatedAt: '由 Dashboard 传入的数据更新时间补充',
      decisionHint: '可辅助判断全市专业布局、重点产业人才供给和治理优化重点。',
      definition: '按先导产业目录筛选后统计全市高校对应就业人数。',
      dataSource: '全市就业去向汇总数据与重点产业分类结果。',
      dimensions: ['高校', '专业', '重点产业方向'],
      apiPath: '/api/employment-summary',
      notes: '适合与区域需求预测、高校对比结果联动查看。',
    },
  },
  public: {},
}

export function getMetricInsight(roleMode, metricKey, context = {}) {
  const matched = metricInsightMap[roleMode]?.[metricKey]
  if (!matched) return null

  const scopeLabel =
    matched.scope === '当前学校纳入统计的就业样本' && context.currentSchool
      ? `${context.currentSchool}就业样本`
      : matched.scope

  return {
    ...matched,
    scope: scopeLabel,
    updatedAt: context.dataLoadedAt || matched.updatedAt,
  }
}
