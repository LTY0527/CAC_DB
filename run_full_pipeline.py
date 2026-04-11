"""
高校人才培养与就业大数据平台一键全流程脚本

执行链路:
1. 数据生成
2. 基础表建表
3. 基础数据导入
4. 特征加工/ADS 聚合
5. LSTM 需求预测
6. 协同过滤招生匹配 + 余弦相似度就业推荐
7. 关联规则挖掘
8. 结果校验
"""

from __future__ import annotations

import io
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from config import DB_SETTINGS, DB_URL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
LOG_FILE = ROOT_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def build_db_engine():
    fallback_url = (
        f"mysql+pymysql://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}"
        f"@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}?charset=utf8mb4"
    )
    candidate_urls = (DB_URL, fallback_url)

    last_error = None
    for url in candidate_urls:
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("[数据库] 使用连接串: %s", url.split("@", 1)[0])
            return engine
        except Exception as exc:  # noqa: BLE001
            last_error = exc

    raise RuntimeError(f"无法创建数据库连接: {last_error}") from last_error


DB_ENGINE = build_db_engine()


@dataclass(frozen=True)
class TableCheck:
    name: str
    min_rows: int = 1


@dataclass(frozen=True)
class FileCheck:
    path: str
    min_size_bytes: int = 1


@dataclass(frozen=True)
class PipelineStage:
    key: str
    description: str
    script: str
    env: dict[str, str] = field(default_factory=dict)
    requires_tables: tuple[TableCheck, ...] = ()
    requires_files: tuple[FileCheck, ...] = ()
    produces_tables: tuple[TableCheck, ...] = ()
    produces_files: tuple[FileCheck, ...] = ()


BASE_TABLES = (
    TableCheck("dim_student", min_rows=0),
    TableCheck("dim_company", min_rows=0),
    TableCheck("fact_academic", min_rows=0),
    TableCheck("fact_employment", min_rows=0),
)

BASE_TABLES_WITH_DATA = (
    TableCheck("dim_student"),
    TableCheck("dim_company"),
    TableCheck("fact_academic"),
    TableCheck("fact_employment"),
)

RESULT_TABLES = (
    TableCheck("ads_employment_summary"),
    TableCheck("ads_school_kpi"),
    TableCheck("ads_salary_forecast"),
    TableCheck("ads_salary_forecast_eval"),
    TableCheck("ads_salary_forecast_backtest"),
    TableCheck("ads_enrollment_matching"),
    TableCheck("ads_enrollment_matching_eval"),
    TableCheck("ads_major_matching_rules"),
    TableCheck("ads_training_program_suggestions"),
    TableCheck("ads_job_recommendation"),
    TableCheck("ads_job_recommendation_eval"),
)

CSV_FILES = (
    FileCheck("dim_student.csv"),
    FileCheck("dim_company.csv"),
    FileCheck("fact_academic.csv"),
    FileCheck("fact_employment.csv"),
)

PIPELINE_STAGES = (
    PipelineStage(
        key="generate_data",
        description="阶段 1/7 生成样本数据",
        script="platform_data_factory.py",
        produces_files=CSV_FILES,
    ),
    PipelineStage(
        key="create_base_tables",
        description="阶段 2/7 初始化基础表结构",
        script="create_tables.py",
        produces_tables=BASE_TABLES,
    ),
    PipelineStage(
        key="import_base_data",
        description="阶段 3/8 导入基础数据到 MySQL",
        script="PutData.py",
        requires_files=CSV_FILES,
        requires_tables=BASE_TABLES,
        produces_tables=BASE_TABLES_WITH_DATA,
    ),
    PipelineStage(
        key="init_security",
        description="阶段 4/8 初始化系统账号与审计表",
        script="init_security.py",
        requires_tables=BASE_TABLES_WITH_DATA,
    ),
    PipelineStage(
        key="feature_engineering",
        description="阶段 5/8 特征加工与 ADS 聚合",
        script="Spark-all.py",
        env={"MATCHING_DATA_SOURCE": "jdbc"},
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(TableCheck("ads_employment_summary"), TableCheck("ads_school_kpi")),
    ),
    PipelineStage(
        key="lstm_forecast",
        description="阶段 6/8 LSTM 需求预测",
        script="LSTM-all.py",
        requires_tables=(TableCheck("fact_employment"),),
        produces_tables=(
            TableCheck("ads_salary_forecast"),
            TableCheck("ads_salary_forecast_eval"),
            TableCheck("ads_salary_forecast_backtest"),
        ),
    ),
    PipelineStage(
        key="matching",
        description="阶段 7/8 协同过滤招生匹配与余弦相似度就业推荐",
        script="CF-all.py",
        env={
            "MATCHING_DATA_SOURCE": "jdbc",
            "MATCHING_OUTPUT_MODE": "jdbc",
        },
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(
            TableCheck("ads_enrollment_matching"),
            TableCheck("ads_job_recommendation"),
            TableCheck("ads_enrollment_matching_eval"),
            TableCheck("ads_job_recommendation_eval"),
        ),
    ),
    PipelineStage(
        key="rule_mining",
        description="阶段 8/8 关联规则挖掘",
        script="FPgrowth-all.py",
        env={"MATCHING_DATA_SOURCE": "jdbc"},
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(
            TableCheck("ads_major_matching_rules"),
            TableCheck("ads_training_program_suggestions"),
        ),
    ),
)


