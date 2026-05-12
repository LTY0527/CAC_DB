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

from config import DB_URL


def scalar(conn, sql: str, default=0, params=None):
    try:
        value = conn.execute(text(sql), params or {}).scalar()
        return default if value is None else value
    except Exception:
        return default


def table_exists(conn, table: str) -> bool:
    return bool(
        scalar(
            conn,
            "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:table",
            0,
            {"table": table},
        )
    )


def check(name, passed, value, expected):
    return {"check": name, "passed": bool(passed), "value": value, "expected": expected}


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    checks = []
    with engine.connect() as conn:
        school_count = scalar(conn, "SELECT COUNT(*) FROM dim_school")
        checks.append(check("dim_school 是否正好 10 所上海高校", school_count == 10, school_count, "10"))
        has_shu = scalar(conn, "SELECT COUNT(*) FROM dim_school WHERE school_name='上海大学'")
        checks.append(check("dim_school 是否包含上海大学", has_shu == 1, has_shu, "1"))
        major_count = scalar(conn, "SELECT COUNT(*) FROM dim_major_catalog")
        checks.append(check("dim_major_catalog 是否为 845 条", major_count == 845, major_count, "845"))
        disc_count = scalar(conn, "SELECT COUNT(DISTINCT discipline_category) FROM dim_major_catalog")
        checks.append(check("dim_major_catalog 是否覆盖 12 个学科门类", disc_count == 12, disc_count, "12"))
        class_count = scalar(conn, "SELECT COUNT(DISTINCT major_class) FROM dim_major_catalog")
        checks.append(check("dim_major_catalog 是否覆盖 93 个专业类", class_count == 93, class_count, "93"))
        ace_schools = scalar(conn, "SELECT COUNT(DISTINCT school_id) FROM bridge_school_major WHERE is_ace_major=1")
        checks.append(check("bridge_school_major 是否为每所高校生成真实优势专业", ace_schools == 10, ace_schools, "10"))
        posting_count = scalar(conn, "SELECT COUNT(*) FROM fact_job_posting")
        checks.append(check("fact_job_posting 是否大于等于 80000 条", posting_count >= 80000, posting_count, ">=80000"))
        comp_ratio = float(scalar(conn, "SELECT AVG(computer_related) FROM dim_job_category", 1))
        checks.append(check("计算机相关岗位占比是否小于等于 25%", comp_ratio <= 0.25, round(comp_ratio, 4), "<=0.25"))
        non_comp_industry = scalar(conn, "SELECT COUNT(DISTINCT industry_id) FROM dim_job_category WHERE computer_related=0")
        checks.append(check("非计算机岗位是否覆盖至少 15 个行业", non_comp_industry >= 15, non_comp_industry, ">=15"))
        emp_rate_spread = float(scalar(conn, """
            SELECT MAX(rate)-MIN(rate) FROM (
              SELECT g.school_id, COUNT(e.employment_id) / COUNT(g.graduate_id) AS rate
              FROM fact_graduate g LEFT JOIN fact_employment e ON e.graduate_id=g.graduate_id
              GROUP BY g.school_id
            ) x
        """))
        checks.append(check("就业率是否分布合理而非全部接近 100%", emp_rate_spread > 0.02, round(emp_rate_spread, 4), ">0.02 spread"))
        salary_spread = float(scalar(conn, "SELECT STDDEV(avg_salary) FROM (SELECT school_id, major_code, AVG(salary) avg_salary FROM fact_employment GROUP BY school_id, major_code) x"))
        checks.append(check("平均薪资是否按学校、专业、行业有差异", salary_spread > 900, round(salary_spread, 2), ">900"))
        season_ratio = float(scalar(conn, "SELECT MAX(total_demand)/NULLIF(MIN(total_demand),0) FROM (SELECT month, SUM(demand_count) total_demand FROM fact_job_posting GROUP BY month) x"))
        checks.append(check("岗位需求曲线是否存在季节波动", season_ratio > 1.25, round(season_ratio, 3), ">1.25"))

        if table_exists(conn, "ads_job_demand_forecast") and scalar(conn, "SELECT COUNT(*) FROM ads_job_demand_forecast") > 0:
            neg = scalar(conn, "SELECT COUNT(*) FROM ads_job_demand_forecast WHERE predicted_demand_count < 0")
            checks.append(check("预测结果是否不存在负数", neg == 0, neg, "0"))
            mape = float(scalar(conn, "SELECT ROUND(AVG(mape),2) FROM ads_job_demand_forecast"))
            checks.append(check("MAPE 是否在合理范围", 12 <= mape <= 28, mape, "12-28"))
        if table_exists(conn, "ads_enrollment_matching") and scalar(conn, "SELECT COUNT(*) FROM ads_enrollment_matching") > 0:
            precision = float(scalar(conn, "SELECT AVG(precision_at_k) FROM ads_enrollment_matching"))
            checks.append(check("Precision@K 是否不为 0", precision > 0, round(precision, 4), ">0"))
        if table_exists(conn, "ads_training_rules") and scalar(conn, "SELECT COUNT(*) FROM ads_training_rules") > 0:
            evidence_distinct = scalar(conn, "SELECT COUNT(DISTINCT ROUND(evidence_score,2)) FROM ads_training_rules")
            checks.append(check("高价值规则 evidence_score 是否不是全部相同", evidence_distinct > 1, evidence_distinct, ">1"))
        if table_exists(conn, "ads_major_optimization") and scalar(conn, "SELECT COUNT(*) FROM ads_major_optimization") > 0:
            total = scalar(conn, "SELECT COUNT(DISTINCT school_id, major_code) FROM ads_major_optimization")
            primary_sum = scalar(conn, "SELECT COUNT(*) FROM ads_major_optimization WHERE primary_suggestion_type IN ('expand','stable','shrink','practice','support')")
            type_count = scalar(conn, "SELECT COUNT(DISTINCT primary_suggestion_type) FROM ads_major_optimization")
            checks.append(check("专业结构调整建议是否包含五类主建议且口径一致", total == primary_sum and type_count >= 5, {"total": total, "primary_sum": primary_sum, "types": type_count}, "五类且总数一致"))

        if table_exists(conn, "fact_employment"):
            emp_columns = {
                row[0]
                for row in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='fact_employment'"))
            }
            if "is_shanghai_leading_employment" in emp_columns:
                leading_emp = scalar(conn, "SELECT COUNT(*) FROM fact_employment WHERE is_shanghai_leading_employment=1")
                shu_leading_emp = scalar(conn, """
                    SELECT COUNT(*) FROM fact_employment e
                    JOIN dim_school s ON e.school_id=s.school_id
                    WHERE s.school_name='????' AND e.is_shanghai_leading_employment=1
                """)
                checks.append(check("?????????????? 0", leading_emp > 0, leading_emp, ">0"))
                checks.append(check("?????????????????? 0", shu_leading_emp > 0, shu_leading_emp, ">0"))

    source_text = ""
    for path in (ROOT / "frontend" / "src").rglob("*"):
        if path.is_file() and path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
            source_text += path.read_text(encoding="utf-8", errors="ignore") + "\n"
    mock_hits = len(re.findall(r"mockData|assets/mock|fakeData|demoData|hardcoded", source_text, flags=re.I))
    salary_hits = len(re.findall(r"salary_forecast|salaryForecast", source_text, flags=re.I))
    checks.append(check("是否存在明显硬编码 mock 数据", mock_hits == 0, mock_hits, "0"))
    checks.append(check("是否存在旧版 salary prediction 主逻辑残留", salary_hits == 0, salary_hits, "0"))

    report = {"generated_at": __import__("datetime").datetime.now().isoformat(), "passed": all(item["passed"] for item in checks), "checks": checks}
    (ROOT / "DATA_QUALITY_REPORT.md").write_text(
        "# DATA_QUALITY_REPORT\n\n" + "\n".join([f"- [{'x' if c['passed'] else ' '}] {c['check']}: {c['value']}，期望 {c['expected']}" for c in checks]),
        encoding="utf-8",
    )
    out_json = ROOT / "data" / "generated" / "data_quality_db_report.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
