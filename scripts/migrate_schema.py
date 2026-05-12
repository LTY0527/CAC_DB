# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_SETTINGS, DB_URL  # noqa: E402


def configure_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


SECURITY_USER_COLUMNS = {
    "user_id": "BIGINT PRIMARY KEY AUTO_INCREMENT",
    "username": "VARCHAR(64) NOT NULL",
    "password_hash": "VARCHAR(255) NOT NULL DEFAULT ''",
    "hash_algo": "VARCHAR(32) NOT NULL DEFAULT 'scrypt'",
    "hash_version": "VARCHAR(32) NOT NULL DEFAULT 'v1'",
    "role": "VARCHAR(32) NOT NULL DEFAULT 'public'",
    # dim_school.school_id in this project uses values such as SHU007.
    "school_id": "VARCHAR(32) NULL",
    "display_name": "VARCHAR(64) NULL",
    "email": "VARCHAR(128) NULL",
    "phone": "VARCHAR(32) NULL",
    "account_status": "VARCHAR(32) NOT NULL DEFAULT 'active'",
    "failed_login_count": "INT NOT NULL DEFAULT 0",
    "failed_attempts": "INT NOT NULL DEFAULT 0",
    "last_failed_login_at": "DATETIME NULL",
    "lock_until": "DATETIME NULL",
    "last_login_at": "DATETIME NULL",
    "password_updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "created_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    "updated_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
}

AUDIT_COLUMNS = {
    "audit_id": "BIGINT PRIMARY KEY AUTO_INCREMENT",
    "user_id": "BIGINT NULL",
    "username": "VARCHAR(64) NULL",
    "role": "VARCHAR(32) NULL",
    "school_id": "VARCHAR(32) NULL",
    "action": "VARCHAR(80) NULL",
    "module": "VARCHAR(120) NULL",
    "ip": "VARCHAR(80) NULL",
    "detail_json": "JSON NULL",
    "action_type": "VARCHAR(64) NULL",
    "module_name": "VARCHAR(100) NULL",
    "target_type": "VARCHAR(64) NULL",
    "target_id": "VARCHAR(128) NULL",
    "request_path": "VARCHAR(255) NULL",
    "request_method": "VARCHAR(16) NULL",
    "result_status": "VARCHAR(20) NULL",
    "message": "VARCHAR(255) NULL",
    "ip_address": "VARCHAR(64) NULL",
    "user_agent": "VARCHAR(255) NULL",
    "created_at": "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
}

BUSINESS_TABLES = [
    "dim_school",
    "dim_major_catalog",
    "bridge_school_major",
    "dim_industry",
    "dim_job_category",
    "fact_job_posting",
    "fact_graduate",
    "fact_employment",
    "fact_enrollment_plan",
    "fact_course_skill",
    "ads_job_demand_forecast",
    "ads_enrollment_matching",
    "ads_training_rules",
    "ads_major_optimization",
    "ads_job_recommendation",
]


