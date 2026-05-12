from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import app

DOC_PATH = ROOT / "docs" / "PUBLIC_PORTAL_DATA_CHECK_REPORT.md"
JSON_PATH = ROOT / "data" / "generated" / "public_portal_data_check_report.json"


def check_item(name: str, passed: bool, value, expected: str) -> dict:
    return {"check": name, "passed": bool(passed), "value": value, "expected": expected}


def main() -> int:
    client = app.app.test_client()
    token = app.make_token({
        "user_id": "public-check",
        "username": "public-check",
        "role": "public",
        "role_db": "public",
        "school_id": None,
    })
    headers = {"Authorization": f"Bearer {token}"}

    overview_resp = client.get("/api/public/overview", headers=headers)
    overview_json = overview_resp.get_json() or {}
    overview_data = overview_json.get("data") or {}
    summary = overview_data.get("summary") or {}
    schools = overview_data.get("schools") or []

    comparison_resp = client.get("/api/public/school-comparison", headers=headers)
    comparison_json = comparison_resp.get_json() or {}
    comparison_items = (comparison_json.get("data") or {}).get("items") or []

    school_names = [item.get("school_name") for item in schools if item.get("school_name")]
    checks = [
        check_item("public overview HTTP 状态", overview_resp.status_code == 200, overview_resp.status_code, "200"),
        check_item("public overview code", overview_json.get("code") == 0, overview_json.get("code"), "0"),
        check_item("summary.school_count 是否为 10", summary.get("school_count") == 10, summary.get("school_count"), "10"),
        check_item("schools 数组长度是否为 10", len(schools) == 10, len(schools), "10"),
        check_item("每所学校是否有 school_name", len(school_names) == 10, len(school_names), "10"),
        check_item("每所学校是否有 avg_salary", all(float(item.get("avg_salary") or 0) > 0 for item in schools), "ok", ">0"),
        check_item("每所学校是否有 employment_sample_count", all(int(item.get("employment_sample_count") or 0) > 0 for item in schools), "ok", ">0"),
        check_item("每所学校是否有 covered_major_count", all(int(item.get("covered_major_count") or 0) > 0 for item in schools), "ok", ">0"),
        check_item("每所学校是否有 longitude / latitude", all(item.get("longitude") and item.get("latitude") for item in schools), "ok", "非空"),
        check_item("public school comparison 是否返回多所高校", len(comparison_items) >= 10, len(comparison_items), ">=10"),
    ]

    frontend_path = ROOT / "frontend" / "src" / "pages" / "PublicWorkspace.jsx"
    frontend_text = frontend_path.read_text(encoding="utf-8", errors="ignore") if frontend_path.exists() else ""
    selected_school_risk = "selectedSchool ? 1" in frontend_text or "selectedSchool?1" in frontend_text
    checks.append(check_item("前端是否存在 selectedSchool 导致覆盖高校数为 1 的明显逻辑", not selected_school_risk, selected_school_risk, "False"))

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "summary": summary,
        "schools": schools,
        "comparison_count": len(comparison_items),
    }

    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = ["# PUBLIC_PORTAL_DATA_CHECK_REPORT", ""]
    for item in checks:
        mark = "x" if item["passed"] else " "
        lines.append(f"- [{mark}] {item['check']}: {item['value']}，期望 {item['expected']}")
    lines.extend(["", "## Schools", ""])
    for item in schools:
        lines.append(
            f"- {item.get('school_name')}: 就业样本 {item.get('employment_sample_count')}，"
            f"平均薪资 {item.get('avg_salary')}，覆盖专业 {item.get('covered_major_count')}，"
            f"坐标 {item.get('longitude')}, {item.get('latitude')}"
        )
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
