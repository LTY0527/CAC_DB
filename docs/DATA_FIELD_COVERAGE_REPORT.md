# DATA_FIELD_COVERAGE_REPORT

- 生成时间：2026-04-28 20:40
- 对照来源：`C:/Users/1/Desktop/数据表.docx` 中《所需外部数据清单》
- 扫描对象：`scripts/platform_data_factory.py`、`scripts/create_tables.py`、`data/generated/*.csv`、当前 MySQL `information_schema.COLUMNS`
- 本次只做检查报告，未修改代码、数据生成脚本或数据库结构。

## 一、总体结论

当前 CAC_DB 生成链路已经覆盖了高校、专业、学科、行业、岗位、企业、毕业生、就业、招生、课程技能、政策信号等竞赛核心业务字段。

但与《所需外部数据清单》相比，字段覆盖呈现两个明显特征：

1. 当前 `data/generated/*.csv` 主链路偏“脱敏业务事实表”，没有生成姓名、身份证号、生源地区代码、生源地等外部授权原始身份字段。
2. 当前 MySQL 中仍保留部分旧表，如 `dim_student`、`dim_company`、`fact_job_demand`、`fact_academic`，这些表覆盖了一些外部清单字段，但它们不属于当前 `scripts/platform_data_factory.py` 输出的 CSV 主链路。

因此，本报告将“当前生成链路覆盖”和“MySQL 存量旧表覆盖”分开说明。若字段仅存在于 MySQL 存量旧表，而不在 `data/generated/*.csv` 中，本报告归为“部分覆盖”。

## 二、覆盖统计

- 已同名覆盖：0 项
- 已业务等价覆盖：15 项
- 部分覆盖：26 项
- 未覆盖：9 项

说明：当前数据库和 CSV 主要采用英文列名，因此中文字段字面“同名覆盖”为 0；大量字段通过英文标准字段实现业务等价覆盖。

## 三、当前生成 CSV 表头概览

- `dim_school.csv`：`school_id`, `school_name`, `school_type`, `city`, `district`, `discipline_strength_tags`, `industry_affinity`, `major_count`, `first_class_major_count`, `salary_level_factor`, `employment_stability_factor`, `research_factor`, `application_factor`, `policy_response_factor`
- `dim_major_catalog.csv`：`major_code`, `major_name`, `discipline_category`, `major_class`, `degree_type`, `study_years`, `is_controlled`, `is_special`, `is_new_strategy_major`, `policy_direction_tags`
- `bridge_school_major.csv`：`school_id`, `major_code`, `is_enrolling`, `is_ace_major`, `is_first_class_major`, `school_major_strength_score`, `historical_enrollment_scale`, `major_status`
- `dim_industry.csv`：`industry_id`, `industry_name`, `policy_direction_tags`, `base_growth_factor`
- `dim_job_category.csv`：`job_category_id`, `job_category_name`, `industry_id`, `job_group`, `computer_related`, `skill_tags`, `compatible_major_classes`, `salary_min_base`, `salary_max_base`, `demand_growth_level`, `policy_direction_tags`
- `dim_enterprise.csv`：`enterprise_id`, `enterprise_name`, `industry_id`, `city`, `district`, `enterprise_scale`, `ownership_type`, `is_high_tech`, `is_specialized_new`, `salary_factor`, `hiring_stability_factor`
- `fact_job_posting.csv`：`posting_id`, `enterprise_id`, `industry_id`, `job_category_id`, `month`, `city`, `demand_count`, `salary_min`, `salary_max`, `education_required`, `experience_level`, `skill_tags`, `preferred_major_codes`, `policy_direction_tags`, `school_preference_level`
- `fact_graduate.csv`：`graduate_id`, `school_id`, `major_code`, `graduation_year`, `gender`, `degree_level`, `gpa_level`, `skill_tags`, `internship_count`, `certification_tags`, `job_intention_tags`
- `fact_employment.csv`：`employment_id`, `graduate_id`, `school_id`, `major_code`, `enterprise_id`, `industry_id`, `job_category_id`, `employment_month`, `salary`, `employment_type`, `city`, `match_score`, `is_major_related`, `social_security_verified`, `employment_quality_level`
- `fact_enrollment_plan.csv`：`plan_id`, `school_id`, `major_code`, `year`, `planned_quota`, `actual_enrollment`, `applicant_count`, `first_choice_rate`, `admission_score_avg`, `enrollment_satisfaction_score`
- `fact_course_skill.csv`：`course_id`, `school_id`, `major_code`, `course_name`, `skill_tags`, `course_type`, `practice_hours`, `industry_alignment_score`
- `fact_policy_signal.csv`：`policy_id`, `month`, `policy_direction`, `industry_id`, `major_code`, `policy_heat`, `city_support_score`, `strategy_level`, `description`

