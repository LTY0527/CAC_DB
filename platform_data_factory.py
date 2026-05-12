# -*- coding: utf-8 -*-
"""
数据集团多源异构样本数据生成脚本。

产物：
- dim_student.csv：学生画像数据
- dim_company.csv：企业画像数据
- fact_academic.csv：学业与专业数据
- fact_employment.csv：就业去向数据
- fact_job_demand.csv：数据集团企业岗位招聘需求数据

岗位需求数据覆盖 36 个月、多城市、多行业、多岗位、多专业，并刻意制造少量
空值、异常值和格式不统一字段，用于演示数据清洗、标准化和异常处理过程。
"""

from __future__ import annotations

import io
import json
import math
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

try:
    from faker import Faker
except ImportError:  # pragma: no cover - 仅在缺少依赖时使用
    Faker = None


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
SEED = 20260426
STUDENT_COUNT = int(os.getenv("DATA_FACTORY_STUDENT_COUNT", "100000"))
JOB_MONTHS = int(os.getenv("DATA_FACTORY_JOB_MONTHS", "36"))
CREATED_AT = "2026-04-26 00:00:00"
BATCH_ID = f"DG_JOB_{datetime.now().strftime('%Y%m%d')}"

random.seed(SEED)
fake = Faker("zh_CN") if Faker else None
if fake:
    Faker.seed(SEED)


MAJORS = [
    {"major_code": "080901", "major_name": "计算机科学与技术", "discipline_category": "工学", "major_category": "计算机类"},
    {"major_code": "080902", "major_name": "软件工程", "discipline_category": "工学", "major_category": "计算机类"},
    {"major_code": "080906", "major_name": "数据科学与大数据技术", "discipline_category": "工学", "major_category": "计算机类"},
    {"major_code": "080907", "major_name": "人工智能", "discipline_category": "工学", "major_category": "计算机类"},
    {"major_code": "080904", "major_name": "信息安全", "discipline_category": "工学", "major_category": "计算机类"},
    {"major_code": "080701", "major_name": "电子信息工程", "discipline_category": "工学", "major_category": "电子信息类"},
    {"major_code": "080801", "major_name": "自动化", "discipline_category": "工学", "major_category": "自动化类"},
    {"major_code": "020302", "major_name": "金融工程", "discipline_category": "经济学", "major_category": "金融学类"},
    {"major_code": "120801", "major_name": "电子商务", "discipline_category": "管理学", "major_category": "电子商务类"},
    {"major_code": "120203", "major_name": "会计学", "discipline_category": "管理学", "major_category": "工商管理类"},
    {"major_code": "080202", "major_name": "机械设计制造及其自动化", "discipline_category": "工学", "major_category": "机械类"},
    {"major_code": "081302", "major_name": "制药工程", "discipline_category": "工学", "major_category": "化工与制药类"},
]

SCHOOLS = [
    ("上海大学", "市属重点高校", 0.16),
    ("上海交通大学", "双一流建设高校", 0.12),
    ("复旦大学", "双一流建设高校", 0.10),
    ("同济大学", "双一流建设高校", 0.10),
    ("华东师范大学", "双一流建设高校", 0.09),
    ("上海财经大学", "双一流建设高校", 0.08),
    ("东华大学", "双一流建设高校", 0.08),
    ("华东理工大学", "双一流建设高校", 0.09),
    ("上海工程技术大学", "应用型本科高校", 0.10),
    ("上海师范大学", "市属重点高校", 0.08),
]

ORIGINS = [
    ("310000", "上海市"),
    ("320000", "江苏省"),
    ("330000", "浙江省"),
    ("340000", "安徽省"),
    ("360000", "江西省"),
    ("370000", "山东省"),
    ("410000", "河南省"),
    ("420000", "湖北省"),
    ("430000", "湖南省"),
    ("440000", "广东省"),
    ("500000", "重庆市"),
    ("510000", "四川省"),
]

