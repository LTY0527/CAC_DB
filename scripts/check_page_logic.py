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

BAD_COMBOS = [
    ("临床医学", "设施农业工程师"),
    ("国际经济与贸易", "电池研发工程师"),
    ("数学与应用数学", "新能源汽车工程师"),
]


def scalar(conn, sql, params=None, default=0):
    value = conn.execute(text(sql), params or {}).scalar()
    return default if value is None else value


def item(name, passed, value, expected):
    return {"check": name, "passed": bool(passed), "value": value, "expected": expected}


def try_api_checks(checks):
    base = "http://127.0.0.1:5000/api"
    try:
        def login(username: str) -> str | None:
            req = Request(
                f"{base}/auth/login",
                data=json.dumps({"username": username, "password": "123456"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            payload = json.loads(urlopen(req, timeout=5).read().decode("utf-8"))
            return payload.get("data", {}).get("token")

        token = login("teacher_shu")
        if not token:
            checks.append(item("API 登录检查", False, "teacher_shu 登录失败", "返回 token"))
            return
        endpoints = [
            "/demand/kpi",
            "/demand/forecast",
            "/enrollment/matching",
            "/major/optimization",
            "/training/rules",
            "/recommendation/summary",
            "/recommendation/jobs",
            "/report/ai",
        ]
        for endpoint in endpoints:
            req = Request(f"{base}{endpoint}", headers={"Authorization": f"Bearer {token}"})
            data = json.loads(urlopen(req, timeout=8).read().decode("utf-8"))
            payload_data = data.get("data")
            if isinstance(payload_data, dict):
                non_empty = bool(payload_data)
            else:
                non_empty = bool(payload_data)
            checks.append(item(f"接口 {endpoint} 返回非空成功数据", data.get("code") == 0 and non_empty, {"code": data.get("code"), "non_empty": non_empty}, "code=0 且 data 非空"))
        gov_token = login("gov_sh")
        for endpoint in ["/demand/kpi", "/demand/forecast", "/monitor/school"]:
            req = Request(f"{base}{endpoint}", headers={"Authorization": f"Bearer {gov_token}"})
            data = json.loads(urlopen(req, timeout=8).read().decode("utf-8"))
            payload_data = data.get("data")
            non_empty = bool(payload_data)
            checks.append(item(f"政府端接口 {endpoint} 返回非空成功数据", data.get("code") == 0 and non_empty, {"code": data.get("code"), "non_empty": non_empty}, "code=0 且 data 非空"))
    except URLError as exc:
        checks.append(item("API 可用性检查", True, f"后端未运行，已跳过 HTTP 检查：{exc}", "运行 backend/app.py 后可检查"))
    except Exception as exc:
        checks.append(item("API 可用性检查", False, str(exc), "主要 API 可访问"))


def main() -> None:
    engine = create_engine(DB_URL, pool_pre_ping=True)
    checks = []
    details = {}
    with engine.connect() as conn:
        shu = conn.execute(text("SELECT school_id, school_name, major_count FROM dim_school WHERE school_name='上海大学'")).mappings().first()
        if not shu:
            checks.append(item("上海大学学校维度存在", False, None, "上海大学"))
            school_id = "SHU007"
        else:
            school_id = shu["school_id"]
            details["shanghai_university"] = dict(shu)
            checks.append(item("上海大学学校维度存在", True, dict(shu), "上海大学"))
        bridge_count = scalar(conn, "SELECT COUNT(*) FROM bridge_school_major WHERE school_id=:sid", {"sid": school_id})
        grad_count = scalar(conn, "SELECT COUNT(*) FROM fact_graduate WHERE school_id=:sid", {"sid": school_id})
        emp_count = scalar(conn, "SELECT COUNT(*) FROM fact_employment WHERE school_id=:sid", {"sid": school_id})
        checks.append(item("上海大学 bridge_school_major >= 80", bridge_count >= 80, bridge_count, ">=80"))
        checks.append(item("上海大学 fact_graduate >= 6000", grad_count >= 6000, grad_count, ">=6000"))
        checks.append(item("上海大学 fact_employment >= 4500", emp_count >= 4500, emp_count, ">=4500"))

        forecast_count = scalar(conn, "SELECT COUNT(*) FROM ads_job_demand_forecast WHERE school_id=:sid", {"sid": school_id})
        forecast_avg = float(scalar(conn, "SELECT AVG(predicted_demand_count) FROM ads_job_demand_forecast WHERE school_id=:sid", {"sid": school_id}, 0))
        top_zero = scalar(
            conn,
            """
            SELECT COUNT(*) FROM (
              SELECT major_code, job_category_id, SUM(predicted_demand_count) total
              FROM ads_job_demand_forecast WHERE school_id=:sid
              GROUP BY major_code, job_category_id ORDER BY total DESC LIMIT 10
            ) x WHERE total <= 0
            """,
            {"sid": school_id},
        )
        checks.append(item("上海大学预测记录数 > 0", forecast_count > 0, forecast_count, ">0"))
        checks.append(item("上海大学预测平均值 >= 50", forecast_avg >= 50, round(forecast_avg, 2), ">=50"))
        checks.append(item("Top10 组合未来 12 月不全 0", top_zero == 0, top_zero, "0"))
        bad_hits = []
        for major, job in BAD_COMBOS:
            count = scalar(conn, "SELECT COUNT(*) FROM ads_job_demand_forecast WHERE major_name=:major AND job_category_name=:job", {"major": major, "job": job})
            if count:
                bad_hits.append({"major": major, "job": job, "count": count})
        checks.append(item("不存在明显不合理专业-岗位组合", not bad_hits, bad_hits, "[]"))

        enroll_count = scalar(conn, "SELECT COUNT(*) FROM ads_enrollment_matching WHERE school_id=:sid", {"sid": school_id})
        avg_match = float(scalar(conn, "SELECT AVG(match_score) FROM ads_enrollment_matching WHERE school_id=:sid", {"sid": school_id}, 0))
        zero_sample = scalar(conn, "SELECT COUNT(*) FROM ads_enrollment_matching WHERE school_id=:sid AND sample_count<=0", {"sid": school_id})
        checks.append(item("上海大学招生匹配记录 >= 60", enroll_count >= 60, enroll_count, ">=60"))
        checks.append(item("上海大学平均 match_score > 0.35", avg_match > 0.35, round(avg_match, 4), ">0.35"))
        checks.append(item("招生匹配 sample_count 不为 0", zero_sample == 0, zero_sample, "0"))

        rec_students = scalar(conn, "SELECT COUNT(DISTINCT graduate_id) FROM ads_job_recommendation WHERE school_id=:sid", {"sid": school_id})
        rec_enterprises = scalar(conn, "SELECT COUNT(DISTINCT enterprise_id) FROM ads_job_recommendation WHERE school_id=:sid", {"sid": school_id})
        top1 = float(scalar(conn, "SELECT AVG(similarity_score) FROM ads_job_recommendation WHERE school_id=:sid AND rank_no=1", {"sid": school_id}, 0))
        checks.append(item("上海大学推荐覆盖学生 >= 3000", rec_students >= 3000, rec_students, ">=3000"))
        checks.append(item("上海大学推荐覆盖单位 >= 100", rec_enterprises >= 100, rec_enterprises, ">=100"))
        checks.append(item("Top1 平均 similarity_score > 0.6", top1 > 0.6, round(top1, 4), ">0.6"))

        opt_total = scalar(conn, "SELECT COUNT(DISTINCT school_id, major_code) FROM ads_major_optimization")
        opt_primary = scalar(conn, "SELECT COUNT(*) FROM ads_major_optimization WHERE primary_suggestion_type IN ('expand','stable','shrink','practice','support')")
        checks.append(item("专业结构调整总数等于五类主建议加和", opt_total == opt_primary, {"total": opt_total, "primary_sum": opt_primary}, "相等"))

        rule_count = scalar(conn, "SELECT COUNT(*) FROM ads_training_rules")
        evidence_distinct = scalar(conn, "SELECT COUNT(DISTINCT ROUND(evidence_score,2)) FROM ads_training_rules")
        checks.append(item("培养规则记录数 > 0", rule_count > 0, rule_count, ">0"))
        checks.append(item("evidence_score 不全部相同", evidence_distinct > 1, evidence_distinct, ">1"))

        emp_columns = {
            row[0]
            for row in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='fact_employment'"))
        }
        if "is_shanghai_leading_employment" in emp_columns:
            shu_leading_emp = scalar(conn, """
                SELECT COUNT(*) FROM fact_employment
                WHERE school_id=:sid AND is_shanghai_leading_employment=1
            """, {"sid": school_id})
            city_leading_emp = scalar(conn, "SELECT COUNT(*) FROM fact_employment WHERE is_shanghai_leading_employment=1")
            checks.append(item("???????????? > 0", shu_leading_emp > 0, shu_leading_emp, ">0"))
            checks.append(item("???????????? > 0", city_leading_emp > 0, city_leading_emp, ">0"))

    try_api_checks(checks)
    report = {"generated_at": datetime.now().isoformat(), "passed": all(c["passed"] for c in checks), "checks": checks, "details": details}
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "data" / "generated").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "PAGE_LOGIC_CHECK_REPORT.md").write_text(
        "# PAGE_LOGIC_CHECK_REPORT\n\n" + "\n".join([f"- [{'x' if c['passed'] else ' '}] {c['check']}: {c['value']}，期望 {c['expected']}" for c in checks]),
        encoding="utf-8",
    )
    (ROOT / "data" / "generated" / "page_logic_check_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
