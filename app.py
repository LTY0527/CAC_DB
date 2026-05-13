# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import builtins
import hashlib
import hmac
import json
import math
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

PUBLIC_SCHOOL_DISPLAY_MAJOR_MAP = {
    "上海交通大学": "计算机科学与技术",
    "同济大学": "土木工程",
    "复旦大学": "数学与应用数学",
    "上海大学": "金属材料工程",
    "华东师范大学": "教育学",
    "上海理工大学": "能源与动力工程",
    "华东理工大学": "化学工程与工艺",
    "东华大学": "纺织科学与工程",
    "上海外国语大学": "国际经济与贸易",
    "上海财经大学": "会计学",
}

PUBLIC_SCHOOL_NAME_ALIASES = {
    "上海交大": "上海交通大学",
    "复旦": "复旦大学",
    "同济": "同济大学",
    "华师大": "华东师范大学",
    "华理": "华东理工大学",
    "上财": "上海财经大学",
    "上大": "上海大学",
    "上外": "上海外国语大学",
    "上理工": "上海理工大学",
}

MAJOR_INDUSTRY_RULES = {
    "风景园林": {
        "allow_industries": ["建筑设计", "城市规划", "园林景观", "生态环保", "土木建筑", "文化旅游", "房地产与工程咨询"],
        "allow_keywords": ["园林", "景观", "规划", "建筑", "生态", "环保", "绿化", "市政", "设计", "工程咨询"],
        "deny_industries": ["集成电路与电子信息", "集成电路", "芯片", "半导体", "新能源汽车", "生物医药"],
        "deny_keywords": ["集成电路", "芯片", "半导体", "射频", "芯片验证", "嵌入式", "新能源电池"],
    },
    "计算机科学与技术": {
        "allow_industries": ["软件和信息服务", "人工智能", "互联网", "集成电路与电子信息", "数字经济", "金融科技"],
        "allow_keywords": ["软件", "算法", "数据", "系统", "开发", "测试", "人工智能", "网络", "云计算"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "集成电路": {
        "allow_industries": ["集成电路与电子信息", "电子信息", "半导体"],
        "allow_keywords": ["集成电路", "芯片", "半导体", "射频", "版图", "验证", "EDA"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "电子信息": {
        "allow_industries": ["集成电路与电子信息", "电子信息", "通信", "智能制造"],
        "allow_keywords": ["电子", "通信", "芯片", "嵌入式", "硬件", "测试", "自动化"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "能源与动力工程": {
        "allow_industries": ["能源动力", "新能源", "装备制造", "汽车工程", "电力工程"],
        "allow_keywords": ["能源", "动力", "新能源", "电力", "热能", "发动机", "储能", "汽车"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "纺织科学与工程": {
        "allow_industries": ["纺织服装", "新材料", "时尚设计", "智能制造"],
        "allow_keywords": ["纺织", "服装", "面料", "材料", "染整", "时尚", "设计"],
        "deny_industries": ["集成电路与电子信息", "芯片", "半导体"],
        "deny_keywords": ["集成电路", "芯片", "半导体", "射频"],
    },
    "化学工程与工艺": {
        "allow_industries": ["化工", "新材料", "生物医药", "能源化工", "环保"],
        "allow_keywords": ["化工", "化学", "材料", "工艺", "制药", "环保", "新能源材料"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "土木工程": {
        "allow_industries": ["土木建筑", "城市建设", "房地产与工程咨询", "交通工程"],
        "allow_keywords": ["土木", "建筑", "结构", "施工", "工程", "市政", "交通", "监理"],
        "deny_industries": ["集成电路与电子信息", "芯片", "半导体"],
        "deny_keywords": ["集成电路", "芯片", "半导体", "射频"],
    },
    "教育学": {
        "allow_industries": ["教育培训", "公共服务", "文化传播", "人力资源"],
        "allow_keywords": ["教育", "培训", "课程", "教研", "学习", "师资", "人才发展"],
        "deny_industries": ["集成电路与电子信息", "芯片", "半导体"],
        "deny_keywords": ["集成电路", "芯片", "半导体", "射频"],
    },
    "会计学": {
        "allow_industries": ["金融服务", "会计审计", "企业服务", "贸易服务"],
        "allow_keywords": ["会计", "审计", "财务", "税务", "风控", "金融", "结算"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "国际经济与贸易": {
        "allow_industries": ["贸易服务", "金融服务", "跨境电商", "物流供应链", "商务服务"],
        "allow_keywords": ["贸易", "外贸", "商务", "供应链", "跨境", "金融", "市场"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "金属材料工程": {
        "allow_industries": ["新材料", "高端装备", "智能制造", "汽车工程"],
        "allow_keywords": ["材料", "金属", "冶金", "制造", "工艺", "装备", "汽车"],
        "deny_industries": [],
        "deny_keywords": [],
    },
    "数学与应用数学": {
        "allow_industries": ["软件和信息服务", "人工智能", "金融科技", "教育培训", "数据服务"],
        "allow_keywords": ["算法", "数据", "模型", "量化", "软件", "分析", "数学", "教研"],
        "deny_industries": [],
        "deny_keywords": [],
    },
}

GENERIC_UNCOVERED_MAJOR_DENY_KEYWORDS = ["集成电路", "芯片", "半导体", "射频", "芯片验证", "嵌入式"]
GLOBAL_RECOMMENDATION_DENY_KEYWORDS = ["芯片验证工程师"]

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


def table_exists_cached(table_name: str) -> bool:
    return bool(
        one(
            """
            SELECT COUNT(*) v
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
            """,
            {"table_name": table_name},
        ).get("v", 0)
    )


def table_columns(table_name: str) -> set[str]:
    return {
        item.get("column_name") or item.get("COLUMN_NAME")
        for item in rows(
            """
            SELECT column_name AS column_name
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
            """,
            {"table_name": table_name},
        )
    }


def first_existing_column(table_name: str, candidates: list[str]) -> str | None:
    columns = table_columns(table_name)
    return next((column for column in candidates if column in columns), None)


def resolve_current_school_scope():
    role = g.current_user.get("role_db")
    requested_school_id = (request.args.get("school_id") or "").strip()
    requested_all = requested_school_id.lower() in {"", "all", "__all__", "__all_majors__", "全部", "全部学校"}
    current_school_id = (g.current_user.get("school_id") or DEFAULT_SCHOOL_ID or "").strip()

    if role == "government":
        school_id = None if requested_all else requested_school_id
    else:
        school_id = current_school_id

    school_name = ""
    if school_id:
        school = one(
            """
            SELECT school_id, school_name
            FROM dim_school
            WHERE TRIM(CAST(school_id AS CHAR))=:school_id
            LIMIT 1
            """,
            {"school_id": str(school_id).strip()},
        )
        school_id = str(school.get("school_id") or school_id).strip()
        school_name = school.get("school_name") or ""

    return {
        "role": role,
        "school_id": school_id,
        "school_name": school_name,
        "school_id_aliases": [school_id] if school_id else [],
    }


def scoped_where(table_name: str, scope: dict, alias: str = "", extra: list[str] | None = None):
    columns = table_columns(table_name)
    params = {}
    clauses = list(extra or [])
    qualifier = f"{alias}." if alias else ""
    school_id = scope.get("school_id")
    school_name = scope.get("school_name")
    if school_id:
        if "school_id" in columns:
            clauses.append(f"TRIM(CAST({qualifier}school_id AS CHAR))=:scope_school_id")
            params["scope_school_id"] = str(school_id).strip()
        elif "school_name" in columns and school_name:
            clauses.append(f"TRIM(CAST({qualifier}school_name AS CHAR))=:scope_school_name")
            params["scope_school_name"] = str(school_name).strip()
        else:
            clauses.append("1=0")
    return ("WHERE " + " AND ".join(clauses) if clauses else "", params)


def stable_float(*parts) -> float:
    raw = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def split_tags(value) -> set[str]:
    if value is None:
        return set()
    text_value = str(value)
    for mark in ["|", "、", ",", "，", ";", "；", "/", " "]:
        text_value = text_value.replace(mark, "|")
    return {part.strip() for part in text_value.split("|") if part.strip()}


def normalized_text(*values) -> str:
    return "|".join(str(value or "").strip() for value in values if value is not None)


def contains_any(text_value: str, keywords: list[str]) -> bool:
    text_value = str(text_value or "")
    return any(keyword and keyword in text_value for keyword in keywords)


def major_industry_rule(major_name: str | None) -> dict:
    name = str(major_name or "").strip()
    for key, rule in MAJOR_INDUSTRY_RULES.items():
        if key in name or name in key:
            return {**rule, "_matched": True}
    return {
        "allow_industries": [],
        "allow_keywords": [],
        "deny_industries": [],
        "deny_keywords": [],
        "_matched": False,
    }


def recommendation_candidate_text(candidate: dict, enterprise: dict | None = None) -> str:
    enterprise = enterprise or {}
    return normalized_text(
        candidate.get("industry_name"),
        candidate.get("industry_type"),
        candidate.get("job_category_name"),
        candidate.get("recommended_job"),
        candidate.get("major_name"),
        candidate.get("skill_tags"),
        candidate.get("compatible_major_classes"),
        candidate.get("policy_direction_tags"),
        enterprise.get("enterprise_name"),
        enterprise.get("industry_name"),
    )


def violates_major_industry_rule(major_name: str | None, candidate: dict, enterprise: dict | None = None) -> bool:
    rule = major_industry_rule(major_name)
    text_value = recommendation_candidate_text(candidate, enterprise)
    enterprise = enterprise or {}
    industry_value = str(candidate.get("industry_name") or candidate.get("industry_type") or enterprise.get("industry_name") or "")
    if contains_any(industry_value, rule.get("deny_industries", [])):
        return True
    deny_keywords = list(rule.get("deny_keywords", [])) + GLOBAL_RECOMMENDATION_DENY_KEYWORDS
    if not rule.get("_matched"):
        deny_keywords += GENERIC_UNCOVERED_MAJOR_DENY_KEYWORDS
    if contains_any(text_value, deny_keywords):
        return True
    return False


def matches_major_allow_rule(major_name: str | None, candidate: dict, enterprise: dict | None = None) -> bool:
    rule = major_industry_rule(major_name)
    allow_industries = rule.get("allow_industries", [])
    allow_keywords = rule.get("allow_keywords", [])
    if not allow_industries and not allow_keywords:
        return True
    text_value = recommendation_candidate_text(candidate, enterprise)
    enterprise = enterprise or {}
    industry_value = str(candidate.get("industry_name") or candidate.get("industry_type") or enterprise.get("industry_name") or "")
    return contains_any(industry_value, allow_industries) or contains_any(text_value, allow_keywords)


def recommendation_row_is_valid_for_profile(profile: dict, row: dict) -> bool:
    candidate = {
        "industry_name": row.get("industry_name") or row.get("industry_type"),
        "job_category_name": row.get("job_category_name") or row.get("recommended_job"),
        "major_name": row.get("major_name"),
    }
    enterprise = {"enterprise_name": row.get("enterprise_name") or row.get("recommended_enterprise")}
    return not violates_major_industry_rule(profile.get("major_name"), candidate, enterprise)


def id_match_conditions(alias: str, columns: list[str], id_text: str, param_prefix: str = "student"):
    qualifier = f"{alias}." if alias else ""
    text_key = f"{param_prefix}_id_text"
    int_key = f"{param_prefix}_id_int"
    params = {text_key: id_text}
    conditions = []
    is_numeric = id_text.isdigit()
    if is_numeric:
        params[int_key] = int(id_text)
    for column in columns:
        conditions.append(f"CAST({qualifier}{column} AS CHAR)=:{text_key}")
        conditions.append(f"TRIM(CAST({qualifier}{column} AS CHAR))=:{text_key}")
        if is_numeric:
            conditions.append(f"CAST({qualifier}{column} AS UNSIGNED)=:{int_key}")
    return conditions, params


def available_recommendation_examples(scope: dict, limit: int = 5) -> list[str]:
    examples: list[str] = []
    if table_columns("ads_job_recommendation"):
        rec_where, rec_params = scoped_where("ads_job_recommendation", scope)
        examples.extend(
            str(item["graduate_id"])
            for item in rows(
                f"""
                SELECT graduate_id
                FROM ads_job_recommendation
                {rec_where}
                GROUP BY graduate_id
                ORDER BY CAST(graduate_id AS UNSIGNED), graduate_id
                LIMIT :limit
                """,
                {**rec_params, "limit": limit},
            )
            if item.get("graduate_id") is not None
        )
    if len(examples) < limit and table_columns("fact_graduate"):
        grad_where, grad_params = scoped_where("fact_graduate", scope)
        supplement = rows(
            f"""
            SELECT graduate_id
            FROM fact_graduate
            {grad_where}
            GROUP BY graduate_id
            ORDER BY CAST(graduate_id AS UNSIGNED), graduate_id
            LIMIT :limit
            """,
            {**grad_params, "limit": limit * 3},
        )
        seen = set(examples)
        for item in supplement:
            value = str(item.get("graduate_id") or "")
            if value and value not in seen:
                examples.append(value)
                seen.add(value)
            if len(examples) >= limit:
                break
    return examples[:limit]


def fetch_student_profile(id_text: str, scope: dict) -> dict | None:
    profile_sqls = []
    if {"graduate_id", "school_id"}.issubset(table_columns("fact_graduate")):
        id_columns = [column for column in ["graduate_id", "student_id", "student_no", "id"] if column in table_columns("fact_graduate")]
        id_conditions, id_params = id_match_conditions("g", id_columns, id_text, "grad")
        where_sql, scope_params = scoped_where("fact_graduate", scope, "g", [f"({' OR '.join(id_conditions)})"])
        profile_sqls.append((
            f"""
            SELECT g.graduate_id, g.school_id, s.school_name, g.major_code, m.major_name,
                   g.degree_level, g.gpa_level, g.skill_tags, g.internship_count,
                   g.certification_tags, g.job_intention_tags
            FROM fact_graduate g
            LEFT JOIN dim_school s ON TRIM(CAST(g.school_id AS CHAR))=TRIM(CAST(s.school_id AS CHAR))
            LEFT JOIN dim_major_catalog m ON TRIM(CAST(g.major_code AS CHAR))=TRIM(CAST(m.major_code AS CHAR))
            {where_sql}
            LIMIT 1
            """,
            {**id_params, **scope_params},
        ))
    if {"graduate_id", "school_id"}.issubset(table_columns("fact_employment")):
        id_columns = [column for column in ["graduate_id", "student_id", "student_no", "id"] if column in table_columns("fact_employment")]
        id_conditions, id_params = id_match_conditions("e", id_columns, id_text, "emp")
        where_sql, scope_params = scoped_where("fact_employment", scope, "e", [f"({' OR '.join(id_conditions)})"])
        profile_sqls.append((
            f"""
            SELECT e.graduate_id, e.school_id, s.school_name, e.major_code, m.major_name,
                   NULL AS degree_level, NULL AS gpa_level, NULL AS skill_tags, NULL AS internship_count,
                   NULL AS certification_tags, i.industry_name AS job_intention_tags
            FROM fact_employment e
            LEFT JOIN dim_school s ON TRIM(CAST(e.school_id AS CHAR))=TRIM(CAST(s.school_id AS CHAR))
            LEFT JOIN dim_major_catalog m ON TRIM(CAST(e.major_code AS CHAR))=TRIM(CAST(m.major_code AS CHAR))
            LEFT JOIN dim_industry i ON e.industry_id=i.industry_id
            {where_sql}
            LIMIT 1
            """,
            {**id_params, **scope_params},
        ))
    for sql, params in profile_sqls:
        data = rows(sql, params)
        if data:
            return data[0]
    return None


def fetch_existing_student_recommendations(id_text: str, scope: dict) -> list[dict]:
    rec_columns = table_columns("ads_job_recommendation")
    id_columns = [column for column in ["graduate_id", "student_id", "student_no", "id"] if column in rec_columns]
    if not id_columns:
        return []
    id_conditions, params = id_match_conditions("r", id_columns, id_text, "rec")
    where_sql, scope_params = scoped_where("ads_job_recommendation", scope, "r", [f"({' OR '.join(id_conditions)})"])
    return rows(
        f"""
        SELECT r.*, r.graduate_id AS student_id, r.enterprise_name AS recommended_enterprise,
               r.job_category_name AS recommended_job, r.similarity_score AS matching_score,
               r.reason_text AS recommend_reason, r.industry_name AS industry_type
        FROM ads_job_recommendation r
        {where_sql}
        ORDER BY COALESCE(r.rank_no, 999999), r.enterprise_name, r.job_category_name
        """,
        {**params, **scope_params},
    )


def load_recommendation_candidates(profile: dict, limit: int = 500) -> list[dict]:
    major_code = profile.get("major_code")
    school_id = profile.get("school_id")
    major_name = profile.get("major_name")
    candidate_sets = []
    forecast_columns = table_columns("ads_job_demand_forecast")
    if {"major_code", "industry_id", "job_category_id"}.issubset(forecast_columns):
        base_select = """
            SELECT f.school_id, f.school_name, f.major_code, f.major_name, f.industry_id, f.industry_name,
                   f.job_category_id, f.job_category_name,
                   SUM(f.predicted_demand_count) AS demand_count,
                   AVG(f.avg_salary) AS avg_salary,
                   AVG(f.demand_growth_rate) AS demand_growth_rate,
                   MAX(j.skill_tags) AS skill_tags,
                   MAX(j.compatible_major_classes) AS compatible_major_classes,
                   MAX(j.policy_direction_tags) AS policy_direction_tags
            FROM ads_job_demand_forecast f
            LEFT JOIN dim_job_category j ON f.job_category_id=j.job_category_id
        """
        group_order = """
            GROUP BY f.school_id, f.school_name, f.major_code, f.major_name,
                     f.industry_id, f.industry_name, f.job_category_id, f.job_category_name
            ORDER BY demand_count DESC, avg_salary DESC
            LIMIT :limit
        """
        candidate_sets.extend([
            (f"{base_select} WHERE f.school_id=:school_id AND f.major_code=:major_code {group_order}", {"school_id": school_id, "major_code": major_code, "limit": limit}),
            (f"{base_select} WHERE f.major_code=:major_code {group_order}", {"major_code": major_code, "limit": limit}),
            (f"{base_select} WHERE f.school_id=:school_id {group_order}", {"school_id": school_id, "limit": limit}),
            (f"{base_select} {group_order}", {"limit": limit}),
        ])
    combined = []
    seen = set()
    for sql, params in candidate_sets:
        data = rows(sql, params)
        for item in data:
            key = (item.get("school_id"), item.get("major_code"), item.get("industry_id"), item.get("job_category_id"))
            if key in seen:
                continue
            seen.add(key)
            combined.append(item)
        if len(combined) >= limit:
            break
    if combined:
        return combined[:limit]
    if table_columns("fact_job_demand"):
        return rows(
            """
            SELECT NULL AS school_id, NULL AS school_name, NULL AS major_code, major_name,
                   NULL AS industry_id, leading_industry_tag AS industry_name,
                   NULL AS job_category_id, job_category AS job_category_name,
                   SUM(recruit_count) AS demand_count, AVG(salary_avg) AS avg_salary,
                   0 AS demand_growth_rate, GROUP_CONCAT(skill_keywords SEPARATOR '|') AS skill_tags,
                   major_category AS compatible_major_classes, '' AS policy_direction_tags
            FROM fact_job_demand
            WHERE (:major_name='' OR major_name=:major_name)
            GROUP BY major_name, leading_industry_tag, job_category, major_category
            ORDER BY demand_count DESC, avg_salary DESC
            LIMIT :limit
            """,
            {"major_name": major_name or "", "limit": limit},
        )
    return []


def enterprise_for_candidate(candidate: dict, graduate_id: str, rank_seed: int) -> dict:
    industry_id = candidate.get("industry_id")
    if industry_id is not None and table_columns("dim_enterprise"):
        ent_rows = rows(
            """
            SELECT enterprise_id, enterprise_name, industry_id, district,
                   salary_factor, hiring_stability_factor, is_high_tech, is_specialized_new
            FROM dim_enterprise
            WHERE industry_id=:industry_id
            ORDER BY enterprise_id
            LIMIT 300
            """,
            {"industry_id": industry_id},
        )
        if ent_rows:
            index = int(stable_float(graduate_id, industry_id, candidate.get("job_category_id"), rank_seed) * len(ent_rows)) % len(ent_rows)
            return ent_rows[index]
    if table_columns("dim_enterprise"):
        ent_rows = rows(
            """
            SELECT enterprise_id, enterprise_name, industry_id, district,
                   salary_factor, hiring_stability_factor, is_high_tech, is_specialized_new
            FROM dim_enterprise
            ORDER BY enterprise_id
            LIMIT 500
            """
        )
        if ent_rows:
            index = int(stable_float(graduate_id, candidate.get("job_category_id"), rank_seed) * len(ent_rows)) % len(ent_rows)
            return ent_rows[index]
    return {"enterprise_id": None, "enterprise_name": "暂无单位候选", "salary_factor": 1, "hiring_stability_factor": 0.6}


def build_student_job_recommendations(profile: dict, top_k: int = 3) -> list[dict]:
    candidates = load_recommendation_candidates(profile)
    if not candidates:
        return []
    major_name = profile.get("major_name")
    rule = major_industry_rule(major_name)
    safe_candidates = [
        item for item in candidates
        if not violates_major_industry_rule(major_name, item)
    ]
    allow_industries = rule.get("allow_industries", [])
    allow_keywords = rule.get("allow_keywords", [])
    if allow_industries or allow_keywords:
        allowed_candidates = [
            item for item in safe_candidates
            if matches_major_allow_rule(major_name, item)
        ]
        candidates = allowed_candidates
    else:
        candidates = safe_candidates
    if not candidates:
        return []
    graduate_id = str(profile.get("graduate_id") or "")
    student_skills = split_tags(profile.get("skill_tags")) | split_tags(profile.get("certification_tags"))
    student_intents = split_tags(profile.get("job_intention_tags"))
    max_demand = max(float(item.get("demand_count") or 0) for item in candidates) or 1
    salaries = [float(item.get("avg_salary") or 0) for item in candidates if float(item.get("avg_salary") or 0) > 0]
    min_salary = min(salaries) if salaries else 0
    max_salary = max(salaries) if salaries else 1
    salary_span = max(max_salary - min_salary, 1)
    scored = []
    for index, item in enumerate(candidates):
        candidate_skills = split_tags(item.get("skill_tags")) | split_tags(item.get("policy_direction_tags"))
        overlap = len(student_skills & candidate_skills) / max(len(student_skills), 1) if student_skills else 0.25
        major_match = 1.0 if str(item.get("major_code") or "") == str(profile.get("major_code") or "") else 0.35
        if profile.get("major_name") and str(profile.get("major_name")) in str(item.get("compatible_major_classes") or ""):
            major_match = max(major_match, 0.7)
        industry_text = f"{item.get('industry_name') or ''}|{item.get('job_category_name') or ''}"
        industry_match = 0.55
        if student_intents and any(intent in industry_text for intent in student_intents):
            industry_match = 1.0
        allow_industry_hit = 1.0 if contains_any(str(item.get("industry_name") or ""), allow_industries) else 0.0
        allow_keyword_hit = 1.0 if contains_any(recommendation_candidate_text(item), allow_keywords) else 0.0
        major_keyword_hit = 1.0 if profile.get("major_name") and contains_any(recommendation_candidate_text(item), [str(profile.get("major_name"))]) else 0.0
        demand_norm = float(item.get("demand_count") or 0) / max_demand
        salary_norm = (float(item.get("avg_salary") or 0) - min_salary) / salary_span if item.get("avg_salary") else 0
        tie = stable_float(graduate_id, item.get("industry_id"), item.get("job_category_id"), index)
        if allow_industries or allow_keywords:
            score = (
                0.25 * allow_industry_hit
                + 0.25 * allow_keyword_hit
                + 0.20 * max(major_match, major_keyword_hit)
                + 0.15 * demand_norm
                + 0.10 * salary_norm
                + 0.05 * tie
            )
        else:
            score = (
                0.35 * major_match
                + 0.25 * industry_match
                + 0.15 * overlap
                + 0.10 * demand_norm
                + 0.10 * salary_norm
                + 0.05 * tie
            )
        scored.append((score, item, index, overlap, major_match, industry_match))
    scored.sort(key=lambda value: (value[0], float(value[1].get("demand_count") or 0), float(value[1].get("avg_salary") or 0)), reverse=True)
    result = []
    used_enterprises = set()
    used_jobs = set()
    for score, item, index, overlap, major_match, industry_match in scored:
        enterprise = enterprise_for_candidate(item, graduate_id, index)
        if violates_major_industry_rule(major_name, item, enterprise):
            continue
        enterprise_key = enterprise.get("enterprise_id") or enterprise.get("enterprise_name")
        job_key = item.get("job_category_id") or item.get("job_category_name")
        if len(result) < top_k and enterprise_key in used_enterprises and len(used_enterprises) >= top_k:
            continue
        if len(result) < top_k and (enterprise_key, job_key) in used_jobs:
            continue
        used_enterprises.add(enterprise_key)
        used_jobs.add((enterprise_key, job_key))
        similarity = round(max(0.5, min(0.95, score)), 4)
        confidence = "high" if similarity >= 0.75 else ("medium" if similarity >= 0.62 else "low")
        neutral_reason = "基于专业方向、岗位行业和需求热度综合匹配"
        result.append({
            "graduate_id": profile.get("graduate_id"),
            "student_id": profile.get("graduate_id"),
            "school_id": profile.get("school_id"),
            "school_name": profile.get("school_name"),
            "major_code": profile.get("major_code") or item.get("major_code"),
            "major_name": profile.get("major_name") or item.get("major_name"),
            "enterprise_id": enterprise.get("enterprise_id"),
            "enterprise_name": enterprise.get("enterprise_name"),
            "recommended_enterprise": enterprise.get("enterprise_name"),
            "industry_id": item.get("industry_id"),
            "industry_name": item.get("industry_name"),
            "industry_type": item.get("industry_name"),
            "job_category_id": item.get("job_category_id"),
            "job_category_name": item.get("job_category_name"),
            "recommended_job": item.get("job_category_name"),
            "similarity_score": similarity,
            "matching_score": similarity,
            "confidence_level": confidence,
            "predicted_demand_count": float(item.get("demand_count") or 0),
            "salary_reference": round(float(item.get("avg_salary") or 0) * float(enterprise.get("salary_factor") or 1), 2),
            "rank_no": len(result) + 1,
            "reason_text": neutral_reason,
            "recommendation_reason": neutral_reason,
            "recommend_reason": neutral_reason,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        if len(result) >= top_k:
            break
    return result


def persist_student_recommendations(recommendations: list[dict]) -> None:
    if not recommendations:
        return
    columns = table_columns("ads_job_recommendation")
    writable = [
        "graduate_id", "school_id", "school_name", "major_code", "major_name",
        "enterprise_id", "enterprise_name", "industry_id", "industry_name",
        "job_category_id", "job_category_name", "similarity_score", "matching_score",
        "confidence_level", "predicted_demand_count", "salary_reference", "rank_no",
        "reason_text", "recommendation_reason", "updated_at",
    ]
    insert_columns = [column for column in writable if column in columns]
    if not insert_columns:
        return
    values_sql = ", ".join(f":{column}" for column in insert_columns)
    column_sql = ", ".join(insert_columns)
    with engine.begin() as conn:
        for item in recommendations:
            conn.execute(
                text(f"INSERT INTO ads_job_recommendation ({column_sql}) VALUES ({values_sql})"),
                {column: item.get(column) for column in insert_columns},
            )


def get_or_build_student_job_recommendations(profile: dict, scope: dict, top_k: int = 3) -> list[dict]:
    id_text = str(profile.get("graduate_id") or "").strip()
    existing = fetch_existing_student_recommendations(id_text, scope)
    valid_existing = [item for item in existing if recommendation_row_is_valid_for_profile(profile, item)]
    if len(valid_existing) >= top_k:
        return valid_existing[:top_k]
    if existing:
        rec_columns = table_columns("ads_job_recommendation")
        id_columns = [column for column in ["graduate_id", "student_id", "student_no", "id"] if column in rec_columns]
        if id_columns:
            id_conditions, params = id_match_conditions("", id_columns, id_text, "del")
            where_sql, scope_params = scoped_where("ads_job_recommendation", scope, "", [f"({' OR '.join(id_conditions)})"])
            with engine.begin() as conn:
                conn.execute(text(f"DELETE FROM ads_job_recommendation {where_sql}"), {**params, **scope_params})
    generated = build_student_job_recommendations(profile, top_k=top_k)
    persist_student_recommendations(generated)
    return fetch_existing_student_recommendations(id_text, scope)[:top_k] or generated


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
    scope = resolve_current_school_scope()
    rec_where, rec_params = scoped_where("ads_job_recommendation", scope)
    rec_where_r, rec_params_r = scoped_where("ads_job_recommendation", scope, "r")
    rec_where_r2, rec_params_r2 = scoped_where("ads_job_recommendation", scope, "r2")

    position_col = first_existing_column("ads_job_recommendation", ["job_category_id", "job_category_name", "enterprise_id"])
    position_expr = f"COUNT(DISTINCT {position_col})" if position_col else "0"
    data = one(
        f"""
        SELECT COUNT(DISTINCT graduate_id) covered_students,
               COUNT(DISTINCT enterprise_id) covered_enterprises,
               COUNT(*) recommendation_count,
               {position_expr} recommendation_position_count
        FROM ads_job_recommendation
        {rec_where}
        """,
        rec_params,
    )

    top1 = one(
        f"""
        SELECT COUNT(*) top1_students,
               ROUND(AVG(top_similarity),4) top1_avg_similarity,
               COALESCE(SUM(is_high),0) high_match_students
        FROM (
          SELECT r.graduate_id,
                 MAX(r.similarity_score) top_similarity,
                 MAX(CASE WHEN r.confidence_level='high' OR r.similarity_score>=0.75 THEN 1 ELSE 0 END) is_high
          FROM ads_job_recommendation r
          JOIN (
            SELECT r2.graduate_id, MIN(COALESCE(r2.rank_no, 999999)) min_rank
            FROM ads_job_recommendation r2
            {rec_where_r2}
            GROUP BY r2.graduate_id
          ) t ON t.graduate_id=r.graduate_id AND COALESCE(r.rank_no, 999999)=t.min_rank
          {rec_where_r}
          GROUP BY r.graduate_id
        ) top_rows
        """,
        {**rec_params_r2, **rec_params_r},
    )

    def distinct_student_count(table_name: str, id_candidates: list[str]) -> int:
        id_column = first_existing_column(table_name, id_candidates)
        if not id_column:
            return 0
        where_sql, params = scoped_where(table_name, scope)
        return int(one(
            f"SELECT COUNT(DISTINCT {id_column}) v FROM {table_name} {where_sql}",
            params,
        ).get("v", 0) or 0)

    covered_students = int(data.get("covered_students") or 0)
    fact_graduate_total = distinct_student_count("fact_graduate", ["graduate_id", "student_id", "student_no", "id"])
    fact_employment_total = distinct_student_count("fact_employment", ["graduate_id", "student_id", "student_no", "id"])
    candidate_recommendation_total = covered_students
    if fact_graduate_total > 0:
        if fact_graduate_total < covered_students:
            school_student_total = covered_students
            total_source = "reconciled_max_fact_graduate_and_recommendation"
        else:
            school_student_total = fact_graduate_total
            total_source = "fact_graduate_distinct_graduate_id"
    elif fact_employment_total > 0:
        school_student_total = max(fact_employment_total, covered_students)
        total_source = "fact_employment_distinct_graduate_id" if fact_employment_total >= covered_students else "reconciled_max_fact_employment_and_recommendation"
    elif covered_students > 0:
        school_student_total = covered_students
        total_source = "recommendation_distinct_graduate_id_fallback"
    else:
        school_student_total = 0
        total_source = "no_student_data"

    high_match_students = int(top1.get("high_match_students") or 0)
    top1_avg_similarity = float(top1.get("top1_avg_similarity") or 0)
    data["school_student_total"] = school_student_total
    data["school_student_total_source"] = total_source
    data["school_student_total_candidates"] = {
        "fact_graduate": fact_graduate_total,
        "fact_employment": fact_employment_total,
        "recommendation": candidate_recommendation_total,
    }
    data["covered_students"] = covered_students
    data["uncovered_students"] = max(school_student_total - covered_students, 0)
    data["coverage_rate"] = round(covered_students / school_student_total, 4) if school_student_total else 0
    data["high_match_students"] = high_match_students
    data["high_confidence_ratio"] = round(high_match_students / covered_students, 4) if covered_students else 0
    data["top1_avg_similarity"] = top1_avg_similarity

    data["available_examples"] = available_recommendation_examples(scope, limit=5)
    data["scope"] = {
        "role": scope.get("role"),
        "school_id": scope.get("school_id"),
        "school_name": scope.get("school_name"),
    }
    print(f"[api/recommendation/summary] scope={data['scope']} data={data}")
    return ok(data)


@app.get("/api/recommendation/student")
@require_roles("teacher", "government")
def recommendation_student():
    graduate_id = (request.args.get("graduate_id") or request.args.get("student_id") or request.args.get("id") or "").strip()
    if not graduate_id:
        return fail("缺少 graduate_id 参数", status=400, data={"items": [], "available_examples": []})
    scope = resolve_current_school_scope()
    id_text = str(graduate_id).strip()
    examples = available_recommendation_examples(scope, limit=5)
    profile = fetch_student_profile(id_text, scope)
    if not profile:
        return ok({
            "graduate_id": id_text,
            "student_exists": False,
            "items": [],
            "available_examples": examples,
            "message": "未找到该学生，请尝试示例 ID",
        })

    data = get_or_build_student_job_recommendations(profile, scope, top_k=3)
    if not data:
        return ok({
            "graduate_id": id_text,
            "student_exists": True,
            "items": [],
            "available_examples": examples,
            "message": "该学生暂无推荐结果，请检查推荐任务是否已生成",
        })
    return ok({
        "graduate_id": str(profile.get("graduate_id") or data[0]["graduate_id"]),
        "student_exists": True,
        "student_id": str(data[0].get("student_id") or data[0].get("graduate_id") or ""),
        "major_name": profile.get("major_name") or data[0].get("major_name", ""),
        "school_name": profile.get("school_name") or data[0].get("school_name", ""),
        "available_examples": examples,
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

def is_public_advantage_major_allowed(school_name: str, major_name: str) -> bool:
    name = str(major_name or "").strip()
    if not name or name in {"ALL", "全部", "数据不足"} or name[-1:].isdigit():
        return False
    if str(school_name or "").strip() == "上海大学" and name == "轻化工程":
        return False
    return is_valid_display_major_name(name)


def public_display_major_for_school(school_name: str) -> dict:
    normalized_school_name = str(school_name or "").strip()
    normalized_school_name = PUBLIC_SCHOOL_NAME_ALIASES.get(normalized_school_name, normalized_school_name)
    major_name = PUBLIC_SCHOOL_DISPLAY_MAJOR_MAP.get(normalized_school_name)
    if normalized_school_name == "上海大学":
        major_name = "金属材料工程"
    if not major_name:
        return {"major_name": None, "major_code": None, "source": "no_business_config"}
    major = one(
        """
        SELECT major_code, major_name
        FROM dim_major_catalog
        WHERE major_name=:major_name
        ORDER BY major_code
        LIMIT 1
        """,
        {"major_name": major_name},
    )
    return {
        "major_name": major_name,
        "major_code": major.get("major_code"),
        "source": "business_config",
    }


def public_advantage_major_map():
    major_columns = table_columns("dim_major_catalog")
    display_filters = ["m.major_name IS NOT NULL", "m.major_name <> ''", "m.major_name NOT REGEXP '[0-9]$'"]
    if "is_real_display_major" in major_columns:
        display_filters.append("COALESCE(m.is_real_display_major,1)=1")
    if "is_catalog_placeholder" in major_columns:
        display_filters.append("COALESCE(m.is_catalog_placeholder,0)=0")
    where_display = " AND ".join(display_filters)
    salary_weight_expr = "COALESCE(m.salary_rank_weight,0)" if "salary_rank_weight" in major_columns else "0"

    relation_specs = [
        ("bridge_school_major", "bridge"),
        ("fact_graduate", "fact_graduate"),
        ("fact_employment", "fact_employment"),
        ("fact_enrollment_plan", "fact_enrollment_plan"),
        ("fact_course_skill", "fact_course_skill"),
        ("dim_school_major", "dim_school_major"),
        ("school_major", "school_major"),
    ]
    relation_source_counts = {}
    relation_map = {}
    source_rank = {name: index for index, (_, name) in enumerate(relation_specs)}

    for table_name, source_name in relation_specs:
        columns = table_columns(table_name)
        if not {"school_id", "major_code"}.issubset(columns):
            relation_source_counts[source_name] = 0
            continue
        ace_expr = "MAX(COALESCE(t.is_ace_major,0))" if "is_ace_major" in columns else "0"
        strength_expr = "MAX(COALESCE(t.school_major_strength_score,0))" if "school_major_strength_score" in columns else "0"
        relation_rows = rows(
            f"""
            SELECT s.school_id, s.school_name, m.major_code, m.major_name,
                   '{source_name}' AS validation_source,
                   {salary_weight_expr} AS salary_rank_weight,
                   {ace_expr} AS is_ace_major,
                   {strength_expr} AS school_major_strength_score
            FROM {table_name} t
            JOIN dim_school s
              ON TRIM(CAST(t.school_id AS CHAR))=TRIM(CAST(s.school_id AS CHAR))
            JOIN dim_major_catalog m
              ON TRIM(CAST(t.major_code AS CHAR))=TRIM(CAST(m.major_code AS CHAR))
            WHERE t.school_id IS NOT NULL
              AND t.major_code IS NOT NULL
              AND {where_display}
            GROUP BY s.school_id, s.school_name, m.major_code, m.major_name, {salary_weight_expr}
            """
        )
        valid_rows = [
            item for item in relation_rows
            if is_public_advantage_major_allowed(item.get("school_name"), item.get("major_name"))
        ]
        relation_source_counts[source_name] = len(valid_rows)
        for item in valid_rows:
            key = (item["school_id"], item["major_code"])
            old = relation_map.get(key)
            if not old or source_rank[source_name] < source_rank.get(old.get("validation_source"), 999):
                relation_map[key] = item

    emp_metrics = {}
    if {"school_id", "major_code"}.issubset(table_columns("fact_employment")):
        for item in rows(
            """
            SELECT school_id, major_code,
                   COUNT(DISTINCT graduate_id) sample_count,
                   ROUND(AVG(salary),2) avg_salary,
                   ROUND(AVG(CASE WHEN employment_quality_level='高' OR match_score>=82 THEN 1 ELSE 0 END),4) employment_quality_score,
                   ROUND(AVG(CASE WHEN is_shanghai_leading_employment=1 THEN 1 ELSE 0 END),4) leading_industry_rate
            FROM fact_employment
            GROUP BY school_id, major_code
            """
        ):
            emp_metrics[(item["school_id"], item["major_code"])] = item

    ads_metrics = {}
    if {"school_id", "major_code"}.issubset(table_columns("ads_school_compare_summary")):
        for item in rows(
            """
            SELECT school_id, major_code,
                   employment_count sample_count,
                   ROUND(avg_salary,2) avg_salary,
                   ROUND(high_quality_employment_rate,4) employment_quality_score,
                   ROUND(leading_industry_employment_rate,4) leading_industry_rate
            FROM ads_school_compare_summary
            WHERE major_code IS NOT NULL AND major_code <> 'ALL'
            """
        ):
            ads_metrics[(item["school_id"], item["major_code"])] = item

    candidates = []
    for key, relation in relation_map.items():
        metrics = ads_metrics.get(key) or emp_metrics.get(key) or {}
        sample_count = int(metrics.get("sample_count") or 0)
        avg_salary = float(metrics.get("avg_salary") or 0)
        candidates.append({
            "school_id": relation["school_id"],
            "school_name": relation["school_name"],
            "major_code": relation["major_code"],
            "major_name": relation["major_name"],
            "sample_count": sample_count,
            "avg_salary": avg_salary,
            "employment_quality_score": float(metrics.get("employment_quality_score") or 0),
            "leading_industry_rate": float(metrics.get("leading_industry_rate") or 0),
            "salary_rank_weight": float(relation.get("salary_rank_weight") or 0) or salary_rank_weight_for_major(relation.get("major_name", "")),
            "validation_source": relation.get("validation_source"),
        })

    salaries = [item["avg_salary"] for item in candidates if item["avg_salary"] > 0]
    min_salary = min(salaries) if salaries else 0
    max_salary = max(salaries) if salaries else 0
    salary_span = max(max_salary - min_salary, 1)
    max_sample = max([item["sample_count"] for item in candidates] or [0])
    grouped = {}
    for item in candidates:
        salary_score = (item["avg_salary"] - min_salary) / salary_span if item["avg_salary"] > 0 else 0
        sample_score = math.log(item["sample_count"] + 1) / math.log(max_sample + 1) if max_sample > 0 else 0
        score = (
            salary_score * 0.35
            + item["employment_quality_score"] * 0.25
            + item["leading_industry_rate"] * 0.20
            + sample_score * 0.15
            + min(item["salary_rank_weight"] / 100, 1) * 0.05
        )
        normalized = {
            "major_code": item["major_code"],
            "major_name": item["major_name"],
            "sample_count": item["sample_count"],
            "avg_salary": round(item["avg_salary"], 2),
            "employment_quality_score": round(item["employment_quality_score"], 4),
            "leading_industry_rate": round(item["leading_industry_rate"], 4),
            "score": round(score, 4),
            "validation_source": item["validation_source"],
        }
        grouped.setdefault(item["school_id"], []).append(normalized)

    result = {}
    for school_id, items in grouped.items():
        result[school_id] = sorted(
            items,
            key=lambda item: (item["score"], item["sample_count"], item["avg_salary"], item["major_name"]),
            reverse=True,
        )[0]
    diagnostics = {
        "relation_source_counts": relation_source_counts,
        "verified_major_candidate_count": len(candidates),
        "selected_advantage_major_count": len(result),
    }
    return result, diagnostics


def public_school_rows(major_code="ALL", include_diagnostics=False):
    is_all = str(major_code or "").lower() in {"", "all", "__all_majors__", "全部专业"}
    join_filter = "a.major_code='ALL'" if is_all else "a.major_code=:major_code"
    params = {} if is_all else {"major_code": major_code}
    compare_rows = rows(
        f"""
        SELECT s.school_id, s.school_name, s.school_type, s.district,
               a.major_code, a.major_name, a.employment_count, a.graduate_count,
               ROUND(a.employment_rate,4) AS employment_rate,
               ROUND(a.avg_salary,2) AS avg_salary,
               ROUND(a.high_quality_employment_rate,4) AS high_quality_employment_rate,
               a.leading_industry_employment_count,
               ROUND(a.leading_industry_employment_rate,4) AS leading_industry_rate,
               a.top_industry_name,
               a.top_industry_count,
               a.industry_distribution_json,
               COALESCE(emp.employment_sample_count,0) AS fallback_employment_sample_count,
               ROUND(COALESCE(emp.avg_salary,0),2) AS fallback_avg_salary,
               COALESCE(grad.graduate_count,0) AS fallback_graduate_count,
               ROUND(COALESCE(emp.high_quality_employment_rate,0),4) AS fallback_high_quality_employment_rate,
               ROUND(COALESCE(emp.leading_industry_rate,0),4) AS fallback_leading_industry_rate,
               emp.top_industry_name AS fallback_top_industry_name,
               COALESCE(b.covered_major_count,0) AS covered_major_count
        FROM dim_school s
        LEFT JOIN ads_school_compare_summary a
          ON a.school_id=s.school_id
         AND {join_filter}
        LEFT JOIN (
          SELECT school_id, COUNT(DISTINCT graduate_id) graduate_count
          FROM fact_graduate
          GROUP BY school_id
        ) grad ON grad.school_id=s.school_id
        LEFT JOIN (
          SELECT e.school_id,
                 COUNT(*) employment_sample_count,
                 AVG(e.salary) avg_salary,
                 AVG(CASE WHEN e.employment_quality_level='高' OR e.match_score>=82 THEN 1 ELSE 0 END) high_quality_employment_rate,
                 AVG(CASE WHEN e.is_shanghai_leading_employment=1 THEN 1 ELSE 0 END) leading_industry_rate,
                 SUBSTRING_INDEX(GROUP_CONCAT(i.industry_name ORDER BY cnt.industry_count DESC SEPARATOR ','), ',', 1) top_industry_name
          FROM fact_employment e
          LEFT JOIN dim_industry i ON e.industry_id=i.industry_id
          LEFT JOIN (
            SELECT school_id, industry_id, COUNT(*) industry_count
            FROM fact_employment
            GROUP BY school_id, industry_id
          ) cnt ON cnt.school_id=e.school_id AND cnt.industry_id=e.industry_id
          GROUP BY e.school_id
        ) emp ON emp.school_id=s.school_id
        LEFT JOIN (
          SELECT school_id, COUNT(DISTINCT major_code) covered_major_count
          FROM bridge_school_major
          GROUP BY school_id
        ) b ON b.school_id=s.school_id
        ORDER BY COALESCE(a.employment_count,0) DESC, s.school_name
        """,
        params,
    )
    advantage_map, advantage_diagnostics = public_advantage_major_map()
    schools = []
    for item in compare_rows:
        geo = PUBLIC_SCHOOL_GEO.get(item["school_name"], {})
        advantage_major = advantage_map.get(item["school_id"])
        display_major = public_display_major_for_school(item["school_name"])
        display_major_name = display_major.get("major_name") or "数据不足"
        display_major_source = display_major.get("source") or "no_business_config"
        display_major_obj = {
            "major_code": display_major.get("major_code"),
            "major_name": display_major_name,
            "source": display_major_source,
        } if display_major.get("major_name") else None
        advantage_major_name = display_major_name
        advantage_major_status = display_major_source
        schools.append({
            "school_id": item["school_id"],
            "school_name": item["school_name"],
            "district": geo.get("district", item.get("district") or ""),
            "address": geo.get("address", ""),
            "longitude": geo.get("longitude"),
            "latitude": geo.get("latitude"),
            "school_type": item.get("school_type", ""),
            "avg_salary": item.get("avg_salary") or item.get("fallback_avg_salary") or 0,
            "employment_sample_count": item.get("employment_count") or item.get("fallback_employment_sample_count") or 0,
            "graduate_count": item.get("graduate_count") or item.get("fallback_graduate_count") or 0,
            "covered_major_count": item.get("covered_major_count") or 0,
            "employment_rate": item.get("employment_rate") or 0,
            "high_quality_employment_rate": item.get("high_quality_employment_rate") or item.get("fallback_high_quality_employment_rate") or 0,
            "leading_industry_count": item.get("leading_industry_employment_count") or 0,
            "leading_industry_rate": item.get("leading_industry_rate") or item.get("fallback_leading_industry_rate") or 0,
            "top_industry_name": item.get("top_industry_name") or item.get("fallback_top_industry_name") or "",
            "display_major_name": display_major_name,
            "major_name": display_major_name,
            "major_code": display_major.get("major_code"),
            "display_major_source": display_major_source,
            "advantage_major": display_major_obj or advantage_major,
            "advantage_major_name": advantage_major_name,
            "advantage_major_status": advantage_major_status,
            "advantage_majors": [display_major_name] if display_major.get("major_name") else [],
            "industry_distribution": item.get("industry_distribution_json") or "[]",
        })
    if include_diagnostics:
        diagnostics = {
            "dim_school_count": int(one("SELECT COUNT(*) v FROM dim_school").get("v", 0) or 0),
            "school_count": len(schools),
            "school_level_rows_count": len(compare_rows),
            "schools_with_verified_major": sum(1 for item in schools if item.get("advantage_major")),
            "schools_without_verified_major": sum(1 for item in schools if not item.get("advantage_major")),
            **advantage_diagnostics,
        }
        return schools, diagnostics
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
    items, diagnostics = public_school_rows(major_code, include_diagnostics=True)
    return ok({"items": items, "diagnostics": diagnostics})


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
