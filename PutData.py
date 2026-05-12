# -*- coding: utf-8 -*-
"""
CSV 数据导入 MySQL 脚本。

导入数据集团多源异构样本数据，支持基础表和 fact_job_demand 岗位需求事实表。
岗位需求导入前会执行清洗、去重、标准化、异常值处理，并写入 ods_cleaning_log，
便于答辩展示“数据清洗过程”和“数据仓库入库过程”。
"""

from __future__ import annotations

import ast
import io
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
LOG_FILE = ROOT_DIR / f"mysql_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
class ImportTask:
    file_name: str
    table_name: str
    description: str
    primary_key: str | None = None
    source_name: str = "数据集团样本数据"


IMPORT_TASKS = [
    ImportTask("dim_student.csv", "dim_student", "学生维度表", "student_id", "学生画像库"),
    ImportTask("dim_company.csv", "dim_company", "企业维度表", "company_id", "企业画像库"),
    ImportTask("fact_academic.csv", "fact_academic", "学业事实表", "academic_id", "高校教务库"),
    ImportTask("fact_employment.csv", "fact_employment", "就业事实表", "emp_id", "社保就业库"),
    ImportTask("fact_job_demand.csv", "fact_job_demand", "岗位需求事实表", "demand_id", "数据集团企业招聘库"),
]

TABLE_WHITELIST = {task.table_name for task in IMPORT_TASKS}


def get_db_engine():
    """创建数据库连接引擎。"""
    engine = create_engine(
        DB_URL_PYMYSQL,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=8,
        max_overflow=12,
    )
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("数据库连接验证成功")
    return engine


def table_exists(engine, table_name: str) -> bool:
    """检查目标表是否存在。"""
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).scalar()
    return bool(exists)


def require_tables(engine) -> None:
    """导入前校验表结构。"""
    required_tables = sorted(TABLE_WHITELIST | {"ods_cleaning_log"})
    missing = [table for table in required_tables if not table_exists(engine, table)]
    if missing:
        raise RuntimeError(f"缺少数据表：{', '.join(missing)}。请先执行 python create_tables.py")


