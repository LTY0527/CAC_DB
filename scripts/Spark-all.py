# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL


def log_chain(conn, status: str, row_count: int, started: datetime, error: str = "") -> None:
    conn.execute(
        text(
            """
            INSERT INTO ads_algorithm_chain_log
            (batch_id, stage_order, stage_name, input_tables, output_tables, algorithm_name,
             status, row_count, started_at, finished_at, cost_seconds, error_message)
            VALUES (:batch_id, 1, 'Spark 聚合特征', 'fact_job_posting,fact_employment,fact_enrollment_plan,fact_policy_signal',
                    'ads_job_demand_features', 'Spark/Pandas Feature Aggregation', :status, :row_count,
                    :started_at, NOW(), TIMESTAMPDIFF(SECOND,:started_at,NOW()), :error_message)
            """
        ),
        {
            "batch_id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "status": status,
            "row_count": row_count,
            "started_at": started,
            "error_message": error,
        },
    )


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    started = datetime.now()
    try:
        posting = pd.read_sql("SELECT * FROM fact_job_posting", engine)
        bridge = pd.read_sql("SELECT * FROM bridge_school_major", engine)
        employment = pd.read_sql("SELECT * FROM fact_employment", engine)
        graduates = pd.read_sql("SELECT school_id, major_code, COUNT(*) graduate_count FROM fact_graduate GROUP BY school_id, major_code", engine)
        enrollment = pd.read_sql("SELECT school_id, major_code, AVG(applicant_count) applicant_count, AVG(planned_quota) planned_quota, AVG(first_choice_rate) first_choice_rate FROM fact_enrollment_plan WHERE year>=2024 GROUP BY school_id, major_code", engine)
        policy = pd.read_sql("SELECT month, industry_id, major_code, AVG(policy_heat) policy_heat FROM fact_policy_signal GROUP BY month, industry_id, major_code", engine)
        schools = pd.read_sql("SELECT school_id, school_name, industry_affinity FROM dim_school", engine)
        majors = pd.read_sql("SELECT major_code, major_name, discipline_category FROM dim_major_catalog", engine)
        industries = pd.read_sql("SELECT industry_id, industry_name FROM dim_industry", engine)
        jobs = pd.read_sql("SELECT job_category_id, job_category_name FROM dim_job_category", engine)
        enterprises = pd.read_sql("SELECT enterprise_id, is_high_tech FROM dim_enterprise", engine)

        post = posting.merge(
            bridge[["school_id", "major_code", "school_major_strength_score", "is_ace_major"]],
            left_on="preferred_major_codes",
            right_on="major_code",
            how="inner",
        )
        post["salary_mid"] = (post["salary_min"] + post["salary_max"]) / 2
        features = (
            post.groupby(["month", "school_id", "major_code", "industry_id", "job_category_id"], as_index=False)
            .agg(
                demand_count_sum=("demand_count", "sum"),
                posting_count=("posting_id", "count"),
                avg_salary=("salary_mid", "mean"),
                school_major_strength_score=("school_major_strength_score", "mean"),
            )
        )

        emp = employment.groupby(["school_id", "major_code"], as_index=False).agg(
            employed_count=("employment_id", "count"),
            match_score=("match_score", "mean"),
        )
        emp = emp.merge(graduates, on=["school_id", "major_code"], how="left")
        emp["employment_rate"] = (emp["employed_count"] / emp["graduate_count"].clip(lower=1)).clip(0.35, 0.98)
        features = features.merge(emp[["school_id", "major_code", "employment_rate", "match_score"]], on=["school_id", "major_code"], how="left")

        enrollment["enrollment_pressure"] = (enrollment["applicant_count"] / enrollment["planned_quota"].clip(lower=1) * enrollment["first_choice_rate"]).clip(0.3, 12)
        features = features.merge(enrollment[["school_id", "major_code", "enrollment_pressure"]], on=["school_id", "major_code"], how="left")
        features = features.merge(policy, on=["month", "industry_id", "major_code"], how="left")
        features = features.merge(schools[["school_id", "school_name"]], on="school_id", how="left")
        features = features.merge(majors, on="major_code", how="left")
        features = features.merge(industries, on="industry_id", how="left")
        features = features.merge(jobs, on="job_category_id", how="left")

        features["policy_heat"] = features["policy_heat"].fillna(features["policy_heat"].median()).fillna(55)
        features["employment_rate"] = features["employment_rate"].fillna(0.72)
        features["match_score"] = features["match_score"].fillna(68)
        features["avg_match_score"] = features["match_score"]
        features["enrollment_pressure"] = features["enrollment_pressure"].fillna(2.8)
        features["skill_gap_score"] = (100 - features["match_score"]).clip(8, 55)
        features["major_strength_score"] = features["school_major_strength_score"]
        features["school_industry_affinity"] = 0.72 + (features["school_major_strength_score"] / 100) * 0.2
        features = features.fillna({
            "school_name": "",
            "major_name": "",
            "industry_name": "",
            "job_category_name": "",
            "demand_count_sum": 0,
            "posting_count": 0,
            "avg_salary": 0,
        })

        cols = [
            "month", "school_id", "school_name", "major_code", "major_name", "industry_id", "industry_name",
            "job_category_id", "job_category_name", "demand_count_sum", "posting_count", "avg_salary",
            "policy_heat", "employment_rate", "match_score", "avg_match_score", "skill_gap_score",
            "enrollment_pressure", "school_major_strength_score", "major_strength_score", "school_industry_affinity",
        ]
        out = features[cols]
        leading_summary = (
            employment.merge(schools[["school_id", "school_name"]], on="school_id", how="left")
            .assign(
                is_leading=lambda df: df.get("is_shanghai_leading_employment", 0).fillna(0).astype(int),
                ai_flag=lambda df: (df.get("leading_industry_code", "") == "AI").astype(int),
                ic_flag=lambda df: (df.get("leading_industry_code", "") == "IC").astype(int),
                biomed_flag=lambda df: (df.get("leading_industry_code", "") == "BIOMED").astype(int),
                leading_salary=lambda df: df["salary"].where(df.get("is_shanghai_leading_employment", 0).fillna(0).astype(int) == 1),
            )
            .groupby(["school_id", "school_name", "employment_month"], as_index=False)
            .agg(
                total_employment_count=("employment_id", "count"),
                leading_industry_employment_count=("is_leading", "sum"),
                ai_employment_count=("ai_flag", "sum"),
                ic_employment_count=("ic_flag", "sum"),
                biomed_employment_count=("biomed_flag", "sum"),
                avg_salary=("salary", "mean"),
                leading_avg_salary=("leading_salary", "mean"),
            )
            .rename(columns={"employment_month": "month"})
        )
        leading_summary["leading_industry_employment_rate"] = (
            leading_summary["leading_industry_employment_count"] / leading_summary["total_employment_count"].clip(lower=1)
        ).round(4)
        leading_summary["avg_salary"] = leading_summary["avg_salary"].round(2)
        leading_summary["leading_avg_salary"] = leading_summary["leading_avg_salary"].fillna(0).round(2)

        emp_detail = (
            employment.merge(schools[["school_id", "school_name"]], on="school_id", how="left")
            .merge(majors, on="major_code", how="left")
            .merge(industries, on="industry_id", how="left")
            .merge(enterprises, on="enterprise_id", how="left")
        )
        salary_threshold = emp_detail.groupby(["school_id", "major_code"])["salary"].transform(lambda s: s.quantile(0.70))
        salary_median = emp_detail.groupby(["school_id", "major_code"])["salary"].transform("median")
        emp_detail["is_leading"] = emp_detail.get("is_shanghai_leading_employment", 0).fillna(0).astype(int)
        high_tech_flag = emp_detail.get("is_high_tech", 0).fillna(0).astype(int)
        emp_detail["is_high_quality"] = (
            (emp_detail["salary"] >= salary_threshold.fillna(emp_detail["salary"].median()))
            | ((emp_detail["is_leading"] == 1) & (emp_detail["salary"] >= salary_median.fillna(emp_detail["salary"].median())))
            | ((high_tech_flag == 1) & (emp_detail["salary"] >= salary_median.fillna(emp_detail["salary"].median())))
        ).astype(int)

        grad_by_school_major = pd.read_sql("SELECT school_id, major_code, COUNT(*) graduate_count FROM fact_graduate GROUP BY school_id, major_code", engine)

        def build_compare(scope_cols: list[str]) -> pd.DataFrame:
            grouped = emp_detail.groupby(scope_cols, as_index=False).agg(
                employment_count=("employment_id", "count"),
                avg_salary=("salary", "mean"),
                high_quality_employment_count=("is_high_quality", "sum"),
                leading_industry_employment_count=("is_leading", "sum"),
            )
            industry_counts = (
                emp_detail.groupby(scope_cols + ["industry_name"], as_index=False)
                .agg(industry_count=("employment_id", "count"))
            )
            top_industry = (
                industry_counts.sort_values(scope_cols + ["industry_count"], ascending=[True] * len(scope_cols) + [False])
                .groupby(scope_cols, as_index=False)
                .first()
                .rename(columns={"industry_name": "top_industry_name", "industry_count": "top_industry_count"})
            )
            distributions = []
            for key, part in industry_counts.groupby(scope_cols):
                if not isinstance(key, tuple):
                    key = (key,)
                total = max(float(part["industry_count"].sum()), 1.0)
                item = {col: val for col, val in zip(scope_cols, key)}
                item["industry_distribution_json"] = part.sort_values("industry_count", ascending=False).assign(
                    rate=lambda df: (df["industry_count"] / total).round(4)
                )[["industry_name", "industry_count", "rate"]].rename(columns={"industry_count": "count"}).to_json(orient="records", force_ascii=False)
                distributions.append(item)
            dist_df = pd.DataFrame(distributions)
            result = grouped.merge(top_industry, on=scope_cols, how="left").merge(dist_df, on=scope_cols, how="left")
            result["top_industry_rate"] = result["top_industry_count"].fillna(0) / result["employment_count"].clip(lower=1)
            result["high_quality_employment_rate"] = result["high_quality_employment_count"] / result["employment_count"].clip(lower=1)
            result["leading_industry_employment_rate"] = result["leading_industry_employment_count"] / result["employment_count"].clip(lower=1)
            return result

        school_major_compare = build_compare(["school_id", "school_name", "major_code", "major_name", "discipline_category"])
        school_major_compare = school_major_compare.merge(grad_by_school_major, on=["school_id", "major_code"], how="left")
        school_major_compare["graduate_count"] = school_major_compare["graduate_count"].fillna(school_major_compare["employment_count"]).astype(int)
        school_major_compare["employment_rate"] = (school_major_compare["employment_count"] / school_major_compare["graduate_count"].clip(lower=1)).clip(0, 1)

        school_all_compare = build_compare(["school_id", "school_name"])
        grad_by_school = graduates.groupby("school_id", as_index=False).agg(graduate_count=("graduate_count", "sum"))
        school_all_compare = school_all_compare.merge(grad_by_school, on="school_id", how="left")
        school_all_compare["graduate_count"] = school_all_compare["graduate_count"].fillna(school_all_compare["employment_count"]).astype(int)
        school_all_compare["employment_rate"] = (school_all_compare["employment_count"] / school_all_compare["graduate_count"].clip(lower=1)).clip(0, 1)
        school_all_compare["major_code"] = "ALL"
        school_all_compare["major_name"] = "全部专业"
        school_all_compare["discipline_category"] = "全部"

        school_compare = pd.concat([school_all_compare, school_major_compare], ignore_index=True, sort=False)
        school_compare["avg_salary"] = school_compare["avg_salary"].round(2)
        for col in ["employment_rate", "high_quality_employment_rate", "leading_industry_employment_rate", "top_industry_rate"]:
            school_compare[col] = school_compare[col].fillna(0).round(4)
        school_compare["top_industry_name"] = school_compare["top_industry_name"].fillna("")
        school_compare["top_industry_count"] = school_compare["top_industry_count"].fillna(0).astype(int)
        school_compare["industry_distribution_json"] = school_compare["industry_distribution_json"].fillna("[]")
        school_compare = school_compare[[
            "school_id", "school_name", "major_code", "major_name", "discipline_category",
            "employment_count", "graduate_count", "employment_rate", "avg_salary",
            "high_quality_employment_count", "high_quality_employment_rate",
            "leading_industry_employment_count", "leading_industry_employment_rate",
            "top_industry_name", "top_industry_count", "top_industry_rate", "industry_distribution_json",
        ]]
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE ads_job_demand_features"))
            out.to_sql("ads_job_demand_features", conn, if_exists="append", index=False, chunksize=4000, method="multi")
            conn.execute(text("TRUNCATE TABLE ads_leading_industry_employment_summary"))
            leading_summary.to_sql("ads_leading_industry_employment_summary", conn, if_exists="append", index=False, chunksize=2000, method="multi")
            conn.execute(text("TRUNCATE TABLE ads_school_compare_summary"))
            school_compare.to_sql("ads_school_compare_summary", conn, if_exists="append", index=False, chunksize=2000, method="multi")
            log_chain(conn, "SUCCESS", len(out), started)
        print(f"ads_job_demand_features: {len(out)}")
        print(f"ads_leading_industry_employment_summary: {len(leading_summary)}")
        print(f"ads_school_compare_summary: {len(school_compare)}")
    except Exception as exc:
        with engine.begin() as conn:
            log_chain(conn, "FAIL", 0, started, str(exc))
        raise


if __name__ == "__main__":
    main()
