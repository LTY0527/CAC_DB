# CAC_DB

基于大数据高校“需求-招生-培养-就业-监测”一体化平台。

## 快速启动

Windows 终端建议先切换 UTF-8，避免中文日志乱码：

```bat
chcp 65001
```

后端和脚本统一读取 `backend/.env` 中的数据库配置：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=bigdata
DB_CHARSET=utf8mb4
```

首次运行或表结构不一致时：

```bash
python scripts/migrate_schema.py
python scripts/check_schema.py
python scripts/init_security.py
python backend/app.py
```

完整数据链路：

```bash
python scripts/platform_data_factory.py --rows 100000 --seed 20260427
python scripts/create_tables.py --reset
python scripts/PutData.py --reset --input data/generated
python scripts/Spark-all.py
python scripts/LSTM-all.py
python scripts/CF-all.py
python scripts/FPgrowth-all.py
python scripts/init_security.py
python backend/app.py
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 默认账户

- 教师端：`teacher_shu / 123456`
- 政府端：`gov_sh / 123456`
- 公众端：`guest / 123456`

## 核心表

- DIM：`dim_school`、`dim_major_catalog`、`dim_industry`、`dim_job_category`、`dim_enterprise`
- FACT：`fact_job_posting`、`fact_graduate`、`fact_employment`、`fact_enrollment_plan`、`fact_course_skill`、`fact_policy_signal`
- ADS：`ads_job_demand_features`、`ads_job_demand_forecast`、`ads_enrollment_matching`、`ads_training_rules`、`ads_major_optimization`、`ads_job_recommendation`
- SYS：`sys_user_account`、`sys_audit_log`

## 安全与审计

登录账户只保存 `password_hash`，并记录 `hash_algo`、`hash_version`。后端启动时会执行轻量 schema 检查和幂等迁移，补齐安全表缺失字段，但不会重建或清空业务数据。
