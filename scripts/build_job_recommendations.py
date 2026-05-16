# -*- coding: utf-8 -*-
"""Build batch job recommendations from the current schema tables."""

from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL


REQUIRED_TABLES = (
    "fact_graduate",
    "fact_job_posting",
    "dim_school",
    "dim_major_catalog",
    "dim_enterprise",
    "dim_industry",
    "dim_job_category",
    "ads_job_demand_forecast",
    "ads_job_recommendation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ads_job_recommendation from current-schema source tables.")
    parser.add_argument("--school-id", default="ALL", help="School id to generate, or ALL for all schools.")
    parser.add_argument("--limit", type=int, default=5000, help="Maximum graduates to cover. Use 0 for all graduates.")
    parser.add_argument("--top-k", type=int, default=3, help="Recommendations per graduate.")
    return parser.parse_args()


def normalize_school_id(value: str | None) -> str | None:
    raw = (value or "").strip()
    if raw.lower() in {"", "all", "__all__", "全部", "全部学校"}:
        return None
    return raw


def split_tags(value: object) -> set[str]:
    text_value = str(value or "").replace("|", "、").replace(",", "、")
    return {item.strip() for item in text_value.split("、") if item.strip()}


def norm(values: pd.Series, floor: float = 0.0, ceil: float = 1.0) -> pd.Series:
    series = pd.to_numeric(values, errors="coerce").fillna(0.0)
    span = series.max() - series.min()
    if span <= 1e-9:
        return pd.Series([0.55] * len(series), index=series.index)
    return (series - series.min()) / span * (ceil - floor) + floor


