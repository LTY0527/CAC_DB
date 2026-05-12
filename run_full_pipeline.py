# -*- coding: utf-8 -*-
"""
高校“需求—招生—培养—就业—监测”一体化平台一键链路脚本。

链路：
1. 数据集团样本数据生成
2. 初始化数据库表结构
3. 导入基础数据与岗位需求数据
4. 初始化账号、权限与审计表
5. Spark 特征加工与 ADS 聚合
6. LSTM 岗位需求人数预测
7. 协同过滤招生匹配与就业推荐
8. FP-Growth 关联规则挖掘
9. 培养方案优化建议生成
10. 结果校验与链路日志汇总

第一轮重构保证 1-6 阶段跑通；后续算法脚本若尚未完成深改，会被记录为
可降级阶段，不影响数据库与岗位需求预测主链路。
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

from config import DB_SETTINGS, DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
PIPELINE_BATCH_ID = f"CHAIN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
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


@dataclass(frozen=True)
class TableCheck:
    name: str
    min_rows: int = 1
    required: bool = True


@dataclass(frozen=True)
class FileCheck:
    path: str
    min_size_bytes: int = 1
    required: bool = True


@dataclass(frozen=True)
class PipelineStage:
    order: int
    key: str
    stage_name: str
    script: str | None
    algorithm_name: str
    input_tables: tuple[str, ...] = ()
    output_tables: tuple[str, ...] = ()
    requires_tables: tuple[TableCheck, ...] = ()
    produces_tables: tuple[TableCheck, ...] = ()
    requires_files: tuple[FileCheck, ...] = ()
    produces_files: tuple[FileCheck, ...] = ()
    env: dict[str, str] = field(default_factory=dict)
    core: bool = True


CSV_FILES = (
    FileCheck("dim_student.csv"),
    FileCheck("dim_company.csv"),
    FileCheck("fact_academic.csv"),
    FileCheck("fact_employment.csv"),
    FileCheck("fact_job_demand.csv"),
)

BASE_TABLES = (
    TableCheck("dim_student", min_rows=0),
    TableCheck("dim_company", min_rows=0),
    TableCheck("fact_academic", min_rows=0),
    TableCheck("fact_employment", min_rows=0),
    TableCheck("fact_job_demand", min_rows=0),
    TableCheck("ods_cleaning_log", min_rows=0),
    TableCheck("ads_algorithm_chain_log", min_rows=0),
    TableCheck("sys_audit_log", min_rows=0),
)

BASE_TABLES_WITH_DATA = (
    TableCheck("dim_student"),
    TableCheck("dim_company"),
    TableCheck("fact_academic"),
    TableCheck("fact_employment"),
    TableCheck("fact_job_demand"),
    TableCheck("ods_cleaning_log"),
)

PIPELINE_STAGES = (
    PipelineStage(
        order=1,
        key="generate_data",
        stage_name="数据集团样本数据生成",
        script="platform_data_factory.py",
        algorithm_name="DataGroupSyntheticFactory",
        output_tables=(),
        produces_files=CSV_FILES,
        core=True,
    ),
    PipelineStage(
        order=2,
        key="create_tables",
        stage_name="初始化数据库表结构",
        script="create_tables.py",
        algorithm_name="MySQL DDL",
        output_tables=tuple(table.name for table in BASE_TABLES),
        produces_tables=BASE_TABLES,
        core=True,
    ),
    PipelineStage(
        order=3,
        key="import_data",
        stage_name="导入基础数据与岗位需求数据",
        script="PutData.py",
        algorithm_name="ODS Cleaning + MySQL Load",
        input_tables=tuple(table.name for table in BASE_TABLES),
        output_tables=tuple(table.name for table in BASE_TABLES_WITH_DATA),
        requires_files=CSV_FILES,
        requires_tables=BASE_TABLES,
        produces_tables=BASE_TABLES_WITH_DATA,
        core=True,
    ),
    PipelineStage(
        order=4,
        key="init_security",
        stage_name="初始化账号权限与审计表",
        script="init_security.py",
        algorithm_name="PasswordHash + RoleBootstrap",
        input_tables=("sys_audit_log",),
        output_tables=("sys_audit_log",),
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(TableCheck("sys_audit_log", min_rows=0),),
        core=False,
    ),
    PipelineStage(
        order=5,
        key="spark_features",
        stage_name="Spark 特征加工与 ADS 聚合",
        script="Spark-all.py",
        algorithm_name="Spark/Pandas Feature Engineering",
        input_tables=("fact_employment", "fact_academic", "fact_job_demand"),
        output_tables=("ads_employment_summary", "ads_school_kpi", "ads_job_demand_monthly", "ads_job_skill_heatmap", "ads_major_supply_demand_gap"),
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(
            TableCheck("ads_employment_summary", min_rows=0, required=False),
            TableCheck("ads_school_kpi", min_rows=0, required=False),
            TableCheck("ads_job_demand_monthly", min_rows=0, required=False),
            TableCheck("ads_job_skill_heatmap", min_rows=0, required=False),
            TableCheck("ads_major_supply_demand_gap", min_rows=0, required=False),
        ),
        env={"MATCHING_DATA_SOURCE": "jdbc"},
        core=False,
    ),
    PipelineStage(
        order=6,
        key="lstm_job_demand",
        stage_name="LSTM 岗位需求人数预测",
        script="LSTM-job-demand.py",
        algorithm_name="LSTM",
        input_tables=("ads_job_demand_monthly", "fact_job_demand", "fact_employment", "fact_academic"),
        output_tables=("ads_job_demand_forecast", "ads_job_demand_forecast_eval", "ads_job_demand_forecast_backtest"),
        requires_tables=(TableCheck("fact_job_demand"),),
        produces_tables=(
            TableCheck("ads_job_demand_forecast"),
            TableCheck("ads_job_demand_forecast_eval"),
            TableCheck("ads_job_demand_forecast_backtest"),
        ),
        core=True,
    ),
    PipelineStage(
        order=7,
        key="cf_matching",
        stage_name="协同过滤招生匹配与就业推荐",
        script="CF-all.py",
        algorithm_name="Collaborative Filtering + Cosine Similarity",
        input_tables=("fact_academic", "fact_employment", "ads_job_demand_forecast"),
        output_tables=("ads_enrollment_matching", "ads_enrollment_matching_eval", "ads_job_recommendation", "ads_job_recommendation_eval"),
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(
            TableCheck("ads_enrollment_matching", min_rows=0, required=False),
            TableCheck("ads_enrollment_matching_eval", min_rows=0, required=False),
            TableCheck("ads_job_recommendation", min_rows=0, required=False),
            TableCheck("ads_job_recommendation_eval", min_rows=0, required=False),
        ),
        env={"MATCHING_DATA_SOURCE": "jdbc", "MATCHING_OUTPUT_MODE": "jdbc"},
        core=False,
    ),
    PipelineStage(
        order=8,
        key="fp_growth",
        stage_name="FP-Growth 关联规则挖掘",
        script="FPgrowth-all.py",
        algorithm_name="FP-Growth",
        input_tables=("fact_job_demand", "fact_employment", "fact_academic"),
        output_tables=("ads_major_matching_rules",),
        requires_tables=BASE_TABLES_WITH_DATA,
        produces_tables=(TableCheck("ads_major_matching_rules", min_rows=0, required=False),),
        env={"MATCHING_DATA_SOURCE": "jdbc"},
        core=False,
    ),
    PipelineStage(
        order=9,
        key="training_suggestion",
        stage_name="培养方案优化建议生成",
        script="training_program_suggester.py",
        algorithm_name="RuleBasedTrainingProgramSuggestion",
        input_tables=("ads_job_demand_forecast", "ads_job_skill_heatmap", "ads_major_matching_rules", "ads_major_supply_demand_gap"),
        output_tables=("ads_training_program_suggestions",),
        produces_tables=(TableCheck("ads_training_program_suggestions", min_rows=0, required=False),),
        core=False,
    ),
    PipelineStage(
        order=10,
        key="summary",
        stage_name="结果校验与链路日志汇总",
        script=None,
        algorithm_name="ResultValidation",
        input_tables=("ads_algorithm_chain_log",),
        output_tables=("ads_algorithm_chain_log",),
        core=True,
    ),
)


def get_db_engine():
    engine = create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


DB_ENGINE = get_db_engine()
PENDING_CHAIN_LOGS: list[dict] = []


def log_banner(title: str) -> None:
    logger.info("")
    logger.info("=" * 88)
    logger.info(title)
    logger.info("=" * 88)


def table_exists(table_name: str) -> bool:
    with DB_ENGINE.connect() as conn:
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


def fetch_table_row_count(table_name: str) -> int | None:
    if not table_exists(table_name):
        return None
    with DB_ENGINE.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar() or 0)


def verify_files(checks: tuple[FileCheck, ...], reason: str) -> None:
    for check in checks:
        file_path = ROOT_DIR / check.path
        if not file_path.exists():
            message = f"{reason}: 缺少文件 {file_path}"
            if check.required:
                raise FileNotFoundError(message)
            logger.warning(message)
            continue
        size = file_path.stat().st_size
        if size < check.min_size_bytes:
            message = f"{reason}: 文件为空或异常 {file_path}，size={size}"
            if check.required:
                raise RuntimeError(message)
            logger.warning(message)
            continue
        logger.info("依赖文件检查通过：%s，size=%s bytes", file_path.name, size)


def verify_tables(checks: tuple[TableCheck, ...], reason: str) -> None:
    for check in checks:
        row_count = fetch_table_row_count(check.name)
        if row_count is None:
            message = f"{reason}: 数据表不存在 {check.name}"
            if check.required:
                raise RuntimeError(message)
            logger.warning(message)
            continue
        if row_count < check.min_rows:
            message = f"{reason}: 数据表 {check.name} 行数不足，当前 {row_count}，期望至少 {check.min_rows}"
            if check.required:
                raise RuntimeError(message)
            logger.warning(message)
            continue
        logger.info("依赖表检查通过：%s，行数=%s", check.name, row_count)


def ensure_chain_log_table() -> bool:
    return table_exists("ads_algorithm_chain_log")


def build_chain_log_params(stage: PipelineStage, status: str, started_at: datetime, finished_at: datetime, row_count: int, error_message: str = "") -> dict:
    return {
        "batch_id": PIPELINE_BATCH_ID,
        "stage_order": stage.order,
        "stage_name": stage.stage_name,
        "input_tables": ",".join(stage.input_tables),
        "output_tables": ",".join(stage.output_tables),
        "algorithm_name": stage.algorithm_name,
        "status": status,
        "row_count": row_count,
        "started_at": started_at,
        "finished_at": finished_at,
        "cost_seconds": round((finished_at - started_at).total_seconds(), 2),
        "error_message": error_message[:2000] if error_message else None,
    }


def insert_chain_log_rows(rows: list[dict]) -> None:
    with DB_ENGINE.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO ads_algorithm_chain_log (
                    batch_id, stage_order, stage_name, input_tables, output_tables,
                    algorithm_name, status, row_count, started_at, finished_at,
                    cost_seconds, error_message
                )
                VALUES (
                    :batch_id, :stage_order, :stage_name, :input_tables, :output_tables,
                    :algorithm_name, :status, :row_count, :started_at, :finished_at,
                    :cost_seconds, :error_message
                )
                """
            ),
            rows,
        )


