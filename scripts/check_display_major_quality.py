# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL  # noqa: E402
from scripts.major_display_policy import is_valid_display_major_name  # noqa: E402

REPORT_MD = ROOT / "docs" / "DISPLAY_MAJOR_QUALITY_CHECK_REPORT.md"
REPORT_JSON = ROOT / "data" / "generated" / "display_major_quality_check_report.json"


def configure_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def rows(conn, sql: str, params=None) -> list[dict]:
    return [dict(row) for row in conn.execute(text(sql), params or {}).mappings()]


def scalar(conn, sql: str, params=None):
    return conn.execute(text(sql), params or {}).scalar()


def api_get(path: str) -> dict:
    from app import app, make_token

    token = make_token({"user_id": 0, "username": "quality_check", "role": "government", "role_db": "government"})
    with app.test_client() as client:
        resp = client.get(path, headers={"Authorization": f"Bearer {token}"})
        return {"status": resp.status_code, "payload": resp.get_json(silent=True) or {}}


def invalid_names(names: list[str]) -> list[str]:
    return [name for name in names if not is_valid_display_major_name(name) or re.search(r"\d+$", str(name or ""))]


def main() -> None:
    configure_utf8()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    report: dict[str, object] = {}

    with engine.connect() as conn:
        report["major_catalog_count"] = scalar(conn, "SELECT COUNT(*) FROM dim_major_catalog")
        report["real_display_major_count"] = scalar(conn, "SELECT COUNT(*) FROM dim_major_catalog WHERE is_real_display_major=1")
        report["catalog_placeholder_count"] = scalar(conn, "SELECT COUNT(*) FROM dim_major_catalog WHERE is_catalog_placeholder=1")
        report["bridge_placeholder_count"] = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM bridge_school_major b
            JOIN dim_major_catalog m ON b.major_code=m.major_code
            WHERE COALESCE(m.is_catalog_placeholder,0)=1
               OR COALESCE(m.is_real_display_major,0)<>1
               OR m.major_name REGEXP '[0-9]$'
            """,
        )
        report["employment_placeholder_count"] = scalar(
            conn,
            """
            SELECT COUNT(*)
            FROM fact_employment e
            JOIN dim_major_catalog m ON e.major_code=m.major_code
            WHERE COALESCE(m.is_catalog_placeholder,0)=1
               OR COALESCE(m.is_real_display_major,0)<>1
               OR m.major_name REGEXP '[0-9]$'
            """,
        )
        report["fact_graduate_count"] = scalar(conn, "SELECT COUNT(*) FROM fact_graduate")
        report["fact_employment_count"] = scalar(conn, "SELECT COUNT(*) FROM fact_employment")
        report["fact_job_posting_count"] = scalar(conn, "SELECT COUNT(*) FROM fact_job_posting")
        report["school_employment_distribution"] = rows(
            conn,
            """
            SELECT s.school_name, COUNT(e.employment_id) AS employment_count
            FROM dim_school s
            LEFT JOIN fact_employment e ON s.school_id=e.school_id
            GROUP BY s.school_id, s.school_name
            ORDER BY s.school_id
            """,
        )
        counts = [int(item["employment_count"] or 0) for item in report["school_employment_distribution"]]
        report["school_employment_max_min_ratio"] = round(max(counts) / max(min(counts), 1), 3) if counts else 0
        report["public_school_comparison_invalid_names"] = invalid_names([
            item["major_name"]
            for item in rows(
                conn,
                """
                SELECT a.major_name
                FROM ads_school_compare_summary a
                JOIN dim_major_catalog m ON a.major_code=m.major_code
                WHERE a.major_code <> 'ALL'
                  AND (COALESCE(m.is_catalog_placeholder,0)=1 OR COALESCE(m.is_real_display_major,0)<>1 OR m.major_name REGEXP '[0-9]$')
                LIMIT 20
                """,
            )
        ])

    salary_api = api_get("/api/public/salary-ranking?limit=10")
    salary_items = salary_api.get("payload", {}).get("data", {}).get("items", [])
    warning_api = api_get("/api/monitor/school")
    warning_items = warning_api.get("payload", {}).get("data", {}).get("items", [])
    government_api = api_get("/api/government/school-comparison")
    gov_data = government_api.get("payload", {}).get("data", {})
    gov_items = gov_data.get("items", [])
    report["public_salary_ranking_status"] = salary_api["status"]
    report["public_salary_ranking_names"] = [item.get("major_name") for item in salary_items]
    report["public_salary_ranking_invalid_names"] = invalid_names(report["public_salary_ranking_names"])
    report["government_warning_status"] = warning_api["status"]
    report["government_warning_names"] = [item.get("target_name") for item in warning_items]
    report["government_warning_invalid_names"] = invalid_names(report["government_warning_names"])
    report["government_sample_count"] = gov_data.get("summary", {}).get("total_employment_count")
    report["government_school_comparison_status"] = government_api["status"]
    report["government_school_comparison_count"] = len(gov_items)

    report["passed"] = (
        report["major_catalog_count"] == 845
        and report["real_display_major_count"] >= 100
        and report["bridge_placeholder_count"] == 0
        and report["fact_employment_count"] >= 100000
        and report["fact_graduate_count"] >= 120000
        and report["fact_job_posting_count"] >= 120000
        and report["school_employment_max_min_ratio"] <= 2
        and not report["public_salary_ranking_invalid_names"]
        and not report["government_warning_invalid_names"]
        and int(report.get("government_sample_count") or 0) >= 100000
    )

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 展示专业质量与就业样本检查报告",
        "",
        f"- 结论：{'通过' if report['passed'] else '未通过'}",
        f"- dim_major_catalog：{report['major_catalog_count']}",
        f"- 真实展示专业数：{report['real_display_major_count']}",
        f"- 目录占位专业数：{report['catalog_placeholder_count']}",
        f"- bridge_school_major 占位专业数：{report['bridge_placeholder_count']}",
        f"- fact_employment：{report['fact_employment_count']}",
        f"- fact_graduate：{report['fact_graduate_count']}",
        f"- fact_job_posting：{report['fact_job_posting_count']}",
        f"- 最大/最小学校就业样本比：{report['school_employment_max_min_ratio']}",
        f"- 政府端全市就业样本：{report['government_sample_count']}",
        "",
        "## 十校就业样本分布",
    ]
    for item in report["school_employment_distribution"]:
        lines.append(f"- {item['school_name']}：{item['employment_count']}")
    lines.extend([
        "",
        "## 高薪专业 Top10",
        *[f"- {name}" for name in report["public_salary_ranking_names"]],
        "",
        "## 区域预警专业",
        *[f"- {name}" for name in report["government_warning_names"]],
        "",
        "## 异常项",
        f"- 高薪榜异常专业：{report['public_salary_ranking_invalid_names'] or '无'}",
        f"- 区域预警异常专业：{report['government_warning_invalid_names'] or '无'}",
        f"- 学校对比 ADS 异常专业样例：{report['public_school_comparison_invalid_names'] or '无'}",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"报告已生成: {REPORT_MD}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
