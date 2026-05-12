# QUICK_START

## 1. 配置数据库

在 `.env` 或环境变量中配置：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=bigdata
```

## 2. 一键执行完整链路

```bash
python run_full_pipeline.py
```

完整链路包含：

1. 数据集团样本数据生成
2. 初始化数据库表结构
3. 导入基础数据与岗位需求数据
4. 初始化账号、权限与审计表
5. Spark/pandas 特征加工与 ADS 聚合
6. LSTM 岗位需求人数预测
7. 协同过滤招生匹配与就业推荐
8. FP-Growth 关联规则挖掘
9. 培养方案优化建议生成
10. 结果校验与链路日志汇总

## 3. 分步运行

```bash
python platform_data_factory.py
python create_tables.py
python PutData.py
python init_security.py
python Spark-all.py
python LSTM-job-demand.py
python CF-all.py
python FPgrowth-all.py
python training_program_suggester.py
```

## 4. 启动后端

```bash
python backend/app.py
```

重点接口：

- `/api/demand/forecast`
- `/api/demand/forecast/eval`
- `/api/demand/forecast/backtest`
- `/api/supply-demand/gap`
- `/api/job-skills/heatmap`
- `/api/algorithm/chain-log`
- `/api/report`

## 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 Vite 提示的本地地址。教师端、政府端和公众端会根据账号角色展示不同模块。

## 6. 演示账号

- 教师端：`teacher_shu / 123456`
- 政府端：`gov_sh / 123456`
- 公众端：`guest / 123456`

## 7. 演示提示

正式演示建议直接执行 `python run_full_pipeline.py`，完成后打开前端查看“需求预测”“算法链路”“分析专报”和“审计日志”相关模块。