def log_banner(title: str) -> None:
    logger.info("\n%s", "=" * 78)
    logger.info(title)
    logger.info("%s", "=" * 78)


def ensure_script_exists(script_name: str) -> Path:
    script_path = ROOT_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"脚本不存在: {script_path}")
    return script_path


def verify_files(checks: tuple[FileCheck, ...], reason: str) -> None:
    for check in checks:
        file_path = ROOT_DIR / check.path
        if not file_path.exists():
            raise FileNotFoundError(f"{reason}: 缺少文件 {file_path}")
        size = file_path.stat().st_size
        if size < check.min_size_bytes:
            raise RuntimeError(f"{reason}: 文件为空或异常 {file_path} (size={size})")
        logger.info("[依赖检查] 文件 %s 已就绪, size=%s bytes", file_path.name, size)


def fetch_table_row_count(table_name: str) -> int:
    with DB_ENGINE.connect() as conn:
        exists_sql = text(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_name = :table_name
            """
        )
        exists = conn.execute(exists_sql, {"table_name": table_name}).scalar() or 0
        if not exists:
            raise RuntimeError(f"数据表不存在: {table_name}")

        count_sql = text(f"SELECT COUNT(*) FROM `{table_name}`")
        return int(conn.execute(count_sql).scalar() or 0)


def verify_tables(checks: tuple[TableCheck, ...], reason: str) -> None:
    for check in checks:
        row_count = fetch_table_row_count(check.name)
        if row_count < check.min_rows:
            raise RuntimeError(
                f"{reason}: 数据表 {check.name} 行数不足, 当前 {row_count}, 期望至少 {check.min_rows}"
            )
        logger.info("[依赖检查] 表 %s 行数=%s", check.name, row_count)


def verify_database_connection() -> None:
    try:
        with DB_ENGINE.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("[数据库] 连接成功")
    except SQLAlchemyError as exc:
        raise RuntimeError(f"数据库连接失败: {exc}") from exc


def run_stage(stage: PipelineStage) -> None:
    script_path = ensure_script_exists(stage.script)

    if stage.requires_files:
        verify_files(stage.requires_files, f"{stage.description} 依赖检查失败")
    if stage.requires_tables:
        verify_tables(stage.requires_tables, f"{stage.description} 依赖检查失败")

    log_banner(stage.description)
    logger.info("[阶段开始] key=%s script=%s", stage.key, script_path.name)

    env = os.environ.copy()
    env.update(stage.env)
    env["PYTHONIOENCODING"] = "utf-8"

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR),
        env=env,
        check=False,
    )
    duration = time.time() - start

    if result.returncode != 0:
        raise RuntimeError(
            f"{stage.description} 失败: 脚本 {stage.script} 返回码 {result.returncode}"
        )

    if stage.produces_files:
        verify_files(stage.produces_files, f"{stage.description} 产物校验失败")
    if stage.produces_tables:
        verify_tables(stage.produces_tables, f"{stage.description} 产物校验失败")
        logger.info("[数据库写入] %s 对应结果表校验通过", stage.description)

    logger.info("[阶段完成] key=%s cost=%.2fs", stage.key, duration)


def summarize_success() -> None:
    log_banner("全流程执行完成")
    logger.info("日志文件: %s", LOG_FILE)
    for table in RESULT_TABLES:
        row_count = fetch_table_row_count(table.name)
        logger.info("[结果表] %s -> %s 行", table.name, row_count)


def main() -> int:
    try:
        log_banner("高校人才培养与就业大数据平台一键全流程启动")
        logger.info("工作目录: %s", ROOT_DIR)
        verify_database_connection()

        for stage in PIPELINE_STAGES:
            run_stage(stage)

        summarize_success()
        logger.info("全部阶段执行成功，前后端现在可以直接读取最新分析结果。")
        return 0
    except Exception as exc:
        logger.exception("[流程失败] %s", exc)
        logger.error("失败脚本或阶段请查看上方日志和文件: %s", LOG_FILE)
        return 1


if __name__ == "__main__":
    sys.exit(main())