CITY_POOL = ["上海", "杭州", "苏州", "南京", "深圳", "北京", "合肥", "宁波"]
SOURCE_CHANNELS = ["数据集团企业招聘库", "社保就业库", "公开招聘平台", "行业协会数据"]

INDUSTRIES = {
    "人工智能": {"company_prefix": ["智算", "深瞳", "星火"], "salary": (16000, 36000)},
    "软件服务": {"company_prefix": ["云链", "数栈", "开源"], "salary": (13000, 30000)},
    "先进制造": {"company_prefix": ["智造", "精工", "装备"], "salary": (11000, 26000)},
    "金融科技": {"company_prefix": ["融信", "量化", "银联"], "salary": (15000, 34000)},
    "集成电路": {"company_prefix": ["芯云", "微纳", "硅谷"], "salary": (15000, 35000)},
    "生物医药": {"company_prefix": ["生命", "药研", "康源"], "salary": (10000, 26000)},
    "数字贸易": {"company_prefix": ["跨境", "数贸", "贸联"], "salary": (10000, 24000)},
    "数字安全": {"company_prefix": ["安全", "网盾", "信安"], "salary": (14000, 32000)},
}

JOB_PROFILES = [
    {
        "job_category": "后端开发",
        "titles": ["Java后端工程师", "Python后端工程师", "平台研发工程师"],
        "majors": ["软件工程", "计算机科学与技术", "数据科学与大数据技术"],
        "industries": ["软件服务", "人工智能", "金融科技"],
        "skills": ["Java", "Python", "MySQL", "Redis", "Spring Boot", "Flask", "Docker"],
        "base": 42,
        "monthly_growth": 0.035,
    },
    {
        "job_category": "数据分析",
        "titles": ["数据分析师", "BI分析师", "经营分析师"],
        "majors": ["数据科学与大数据技术", "金融工程", "电子商务"],
        "industries": ["人工智能", "金融科技", "数字贸易"],
        "skills": ["Python", "SQL", "Pandas", "Tableau", "Spark", "统计建模"],
        "base": 36,
        "monthly_growth": 0.032,
    },
    {
        "job_category": "算法工程",
        "titles": ["机器学习工程师", "算法工程师", "大模型应用工程师"],
        "majors": ["人工智能", "数据科学与大数据技术", "计算机科学与技术"],
        "industries": ["人工智能", "软件服务", "集成电路"],
        "skills": ["Python", "机器学习", "PyTorch", "TensorFlow", "特征工程", "大模型"],
        "base": 28,
        "monthly_growth": 0.048,
    },
    {
        "job_category": "测试工程",
        "titles": ["测试工程师", "自动化测试工程师", "质量工程师"],
        "majors": ["软件工程", "计算机科学与技术", "自动化"],
        "industries": ["软件服务", "先进制造", "数字贸易"],
        "skills": ["Python", "Selenium", "接口测试", "JMeter", "Linux", "自动化测试"],
        "base": 24,
        "monthly_growth": 0.012,
    },
    {
        "job_category": "产品经理",
        "titles": ["产品经理", "数据产品经理", "平台产品经理"],
        "majors": ["电子商务", "软件工程", "金融工程"],
        "industries": ["数字贸易", "金融科技", "软件服务"],
        "skills": ["需求分析", "Axure", "SQL", "用户研究", "数据分析", "项目管理"],
        "base": 22,
        "monthly_growth": 0.018,
    },
    {
        "job_category": "网络安全",
        "titles": ["安全工程师", "渗透测试工程师", "安全运营工程师"],
        "majors": ["信息安全", "计算机科学与技术", "软件工程"],
        "industries": ["数字安全", "金融科技", "软件服务"],
        "skills": ["网络安全", "渗透测试", "Linux", "Python", "安全运营", "风险评估"],
        "base": 30,
        "monthly_growth": 0.042,
    },
    {
        "job_category": "数据库开发",
        "titles": ["数据库开发工程师", "数据仓库工程师", "ETL工程师"],
        "majors": ["数据科学与大数据技术", "软件工程", "计算机科学与技术"],
        "industries": ["软件服务", "金融科技", "人工智能"],
        "skills": ["MySQL", "SQL优化", "ETL", "Spark", "Hive", "数据仓库"],
        "base": 31,
        "monthly_growth": 0.028,
    },
    {
        "job_category": "运维工程",
        "titles": ["云运维工程师", "DevOps工程师", "平台运维工程师"],
        "majors": ["计算机科学与技术", "软件工程", "自动化"],
        "industries": ["软件服务", "先进制造", "数字安全"],
        "skills": ["Linux", "Kubernetes", "Docker", "Shell", "监控告警", "云计算"],
        "base": 26,
        "monthly_growth": 0.020,
    },
    {
        "job_category": "嵌入式开发",
        "titles": ["嵌入式工程师", "单片机开发工程师", "智能硬件工程师"],
        "majors": ["电子信息工程", "自动化", "机械设计制造及其自动化"],
        "industries": ["集成电路", "先进制造", "人工智能"],
        "skills": ["C语言", "嵌入式Linux", "ARM", "传感器", "自动控制", "硬件调试"],
        "base": 25,
        "monthly_growth": 0.030,
    },
]


