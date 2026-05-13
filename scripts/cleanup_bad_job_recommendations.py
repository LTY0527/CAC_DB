# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (  # noqa: E402
    engine,
    recommendation_row_is_valid_for_profile,
    rows,
    table_columns,
)


CHECK_MAJORS = {"风景园林", "土木工程", "教育学", "纺织科学与工程"}


def load_bad_rows(limit: int | None = None) -> list[dict]:
    sql = """
        SELECT r.recommendation_id, r.graduate_id, r.school_id, r.school_name,
               r.major_code, r.major_name, r.enterprise_id, r.enterprise_name,
               r.industry_id, r.industry_name, r.job_category_id, r.job_category_name,
               r.rank_no, r.reason_text
        FROM ads_job_recommendation r
        WHERE r.major_name IN :majors
        ORDER BY r.major_name, r.graduate_id, r.rank_no
    """
    if limit:
        sql += " LIMIT :limit"
    params = {"majors": tuple(CHECK_MAJORS)}
    if limit:
        params["limit"] = limit
    with engine.connect() as conn:
        result = conn.execute(text(sql).bindparams(bindparam("majors", expanding=True)), params)
        candidates = [{k: v for k, v in row.items()} for row in result.mappings()]
    bad = []
    for item in candidates:
        if not recommendation_row_is_valid_for_profile({"major_name": item.get("major_name")}, item):
            bad.append(item)
    return bad


def delete_bad_rows(bad_rows: list[dict]) -> int:
    if not bad_rows:
        return 0
    columns = table_columns("ads_job_recommendation")
    deleted = 0
    with engine.begin() as conn:
        for item in bad_rows:
            if "recommendation_id" in columns and item.get("recommendation_id") is not None:
                result = conn.execute(
                    text("DELETE FROM ads_job_recommendation WHERE recommendation_id=:recommendation_id"),
                    {"recommendation_id": item["recommendation_id"]},
                )
            else:
                result = conn.execute(
                    text(
                        """
                        DELETE FROM ads_job_recommendation
                        WHERE graduate_id=:graduate_id
                          AND COALESCE(rank_no,0)=COALESCE(:rank_no,0)
                          AND COALESCE(enterprise_id,0)=COALESCE(:enterprise_id,0)
                        """
                    ),
                    {
                        "graduate_id": item.get("graduate_id"),
                        "rank_no": item.get("rank_no"),
                        "enterprise_id": item.get("enterprise_id"),
                    },
                )
            deleted += result.rowcount or 0
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser(description="Find and optionally remove obvious major-industry job recommendation mismatches.")
    parser.add_argument("--apply", action="store_true", help="Delete invalid recommendation rows.")
    parser.add_argument("--limit", type=int, default=None, help="Limit scanned rows for quick checks.")
    args = parser.parse_args()

    bad = load_bad_rows(args.limit)
    print(f"bad_job_recommendation_count={len(bad)}")
    for item in bad[:20]:
        print(
            "sample "
            f"recommendation_id={item.get('recommendation_id')} "
            f"graduate_id={item.get('graduate_id')} "
            f"major={item.get('major_name')} "
            f"industry={item.get('industry_name')} "
            f"job={item.get('job_category_name')} "
            f"enterprise={item.get('enterprise_name')}"
        )
    if not args.apply:
        print("dry_run=true; rerun with --apply to delete these recommendation rows.")
        print("After cleanup, run scripts/backfill_job_recommendations.py --apply --refresh as needed.")
        return
    deleted = delete_bad_rows(bad)
    print(f"deleted_rows={deleted}")


if __name__ == "__main__":
    main()
