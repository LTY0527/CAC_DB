# 快速参考 - MySQL 数据导入
### 步骤 1：正确配置 MySQL 连接信息

修改 `PutData.py` 第 34-40 行：
```python
DB_CONFIG = {
    'host': 'localhost',      # 改成你的 MySQL 主机
    'port': 3306,             # 改成你的 MySQL 端口
    'user': 'root',           # 改成你的 MySQL 用户名
    'password': '123456',     # 改成你的 MySQL 密码
    'database': 'bigdata',    # 改成你的数据库名
    'charset': 'utf8mb4'
}
```

**同时修改 `create_tables.py` 中相同位置的配置**

### 步骤 2：运行一键导入脚本（推荐）

```bash
python run_full_pipeline.py
```

这会自动执行：
1. 生成 CSV 数据文件
2. 创建 MySQL 表结构
3. 导入数据到数据库

**耗时：约 20-30 秒（10 万条数据）**

### 步骤 3：验证数据

在 MySQL 中运行：
```sql
SELECT COUNT(*) as total FROM dim_student;
SELECT COUNT(*) as total FROM fact_employment;
```

---

##  单步执行（如需逐步操作）

### 只需生成数据（不导入数据库）
```bash
python platform_data_factory.py
```
✅ 输出 4 个 CSV 文件

### 只需创建表结构（不导入数据）
```bash
python create_tables.py
```
✅ 在 MySQL 中创建 4 张表

### 只导入 CSV 数据到数据库
```bash
python PutData.py
```
✅ 将 CSV 文件中的数据导入到 MySQL

---

##  监控导入过程

导入时会看到实时日志：
```
【开始导入】 学生维度表 [dim_student]
  数据源文件: dim_student.csv
  → 正在读取 CSV 文件...
  ✓ 读取完成，耗时 1.23s，共 100000 条记录
  → 正在清洗数据...
  → 正在执行批量插入...
✅【完成】 dim_student - 100000 条记录, 总耗时 15.34s
```

---

##  出现错误？看这里

| 错误 | 解决方案 |
|------|---------|
| `Can't connect to MySQL server` | 检查 MySQL 是否运行，检查 host/port 是否正确 |
| `Access denied` | 检查用户名和密码是否正确 |
| `Database 'bigdata' doesn't exist` | 先在 MySQL 中创建数据库：`CREATE DATABASE bigdata;` |
| `Table already exists` | `create_tables.py` 会自动删除旧表，再次运行即可 |
| `FileNotFoundError: dim_student.csv` | 先运行 `platform_data_factory.py` 生成数据 |

---

## 四张表结构

### `dim_student` - 学生表
- student_id (PK)
- student_name, id_card, gender
- origin_region_code, origin_place
- school_name, school_level, edu_name
- created_at

### `dim_company` - 企业表
- company_id (PK)
- employer_name
- company_scale, is_top_500, is_listed
- strategic_tags, reg_capital, last_year_revenue

### `fact_academic` - 学业表
- academic_id (PK)
- student_id (FK → dim_student)
- edu_level, major_code, major_name
- discipline_category, major_category, skill_level

### `fact_employment` - 就业表
- emp_id (PK)
- student_id (FK → dim_student)
- employer_name, avg_salary
- first_insured_date, sh_insurance_status
- leading_industry_tag

---

##  查询示例

```sql
-- 获取上海交通大学学生总数
SELECT COUNT(*) FROM dim_student WHERE school_name = '上海交通大学';

-- 查询平均薪资最高的行业
SELECT leading_industry_tag, AVG(avg_salary) as avg_salary
FROM fact_employment
GROUP BY leading_industry_tag
ORDER BY avg_salary DESC;

-- 查询在三大先导产业的学生
SELECT s.student_name, e.leading_industry_tag, e.avg_salary
FROM dim_student s
JOIN fact_employment e ON s.student_id = e.student_id
WHERE e.leading_industry_tag IN ('集成电路', '人工智能', '生物医药');

-- 查询双一流高校有社保的学生比例
SELECT 
    s.school_name,
    COUNT(*) as total_students,
    SUM(e.sh_insurance_status) as with_insurance,
    ROUND(SUM(e.sh_insurance_status)/COUNT(*)*100, 2) as insurance_rate
FROM dim_student s
JOIN fact_employment e ON s.student_id = e.student_id
WHERE s.school_level = '双一流建设高校'
GROUP BY s.school_name;
```

---

##  核心改进点

**自动表创建** - 无需手动建表，脚本自动完成
**完整日志** - 每步都有详细的日志记录
**错误恢复** - 出错时能准确定位问题
**性能优化** - 使用批量导入和连接池
**数据验证** - 导入前验证 CSV 文件完整性
 **外键管理** - 自动处理外键约束

---

##  快速帮助

```bash
# 查看最新日志
tail -f mysql_import_*.log

# 查看所有日志文件
ls -la *.log

# 重新初始化（清空所有表）
python create_tables.py
```

---

**祝导入顺利！**
