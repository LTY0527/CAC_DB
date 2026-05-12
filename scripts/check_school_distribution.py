# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.connect() as conn:
        grad = [dict(r) for r in conn.execute(text("""
            SELECT s.school_id, s.school_name, COUNT(g.graduate_id) graduate_count
            FROM dim_school s LEFT JOIN fact_graduate g ON s.school_id=g.school_id
            GROUP BY s.school_id, s.school_name ORDER BY graduate_count DESC
        """)).mappings()]
        emp = [dict(r) for r in conn.execute(text("""
            SELECT s.school_id, s.school_name, COUNT(e.employment_id) employment_count
            FROM dim_school s LEFT JOIN fact_employment e ON s.school_id=e.school_id
            GROUP BY s.school_id, s.school_name ORDER BY employment_count DESC
        """)).mappings()]
        compare_count = conn.execute(text("SELECT COUNT(*) FROM ads_school_compare_summary")).scalar() or 0
        total_sample = conn.execute(text("""
            SELECT (SELECT COUNT(*) FROM fact_graduate)
                 + (SELECT COUNT(*) FROM fact_employment)
                 + (SELECT COUNT(*) FROM fact_job_posting)
        """)).scalar() or 0

    emp_vals = [int(r["employment_count"]) for r in emp if int(r["employment_count"]) > 0]
    max_min_ratio = max(emp_vals) / max(min(emp_vals), 1) if emp_vals else 0
    avg_emp = sum(emp_vals) / len(emp_vals) if emp_vals else 0
    shu_emp = next((int(r["employment_count"]) for r in emp if r["school_name"] == "上海大学"), 0)
    checks = [
        {"check": "每校就业样本最大/最小比例 <= 3", "passed": max_min_ratio <= 3, "value": round(max_min_ratio, 3), "expected": "<=3"},
        {"check": "上海大学就业样本不超过十校平均值 2 倍", "passed": shu_emp <= avg_emp * 2, "value": shu_emp, "expected": f"<={round(avg_emp * 2)}"},
        {"check": "全市数据底座总量 >= 100000", "passed": total_sample >= 100000, "value": int(total_sample), "expected": ">=100000"},
        {"check": "ads_school_compare_summary 已生成", "passed": compare_count > 0, "value": int(compare_count), "expected": ">0"},
    ]
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "graduate_distribution": grad,
        "employment_distribution": emp,
        "total_data_sample_count": int(total_sample),
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "SCHOOL_DISTRIBUTION_CHECK_REPORT.md").write_text(
        "# SCHOOL_DISTRIBUTION_CHECK_REPORT\n\n"
        + "\n".join(f"- [{'x' if c['passed'] else ' '}] {c['check']}: {c['value']}，期望 {c['expected']}" for c in checks)
        + "\n\n## Graduate Distribution\n\n"
        + "\n".join(f"- {r['school_name']}: {r['graduate_count']}" for r in grad)
        + "\n\n## Employment Distribution\n\n"
        + "\n".join(f"- {r['school_name']}: {r['employment_count']}" for r in emp),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
