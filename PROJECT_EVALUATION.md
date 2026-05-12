# PROJECT_EVALUATION

## 评价结论

CAC_DB 已从偏“薪资预测/就业分析”的实现升级为“基于数据集团海量多源异构数据的高校需求—招生—培养—就业—监测一体化平台”。系统具备清晰的数据仓库分层、算法链路闭环、前后端展示和安全审计能力，适合本科毕设、课程设计或比赛答辩展示。

## 数据库应用系统特色

- 数据来源强调数据集团企业招聘库、社保就业库、公开招聘平台和行业协会数据。
- 数据层包含 ODS、DIM、FACT、ADS、SYS 多层表结构。
- `ods_cleaning_log` 记录清洗、去重、缺失值、异常值和标准化过程。
- `ads_algorithm_chain_log` 记录每个算法阶段的输入表、输出表、算法名称、运行状态和耗时。
- `sys_user_account` 与 `sys_audit_log` 支持登录加密、角色权限和操作审计。

## 算法链路闭环

1. `fact_job_demand` 存储岗位招聘需求。
2. `Spark-all.py` 生成岗位月度需求、技能热力和专业供需缺口。
3. `LSTM-job-demand.py` 预测未来 12 个月岗位需求人数。
4. `CF-all.py` 使用预测需求权重生成招生匹配与就业推荐。
5. `FPgrowth-all.py` 挖掘专业—岗位—技能—行业关联规则。
6. `training_program_suggester.py` 生成培养方案优化建议。
7. 后端和前端按教师端、政府端、公众端分角色展示。

## 验收点

- `python create_tables.py` 可创建核心表。
- `python platform_data_factory.py` 可生成五类 CSV。
- `python PutData.py` 可导入数据并写入清洗日志。
- `python Spark-all.py` 可生成 ADS 聚合表。
- `python LSTM-job-demand.py` 可生成岗位需求预测、评估和回测表。
- `python CF-all.py` 可生成需求牵引招生匹配和就业推荐表。
- `python FPgrowth-all.py` 可生成关联规则表。
- `python training_program_suggester.py` 可生成培养方案建议表。
- `python run_full_pipeline.py` 可执行完整链路。
- 前端不再以“预测薪资趋势”作为核心模块标题，需求预测统一展示为“岗位需求人数预测”。

## 答辩建议

讲述主线建议聚焦：

“数据集团多源异构数据接入 → 清洗与标准化 → MySQL 数据仓库 → Spark 特征加工 → LSTM 岗位需求人数预测 → 协同过滤招生匹配 → 余弦相似度就业推荐 → FP-Growth 关联规则 → 培养方案优化 → 分角色可视化 → 审计日志追踪。”
