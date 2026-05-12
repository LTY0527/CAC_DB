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


DDL = """
CREATE TABLE IF NOT EXISTS ads_school_compare_summary (
    summary_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    school_id VARCHAR(20),
    school_name VARCHAR(100),
    major_code VARCHAR(20),
    major_name VARCHAR(120),
    discipline_category VARCHAR(50),
    employment_count INT,
    graduate_count INT,
    employment_rate DECIMAL(10,4),
    avg_salary DECIMAL(12,2),
    high_quality_employment_count INT,
    high_quality_employment_rate DECIMAL(10,4),
    leading_industry_employment_count INT,
    leading_industry_employment_rate DECIMAL(10,4),
    top_industry_name VARCHAR(100),
    top_industry_count INT,
    top_industry_rate DECIMAL(10,4),
    industry_distribution_json JSON NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_school_compare_scope (school_id, major_code),
    INDEX idx_school_compare_major (major_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def fetch_counts(conn) -> dict[str, int]:
    return {
        row["school_id"]: int(row["cnt"])
        for row in conn.execute(text("""
            SELECT school_id, COUNT(*) cnt
            FROM fact_employment
            GROUP BY school_id
        """)).mappings()
    }


def rebalance_current_employment(conn) -> dict:
    counts = fetch_counts(conn)
    if not counts:
        return {"moved": 0, "reason": "fact_employment empty"}
    total = sum(counts.values())
    avg = total / len(counts)
    if max(counts.values()) / max(min(counts.values()), 1) <= 3 and counts.get("SHU007", 0) <= avg * 2:
        return {"moved": 0, "reason": "already balanced", "before": counts, "after": counts}

    shu_target = min(8000, max(5600, int(total * 0.14)))
    other_target = int((total - shu_target) / max(len(counts) - 1, 1))
    targets = {sid: (shu_target if sid == "SHU007" else other_target) for sid in counts}
    remainder = total - sum(targets.values())
    for sid in sorted(targets):
        if remainder <= 0:
            break
        targets[sid] += 1
        remainder -= 1

    source = "SHU007" if counts.get("SHU007", 0) > targets.get("SHU007", 0) else max(counts, key=counts.get)
    moved = 0
    source_offset = 0
    for dest in sorted(counts, key=lambda sid: counts[sid]):
        if dest == source:
            continue
        need = max(0, targets.get(dest, other_target) - counts.get(dest, 0))
        if need <= 0:
            continue
        majors = [row["major_code"] for row in conn.execute(text("""
            SELECT major_code
            FROM bridge_school_major
            WHERE school_id=:school_id
            ORDER BY is_ace_major DESC, historical_enrollment_scale DESC
        """), {"school_id": dest}).mappings()]
        if not majors:
            continue
        rows = list(conn.execute(text("""
            SELECT employment_id, graduate_id
            FROM fact_employment
            WHERE school_id=:source
            ORDER BY employment_id
            LIMIT :need OFFSET :offset
        """), {"source": source, "need": need, "offset": source_offset}).mappings())
        source_offset += len(rows)
        for idx, row in enumerate(rows):
            major_code = majors[idx % len(majors)]
            conn.execute(text("""
                UPDATE fact_employment
                SET school_id=:dest, major_code=:major_code
                WHERE employment_id=:employment_id
            """), {"dest": dest, "major_code": major_code, "employment_id": row["employment_id"]})
            conn.execute(text("""
                UPDATE fact_graduate
                SET school_id=:dest, major_code=:major_code
                WHERE graduate_id=:graduate_id
            """), {"dest": dest, "major_code": major_code, "graduate_id": row["graduate_id"]})
            moved += 1

    return {"moved": moved, "before": counts, "after": fetch_counts(conn), "targets": targets}


def build_summary(engine) -> pd.DataFrame:
    employment = pd.read_sql("SELECT * FROM fact_employment", engine)
    graduates = pd.read_sql("SELECT school_id, major_code, COUNT(*) graduate_count FROM fact_graduate GROUP BY school_id, major_code", engine)
    schools = pd.read_sql("SELECT school_id, school_name FROM dim_school", engine)
    majors = pd.read_sql("SELECT major_code, major_name, discipline_category FROM dim_major_catalog", engine)
    industries = pd.read_sql("SELECT industry_id, industry_name FROM dim_industry", engine)
    enterprises = pd.read_sql("SELECT enterprise_id, is_high_tech FROM dim_enterprise", engine)

    emp = (
        employment.merge(schools, on="school_id", how="left")
        .merge(majors, on="major_code", how="left")
        .merge(industries, on="industry_id", how="left")
        .merge(enterprises, on="enterprise_id", how="left")
    )
    threshold = emp.groupby(["school_id", "major_code"])["salary"].transform(lambda s: s.quantile(0.70))
    median_salary = emp.groupby(["school_id", "major_code"])["salary"].transform("median")
    emp["is_leading"] = emp.get("is_shanghai_leading_employment", 0).fillna(0).astype(int)
    high_tech = emp.get("is_high_tech", 0).fillna(0).astype(int)
    emp["is_high_quality"] = (
        (emp["salary"] >= threshold.fillna(emp["salary"].median()))
        | ((emp["is_leading"] == 1) & (emp["salary"] >= median_salary.fillna(emp["salary"].median())))
        | ((high_tech == 1) & (emp["salary"] >= median_salary.fillna(emp["salary"].median())))
    ).astype(int)

    def aggregate(scope_cols: list[str]) -> pd.DataFrame:
        base = emp.groupby(scope_cols, as_index=False).agg(
            employment_count=("employment_id", "count"),
            avg_salary=("salary", "mean"),
            high_quality_employment_count=("is_high_quality", "sum"),
            leading_industry_employment_count=("is_leading", "sum"),
        )
        industry_counts = emp.groupby(scope_cols + ["industry_name"], as_index=False).agg(top_industry_count=("employment_id", "count"))
        top = (
            industry_counts.sort_values(scope_cols + ["top_industry_count"], ascending=[True] * len(scope_cols) + [False])
            .groupby(scope_cols, as_index=False)
            .first()
            .rename(columns={"industry_name": "top_industry_name"})
        )
        distributions = []
        for key, part in industry_counts.groupby(scope_cols):
            if not isinstance(key, tuple):
                key = (key,)
            total = max(float(part["top_industry_count"].sum()), 1.0)
            item = dict(zip(scope_cols, key))
            item["industry_distribution_json"] = part.sort_values("top_industry_count", ascending=False).assign(
                rate=lambda df: (df["top_industry_count"] / total).round(4)
            )[["industry_name", "top_industry_count", "rate"]].rename(columns={"top_industry_count": "count"}).to_json(orient="records", force_ascii=False)
            distributions.append(item)
        result = base.merge(top, on=scope_cols, how="left").merge(pd.DataFrame(distributions), on=scope_cols, how="left")
        result["top_industry_rate"] = result["top_industry_count"].fillna(0) / result["employment_count"].clip(lower=1)
        result["high_quality_employment_rate"] = result["high_quality_employment_count"] / result["employment_count"].clip(lower=1)
        result["leading_industry_employment_rate"] = result["leading_industry_employment_count"] / result["employment_count"].clip(lower=1)
        return result

    by_major = aggregate(["school_id", "school_name", "major_code", "major_name", "discipline_category"])
    by_major = by_major.merge(graduates, on=["school_id", "major_code"], how="left")
    by_major["graduate_count"] = by_major["graduate_count"].fillna(by_major["employment_count"]).astype(int)
    by_major["employment_rate"] = (by_major["employment_count"] / by_major["graduate_count"].clip(lower=1)).clip(0, 1)

    by_school = aggregate(["school_id", "school_name"])
    grad_school = graduates.groupby("school_id", as_index=False).agg(graduate_count=("graduate_count", "sum"))
    by_school = by_school.merge(grad_school, on="school_id", how="left")
    by_school["graduate_count"] = by_school["graduate_count"].fillna(by_school["employment_count"]).astype(int)
    by_school["employment_rate"] = (by_school["employment_count"] / by_school["graduate_count"].clip(lower=1)).clip(0, 1)
    by_school["major_code"] = "ALL"
    by_school["major_name"] = "全部专业"
    by_school["discipline_category"] = "全部"

    out = pd.concat([by_school, by_major], ignore_index=True, sort=False)
    out["avg_salary"] = out["avg_salary"].round(2)
    for col in ["employment_rate", "high_quality_employment_rate", "leading_industry_employment_rate", "top_industry_rate"]:
        out[col] = out[col].fillna(0).round(4)
    out["top_industry_name"] = out["top_industry_name"].fillna("")
    out["top_industry_count"] = out["top_industry_count"].fillna(0).astype(int)
    out["industry_distribution_json"] = out["industry_distribution_json"].fillna("[]")
    return out[[
        "school_id", "school_name", "major_code", "major_name", "discipline_category",
        "employment_count", "graduate_count", "employment_rate", "avg_salary",
        "high_quality_employment_count", "high_quality_employment_rate",
        "leading_industry_employment_count", "leading_industry_employment_rate",
        "top_industry_name", "top_industry_count", "top_industry_rate", "industry_distribution_json",
    ]]


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        conn.execute(text(DDL))
        rebalance = rebalance_current_employment(conn)
    summary = build_summary(engine)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE ads_school_compare_summary"))
        summary.to_sql("ads_school_compare_summary", conn, if_exists="append", index=False, chunksize=2000, method="multi")
    print(json.dumps({"rebalance": rebalance, "ads_school_compare_summary": len(summary)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
