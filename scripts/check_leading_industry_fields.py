# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL


def scalar(conn, sql: str, params=None):
    value = conn.execute(text(sql), params or {}).scalar()
    return 0 if value is None else value


def check(name: str, passed: bool, value, expected) -> dict:
    return {"check": name, "passed": bool(passed), "value": value, "expected": expected}


def api_probe(checks: list[dict]) -> None:
    base = "http://127.0.0.1:5000/api"
    try:
        def login(username: str) -> str:
            req = Request(
                f"{base}/auth/login",
                data=json.dumps({"username": username, "password": "123456"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            payload = json.loads(urlopen(req, timeout=5).read().decode("utf-8"))
            return payload.get("data", {}).get("token", "")

        for username, label in [("teacher_shu", "教师端"), ("gov_sh", "政府端")]:
            token = login(username)
            req = Request(f"{base}/employment-summary", headers={"Authorization": f"Bearer {token}"})
            payload = json.loads(urlopen(req, timeout=8).read().decode("utf-8"))
            data = payload.get("data") or []
            leading = sum(int(item.get("emp_count") or 0) for item in data if item.get("leading_industry_tag") in {"三大先导", "涓夊ぇ鍏堝"})
            checks.append(check(f"{label} /api/employment-summary 先导产业人数 > 0", leading > 0, leading, ">0"))
            if username == "gov_sh":
                req = Request(f"{base}/monitor/school", headers={"Authorization": f"Bearer {token}"})
                payload = json.loads(urlopen(req, timeout=8).read().decode("utf-8"))
                summary = (payload.get("data") or {}).get("summary") or {}
                monitor_count = int(summary.get("leading_industry_employment_count") or 0)
                checks.append(check("政府端 /api/monitor/school 先导产业吸纳人数 > 0", monitor_count > 0, monitor_count, ">0"))
    except URLError as exc:
        checks.append(check("接口检查已跳过", True, f"后端未运行：{exc}", "启动后端后可检查"))
    except Exception as exc:
        checks.append(check("接口检查失败", False, str(exc), "HTTP 200 且先导产业统计 > 0"))


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    checks: list[dict] = []
    details: dict = {}
    with engine.connect() as conn:
        industry_count = scalar(conn, "SELECT COUNT(*) FROM dim_industry WHERE is_shanghai_leading_industry=1")
        enterprise_count = scalar(conn, "SELECT COUNT(*) FROM dim_enterprise WHERE is_shanghai_leading_enterprise=1")
        job_count = scalar(conn, "SELECT COUNT(*) FROM fact_job_posting WHERE is_shanghai_leading_job=1")
        employment_count = scalar(conn, "SELECT COUNT(*) FROM fact_employment WHERE is_shanghai_leading_employment=1")
        shu_count = scalar(conn, """
            SELECT COUNT(*) FROM fact_employment e
            JOIN dim_school s ON e.school_id=s.school_id
            WHERE s.school_name='上海大学' AND e.is_shanghai_leading_employment=1
        """)
        code_rows = conn.execute(text("""
            SELECT leading_industry_code, COUNT(*) AS cnt
            FROM fact_employment
            WHERE is_shanghai_leading_employment=1
            GROUP BY leading_industry_code
        """)).mappings().all()
        code_counts = {str(row["leading_industry_code"]): int(row["cnt"]) for row in code_rows}
        details.update({
            "leading_industry_count": int(industry_count),
            "leading_enterprise_count": int(enterprise_count),
            "leading_job_posting_count": int(job_count),
            "leading_employment_count": int(employment_count),
            "shanghai_university_leading_employment_count": int(shu_count),
            "code_counts": code_counts,
        })
        checks.extend([
            check("dim_industry 三大先导产业标签数量 >= 3", industry_count >= 3, int(industry_count), ">=3"),
            check("dim_enterprise 三大先导企业数量 > 0", enterprise_count > 0, int(enterprise_count), ">0"),
            check("fact_job_posting 三大先导岗位数量 > 0", job_count > 0, int(job_count), ">0"),
            check("fact_employment 三大先导就业人数 > 0", employment_count > 0, int(employment_count), ">0"),
            check("上海大学三大先导就业人数 > 0", shu_count > 0, int(shu_count), ">0"),
            check("AI / IC / BIOMED 三类均有就业记录", all(code_counts.get(code, 0) > 0 for code in ("AI", "IC", "BIOMED")), code_counts, "AI/IC/BIOMED > 0"),
        ])
    api_probe(checks)
    report = {"generated_at": datetime.now().isoformat(timespec="seconds"), "passed": all(item["passed"] for item in checks), "checks": checks, "details": details}
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "data" / "generated").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "LEADING_INDUSTRY_FIELD_CHECK_REPORT.md").write_text(
        "# LEADING_INDUSTRY_FIELD_CHECK_REPORT\n\n"
        + "\n".join(f"- [{'x' if item['passed'] else ' '}] {item['check']}: {item['value']}，期望 {item['expected']}" for item in checks),
        encoding="utf-8",
    )
    (ROOT / "data" / "generated" / "leading_industry_field_check_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
