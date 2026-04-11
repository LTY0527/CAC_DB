from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer
from sqlalchemy import text


AUTH_SECRET = os.getenv("CAC_AUTH_SECRET", "cac-db-platform-auth-secret-v1")
AUTH_SALT = "cac-db-platform-auth"
AUTH_TOKEN_MAX_AGE = 60 * 60 * 24
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15

DEMO_ACCOUNT_SEEDS = (
    {
        "username": "teacher_shu",
        "password_hash": "scrypt:32768:8:1$rN7ko1A4rFcIFPfA$6107a4280af337a3985ea7e2a439916cca39e6dac6a1bbe80322917fa84a5e587ee82cef85f644076f287b491d6268af39ad4ed63ad660fda6d1b91f2508ceee",
        "hash_algo": "scrypt",
        "hash_version": "v1",
        "role": "teacher",
        "display_name": "张老师",
        "school_name": "上海大学",
        "account_status": "active",
    },
    {
        "username": "gov_sh",
        "password_hash": "scrypt:32768:8:1$TPgVGIrZcdBIx0Zr$af3b9fb737ff44e2884830d19b9955fd2d64bf35171b5c0a91d80306f9979f067c024a5271b4026f5f43f6977679a8b6cacb96d5879df89b26c6e5980261d311",
        "hash_algo": "scrypt",
        "hash_version": "v1",
        "role": "government",
        "display_name": "市教委专员",
        "school_name": None,
        "account_status": "active",
    },
    {
        "username": "guest",
        "password_hash": "scrypt:32768:8:1$givdbWsAlqfOLpOW$2d9ce01c959704573dad279162f29a980ed7b6336d3fca21da563f92c9cd845d349a4c36675dfe5aa7902ce4198a9d9c629e386241757ae30c5122926b84e887",
        "hash_algo": "scrypt",
        "hash_version": "v1",
        "role": "public",
        "display_name": "社会公众",
        "school_name": None,
        "account_status": "active",
    },
)


def get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=AUTH_SECRET, salt=AUTH_SALT)


def issue_auth_token(payload: dict[str, Any]) -> str:
    return get_serializer().dumps(payload)


def verify_auth_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        data = get_serializer().loads(token, max_age=AUTH_TOKEN_MAX_AGE)
        return data if isinstance(data, dict) else None
    except (BadSignature, BadTimeSignature):
        return None


def sanitize_log_text(value: Any, max_len: int = 255) -> str:
    if value is None:
        return ""
    text_value = str(value).replace("\r", " ").replace("\n", " ").strip()
    if len(text_value) > max_len:
        return text_value[: max_len - 3] + "..."
    return text_value


def extract_client_ip(flask_request) -> str:
    forwarded_for = sanitize_log_text(flask_request.headers.get("X-Forwarded-For"), max_len=128)
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return sanitize_log_text(flask_request.remote_addr or "", max_len=64)


