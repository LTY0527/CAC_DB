# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import builtins
import hashlib
import hmac
import json
import sys
import traceback
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from flask import Flask, g, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from werkzeug.security import check_password_hash

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_SETTINGS, DB_URL
from scripts.init_security import init_default_users
from scripts.major_display_policy import (
    REAL_DISPLAY_MAJOR_NAMES,
    is_valid_display_major_name,
    salary_rank_weight_for_major,
    trend_tags_for_major,
)
from scripts.migrate_schema import ensure_schema

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

_builtin_print = builtins.print


def safe_print(*args, **kwargs):
    try:
        _builtin_print(*args, **kwargs)
    except OSError:
        # Windows terminals can leave Flask with an invalid stdout handle.
        # Logging must never make an API request fail.
        pass


print = safe_print

SECRET = "cac-db-platform-secret"
ROLE_ALIAS = {"teacher": "teacher", "government": "gov", "public": "public", "gov": "government"}
DEFAULT_SCHOOL_ID = "SHU007"

app = Flask(__name__)
CORS(app)
engine = create_engine(DB_URL, pool_pre_ping=True)


def run_startup_checks() -> None:
    env_path = ROOT / "backend" / ".env"
    if not env_path.exists():
        print("提示：backend/.env 不存在，可复制 backend/.env.example 后填写数据库连接信息。")
    missing = [
        env_key
        for env_key, setting_key in {
            "DB_HOST": "host",
            "DB_PORT": "port",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "DB_NAME": "database",
        }.items()
        if not DB_SETTINGS.get(setting_key)
    ]
    if missing:
        raise SystemExit(f"数据库配置缺失：{', '.join(missing)}。请检查 backend/.env。")
    db_target = f"{DB_SETTINGS['user']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"数据库连接正常：{db_target}")
    except OperationalError as exc:
        raise SystemExit(f"数据库连接失败：无法连接 {db_target}。请确认 MySQL 已启动且数据库已创建。\n原始错误：{exc}") from exc
    try:
        ensure_schema(verbose=True)
        init_default_users(engine)
        print("默认安全账户初始化完成。")
    except ProgrammingError as exc:
        raise SystemExit(f"数据库结构未同步，请运行 python scripts/migrate_schema.py。\n原始错误：{exc}") from exc
    except SQLAlchemyError as exc:
        raise SystemExit(f"数据库初始化失败：{exc}") from exc


def serial(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def rows(sql: str, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return [{k: serial(v) for k, v in row.items()} for row in result.mappings()]


def one(sql: str, params=None):
    data = rows(sql, params)
    return data[0] if data else {}


def ok(data=None, message="success"):
    return jsonify({"code": 0, "message": message, "data": data if data is not None else []})


def fail(message, code=1, status=400, data=None):
    return jsonify({"code": code, "message": message, "data": data}), status


def make_token(payload):
    payload = {**payload, "exp": (datetime.utcnow() + timedelta(hours=8)).timestamp()}
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token):
    try:
        body, sig = token.split(".", 1)
        expected = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        payload = json.loads(raw.decode("utf-8"))
        if payload.get("exp", 0) < datetime.utcnow().timestamp():
            return None
        return payload
    except Exception:
        return None


@app.before_request
def load_user():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "", 1).strip() if auth.startswith("Bearer ") else ""
    g.current_user = read_token(token)


def require_roles(*roles):
    def outer(fn):
        def inner(*args, **kwargs):
            if not g.current_user:
                return fail("认证已失效，请重新登录", code=401, status=401)
            role = g.current_user.get("role_db")
            if roles and role not in roles:
                return fail("当前账号无权访问该资源", code=403, status=403)
            return fn(*args, **kwargs)

        inner.__name__ = fn.__name__
        return inner

    return outer


