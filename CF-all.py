# -*- coding: utf-8 -*-
"""
需求牵引的招生匹配与就业推荐脚本。

核心逻辑：
- 招生匹配：协同过滤基础分 + LSTM 岗位预测需求权重 + 专业供需缺口 + 技能适配。
- 就业推荐：学生画像与岗位画像余弦相似度，并叠加岗位预测需求信号。
"""

from __future__ import annotations

import io
import json
import math
import sys
from collections import Counter

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TOP_K = 3


def get_engine():
    return create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)


def read_table(engine, table_name: str) -> pd.DataFrame:
    try:
        return pd.read_sql(f"SELECT * FROM `{table_name}`", engine)
    except Exception:
        return pd.DataFrame()


def write_table(engine, df: pd.DataFrame, table_name: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
        df.to_sql(table_name, conn, if_exists="replace", index=False, chunksize=2000, method="multi")
    print(f"[CF] 已写入 {table_name}: {len(df)} 行")


def normalize(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0).astype(float)
    min_value, max_value = values.min(), values.max()
    if max_value <= min_value:
        return pd.Series(np.ones(len(values)) * 0.5, index=series.index)
    return (values - min_value) / (max_value - min_value)


def parse_skills(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if not value or pd.isna(value):
        return []
    try:
        parsed = json.loads(str(value))
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except Exception:
        pass
    text = str(value)
    for sep in ["、", ";", "；", "|"]:
        text = text.replace(sep, ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def build_enrollment_matching(student_df, academic_df, employment_df, forecast_df, gap_df, heatmap_df) -> pd.DataFrame:
    joined = student_df.merge(academic_df, on="student_id", how="inner").merge(employment_df, on="student_id", how="left")
    joined["avg_salary"] = pd.to_numeric(joined["avg_salary"], errors="coerce").fillna(0)
    joined["skill_score"] = joined["skill_level"].map({"初": 0.45, "中": 0.70, "高": 0.95}).fillna(0.60)

    base = (
        joined.groupby(["major_name", "origin_place", "school_level", "skill_level"], dropna=False)
        .agg(avg_salary=("avg_salary", "mean"), sample_size=("student_id", "count"), skill_level_score=("skill_score", "mean"))
        .reset_index()
    )
    base["matching_score"] = (normalize(base["avg_salary"]) * 0.65 + normalize(base["sample_size"]) * 0.20 + base["skill_level_score"] * 0.15).round(4)

    forecast_major = (
        forecast_df.groupby("major_name", dropna=False)
        .agg(forecast_demand_count=("predicted_demand_count", "sum"), demand_level=("demand_level", lambda s: Counter(s).most_common(1)[0][0]))
        .reset_index()
    )
    forecast_major["demand_weight"] = normalize(forecast_major["forecast_demand_count"]).round(4)

    gap_major = gap_df[["major_name", "gap_count", "gap_rate", "gap_level"]].copy() if not gap_df.empty else pd.DataFrame(columns=["major_name", "gap_count", "gap_rate", "gap_level"])
    gap_major["supply_demand_gap"] = pd.to_numeric(gap_major.get("gap_count", 0), errors="coerce").fillna(0)
    gap_major["gap_score"] = normalize(gap_major.get("gap_rate", 0)).round(4) if not gap_major.empty else []

    skill_major = (
        heatmap_df.groupby("major_name")["skill_weight"].sum().reset_index(name="skill_heat_score")
        if not heatmap_df.empty
        else pd.DataFrame(columns=["major_name", "skill_heat_score"])
    )
    skill_major["skill_adapt_score"] = normalize(skill_major.get("skill_heat_score", 0)).round(4) if not skill_major.empty else []

    result = base.merge(forecast_major, on="major_name", how="left").merge(gap_major, on="major_name", how="left").merge(skill_major, on="major_name", how="left")
    result["forecast_demand_count"] = result["forecast_demand_count"].fillna(0)
    result["demand_weight"] = result["demand_weight"].fillna(0.5)
    result["supply_demand_gap"] = result["supply_demand_gap"].fillna(0)
    result["gap_score"] = result["gap_score"].fillna(0.5)
    result["skill_adapt_score"] = result["skill_adapt_score"].fillna(result["skill_level_score"]).fillna(0.6)
    result["final_recommend_score"] = (
        0.45 * result["matching_score"]
        + 0.30 * result["demand_weight"]
        + 0.15 * result["gap_score"]
        + 0.10 * result["skill_adapt_score"]
    ).round(4)
    result["student_profile"] = result["origin_place"].fillna("未知生源") + " / " + result["school_level"].fillna("未知院校层次")
    result["region"] = result["origin_place"].fillna("未知地区")
    result["demand_level"] = result["demand_level"].fillna("中需求")
    result["recommendation_reason"] = result.apply(
        lambda row: (
            f"{row['major_name']}未来12个月预测岗位需求约{row['forecast_demand_count']:.0f}人，"
            f"专业供需缺口为{row['supply_demand_gap']:.0f}人；结合{row['student_profile']}画像和技能等级，"
            "建议作为需求牵引招生匹配的重点参考。"
        ),
        axis=1,
    )
    return result[
        [
            "major_name",
            "student_profile",
            "region",
            "skill_level",
            "matching_score",
            "demand_weight",
            "forecast_demand_count",
            "supply_demand_gap",
            "final_recommend_score",
            "recommendation_reason",
            "sample_size",
        ]
    ].sort_values(["final_recommend_score", "forecast_demand_count"], ascending=False)


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denom = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denom) if denom else 0.0


def build_job_recommendation(student_df, academic_df, job_df, forecast_df, heatmap_df) -> pd.DataFrame:
    students = student_df.merge(academic_df, on="student_id", how="inner").head(500)
    if students.empty or job_df.empty:
        return pd.DataFrame()

    forecast_key = (
        forecast_df.groupby(["major_name", "job_category"], dropna=False)
        .agg(predicted_demand_count=("predicted_demand_count", "sum"), demand_level=("demand_level", lambda s: Counter(s).most_common(1)[0][0]))
        .reset_index()
    )
    heatmap_key = (
        heatmap_df.groupby(["major_name", "job_category"])["skill_name"].apply(lambda s: list(s.head(8))).reset_index(name="required_skills")
        if not heatmap_df.empty
        else pd.DataFrame(columns=["major_name", "job_category", "required_skills"])
    )
    jobs = (
        job_df.sort_values("publish_date", ascending=False)
        .dropna(subset=["job_title", "job_category", "major_name"])
        .drop_duplicates(["employer_name", "job_title", "major_name", "job_category"])
        .head(1200)
        .merge(forecast_key, on=["major_name", "job_category"], how="left")
        .merge(heatmap_key, on=["major_name", "job_category"], how="left")
    )
    jobs["predicted_demand_count"] = jobs["predicted_demand_count"].fillna(0)
    jobs["demand_level"] = jobs["demand_level"].fillna("中需求")
    demand_norm = normalize(jobs["predicted_demand_count"])
    jobs["demand_norm"] = demand_norm

    rows = []
    skill_rank = {"初": 0.45, "中": 0.70, "高": 0.95}
    for student in students.itertuples(index=False):
        candidate = jobs[jobs["major_name"] == student.major_name].copy()
        if candidate.empty:
            candidate = jobs.copy()
        student_skill_score = skill_rank.get(getattr(student, "skill_level", "中"), 0.65)
        student_vector = np.array([student_skill_score, 1.0 if getattr(student, "edu_level", "本科") in ["硕士", "博士"] else 0.7, 0.8])
        scored = []
        for job in candidate.itertuples(index=False):
            required_skills = getattr(job, "required_skills", []) or parse_skills(getattr(job, "skill_keywords", ""))
            skill_match_score = min(1.0, 0.45 + 0.08 * len(required_skills)) * student_skill_score
            job_vector = np.array([skill_match_score, 0.9 if getattr(job, "education_requirement", "本科") in ["硕士", "博士"] else 0.7, 0.6 + 0.4 * getattr(job, "demand_norm", 0)])
            similarity = cosine_similarity(student_vector, job_vector)
            final_score = 0.65 * similarity + 0.25 * getattr(job, "demand_norm", 0) + 0.10 * skill_match_score
            scored.append((final_score, similarity, skill_match_score, job, required_skills))
        for rank_no, (final_score, similarity, skill_match_score, job, required_skills) in enumerate(sorted(scored, key=lambda x: x[0], reverse=True)[:TOP_K], start=1):
            rows.append(
                {
                    "student_id": getattr(student, "student_id"),
                    "student_name": getattr(student, "student_name"),
                    "major_name": getattr(student, "major_name"),
                    "employer_name": getattr(job, "employer_name"),
                    "job_title": getattr(job, "job_title"),
                    "job_category": getattr(job, "job_category"),
                    "industry_tag": getattr(job, "leading_industry_tag"),
                    "city": getattr(job, "city"),
                    "predicted_demand_count": round(float(getattr(job, "predicted_demand_count", 0)), 2),
                    "demand_level": getattr(job, "demand_level", "中需求"),
                    "skill_match_score": round(float(skill_match_score), 4),
                    "cosine_similarity": round(float(similarity), 4),
                    "ranking_score": round(float(final_score), 4),
                    "rank_no": rank_no,
                    "recommendation_reason": (
                        f"该专业对应的{getattr(job, 'job_category')}岗位未来12个月预测需求较高，"
                        f"岗位核心技能包含{ '、'.join(required_skills[:4]) if required_skills else '专业基础能力' }，"
                        "同时学生技能等级与岗位技能要求匹配度较高，因此推荐优先关注该行业岗位。"
                    ),
                }
            )
    return pd.DataFrame(rows)


def build_eval_tables(enrollment_df: pd.DataFrame, job_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    enrollment_eval = pd.DataFrame(
        [
            {"metric_name": "AvgFinalScore", "metric_value": round(float(enrollment_df["final_recommend_score"].mean() or 0), 4), "metric_label": "招生匹配平均综合分", "metric_desc": "融合协同过滤、预测需求、供需缺口和技能适配后的平均分。", "k_value": TOP_K, "evaluated_profiles": len(enrollment_df), "eval_mode": "需求牵引综合评分"},
            {"metric_name": "HighDemandRatio", "metric_value": round(float((enrollment_df["demand_weight"] >= 0.7).mean() or 0), 4), "metric_label": "高需求专业占比", "metric_desc": "招生匹配结果中预测需求权重较高的专业占比。", "k_value": TOP_K, "evaluated_profiles": len(enrollment_df), "eval_mode": "需求牵引综合评分"},
        ]
    )
    job_eval = pd.DataFrame(
        [
            {"metric_name": "AvgTopKSimilarity", "metric_value": round(float(job_df["cosine_similarity"].mean() or 0), 4), "metric_label": f"Top{TOP_K}平均相似度", "metric_desc": "学生画像与岗位画像的平均余弦相似度。", "sample_size": len(job_df), "eval_mode": "余弦相似度统计"},
            {"metric_name": "HighDemandRecommendationRatio", "metric_value": round(float((job_df["demand_level"] == "高需求").mean() or 0), 4), "metric_label": "高需求岗位推荐占比", "metric_desc": "推荐结果中高需求岗位的占比。", "sample_size": len(job_df), "eval_mode": "需求牵引推荐统计"},
        ]
    )
    return enrollment_eval, job_eval


def run_matching_pipeline() -> bool:
    print("[CF] 需求牵引招生匹配与就业推荐启动。")
    engine = get_engine()
    try:
        student_df = read_table(engine, "dim_student")
        academic_df = read_table(engine, "fact_academic")
        employment_df = read_table(engine, "fact_employment")
        job_df = read_table(engine, "fact_job_demand")
        forecast_df = read_table(engine, "ads_job_demand_forecast")
        gap_df = read_table(engine, "ads_major_supply_demand_gap")
        heatmap_df = read_table(engine, "ads_job_skill_heatmap")

        enrollment_df = build_enrollment_matching(student_df, academic_df, employment_df, forecast_df, gap_df, heatmap_df)
        recommendation_df = build_job_recommendation(student_df, academic_df, job_df, forecast_df, heatmap_df)
        enrollment_eval, job_eval = build_eval_tables(enrollment_df, recommendation_df)

        write_table(engine, enrollment_df, "ads_enrollment_matching")
        write_table(engine, enrollment_eval, "ads_enrollment_matching_eval")
        write_table(engine, recommendation_df, "ads_job_recommendation")
        write_table(engine, job_eval, "ads_job_recommendation_eval")
        print("[CF] 需求牵引招生匹配与余弦相似度就业推荐完成。")
        return True
    except Exception as exc:
        print(f"[CF] 运行失败：{exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if run_matching_pipeline() else 1)
