# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL  # noqa: E402
from scripts.major_display_policy import major_display_metadata  # noqa: E402


COLUMNS = {
    "is_real_display_major": "TINYINT DEFAULT 0",
    "is_catalog_placeholder": "TINYINT DEFAULT 0",
    "display_priority": "INT DEFAULT 0",
    "salary_rank_weight": "DECIMAL(8,4) DEFAULT 0",
    "industry_trend_tags": "TEXT NULL",
}


def configure_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def existing_columns(conn) -> set[str]:
    result = conn.execute(text("SHOW COLUMNS FROM dim_major_catalog"))
    return {row._mapping["Field"] for row in result}


def main() -> None:
    configure_utf8()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        cols = existing_columns(conn)
        for name, ddl in COLUMNS.items():
            if name not in cols:
                conn.execute(text(f"ALTER TABLE dim_major_catalog ADD COLUMN {name} {ddl}"))
                print(f"新增字段 dim_major_catalog.{name}")
            else:
                print(f"字段已存在 dim_major_catalog.{name}")

        rows = conn.execute(text("SELECT major_code, major_name FROM dim_major_catalog")).mappings().all()
        real_count = 0
        placeholder_count = 0
        for row in rows:
            meta = major_display_metadata(row["major_name"])
            real_count += int(meta["is_real_display_major"])
            placeholder_count += int(meta["is_catalog_placeholder"])
            conn.execute(
                text(
                    """
                    UPDATE dim_major_catalog
                    SET is_real_display_major=:is_real_display_major,
                        is_catalog_placeholder=:is_catalog_placeholder,
                        display_priority=:display_priority,
                        salary_rank_weight=:salary_rank_weight,
                        industry_trend_tags=:industry_trend_tags
                    WHERE major_code=:major_code
                    """
                ),
                {**meta, "major_code": row["major_code"]},
            )

        print(f"专业目录总数: {len(rows)}")
        print(f"真实展示专业数: {real_count}")
        print(f"目录占位专业数: {placeholder_count}")


if __name__ == "__main__":
    main()
