# -*- coding: utf-8 -*-
"""One-click data generation pipeline for the current CAC_DB backend schema."""

from __future__ import annotations

import argparse
import io
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from config import DB_SETTINGS, DB_URL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Stage:
    name: str
    args: tuple[str, ...]
    output_tables: tuple[str, ...] = ()


KEY_TABLES = (
    "dim_school",
    "dim_major_catalog",
    "bridge_school_major",
    "dim_industry",
    "dim_job_category",
    "dim_enterprise",
    "fact_graduate",
    "fact_job_posting",
    "fact_employment",
    "fact_enrollment_plan",
    "fact_course_skill",
    "fact_policy_signal",
    "ads_job_demand_forecast",
    "ads_enrollment_matching",
    "ads_major_optimization",
    "ads_training_rules",
    "ads_job_recommendation",
    "sys_user_account",
    "sys_audit_log",
)


def script_args(script_name: str, *args: str) -> tuple[str, ...]:
    return (str(ROOT / "scripts" / script_name), *args)


def build_stages(args: argparse.Namespace) -> tuple[Stage, ...]:
    return (
        Stage(
            "Generate platform source data",
            script_args("platform_data_factory.py", "--rows", str(args.rows), "--seed", str(args.seed)),
        ),
        Stage(
            "Create current schema",
            script_args("create_tables.py", "--reset"),
            ("dim_school", "fact_graduate", "fact_job_posting", "ads_job_recommendation"),
        ),
        Stage(
            "Load generated source data",
            script_args("PutData.py", "--reset", "--input", args.input),
            ("dim_school", "fact_graduate", "fact_job_posting", "fact_employment"),
        ),
        Stage(
            "Build Spark-style demand features",
            script_args("Spark-all.py"),
            ("ads_job_demand_features", "ads_school_compare_summary"),
        ),
        Stage(
            "Forecast job demand",
            script_args("LSTM-all.py"),
            ("ads_job_demand_forecast",),
        ),
        Stage(
            "Build enrollment matching and major optimization",
            script_args("CF-all.py"),
            ("ads_enrollment_matching", "ads_major_optimization"),
        ),
        Stage(
            "Build graduate job recommendations",
            script_args(
                "build_job_recommendations.py",
                "--school-id",
                args.recommendation_school_id,
                "--limit",
                str(args.recommendation_limit),
                "--top-k",
                str(args.recommendation_top_k),
            ),
            ("ads_job_recommendation",),
        ),
        Stage(
            "Mine training rules",
            script_args("FPgrowth-all.py"),
            ("ads_training_rules",),
        ),
        Stage(
            "Initialize security accounts",
            script_args("init_security.py"),
            ("sys_user_account", "sys_audit_log"),
        ),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the full CAC_DB current-schema demo database.")
    parser.add_argument("--rows", type=int, default=int(os.getenv("PIPELINE_ROWS", "100000")))
    parser.add_argument("--seed", type=int, default=int(os.getenv("PIPELINE_SEED", "20260427")))
    parser.add_argument("--input", default=os.getenv("PIPELINE_INPUT", "data/generated"))
    parser.add_argument("--recommendation-school-id", default=os.getenv("JOB_RECOMMENDATION_SCHOOL_ID", "ALL"))
    parser.add_argument("--recommendation-limit", type=int, default=int(os.getenv("JOB_RECOMMENDATION_LIMIT", "5000")))
    parser.add_argument("--recommendation-top-k", type=int, default=int(os.getenv("JOB_RECOMMENDATION_TOP_K", "3")))
    return parser.parse_args()


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


def count_table(conn, table_name: str) -> int | None:
    if not table_exists(conn, table_name):
        return None
    return int(conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar() or 0)


def run_stage(stage: Stage) -> None:
    command = (sys.executable, *stage.args)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    started = time.perf_counter()

    logger.info("")
    logger.info("=" * 88)
    logger.info("Stage: %s", stage.name)
    logger.info("Command: %s", " ".join(command))

    result = subprocess.run(command, cwd=str(ROOT), env=env, check=False)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(f"{stage.name} failed with exit code {result.returncode}")

    logger.info("Stage completed in %.2fs", elapsed)

    if stage.output_tables:
        engine = create_engine(DB_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            for table_name in stage.output_tables:
                logger.info("  - %-32s %s", table_name, count_table(conn, table_name))


def validate_final_database() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    missing: list[str] = []
    empty_required: list[str] = []

    logger.info("")
    logger.info("=" * 88)
    logger.info("Final key table counts")
    with engine.connect() as conn:
        for table_name in KEY_TABLES:
            row_count = count_table(conn, table_name)
            logger.info("  - %-32s %s", table_name, "missing" if row_count is None else row_count)
            if row_count is None:
                missing.append(table_name)
            elif table_name != "sys_audit_log" and row_count <= 0:
                empty_required.append(table_name)

    if missing:
        raise RuntimeError(f"Missing required tables: {', '.join(missing)}")
    if empty_required:
        raise RuntimeError(f"Required tables are empty: {', '.join(empty_required)}")


def main() -> int:
    args = parse_args()
    logger.info("CAC_DB current-schema pipeline started")
    logger.info("Working directory: %s", ROOT)
    logger.info("Database: %s:%s/%s", DB_SETTINGS["host"], DB_SETTINGS["port"], DB_SETTINGS["database"])
    logger.info("Log file: %s", LOG_FILE)

    try:
        for stage in build_stages(args):
            run_stage(stage)
        validate_final_database()
        logger.info("")
        logger.info("Pipeline completed successfully. A fresh database can be rebuilt with: python run_full_pipeline.py")
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline failed: %s", exc)
        logger.error("See log file: %s", LOG_FILE)
        return 1


if __name__ == "__main__":
    sys.exit(main())
