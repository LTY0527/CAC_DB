# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Any

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parent
ROOT = BACKEND_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.init_security import init_default_users  # noqa: E402
from scripts.migrate_schema import ensure_schema  # noqa: E402

AUTH_SECRET = os.getenv("CAC_AUTH_SECRET", "cac-db-platform-auth-secret-v1")
AUTH_SALT = "cac-db-platform-auth"
AUTH_TOKEN_MAX_AGE = 60 * 60 * 24
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15


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
    return text_value if len(text_value) <= max_len else text_value[: max_len - 3] + "..."


def extract_client_ip(flask_request) -> str:
    forwarded_for = sanitize_log_text(flask_request.headers.get("X-Forwarded-For"), max_len=128)
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return sanitize_log_text(flask_request.remote_addr or "", max_len=64)


def bootstrap_security(engine) -> None:
    ensure_schema(verbose=True)
    init_default_users(engine)


def record_audit_log(
    engine,
    *,
    user_id: int | None = None,
    username: str | None = None,
    role: str | None = None,
    school_id: str | None = None,
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
                    user_id, username, role, school_id, action_type, module_name,
                    target_type, target_id, request_path, request_method,
                    result_status, message, ip_address, user_agent,
                    action, module, ip, detail_json
                ) VALUES (
                    :user_id, :username, :role, :school_id, :action_type, :module_name,
                    :target_type, :target_id, :request_path, :request_method,
                    :result_status, :message, :ip_address, :user_agent,
                    :action_type, :module_name, :ip_address, NULL
                )
                """
            ),
            {
                "user_id": user_id,
                "username": sanitize_log_text(username, 64) or None,
                "role": sanitize_log_text(role, 32) or None,
                "school_id": sanitize_log_text(school_id, 32) or None,
                "action_type": sanitize_log_text(action_type, 64),
                "module_name": sanitize_log_text(module_name, 100),
                "target_type": sanitize_log_text(target_type, 64) or None,
                "target_id": sanitize_log_text(target_id, 128) or None,
                "request_path": sanitize_log_text(request_path, 255) or None,
                "request_method": sanitize_log_text(request_method, 16) or None,
                "result_status": sanitize_log_text(result_status, 20),
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
