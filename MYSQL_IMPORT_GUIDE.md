# MySQL 数据导入使用指南

## 📋 项目概述

本项目用于将生产的四张表（dim_student、dim_company、fact_academic、fact_employment）自动导入到 MySQL 数据库中。

### 四张表说明

| 表名 | 类型 | 描述 |
|------|------|------|
| `dim_student` | 维度表 | 学生基本信息（学号、姓名、学校、专业等） |
| `dim_company` | 维度表 | 企业基本信息（企业名、规模、资本等） |
| `fact_academic` | 事实表 | 学生学业信息（专业、成绩、技能等） |
| `fact_employment` | 事实表 | 学生就业信息（薪资、参保日期、行业等） |

---

## 🚀 快速开始

### 方案 A：一键执行完整流程（推荐）

如果你想一次性完成数据生成 → 表创建 → 数据导入，运行：

```bash
python run_full_pipeline.py
```

此脚本会按顺序执行：
1. ✅ 生成 CSV 数据文件（platform_data_factory.py）
2. ✅ 创建 MySQL 表结构（create_tables.py）
3. ✅ 导入数据到数据库（PutData.py）

---

### 方案 B：分步执行（灵活）

#### 第一步：生成数据源文件

```bash
python platform_data_factory.py
```

**输出文件：**
- `dim_student.csv` (10万条学生记录)
- `fact_academic.csv` (10万条学业记录)
- `dim_company.csv` (1600个企业记录)
- `fact_employment.csv` (10万条就业记录)

---

#### 第二步：初始化数据库表结构

```bash
python create_tables.py
```

**功能：**
- 自动连接到 MySQL
- 创建/重建四张表
- 自动建立外键关联
- 设置索引优化查询性能

**输出日志示例：**
```
✓ 数据库连接引擎创建成功
【创建表】 dim_student (学生维度表)
  ✓ dim_student 表创建成功
...
✅ 所有表创建成功！
```

---

#### 第三步：导入数据到 MySQL

```bash
python PutData.py
```

**功能：**
- 读取 CSV 文件
- 执行数据清洗与转换
- 批量导入数据到数据库
- 生成详细的导入日志

**输出日志示例：**
```
【开始导入】 学生维度表 [dim_student]
  数据源文件: dim_student.csv
  → 正在读取 CSV 文件...
  ✓ 读取完成，耗时 1.23s，共 100000 条记录，11 列
  ...
✅【完成】 dim_student - 100000 条记录, 总耗时 15.34s
```

---

## ⚙️ 配置说明

### 数据库连接配置

如需修改 MySQL 连接信息，编辑：

**PutData.py**
```python
DB_CONFIG = {
    'host': 'localhost',      # MySQL 主机
    'port': 3306,             # MySQL 端口
    'user': 'root',           # 用户名
    'password': '123456',     # 密码
    'database': 'bigdata',    # 数据库名
    'charset': 'utf8mb4'
}
```

**create_tables.py** 中的配置相同，两者需保持一致。

---

## 📊 数据验证

### 方法 1：在 MySQL 中查询

```sql
-- 查询学生表数据
SELECT COUNT(*) FROM dim_student;
SELECT * FROM dim_student LIMIT 10;

-- 查询就业表数据
SELECT COUNT(*) FROM fact_employment;
SELECT COUNT(DISTINCT sh_insurance_status) FROM fact_employment;

-- 查询学业表数据
SELECT COUNT(*) FROM fact_academic;
SELECT DISTINCT skill_level FROM fact_academic;
```

### 方法 2：查看导入日志

脚本会生成日志文件：
- `mysql_import_YYYYMMDD_HHMMSS.log` - 数据导入日志
- `create_tables_YYYYMMDD_HHMMSS.log` - 表创建日志
- `pipeline_YYYYMMDD_HHMMSS.log` - 完整管道日志

---

## 🔧 高级功能

### 连接池配置

`PutData.py` 中已配置连接池以应对大数据量导入：

```python
create_engine(
    DB_CONNECTION_STRING,
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接有效性检测
    pool_recycle=3600,      # 连接回收时间（秒）
)
```

### 批量导入配置

```python
df.to_sql(
    chunksize=2000,         # 每批 2000 条记录
    method='multi'          # 使用多值 INSERT（性能优化）
)
```

---

## 📝 日志文件说明

生成的日志文件包含以下信息：

| 日志类型 | 记录内容 |
|---------|---------|
| 时间戳 | 每条日志的执行时间 |
| 日志等级 | INFO（信息）/ WARNING（警告）/ ERROR（错误） |
| 操作描述 | 具体执行的操作及结果 |
| 性能数据 | 读取、写入耗时 |

**查看日志示例：**
```bash
# Linux/Mac
tail -f mysql_import_*.log

# Windows PowerShell
Get-Content mysql_import_*.log -Tail 50 -Wait
```

---

## ⚠️ 常见问题解决

### 问题 1：连接被拒绝
```
Error: 2003: Can't connect to MySQL server on 'localhost:3306'
```

**解决方案：**
- 检查 MySQL 是否正在运行
- 检查主机/端口是否正确
- 检查用户名/密码是否正确

### 问题 2：文件编码错误
```
UnicodeDecodeError: 'utf-8' codec can't decode byte...
```

**解决方案：**
- 已自动处理（使用 `utf-8-sig` 编码）
- CSV 文件必须使用 UTF-8 编码保存

