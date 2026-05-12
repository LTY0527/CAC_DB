# REFACTOR_REPORT

## 删除的文件列表

- `frontend/src/utils/mockData.js`
- `frontend/src/pages/AIReport.jsx`
- `frontend/src/pages/SalaryForecast.jsx`
- `frontend/src/assets/mock/employment_summary.json`
- `frontend/src/assets/mock/enrollment_matching.json`
- `frontend/src/assets/mock/job_recommendation.json`
- `frontend/src/assets/mock/major_matching_rules.json`
- `frontend/src/assets/mock/salary_forecast.json`

## 合并与新增的文件

- 新增 `app.py`：统一 Flask API 入口，返回 `{ code, message, data }`。
- 新增 `scripts/platform_data_factory.py`：新版底层数据生成。
- 新增 `scripts/create_tables.py`：新版 MySQL 分层表结构。
- 新增 `scripts/PutData.py`：新版 CSV 导入与基础质量校验。
- 新增 `scripts/Spark-all.py`：岗位需求预测特征聚合。
- 新增 `scripts/LSTM-all.py`：岗位需求人数预测与回测评估。
- 新增 `scripts/CF-all.py`：招生匹配、专业结构建议、就业推荐。
- 新增 `scripts/FPgrowth-all.py`：培养方案规则挖掘。
- 新增 `scripts/check_data_quality.py`：自动化验收检查。
- 新增 `scripts/init_security.py`：安全账户初始化。
- 新增 `scripts/data_seed/school_profiles.py`：10 所上海高校画像。
- 新增 `scripts/data_seed/major_catalog_2025.py`：845 个本科专业目录生成。
- 新增 `config/job_taxonomy.yaml`：90 个岗位类别与多元行业分类。
- 新增 `frontend/src/pages/DemandForecast.jsx`：替换旧预测页面。

## 重命名的接口

- `/api/demand/forecast`：岗位需求人数预测。
- `/api/demand/kpi`：预测 KPI。
- `/api/enrollment/matching`：招生匹配。
- `/api/major/optimization`：专业结构调整建议。
- `/api/training/rules`：培养方案规则。
- `/api/recommendation/jobs`：就业推荐。
- `/api/monitor/school`：公开监测与政府预警。
- `/api/report/ai`：智能专报。
- `/api/audit/logs`：审计日志。

## 保留的兼容项

- `/api/enrollment-matching`
- `/api/major-structure-advice`
- `/api/major-matching-rules`
- `/api/job-recommendation`
- `/api/regional-warnings`
- `/api/report`
- `/api/report/generate`

这些路径仅用于兼容现有前端路由和历史调用，主链路已切换到新版接口。

## 可能影响的功能

- 旧版本地 JSON mock 数据已删除，前端必须连接后端和 MySQL。
- 旧版薪资预测主链路已移除，薪资仅作为平均薪资、就业质量等辅助指标展示。
- 根目录旧脚本仍保留为历史文件，但正式运行链路使用 `scripts/` 目录。

## 如何回滚

1. 使用 Git 回滚本次新增的 `scripts/`、`config/`、`data/`、`app.py`、报告文件和前端删除项。
2. 恢复旧前端 `SalaryForecast.jsx` 与 `mockData.js`。
3. 使用旧根目录 `create_tables.py`、`PutData.py`、`Spark-all.py`、`LSTM-all.py` 等脚本重建旧表。

## 验证结果

- `npm run build` 通过。
- 新版 API 扫描通过。
- 完整链路命令通过。
- `scripts/check_data_quality.py` 全部通过。
