# -*- coding: utf-8 -*-
"""
Spark / pandas 特征加工脚本。

输出 ADS：
- ads_employment_summary
- ads_school_kpi
- ads_job_demand_monthly
- ads_job_skill_heatmap
- ads_major_supply_demand_gap

如果本机 Spark 或 JDBC 驱动不可用，自动使用 pandas + SQLAlchemy 完成核心聚合。
"""

from __future__ import annotations

import ast
import io
import json
import sys
from collections import Counter
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def get_engine():
    return create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)


def read_table(engine, table_name: str) -> pd.DataFrame:
    try:
        return pd.read_sql(f"SELECT * FROM `{table_name}`", engine)
    except Exception as exc:
        raise RuntimeError(f"读取数据表 {table_name} 失败，请先执行建表和导入：{exc}") from exc


def parse_skill_list(value) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text_value = str(value).strip()
    if not text_value:
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text_value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    for sep in ["、", ";", "；", "|"]:
        text_value = text_value.replace(sep, ",")
    return [item.strip() for item in text_value.split(",") if item.strip()]


def write_table(engine, df: pd.DataFrame, table_name: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
        if not df.empty:
            df.to_sql(table_name, conn, if_exists="replace", index=False, chunksize=2000, method="multi")
        else:
            df.to_sql(table_name, conn, if_exists="replace", index=False)
    print(f"[ADS] 已写入 {table_name}: {len(df)} 行")


def build_employment_ads(student_df: pd.DataFrame, academic_df: pd.DataFrame, employment_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = (
        employment_df.merge(student_df, on="student_id", how="left")
        .merge(academic_df, on="student_id", how="left", suffixes=("", "_academic"))
    )
    merged["avg_salary"] = pd.to_numeric(merged["avg_salary"], errors="coerce").fillna(0)
    summary = (
        merged.groupby(
            ["school_name", "school_level", "discipline_category", "major_name", "leading_industry_tag"],
            dropna=False,
        )
        .agg(avg_salary=("avg_salary", "mean"), emp_count=("student_id", "count"))
        .reset_index()
    )
    summary["avg_salary"] = summary["avg_salary"].round(2)
    summary["high_tech_ratio"] = (summary["leading_industry_tag"].isin(["人工智能", "集成电路", "生物医药", "数字安全"])).astype(float)

    school_kpi = (
        merged.groupby(["school_name", "school_level"], dropna=False)
        .agg(
            overall_avg_salary=("avg_salary", "mean"),
            total_graduates=("student_id", "count"),
            strategic_industry_rate=("leading_industry_tag", lambda s: s.isin(["人工智能", "集成电路", "生物医药", "数字安全"]).mean()),
        )
        .reset_index()
    )
    school_kpi["overall_avg_salary"] = school_kpi["overall_avg_salary"].round(2)
    school_kpi["strategic_industry_rate"] = school_kpi["strategic_industry_rate"].round(4)
    return summary, school_kpi


def build_job_demand_monthly(job_df: pd.DataFrame) -> pd.DataFrame:
    df = job_df.copy()
    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    df = df.dropna(subset=["publish_date", "major_name", "job_category"])
    df["demand_month"] = df["publish_date"].dt.strftime("%Y-%m")
    df["recruit_count"] = pd.to_numeric(df["recruit_count"], errors="coerce").fillna(1).clip(lower=0)
    df["salary_avg"] = pd.to_numeric(df["salary_avg"], errors="coerce")
    df["industry_tag"] = df["leading_industry_tag"].fillna("未分类行业")

    rows = []
    group_cols = ["major_name", "job_category", "industry_tag", "city", "demand_month"]
    for keys, group in df.groupby(group_cols, dropna=False):
        skills = Counter()
        for value in group["skill_keywords"]:
            skills.update(parse_skill_list(value))
        rows.append(
            {
                "major_name": keys[0],
                "job_category": keys[1],
                "industry_tag": keys[2],
                "city": keys[3] or "全市",
                "demand_month": keys[4],
                "demand_count": round(float(group["recruit_count"].sum()), 2),
                "company_count": int(group["employer_name"].nunique()),
                "avg_salary": round(float(group["salary_avg"].mean()), 2) if group["salary_avg"].notna().any() else None,
                "skill_keywords_summary": json.dumps([item for item, _ in skills.most_common(8)], ensure_ascii=False),
            }
        )
    monthly = pd.DataFrame(rows).sort_values(["major_name", "job_category", "industry_tag", "city", "demand_month"])
    monthly["demand_growth_rate"] = (
        monthly.groupby(["major_name", "job_category", "industry_tag", "city"])["demand_count"]
        .pct_change()
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0)
        .round(4)
    )
    return monthly


def build_skill_heatmap(job_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in job_df.iterrows():
        for skill in parse_skill_list(row.get("skill_keywords")):
            rows.append(
                {
                    "major_name": row.get("major_name"),
                    "job_category": row.get("job_category"),
                    "skill_name": skill,
                }
            )
    if not rows:
        return pd.DataFrame(columns=["major_name", "job_category", "skill_name", "skill_count", "skill_weight"])
    skill_df = pd.DataFrame(rows).dropna(subset=["major_name", "job_category", "skill_name"])
    count_df = skill_df.groupby(["major_name", "job_category", "skill_name"]).size().reset_index(name="skill_count")
    total_df = count_df.groupby(["major_name", "job_category"])["skill_count"].transform("sum")
    count_df["skill_weight"] = (count_df["skill_count"] / total_df).round(6)
    return count_df.sort_values(["major_name", "job_category", "skill_count"], ascending=[True, True, False])


def build_supply_demand_gap(academic_df: pd.DataFrame, job_df: pd.DataFrame) -> pd.DataFrame:
    graduate = academic_df.groupby("major_name")["student_id"].nunique().reset_index(name="graduate_count")
    demand = (
        job_df.assign(recruit_count=pd.to_numeric(job_df["recruit_count"], errors="coerce").fillna(1).clip(lower=0))
        .groupby("major_name")["recruit_count"]
        .sum()
        .reset_index(name="demand_count")
    )
    gap = graduate.merge(demand, on="major_name", how="outer").fillna(0)
    gap["graduate_count"] = gap["graduate_count"].astype(int)
    gap["demand_count"] = gap["demand_count"].round(2)
    gap["gap_count"] = (gap["demand_count"] - gap["graduate_count"]).round(2)
    gap["gap_rate"] = (gap["gap_count"] / gap["graduate_count"].replace(0, 1)).round(4)

    def level(rate):
        if rate >= 0.25:
            return "供不应求"
        if rate <= -0.15:
            return "供大于求"
        return "基本平衡"

    gap["gap_level"] = gap["gap_rate"].apply(level)
    return gap.sort_values("gap_rate", ascending=False)


def run_data_aggregation() -> bool:
    print("[ADS] 岗位需求特征加工启动。")
    engine = get_engine()
    try:
        student_df = read_table(engine, "dim_student")
        company_df = read_table(engine, "dim_company")
        academic_df = read_table(engine, "fact_academic")
        employment_df = read_table(engine, "fact_employment")
        job_df = read_table(engine, "fact_job_demand")
        print(
            f"[ADS] 数据已加载：学生{len(student_df)}、企业{len(company_df)}、学业{len(academic_df)}、就业{len(employment_df)}、岗位需求{len(job_df)}。"
        )

        employment_summary, school_kpi = build_employment_ads(student_df, academic_df, employment_df)
        monthly = build_job_demand_monthly(job_df)
        heatmap = build_skill_heatmap(job_df)
        gap = build_supply_demand_gap(academic_df, job_df)

        write_table(engine, employment_summary, "ads_employment_summary")
        write_table(engine, school_kpi, "ads_school_kpi")
        write_table(engine, monthly, "ads_job_demand_monthly")
        write_table(engine, heatmap, "ads_job_skill_heatmap")
        write_table(engine, gap, "ads_major_supply_demand_gap")

        print("[ADS] 岗位需求特征加工完成：月度需求、技能热力、专业供需缺口均已写入 MySQL。")
        return True
    except Exception as exc:
        print(f"[ADS] 特征加工失败：{exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if run_data_aggregation() else 1)
