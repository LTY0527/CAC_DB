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
from scripts.migrate_schema import BUSINESS_TABLES, AUDIT_COLUMNS, SECURITY_USER_COLUMNS, configure_utf8  # noqa: E402


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


def columns(conn, table_name: str) -> set[str]:
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


def main() -> None:
    configure_utf8()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    failed = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print(f"数据库连接正常：{DB_SETTINGS['user']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}")

            checks = {
                "sys_user_account": set(SECURITY_USER_COLUMNS),
                "sys_audit_log": set(AUDIT_COLUMNS),
            }
            for table_name, required_columns in checks.items():
                if not table_exists(conn, table_name):
                    print(f"[失败] 缺少表 {table_name}")
                    failed = True
                    continue
                missing = sorted(required_columns - columns(conn, table_name))
                if missing:
                    print(f"[失败] {table_name} 缺少字段：{', '.join(missing)}")
                    failed = True
                else:
                    print(f"[通过] {table_name} 字段完整")

            for table_name in BUSINESS_TABLES:
                if table_exists(conn, table_name):
                    print(f"[通过] 业务表存在：{table_name}")
                else:
                    print(f"[提示] 业务表缺失：{table_name}，请运行完整数据链路")

    except SQLAlchemyError as exc:
        print(f"数据库结构检查失败：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if failed:
        print("数据库结构未同步，请运行：python scripts/migrate_schema.py", file=sys.stderr)
        raise SystemExit(1)
    print("数据库结构检查通过。")


if __name__ == "__main__":
    main()
