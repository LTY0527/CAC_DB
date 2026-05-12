# DATA_FIELD_MAPPING

## 外部数据字段基础映射

| 原始字段 | 当前数据库落库字段 | 说明 |
| --- | --- | --- |
| 学校名称 | `dim_school.school_name` | 高校维度主名称 |
| 专业代码 | `dim_major_catalog.major_code` | 本科专业目录代码 |
| 专业 | `dim_major_catalog.major_name` | 本科专业名称 |
| 学科门类 | `dim_major_catalog.discipline_category` | 12 个学科门类 |
| 专业类 | `dim_major_catalog.major_class` | 93 个专业类 |
| 毕业去向 | `fact_employment.employment_type` | 签约就业、灵活就业、基层项目等 |
| 单位名称 | `dim_enterprise.enterprise_name` | 脱敏仿真就业/招聘单位名称 |
| 单位行业 | `dim_industry.industry_name` | 单位所属行业 |
| 工资 | `fact_employment.salary` | 就业薪资字段 |
| 三大先导产业 | `fact_employment.leading_industry_name` / `fact_employment.is_shanghai_leading_employment` | 三大先导产业名称及布尔标记 |

## 真实展示专业字段映射

| 用途 | 当前数据库字段 | 说明 |
| --- | --- | --- |
| 真实展示专业标记 | `dim_major_catalog.is_real_display_major` | 允许进入公众端、政府端、教师端核心展示 |
| 目录占位专业标记 | `dim_major_catalog.is_catalog_placeholder` | 仅用于满足 845 专业目录规模，不进入核心展示 |
| 展示优先级 | `dim_major_catalog.display_priority` | 学校优势专业和产业热点专业优先 |
| 高薪榜产业权重 | `dim_major_catalog.salary_rank_weight` | 高薪专业榜综合排序辅助权重 |
| 产业趋势标签 | `dim_major_catalog.industry_trend_tags` | 人工智能、集成电路、数据智能、金融科技等 |

## 三大先导产业字段映射

### 原始字段

- 三大先导产业
- 是否上海市三大先导？

### 统一定义

上海市三大先导产业在项目中统一按以下枚举识别：

| code | name |
| --- | --- |
| IC | 集成电路 |
| BIOMED | 生物医药 |
| AI | 人工智能 |

配置文件：`config/industry_policy_tags.yaml`

### 当前数据库字段

| 层级 | 表 | 字段 |
| --- | --- | --- |
| 行业维度 | dim_industry | is_shanghai_leading_industry |
| 行业维度 | dim_industry | leading_industry_name |
| 行业维度 | dim_industry | leading_industry_code |
| 企业维度 | dim_enterprise | is_shanghai_leading_enterprise |
| 企业维度 | dim_enterprise | leading_industry_name |
| 企业维度 | dim_enterprise | leading_industry_code |
| 招聘事实 | fact_job_posting | is_shanghai_leading_job |
| 招聘事实 | fact_job_posting | leading_industry_name |
| 招聘事实 | fact_job_posting | leading_industry_code |
| 就业事实 | fact_employment | is_shanghai_leading_employment |
| 就业事实 | fact_employment | leading_industry_name |
| 就业事实 | fact_employment | leading_industry_code |
| 汇总结果 | ads_leading_industry_employment_summary | leading_industry_employment_count |
| 汇总结果 | ads_leading_industry_employment_summary | leading_industry_employment_rate |
| 汇总结果 | ads_leading_industry_employment_summary | ai_employment_count |
| 汇总结果 | ads_leading_industry_employment_summary | ic_employment_count |
| 汇总结果 | ads_leading_industry_employment_summary | biomed_employment_count |

### 前端展示字段

- `leading_industry_employment_count`
- `leading_industry_employment_rate`
- `leading_industry_trend`
- 兼容就业汇总明细中的 `leading_industry_tag`

### 统计口径

教师端先导产业吸纳人数：

```sql
SELECT COUNT(*)
FROM fact_employment
WHERE school_id = :school_id
  AND is_shanghai_leading_employment = 1;
```

政府端十校先导产业吸纳人数：

```sql
SELECT COUNT(*)
FROM fact_employment
WHERE is_shanghai_leading_employment = 1;
```

政府端趋势/占比：

```sql
SELECT
  SUM(CASE WHEN is_shanghai_leading_employment = 1 THEN 1 ELSE 0 END) / COUNT(*)
FROM fact_employment;
```

### 兼容说明

旧库如果缺少上述字段，可运行：

```bash
python scripts/migrate_leading_industry_fields.py
```

该脚本只补字段和按行业/企业/岗位关键词回填标签，不清空已有数据。