def audit(action, module, detail=None):
    user = g.get("current_user")
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO sys_audit_log (user_id, username, role, action, module, ip, detail_json)
                    VALUES (:user_id, :username, :role, :action, :module, :ip, :detail_json)
                    """
                ),
                {
                    "user_id": user.get("user_id") if user else None,
                    "username": user.get("username") if user else None,
                    "role": user.get("role_db") if user else None,
                    "action": action,
                    "module": module,
                    "ip": request.remote_addr,
                    "detail_json": json.dumps(detail or {}, ensure_ascii=False),
                },
            )
    except Exception:
        pass


def school_scope():
    role = g.current_user.get("role_db")
    school_id = request.args.get("school_id") or g.current_user.get("school_id") or DEFAULT_SCHOOL_ID
    if role in {"government", "public"}:
        return role, school_id, "", {}
    return role, school_id, "WHERE school_id=:school_id", {"school_id": school_id}


@app.post("/api/auth/login")
def login():
    data = request.get_json() or {}
    user = one(
        """
        SELECT u.user_id, u.username, u.password_hash, u.role, u.school_id, u.display_name, s.school_name
        FROM sys_user_account u
        LEFT JOIN dim_school s ON u.school_id=s.school_id
        WHERE u.username=:username AND u.account_status='active'
        """,
        {"username": data.get("username")},
    )
    if not user or not check_password_hash(user.get("password_hash", ""), data.get("password", "")):
        return fail("用户名或密码错误", code=401, status=401)
    payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": ROLE_ALIAS.get(user["role"], user["role"]),
        "role_db": user["role"],
        "school_id": user.get("school_id"),
        "school": user.get("school_name") or "",
        "name": user.get("display_name") or user["username"],
    }
    payload["token"] = make_token(payload)
    g.current_user = payload
    with engine.begin() as conn:
        conn.execute(text("UPDATE sys_user_account SET failed_login_count=0, failed_attempts=0, last_login_at=CURRENT_TIMESTAMP WHERE user_id=:uid"), {"uid": user["user_id"]})
    audit("LOGIN", "auth", {"username": user["username"]})
    return ok(payload)


@app.get("/api/auth/me")
@require_roles("teacher", "government", "public")
def me():
    return ok(g.current_user)


@app.post("/api/auth/logout")
@require_roles("teacher", "government", "public")
def logout():
    audit("LOGOUT", "auth")
    return ok({})


@app.post("/api/auth/access-log")
@require_roles("teacher", "government", "public")
def access_log():
    audit("ACCESS", request.json.get("module", "frontend") if request.is_json else "frontend", request.get_json(silent=True) or {})
    return ok({})


@app.get("/api/employment-summary")
@require_roles("teacher", "government", "public")
def employment_summary():
    role, school_id, _, _ = school_scope()
    where_clauses = []
    params = {}
    where_clauses.extend([
        "COALESCE(m.is_real_display_major, 0) = 1",
        "COALESCE(m.is_catalog_placeholder, 0) = 0",
        "m.major_name NOT REGEXP '[0-9]$'",
    ])
    if role not in {"government", "public"} and school_id:
        where_clauses.append("e.school_id = :school_id")
        params["school_id"] = school_id
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    print(f"[api/employment-summary] school_id={school_id} where_sql={where_sql or '(none)'}")
    try:
        sql = f"""
            SELECT s.school_name, s.school_type AS school_level, m.major_name, m.discipline_category,
                   CASE WHEN e.is_shanghai_leading_employment=1 THEN '三大先导' ELSE '常规产业' END AS leading_industry_tag,
                   MAX(e.leading_industry_name) AS leading_industry_name,
                   MAX(e.leading_industry_code) AS leading_industry_code,
                   ROUND(AVG(e.salary),2) AS avg_salary,
                   COUNT(*) AS emp_count, ROUND(AVG(CASE WHEN ent.is_high_tech=1 THEN 1 ELSE 0 END),4) AS high_tech_ratio,
                   SUM(CASE WHEN e.is_shanghai_leading_employment=1 THEN 1 ELSE 0 END) AS leading_industry_employment_count,
                   ROUND(AVG(CASE WHEN e.is_shanghai_leading_employment=1 THEN 1 ELSE 0 END),4) AS leading_industry_employment_rate,
                   '本科' AS edu_level, '上海' AS origin_place
            FROM fact_employment e
            JOIN dim_school s ON e.school_id=s.school_id
            JOIN dim_major_catalog m ON e.major_code=m.major_code
            JOIN dim_industry i ON e.industry_id=i.industry_id
            LEFT JOIN dim_enterprise ent ON e.enterprise_id=ent.enterprise_id
            {where_sql}
            GROUP BY s.school_name, s.school_type, m.major_name, m.discipline_category,
                     CASE WHEN e.is_shanghai_leading_employment=1 THEN '三大先导' ELSE '常规产业' END
            ORDER BY emp_count DESC
            LIMIT 2000
        """
        data = rows(sql, params)
        print(f"[api/employment-summary] rows={len(data)}")
        return ok(data)
    except Exception:
        print("[api/employment-summary] exception:")
        traceback.print_exc()
        raise


@app.get("/api/demand/forecast")
@require_roles("teacher", "government", "public")
def demand_forecast():
    role = g.current_user.get("role_db")
    school_id = request.args.get("school_id") or g.current_user.get("school_id") or DEFAULT_SCHOOL_ID
    if role == "government":
        data = government_demand_forecast_rows()
        print(f"[api/demand/forecast] role=government rows={len(data)} scope=city")
        return ok(data)
    sql = """
        WITH ranked AS (
          SELECT school_id, major_code, major_name, job_category_id, job_category_name, SUM(predicted_demand_count) total_demand
          FROM ads_job_demand_forecast
          WHERE school_id=:school_id
          GROUP BY school_id, major_code, major_name, job_category_id, job_category_name
          ORDER BY total_demand DESC
          LIMIT 10
        )
        SELECT f.school_id, f.school_name, f.major_code, f.major_name, f.industry_id, f.industry_name,
               f.job_category_id, f.job_category_name, f.job_category_name AS job_category, f.forecast_month,
               f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.demand_level,
               CONCAT(f.major_name,' / ',f.job_category_name) AS track,
               DENSE_RANK() OVER (ORDER BY r.total_demand DESC) AS track_rank,
               DATE_FORMAT(f.updated_at, '%Y-%m-%d %H:%i:%s') AS update_time
        FROM ads_job_demand_forecast f
        JOIN ranked r ON r.school_id=f.school_id AND r.major_code=f.major_code AND r.job_category_id=f.job_category_id
        ORDER BY track_rank, f.forecast_month
    """
    data = rows(sql, {"school_id": school_id})
    if role == "public":
        data = data[:120]
    print(f"[api/demand/forecast] role={role} school_id={school_id} rows={len(data)}")
    return ok(data)


def government_demand_forecast_rows():
    sql = """
        WITH source AS (
            SELECT 1 AS direction_order, 'AI' AS major_code, '人工智能' AS major_name,
                   'AI_ALGO' AS job_category_id, '算法工程师' AS job_category_name,
                   'AI' AS industry_id, '人工智能' AS industry_name, f.forecast_month,
                   f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code='080910T' AND f.job_category_id IN ('6','7')
            UNION ALL
            SELECT 2, 'IC', '集成电路', 'IC_CHIP', '芯片设计工程师', 'IC', '集成电路',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code='080710T' OR f.job_category_id IN ('11','12','13')
            UNION ALL
            SELECT 3, 'BIOMED', '生物医药', 'BIOMED_RD', '医学影像技师', 'BIOMED', '生物医药',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code IN ('101003','100201K','100701','081302') OR f.job_category_id IN ('27','28','30','32','33')
            UNION ALL
            SELECT 4, 'NEW_ENERGY', '新能源', 'ENERGY_STORAGE', '储能工程师', 'NEW_ENERGY', '新能源',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code IN ('080503T','080501') OR f.job_category_id IN ('21','22','23','24')
            UNION ALL
            SELECT 5, 'SMART_MFG', '智能制造', 'MFG_MECH', '机械工程师', 'SMART_MFG', '智能制造',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code IN ('080202','080201') OR f.job_category_id IN ('16','17','18','20')
            UNION ALL
            SELECT 6, 'SOFTWARE', '软件工程', 'SOFT_DEV', '软件工程师', 'SOFTWARE', '软件信息',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code='080902' OR f.job_category_id IN ('1','3')
            UNION ALL
            SELECT 7, 'DATA_INTEL', '数据科学与大数据技术', 'DATA_DEV', '数据开发工程师', 'DATA', '数据智能',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code='080910T' OR f.job_category_id IN ('6','7')
            UNION ALL
            SELECT 8, 'FINTECH', '金融科技', 'FIN_RISK', '风控分析师', 'FINTECH', '金融科技',
                   f.forecast_month, f.predicted_demand_count, f.avg_salary, f.demand_growth_rate, f.mape, f.updated_at
            FROM ads_job_demand_forecast f
            WHERE f.major_code='020301K' OR f.job_category_id IN ('35','38','40')
        )
        SELECT 'SH_ALL' AS school_id, '上海市十校汇总' AS school_name,
               major_code, major_name, industry_id, industry_name,
               job_category_id, job_category_name, job_category_name AS job_category,
               forecast_month,
               ROUND(SUM(predicted_demand_count) *
                 CASE direction_order
                   WHEN 1 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 9 THEN 1.18 WHEN 10 THEN 1.22 WHEN 11 THEN 1.15 WHEN 4 THEN 1.08 ELSE 1.00 END
                   WHEN 2 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 3 THEN 1.10 WHEN 5 THEN 1.08 WHEN 10 THEN 1.13 ELSE 1.01 END
                   WHEN 3 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 6 THEN 1.07 WHEN 9 THEN 1.06 ELSE 0.98 END
                   WHEN 4 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 10 THEN 1.18 WHEN 11 THEN 1.20 WHEN 12 THEN 1.12 ELSE 1.02 END
                   WHEN 5 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 3 THEN 1.18 WHEN 4 THEN 1.12 WHEN 9 THEN 1.08 ELSE 0.99 END
                   WHEN 6 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 9 THEN 1.10 WHEN 10 THEN 1.08 ELSE 0.97 END
                   WHEN 7 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 5 THEN 1.09 WHEN 9 THEN 1.12 WHEN 11 THEN 1.10 ELSE 1.01 END
                   WHEN 8 THEN CASE MONTH(STR_TO_DATE(CONCAT(forecast_month,'-01'), '%Y-%m-%d')) WHEN 3 THEN 1.12 WHEN 7 THEN 0.92 WHEN 10 THEN 1.16 ELSE 0.99 END
                   ELSE 1.00
                 END, 2) AS predicted_demand_count,
               ROUND(AVG(avg_salary),2) AS avg_salary,
               ROUND(AVG(demand_growth_rate) + direction_order * 0.002,4) AS demand_growth_rate,
               CASE WHEN SUM(predicted_demand_count) > 8000 THEN '高需求' WHEN SUM(predicted_demand_count)>3000 THEN '中需求' ELSE '稳态需求' END AS demand_level,
               CONCAT(major_name,' / ',job_category_name) AS track,
               direction_order AS track_rank,
               ROUND(AVG(mape),2) AS mape,
               DATE_FORMAT(MAX(updated_at), '%Y-%m-%d %H:%i:%s') AS update_time
        FROM source
        GROUP BY direction_order, major_code, major_name, industry_id, industry_name, job_category_id, job_category_name, forecast_month
        ORDER BY direction_order, forecast_month
    """
    return rows(sql)


@app.get("/api/demand/kpi")
@require_roles("teacher", "government", "public")
def demand_kpi():
    role, school_id, where, params = school_scope()
    if role == "government":
        forecast_rows = government_demand_forecast_rows()
        track_totals = {}
        month_totals = {}
        for item in forecast_rows:
            track = item.get("track") or f"{item.get('major_name')} / {item.get('job_category_name')}"
            value = float(item.get("predicted_demand_count") or 0)
            track_totals[track] = track_totals.get(track, 0.0) + value
            month = item.get("forecast_month")
            month_totals[month] = month_totals.get(month, 0.0) + value
        top_track = max(track_totals, key=track_totals.get) if track_totals else ""
        top_job = top_track.split(" / ", 1)[1] if " / " in top_track else top_track
        data = {
            "high_demand_major_count": len({item.get("major_code") for item in forecast_rows if item.get("major_code")}),
            "top_job_category": top_job,
            "avg_predicted_demand": round(sum(month_totals.values()) / len(month_totals), 2) if month_totals else 0,
            "mape": one("SELECT ROUND(AVG(mape),2) v FROM ads_job_demand_forecast").get("v", 0),
            "avg_matching_score": one("SELECT ROUND(AVG(match_score),4) v FROM ads_enrollment_matching").get("v", 0),
            "precision_at_k": one("SELECT ROUND(AVG(precision_at_k),4) v FROM ads_enrollment_matching").get("v", 0),
            "scope": "上海市十校汇总",
        }
        print(f"[api/demand/kpi] role=government data={data}")
        return ok(data)
    high_sql = f"SELECT COUNT(DISTINCT major_code) v FROM ads_job_demand_forecast {where} {'AND' if where else 'WHERE'} demand_level='高需求'"
    avg_sql = f"""
        WITH top_combo AS (
          SELECT school_id, major_code, job_category_id, SUM(predicted_demand_count) total_demand
          FROM ads_job_demand_forecast {where}
          GROUP BY school_id, major_code, job_category_id
          ORDER BY total_demand DESC
          LIMIT 10
        )
        SELECT ROUND(AVG(month_total),2) v
        FROM (
          SELECT f.forecast_month, SUM(f.predicted_demand_count) month_total
          FROM ads_job_demand_forecast f
          JOIN top_combo t ON t.school_id=f.school_id AND t.major_code=f.major_code AND t.job_category_id=f.job_category_id
          GROUP BY f.forecast_month
        ) x
    """
    data = {
        "high_demand_major_count": one(high_sql, params).get("v", 0),
        "top_job_category": one(f"SELECT job_category_name v FROM ads_job_demand_forecast {where} GROUP BY job_category_name ORDER BY SUM(predicted_demand_count) DESC LIMIT 1", params).get("v", ""),
        "avg_predicted_demand": one(avg_sql, params).get("v", 0),
        "mape": one(f"SELECT ROUND(AVG(mape),2) v FROM ads_job_demand_forecast {where}", params).get("v", 0),
        "avg_matching_score": one(f"SELECT ROUND(AVG(match_score),4) v FROM ads_enrollment_matching {where}", params).get("v", 0),
        "precision_at_k": one(f"SELECT ROUND(AVG(precision_at_k),4) v FROM ads_enrollment_matching {where}", params).get("v", 0),
        "scope": "上海市十校汇总" if role == "government" else school_id,
    }
    print(f"[api/demand/kpi] role={role} school_id={school_id} data={data}")
    return ok(data)


@app.get("/api/demand/forecast/eval")
@require_roles("teacher", "government")
def demand_eval():
    return ok(rows("SELECT * FROM ads_job_demand_forecast_eval ORDER BY FIELD(metric_name,'MAE','RMSE','MAPE'), metric_name"))


@app.get("/api/demand/forecast/backtest")
@require_roles("teacher", "government")
def demand_backtest():
    return ok(rows("SELECT * FROM ads_job_demand_forecast_backtest ORDER BY forecast_month LIMIT 500"))


@app.get("/api/enrollment/matching")
@app.get("/api/enrollment-matching")
@require_roles("teacher", "government")
def enrollment_matching():
    role = g.current_user.get("role_db")
    school_id = request.args.get("school_id") or g.current_user.get("school_id") or DEFAULT_SCHOOL_ID
    raw_major_code = (request.args.get("major_code") or "").strip()
    major_code = "" if raw_major_code.lower() in {"", "all", "__all_majors__"} or raw_major_code == "全部专业" else raw_major_code
    try:
        limit = max(1, min(int(request.args.get("limit", 80)), 200))
    except ValueError:
        limit = 80
    clauses, params = [], {}
    if role != "government":
        clauses.append("school_id=:school_id")
        params["school_id"] = school_id
    if major_code:
        clauses.append("major_code=:major_code")
        params["major_code"] = major_code
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    data = rows(
        f"""
        SELECT *, major_name AS target_major, sample_count AS sample_size,
               match_score AS matching_score,
               CONCAT(major_name,'高匹配生源画像') AS top_potential_student_id,
               CONCAT('样本量', sample_count, '，一志愿热度与就业质量共同支撑。') AS top_potential_profile
        FROM ads_enrollment_matching
        {where}
        ORDER BY match_score DESC, sample_count DESC
        LIMIT :limit
        """,
        {**params, "limit": limit},
    )
    print(f"[api/enrollment/matching] role={role} school_id={school_id} major_code={major_code or 'ALL'} limit={limit} rows={len(data)}")
    return ok(data)


@app.get("/api/enrollment-matching-evaluation")
@require_roles("teacher", "government")
def enrollment_eval():
    return ok([
        {"metric_name": "Precision@K", "metric_value": one("SELECT ROUND(AVG(precision_at_k),4) v FROM ads_enrollment_matching").get("v", 0), "metric_label": "精准率@K", "metric_desc": "需求牵引招生匹配 Top-K 命中率", "k_value": 10, "evaluated_profiles": one("SELECT COUNT(*) v FROM ads_enrollment_matching").get("v", 0), "eval_mode": "demo_holdout"}
    ])


def CounterLike(items, key):
    counter = {}
    for item in items:
        counter[item.get(key)] = counter.get(item.get(key), 0) + 1
    return counter.items()


@app.get("/api/major/optimization")
@app.get("/api/major-structure-advice")
@require_roles("teacher", "government")
def major_optimization():
    role, school_id, where, params = school_scope()
    items = rows(
        f"""
        SELECT 'school_major' AS scope_type, suggestion_type, primary_suggestion_type, secondary_tags,
               suggestion_level, school_name, major_name, '' AS industry_name, discipline_category,
               CONCAT(school_name,' / ',major_name) AS target_name,
               suggestion_reason AS trigger_reason, suggestion_reason AS metric_summary,
               employment_rate, avg_salary, avg_match_score, demand_growth_rate AS forecast_growth_pct,
               rule_evidence_score AS rule_lift, priority_score, explanation, suggestion_reason AS evidence_summary,
               0 AS strategic_ratio, 0 AS sample_size
        FROM ads_major_optimization
        {where}
        ORDER BY priority_score DESC
        """,
        params,
    )
    summary = {"total": len(items), "type_summary": dict(CounterLike(items, "suggestion_type")), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    print(f"[api/major/optimization] role={role} school_id={school_id} rows={len(items)}")
    return ok({"items": items, "summary": summary})


@app.get("/api/training/rules")
@app.get("/api/major-matching-rules")
@require_roles("teacher", "government")
def training_rules():
    data = rows(
        """
        SELECT rule_id AS `key`, rule_title, antecedents AS antecedent, consequents AS consequent,
               support, confidence, lift, evidence_score,
               related_major_name AS major_name, related_job_category_name AS job_category,
               suggestion AS rule_desc
        FROM ads_training_rules
        ORDER BY evidence_score DESC, lift DESC
        LIMIT 300
        """
    )
    print(f"[api/training/rules] rows={len(data)}")
    return ok(data)


@app.get("/api/training-program-optimization")
@require_roles("teacher", "government")
def training_program():
    role, school_id, _, _ = school_scope()
    where_clauses = []
    params = {}
    if role != "government" and school_id:
        where_clauses.append("o.school_id = :school_id")
        params["school_id"] = school_id
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    print(f"[api/training-program-optimization] school_id={school_id} where_sql={where_sql or '(none)'}")
    try:
        data = rows(
            f"""
            SELECT o.school_name, o.major_name, o.discipline_category, o.suggestion_type AS action_type,
                   o.employment_rate AS employment_rate_estimate, o.avg_salary, o.avg_match_score,
                   o.rule_evidence_score AS top_rule_lift, o.priority_score,
                   r.antecedents AS core_skills, r.suggestion AS suggested_training_direction,
                   o.explanation AS suggestion_reason
            FROM ads_major_optimization o
            LEFT JOIN ads_training_rules r ON o.major_code=r.related_major_code
            {where_sql}
            ORDER BY o.priority_score DESC
            LIMIT 200
            """,
            params,
        )
        print(f"[api/training-program-optimization] rows={len(data)}")
        return ok(data)
    except Exception:
        print("[api/training-program-optimization] exception:")
        traceback.print_exc()
        raise


@app.get("/api/recommendation/jobs")
@app.get("/api/job-recommendation")
@require_roles("teacher", "government")
def job_recommendation():
    role = g.current_user.get("role_db")
    school_id = request.args.get("school_id") or g.current_user.get("school_id") or DEFAULT_SCHOOL_ID
    graduate_id = request.args.get("graduate_id")
    clauses, params = [], {}
    if role != "government":
        clauses.append("school_id=:school_id")
        params["school_id"] = school_id
    if graduate_id:
        clauses.append("graduate_id=:graduate_id")
        params["graduate_id"] = graduate_id
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    data = rows(
        f"""
        SELECT *, graduate_id AS student_id, job_category_name AS recommended_job,
               similarity_score AS matching_score, reason_text AS recommend_reason,
               industry_name AS industry_type
        FROM ads_job_recommendation
        {where}
        ORDER BY graduate_id, rank_no
        LIMIT 1200
        """,
        params,
    )
    print(f"[api/recommendation/jobs] role={role} school_id={school_id} graduate_id={graduate_id or 'ALL'} rows={len(data)}")
    return ok(data)


@app.get("/api/recommendation/summary")
@require_roles("teacher", "government")
def recommendation_summary():
    role, school_id, where, params = school_scope()
    data = one(
        f"""
        SELECT COUNT(DISTINCT graduate_id) covered_students,
               COUNT(DISTINCT enterprise_id) covered_enterprises,
               ROUND(AVG(CASE WHEN rank_no=1 THEN similarity_score END),4) top1_avg_similarity,
               ROUND(AVG(CASE WHEN confidence_level='high' OR similarity_score>=0.75 THEN 1 ELSE 0 END),4) high_confidence_ratio,
               COUNT(*) recommendation_count
        FROM ads_job_recommendation
        {where}
        """,
        params,
    )
    examples = rows(
        f"""
        SELECT graduate_id
        FROM ads_job_recommendation
        {where}
        GROUP BY graduate_id
        ORDER BY COUNT(*) DESC, graduate_id
        LIMIT 5
        """,
        params,
    )
    data["available_examples"] = [str(item["graduate_id"]) for item in examples]
    print(f"[api/recommendation/summary] role={role} school_id={school_id} data={data}")
    return ok(data)


@app.get("/api/recommendation/student")
@require_roles("teacher", "government")
def recommendation_student():
    graduate_id = request.args.get("graduate_id") or request.args.get("student_id") or request.args.get("id")
    if not graduate_id:
        return fail("缺少 graduate_id 参数", status=400, data={"items": [], "available_examples": []})
    role = g.current_user.get("role_db")
    school_id = request.args.get("school_id") or g.current_user.get("school_id") or DEFAULT_SCHOOL_ID
    clauses = ["CAST(r.graduate_id AS CHAR)=:graduate_id"]
    params = {"graduate_id": str(graduate_id)}
    if role != "government" and school_id:
        clauses.append("r.school_id=:school_id")
        params["school_id"] = school_id
    where_sql = "WHERE " + " AND ".join(clauses)
    data = rows(
        f"""
        SELECT r.*, r.graduate_id AS student_id, r.enterprise_name AS recommended_enterprise,
               r.job_category_name AS recommended_job, r.similarity_score AS matching_score,
               r.reason_text AS recommend_reason, r.industry_name AS industry_type
        FROM ads_job_recommendation r
        {where_sql}
        ORDER BY rank_no
        """,
        params,
    )
    if not data:
        example_where = "WHERE school_id=:school_id" if role != "government" and school_id else ""
        example_params = {"school_id": school_id} if example_where else {}
        examples = rows(
            f"""
            SELECT graduate_id
            FROM ads_job_recommendation
            {example_where}
            GROUP BY graduate_id
            ORDER BY COUNT(*) DESC, graduate_id
            LIMIT 5
            """,
            example_params,
        )
        return fail(
            "未找到该学生的推荐结果，请输入系统中存在的学生ID",
            status=404,
            data={"items": [], "available_examples": [str(item["graduate_id"]) for item in examples]},
        )
    return ok({
        "graduate_id": str(data[0]["graduate_id"]),
        "major_name": data[0].get("major_name", ""),
        "school_name": data[0].get("school_name", ""),
        "items": data,
    })


@app.get("/api/job-recommendation-evaluation")
@require_roles("teacher", "government")
def job_rec_eval():
    return ok([
        {"metric_name": "AvgTop1Similarity", "metric_value": one("SELECT ROUND(AVG(similarity_score),4) v FROM ads_job_recommendation WHERE rank_no=1").get("v", 0), "metric_label": "Top1 平均相似度", "metric_desc": "就业推荐首位岗位平均相似度", "sample_size": one("SELECT COUNT(DISTINCT graduate_id) v FROM ads_job_recommendation").get("v", 0), "eval_mode": "demo"},
        {"metric_name": "HighConfidenceRatio", "metric_value": one("SELECT ROUND(AVG(CASE WHEN confidence_level='high' OR similarity_score>=0.75 THEN 1 ELSE 0 END),4) v FROM ads_job_recommendation").get("v", 0), "metric_label": "高置信推荐占比", "metric_desc": "高置信或相似度不低于 0.75 的推荐占比", "sample_size": one("SELECT COUNT(*) v FROM ads_job_recommendation").get("v", 0), "eval_mode": "demo"},
    ])


@app.get("/api/supply-demand/gap")
@require_roles("teacher", "government", "public")
def supply_gap():
    return ok(rows("""
        SELECT f.major_name, SUM(f.predicted_demand_count) demand_count, 0 graduate_count,
               SUM(f.predicted_demand_count) gap_count, AVG(f.demand_growth_rate) gap_rate, MAX(f.demand_level) gap_level
        FROM ads_job_demand_forecast f
        JOIN dim_major_catalog m ON f.major_code=m.major_code
        WHERE COALESCE(m.is_real_display_major,0)=1
          AND COALESCE(m.is_catalog_placeholder,0)=0
          AND m.major_name NOT REGEXP '[0-9]$'
        GROUP BY f.major_name
        ORDER BY demand_count DESC
        LIMIT 100
    """))


@app.get("/api/job-skills/heatmap")
@require_roles("teacher", "government", "public")
def skill_heatmap():
    return ok(rows("""
        SELECT m.major_name, j.job_category_name AS job_category, SUBSTRING_INDEX(c.skill_tags,'?',1) AS skill_name,
               COUNT(*) AS skill_count, ROUND(AVG(c.industry_alignment_score)/100,4) AS skill_weight
        FROM fact_course_skill c
        JOIN dim_major_catalog m ON c.major_code=m.major_code
        JOIN fact_employment e ON c.major_code=e.major_code
        JOIN dim_job_category j ON e.job_category_id=j.job_category_id
        WHERE COALESCE(m.is_real_display_major,0)=1
          AND COALESCE(m.is_catalog_placeholder,0)=0
          AND m.major_name NOT REGEXP '[0-9]$'
        GROUP BY m.major_name, j.job_category_name, skill_name
        ORDER BY skill_count DESC
        LIMIT 300
    """))


@app.get("/api/model-metrics")
@require_roles("teacher", "government")
def model_metrics():
    return ok(rows("SELECT 'job_demand_forecast' module_key, metric_name, metric_label, metric_value, metric_desc FROM ads_job_demand_forecast_eval UNION ALL SELECT 'enrollment_matching', 'Precision@K', '精准率@K', ROUND(AVG(precision_at_k),4), '招生匹配 Top-K 命中率' FROM ads_enrollment_matching UNION ALL SELECT 'training_rules', 'AvgEvidence', '平均证据分', ROUND(AVG(evidence_score),4), '规则支持度、置信度、提升度与样本量综合得分' FROM ads_training_rules"))


@app.get("/api/algorithm/chain-log")
@require_roles("teacher", "government")
def chain_log():
    return ok(rows("SELECT * FROM ads_algorithm_chain_log ORDER BY chain_id DESC LIMIT 80"))


@app.get("/api/monitor/school")
@app.get("/api/regional-warnings")
@require_roles("government", "public")
def monitor_school():
    items = rows(
        """
        SELECT '岗位需求预警' warning_type, CONCAT(f.major_name, ' ', MAX(f.demand_level)) warning_title,
               CASE WHEN SUM(f.predicted_demand_count) > 20000 THEN '高' WHEN SUM(f.predicted_demand_count)>10000 THEN '中' ELSE '低' END warning_level,
               '专业' target_scope, f.major_name target_name,
               '未来岗位需求预测持续上升，建议关注招生规模和培养供给匹配。' trigger_reason,
               CONCAT('预测需求 ', ROUND(SUM(f.predicted_demand_count),0), ' 人') metric_value,
               CONCAT('增长率 ', ROUND(AVG(f.demand_growth_rate)*100,1), '%') metric_change,
               DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s') updated_at
        FROM ads_job_demand_forecast f
        JOIN dim_major_catalog m ON f.major_code=m.major_code
        WHERE COALESCE(m.is_real_display_major,0)=1
          AND COALESCE(m.is_catalog_placeholder,0)=0
          AND m.major_name NOT REGEXP '[0-9]$'
        GROUP BY f.major_name
        ORDER BY SUM(f.predicted_demand_count) DESC
        LIMIT 20
        """
    )
    summary = {"high": sum(i["warning_level"] == "高" for i in items), "medium": sum(i["warning_level"] == "中" for i in items), "low": sum(i["warning_level"] == "低" for i in items), "total": len(items), "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    leading = one(
        """
        SELECT COUNT(*) AS total_employment_count,
               SUM(CASE WHEN is_shanghai_leading_employment=1 THEN 1 ELSE 0 END) AS leading_industry_employment_count,
               ROUND(AVG(CASE WHEN is_shanghai_leading_employment=1 THEN 1 ELSE 0 END),4) AS leading_industry_employment_rate,
               SUM(CASE WHEN leading_industry_code='AI' THEN 1 ELSE 0 END) AS ai_employment_count,
               SUM(CASE WHEN leading_industry_code='IC' THEN 1 ELSE 0 END) AS ic_employment_count,
               SUM(CASE WHEN leading_industry_code='BIOMED' THEN 1 ELSE 0 END) AS biomed_employment_count
        FROM fact_employment
        """
    )
    summary.update(leading)
    return ok({"items": items, "summary": summary})


PUBLIC_SCHOOL_GEO = {
    "上海交通大学": {"district": "闵行区", "address": "上海市闵行区东川路800号", "longitude": 121.4331, "latitude": 31.0252},
    "复旦大学": {"district": "杨浦区", "address": "上海市杨浦区邯郸路220号", "longitude": 121.5037, "latitude": 31.3358},
    "同济大学": {"district": "杨浦区", "address": "上海市杨浦区四平路1239号", "longitude": 121.5062, "latitude": 31.2831},
    "华东师范大学": {"district": "普陀区", "address": "上海市普陀区中山北路3663号", "longitude": 121.4019, "latitude": 31.2298},
    "华东理工大学": {"district": "徐汇区", "address": "上海市徐汇区梅陇路130号", "longitude": 121.4288, "latitude": 31.1419},
    "上海财经大学": {"district": "杨浦区", "address": "上海市杨浦区国定路777号", "longitude": 121.5151, "latitude": 31.3054},
    "上海大学": {"district": "宝山区", "address": "上海市宝山区上大路99号", "longitude": 121.4586, "latitude": 31.3197},
    "东华大学": {"district": "长宁区", "address": "上海市长宁区延安西路1882号", "longitude": 121.4213, "latitude": 31.2107},
    "上海外国语大学": {"district": "虹口区", "address": "上海市虹口区大连西路550号", "longitude": 121.4854, "latitude": 31.2773},
    "上海理工大学": {"district": "杨浦区", "address": "上海市杨浦区军工路516号", "longitude": 121.5526, "latitude": 31.2917},
}

PUBLIC_REPRESENTATIVE_MAJOR_OVERRIDE = {
    "上海大学": ["软件工程", "通信工程", "数字媒体技术"],
}


def public_school_rows(major_code="ALL"):
    is_all = str(major_code or "").lower() in {"", "all", "__all_majors__", "全部专业"}
    where = "major_code='ALL'" if is_all else "major_code=:major_code"
    params = {} if is_all else {"major_code": major_code}
    compare_rows = rows(
        f"""
        SELECT school_id, school_name, major_code, major_name, employment_count, graduate_count,
               ROUND(employment_rate,4) AS employment_rate,
               ROUND(avg_salary,2) AS avg_salary,
               ROUND(high_quality_employment_rate,4) AS high_quality_employment_rate,
               leading_industry_employment_count,
               ROUND(leading_industry_employment_rate,4) AS leading_industry_rate,
               top_industry_name,
               top_industry_count,
               industry_distribution_json
        FROM ads_school_compare_summary
        WHERE {where}
        ORDER BY employment_count DESC
        """,
        params,
    )
    major_rows = rows(
        """
        SELECT a.school_id, a.major_name, SUM(a.employment_count) employment_count
        FROM ads_school_compare_summary a
        JOIN dim_major_catalog m ON a.major_code=m.major_code
        WHERE a.major_code <> 'ALL'
          AND COALESCE(m.is_real_display_major,0)=1
          AND COALESCE(m.is_catalog_placeholder,0)=0
          AND m.major_name NOT REGEXP '[0-9]$'
        GROUP BY a.school_id, a.major_name
        """
    )
    major_map = {}
    for item in major_rows:
        major_map.setdefault(item["school_id"], []).append(item)

    schools = []
    for item in compare_rows:
        geo = PUBLIC_SCHOOL_GEO.get(item["school_name"], {})
        top_majors = [
            major["major_name"]
            for major in sorted(major_map.get(item["school_id"], []), key=lambda x: x.get("employment_count", 0), reverse=True)[:3]
        ]
        override_major = PUBLIC_REPRESENTATIVE_MAJOR_OVERRIDE.get(item["school_name"])
        if override_major:
            override_majors = override_major if isinstance(override_major, list) else [override_major]
            top_majors = override_majors + [major for major in top_majors if major not in override_majors]
            top_majors = top_majors[:3]
        schools.append({
            "school_id": item["school_id"],
            "school_name": item["school_name"],
            "district": geo.get("district", ""),
            "address": geo.get("address", ""),
            "longitude": geo.get("longitude"),
            "latitude": geo.get("latitude"),
            "school_type": one("SELECT school_type FROM dim_school WHERE school_id=:school_id", {"school_id": item["school_id"]}).get("school_type", ""),
            "avg_salary": item["avg_salary"],
            "employment_sample_count": item["employment_count"],
            "graduate_count": item["graduate_count"],
            "covered_major_count": one(
                "SELECT COUNT(DISTINCT major_code) v FROM bridge_school_major WHERE school_id=:school_id",
                {"school_id": item["school_id"]},
            ).get("v", 0),
            "employment_rate": item["employment_rate"],
            "high_quality_employment_rate": item["high_quality_employment_rate"],
            "leading_industry_count": item["leading_industry_employment_count"],
            "leading_industry_rate": item["leading_industry_rate"],
            "top_industry_name": item["top_industry_name"],
            "advantage_majors": top_majors,
            "industry_distribution": item.get("industry_distribution_json") or "[]",
        })
    return schools


@app.get("/api/public/overview")
@require_roles("public", "government")
def public_overview():
    schools = public_school_rows("ALL")
    total_emp = sum(int(item.get("employment_sample_count") or 0) for item in schools)
    avg_salary = (
        sum(float(item.get("avg_salary") or 0) * int(item.get("employment_sample_count") or 0) for item in schools) / total_emp
        if total_emp else 0
    )
    summary = {
        "school_count": len(schools),
        "total_employment_sample_count": total_emp,
        "avg_salary": round(avg_salary, 2),
        "major_count": one("SELECT COUNT(*) v FROM dim_major_catalog").get("v", 0),
        "public_metric_count": 4,
    }
    return ok({"summary": summary, "schools": schools})


@app.get("/api/public/schools")
@require_roles("public", "government")
def public_schools():
    return ok({"items": public_school_rows("ALL")})


@app.get("/api/public/salary-ranking")
@require_roles("public", "government")
def public_salary_ranking():
    limit = max(1, min(int(request.args.get("limit", 10)), 30))
    min_sample = max(1, int(request.args.get("min_sample", 30)))
    school_id = request.args.get("school_id")
    where = ""
    params = {"min_sample": min_sample}
    if school_id:
        where = "WHERE e.school_id = :school_id"
        params["school_id"] = school_id

    data = rows(
        f"""
        SELECT m.major_code, m.major_name,
               ROUND(AVG(e.salary), 2) AS avg_salary,
               COUNT(*) AS sample_count,
               ROUND(AVG(CASE WHEN e.employment_quality_level IN ('high','高质量')
                                 OR e.match_score >= 0.75
                                 OR e.is_shanghai_leading_employment = 1
                                THEN 1 ELSE 0 END), 4) AS employment_quality_score,
               ROUND(AVG(CASE WHEN e.is_shanghai_leading_employment = 1 THEN 1 ELSE 0 END), 4) AS leading_industry_rate,
               MAX(COALESCE(m.is_real_display_major, 0)) AS is_real_display_major,
               MAX(COALESCE(m.is_catalog_placeholder, 0)) AS is_catalog_placeholder,
               MAX(COALESCE(m.salary_rank_weight, 0)) AS salary_rank_weight,
               MAX(COALESCE(m.industry_trend_tags, '')) AS industry_trend_tags
        FROM fact_employment e
        JOIN dim_major_catalog m ON e.major_code = m.major_code
        {where}
        GROUP BY m.major_code, m.major_name
        HAVING sample_count >= :min_sample
        """
        ,
        params,
    )

    candidates = [
        item
        for item in data
        if item.get("major_name") in REAL_DISPLAY_MAJOR_NAMES
        and is_valid_display_major_name(item.get("major_name"))
        and int(item.get("is_catalog_placeholder") or 0) == 0
    ]
    if not candidates:
        candidates = [
            item
            for item in data
            if is_valid_display_major_name(item.get("major_name"))
            and item.get("major_name") in REAL_DISPLAY_MAJOR_NAMES
        ]
    trend_candidates = [
        item
        for item in candidates
        if (item.get("industry_trend_tags") or trend_tags_for_major(item.get("major_name")))
    ]
    if len(trend_candidates) >= limit:
        candidates = trend_candidates

    salaries = [float(item.get("avg_salary") or 0) for item in candidates]
    min_salary = min(salaries) if salaries else 0
    max_salary = max(salaries) if salaries else 0
    salary_span = max(max_salary - min_salary, 1)

    ranked = []
    for item in candidates:
        major_name = item.get("major_name", "")
        avg_salary = float(item.get("avg_salary") or 0)
        salary_score = (avg_salary - min_salary) / salary_span * 100
        trend_weight = float(item.get("salary_rank_weight") or 0) or salary_rank_weight_for_major(major_name)
        quality_score = float(item.get("employment_quality_score") or 0) * 100
        confidence_score = min(float(item.get("sample_count") or 0) / 300, 1.0) * 100
        salary_rank_score = (
            0.55 * salary_score
            + 0.20 * trend_weight
            + 0.15 * quality_score
            + 0.10 * confidence_score
        )
        tags = item.get("industry_trend_tags") or "、".join(trend_tags_for_major(major_name))
        ranked.append({
            "major_code": item.get("major_code"),
            "major_name": major_name,
            "avg_salary": round(avg_salary, 2),
            "sample_count": int(item.get("sample_count") or 0),
            "industry_trend_tags": [tag for tag in str(tags).split("、") if tag],
            "employment_quality_score": round(quality_score, 2),
            "leading_industry_rate": item.get("leading_industry_rate", 0),
            "salary_rank_score": round(salary_rank_score, 2),
        })

    ranked.sort(key=lambda item: item["salary_rank_score"], reverse=True)
    for index, item in enumerate(ranked[:limit], start=1):
        item["rank"] = index
    return ok({"items": ranked[:limit]})


@app.get("/api/public/school-comparison")
@require_roles("public", "government")
def public_school_comparison():
    major_code = request.args.get("major_code") or "all"
    return ok({"items": public_school_rows(major_code)})


@app.route("/api/report/ai", methods=["GET", "POST"])

@app.route("/api/report", methods=["GET"])
@app.route("/api/report/generate", methods=["POST"])
@require_roles("teacher", "government")
def report_ai():
    kpi = {
        "high": one("SELECT COUNT(DISTINCT major_code) v FROM ads_job_demand_forecast WHERE demand_level='高需求'").get("v", 0),
        "mape": one("SELECT ROUND(AVG(mape),2) v FROM ads_job_demand_forecast").get("v", 0),
        "precision": one("SELECT ROUND(AVG(precision_at_k),4) v FROM ads_enrollment_matching").get("v", 0),
        "rules": one("SELECT COUNT(*) v FROM ads_training_rules").get("v", 0),
    }
    top = rows("""
        SELECT f.major_name, f.job_category_name, SUM(f.predicted_demand_count) demand
        FROM ads_job_demand_forecast f
        JOIN dim_major_catalog m ON f.major_code=m.major_code
        WHERE COALESCE(m.is_real_display_major,0)=1
          AND COALESCE(m.is_catalog_placeholder,0)=0
          AND m.major_name NOT REGEXP '[0-9]$'
        GROUP BY f.major_name, f.job_category_name
        ORDER BY demand DESC
        LIMIT 5
    """)
    text_report = "高校需求-招生-培养-就业-监测一体化分析专报\n\n"
    text_report += f"当前高需求专业数 {kpi['high']} 个，岗位需求预测 MAPE 为 {kpi['mape']}%，招生匹配 Precision@K 为 {kpi['precision']}。\n"
    text_report += f"规则挖掘形成 {kpi['rules']} 条课程技能与就业岗位证据链，覆盖化工、医学、建筑、教育、财经、外语、服装、光电和软件数据等方向。\n"
    text_report += "重点需求组合：\n" + "\n".join([f"- {r['major_name']} / {r['job_category_name']}：{r['demand']:.0f} 人" for r in top])
    return ok({"report": text_report, "fallback": False})


@app.get("/api/audit/logs")
@app.get("/api/audit-logs")
@require_roles("government")
def audit_logs():
    logs = rows("SELECT * FROM sys_audit_log ORDER BY audit_id DESC LIMIT 200")
    return ok({"items": logs, "total": len(logs)})


@app.get("/api/gov/school-benchmark-overview")
@app.get("/api/government/school-comparison")
@require_roles("government")
def school_benchmark():
    major_code = request.args.get("major_code") or request.args.get("major") or "all"
    limit = max(1, min(int(request.args.get("limit", 10)), 50))
    is_all = str(major_code).lower() in {"", "all", "全部专业", "__all_majors__"}
    where = "WHERE major_code='ALL'" if is_all else "WHERE major_code=:major_code"
    params = {"major_code": major_code, "limit": limit} if not is_all else {"limit": limit}
    items = rows(
        f"""
        SELECT school_id, school_name, major_code, major_name, discipline_category,
               employment_count, graduate_count,
               ROUND(employment_rate,4) AS employment_rate_raw,
               ROUND(employment_rate*100,2) AS employment_rate,
               ROUND(employment_rate*100,2) AS employment_rate_pct,
               ROUND(avg_salary,2) AS avg_salary,
               high_quality_employment_count,
               ROUND(high_quality_employment_rate,4) AS high_quality_employment_rate_raw,
               ROUND(high_quality_employment_rate*100,2) AS high_quality_employment_rate,
               ROUND(high_quality_employment_rate*100,2) AS high_quality_employment_rate_pct,
               leading_industry_employment_count,
               ROUND(leading_industry_employment_rate,4) AS leading_industry_employment_rate_raw,
               ROUND(leading_industry_employment_rate*100,2) AS leading_industry_employment_rate,
               top_industry_name, top_industry_count, ROUND(top_industry_rate,4) AS top_industry_rate,
               industry_distribution_json AS industry_distribution,
               employment_count AS student_count,
               ROUND(employment_rate*100,2) AS industry_match_score,
               ROUND(high_quality_employment_rate*100,2) AS strategic_ratio,
               top_industry_name AS top_industry,
               '平台汇总' AS school_level
        FROM ads_school_compare_summary
        {where}
        ORDER BY employment_count DESC
        LIMIT :limit
        """,
        params,
    )
    summary = one(
        """
        SELECT
          (SELECT COUNT(*) FROM fact_graduate) + (SELECT COUNT(*) FROM fact_employment) + (SELECT COUNT(*) FROM fact_job_posting) AS total_data_sample_count,
          (SELECT COUNT(*) FROM fact_graduate) AS total_graduate_count,
          (SELECT COUNT(*) FROM fact_employment) AS total_employment_count,
          (SELECT COUNT(*) FROM fact_job_posting) AS total_job_posting_count,
          (SELECT COUNT(*) FROM dim_school) AS school_count,
          (SELECT COUNT(*) FROM dim_major_catalog) AS major_count
        """
    )
    major_options = rows(
        """
        SELECT a.major_code, a.major_name, COUNT(DISTINCT a.school_id) AS school_coverage,
               SUM(a.employment_count) AS employment_count
        FROM ads_school_compare_summary a
        JOIN dim_major_catalog m ON a.major_code=m.major_code
        WHERE a.major_code <> 'ALL'
          AND COALESCE(m.is_real_display_major,0)=1
          AND COALESCE(m.is_catalog_placeholder,0)=0
          AND m.major_name NOT REGEXP '[0-9]$'
        GROUP BY a.major_code, a.major_name
        HAVING school_coverage >= 2
        ORDER BY school_coverage DESC, employment_count DESC
        LIMIT 80
        """
    )
    payload = {
        "summary": summary,
        "items": items,
        "overview": items if is_all else rows("SELECT * FROM ads_school_compare_summary WHERE major_code='ALL' ORDER BY employment_count DESC LIMIT 10"),
        "rows": items,
        "major_options": major_options,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    message = "success" if items else "学校对标分析暂无数据，请先运行 Spark 聚合或迁移脚本生成 ads_school_compare_summary"
    return ok(payload, message=message)


@app.get("/api/gov/school-detail")
@require_roles("government")
def school_detail():
    school_name = request.args.get("school_name", "上海大学")
    overview = one("SELECT * FROM dim_school WHERE school_name=:school_name", {"school_name": school_name})
    majors = rows("SELECT o.* FROM ads_major_optimization o WHERE o.school_name=:school_name ORDER BY priority_score DESC LIMIT 30", {"school_name": school_name})
    return ok({"overview": overview, "majors": majors, "warnings": []})


@app.get("/api/gov/major-detail")
@require_roles("government")
def major_detail():
    school_name = request.args.get("school_name", "上海大学")
    major_name = request.args.get("major_name", "数据科学与大数据技术")
    data = one("SELECT * FROM ads_major_optimization WHERE school_name=:s AND major_name=:m LIMIT 1", {"s": school_name, "m": major_name})
    return ok(data or {})


@app.get("/api/gov/school-benchmark-major")
@require_roles("government")
def school_benchmark_major():
    major_name = request.args.get("major_name", "")
    data = rows(
        """
        SELECT school_id, school_name, major_code, major_name, discipline_category,
               employment_count AS student_count, employment_count, graduate_count,
               ROUND(employment_rate*100,2) AS employment_rate,
               ROUND(avg_salary,2) AS avg_salary,
               ROUND(high_quality_employment_rate*100,2) AS strategic_ratio,
               top_industry_name AS top_industry,
               leading_industry_employment_count,
               ROUND(leading_industry_employment_rate*100,2) AS leading_industry_employment_rate,
               industry_distribution_json AS industry_distribution,
               '平台汇总' AS school_level
        FROM ads_school_compare_summary
        WHERE major_name=:major_name AND major_code <> 'ALL'
        ORDER BY employment_count DESC
        """,
        {"major_name": major_name},
    )
    return ok({"rows": data, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


if __name__ == "__main__":
    run_startup_checks()
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