def company_name(industry: str, index: int) -> str:
    """生成稳定企业名称。"""
    prefix = random.choice(INDUSTRIES[industry]["company_prefix"])
    suffix = fake.company_suffix() if fake else random.choice(["科技有限公司", "数据有限公司", "产业集团"])
    return f"{random.choice(CITY_POOL)}{prefix}{industry}{suffix}{index:03d}"


def generate_companies() -> tuple[pd.DataFrame, dict[str, list[dict]]]:
    """生成企业维表和按行业分组的企业池。"""
    rows: list[dict] = []
    industry_pool: dict[str, list[dict]] = {industry: [] for industry in INDUSTRIES}
    company_id = 1
    for industry in INDUSTRIES:
        for index in range(1, 41):
            name = company_name(industry, index)
            row = {
                "company_id": company_id,
                "employer_name": name,
                "company_scale": random.choices(["大型", "中型", "小型"], weights=[0.22, 0.52, 0.26], k=1)[0],
                "is_top_500": int(random.random() < 0.08),
                "is_listed": int(random.random() < 0.16),
                "strategic_tags": json.dumps([industry, "数据集团接入"], ensure_ascii=False),
                "reg_capital": round(random.uniform(3000, 90000), 2),
                "last_year_revenue": round(random.uniform(12000, 380000), 2),
            }
            rows.append(row)
            industry_pool[industry].append({"company_id": company_id, "employer_name": name})
            company_id += 1
    return pd.DataFrame(rows), industry_pool


def generate_students_and_academics() -> tuple[pd.DataFrame, pd.DataFrame]:
    """生成学生画像和学业事实数据。"""
    school_names = [item[0] for item in SCHOOLS]
    school_weights = [item[2] for item in SCHOOLS]
    school_level_map = {item[0]: item[1] for item in SCHOOLS}

    students: list[dict] = []
    academics: list[dict] = []
    for student_id in range(1, STUDENT_COUNT + 1):
        school_name = random.choices(school_names, weights=school_weights, k=1)[0]
        school_level = school_level_map[school_name]
        origin_region_code, origin_place = random.choice(ORIGINS)
        major = random.choices(
            MAJORS,
            weights=[0.13, 0.13, 0.12, 0.10, 0.08, 0.08, 0.08, 0.07, 0.07, 0.05, 0.05, 0.04],
            k=1,
        )[0]
        edu_name = random.choices(["本科", "硕士", "博士"], weights=[0.74, 0.22, 0.04], k=1)[0]
        skill_level = random.choices(["初", "中", "高"], weights=[0.25, 0.48, 0.27], k=1)[0]
        students.append(
            {
                "student_id": student_id,
                "student_name": fake.name() if fake else f"学生{student_id}",
                "id_card": fake.ssn() if fake else f"310000199901{student_id % 9999:04d}",
                "gender": random.choice(["男", "女"]),
                "origin_region_code": origin_region_code,
                "origin_place": origin_place,
                "created_at": CREATED_AT,
                "school_name": school_name,
                "school_level": school_level,
                "edu_name": edu_name,
            }
        )
        academics.append(
            {
                "academic_id": student_id,
                "student_id": student_id,
                "edu_level": edu_name,
                "major_code": major["major_code"],
                "major_name": major["major_name"],
                "discipline_category": major["discipline_category"],
                "major_category": major["major_category"],
                "skill_level": skill_level,
            }
        )
    return pd.DataFrame(students), pd.DataFrame(academics)


