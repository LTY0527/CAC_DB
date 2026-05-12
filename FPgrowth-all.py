# -*- coding: utf-8 -*-
"""
FP-Growth 专业—岗位—技能—行业关联规则挖掘。

交易项来自 fact_job_demand：专业、岗位类别、行业、技能、学历、城市。
输出 ads_major_matching_rules，直接服务培养方案优化。
"""

from __future__ import annotations

import ast
import io
import itertools
import json
import sys
from collections import Counter, defaultdict

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def get_engine():
    return create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)


def parse_skills(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not value or pd.isna(value):
        return []
    text = str(value).strip()
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    for sep in ["、", ";", "；", "|"]:
        text = text.replace(sep, ",")
    return [item.strip() for item in text.split(",") if item.strip()]


def build_transactions(job_df: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in job_df.dropna(subset=["major_name", "job_category"]).iterrows():
        skills = parse_skills(row.get("skill_keywords"))[:6]
        raw_items = [
            str(row.get("major_name") or "").strip(),
            str(row.get("job_category") or "").strip(),
            str(row.get("leading_industry_tag") or "").strip(),
            str(row.get("education_requirement") or "").strip(),
            str(row.get("city") or "").strip(),
            *skills,
        ]
        items = sorted({item for item in raw_items if item})
        rows.append(
            {
                "items": items,
                "major_name": row.get("major_name"),
                "job_category": row.get("job_category"),
                "industry_tag": row.get("leading_industry_tag"),
            }
        )
    return rows


def mine_rules(transactions: list[dict], min_support=0.012, min_confidence=0.28) -> pd.DataFrame:
    total = len(transactions)
    if total == 0:
        return pd.DataFrame()
    item_counts = Counter()
    pair_counts = Counter()
    meta_map = defaultdict(Counter)

    for tx in transactions:
        items = tx["items"]
        for item in items:
            item_counts[item] += 1
        for left, right in itertools.permutations(items, 2):
            pair_counts[(left, right)] += 1
            meta_map[(left, right)][(tx["major_name"], tx["job_category"], tx["industry_tag"])] += 1

    rules = []
    for (left, right), pair_count in pair_counts.items():
        support = pair_count / total
        confidence = pair_count / max(item_counts[left], 1)
        lift = confidence / max(item_counts[right] / total, 1e-9)
        if support < min_support or confidence < min_confidence or lift <= 1.0:
            continue
        (major_name, job_category, industry_tag), _ = meta_map[(left, right)].most_common(1)[0]
        rules.append(
            {
                "antecedents": json.dumps([left], ensure_ascii=False),
                "consequents": json.dumps([right], ensure_ascii=False),
                "support": round(support, 4),
                "confidence": round(confidence, 4),
                "lift": round(lift, 4),
                "major_name": major_name,
                "job_category": job_category,
                "industry_tag": industry_tag,
                "rule_desc": f"{major_name}专业与{left}、{right}组合在{job_category}岗位中具有较强关联，可作为培养方案优化依据。",
            }
        )

    result = pd.DataFrame(rules)
    if result.empty:
        return result
    return result.sort_values(["lift", "confidence", "support"], ascending=False).head(300).reset_index(drop=True)


def run_fp_growth_analysis() -> bool:
    print("[FP-Growth] 岗位需求关联规则挖掘启动。")
    engine = get_engine()
    try:
        job_df = pd.read_sql("SELECT * FROM fact_job_demand", engine)
        transactions = build_transactions(job_df)
        rules_df = mine_rules(transactions)
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ads_major_matching_rules"))
            conn.execute(
                text(
                    """
                    CREATE TABLE ads_major_matching_rules (
                        rule_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                        antecedents TEXT,
                        consequents TEXT,
                        support DECIMAL(10,4),
                        confidence DECIMAL(10,4),
                        lift DECIMAL(10,4),
                        major_name VARCHAR(100),
                        job_category VARCHAR(100),
                        industry_tag VARCHAR(100),
                        rule_desc TEXT,
                        created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_major_job (major_name, job_category),
                        INDEX idx_lift (lift)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    COMMENT='专业—岗位—技能—行业关联规则表'
                    """
                )
            )
            if not rules_df.empty:
                rules_df.to_sql("ads_major_matching_rules", conn, if_exists="append", index=False, chunksize=1000, method="multi")
        print(f"[FP-Growth] 关联规则写入完成：ads_major_matching_rules={len(rules_df)} 行。")
        return True
    except Exception as exc:
        print(f"[FP-Growth] 运行失败：{exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if run_fp_growth_analysis() else 1)