def table_exists(conn, table_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                  AND table_type = 'BASE TABLE'
                """
            ),
            {"table_name": table_name},
        ).scalar()
    )


def table_columns(conn, table_name: str) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        )
    }


def ensure_required_tables(engine) -> None:
    with engine.connect() as conn:
        missing = [table_name for table_name in REQUIRED_TABLES if not table_exists(conn, table_name)]
    if missing:
        raise RuntimeError(f"Missing required current-schema tables: {', '.join(missing)}")


def read_graduates(engine, school_id: str | None) -> pd.DataFrame:
    where_sql = "WHERE g.graduation_year=2026"
    params: dict[str, str] = {}
    if school_id:
        where_sql += " AND g.school_id=:school_id"
        params["school_id"] = school_id
    return pd.read_sql(
        text(
            f"""
            SELECT g.graduate_id, g.school_id, s.school_name, g.major_code, m.major_name,
                   m.major_class, g.skill_tags, g.job_intention_tags, g.gpa_level, g.internship_count
            FROM fact_graduate g
            JOIN dim_school s ON s.school_id=g.school_id
            JOIN dim_major_catalog m ON m.major_code=g.major_code
            {where_sql}
            """
        ),
        engine,
        params=params,
    )


def select_graduates(grads: pd.DataFrame, limit: int, school_id: str | None) -> pd.DataFrame:
    if grads.empty or limit <= 0 or len(grads) <= limit:
        return grads.sort_values(["school_id", "internship_count", "graduate_id"], ascending=[True, False, True]).reset_index(drop=True)

    if school_id:
        return grads.sort_values(["internship_count", "graduate_id"], ascending=[False, True]).head(limit).reset_index(drop=True)

    school_count = max(grads["school_id"].nunique(), 1)
    per_school = max(1, math.ceil(limit / school_count))
    selected = (
        grads.sort_values(["school_id", "internship_count", "graduate_id"], ascending=[True, False, True])
        .groupby("school_id", group_keys=False)
        .head(per_school)
    )
    return selected.sort_values(["school_id", "internship_count", "graduate_id"], ascending=[True, False, True]).head(limit).reset_index(drop=True)


def read_candidates(engine) -> pd.DataFrame:
    forecast = pd.read_sql(
        """
        SELECT f.school_id, f.school_name, f.major_code, f.major_name,
               f.industry_id, COALESCE(i.industry_name, f.industry_name) AS industry_name,
               f.job_category_id, f.job_category_name,
               SUM(f.predicted_demand_count) AS forecast_demand_12m,
               AVG(f.avg_salary) AS forecast_avg_salary,
               AVG(f.demand_growth_rate) AS demand_growth_rate
        FROM ads_job_demand_forecast f
        LEFT JOIN dim_industry i ON i.industry_id=f.industry_id
        GROUP BY f.school_id, f.school_name, f.major_code, f.major_name,
                 f.industry_id, COALESCE(i.industry_name, f.industry_name),
                 f.job_category_id, f.job_category_name
        """,
        engine,
    )
    posting = pd.read_sql(
        """
        SELECT industry_id, job_category_id,
               SUM(demand_count) AS posting_demand,
               AVG((salary_min + salary_max) / 2) AS posting_avg_salary,
               COUNT(*) AS posting_count
        FROM fact_job_posting
        GROUP BY industry_id, job_category_id
        """,
        engine,
    )
    jobs = pd.read_sql(
        """
        SELECT job_category_id, job_category_name, industry_id, skill_tags,
               compatible_major_classes, salary_min_base, salary_max_base, demand_growth_level
        FROM dim_job_category
        """,
        engine,
    )
    bridge = pd.read_sql(
        """
        SELECT school_id, major_code, is_ace_major, is_first_class_major, school_major_strength_score
        FROM bridge_school_major
        """,
        engine,
    )
    employment_quality = pd.read_sql(
        """
        SELECT school_id, major_code, industry_id, job_category_id,
               AVG(CASE WHEN employment_quality_level IN ('A','B') THEN 1 ELSE 0 END) AS quality_rate,
               AVG(match_score) AS historical_match_score
        FROM fact_employment
        GROUP BY school_id, major_code, industry_id, job_category_id
        """,
        engine,
    )

    candidates = forecast.merge(posting, on=["industry_id", "job_category_id"], how="left")
    candidates = candidates.merge(jobs, on=["industry_id", "job_category_id", "job_category_name"], how="left")
    candidates = candidates.merge(bridge, on=["school_id", "major_code"], how="left")
    candidates = candidates.merge(employment_quality, on=["school_id", "major_code", "industry_id", "job_category_id"], how="left")
    candidates = candidates.fillna(
        {
            "forecast_demand_12m": 0,
            "forecast_avg_salary": 0,
            "demand_growth_rate": 0,
            "posting_demand": 0,
            "posting_avg_salary": 0,
            "posting_count": 0,
            "skill_tags": "",
            "compatible_major_classes": "",
            "is_ace_major": 0,
            "is_first_class_major": 0,
            "school_major_strength_score": 60,
            "quality_rate": 0.58,
            "historical_match_score": 65,
        }
    )
    candidates["avg_salary"] = candidates["forecast_avg_salary"].where(
        candidates["forecast_avg_salary"].astype(float) > 0,
        candidates["posting_avg_salary"],
    )
    candidates["demand_score"] = norm(candidates["forecast_demand_12m"] + candidates["posting_demand"] * 0.08, 0.25, 0.95)
    candidates["salary_score"] = norm(candidates["avg_salary"], 0.25, 0.95)
    return candidates


def read_enterprises(engine) -> pd.DataFrame:
    return pd.read_sql(
        """
        SELECT enterprise_id, enterprise_name, industry_id, city, district,
               salary_factor, hiring_stability_factor, is_high_tech, is_specialized_new
        FROM dim_enterprise
        """,
        engine,
    ).fillna({"salary_factor": 1.0, "hiring_stability_factor": 1.0, "is_high_tech": 0, "is_specialized_new": 0})


def deterministic_index(*parts: object, modulo: int) -> int:
    seed = "|".join(str(part) for part in parts)
    return sum((idx + 1) * ord(char) for idx, char in enumerate(seed)) % max(modulo, 1)


def build_rows(grads: pd.DataFrame, candidates: pd.DataFrame, enterprises: pd.DataFrame, top_k: int) -> list[dict]:
    enterprise_by_industry = {industry_id: group.reset_index(drop=True) for industry_id, group in enterprises.groupby("industry_id")}
    rows: list[dict] = []
    now_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for _, grad in grads.iterrows():
        pool = candidates[(candidates["school_id"] == grad["school_id"]) & (candidates["major_code"] == grad["major_code"])].copy()
        if pool.empty:
            pool = candidates[candidates["major_code"] == grad["major_code"]].copy()
        if pool.empty:
            pool = candidates.sort_values(["forecast_demand_12m", "posting_demand"], ascending=False).head(50).copy()
        elif len(pool) < top_k:
            fallback = candidates.sort_values(["forecast_demand_12m", "posting_demand"], ascending=False).head(50)
            pool = (
                pd.concat([pool, fallback], ignore_index=True)
                .drop_duplicates(["school_id", "major_code", "industry_id", "job_category_id"])
                .copy()
            )

        grad_skills = split_tags(grad["skill_tags"])
        grad_intents = split_tags(grad["job_intention_tags"])
        grad_major_class = str(grad.get("major_class") or "")

        pool["skill_overlap"] = pool["skill_tags"].apply(lambda raw: len(grad_skills & split_tags(raw)) / max(len(grad_skills), 1))
        pool["intent_overlap"] = pool["job_category_name"].apply(lambda name: 1.0 if str(name) in grad_intents else 0.35)
        pool["major_class_overlap"] = pool["compatible_major_classes"].apply(lambda raw: 1.0 if grad_major_class and grad_major_class in split_tags(raw) else 0.35)
        pool["base_score"] = (
            0.30 * pool["demand_score"].astype(float)
            + 0.20 * pool["skill_overlap"].astype(float)
            + 0.16 * pool["intent_overlap"].astype(float)
            + 0.12 * pool["major_class_overlap"].astype(float)
            + 0.10 * pool["quality_rate"].astype(float)
            + 0.07 * (pool["school_major_strength_score"].astype(float) / 100)
            + 0.05 * pool["salary_score"].astype(float)
        )

        choices = pool.sort_values(["base_score", "forecast_demand_12m", "posting_demand"], ascending=False).head(max(top_k, 1))
        used_enterprises: set[int] = set()
        for rank_index, (_, job) in enumerate(choices.iterrows(), start=1):
            ent_pool = enterprise_by_industry.get(job["industry_id"], enterprises).reset_index(drop=True)
            ent = ent_pool.iloc[deterministic_index(grad["graduate_id"], job["industry_id"], rank_index, modulo=len(ent_pool))]
            if int(ent["enterprise_id"]) in used_enterprises and len(ent_pool) > 1:
                ent = ent_pool.iloc[deterministic_index(grad["graduate_id"], job["industry_id"], rank_index, "alt", modulo=len(ent_pool))]
            used_enterprises.add(int(ent["enterprise_id"]))

            enterprise_score = 0.06 * float(ent["salary_factor"]) + 0.05 * float(ent["hiring_stability_factor"])
            innovation_score = 0.015 * float(ent["is_high_tech"]) + 0.015 * float(ent["is_specialized_new"])
            raw_score = 0.50 + float(job["base_score"]) * 0.36 + enterprise_score + innovation_score - (rank_index - 1) * 0.045
            similarity = round(max(0.52, min(0.94, raw_score)), 4)
            confidence = "high" if similarity >= 0.75 else ("medium" if similarity >= 0.64 else "low")
            demand_12m = float(job["forecast_demand_12m"])
            salary_reference = float(job["avg_salary"] or 0) * float(ent["salary_factor"] or 1)
            reason = (
                f"{grad['major_name']}与{job['job_category_name']}岗位技能、求职意向和区域需求匹配，"
                f"未来12个月预测需求约{int(round(demand_12m))}人。"
            )
            rows.append(
                {
                    "graduate_id": int(grad["graduate_id"]),
                    "school_id": grad["school_id"],
                    "school_name": grad["school_name"],
                    "major_code": grad["major_code"],
                    "major_name": grad["major_name"],
                    "enterprise_id": int(ent["enterprise_id"]),
                    "enterprise_name": ent["enterprise_name"],
                    "industry_id": int(job["industry_id"]),
                    "industry_name": job["industry_name"],
                    "job_category_id": int(job["job_category_id"]),
                    "job_category_name": job["job_category_name"],
                    "similarity_score": similarity,
                    "matching_score": similarity,
                    "confidence_level": confidence,
                    "predicted_demand_count": round(demand_12m, 2),
                    "salary_reference": round(salary_reference, 2),
                    "rank_no": rank_index,
                    "reason_text": reason,
                    "recommendation_reason": reason,
                    "updated_at": now_text,
                }
            )

    return rows


def write_rows(engine, rows: list[dict], school_id: str | None, started_at: datetime) -> None:
    out = pd.DataFrame(rows)
    with engine.begin() as conn:
        if school_id:
            conn.execute(text("DELETE FROM ads_job_recommendation WHERE school_id=:school_id"), {"school_id": school_id})
        else:
            conn.execute(text("TRUNCATE TABLE ads_job_recommendation"))

        if not out.empty:
            columns = table_columns(conn, "ads_job_recommendation")
            insert_columns = [column for column in out.columns if column in columns]
            out[insert_columns].to_sql("ads_job_recommendation", conn, if_exists="append", index=False, chunksize=3000, method="multi")

        if table_exists(conn, "ads_algorithm_chain_log"):
            conn.execute(
                text(
                    """
                    INSERT INTO ads_algorithm_chain_log
                    (batch_id, stage_order, stage_name, input_tables, output_tables, algorithm_name,
                     status, row_count, started_at, finished_at, cost_seconds)
                    VALUES (:batch_id, 7, '就业岗位批量推荐',
                            'fact_graduate,fact_job_posting,dim_school,dim_major_catalog,dim_enterprise,dim_industry,dim_job_category,ads_job_demand_forecast',
                            'ads_job_recommendation', 'hybrid similarity recommendation',
                            'SUCCESS', :row_count, :started_at, NOW(), TIMESTAMPDIFF(SECOND,:started_at,NOW()))
                    """
                ),
                {"batch_id": datetime.now().strftime("%Y%m%d%H%M%S"), "row_count": len(out), "started_at": started_at},
            )


def main() -> None:
    args = parse_args()
    school_id = normalize_school_id(args.school_id)
    top_k = max(1, args.top_k)
    started_at = datetime.now()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    ensure_required_tables(engine)

    grads = select_graduates(read_graduates(engine, school_id), args.limit, school_id)
    candidates = read_candidates(engine)
    enterprises = read_enterprises(engine)
    if grads.empty or candidates.empty or enterprises.empty:
        raise RuntimeError("Cannot build job recommendations because graduates, demand candidates, or enterprises are empty.")

    rows = build_rows(grads, candidates, enterprises, top_k)
    write_rows(engine, rows, school_id, started_at)

    result = pd.DataFrame(rows)
    covered = int(result["graduate_id"].nunique()) if not result.empty else 0
    school_count = int(result["school_id"].nunique()) if not result.empty else 0
    print(
        f"ads_job_recommendation: {len(result)}, covered_graduates={covered}, "
        f"schools={school_count}, top_k={top_k}"
    )


if __name__ == "__main__":
    main()