def generate_employments(academics: pd.DataFrame, company_pool: dict[str, list[dict]]) -> pd.DataFrame:
    """生成就业事实数据，薪资仅作为辅助分析字段。"""
    major_to_profile = {
        major: [profile for profile in JOB_PROFILES if major in profile["majors"]]
        for major in academics["major_name"].unique()
    }
    rows: list[dict] = []
    month_start = pd.Timestamp("2024-07-01")
    for row in academics.itertuples(index=False):
        profiles = major_to_profile.get(row.major_name) or JOB_PROFILES
        profile = random.choice(profiles)
        industry = random.choice(profile["industries"])
        company = random.choice(company_pool[industry])
        salary_min, salary_max = INDUSTRIES[industry]["salary"]
        edu_bonus = {"本科": 1.00, "硕士": 1.22, "博士": 1.45}.get(row.edu_level, 1.00)
        skill_bonus = {"初": 0.90, "中": 1.00, "高": 1.16}.get(row.skill_level, 1.00)
        salary = max(6500, random.gauss((salary_min + salary_max) / 2, 2200) * edu_bonus * skill_bonus)
        insured_date = month_start + pd.DateOffset(days=random.randint(0, 630))
        rows.append(
            {
                "emp_id": row.student_id,
                "student_id": row.student_id,
                "employer_name": company["employer_name"],
                "avg_salary": round(float(salary), 2),
                "first_insured_date": insured_date.strftime("%Y-%m-%d"),
                "sh_insurance_status": int(random.random() < 0.78),
                "leading_industry_tag": industry,
            }
        )
    return pd.DataFrame(rows)


def make_skill_field(skills: list[str], row_index: int) -> str:
    """制造少量技能字段格式不统一的清洗场景。"""
    picked = random.sample(skills, k=min(len(skills), random.randint(4, 6)))
    if row_index % 97 == 0:
        return "、".join(picked)
    if row_index % 131 == 0:
        return ",".join(picked)
    if row_index % 173 == 0:
        return str(picked)
    return json.dumps(picked, ensure_ascii=False)


