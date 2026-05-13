# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import (  # noqa: E402
    engine,
    fetch_student_profile,
    get_or_build_student_job_recommendations,
    id_match_conditions,
    rows,
    scoped_where,
    table_columns,
)
from sqlalchemy import text  # noqa: E402


def build_scope(school_id: str | None) -> dict:
    school_name = ""
    if school_id:
        data = rows(
            """
            SELECT school_id, school_name
            FROM dim_school
            WHERE TRIM(CAST(school_id AS CHAR))=:school_id
            LIMIT 1
            """,
            {"school_id": school_id},
        )
        if data:
            school_id = str(data[0]["school_id"])
            school_name = data[0].get("school_name") or ""
    return {
        "role": "government",
        "school_id": school_id,
        "school_name": school_name,
        "school_id_aliases": [school_id] if school_id else [],
    }


def student_ids(scope: dict, limit: int | None) -> list[str]:
    where_sql, params = scoped_where("fact_graduate", scope)
    sql = f"""
        SELECT graduate_id
        FROM fact_graduate
        {where_sql}
        GROUP BY graduate_id
        ORDER BY CAST(graduate_id AS UNSIGNED), graduate_id
    """
    if limit:
        sql += " LIMIT :limit"
        params = {**params, "limit": limit}
    return [str(item["graduate_id"]) for item in rows(sql, params)]


def existing_recommendation_ids(scope: dict) -> set[str]:
    where_sql, params = scoped_where("ads_job_recommendation", scope)
    return {
        str(item["graduate_id"])
        for item in rows(
            f"""
            SELECT graduate_id
            FROM ads_job_recommendation
            {where_sql}
            GROUP BY graduate_id
            """,
            params,
        )
    }


def delete_student_recommendations(student_id: str, scope: dict) -> None:
    columns = table_columns("ads_job_recommendation")
    id_columns = [column for column in ["graduate_id", "student_id", "student_no", "id"] if column in columns]
    if not id_columns:
        return
    id_conditions, params = id_match_conditions("", id_columns, student_id, "sid")
    where_sql, scope_params = scoped_where("ads_job_recommendation", scope, "", [f"({' OR '.join(id_conditions)})"])
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM ads_job_recommendation {where_sql}"), {**params, **scope_params})


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill differentiated Top-K job recommendations.")
    parser.add_argument("--apply", action="store_true", help="Write generated recommendations into ads_job_recommendation.")
    parser.add_argument("--school-id", default=None, help="Limit to one school_id, for example SHU007.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of students scanned.")
    parser.add_argument("--refresh", action="store_true", help="Regenerate even when recommendations already exist.")
    args = parser.parse_args()

    scope = build_scope(args.school_id)
    all_students = student_ids(scope, args.limit)
    existing = existing_recommendation_ids(scope)
    targets = all_students if args.refresh else [sid for sid in all_students if sid not in existing]
    print(f"school_id={scope.get('school_id') or 'ALL'}")
    print(f"total_students={len(all_students)}")
    print(f"existing_recommendation_students={len(existing)}")
    print(f"students_missing_recommendation={len(targets)}")

    generated = 0
    if not args.apply:
        print("dry_run=true; add --apply to generate and write Top3 recommendations.")
        print("sample_targets=" + ",".join(targets[:20]))
        return

    for student_id in targets:
        if args.refresh:
            delete_student_recommendations(student_id, scope)
        profile = fetch_student_profile(student_id, scope)
        if not profile:
            continue
        items = get_or_build_student_job_recommendations(profile, scope, top_k=3)
        if items:
            generated += 1
    print(f"new_generated_recommendation_students={generated}")


if __name__ == "__main__":
    main()
