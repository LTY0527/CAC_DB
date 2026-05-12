# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL


def serial(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    checks = []
    with engine.connect() as conn:
        school_count = conn.execute(text("SELECT COUNT(*) FROM dim_school")).scalar() or 0
        all_rows = [{k: serial(v) for k, v in dict(r).items()} for r in conn.execute(text("""
            SELECT school_name, employment_count, graduate_count, employment_rate,
                   avg_salary, high_quality_employment_rate, top_industry_name,
                   leading_industry_employment_count
            FROM ads_school_compare_summary
            WHERE major_code='ALL'
            ORDER BY employment_count DESC
        """)).mappings()]
        major_rows = conn.execute(text("SELECT COUNT(*) FROM ads_school_compare_summary WHERE major_code<>'ALL'")).scalar() or 0
        total_sample = conn.execute(text("""
            SELECT (SELECT COUNT(*) FROM fact_graduate)
                 + (SELECT COUNT(*) FROM fact_employment)
                 + (SELECT COUNT(*) FROM fact_job_posting)
        """)).scalar() or 0
        emp_vals = [int(r["employment_count"]) for r in all_rows if int(r["employment_count"] or 0) > 0]
        ratio = max(emp_vals) / max(min(emp_vals), 1) if emp_vals else 0
        checks.extend([
            {"check": "dim_school 是否为 10", "passed": school_count == 10, "value": int(school_count), "expected": "10"},
            {"check": "ads_school_compare_summary 是否有全专业数据", "passed": len(all_rows) == 10, "value": len(all_rows), "expected": "10"},
            {"check": "ads_school_compare_summary 是否有专业粒度数据", "passed": major_rows > 0, "value": int(major_rows), "expected": ">0"},
            {"check": "学校对标就业样本最大/最小比例不过大", "passed": ratio <= 3, "value": round(ratio, 3), "expected": "<=3"},
            {"check": "全市数据样本总量 >= 100000", "passed": total_sample >= 100000, "value": int(total_sample), "expected": ">=100000"},
            {"check": "学校对标分析接口数据源不为空", "passed": bool(all_rows), "value": len(all_rows), "expected": ">0"},
        ])
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "passed": all(item["passed"] for item in checks),
        "checks": checks,
        "school_compare_rows": all_rows,
        "total_data_sample_count": int(total_sample),
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "data" / "generated").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "GOVERNMENT_OVERVIEW_DATA_CHECK_REPORT.md").write_text(
        "# GOVERNMENT_OVERVIEW_DATA_CHECK_REPORT\n\n"
        + "\n".join(f"- [{'x' if c['passed'] else ' '}] {c['check']}: {c['value']}，期望 {c['expected']}" for c in checks)
        + "\n\n## School Compare Rows\n\n"
        + "\n".join(
            f"- {r['school_name']}: 就业样本 {r['employment_count']}，就业率 {float(r['employment_rate'] or 0):.2%}，平均薪资 {float(r['avg_salary'] or 0):.0f}，高质量就业占比 {float(r['high_quality_employment_rate'] or 0):.2%}，热门行业 {r['top_industry_name']}"
            for r in all_rows
        ),
        encoding="utf-8",
    )
    (ROOT / "data" / "generated" / "government_overview_data_check_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