### 问题 3：表已存在
```
Error: (pymysql.err.ProgrammingError) ... existing table
```

**解决方案：**
- `create_tables.py` 会自动 DROP 旧表再创建
- 若要保留数据，参考【高级功能】中的表结构创建逻辑

### 问题 4：外键约束错误
```
Error: Cannot delete or update a parent row: a foreign key constraint fails
```

**解决方案：**
- 脚本已处理（自动禁用/启用外键检查）
- 若手动操作，使用：`SET FOREIGN_KEY_CHECKS = 0;`

---

## 🎯 性能指标

基于 10 万条学生记录的测试数据：

| 操作 | 耗时 | 备注 |
|------|------|------|
| CSV 读取 | ~1-2s | 取决于磁盘 I/O |
| 数据清洗 | ~0.5s | 仅对日期转换 |
| 批量导入 | ~10-15s | 取决于网络和 MySQL 配置 |
| **总耗时** | **~12-18s** | 四张表合计 |

---

## 📚 依赖包

```
pandas>=1.3.0
sqlalchemy>=1.4.0
pymysql>=1.0.0
```

**安装依赖：**
```bash
pip install -r backend/requirements.txt
```

或单独安装：
```bash
pip install pandas sqlalchemy pymysql
```

---

## 🔐 安全建议

1. **不要在代码中提交真实密码** - 使用环境变量
2. **生产环境** - 使用专用数据库用户（最小权限原则）
3. **备份** - 导入前备份重要数据
4. **验证** - 导入后验证数据完整性

**使用环境变量（推荐）：**
```python
import os

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'bigdata'),
}
```

---

## 📞 技术支持

如有问题，请：
1. 查看生成的日志文件
2. 检查 MySQL 错误日志：`SELECT * FROM INFORMATION_SCHEMA.TABLES`
3. 验证网络连接和权限

---

## 📜 版本历史

**v2.0（当前）**
- ✨ 新增自动表创建脚本（create_tables.py）
- ✨ 新增完整流程脚本（run_full_pipeline.py）
- 🔧 改进日志记录和错误处理
- 🚀 优化批量导入性能
- 📝 添加数据库初始化注释

**v1.0**
- 基础数据导入功能

---

**最后更新：2026-04-08**

---

## 2026-04-12 更新说明（按当前代码为准）

以下内容为补充说明，优先级高于本文前面提到的“直接修改 `PutData.py` / `create_tables.py` 数据库配置”的旧做法。

### 1. 数据库配置已统一收口到 `config.py`

当前数据库连接配置统一从 [config.py](/e:/Code/CAC/config.py) 读取，`create_tables.py`、`PutData.py`、`backend/app.py`、`CF-all.py`、`FPgrowth-all.py`、`LSTM-all.py` 等脚本都会直接或间接使用这里的配置。

当前支持的环境变量如下：

```powershell
DB_HOST
DB_PORT
DB_USER
DB_PASSWORD
DB_NAME
DB_CHARSET
DB_JDBC_DRIVER
```

推荐在 PowerShell 中先设置当前会话变量，再执行脚本：

```powershell
$env:DB_HOST="localhost"
$env:DB_PORT="3306"
$env:DB_USER="root"
$env:DB_PASSWORD="你的数据库密码"
$env:DB_NAME="bigdata"
```

验证当前脚本读取到的数据库配置：

```powershell
python -c "from config import DB_SETTINGS; print(DB_SETTINGS)"
```

说明：
- 如果没有设置环境变量，`config.py` 会回退到默认值。
- 如果密码中包含 `@`、空格、`:` 等特殊字符，当前代码已在 `config.py` 中统一做 URL 编码处理，不需要再手动改连接串。

### 2. 当前推荐的一键导入方式

当前项目已经提供完整流水线脚本 [run_full_pipeline.py](/e:/Code/CAC/run_full_pipeline.py)。

执行命令：

```powershell
python run_full_pipeline.py
```

该脚本当前会依次执行：

1. `platform_data_factory.py`
2. `create_tables.py`
3. `PutData.py`
4. `init_security.py`
5. `Spark-all.py`
6. `LSTM-all.py`
7. `CF-all.py`
8. `FPgrowth-all.py`

也就是说，它不仅会导入基础表，还会初始化系统账号表，并生成 `ads_*` 分析结果表。

### 3. 运行前需要额外确认的环境

除 Python 依赖外，还需要确认以下本地环境：

- MySQL 服务已启动，且 `bigdata` 数据库可访问
- Spark / Java 环境可用
- MySQL JDBC jar 已存在于 `libs` 目录

当前默认 jar 路径：

```text
E:\Code\CAC\libs\mysql-connector-java-8.0.11.jar
```

如果文件名不同，需要同步修改 [config.py](/e:/Code/CAC/config.py) 中的 `JAR_PATH`。

### 4. 当前需要验证的核心结果表

基础表：

```sql
SELECT COUNT(*) FROM dim_student;
SELECT COUNT(*) FROM dim_company;
SELECT COUNT(*) FROM fact_academic;
SELECT COUNT(*) FROM fact_employment;
```

分析结果表：

```sql
SELECT COUNT(*) FROM ads_job_demand_forecast;
SELECT COUNT(*) FROM ads_enrollment_matching;
SELECT COUNT(*) FROM ads_major_matching_rules;
SELECT COUNT(*) FROM ads_job_recommendation;
```

如果前端页面出现“数据异常”，优先检查以上 `ads_*` 表是否存在且有数据。