## 四、现有数据字段清单覆盖明细

| 清单字段 | 覆盖分类 | 覆盖证据 | 说明 |
|---|---|---|---|
| 姓名 | 部分覆盖 | MySQL 存量表 `dim_student.student_name` | 当前 generated CSV 与 `scripts/platform_data_factory.py` 不生成姓名。 |
| 身份证号 | 部分覆盖 | MySQL 存量表 `dim_student.id_card` | 当前生成链路不生成身份证号；符合脱敏方向，但若竞赛要求字段结构，可增加脱敏证件号或哈希字段。 |
| 性别 | 已业务等价覆盖 | `fact_graduate.gender`；MySQL `dim_student.gender` | 生成 CSV 已覆盖毕业生性别。 |
| 生源地区代码 | 部分覆盖 | MySQL `dim_student.origin_region_code` | 当前生成 CSV 不含生源地区代码。 |
| 生源地 | 部分覆盖 | MySQL `dim_student.origin_place` | 当前生成 CSV 不含生源地/省市来源字段。 |
| 学校名称 | 已业务等价覆盖 | `dim_school.school_name`；多个 ADS 表 `school_name` | 生成链路完整覆盖学校名称。 |
| 办学层次 | 部分覆盖 | MySQL `dim_student.school_level`；生成表 `dim_school.school_type` | `school_type` 是学校类型/办学特色，不完全等同办学层次。 |
| 学历名称 | 已业务等价覆盖 | `fact_graduate.degree_level`；MySQL `dim_student.edu_name` | 生成链路用 degree_level 表示本科/硕士等学历层级。 |
| 学科门类 | 已业务等价覆盖 | `dim_major_catalog.discipline_category`；ADS `discipline_category` | 覆盖。 |
| 专业类 | 已业务等价覆盖 | `dim_major_catalog.major_class`；MySQL `fact_academic.major_category` | 覆盖。 |
| 专业代码 | 已业务等价覆盖 | `major_code` in catalog/bridge/fact/ads | 覆盖。 |
| 专业 | 已业务等价覆盖 | `dim_major_catalog.major_name`；ADS `major_name` | 覆盖。 |
| 毕业去向代码 | 未覆盖 | 无 | 未发现标准毕业去向代码字段。 |
| 毕业去向 | 部分覆盖 | `fact_employment.employment_type` | 可表达签约就业、灵活就业等，但不是标准 17 类毕业去向体系。 |
| 单位名称 | 已业务等价覆盖 | `dim_enterprise.enterprise_name`；ADS `enterprise_name`；MySQL `dim_company.employer_name` | 覆盖就业单位名称。 |
| 单位类型 | 部分覆盖 | `dim_enterprise.ownership_type` | ownership_type 近似单位所有制，不等同清单中的 4 类单位类型。 |
| 企业类别 | 部分覆盖 | `ownership_type`, `is_high_tech`, `is_specialized_new` | 覆盖部分企业类别特征，但没有 14 类标准企业类别字段。 |
| 单位行业 | 已业务等价覆盖 | `dim_industry.industry_name`；fact/ads `industry_id`, `industry_name` | 覆盖。 |
| 在沪参保状态 | 已业务等价覆盖 | `fact_employment.social_security_verified` | 以布尔形式覆盖社保核验/参保状态。 |
| 工资 | 已业务等价覆盖 | `fact_employment.salary`；`avg_salary`；`salary_min`, `salary_max` | 覆盖工资相关数值，但没有字段名注明“申报上年度平均工资”。 |
| 三大先导产业 | 部分覆盖 | MySQL 旧表 `leading_industry_tag`, `dim_company.strategic_tags`；生成表 `policy_direction_tags` 可推断 | 当前生成链路没有显式“三大先导产业”分类字段。 |
| 技能等级 | 部分覆盖 | MySQL `fact_academic.skill_level`；生成表 `skill_tags`, `certification_tags` | 生成链路没有 6 类技能等级字段。 |
| 证书名称 | 部分覆盖 | `fact_graduate.certification_tags` | 为证书标签集合，不是规范化证书名称字段。 |
| 工种代码 | 部分覆盖 | `job_category_id` | 内部岗位类别 ID 可近似映射，但不是官方工种代码。 |
| 职业工种名称 | 已业务等价覆盖 | `dim_job_category.job_category_name`；ADS `job_category_name` | 覆盖职业/岗位类别名称。 |
| 首次在沪参保年月 | 部分覆盖 | `fact_employment.employment_month` + `social_security_verified` | 有就业月份和参保状态，但没有“首次在沪参保年月”字段。 |