def safe_json_array(value: Any) -> str:
    """将技能关键词等异构格式统一为 JSON 数组字符串。"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return json.dumps([], ensure_ascii=False)
    if isinstance(value, list):
        items = value
    else:
        text_value = str(value).strip()
        if not text_value:
            items = []
        else:
            try:
                parsed = json.loads(text_value)
                items = parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                try:
                    parsed = ast.literal_eval(text_value)
                    items = parsed if isinstance(parsed, list) else [parsed]
                except Exception:
                    separators = ["、", ",", ";", "；", "|"]
                    normalized = text_value
                    for sep in separators:
                        normalized = normalized.replace(sep, ",")
                    items = [item.strip() for item in normalized.split(",") if item.strip()]
    clean_items = []
    for item in items:
        item_text = str(item).strip().strip("'\"")
        if item_text and item_text not in clean_items:
            clean_items.append(item_text)
    return json.dumps(clean_items, ensure_ascii=False)


def normalize_json_column(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """统一 JSON 列格式。"""
    if column_name in df.columns:
        df[column_name] = df[column_name].apply(safe_json_array)
    return df


def clean_basic_table(df: pd.DataFrame, table_name: str) -> tuple[pd.DataFrame, dict[str, int], str]:
    """清洗基础维表/事实表。"""
    raw_rows = len(df)
    missing_rows = int(df.isna().any(axis=1).sum())
    duplicate_rows = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    if table_name == "dim_company":
        df = normalize_json_column(df, "strategic_tags")
    if table_name == "fact_employment" and "first_insured_date" in df.columns:
        df["first_insured_date"] = pd.to_datetime(df["first_insured_date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df["avg_salary"] = pd.to_numeric(df["avg_salary"], errors="coerce").fillna(0).clip(lower=0, upper=200000)

    stats = {
        "raw_rows": raw_rows,
        "valid_rows": len(df),
        "invalid_rows": raw_rows - len(df),
        "duplicate_rows": duplicate_rows,
        "missing_value_rows": missing_rows,
        "outlier_rows": 0,
    }
    desc = "基础数据执行去重、日期标准化、JSON字段标准化和数值字段类型转换。"
    return df, stats, desc


def clean_job_demand(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int], str]:
    """清洗数据集团岗位需求事实数据。"""
    raw_rows = len(df)
    required_columns = ["job_title", "job_category", "major_name", "publish_date"]
    missing_rows = int(df[required_columns + ["employer_name"]].isna().any(axis=1).sum())
    duplicate_subset = [
        "employer_name",
        "job_title",
        "job_category",
        "major_name",
        "city",
        "publish_date",
        "source_channel",
    ]
    duplicate_rows = int(df.duplicated(subset=[col for col in duplicate_subset if col in df.columns]).sum())
    df = df.drop_duplicates(subset=[col for col in duplicate_subset if col in df.columns]).copy()

    # 岗位名称为非空字段，缺失时用岗位类别补齐；核心维度缺失则判为无效。
    if "job_title" in df.columns:
        df["job_title"] = df["job_title"].fillna(df["job_category"].fillna("未知岗位").astype(str) + "岗位")
    invalid_mask = pd.Series(False, index=df.index)
    for column in ["job_category", "major_name", "publish_date"]:
        invalid_mask = invalid_mask | df[column].isna()

    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    invalid_mask = invalid_mask | df["publish_date"].isna()

    numeric_columns = ["recruit_count", "salary_min", "salary_max", "salary_avg", "company_id"]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    recruit_original = df["recruit_count"].copy()
    df["recruit_count"] = df["recruit_count"].fillna(1)
    outlier_mask = (df["recruit_count"] <= 0) | (df["recruit_count"] > 300)
    df.loc[df["recruit_count"] <= 0, "recruit_count"] = 1
    df.loc[df["recruit_count"] > 300, "recruit_count"] = 300
    df["recruit_count"] = df["recruit_count"].round().astype(int)

    salary_min = df["salary_min"].copy()
    salary_max = df["salary_max"].copy()
    swap_mask = salary_min.notna() & salary_max.notna() & (salary_min > salary_max)
    df.loc[swap_mask, "salary_min"] = salary_max[swap_mask]
    df.loc[swap_mask, "salary_max"] = salary_min[swap_mask]
    salary_outlier_mask = (df["salary_min"] < 0) | (df["salary_max"] < 0) | (df["salary_max"] > 200000)
    df.loc[df["salary_min"] < 0, "salary_min"] = None
    df.loc[df["salary_max"] < 0, "salary_max"] = None
    df.loc[df["salary_max"] > 200000, "salary_max"] = 200000
    df["salary_avg"] = df[["salary_min", "salary_max"]].mean(axis=1).round(2)

    df = normalize_json_column(df, "skill_keywords")
    df["publish_date"] = df["publish_date"].dt.strftime("%Y-%m-%d")
    df["company_id"] = df["company_id"].where(df["company_id"].notna(), None)

    valid_df = df.loc[~invalid_mask].copy()
    stats = {
        "raw_rows": raw_rows,
        "valid_rows": len(valid_df),
        "invalid_rows": int(invalid_mask.sum()),
        "duplicate_rows": duplicate_rows,
        "missing_value_rows": missing_rows,
        "outlier_rows": int(outlier_mask.sum() + salary_outlier_mask.sum() + swap_mask.sum() + recruit_original.isna().sum()),
    }
    desc = (
        "岗位需求数据完成去重、岗位名称补齐、发布日期标准化、招聘人数负值/零值/极端值修正、"
        "薪资区间纠偏、技能关键词统一为JSON数组。"
    )
    return valid_df, stats, desc


def write_cleaning_log(conn, task: ImportTask, stats: dict[str, int], desc: str, started_at: datetime) -> None:
    """写入 ODS 清洗日志。"""
    finished_at = datetime.now()
    batch_id = None
    if task.table_name == "fact_job_demand":
        batch_id = f"DG_IMPORT_{started_at.strftime('%Y%m%d%H%M%S')}"
    conn.execute(
        text(
            """
            INSERT INTO ods_cleaning_log (
                batch_id, source_name, raw_rows, valid_rows, invalid_rows, duplicate_rows,
                missing_value_rows, outlier_rows, standardization_desc, started_at, finished_at
            )
            VALUES (
                :batch_id, :source_name, :raw_rows, :valid_rows, :invalid_rows, :duplicate_rows,
                :missing_value_rows, :outlier_rows, :standardization_desc, :started_at, :finished_at
            )
            """
        ),
        {
            "batch_id": batch_id,
            "source_name": task.source_name,
            "standardization_desc": desc,
            "started_at": started_at,
            "finished_at": finished_at,
            **stats,
        },
    )


def truncate_table(conn, table_name: str) -> None:
    """清空目标表，表名来自白名单。"""
    if table_name not in TABLE_WHITELIST:
        raise ValueError(f"非法表名：{table_name}")
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    conn.execute(text(f"TRUNCATE TABLE `{table_name}`"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


def import_single_table(engine, task: ImportTask) -> bool:
    """导入单张 CSV。"""
    file_path = ROOT_DIR / task.file_name
    logger.info("")
    logger.info("开始导入：%s -> %s", task.file_name, task.table_name)
    if not file_path.exists():
        logger.error("文件不存在：%s", file_path)
        return False

    started_at = datetime.now()
    start_time = time.time()
    try:
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        logger.info("读取完成：%s 行，%s 列", len(df), len(df.columns))
        if task.table_name == "fact_job_demand":
            clean_df, stats, desc = clean_job_demand(df)
        else:
            clean_df, stats, desc = clean_basic_table(df, task.table_name)

        with engine.begin() as conn:
            truncate_table(conn, task.table_name)
            clean_df.to_sql(
                name=task.table_name,
                con=conn,
                if_exists="append",
                index=False,
                chunksize=2000,
                method="multi",
            )
            write_cleaning_log(conn, task, stats, desc, started_at)

        logger.info(
            "导入完成：%s，有效 %s/%s 行，重复 %s 行，缺失 %s 行，异常 %s 行，耗时 %.2fs",
            task.table_name,
            stats["valid_rows"],
            stats["raw_rows"],
            stats["duplicate_rows"],
            stats["missing_value_rows"],
            stats["outlier_rows"],
            time.time() - start_time,
        )
        return True
    except Exception:
        logger.exception("导入失败：%s", task.table_name)
        return False


def import_all_data() -> bool:
    """按外键依赖顺序导入全部 CSV。"""
    logger.info("=" * 80)
    logger.info("数据集团多源异构数据入库开始")
    logger.info("=" * 80)
    engine = get_db_engine()
    require_tables(engine)

    success_count = 0
    for task in IMPORT_TASKS:
        if import_single_table(engine, task):
            success_count += 1

    logger.info("=" * 80)
    logger.info("入库完成：%s/%s 张表成功", success_count, len(IMPORT_TASKS))
    if success_count == len(IMPORT_TASKS):
        logger.info("基础数据、岗位需求数据和 ODS 清洗日志均已写入 MySQL。")
    logger.info("日志文件：%s", LOG_FILE)
    logger.info("=" * 80)
    return success_count == len(IMPORT_TASKS)


if __name__ == "__main__":
    sys.exit(0 if import_all_data() else 1)
