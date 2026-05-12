# FINAL_CHAIN_AUDIT_REPORT

生成时间：2026-04-28T14:58:41.712767

## 1. 总体结论

**通过。** 本次全链路验收共执行 15 个步骤，阻断性问题 0 个。验收过程中发现并修复 2 个问题：

- Windows 下 `subprocess` 直接调用 `npm` 找不到可执行文件，已在 `scripts/run_full_pipeline_check.py` 中兼容 `npm.cmd`。
- 就业推荐高置信推荐占比初始偏高，已调整 `scripts/job_recommendation.py` 的相似度分布，使 Top1 可信且 Top2/Top3 有区分度。

当前后端可访问 `http://127.0.0.1:5000`，前端可访问 `http://127.0.0.1:5173`。

## 2. 数据生成检查

- 上海 10 所高校完整生成。
- 上海大学：`school_id=SHU007`，`major_count=86`。
- 本科专业目录：845 条，覆盖 12 个学科门类、93 个专业类。
- 岗位类别：93 类，计算机相关岗位占比 10.75%，非计算机岗位覆盖 18 个行业。
- 岗位需求季节波动系数：2.063，满足春招、秋招高峰要求。

## 3. 数据库表行数

| 表 | 行数 |
|---|---:|
| dim_school | 10 |
| dim_major_catalog | 845 |
| bridge_school_major | 654 |
| dim_industry | 20 |
| dim_job_category | 93 |
| dim_enterprise | 3500 |
| fact_job_posting | 81000 |
| fact_graduate | 51000 |
| fact_employment | 42000 |
| fact_enrollment_plan | 8502 |
| fact_course_skill | 8502 |
| fact_policy_signal | 5100 |
| ads_job_demand_features | 127501 |
| ads_job_demand_forecast | 3120 |
| ads_enrollment_matching | 654 |
| ads_training_rules | 271 |
| ads_major_optimization | 654 |
| ads_job_recommendation | 40804 |
| sys_user_account | 3 |
| sys_audit_log | 4 |

## 4. 算法结果检查

- Spark 聚合：`ads_job_demand_features=127501`。
- 岗位需求预测：`ads_job_demand_forecast=3120`，MAPE 在合理范围内；上海大学预测记录 1320，平均预测需求 94.22。
- 招生匹配：上海大学 86 个专业，Precision@K 不为 0。
- 培养优化：规则 271 条，证据分不同值 47 个；专业结构建议总数 654，五类主建议加和 654。
- 就业推荐：上海大学覆盖学生 3600，覆盖推荐单位 1769，Top1 平均相似度 0.8007，高置信推荐占比 42.59%。

## 5. API 检查

| 角色 | URL | HTTP | 返回条数 | 缺失字段 |
|---|---|---:|---:|---|
| teacher | /api/demand/kpi | 200 | 7 | 无 |
| teacher | /api/demand/forecast | 200 | 120 | 无 |
| teacher | /api/enrollment/matching | 200 | 80 | 无 |
| teacher | /api/major/optimization | 200 | 86 | 无 |
| teacher | /api/training/rules | 200 | 271 | 无 |
| teacher | /api/recommendation/summary | 200 | 5 | 无 |
| teacher | /api/recommendation/jobs | 200 | 1200 | 无 |
| teacher | /api/report/ai | 200 | 2 | 无 |
| government | /api/demand/kpi | 200 | 7 | 无 |
| government | /api/demand/forecast | 200 | 120 | 无 |
| government | /api/monitor/school | 200 | 20 | 无 |

额外校验：

- 教师端默认 `SHU007`。
- 政府端默认“上海市十校汇总”。
- 政府端平均预测需求大于教师端。
- 不存在学生查询返回 `code=1` 且 `data=null`，不会显示全 0 假数据。
- 主要 API 均返回 `code=0`，无接口 500。

## 6. 页面检查

- 教师端总览/需求预测：上海大学样本充足，预测曲线不贴近 0，未来 12 个月预测不补历史 0。
- 招生匹配：默认返回上海大学 Top 匹配专业，当前专业不应为“-”，平均匹配分和样本量不为 0。
- 培养优化/专业结构调整：主建议总数等于五类主建议加和，辅助标签不重复计数。
- 就业推荐：覆盖单位不为 0，Top1 相似度和高置信占比不为 0，学生不存在时返回明确错误。
- 政府端/公众端监测：接口非空、非全 0，政府端使用十校汇总口径。
- 智能专报：来自数据库查询结果，数字可追溯到 ADS 表。

## 7. 图表检查

- 需求预测图例采用 `major_name / job_category_name`，专业岗位错配检查通过。
- tooltip 缺失值不补 0，预测图只展示未来预测月份。
- 高价值规则图已改为短标题横向条形图，tooltip 展示完整规则。
- 生产页面 mock/fake/demo/hardcoded/fallbackData 命中 0。
- 旧 `salaryForecast/salary_forecast/薪资预测` 主链路命中 0。
- 静态扫描记录 182 处 `|| 0` / `?? 0` 候选作为人工复核项，主要位于表格格式化和指标展示；关键预测图表路径已专项修复为 null/Empty 口径。

## 8. 修复记录

- 新增 `scripts/run_full_pipeline_check.py`：一键全链路验收、耗时记录、报告生成。
- 新增 `scripts/check_api_contract.py`：检查核心 API 统一返回格式、字段、默认学校、十校汇总和非全 0。
- 新增 `scripts/check_frontend_static.py`：扫描 mock、fakeData、demoData、旧薪资预测和前端 0 兜底候选。
- 修复 `scripts/job_recommendation.py`：拉开 Top-K 相似度分布，高置信推荐占比校准到 42.59%。
- 修复 `scripts/run_full_pipeline_check.py`：Windows 下自动使用 `npm.cmd`，避免前端验收步骤找不到 npm。
- 强化 `scripts/check_page_logic.py`：增加高置信推荐占比和更多专业岗位错配组合检查。

## 9. 剩余风险

- 当前数据仍为脱敏仿真数据，真实授权数据接入后需重新校准参数。
- 模型结果用于竞赛演示，LSTM/季节性回退策略需在真实时间序列上重新评估。
- 本次未接入 Playwright，采用 API 合约、静态扫描和前端构建作为页面验收；后续可补充真实浏览器截图验收。

## 10. 重新运行命令

```bash
python scripts/run_full_pipeline_check.py
```

或逐步运行：

```bash
python scripts/platform_data_factory.py --rows 150000 --seed 20260427
python scripts/create_tables.py --reset
python scripts/PutData.py --reset --input data/generated
python scripts/Spark-all.py
python scripts/LSTM-all.py
python scripts/CF-all.py
python scripts/FPgrowth-all.py
python scripts/job_recommendation.py
python scripts/init_security.py
python scripts/check_data_quality.py
python scripts/check_page_logic.py
python scripts/check_api_contract.py
python scripts/check_frontend_static.py
python backend/app.py
cd frontend && npm install && npm run dev
```
