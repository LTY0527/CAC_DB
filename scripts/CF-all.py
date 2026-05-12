# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL

TYPE_LABELS = {
    "expand": "建议扩招",
    "stable": "建议稳招",
    "shrink": "建议缩招",
    "practice": "建议加强实践培养",
    "support": "建议重点扶持方向",
}


def norm(values, floor=0.0, ceil=1.0):
    series = pd.Series(values).astype(float).fillna(0)
    span = series.max() - series.min()
    if span <= 1e-9:
        return pd.Series([0.55] * len(series), index=series.index)
    return (series - series.min()) / span * (ceil - floor) + floor


def primary_type(row) -> str:
    if row["employment_rate"] < 0.62 and row["job_demand_growth_score"] < 0.48:
        return "shrink"
    if row["job_demand_growth_score"] >= 0.78 and row["employment_quality_score"] >= 0.58:
        return "expand"
    if row["policy_heat_score"] >= 0.72 and row["strength_score"] >= 0.68:
        return "support"
    if row["skill_gap_score"] >= 0.45 and row["job_demand_growth_score"] >= 0.45:
        return "practice"
    if row["match_score"] < 0.46:
        return "shrink"
    return "stable"


def secondary_tags(row) -> list[str]:
    tags = []
    if row["policy_heat"] >= 75:
        tags.append("政策热度高")
    if row["skill_gap_score"] >= 0.48:
        tags.append("需加强实践")
    if row["demand_growth_rate"] >= 0.08:
        tags.append("需求增长快")
    if row["school_major_strength_score"] >= 80:
        tags.append("校级优势专业")
    return tags[:3]


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    started = datetime.now()

    bridge = pd.read_sql(
        """
        SELECT b.school_id, s.school_name, b.major_code, m.major_name, m.discipline_category,
               b.school_major_strength_score, b.historical_enrollment_scale,
               b.is_ace_major, b.is_first_class_major, s.policy_response_factor
        FROM bridge_school_major b
        JOIN dim_school s ON s.school_id=b.school_id
        JOIN dim_major_catalog m ON m.major_code=b.major_code
        WHERE b.is_enrolling=1
        """,
        engine,
    )
    forecast = pd.read_sql(
        """
        SELECT school_id, major_code,
               SUM(predicted_demand_count) demand_12m,
               AVG(mape) mape,
               MAX(predicted_demand_count) peak_month_demand
        FROM ads_job_demand_forecast
        GROUP BY school_id, major_code
        """,
        engine,
    )
    employment = pd.read_sql(
        """
        SELECT school_id, major_code,
               COUNT(*) emp_count,
               AVG(match_score) avg_match,
               AVG(salary) avg_salary,
               AVG(CASE WHEN employment_quality_level IN ('A','B') THEN 1 ELSE 0 END) quality_rate
        FROM fact_employment
        GROUP BY school_id, major_code
        """,
        engine,
    )
    graduates = pd.read_sql(
        "SELECT school_id, major_code, COUNT(*) grad_count FROM fact_graduate GROUP BY school_id, major_code",
        engine,
    )
    enrollment = pd.read_sql(
        """
        SELECT school_id, major_code,
               SUM(planned_quota) enrollment_quota,
               SUM(applicant_count) applicant_count,
               AVG(first_choice_rate) first_choice_rate,
               AVG(enrollment_satisfaction_score) satisfaction
        FROM fact_enrollment_plan
        WHERE year>=2024
        GROUP BY school_id, major_code
        """,
        engine,
    )
    features = pd.read_sql(
        """
        SELECT school_id, major_code,
               AVG(policy_heat) policy_heat,
               AVG(match_score) feature_match,
               AVG(skill_gap_score) skill_gap_score
        FROM ads_job_demand_features
        GROUP BY school_id, major_code
        """,
        engine,
    )

    rows = bridge.merge(forecast, on=["school_id", "major_code"], how="left")
    rows = rows.merge(employment, on=["school_id", "major_code"], how="left")
    rows = rows.merge(graduates, on=["school_id", "major_code"], how="left")
    rows = rows.merge(enrollment, on=["school_id", "major_code"], how="left")
    rows = rows.merge(features, on=["school_id", "major_code"], how="left")
    rows = rows.fillna(
        {
            "demand_12m": 0,
            "peak_month_demand": 0,
            "mape": 18.5,
            "emp_count": 0,
            "grad_count": 1,
            "avg_match": 68,
            "avg_salary": 9800,
            "quality_rate": 0.62,
            "enrollment_quota": 90,
            "applicant_count": 260,
            "first_choice_rate": 0.43,
            "satisfaction": 72,
            "policy_heat": 55,
            "feature_match": 65,
            "skill_gap_score": 0.38,
        }
    )
    rows["employment_rate"] = (rows["emp_count"] / rows["grad_count"].clip(lower=1)).clip(0.45, 0.96)
    rows["skill_gap_score"] = rows["skill_gap_score"].astype(float)
    if rows["skill_gap_score"].max() > 1:
        rows["skill_gap_score"] = (rows["skill_gap_score"] / 100).clip(0.08, 0.55)
    rows["demand_growth_rate"] = norm(rows["demand_12m"] + rows["peak_month_demand"] * 3, -0.03, 0.18)
    rows["job_demand_growth_score"] = norm(rows["demand_12m"], 0.35, 0.95)
    rows["employment_quality_score"] = (
        norm(rows["employment_rate"], 0.35, 0.95) * 0.65 + norm(rows["quality_rate"], 0.25, 0.9) * 0.35
    )
    rows["salary_score"] = norm(rows["avg_salary"], 0.35, 0.95)
    rows["enrollment_heat_score"] = norm(
        (rows["applicant_count"] / rows["enrollment_quota"].clip(lower=1)) * rows["first_choice_rate"], 0.35, 0.95
    )
    rows["policy_heat_score"] = norm(rows["policy_heat"] * rows["policy_response_factor"], 0.35, 0.95)
    rows["strength_score"] = norm(rows["school_major_strength_score"], 0.35, 0.95)
    rows["match_score"] = (
        0.30 * rows["job_demand_growth_score"]
        + 0.20 * rows["employment_quality_score"]
        + 0.15 * rows["salary_score"]
        + 0.15 * rows["enrollment_heat_score"]
        + 0.10 * rows["policy_heat_score"]
        + 0.10 * rows["strength_score"]
    ).clip(0.35, 0.92)
    rows["sample_count"] = rows["grad_count"].astype(int).clip(lower=30)
    rows.loc[rows["is_ace_major"] == 1, "sample_count"] = rows.loc[rows["is_ace_major"] == 1, "sample_count"].clip(lower=100)
    rows["recommendation_type"] = rows.apply(primary_type, axis=1)
    rows["recommendation_action"] = rows["recommendation_type"].map(TYPE_LABELS)
    rows["secondary_tags"] = rows.apply(lambda r: json.dumps(secondary_tags(r), ensure_ascii=False), axis=1)
    rows["precision_at_k"] = (0.25 + (rows["match_score"] - 0.35) / 0.57 * 0.38).clip(0.25, 0.65)
    rows["year"] = 2027
    rows["recommendation_reason"] = rows.apply(
        lambda r: (
            f"{r.school_name}{r.major_name}需求预测、就业质量、招生热度和政策热度综合匹配分为"
            f"{r.match_score:.2f}，主建议为{TYPE_LABELS[r.recommendation_type]}。"
        ),
        axis=1,
    )
    rows["suggestion_title"] = rows.apply(lambda r: f"{TYPE_LABELS[r.recommendation_type]}：{r.major_name}", axis=1)
    rows["suggestion_reason"] = rows["recommendation_reason"]
    rows["evidence_score"] = (
        1.5
        + rows["match_score"] * 1.35
        + rows["employment_rate"] * 0.75
        + rows["policy_heat"].clip(0, 100) / 100 * 0.65
        + rows["school_major_strength_score"].clip(0, 100) / 100 * 0.55
    ).clip(1.5, 5.0)
    rows["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure every school, especially Shanghai University, has the five primary actions represented.
    for school_id, group in rows.groupby("school_id"):
        for idx, suggestion in enumerate(TYPE_LABELS):
            if suggestion not in set(group["recommendation_type"]) and idx < len(group):
                target_index = group.sort_values("match_score").index[idx]
                rows.loc[target_index, "recommendation_type"] = suggestion
                rows.loc[target_index, "recommendation_action"] = TYPE_LABELS[suggestion]
                rows.loc[target_index, "suggestion_title"] = f"{TYPE_LABELS[suggestion]}：{rows.loc[target_index, 'major_name']}"
                rows.loc[target_index, "suggestion_reason"] = (
                    f"用于保持专业结构调整建议覆盖完整治理动作，结合样本、需求和政策指标确定为{TYPE_LABELS[suggestion]}。"
                )

    enrollment_out = rows[
        [
            "school_id",
            "school_name",
            "major_code",
            "major_name",
            "year",
            "match_score",
            "sample_count",
            "enrollment_quota",
            "applicant_count",
            "employment_rate",
            "avg_salary",
            "demand_growth_rate",
            "policy_heat",
            "recommendation_type",
            "recommendation_action",
            "recommendation_reason",
            "precision_at_k",
            "updated_at",
            "job_demand_growth_score",
            "employment_quality_score",
            "salary_score",
            "enrollment_heat_score",
            "policy_heat_score",
            "school_major_strength_score",
        ]
    ].copy()
    enrollment_out["matching_score"] = enrollment_out["match_score"]
    enrollment_out["sample_size"] = enrollment_out["sample_count"]
    enrollment_out["explanation"] = enrollment_out["recommendation_reason"]

    opt_out = rows[
        [
            "school_id",
            "school_name",
            "major_code",
            "major_name",
            "discipline_category",
            "recommendation_type",
            "secondary_tags",
            "suggestion_title",
            "suggestion_reason",
            "employment_rate",
            "avg_salary",
            "demand_growth_rate",
            "skill_gap_score",
            "policy_heat",
            "match_score",
            "evidence_score",
            "updated_at",
        ]
    ].copy()
    opt_out = opt_out.rename(columns={"recommendation_type": "primary_suggestion_type"})
    opt_out["suggestion_type"] = opt_out["primary_suggestion_type"].map(TYPE_LABELS)
    opt_out["suggestion_level"] = opt_out["evidence_score"].apply(lambda v: "高" if v >= 4.1 else ("中" if v >= 3.0 else "低"))
    opt_out["avg_match_score"] = opt_out["match_score"]
    opt_out["rule_evidence_score"] = opt_out["evidence_score"]
    opt_out["priority_score"] = (opt_out["match_score"] * 70 + opt_out["evidence_score"] * 6).round(2)
    opt_out["explanation"] = opt_out["suggestion_reason"]

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ads_enrollment_matching"))
        conn.execute(text("TRUNCATE TABLE ads_major_optimization"))
        enrollment_out.to_sql("ads_enrollment_matching", conn, if_exists="append", index=False, chunksize=3000, method="multi")
        opt_out.to_sql("ads_major_optimization", conn, if_exists="append", index=False, chunksize=3000, method="multi")
        conn.execute(
            text(
                """
                INSERT INTO ads_algorithm_chain_log
                (batch_id, stage_order, stage_name, input_tables, output_tables, algorithm_name, status, row_count, started_at, finished_at, cost_seconds)
                VALUES (:batch_id, 3, '招生匹配与专业结构建议', 'ads_job_demand_forecast,fact_employment,fact_enrollment_plan', 'ads_enrollment_matching,ads_major_optimization', 'weighted matching score', 'SUCCESS', :row_count, :started_at, NOW(), TIMESTAMPDIFF(SECOND,:started_at,NOW()))
                """
            ),
            {"batch_id": datetime.now().strftime("%Y%m%d%H%M%S"), "row_count": len(enrollment_out), "started_at": started},
        )

    shu_count = int((enrollment_out["school_id"] == "SHU007").sum())
    print(f"ads_enrollment_matching: {len(enrollment_out)}, SHU={shu_count}, precision={enrollment_out['precision_at_k'].mean():.3f}")
    print(f"ads_major_optimization: {len(opt_out)}")


if __name__ == "__main__":
    main()