def generate_job_demand(company_pool: dict[str, list[dict]]) -> pd.DataFrame:
    """生成数据集团岗位需求事实数据，包含趋势和清洗场景。"""
    rows: list[dict] = []
    months = pd.date_range(end="2026-03-01", periods=JOB_MONTHS, freq="MS")
    row_index = 0
    for month_index, month_start in enumerate(months):
        season_factor = 1 + 0.13 * math.sin(month_index / 12 * 2 * math.pi)
        for profile in JOB_PROFILES:
            trend = (1 + profile["monthly_growth"]) ** month_index
            for major in profile["majors"]:
                major_meta = next(item for item in MAJORS if item["major_name"] == major)
                for city in CITY_POOL[:6]:
                    city_factor = {"上海": 1.30, "杭州": 1.12, "苏州": 0.96, "南京": 0.92, "深圳": 1.18, "北京": 1.15}.get(city, 1.0)
                    expected = profile["base"] * trend * season_factor * city_factor
                    record_count = max(3, int(expected / 12) + random.randint(1, 4))
                    for _ in range(record_count):
                        row_index += 1
                        industry = random.choice(profile["industries"])
                        company = random.choice(company_pool[industry])
                        salary_low, salary_high = INDUSTRIES[industry]["salary"]
                        salary_min = round(random.uniform(salary_low * 0.72, salary_low * 1.05), 2)
                        salary_max = round(random.uniform(max(salary_min + 1000, salary_high * 0.78), salary_high * 1.10), 2)
                        recruit_count = max(1, int(random.gauss(expected / max(record_count, 1), 2.2)))

                        # 制造清洗场景：空值、异常招聘人数、异常薪资、岗位名称缺失。
                        employer_name = company["employer_name"] if row_index % 89 else None
                        company_id = company["company_id"] if employer_name else None
                        job_title = random.choice(profile["titles"]) if row_index % 113 else None
                        if row_index % 127 == 0:
                            recruit_count = 0
                        elif row_index % 149 == 0:
                            recruit_count = -random.randint(1, 8)
                        elif row_index % 191 == 0:
                            recruit_count = random.randint(500, 1200)
                        if row_index % 157 == 0:
                            salary_min, salary_max = salary_max, salary_min
                        elif row_index % 181 == 0:
                            salary_min = -1000

                        publish_date = month_start + pd.DateOffset(days=random.randint(0, 26))
                        rows.append(
                            {
                                "demand_id": row_index,
                                "employer_name": employer_name,
                                "company_id": company_id,
                                "job_title": job_title,
                                "job_category": profile["job_category"],
                                "leading_industry_tag": industry,
                                "major_name": major,
                                "major_category": major_meta["major_category"],
                                "city": city,
                                "publish_date": publish_date.strftime("%Y-%m-%d"),
                                "recruit_count": recruit_count,
                                "salary_min": salary_min,
                                "salary_max": salary_max,
                                "salary_avg": round((salary_min + salary_max) / 2, 2),
                                "education_requirement": random.choices(["本科", "硕士", "博士"], weights=[0.72, 0.24, 0.04], k=1)[0],
                                "experience_requirement": random.choice(["不限", "1-3年", "3-5年", "5年以上"]),
                                "skill_keywords": make_skill_field(profile["skills"], row_index),
                                "source_channel": random.choice(SOURCE_CHANNELS),
                                "data_batch_id": BATCH_ID,
                            }
                        )
    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, filename: str) -> None:
    path = ROOT_DIR / filename
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[数据工厂] 已生成 {filename}: {len(df):,} 行")


def generate_full_system_data() -> None:
    """生成完整平台样本数据。"""
    print("=" * 80)
    print("数据集团多源异构样本数据生成启动")
    print("=" * 80)
    print(f"[数据工厂] 学生样本量={STUDENT_COUNT:,}，岗位需求覆盖月份={JOB_MONTHS}")

    company_df, company_pool = generate_companies()
    student_df, academic_df = generate_students_and_academics()
    employment_df = generate_employments(academic_df, company_pool)
    job_demand_df = generate_job_demand(company_pool)
    job_demand_df["company_id"] = job_demand_df["company_id"].astype("Int64")

    write_csv(student_df, "dim_student.csv")
    write_csv(company_df, "dim_company.csv")
    write_csv(academic_df, "fact_academic.csv")
    write_csv(employment_df, "fact_employment.csv")
    write_csv(job_demand_df, "fact_job_demand.csv")

    top_demand = (
        job_demand_df.assign(recruit_count_clean=job_demand_df["recruit_count"].clip(lower=1, upper=300))
        .groupby(["major_name", "job_category"])["recruit_count_clean"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )
    print("[数据工厂] 岗位需求 TOP5 专业/岗位：")
    for (major_name, job_category), demand_count in top_demand.items():
        print(f"  - {major_name} / {job_category}: {int(demand_count):,} 人")
    print("[数据工厂] 输出文件：dim_student.csv, dim_company.csv, fact_academic.csv, fact_employment.csv, fact_job_demand.csv")
    print("[数据工厂] 样本数据生成完成，可执行 python PutData.py 导入 MySQL。")


if __name__ == "__main__":
    generate_full_system_data()
