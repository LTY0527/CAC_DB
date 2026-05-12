# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL

LOAD_ORDER = [
    "dim_school",
    "dim_major_catalog",
    "bridge_school_major",
    "dim_industry",
    "dim_job_category",
    "dim_enterprise",
    "fact_job_posting",
    "fact_graduate",
    "fact_employment",
    "fact_enrollment_plan",
    "fact_course_skill",
    "fact_policy_signal",
]

PRIMARY_KEYS = {
    "dim_school": ["school_id"],
    "dim_major_catalog": ["major_code"],
    "bridge_school_major": ["school_id", "major_code"],
    "dim_industry": ["industry_id"],
    "dim_job_category": ["job_category_id"],
    "dim_enterprise": ["enterprise_id"],
    "fact_job_posting": ["posting_id"],
    "fact_graduate": ["graduate_id"],
    "fact_employment": ["employment_id"],
    "fact_enrollment_plan": ["plan_id"],
    "fact_course_skill": ["course_id"],
    "fact_policy_signal": ["policy_id"],
}

MONTH_COLUMNS = {
    "fact_job_posting": "month",
    "fact_employment": "employment_month",
    "fact_policy_signal": "month",
}


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def validate_table(name: str, df: pd.DataFrame, context: dict[str, pd.DataFrame]) -> None:
    keys = PRIMARY_KEYS[name]
    missing = [key for key in keys if key not in df.columns]
    if missing:
        raise ValueError(f"{name} 缺少主键字段: {missing}")
    if df[keys].isna().any().any():
        raise ValueError(f"{name} 主键存在空值")
    if df.duplicated(keys).any():
        raise ValueError(f"{name} 主键重复")
    if name in MONTH_COLUMNS:
        col = MONTH_COLUMNS[name]
        bad = ~df[col].astype(str).str.match(r"^\d{4}-\d{2}$")
        if bad.any():
            raise ValueError(f"{name}.{col} 存在错误月份格式")
    if "major_code" in df.columns and "dim_major_catalog" in context:
        majors = set(context["dim_major_catalog"]["major_code"].astype(str))
        values = set(df["major_code"].dropna().astype(str))
        diff = values - majors
        if diff:
            raise ValueError(f"{name} 存在未登记专业代码: {list(diff)[:5]}")
    if "school_id" in df.columns and "dim_school" in context:
        schools = set(context["dim_school"]["school_id"].astype(str))
        values = set(df["school_id"].dropna().astype(str))
        diff = values - schools
        if diff:
            raise ValueError(f"{name} 存在未登记学校: {list(diff)[:5]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--input", default=str(ROOT / "data" / "generated"))
    args = parser.parse_args()

    input_dir = Path(args.input)
    engine = create_engine(DB_URL, pool_pre_ping=True)
    context: dict[str, pd.DataFrame] = {}

    with engine.begin() as conn:
        if args.reset:
            for table in reversed(LOAD_ORDER):
                conn.execute(text(f"TRUNCATE TABLE `{table}`"))

        for table in LOAD_ORDER:
            path = input_dir / f"{table}.csv"
            if not path.exists():
                raise FileNotFoundError(path)
            df = read_csv(path)
            validate_table(table, df, context)
            df.to_sql(table, conn, if_exists="append", index=False, chunksize=3000, method="multi")
            context[table] = df
            count = conn.execute(text(f"SELECT COUNT(*) FROM `{table}`")).scalar()
            print(f"{table}: {count}")

    print("数据导入完成，开始运行质量检查。")
    import subprocess

    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_data_quality.py")], cwd=ROOT, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