def create_security_tables(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sys_school_ref (
                    school_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学校主键',
                    school_name VARCHAR(100) NOT NULL UNIQUE COMMENT '学校名称',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_school_name (school_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='系统学校引用表';
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sys_user_account (
                    user_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键',
                    username VARCHAR(64) NOT NULL COMMENT '登录名',
                    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
                    hash_algo VARCHAR(32) NOT NULL DEFAULT 'scrypt' COMMENT '哈希算法',
                    hash_version VARCHAR(16) NOT NULL DEFAULT 'v1' COMMENT '哈希版本',
                    role VARCHAR(32) NOT NULL COMMENT '角色 teacher/government/public',
                    school_id INT NULL COMMENT '所属学校ID',
                    display_name VARCHAR(64) NOT NULL COMMENT '显示名称',
                    account_status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT 'active/locked/disabled',
                    failed_attempts INT NOT NULL DEFAULT 0 COMMENT '连续失败次数',
                    lock_until DATETIME NULL COMMENT '锁定截止时间',
                    last_login_at DATETIME NULL COMMENT '最后登录时间',
                    password_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '密码更新时间',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT uk_sys_user_account_username UNIQUE (username),
                    CONSTRAINT fk_sys_user_account_school FOREIGN KEY (school_id) REFERENCES sys_school_ref(school_id),
                    INDEX idx_sys_user_role (role),
                    INDEX idx_sys_user_school_id (school_id),
                    INDEX idx_sys_user_status (account_status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='系统用户账户表';
                """
            )
        )

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sys_audit_log (
                    audit_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '审计日志主键',
                    user_id BIGINT NULL COMMENT '用户ID',
                    username VARCHAR(64) NULL COMMENT '用户名',
                    role VARCHAR(32) NULL COMMENT '角色',
                    school_id INT NULL COMMENT '学校ID',
                    action_type VARCHAR(64) NOT NULL COMMENT '行为类型',
                    module_name VARCHAR(64) NOT NULL COMMENT '模块名称',
                    target_type VARCHAR(64) NULL COMMENT '目标类型',
                    target_id VARCHAR(128) NULL COMMENT '目标ID',
                    request_path VARCHAR(255) NULL COMMENT '请求路径',
                    request_method VARCHAR(16) NULL COMMENT '请求方法',
                    result_status VARCHAR(16) NOT NULL COMMENT 'SUCCESS/FAIL/DENY',
                    message VARCHAR(255) NULL COMMENT '说明信息',
                    ip_address VARCHAR(64) NULL COMMENT 'IP地址',
                    user_agent VARCHAR(255) NULL COMMENT '客户端标识',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    INDEX idx_sys_audit_username (username),
                    INDEX idx_sys_audit_role (role),
                    INDEX idx_sys_audit_action (action_type),
                    INDEX idx_sys_audit_created_at (created_at),
                    INDEX idx_sys_audit_module (module_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='系统审计日志表';
                """
            )
        )


def sync_school_reference(engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sys_school_ref (school_name)
                SELECT DISTINCT school_name
                FROM dim_student
                WHERE school_name IS NOT NULL AND school_name <> ''
                ON DUPLICATE KEY UPDATE school_name = VALUES(school_name)
                """
            )
        )

        for seed in DEMO_ACCOUNT_SEEDS:
            school_name = seed.get("school_name")
            if school_name:
                conn.execute(
                    text(
                        """
                        INSERT INTO sys_school_ref (school_name)
                        VALUES (:school_name)
                        ON DUPLICATE KEY UPDATE school_name = VALUES(school_name)
                        """
                    ),
                    {"school_name": school_name},
                )


def seed_demo_accounts(engine) -> None:
    with engine.begin() as conn:
        for seed in DEMO_ACCOUNT_SEEDS:
            school_id = None
            if seed.get("school_name"):
                school_id = conn.execute(
                    text("SELECT school_id FROM sys_school_ref WHERE school_name = :school_name LIMIT 1"),
                    {"school_name": seed["school_name"]},
                ).scalar()

            existing = conn.execute(
                text("SELECT user_id, password_hash FROM sys_user_account WHERE username = :username LIMIT 1"),
                {"username": seed["username"]},
            ).mappings().first()

            if existing:
                conn.execute(
                    text(
                        """
                        UPDATE sys_user_account
                        SET role = :role,
                            school_id = :school_id,
                            display_name = :display_name,
                            account_status = CASE WHEN account_status = 'disabled' THEN account_status ELSE :account_status END,
                            hash_algo = COALESCE(hash_algo, :hash_algo),
                            hash_version = COALESCE(hash_version, :hash_version),
                            password_hash = CASE WHEN password_hash IS NULL OR password_hash = '' THEN :password_hash ELSE password_hash END
                        WHERE user_id = :user_id
                        """
                    ),
                    {
                        "user_id": existing["user_id"],
                        "role": seed["role"],
                        "school_id": school_id,
                        "display_name": seed["display_name"],
                        "account_status": seed["account_status"],
                        "hash_algo": seed["hash_algo"],
                        "hash_version": seed["hash_version"],
                        "password_hash": seed["password_hash"],
                    },
                )
                continue

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
                        account_status,
                        failed_attempts,
                        lock_until,
                        password_updated_at
                    ) VALUES (
                        :username,
                        :password_hash,
                        :hash_algo,
                        :hash_version,
                        :role,
                        :school_id,
                        :display_name,
                        :account_status,
                        0,
                        NULL,
                        CURRENT_TIMESTAMP
                    )
                    """
                ),
                {
                    "username": seed["username"],
                    "password_hash": seed["password_hash"],
                    "hash_algo": seed["hash_algo"],
                    "hash_version": seed["hash_version"],
                    "role": seed["role"],
                    "school_id": school_id,
                    "display_name": seed["display_name"],
                    "account_status": seed["account_status"],
                },
            )


def bootstrap_security(engine) -> None:
    create_security_tables(engine)
    sync_school_reference(engine)
    seed_demo_accounts(engine)


def record_audit_log(
    engine,
    *,
    user_id: int | None = None,
    username: str | None = None,
    role: str | None = None,
    school_id: int | None = None,
    action_type: str,
    module_name: str,
    target_type: str | None = None,
    target_id: str | None = None,
    request_path: str | None = None,
    request_method: str | None = None,
    result_status: str,
    message: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO sys_audit_log (
                    user_id,
                    username,
                    role,
                    school_id,
                    action_type,
                    module_name,
                    target_type,
                    target_id,
                    request_path,
                    request_method,
                    result_status,
                    message,
                    ip_address,
                    user_agent
                ) VALUES (
                    :user_id,
                    :username,
                    :role,
                    :school_id,
                    :action_type,
                    :module_name,
                    :target_type,
                    :target_id,
                    :request_path,
                    :request_method,
                    :result_status,
                    :message,
                    :ip_address,
                    :user_agent
                )
                """
            ),
            {
                "user_id": user_id,
                "username": sanitize_log_text(username, 64) or None,
                "role": sanitize_log_text(role, 32) or None,
                "school_id": school_id,
                "action_type": sanitize_log_text(action_type, 64),
                "module_name": sanitize_log_text(module_name, 64),
                "target_type": sanitize_log_text(target_type, 64) or None,
                "target_id": sanitize_log_text(target_id, 128) or None,
                "request_path": sanitize_log_text(request_path, 255) or None,
                "request_method": sanitize_log_text(request_method, 16) or None,
                "result_status": sanitize_log_text(result_status, 16),
                "message": sanitize_log_text(message, 255) or None,
                "ip_address": sanitize_log_text(ip_address, 64) or None,
                "user_agent": sanitize_log_text(user_agent, 255) or None,
            },
        )


def is_account_locked(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    lock_until = row.get("lock_until")
    return bool(lock_until and lock_until > datetime.now())


def get_lock_deadline() -> datetime:
    return datetime.now() + timedelta(minutes=LOCK_MINUTES)