def write_chain_log(stage: PipelineStage, status: str, started_at: datetime, finished_at: datetime, row_count: int, error_message: str = "") -> None:
    """写入算法链路运行日志；建表前阶段先缓存在内存中。"""
    params = build_chain_log_params(stage, status, started_at, finished_at, row_count, error_message)
    if stage.order < 2 or not ensure_chain_log_table():
        PENDING_CHAIN_LOGS.append(params)
        return
    rows = []
    if PENDING_CHAIN_LOGS:
        rows.extend(PENDING_CHAIN_LOGS)
        PENDING_CHAIN_LOGS.clear()
    rows.append(params)
    insert_chain_log_rows(rows)


def count_outputs(stage: PipelineStage) -> int:
    """统计阶段产物总行数，不存在的非核心表按 0 处理。"""
    total = 0
    for table_name in stage.output_tables:
        count = fetch_table_row_count(table_name)
        if count is not None:
            total += count
    return total


def run_script(stage: PipelineStage) -> None:
    script_path = ROOT_DIR / str(stage.script)
    if not script_path.exists():
        raise FileNotFoundError(f"阶段脚本不存在：{script_path}")

    env = os.environ.copy()
    env.update(stage.env)
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(ROOT_DIR),
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"脚本 {stage.script} 返回码 {result.returncode}")


