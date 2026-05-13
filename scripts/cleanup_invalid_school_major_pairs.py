# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL  # noqa: E402


TARGETS = {
    "ads_school_compare_summary": "summary_id",
    "fact_employment": "employment_id",
}


def existing_columns(conn, table_name: str) -> set[str]:
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


def fetch_invalid(conn, table_name: str, pk_column: str) -> tuple[int, list[dict]]:
    major_filter = "AND t.major_code <> 'ALL'" if table_name == "ads_school_compare_summary" else ""
    count_sql = text(
        f"""
        SELECT COUNT(*) AS invalid_cnt
        FROM {table_name} t
        LEFT JOIN bridge_school_major b
          ON CAST(t.school_id AS CHAR)=CAST(b.school_id AS CHAR)
         AND CAST(t.major_code AS CHAR)=CAST(b.major_code AS CHAR)
        WHERE t.major_code IS NOT NULL
          {major_filter}
          AND b.school_id IS NULL
        """
    )
    sample_sql = text(
        f"""
        SELECT t.{pk_column} AS row_id, t.school_id, t.major_code,
               s.school_name, m.major_name
        FROM {table_name} t
        LEFT JOIN bridge_school_major b
          ON CAST(t.school_id AS CHAR)=CAST(b.school_id AS CHAR)
         AND CAST(t.major_code AS CHAR)=CAST(b.major_code AS CHAR)
        LEFT JOIN dim_school s
          ON CAST(t.school_id AS CHAR)=CAST(s.school_id AS CHAR)
        LEFT JOIN dim_major_catalog m
          ON CAST(t.major_code AS CHAR)=CAST(m.major_code AS CHAR)
        WHERE t.major_code IS NOT NULL
          {major_filter}
          AND b.school_id IS NULL
        ORDER BY t.school_id, t.major_code
        LIMIT 20
        """
    )
    invalid_cnt = int(conn.execute(count_sql).scalar() or 0)
    samples = [dict(row) for row in conn.execute(sample_sql).mappings()]
    return invalid_cnt, samples


def cleanup(conn, table_name: str) -> int:
    if table_name != "ads_school_compare_summary":
        return 0
    major_filter = "AND t.major_code <> 'ALL'" if table_name == "ads_school_compare_summary" else ""
    result = conn.execute(
        text(
            f"""
            DELETE t
            FROM {table_name} t
            LEFT JOIN bridge_school_major b
              ON CAST(t.school_id AS CHAR)=CAST(b.school_id AS CHAR)
             AND CAST(t.major_code AS CHAR)=CAST(b.major_code AS CHAR)
            WHERE t.major_code IS NOT NULL
              {major_filter}
              AND b.school_id IS NULL
            """
        )
    )
    return int(result.rowcount or 0)


def cleanup_denylist(conn, table_name: str) -> int:
    if table_name == "bridge_school_major":
        result = conn.execute(
            text(
                """
                DELETE b
                FROM bridge_school_major b
                JOIN dim_school s
                  ON CAST(b.school_id AS CHAR)=CAST(s.school_id AS CHAR)
                LEFT JOIN dim_major_catalog m
                  ON CAST(b.major_code AS CHAR)=CAST(m.major_code AS CHAR)
                WHERE s.school_name='上海大学'
                  AND m.major_name='轻化工程'
                """
            )
        )
        return int(result.rowcount or 0)
    if table_name != "ads_school_compare_summary":
        return 0
    result = conn.execute(
        text(
            """
            DELETE t
            FROM ads_school_compare_summary t
            LEFT JOIN dim_school s
              ON CAST(t.school_id AS CHAR)=CAST(s.school_id AS CHAR)
            LEFT JOIN dim_major_catalog m
              ON CAST(t.major_code AS CHAR)=CAST(m.major_code AS CHAR)
            WHERE (t.school_name='上海大学' OR s.school_name='上海大学')
              AND (t.major_name='轻化工程' OR m.major_name='轻化工程')
              AND t.major_code <> 'ALL'
            """
        )
    )
    return int(result.rowcount or 0)


def denylist_count(conn, table_name: str) -> int:
    columns = existing_columns(conn, table_name)
    school_exprs = ["s.school_name='上海大学'"]
    major_exprs = ["m.major_name='轻化工程'"]
    if "school_name" in columns:
        school_exprs.append("t.school_name='上海大学'")
    if "major_name" in columns:
        major_exprs.append("t.major_name='轻化工程'")
    return int(
        conn.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM {table_name} t
                LEFT JOIN dim_school s
                  ON CAST(t.school_id AS CHAR)=CAST(s.school_id AS CHAR)
                LEFT JOIN dim_major_catalog m
                  ON CAST(t.major_code AS CHAR)=CAST(m.major_code AS CHAR)
                WHERE ({' OR '.join(school_exprs)})
                  AND ({' OR '.join(major_exprs)})
                """
            )
        ).scalar()
        or 0
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or clean invalid school-major pairs.")
    parser.add_argument("--apply", action="store_true", help="Delete invalid rows. Without this flag, only prints a dry-run report.")
    args = parser.parse_args()

    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        bridge_denied_cnt = denylist_count(conn, "bridge_school_major")
        print(f"bridge_school_major: shanghai_university_light_chemical_engineering_cnt={bridge_denied_cnt}")
        if args.apply and bridge_denied_cnt:
            print(f"  denylist_deleted={cleanup_denylist(conn, 'bridge_school_major')}")
        elif bridge_denied_cnt:
            print("  dry-run only; rerun with --apply to delete this denylisted bridge relation.")
        for table_name, pk_column in TARGETS.items():
            invalid_cnt, samples = fetch_invalid(conn, table_name, pk_column)
            denied_cnt = denylist_count(conn, table_name)
            print(f"{table_name}: invalid_cnt={invalid_cnt}")
            print(f"{table_name}: shanghai_university_light_chemical_engineering_cnt={denied_cnt}")
            for sample in samples:
                print(f"  sample: {sample}")
            if args.apply and invalid_cnt:
                deleted = cleanup(conn, table_name)
                if table_name == "ads_school_compare_summary":
                    print(f"  deleted={deleted}")
                else:
                    print("  skipped apply: fact tables are reported only and are not deleted by this script.")
            if args.apply and denied_cnt:
                denied_deleted = cleanup_denylist(conn, table_name)
                if table_name == "ads_school_compare_summary":
                    print(f"  denylist_deleted={denied_deleted}")
                else:
                    print("  skipped denylist apply: fact tables are reported only and are not deleted by this script.")
            elif invalid_cnt or denied_cnt:
                if table_name == "ads_school_compare_summary":
                    print("  dry-run only; rerun with --apply to delete invalid or denylisted display rows.")
                else:
                    print("  dry-run only; fact tables are reported for review and are not deleted by this script.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
