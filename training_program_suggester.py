# -*- coding: utf-8 -*-
"""
培养方案优化建议生成脚本。

读取：
- ads_job_demand_forecast
- ads_job_skill_heatmap
- ads_major_matching_rules
- ads_major_supply_demand_gap

输出：
- ads_training_program_suggestions
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

COURSE_MAP = {
    "Python": "Python数据分析",
    "MySQL": "数据库原理与SQL优化",
    "Spark": "大数据计算框架",
    "机器学习": "机器学习基础",
    "Java": "Java企业级开发",
    "Spring Boot": "微服务开发实践",
    "网络安全": "网络攻防与安全运营",
    "Docker": "云原生部署实践",
    "Kubernetes": "容器编排与DevOps",
    "SQL": "数据仓库与商业智能",
    "PyTorch": "深度学习框架实践",
}


def get_engine():
    return create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)


def read_table(engine, table_name: str) -> pd.DataFrame:
    try:
        return pd.read_sql(f"SELECT * FROM `{table_name}`", engine)
    except Exception:
        return pd.DataFrame()


def mode(values, default="中需求"):
    values = [value for value in values if pd.notna(value) and str(value)]
    return Counter(values).most_common(1)[0][0] if values else default


def build_suggestions(forecast_df, heatmap_df, rules_df, gap_df) -> pd.DataFrame:
    forecast_major = (
        forecast_df.groupby("major_name", dropna=False)
        .agg(
            forecast_demand_count=("predicted_demand_count", "sum"),
            demand_level=("demand_level", mode),
            top_job_category=("job_category", mode),
            top_industry=("industry_tag", mode),
        )
        .reset_index()
    )
    gap_major = gap_df[["major_name", "gap_level", "gap_count", "gap_rate"]] if not gap_df.empty else pd.DataFrame(columns=["major_name", "gap_level", "gap_count", "gap_rate"])
    skill_major = (
        heatmap_df.sort_values("skill_count", ascending=False)
        .groupby("major_name")["skill_name"]
        .apply(lambda s: list(dict.fromkeys(s.tolist()))[:8])
        .reset_index(name="core_skill_list")
        if not heatmap_df.empty
        else pd.DataFrame(columns=["major_name", "core_skill_list"])
    )
    rule_major = (
        rules_df.groupby("major_name")
        .agg(rule_count=("rule_id", "count"), best_rule_desc=("rule_desc", mode), avg_lift=("lift", "mean"))
        .reset_index()
        if not rules_df.empty
        else pd.DataFrame(columns=["major_name", "rule_count", "best_rule_desc", "avg_lift"])
    )
    result = forecast_major.merge(gap_major, on="major_name", how="left").merge(skill_major, on="major_name", how="left").merge(rule_major, on="major_name", how="left")
    result["gap_level"] = result["gap_level"].fillna("基本平衡")
    result["core_skill_list"] = result["core_skill_list"].apply(lambda v: v if isinstance(v, list) else [])
    result["rule_count"] = result["rule_count"].fillna(0).astype(int)
    result["avg_lift"] = result["avg_lift"].fillna(0).round(4)

    rows = []
    for row in result.itertuples(index=False):
        skills = list(row.core_skill_list)[:6]
        courses = []
        for skill in skills:
            courses.append(COURSE_MAP.get(skill, f"{skill}应用实践"))
        if not courses:
            courses = ["岗位能力综合实训", "行业数据分析实践", "校企协同项目训练"]
        direction = f"面向{row.top_industry}{row.top_job_category}岗位群，强化{'、'.join(skills[:4]) if skills else '专业核心技能'}能力。"
        reason = (
            f"{row.major_name}未来12个月预测岗位需求约{row.forecast_demand_count:.0f}人，需求等级为{row.demand_level}；"
            f"专业供需状态为{row.gap_level}。系统结合技能热力、FP-Growth关联规则和供需缺口，建议优化课程与实训方向。"
        )
        if row.rule_count:
            reason += f" 典型规则依据：{row.best_rule_desc}"
        rows.append(
            {
                "major_name": row.major_name,
                "demand_level": row.demand_level,
                "gap_level": row.gap_level,
                "core_skills": json.dumps(skills, ensure_ascii=False),
                "suggested_courses": json.dumps(courses[:6], ensure_ascii=False),
                "suggested_training_direction": direction,
                "suggestion_reason": reason,
            }
        )
    return pd.DataFrame(rows).sort_values(["demand_level", "major_name"], ascending=[True, True])


def run_training_program_suggester() -> bool:
    print("[培养建议] 正在生成培养方案优化建议。")
    engine = get_engine()
    try:
        forecast_df = read_table(engine, "ads_job_demand_forecast")
        heatmap_df = read_table(engine, "ads_job_skill_heatmap")
        rules_df = read_table(engine, "ads_major_matching_rules")
        gap_df = read_table(engine, "ads_major_supply_demand_gap")
        suggestions_df = build_suggestions(forecast_df, heatmap_df, rules_df, gap_df)
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ads_training_program_suggestions"))
            conn.execute(
                text(
                    """
                    CREATE TABLE ads_training_program_suggestions (
                        suggestion_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        major_name VARCHAR(100),
                        demand_level VARCHAR(50),
                        gap_level VARCHAR(50),
                        core_skills TEXT,
                        suggested_courses TEXT,
                        suggested_training_direction TEXT,
                        suggestion_reason TEXT,
                        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_major (major_name),
                        INDEX idx_level (demand_level, gap_level)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    COMMENT='培养方案优化建议表'
                    """
                )
            )
            if not suggestions_df.empty:
                suggestions_df.to_sql("ads_training_program_suggestions", conn, if_exists="append", index=False, chunksize=1000, method="multi")
        print(f"[培养建议] 已写入 ads_training_program_suggestions: {len(suggestions_df)} 行。")
        return True
    except Exception as exc:
        print(f"[培养建议] 运行失败：{exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if run_training_program_suggester() else 1)
