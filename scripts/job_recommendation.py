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


def norm(values):
    series = pd.Series(values).astype(float).fillna(0)
    span = series.max() - series.min()
    if span <= 1e-9:
        return pd.Series([0.55] * len(series), index=series.index)
    return (series - series.min()) / span


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    started = datetime.now()
    grads = pd.read_sql(
        """
        SELECT g.graduate_id, g.school_id, s.school_name, g.major_code, m.major_name,
               g.skill_tags, g.job_intention_tags, g.gpa_level, g.internship_count
        FROM fact_graduate g
        JOIN dim_school s ON s.school_id=g.school_id
        JOIN dim_major_catalog m ON m.major_code=g.major_code
        WHERE g.graduation_year=2026
        """,
        engine,
    )
    forecast = pd.read_sql(
        """
        SELECT f.school_id, f.major_code, f.major_name, f.industry_id, f.industry_name,
               f.job_category_id, f.job_category_name,
               SUM(f.predicted_demand_count) demand_12m, AVG(f.avg_salary) avg_salary
        FROM ads_job_demand_forecast f
        GROUP BY f.school_id, f.major_code, f.major_name, f.industry_id, f.industry_name, f.job_category_id, f.job_category_name
        """,
        engine,
    )
    jobs = pd.read_sql("SELECT job_category_id, job_category_name, skill_tags FROM dim_job_category", engine)
    enterprises = pd.read_sql(
        """
        SELECT enterprise_id, enterprise_name, industry_id, city, district,
               salary_factor, hiring_stability_factor, is_high_tech, is_specialized_new
        FROM dim_enterprise
        """,
        engine,
    )
    bridge = pd.read_sql(
        "SELECT school_id, major_code, is_ace_major, school_major_strength_score FROM bridge_school_major",
        engine,
    )
    employment_quality = pd.read_sql(
        """
        SELECT school_id, major_code, industry_id, job_category_id,
               AVG(CASE WHEN employment_quality_level IN ('A','B') THEN 1 ELSE 0 END) quality_rate
        FROM fact_employment
        GROUP BY school_id, major_code, industry_id, job_category_id
        """,
        engine,
    )

    if grads.empty or forecast.empty or enterprises.empty:
        raise RuntimeError("就业推荐生成失败：毕业生、预测结果或企业维度表为空")

    forecast = forecast.merge(jobs, on=["job_category_id", "job_category_name"], how="left")
    forecast = forecast.merge(bridge, on=["school_id", "major_code"], how="left")
    forecast = forecast.merge(employment_quality, on=["school_id", "major_code", "industry_id", "job_category_id"], how="left")
    forecast = forecast.fillna({"is_ace_major": 0, "school_major_strength_score": 60, "quality_rate": 0.58, "skill_tags": ""})
    forecast["demand_score"] = norm(forecast["demand_12m"])

    enterprise_by_industry = {iid: df.reset_index(drop=True) for iid, df in enterprises.groupby("industry_id")}
    rows = []
    max_per_school = {"SHU007": 3600}
    selected = []
    for school_id, group in grads.groupby("school_id"):
        limit = max_per_school.get(school_id, min(1600, len(group)))
        selected.append(group.sort_values(["internship_count", "graduate_id"], ascending=[False, True]).head(limit))
    selected_grads = pd.concat(selected, ignore_index=True)

    for _, grad in selected_grads.iterrows():
        pool = forecast[(forecast["school_id"] == grad["school_id"]) & (forecast["major_code"] == grad["major_code"])].copy()
        if pool.empty:
            pool = forecast[forecast["major_code"] == grad["major_code"]].copy()
        if pool.empty:
            pool = forecast.sort_values("demand_12m", ascending=False).head(30).copy()
        grad_skills = set(str(grad["skill_tags"]).replace("|", "、").split("、"))
        grad_intents = set(str(grad["job_intention_tags"]).replace("|", "、").split("、"))
        pool["skill_overlap"] = pool["skill_tags"].apply(
            lambda raw: len(grad_skills.intersection(set(str(raw).replace("|", "、").split("、")))) / max(len(grad_skills), 1)
        )
        pool["intent_overlap"] = pool["job_category_name"].apply(lambda name: 1.0 if name in grad_intents else 0.35)
        pool["base_score"] = (
            0.34 * pool["demand_score"]
            + 0.24 * pool["skill_overlap"]
            + 0.16 * pool["intent_overlap"]
            + 0.12 * pool["quality_rate"]
            + 0.08 * (pool["school_major_strength_score"] / 100)
            + 0.06 * pool["is_ace_major"].astype(float)
        )
        choices = pool.sort_values(["base_score", "demand_12m"], ascending=False).head(8).reset_index(drop=True)
        used_enterprises = set()
        for rank_no, job in choices.head(3).iterrows():
            ent_pool = enterprise_by_industry.get(job["industry_id"], enterprises).copy()
            if len(ent_pool) == 0:
                ent_pool = enterprises
            ent = ent_pool.iloc[(int(grad["graduate_id"]) + rank_no * 17) % len(ent_pool)]
            if int(ent["enterprise_id"]) in used_enterprises and len(ent_pool) > 1:
                ent = ent_pool.iloc[(int(grad["graduate_id"]) + rank_no * 23 + 5) % len(ent_pool)]
            used_enterprises.add(int(ent["enterprise_id"]))
            enterprise_score = 0.08 * float(ent["salary_factor"]) + 0.06 * float(ent["hiring_stability_factor"])
            raw_score = 0.58 + float(job["base_score"]) * 0.30 + enterprise_score - rank_no * 0.045
            similarity = round(max(0.52, min(0.91, raw_score)), 4)
            confidence = "high" if similarity >= 0.75 else ("medium" if similarity >= 0.64 else "low")
            rows.append(
                {
                    "graduate_id": int(grad["graduate_id"]),
                    "school_id": grad["school_id"],
                    "school_name": grad["school_name"],
                    "major_code": grad["major_code"],
                    "major_name": grad["major_name"],
                    "enterprise_id": int(ent["enterprise_id"]),
                    "enterprise_name": ent["enterprise_name"],
                    "industry_id": job["industry_id"],
                    "industry_name": job["industry_name"],
                    "job_category_id": int(job["job_category_id"]),
                    "job_category_name": job["job_category_name"],
                    "similarity_score": similarity,
                    "matching_score": similarity,
                    "confidence_level": confidence,
                    "predicted_demand_count": float(job["demand_12m"]),
                    "salary_reference": round(float(job["avg_salary"]) * float(ent["salary_factor"]), 2),
                    "rank_no": rank_no + 1,
                    "reason_text": (
                        f"{grad['major_name']}与{job['job_category_name']}岗位技能和求职意向匹配，"
                        f"未来12个月需求约{int(job['demand_12m'])}人。"
                    ),
                    "recommendation_reason": (
                        f"{grad['major_name']}与{job['job_category_name']}岗位技能和求职意向匹配，"
                        f"未来12个月需求约{int(job['demand_12m'])}人。"
                    ),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    out = pd.DataFrame(rows)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ads_job_recommendation"))
        out.to_sql("ads_job_recommendation", conn, if_exists="append", index=False, chunksize=3000, method="multi")
        conn.execute(
            text(
                """
                INSERT INTO ads_algorithm_chain_log
                (batch_id, stage_order, stage_name, input_tables, output_tables, algorithm_name, status, row_count, started_at, finished_at, cost_seconds)
                VALUES (:batch_id, 5, '就业推荐', 'fact_graduate,ads_job_demand_forecast,dim_enterprise', 'ads_job_recommendation', 'hybrid similarity recommendation', 'SUCCESS', :row_count, :started_at, NOW(), TIMESTAMPDIFF(SECOND,:started_at,NOW()))
                """
            ),
            {"batch_id": datetime.now().strftime("%Y%m%d%H%M%S"), "row_count": len(out), "started_at": started},
        )

    shu = out[out["school_id"] == "SHU007"]
    top1 = out[out["rank_no"] == 1]["similarity_score"].mean()
    print(
        f"ads_job_recommendation: {len(out)}, SHU_students={shu['graduate_id'].nunique()}, "
        f"enterprises={out['enterprise_id'].nunique()}, top1={top1:.3f}"
    )


if __name__ == "__main__":
    main()