def run_summary_stage(stage: PipelineStage) -> None:
    logger.info("结果表行数汇总：")
    for table_name in [
        "dim_student",
        "dim_company",
        "fact_academic",
        "fact_employment",
        "fact_job_demand",
        "ods_cleaning_log",
        "ads_job_demand_monthly",
        "ads_job_skill_heatmap",
        "ads_major_supply_demand_gap",
        "ads_job_demand_forecast",
        "ads_job_demand_forecast_eval",
        "ads_job_demand_forecast_backtest",
        "ads_enrollment_matching",
        "ads_job_recommendation",
        "ads_major_matching_rules",
        "ads_training_program_suggestions",
        "ads_algorithm_chain_log",
        "sys_audit_log",
    ]:
        count = fetch_table_row_count(table_name)
        logger.info("  - %-38s %s", table_name, "未创建" if count is None else f"{count} 行")


def run_stage(stage: PipelineStage) -> bool:
    """执行单个阶段，并写入链路日志。"""
    started_at = datetime.now()
    log_banner(f"阶段 {stage.order}/10：{stage.stage_name}")
    logger.info("阶段标识=%s，算法=%s，核心阶段=%s", stage.key, stage.algorithm_name, "是" if stage.core else "否")

    status = "SUCCESS"
    error_message = ""
    row_count = 0
    try:
        if stage.requires_files:
            verify_files(stage.requires_files, f"{stage.stage_name} 依赖文件检查失败")
        if stage.requires_tables:
            verify_tables(stage.requires_tables, f"{stage.stage_name} 依赖表检查失败")

        if stage.script is None:
            run_summary_stage(stage)
        else:
            run_script(stage)

        if stage.produces_files:
            verify_files(stage.produces_files, f"{stage.stage_name} 产物文件校验失败")
        if stage.produces_tables:
            verify_tables(stage.produces_tables, f"{stage.stage_name} 产物表校验失败")
        row_count = count_outputs(stage)
    except Exception as exc:  # noqa: BLE001
        status = "FAILED"
        error_message = str(exc)
        logger.exception("阶段执行失败：%s", stage.stage_name)
        if stage.core:
            finished_at = datetime.now()
            write_chain_log(stage, status, started_at, finished_at, row_count, error_message)
            raise
        logger.warning("该阶段为可降级阶段，已记录失败原因，主链路继续执行。")

    finished_at = datetime.now()
    write_chain_log(stage, status, started_at, finished_at, row_count, error_message)
    logger.info(
        "阶段完成：%s，状态=%s，输出行数=%s，耗时=%.2fs",
        stage.stage_name,
        status,
        row_count,
        (finished_at - started_at).total_seconds(),
    )
    return status == "SUCCESS"


def main() -> int:
    log_banner("高校需求—招生—培养—就业—监测一体化平台算法链路启动")
    logger.info("工作目录：%s", ROOT_DIR)
    logger.info("数据库：%s:%s/%s", DB_SETTINGS["host"], DB_SETTINGS["port"], DB_SETTINGS["database"])
    logger.info("链路批次：%s", PIPELINE_BATCH_ID)

    try:
        success_map = {}
        for stage in PIPELINE_STAGES:
            success_map[stage.key] = run_stage(stage)

        log_banner("算法链路执行完成")
        for stage in PIPELINE_STAGES:
            logger.info("阶段 %02d %-22s %s", stage.order, stage.stage_name, "成功" if success_map.get(stage.key) else "降级/失败")
        logger.info("链路日志表：ads_algorithm_chain_log，批次=%s", PIPELINE_BATCH_ID)
        logger.info("控制台日志文件：%s", LOG_FILE)
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("算法链路执行失败：%s", exc)
        logger.error("请查看日志文件：%s", LOG_FILE)
        return 1


if __name__ == "__main__":
    sys.exit(main())
