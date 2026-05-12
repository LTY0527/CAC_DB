# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL  # noqa: E402
from scripts.major_display_policy import is_valid_display_major_name  # noqa: E402


REPORT_MD = ROOT / "docs" / "MAJOR_DISPLAY_NAME_CHECK_REPORT.md"
REPORT_JSON = ROOT / "data" / "generated" / "major_display_name_check_report.json"


def configure_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def scalar(conn, sql: str, params=None):
    return conn.execute(text(sql), params or {}).scalar()


def fetch_salary_ranking() -> dict:
    from app import app, make_token

    with app.test_client() as client:
        token = make_token({"user_id": 0, "username": "public_check", "role": "public", "role_db": "public"})
        response = client.get("/api/public/salary-ranking?limit=10", headers={"Authorization": f"Bearer {token}"})
        return {"status": response.status_code, "payload": response.get_json(silent=True) or {}}


def main() -> None:
    configure_utf8()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    checks: dict[str, object] = {}
    with engine.connect() as conn:
        columns = {row._mapping["Field"] for row in conn.execute(text("SHOW COLUMNS FROM dim_major_catalog"))}
        checks["major_catalog_count"] = scalar(conn, "SELECT COUNT(*) FROM dim_major_catalog")
        checks["required_display_columns_present"] = all(
            name in columns
            for name in [
                "is_real_display_major",
                "is_catalog_placeholder",
                "display_priority",
                "salary_rank_weight",
                "industry_trend_tags",
            ]
        )
        checks["numeric_suffix_major_count"] = scalar(
            conn,
            "SELECT COUNT(*) FROM dim_major_catalog WHERE major_name REGEXP '[0-9]$'",
        )
        checks["numeric_suffix_placeholder_count"] = scalar(
            conn,
            """
            SELECT COUNT(*) FROM dim_major_catalog
            WHERE major_name REGEXP '[0-9]$' AND COALESCE(is_catalog_placeholder, 0) = 1
            """,
        ) if checks["required_display_columns_present"] else 0
        checks["real_display_major_count"] = scalar(
            conn,
            "SELECT COUNT(*) FROM dim_major_catalog WHERE COALESCE(is_real_display_major, 0) = 1",
        ) if checks["required_display_columns_present"] else 0

    ranking_response = fetch_salary_ranking()
    payload = ranking_response["payload"]
    data = payload.get("data") if isinstance(payload, dict) else {}
    items = data.get("items", []) if isinstance(data, dict) else []
    checks["public_salary_ranking_http_status"] = ranking_response["status"]
    checks["public_salary_ranking_code"] = payload.get("code") if isinstance(payload, dict) else None
    checks["public_salary_ranking_count"] = len(items)
    checks["public_salary_ranking_names"] = [item.get("major_name") for item in items]
    checks["public_salary_ranking_invalid_names"] = [
        item.get("major_name") for item in items if not is_valid_display_major_name(item.get("major_name"))
    ]
    checks["public_salary_ranking_low_sample_items"] = [
        item.get("major_name") for item in items if int(item.get("sample_count") or 0) < 30
    ]
    checks["public_salary_ranking_trend_item_count"] = sum(1 for item in items if item.get("industry_trend_tags"))

    passed = (
        checks["major_catalog_count"] == 845
        and checks["required_display_columns_present"]
        and checks["numeric_suffix_major_count"] == checks["numeric_suffix_placeholder_count"]
        and checks["public_salary_ranking_http_status"] == 200
        and checks["public_salary_ranking_code"] == 0
        and checks["public_salary_ranking_count"] == 10
        and not checks["public_salary_ranking_invalid_names"]
        and not checks["public_salary_ranking_low_sample_items"]
        and checks["public_salary_ranking_trend_item_count"] >= 5
    )
    checks["passed"] = passed

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# 专业展示名称与高薪榜单检查报告",
        "",
        f"- 结论：{'通过' if passed else '未通过'}",
        f"- dim_major_catalog 行数：{checks['major_catalog_count']}",
        f"- 展示字段是否齐全：{checks['required_display_columns_present']}",
        f"- 数字后缀专业数：{checks['numeric_suffix_major_count']}",
        f"- 已标记为目录占位的数字后缀专业数：{checks['numeric_suffix_placeholder_count']}",
        f"- 真实展示专业数：{checks['real_display_major_count']}",
        f"- 公众高薪榜 HTTP 状态：{checks['public_salary_ranking_http_status']}",
        f"- 公众高薪榜返回条数：{checks['public_salary_ranking_count']}",
        "",
        "## 高薪专业 Top10",
    ]
    for item in items:
        tags = "、".join(item.get("industry_trend_tags") or [])
        lines.append(
            f"{item.get('rank')}. {item.get('major_name')}，平均薪资 {item.get('avg_salary')}，样本量 {item.get('sample_count')}，趋势标签：{tags or '无'}"
        )
    lines.extend([
        "",
        "## 异常项",
        f"- 高薪榜异常名称：{checks['public_salary_ranking_invalid_names'] or '无'}",
        f"- 样本量低于阈值项：{checks['public_salary_ranking_low_sample_items'] or '无'}",
    ])
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"报告已生成: {REPORT_MD}")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