## 五、建议新增就业单位数据字段覆盖明细

| 清单字段 | 覆盖分类 | 覆盖证据 | 说明 |
|---|---|---|---|
| 是否上海市三大先导 | 部分覆盖 | MySQL `leading_industry_tag`；生成表 `policy_direction_tags` | 未显式布尔字段。 |
| 是否上海市六大重点领域 | 部分覆盖 | `policy_direction_tags`, `policy_direction` | 可从政策标签推断，未显式布尔字段。 |
| 是否上海市四大新赛道 | 部分覆盖 | `policy_direction_tags`, `policy_direction` | 可从低空经济、数字文化等标签推断，未显式布尔字段。 |
| 是否上海市五大未来产业方向 | 部分覆盖 | `policy_direction_tags`, `policy_direction` | 可从新战略标签推断，未显式布尔字段。 |
| 单位规模 | 已业务等价覆盖 | `dim_enterprise.enterprise_scale`；MySQL `dim_company.company_scale` | 覆盖。 |
| 注册资本 | 部分覆盖 | MySQL `dim_company.reg_capital` | 当前生成 CSV 不覆盖。 |
| 成立日期 | 未覆盖 | 无 | 未发现企业成立日期字段。 |
| 所属地区 | 已业务等价覆盖 | `dim_enterprise.city`, `district`；fact `city` | 覆盖城市/区县。 |
| 注册地址 | 未覆盖 | 无 | 未发现注册地址字段。 |
| 是否上市 | 部分覆盖 | MySQL `dim_company.is_listed` | 当前生成 CSV 不覆盖。 |
| 是否世界500强 | 部分覆盖 | MySQL `dim_company.is_top_500` | 字段未区分世界500强/中国500强。 |
| 是否中国500强 | 部分覆盖 | MySQL `dim_company.is_top_500` | 字段语义不精确，未单独区分。 |
| 是否行业百强 | 未覆盖 | 无 | 未发现行业百强字段。 |
| 上一年度营业收入 | 部分覆盖 | MySQL `dim_company.last_year_revenue` | 当前生成 CSV 不覆盖。 |
| 净利润 | 未覆盖 | 无 | 未发现净利润字段。 |
| 纳税额 | 未覆盖 | 无 | 未发现纳税额字段。 |

## 六、建议新增就业职位数据字段覆盖明细

| 清单字段 | 覆盖分类 | 覆盖证据 | 说明 |
|---|---|---|---|
| 职位名称 | 部分覆盖 | MySQL `fact_job_demand.job_title`；生成表 `dim_job_category.job_category_name` 仅为类别 | 当前生成 CSV 不含具体职位名称。 |
| 职位类别 | 已业务等价覆盖 | `dim_job_category.job_category_name`, `job_group`；MySQL `fact_job_demand.job_category` | 覆盖。 |
| 合同类型 | 未覆盖 | 无 | 未发现合同类型字段。 |

## 七、建议新增现行政策数据字段覆盖明细

