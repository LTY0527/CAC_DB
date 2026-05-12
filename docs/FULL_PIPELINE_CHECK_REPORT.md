# FULL_PIPELINE_CHECK_REPORT

生成时间：2026-04-28T14:58:41.712767

## 总体结论

通过

## 执行步骤

- [x] 生成数据：531.93s
- [x] 创建数据库表：1.92s
- [x] 导入数据：33.02s
- [x] Spark 聚合：31.55s
- [x] 岗位需求预测：10.46s
- [x] 招生匹配：1.7s
- [x] 培养方案优化：1.47s
- [x] 就业推荐：61.75s
- [x] 初始化安全表：0.9s
- [x] 数据质量检查：0.66s
- [x] 页面逻辑检查：1.1s
- [x] API 合约检查：0.99s
- [x] 前端静态扫描：0.09s
- [x] 前端依赖安装：18.31s
- [x] 前端构建检查：1.53s

## 数据库表行数

- dim_school: 10
- dim_major_catalog: 845
- bridge_school_major: 654
- dim_industry: 20
- dim_job_category: 93
- dim_enterprise: 3500
- fact_job_posting: 81000
- fact_graduate: 51000
- fact_employment: 42000
- fact_enrollment_plan: 8502
- fact_course_skill: 8502
- fact_policy_signal: 5100
- ads_job_demand_features: 127501
- ads_job_demand_forecast: 3120
- ads_enrollment_matching: 654
- ads_training_rules: 271
- ads_major_optimization: 654
- ads_job_recommendation: 40804
- sys_user_account: 3
- sys_audit_log: 4

## 关键指标

- shu_graduate_count: 18933
- shu_employment_count: 18543
- shu_forecast_count: 1320
- shu_forecast_avg: 94.22
- shu_enrollment_matching_count: 86
- shu_major_optimization_count: 86
- shu_recommendation_students: 3600
- shu_recommendation_enterprises: 1769
- top1_similarity: 0.8007
- training_rule_count: 271
- evidence_distinct: 47
- optimization_total: 654
- optimization_primary_sum: 654

## 主要 API 返回条数

见 `data/generated/api_contract_report.json`。

## 前端页面检查结果

静态扫描和构建检查已执行，见 `docs/FRONTEND_STATIC_CHECK_REPORT.md`。

## 发现的问题

- 未发现阻断性问题

## 自动修复的问题

- 本次验收脚本未执行额外自动修复；已通过现有链路修复结果复核

## 仍需人工确认的问题

- 数据为脱敏仿真数据，真实接入后需重新校准模型参数。
- 前端自动化为静态扫描和构建检查；如后续加入 Playwright，可补充真实浏览器截图验收。
