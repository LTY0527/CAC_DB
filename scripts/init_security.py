# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL  # noqa: E402
from scripts.migrate_schema import configure_utf8, ensure_schema  # noqa: E402

USERS = [
    {
        "username": "teacher_shu",
        "password": "123456",
        "role": "teacher",
        "school_id": "SHU007",
        "display_name": "上海大学教师",
        "email": "teacher_shu@example.edu.cn",
        "phone": None,
    },
    {
        "username": "gov_sh",
        "password": "123456",
        "role": "government",
        "school_id": None,
        "display_name": "市教委专员",
        "email": "gov_sh@example.gov.cn",
        "phone": None,
    },
    {
        "username": "guest",
        "password": "123456",
        "role": "public",
        "school_id": None,
        "display_name": "社会公众",
        "email": None,
        "phone": None,
    },
]


def init_default_users(engine: Engine | None = None, *, reset_password: bool = True) -> None:
    configure_utf8()
    ensure_schema(verbose=False)
    engine = engine or create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        for user in USERS:
            password_hash = generate_password_hash(user["password"], method="scrypt")
            conn.execute(
                text(
                    """
                    INSERT INTO sys_user_account (
                        username,
                        password_hash,
                        hash_algo,
                        hash_version,
                        role,
                        school_id,
                        display_name,
                        email,
                        phone,
                        account_status,
                        failed_login_count,
                        failed_attempts,
                        last_failed_login_at,
                        lock_until,
                        password_updated_at
                    ) VALUES (
                        :username,
                        :password_hash,
                        'scrypt',
                        'v1',
                        :role,
                        :school_id,
                        :display_name,
                        :email,
                        :phone,
                        'active',
                        0,
                        0,
                        NULL,
                        NULL,
                        CURRENT_TIMESTAMP
                    )
                    ON DUPLICATE KEY UPDATE
                        password_hash = CASE WHEN :reset_password THEN VALUES(password_hash) ELSE password_hash END,
                        hash_algo = 'scrypt',
                        hash_version = 'v1',
                        role = VALUES(role),
                        school_id = VALUES(school_id),
                        display_name = VALUES(display_name),
                        email = VALUES(email),
                        phone = VALUES(phone),
                        account_status = CASE WHEN account_status = 'disabled' THEN account_status ELSE 'active' END,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "username": user["username"],
                    "password_hash": password_hash,
                    "role": user["role"],
                    "school_id": user["school_id"],
                    "display_name": user["display_name"],
                    "email": user["email"],
                    "phone": user["phone"],
                    "reset_password": reset_password,
                },
            )


def main() -> None:
    init_default_users()
    print("安全账户初始化完成。默认账户：teacher_shu/gov_sh/guest，默认密码：123456")


if __name__ == "__main__":
    main()
