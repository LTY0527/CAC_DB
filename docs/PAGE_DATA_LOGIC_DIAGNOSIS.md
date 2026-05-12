# PAGE_DATA_LOGIC_DIAGNOSIS

生成时间：2026-04-28

本报告记录专项修复前的页面数据链路诊断结果，以及本轮修复的落点。原始问题不是单一前端图表问题，而是事实表规模、ADS 聚合口径、算法抽样范围、后端默认过滤、前端兜底展示之间没有闭合。

## 修复前诊断

| 检查项 | 修复前结果 | 诊断 |
|---|---:|---|
| dim_school 中上海大学 school_id | SHU007 | 学校维度存在 |
| dim_school.major_count | 86 | 学校画像符合默认教师端要求 |
| bridge_school_major 上海大学专业数 | 86 | 专业覆盖足够 |
| fact_graduate 上海大学毕业生数 | 2734 | 明显低于默认教师端展示需要 |
| fact_employment 上海大学就业记录数 | 2294 | 本校就业样本过小，截图问题成立 |
| fact_job_posting 上海大学优势专业相关岗位数 | 2888 | 岗位明细数量不足，且 demand_count 偏小 |
| fact_job_posting 上海大学优势专业相关 demand_count | 24509 | 可用总需求偏低，聚合后单组曲线贴近 0 |
| ads_job_demand_features 上海大学记录数 | 11702 | 有聚合结果，但均值仅 7.47 |
| ads_job_demand_forecast 上海大学记录数 | 60 | 仅 5 个组合 x 12 月，无法支撑 Top 8-10 曲线 |
| ads_job_demand_forecast 上海大学平均预测人数 | 12.858 | 与页面平均 12 人一致，属于算法输入和选组口径问题 |
| ads_enrollment_matching 上海大学记录数 | 5 | 只覆盖少数专业，导致“当前专业 -”、列表为空 |
| ads_major_optimization 上海大学记录数 | 5 | 专业结构建议口径不足 |
| ads_training_rules 记录数 | 262 | 有规则，但标题过长且 evidence_score 分布不够直观 |
| ads_job_recommendation 上海大学记录数 | 635 | 覆盖学生仅 127，远低于 3000 要求 |
| ads_job_recommendation 上海大学覆盖单位数 | 219 | 数据库中有单位，但前端按 recommended_job 统计导致页面可显示 0 |
| 教师端接口 | 返回数据但学校、KPI、图表口径混用 | 需要默认 SHU007 且 Top 组合口径一致 |
| 政府端接口 | 与教师端可能共用单校明细 | 需要十校汇总口径 |
| mock/fallback | 前端存在空值转 0 和 KPI / 图表不同口径问题 | 需要无数据时显示暂无数据，不补 0 |

## 根因

1. `platform_data_factory.py` 将 100000 级数据分散到多张表，上海大学单校毕业生和就业样本不足。
2. `fact_job_posting.demand_count` 偏向单条岗位记录数量，没有体现大型企业、头部企业、校招批量需求。
3. `LSTM-all.py` 只对少量全局 Top 组合预测，上海大学仅得到 60 条预测记录。
4. `CF-all.py` 从预测结果反推招生匹配，导致没有预测的专业不会出现在招生匹配和专业优化表。
5. 就业推荐混在 CF 脚本中生成，覆盖学生过少，字段与前端统计口径不一致。
6. 后端 `/api/demand/forecast`、`/api/demand/kpi` 没有区分教师端单校和政府端十校汇总。
7. 前端图表在 tooltip 和序列构造中将缺失值转为 0，规则图表横轴展示完整长规则。

## 修复落点

- 数据层：提高事实表规模，上海大学毕业生和就业样本加权，保持 86 个专业覆盖。
- 映射层：新增专业-岗位亲和逻辑，阻断临床医学/设施农业工程师、国际经济与贸易/电池研发工程师等错配。
- ADS 层：`Spark-all.py` 使用 `SUM(demand_count)` 聚合；`LSTM-all.py` 扩大上海大学 Top 组合预测。
- 招生匹配：`CF-all.py` 改为基于 `bridge_school_major` 全专业输出，上海大学不少于 60 个专业。
- 就业推荐：新增 `scripts/job_recommendation.py`，按学生生成 Top 3 推荐并保留企业字段。
- 后端：教师端默认 SHU007，政府端按十校汇总；所有接口统一返回数据库结果，不返回全 0 假数据。
- 前端：需求预测 tooltip 不再补 0；专业结构 KPI 只按当前列表主建议计数；规则图改为短标题横向条形展示。