def table_exists(conn, table_name: str) -> bool:
    return bool(
        conn.execute(
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
    )


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


def unique_index_exists(conn, table_name: str, index_name: str) -> bool:
    return bool(
        conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.statistics
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                  AND index_name = :index_name
                """
            ),
            {"table_name": table_name, "index_name": index_name},
        ).scalar()
    )


def add_missing_columns(conn, table_name: str, required: dict[str, str], logs: list[str]) -> None:
    columns = existing_columns(conn, table_name)
    for column_name, ddl in required.items():
        if column_name in columns:
            logs.append(f"[存在字段] {table_name}.{column_name}")
            continue
        conn.execute(text(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {ddl}"))
        logs.append(f"[新增字段] {table_name}.{column_name} {ddl}")


def normalize_user_column_types(conn, logs: list[str]) -> None:
    alter_statements = [
        ("username", "MODIFY COLUMN username VARCHAR(64) NOT NULL"),
        ("role", "MODIFY COLUMN role VARCHAR(32) NOT NULL"),
        ("school_id", "MODIFY COLUMN school_id VARCHAR(32) NULL"),
        ("display_name", "MODIFY COLUMN display_name VARCHAR(64) NULL"),
        ("account_status", "MODIFY COLUMN account_status VARCHAR(32) NOT NULL DEFAULT 'active'"),
        ("created_at", "MODIFY COLUMN created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "MODIFY COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
    ]
    for column_name, ddl in alter_statements:
        try:
            conn.execute(text(f"ALTER TABLE sys_user_account {ddl}"))
            logs.append(f"[规范字段] sys_user_account.{column_name}")
        except SQLAlchemyError as exc:
            logs.append(f"[跳过规范] sys_user_account.{column_name}：{exc}")


def ensure_user_table(conn, logs: list[str]) -> None:
    if not table_exists(conn, "sys_user_account"):
        conn.execute(
            text(
                """
                CREATE TABLE sys_user_account (
                    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(64) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    hash_algo VARCHAR(32) NOT NULL DEFAULT 'scrypt',
                    hash_version VARCHAR(32) NOT NULL DEFAULT 'v1',
                    role VARCHAR(32) NOT NULL,
                    school_id VARCHAR(32) NULL,
                    display_name VARCHAR(64),
                    email VARCHAR(128),
                    phone VARCHAR(32),
                    account_status VARCHAR(32) NOT NULL DEFAULT 'active',
                    failed_login_count INT NOT NULL DEFAULT 0,
                    failed_attempts INT NOT NULL DEFAULT 0,
                    last_failed_login_at DATETIME NULL,
                    lock_until DATETIME NULL,
                    last_login_at DATETIME NULL,
                    password_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_user_role (role),
                    INDEX idx_user_school (school_id),
                    INDEX idx_user_status (account_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        )
        logs.append("[已创建表] sys_user_account")
        return

    logs.append("[跳过建表] sys_user_account 已存在")
    add_missing_columns(conn, "sys_user_account", SECURITY_USER_COLUMNS, logs)
    normalize_user_column_types(conn, logs)
    if not unique_index_exists(conn, "sys_user_account", "uk_sys_user_account_username"):
        try:
            conn.execute(text("ALTER TABLE sys_user_account ADD UNIQUE KEY uk_sys_user_account_username (username)"))
            logs.append("[新增索引] sys_user_account.uk_sys_user_account_username")
        except SQLAlchemyError as exc:
            logs.append(f"[跳过索引] username 可能已有唯一约束或存在重复值：{exc}")


def ensure_audit_table(conn, logs: list[str]) -> None:
    if not table_exists(conn, "sys_audit_log"):
        conn.execute(
            text(
                """
                CREATE TABLE sys_audit_log (
                    audit_id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NULL,
                    username VARCHAR(64) NULL,
                    role VARCHAR(32) NULL,
                    school_id VARCHAR(32) NULL,
                    action VARCHAR(80) NULL,
                    module VARCHAR(120) NULL,
                    ip VARCHAR(80) NULL,
                    detail_json JSON NULL,
                    action_type VARCHAR(64) NULL,
                    module_name VARCHAR(100) NULL,
                    target_type VARCHAR(64) NULL,
                    target_id VARCHAR(128) NULL,
                    request_path VARCHAR(255) NULL,
                    request_method VARCHAR(16) NULL,
                    result_status VARCHAR(20) NULL,
                    message VARCHAR(255) NULL,
                    ip_address VARCHAR(64) NULL,
                    user_agent VARCHAR(255) NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_audit_user (user_id),
                    INDEX idx_audit_created (created_at),
                    INDEX idx_audit_module (module),
                    INDEX idx_audit_module_name (module_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        )
        logs.append("[已创建表] sys_audit_log")
        return

    logs.append("[跳过建表] sys_audit_log 已存在")
    add_missing_columns(conn, "sys_audit_log", AUDIT_COLUMNS, logs)


def check_business_tables(conn, logs: list[str]) -> None:
    for table_name in BUSINESS_TABLES:
        if table_exists(conn, table_name):
            logs.append(f"[存在业务表] {table_name}")
        else:
            logs.append(f"[缺失业务表] {table_name}，请运行完整数据链路生成并导入数据")


def ensure_schema(verbose: bool = True) -> list[str]:
    configure_utf8()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    db_target = f"{DB_SETTINGS['user']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
    logs: list[str] = [f"[连接目标] {db_target}"]
    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
        ensure_user_table(conn, logs)
        ensure_audit_table(conn, logs)
        check_business_tables(conn, logs)
    if verbose:
        print("\n".join(logs))
    return logs


def main() -> None:
    try:
        ensure_schema(verbose=True)
        print("数据库结构迁移检查完成。")
    except SQLAlchemyError as exc:
        print(f"数据库结构迁移失败：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