| 清单字段 | 覆盖分类 | 覆盖证据 | 说明 |
|---|---|---|---|
| 政策标题 | 未覆盖 | 无 | `fact_policy_signal.description` 有描述但没有标题字段。 |
| 政策类别 | 部分覆盖 | `fact_policy_signal.strategy_level`, `policy_direction` | 有策略层级/方向，不等于全国/地方/解读分类。 |
| 发布时间 | 部分覆盖 | `fact_policy_signal.month` | 只有月份粒度，不是明确发布日期。 |
| 相关政策 | 部分覆盖 | `policy_direction`, `policy_direction_tags` | 有政策方向/标签，无关联政策 ID 或标题。 |
| 文件原文 | 未覆盖 | 无 | 未发现文件路径/原文字段。 |

## 八、按分类汇总

### 已同名覆盖

- 无。当前表采用英文列名，没有与清单中文字段字面完全同名的列。

### 已业务等价覆盖

- 性别：`fact_graduate.gender`
- 学校名称：`dim_school.school_name`
- 学历名称：`fact_graduate.degree_level`
- 学科门类：`dim_major_catalog.discipline_category`
- 专业类：`dim_major_catalog.major_class`
- 专业代码：`major_code`
- 专业：`major_name`
- 单位名称：`dim_enterprise.enterprise_name`
- 单位行业：`dim_industry.industry_name`
- 在沪参保状态：`fact_employment.social_security_verified`
- 工资：`fact_employment.salary`, `avg_salary`, `salary_min`, `salary_max`
- 职业工种名称：`dim_job_category.job_category_name`
- 单位规模：`dim_enterprise.enterprise_scale`
- 所属地区：`dim_enterprise.city`, `district`
- 职位类别：`dim_job_category.job_category_name`, `job_group`

### 部分覆盖

- 姓名、身份证号、生源地区代码、生源地：仅 MySQL `dim_student` 存量表覆盖，当前 CSV 主链路不生成。
- 办学层次：`school_type` 与 `school_level` 语义不完全一致。
- 毕业去向：`employment_type` 可近似表达，但没有标准代码体系。
- 单位类型、企业类别：企业性质和高新/专精特新标签仅部分覆盖。
- 三大先导产业、四大新赛道、五大未来产业、六大重点领域：可由 policy/industry 标签推断，但缺少显式布尔字段。
- 技能等级、证书名称：当前是技能/证书标签，未规范化为等级/证书名称维表。
- 工种代码：`job_category_id` 为内部 ID，不是官方工种代码。
- 首次在沪参保年月：有就业月份和参保状态，无首次参保年月。
- 注册资本、是否上市、500强、上一年度营业收入：MySQL 旧表 `dim_company` 部分覆盖，当前 CSV 不覆盖。
- 职位名称：MySQL 旧表 `fact_job_demand.job_title` 覆盖，当前 CSV 只生成岗位类别。
- 政策类别、发布时间、相关政策：政策信号表部分覆盖。

### 未覆盖

- 毕业去向代码
- 成立日期
- 注册地址
- 是否行业百强
- 净利润
- 纳税额
- 合同类型
- 政策标题
- 文件原文

## 九、后续补字段建议（本次未执行）

1. 若竞赛材料需要体现“外部授权数据字段结构”，建议新增 ODS/DWD 脱敏学生来源表，包含 `student_name_masked`、`id_card_hash`、`origin_region_code`、`origin_place` 等字段。
2. 建议扩展 `dim_enterprise` 为企业工商画像维表，新增注册资本、成立日期、注册地址、是否上市、是否世界500强、是否中国500强、是否行业百强、营收、净利润、纳税额。
3. 建议新增 `dim_policy_document` 或扩展 `fact_policy_signal`，覆盖政策标题、政策类别、发布时间、相关政策、文件原文路径。
4. 建议新增标准代码字段：毕业去向代码、工种代码、生源地区代码，并保留中文名称字段，便于与外部清单逐项对齐。
5. 建议显式增加上海产业标签布尔字段：`is_sh_three_leading`、`is_sh_six_key_fields`、`is_sh_four_new_tracks`、`is_sh_five_future_industries`，避免前端或算法仅依赖文本标签推断。
