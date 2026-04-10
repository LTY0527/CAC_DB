from pathlib import Path
import sys
from datetime import date, datetime
from decimal import Decimal
import math
from statistics import median
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent
for path in (str(BACKEND_DIR), str(ROOT_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from config import DB_URL  # noqa: E402
from prompt_builder import build_report_prompt  # noqa: E402
from llm_client import call_llm  # noqa: E402


app = Flask(__name__)
CORS(app)

DB_ENGINE = create_engine(DB_URL, pool_pre_ping=True)
TXT_STRATEGIC = "\u4e09\u5927\u5148\u5bfc"


def serialize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def fetch_rows(sql: str, params=None):
    with DB_ENGINE.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return [
            {key: serialize_value(value) for key, value in row.items()}
            for row in result.mappings()
        ]


def success_response(data):
    return jsonify({"success": True, "data": data})


def severity_weight(level: str) -> int:
    return {"高": 3, "中": 2, "低": 1}.get(level, 0)


def build_warning_summary(items):
    return {
        "high": sum(1 for item in items if item.get("warning_level") == "高"),
        "medium": sum(1 for item in items if item.get("warning_level") == "中"),
        "low": sum(1 for item in items if item.get("warning_level") == "低"),
        "total": len(items),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_regional_warnings():
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    warnings = []

    heat_rows = fetch_rows(
        """
        SELECT
            major_name,
            ROUND(AVG(matching_score), 4) AS avg_match_score,
            SUM(sample_size) AS total_sample_size
        FROM ads_enrollment_matching
        GROUP BY major_name
        HAVING SUM(sample_size) >= 10
        """
    )
    forecast_rows = fetch_rows(
        """
        SELECT major_name, forecast_month, predicted_salary
        FROM ads_salary_forecast
        ORDER BY major_name, forecast_month
        """
    )
    forecast_map = {}
    for row in forecast_rows:
        major_name = row.get("major_name")
        if not major_name:
            continue
        forecast_map.setdefault(major_name, []).append(float(row.get("predicted_salary") or 0))

    heat_candidates = []
    for row in heat_rows:
        major_name = row.get("major_name")
        avg_match_score = float(row.get("avg_match_score") or 0)
        total_sample_size = int(row.get("total_sample_size") or 0)
        salary_series = forecast_map.get(major_name, [])
        if len(salary_series) < 2:
            continue
        growth_pct = ((salary_series[-1] - salary_series[0]) / salary_series[0] * 100) if salary_series[0] else 0
        heat_index = avg_match_score * math.log1p(total_sample_size)
        heat_candidates.append(
            {
                "major_name": major_name,
                "avg_match_score": avg_match_score,
                "total_sample_size": total_sample_size,
                "growth_pct": growth_pct,
                "heat_index": heat_index,
            }
        )

    if heat_candidates:
        heat_median = median(item["heat_index"] for item in heat_candidates)
        up_candidates = [
            item
            for item in heat_candidates
            if item["heat_index"] >= heat_median * 1.18 and item["growth_pct"] >= 2.5
        ]
        down_candidates = [
            item
            for item in heat_candidates
            if item["heat_index"] <= heat_median * 0.82 and item["growth_pct"] <= 0.8
        ]

        if up_candidates:
            item = sorted(up_candidates, key=lambda x: (x["heat_index"], x["growth_pct"]), reverse=True)[0]
            level = "高" if item["growth_pct"] >= 4.5 else "中"
        elif heat_candidates:
            item = sorted(heat_candidates, key=lambda x: (x["heat_index"], x["growth_pct"]), reverse=True)[0]
            level = "低"
        else:
            item = None

        if item:
            warnings.append(
                {
                    "warning_type": "专业热度异常上涨",
                    "warning_title": f"{item['major_name']}热度异常上涨",
                    "warning_level": level,
                    "target_scope": "专业",
                    "target_name": item["major_name"],
                    "trigger_reason": "招生匹配热度指数与薪资预期同时明显走强。",
                    "metric_value": f"热度指数 {item['heat_index']:.2f}",
                    "metric_change": f"预测薪资增幅 {item['growth_pct']:.1f}%",
                    "updated_at": updated_at,
                }
            )

        if down_candidates:
            item = sorted(down_candidates, key=lambda x: (x["heat_index"], x["growth_pct"]))[0]
            level = "高" if item["growth_pct"] <= 0 else "中"
        elif heat_candidates:
            item = sorted(heat_candidates, key=lambda x: (x["heat_index"], x["growth_pct"]))[0]
            level = "低"
        else:
            item = None

        if item:
            warnings.append(
                {
                    "warning_type": "专业热度异常下跌",
                    "warning_title": f"{item['major_name']}热度异常下跌",
                    "warning_level": level,
                    "target_scope": "专业",
                    "target_name": item["major_name"],
                    "trigger_reason": "招生匹配热度偏弱，且未来薪资预期增长不足。",
                    "metric_value": f"热度指数 {item['heat_index']:.2f}",
                    "metric_change": f"预测薪资增幅 {item['growth_pct']:.1f}%",
                    "updated_at": updated_at,
                }
            )

    decline_rows = fetch_rows(
        """
        SELECT
            s.school_name,
            a.major_name,
            DATE_FORMAT(e.first_insured_date, '%Y-%m') AS stat_month,
            COUNT(DISTINCT e.student_id) AS employed_count
        FROM fact_employment e
        INNER JOIN dim_student s ON e.student_id = s.student_id
        INNER JOIN fact_academic a ON e.student_id = a.student_id
        WHERE e.first_insured_date >= DATE_SUB(CURDATE(), INTERVAL 8 MONTH)
        GROUP BY s.school_name, a.major_name, DATE_FORMAT(e.first_insured_date, '%Y-%m')
        ORDER BY s.school_name, a.major_name, stat_month
        """
    )
    rate_rows = fetch_rows(
        """
        SELECT
            school_name,
            major_name,
            employment_rate_estimate,
            employment_count
        FROM ads_training_program_suggestions
        """
    )
    rate_map = {
        (row["school_name"], row["major_name"]): {
            "employment_rate_estimate": float(row.get("employment_rate_estimate") or 0),
            "employment_count": int(row.get("employment_count") or 0),
        }
        for row in rate_rows
    }
    decline_map = {}
    for row in decline_rows:
        key = (row["school_name"], row["major_name"])
        decline_map.setdefault(key, []).append(int(row.get("employed_count") or 0))

    decline_candidates = []
    for key, counts in decline_map.items():
        if len(counts) < 3:
            continue
        last_three = counts[-3:]
        if not (last_three[0] > last_three[1] > last_three[2]):
            continue
        current_rate = rate_map.get(key, {}).get("employment_rate_estimate", 0)
        if current_rate <= 0:
            continue
        drop_pct = ((last_three[0] - last_three[2]) / last_three[0] * 100) if last_three[0] else 0
        decline_candidates.append(
            {
                "school_name": key[0],
                "major_name": key[1],
                "last_three": last_three,
                "current_rate": current_rate,
                "drop_pct": drop_pct,
            }
        )

    if decline_candidates:
        item = sorted(
            decline_candidates,
            key=lambda x: (x["drop_pct"], -x["current_rate"]),
            reverse=True,
        )[0]
        level = "高" if item["drop_pct"] >= 25 or item["current_rate"] < 80 else "中"
        warnings.append(
            {
                "warning_type": "就业率连续下滑",
                "warning_title": f"{item['school_name']}·{item['major_name']}就业率连续下滑",
                "warning_level": level,
                "target_scope": "学校 / 专业",
                "target_name": f"{item['school_name']} / {item['major_name']}",
                "trigger_reason": "近三期就业吸纳人数连续回落，当前专业就业率处于偏低区间。",
                "metric_value": f"近三期人数 {item['last_three'][0]} → {item['last_three'][2]}",
                "metric_change": f"估算就业率 {item['current_rate']:.1f}%",
                "updated_at": updated_at,
            }
        )

    salary_rows = fetch_rows(
        """
        SELECT
            leading_industry_tag,
            DATE_FORMAT(first_insured_date, '%Y-%m') AS stat_month,
            ROUND(AVG(CAST(avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            COUNT(*) AS sample_count
        FROM fact_employment
        WHERE first_insured_date >= DATE_SUB(CURDATE(), INTERVAL 8 MONTH)
          AND leading_industry_tag IS NOT NULL
        GROUP BY leading_industry_tag, DATE_FORMAT(first_insured_date, '%Y-%m')
        ORDER BY leading_industry_tag, stat_month
        """
    )
    salary_map = {}
    for row in salary_rows:
        industry = row.get("leading_industry_tag")
        salary_map.setdefault(industry, []).append(float(row.get("avg_salary") or 0))

    slowdown_candidates = []
    for industry, values in salary_map.items():
        if len(values) < 6:
            continue
        previous = values[-6:-3]
        recent = values[-3:]
        previous_avg = sum(previous) / len(previous)
        recent_avg = sum(recent) / len(recent)
        recent_growth = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg else 0
        month_growth = ((recent[-1] - recent[0]) / recent[0] * 100) if recent[0] else 0
        if recent_growth <= 1.2 or month_growth <= 0.5:
            slowdown_candidates.append(
                {
                    "industry": industry,
                    "recent_growth": recent_growth,
                    "month_growth": month_growth,
                    "recent_avg": recent_avg,
                }
            )

    if slowdown_candidates:
        item = sorted(slowdown_candidates, key=lambda x: (x["recent_growth"], x["month_growth"]))[0]
        level = "高" if item["recent_growth"] < 0 or item["month_growth"] < 0 else "中"
    elif salary_map:
        fallback_rows = []
        for industry, values in salary_map.items():
            if len(values) < 3:
                continue
            recent_avg = sum(values[-3:]) / len(values[-3:])
            month_growth = ((values[-1] - values[-3]) / values[-3] * 100) if values[-3] else 0
            fallback_rows.append(
                {
                    "industry": industry,
                    "recent_growth": month_growth,
                    "month_growth": month_growth,
                    "recent_avg": recent_avg,
                }
            )
        item = sorted(fallback_rows, key=lambda x: (x["recent_growth"], x["month_growth"]))[0] if fallback_rows else None
        level = "低"
    else:
        item = None

    if item:
        warnings.append(
            {
                "warning_type": "薪资增速放缓",
                "warning_title": f"{item['industry']}薪资增速放缓",
                "warning_level": level,
                "target_scope": "行业",
                "target_name": item["industry"],
                "trigger_reason": "近三个月平均薪资增速显著低于此前阶段，薪资拉动效应减弱。",
                "metric_value": f"近三月均薪 {item['recent_avg']:.0f} 元",
                "metric_change": f"阶段增速 {item['recent_growth']:.1f}%",
                "updated_at": updated_at,
            }
        )

    mismatch_rows = fetch_rows(
        """
        SELECT
            s.school_name,
            a.major_name,
            COUNT(DISTINCT s.student_id) AS total_students,
            COUNT(DISTINCT e.student_id) AS employed_students
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        GROUP BY s.school_name, a.major_name
        HAVING COUNT(DISTINCT s.student_id) >= 80
        """
    )
    mismatch_candidates = []
    for row in mismatch_rows:
        total_students = int(row.get("total_students") or 0)
        employed_students = int(row.get("employed_students") or 0)
        if total_students <= 0:
            continue
        absorption_rate = employed_students / total_students * 100
        gap_count = total_students - employed_students
        if absorption_rate < 72 and gap_count >= 35:
            mismatch_candidates.append(
                {
                    "school_name": row["school_name"],
                    "major_name": row["major_name"],
                    "total_students": total_students,
                    "employed_students": employed_students,
                    "absorption_rate": absorption_rate,
                    "gap_count": gap_count,
                }
            )

    if mismatch_candidates:
        item = sorted(
            mismatch_candidates,
            key=lambda x: (x["gap_count"], -x["absorption_rate"]),
            reverse=True,
        )[0]
        level = "高" if item["absorption_rate"] < 60 else "中"
    elif mismatch_rows:
        fallback_rows = []
        for row in mismatch_rows:
            total_students = int(row.get("total_students") or 0)
            employed_students = int(row.get("employed_students") or 0)
            if total_students <= 0:
                continue
            absorption_rate = employed_students / total_students * 100
            fallback_rows.append(
                {
                    "school_name": row["school_name"],
                    "major_name": row["major_name"],
                    "total_students": total_students,
                    "employed_students": employed_students,
                    "absorption_rate": absorption_rate,
                }
            )
        item = sorted(fallback_rows, key=lambda x: (x["absorption_rate"], -x["total_students"]))[0] if fallback_rows else None
        level = "低"
    else:
        item = None

    if item:
        warnings.append(
            {
                "warning_type": "招生规模与就业吸纳不匹配",
                "warning_title": f"{item['school_name']}·{item['major_name']}规模与吸纳不匹配",
                "warning_level": level,
                "target_scope": "学校 / 专业",
                "target_name": f"{item['school_name']} / {item['major_name']}",
                "trigger_reason": "专业样本规模较大，但就业吸纳人数未同步增长，存在结构性错配风险。",
                "metric_value": f"样本规模 {item['total_students']}，就业吸纳 {item['employed_students']}",
                "metric_change": f"吸纳率 {item['absorption_rate']:.1f}%",
                "updated_at": updated_at,
            }
        )

    warnings = sorted(
        warnings,
        key=lambda item: (severity_weight(item["warning_level"]), item["warning_type"]),
        reverse=True,
    )[:8]

    return {
        "items": warnings,
        "summary": build_warning_summary(warnings),
    }


def build_gov_school_detail(school_name: str):
    overview_rows = fetch_rows(
        """
        SELECT
            s.school_name,
            MAX(s.school_level) AS school_level,
            COUNT(DISTINCT s.student_id) AS student_count,
            COUNT(DISTINCT a.major_name) AS major_count,
            COUNT(DISTINCT e.student_id) AS employed_students,
            ROUND(COUNT(DISTINCT e.student_id) / NULLIF(COUNT(DISTINCT s.student_id), 0) * 100, 1) AS employment_rate,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        WHERE s.school_name = :school_name
        GROUP BY s.school_name
        """,
        {"school_name": school_name},
    )
    if not overview_rows:
        return None

    major_rows = fetch_rows(
        """
        SELECT
            a.major_name,
            MAX(a.discipline_category) AS discipline_category,
            COUNT(DISTINCT s.student_id) AS student_count,
            COUNT(DISTINCT e.student_id) AS employed_students,
            ROUND(COUNT(DISTINCT e.student_id) / NULLIF(COUNT(DISTINCT s.student_id), 0) * 100, 1) AS employment_rate,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            ROUND(AVG(CASE WHEN e.leading_industry_tag = :strategic_tag THEN 1 ELSE 0 END) * 100, 1) AS strategic_ratio
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        WHERE s.school_name = :school_name
        GROUP BY a.major_name
        ORDER BY student_count DESC, avg_salary DESC
        """,
        {"school_name": school_name, "strategic_tag": TXT_STRATEGIC},
    )

    industry_rows = fetch_rows(
        """
        SELECT
            COALESCE(e.leading_industry_tag, '未标注') AS industry_name,
            COUNT(DISTINCT e.student_id) AS employed_count
        FROM fact_employment e
        INNER JOIN dim_student s ON e.student_id = s.student_id
        WHERE s.school_name = :school_name
        GROUP BY COALESCE(e.leading_industry_tag, '未标注')
        ORDER BY employed_count DESC
        LIMIT 8
        """,
        {"school_name": school_name},
    )

    warning_rows = [
        item
        for item in build_regional_warnings()["items"]
        if school_name in str(item.get("target_name", ""))
    ]

    return {
        "overview": overview_rows[0],
        "major_breakdown": major_rows,
        "industry_flow": industry_rows,
        "warnings": warning_rows,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_gov_major_detail(school_name: str, major_name: str):
    overview_rows = fetch_rows(
        """
        SELECT
            s.school_name,
            a.major_name,
            MAX(a.discipline_category) AS discipline_category,
            COUNT(DISTINCT s.student_id) AS student_count,
            COUNT(DISTINCT e.student_id) AS employed_students,
            ROUND(COUNT(DISTINCT e.student_id) / NULLIF(COUNT(DISTINCT s.student_id), 0) * 100, 1) AS employment_rate,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            ROUND(AVG(CASE WHEN e.leading_industry_tag = :strategic_tag THEN 1 ELSE 0 END) * 100, 1) AS strategic_ratio
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        WHERE s.school_name = :school_name
          AND a.major_name = :major_name
        GROUP BY s.school_name, a.major_name
        """,
        {"school_name": school_name, "major_name": major_name, "strategic_tag": TXT_STRATEGIC},
    )
    if not overview_rows:
        return None

    industry_rows = fetch_rows(
        """
        SELECT
            COALESCE(e.leading_industry_tag, '未标注') AS industry_name,
            COUNT(DISTINCT e.student_id) AS employed_count
        FROM fact_employment e
        INNER JOIN dim_student s ON e.student_id = s.student_id
        INNER JOIN fact_academic a ON e.student_id = a.student_id
        WHERE s.school_name = :school_name
          AND a.major_name = :major_name
        GROUP BY COALESCE(e.leading_industry_tag, '未标注')
        ORDER BY employed_count DESC
        LIMIT 8
        """,
        {"school_name": school_name, "major_name": major_name},
    )

    salary_trend_rows = fetch_rows(
        """
        SELECT
            DATE_FORMAT(e.first_insured_date, '%Y-%m') AS stat_month,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            COUNT(*) AS sample_count
        FROM fact_employment e
        INNER JOIN dim_student s ON e.student_id = s.student_id
        INNER JOIN fact_academic a ON e.student_id = a.student_id
        WHERE s.school_name = :school_name
          AND a.major_name = :major_name
          AND e.first_insured_date IS NOT NULL
        GROUP BY DATE_FORMAT(e.first_insured_date, '%Y-%m')
        ORDER BY stat_month DESC
        LIMIT 12
        """,
        {"school_name": school_name, "major_name": major_name},
    )
    salary_trend_rows = list(reversed(salary_trend_rows))

    enrollment_rows = fetch_rows(
        """
        SELECT
            major_name,
            ROUND(AVG(matching_score), 4) AS avg_match_score,
            SUM(sample_size) AS total_sample_size
        FROM ads_enrollment_matching
        WHERE major_name = :major_name
        GROUP BY major_name
        """,
        {"major_name": major_name},
    )

    warning_rows = [
        item
        for item in build_regional_warnings()["items"]
        if school_name in str(item.get("target_name", "")) or major_name in str(item.get("target_name", ""))
    ]

    return {
        "overview": overview_rows[0],
        "industry_flow": industry_rows,
        "salary_trend": salary_trend_rows,
        "enrollment_hint": enrollment_rows[0] if enrollment_rows else {},
        "warnings": warning_rows,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_school_top_industry_map(scope_major_name: str | None = None):
    sql = """
        SELECT
            s.school_name,
            COALESCE(e.leading_industry_tag, '未标注') AS industry_name,
            COUNT(DISTINCT e.student_id) AS employed_count
        FROM fact_employment e
        INNER JOIN dim_student s ON e.student_id = s.student_id
        INNER JOIN fact_academic a ON e.student_id = a.student_id
        WHERE (:major_name IS NULL OR a.major_name = :major_name)
        GROUP BY s.school_name, COALESCE(e.leading_industry_tag, '未标注')
        ORDER BY s.school_name, employed_count DESC
    """
    rows = fetch_rows(sql, {"major_name": scope_major_name})
    top_map = {}
    for row in rows:
        school_name = row.get("school_name")
        if school_name not in top_map:
            top_map[school_name] = row.get("industry_name") or "未标注"
    return top_map


def build_gov_school_benchmark_overview():
    overview_rows = fetch_rows(
        """
        SELECT
            s.school_name,
            MAX(s.school_level) AS school_level,
            COUNT(DISTINCT s.student_id) AS student_count,
            COUNT(DISTINCT a.major_name) AS major_count,
            COUNT(DISTINCT e.student_id) AS employed_students,
            ROUND(COUNT(DISTINCT e.student_id) / NULLIF(COUNT(DISTINCT s.student_id), 0) * 100, 1) AS employment_rate,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            ROUND(AVG(CASE WHEN e.leading_industry_tag = :strategic_tag THEN 1 ELSE 0 END) * 100, 1) AS strategic_ratio
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        GROUP BY s.school_name
        HAVING COUNT(DISTINCT s.student_id) >= 200
        ORDER BY student_count DESC, avg_salary DESC
        """,
        {"strategic_tag": TXT_STRATEGIC},
    )

    top_industry_map = build_school_top_industry_map()
    for row in overview_rows:
        row["top_industry"] = top_industry_map.get(row["school_name"], "未标注")

    major_options = fetch_rows(
        """
        SELECT
            a.major_name,
            COUNT(DISTINCT s.school_name) AS school_coverage,
            COUNT(DISTINCT s.student_id) AS total_students,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        GROUP BY a.major_name
        HAVING COUNT(DISTINCT s.school_name) >= 3
           AND COUNT(DISTINCT s.student_id) >= 120
        ORDER BY school_coverage DESC, total_students DESC, avg_salary DESC
        LIMIT 20
        """
    )

    return {
        "overview": overview_rows,
        "major_options": major_options,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_gov_major_benchmark(major_name: str):
    rows = fetch_rows(
        """
        SELECT
            s.school_name,
            MAX(s.school_level) AS school_level,
            a.major_name,
            COUNT(DISTINCT s.student_id) AS student_count,
            COUNT(DISTINCT e.student_id) AS employed_students,
            ROUND(COUNT(DISTINCT e.student_id) / NULLIF(COUNT(DISTINCT s.student_id), 0) * 100, 1) AS employment_rate,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            ROUND(AVG(CASE WHEN e.leading_industry_tag = :strategic_tag THEN 1 ELSE 0 END) * 100, 1) AS strategic_ratio
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        LEFT JOIN fact_employment e ON s.student_id = e.student_id
        WHERE a.major_name = :major_name
        GROUP BY s.school_name, a.major_name
        HAVING COUNT(DISTINCT s.student_id) >= 30
        ORDER BY student_count DESC, avg_salary DESC
        """,
        {"major_name": major_name, "strategic_tag": TXT_STRATEGIC},
    )
    top_industry_map = build_school_top_industry_map(major_name)
    for row in rows:
        row["top_industry"] = top_industry_map.get(row["school_name"], "未标注")

    return {
        "major_name": major_name,
        "rows": rows,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def build_major_structure_advice():
    base_rows = fetch_rows(
        """
        SELECT
            school_name,
            school_level,
            discipline_category,
            major_name,
            major_type,
            employment_count,
            employment_rate_estimate,
            avg_salary,
            strategic_ratio,
            high_skill_ratio,
            dominant_industry,
            dominant_skill_level,
            matched_rule_count,
            top_rule_support,
            top_rule_confidence,
            top_rule_lift,
            priority_score,
            action_type,
            evidence_summary
        FROM ads_training_program_suggestions
        """
    )
    if not base_rows:
        return {"items": [], "summary": {"total": 0, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}

    enrollment_rows = fetch_rows(
        """
        SELECT
            major_name,
            ROUND(AVG(matching_score), 4) AS avg_match_score,
            SUM(sample_size) AS total_sample_size
        FROM ads_enrollment_matching
        GROUP BY major_name
        """
    )
    enrollment_map = {
        row["major_name"]: {
            "avg_match_score": float(row.get("avg_match_score") or 0),
            "total_sample_size": int(row.get("total_sample_size") or 0),
        }
        for row in enrollment_rows
    }

    forecast_rows = fetch_rows(
        """
        SELECT major_name, forecast_month, predicted_salary
        FROM ads_salary_forecast
        WHERE major_name IS NOT NULL AND major_name <> ''
        ORDER BY major_name, forecast_month
        """
    )
    forecast_map = {}
    for row in forecast_rows:
        major_name = row.get("major_name")
        if not major_name:
            continue
        forecast_map.setdefault(major_name, []).append(float(row.get("predicted_salary") or 0))

    salary_values = [float(row.get("avg_salary") or 0) for row in base_rows if float(row.get("avg_salary") or 0) > 0]
    employment_values = [float(row.get("employment_rate_estimate") or 0) for row in base_rows if float(row.get("employment_rate_estimate") or 0) > 0]
    match_values = [float(row.get("avg_match_score") or 0) for row in enrollment_map.values() if float(row.get("avg_match_score") or 0) > 0]
    sample_values = [int(row.get("total_sample_size") or 0) for row in enrollment_map.values() if int(row.get("total_sample_size") or 0) > 0]
    skill_values = [float(row.get("high_skill_ratio") or 0) for row in base_rows if float(row.get("high_skill_ratio") or 0) > 0]
    strategic_values = [float(row.get("strategic_ratio") or 0) for row in base_rows if float(row.get("strategic_ratio") or 0) > 0]

    salary_median = median(salary_values) if salary_values else 0
    employment_median = median(employment_values) if employment_values else 0
    match_median = median(match_values) if match_values else 0
    sample_median = median(sample_values) if sample_values else 0
    skill_median = median(skill_values) if skill_values else 0
    strategic_median = median(strategic_values) if strategic_values else 0

    def get_growth_pct(major_name: str):
        values = forecast_map.get(major_name) or []
        if len(values) < 2 or not values[0]:
            return None
        return round((values[-1] - values[0]) / values[0] * 100, 2)

    def classify_level(suggestion_type: str, row: dict, growth_pct):
        employment_rate = float(row.get("employment_rate_estimate") or 0)
        avg_salary = float(row.get("avg_salary") or 0)
        strategic_ratio = float(row.get("strategic_ratio") or 0)
        if suggestion_type == "建议扩招":
            return "高" if employment_rate >= 90 and avg_salary >= salary_median * 1.08 else "中"
        if suggestion_type == "建议缩招":
            return "高" if employment_rate < 80 or avg_salary < salary_median * 0.88 else "中"
        if suggestion_type == "建议加强实践培养":
            return "高" if float(row.get("high_skill_ratio") or 0) >= max(skill_median, 0.35) else "中"
        if suggestion_type == "建议重点扶持方向":
            if strategic_ratio >= max(strategic_median, 0.22) and (growth_pct or 0) >= 1.5:
                return "高"
            return "中"
        return "中" if employment_rate >= employment_median else "低"

    suggestion_items = []
    for row in base_rows:
        major_name = row.get("major_name") or ""
        school_name = row.get("school_name") or ""
        avg_salary = float(row.get("avg_salary") or 0)
        employment_rate = float(row.get("employment_rate_estimate") or 0)
        strategic_ratio = float(row.get("strategic_ratio") or 0)
        high_skill_ratio = float(row.get("high_skill_ratio") or 0)
        top_rule_lift = float(row.get("top_rule_lift") or 0)
        dominant_industry = row.get("dominant_industry") or "未标注"
        action_type = row.get("action_type") or "待分析"

        enrollment_info = enrollment_map.get(major_name, {})
        avg_match_score = float(enrollment_info.get("avg_match_score") or 0)
        total_sample_size = int(enrollment_info.get("total_sample_size") or 0)
        growth_pct = get_growth_pct(major_name)

        demand_positive = (
            avg_match_score >= match_median * 1.03 if match_median else False
        ) or ((growth_pct or 0) >= 1.8)
        demand_negative = (
            avg_match_score > 0 and avg_match_score <= match_median * 0.96 if match_median else False
        ) or (growth_pct is not None and growth_pct <= 0.4)
        employment_strong = employment_rate >= max(88, employment_median)
        employment_weak = employment_rate < max(82, employment_median - 4)
        salary_strong = avg_salary >= salary_median * 1.03 if salary_median else False
        salary_weak = avg_salary <= salary_median * 0.95 if salary_median else False
        high_skill_gap = high_skill_ratio >= max(skill_median, 0.35) and employment_rate < 88

        if demand_positive and employment_strong and salary_strong:
            suggestion_type = "建议扩招"
        elif demand_negative and employment_weak and salary_weak:
            suggestion_type = "建议缩招"
        elif high_skill_gap or action_type == "重点调优":
            suggestion_type = "建议加强实践培养"
        elif employment_rate >= max(84, employment_median - 1) and not demand_negative:
            suggestion_type = "建议稳招"
        else:
            suggestion_type = "建议持续观察"

        support_signals = [
            f"就业率 {employment_rate:.1f}%",
            f"平均薪资 {avg_salary:.0f} 元",
            f"招生匹配均分 {avg_match_score:.3f}" if avg_match_score else "招生匹配均分暂无",
        ]
        if growth_pct is not None:
            support_signals.append(f"预测薪资增幅 {growth_pct:.1f}%")
        support_signals.append(f"规则提升度 {top_rule_lift:.2f}")

        if suggestion_type == "建议扩招":
            trigger_reason = "需求信号上升，就业与薪资表现同步较强。"
            explanation = f"{major_name} 在 {school_name} 的就业率和平均薪资均高于全市中位水平，同时招生匹配或需求预测呈现上升趋势，具备扩招基础。"
        elif suggestion_type == "建议缩招":
            trigger_reason = "需求走弱，就业吸纳与薪资表现偏弱。"
            explanation = f"{major_name} 在 {school_name} 的就业率和平均薪资低于整体中位水平，且需求信号偏弱，建议控制规模并持续跟踪。"
        elif suggestion_type == "建议加强实践培养":
            trigger_reason = "岗位技能门槛较高，但就业转化仍有提升空间。"
            explanation = f"{major_name} 对应行业方向 {dominant_industry} 的技能要求较高，当前就业结果尚未充分转化，建议加强项目实践、实习和企业场景训练。"
        elif suggestion_type == "建议稳招":
            trigger_reason = "需求与就业表现整体稳定，结构调整压力较小。"
            explanation = f"{major_name} 的就业率、薪资和需求信号整体处于稳定区间，建议维持招生规模并持续观察后续变化。"
        else:
            trigger_reason = "现有指标未形成足够强的一致性结论。"
            explanation = f"{major_name} 当前需求、就业与薪资信号分化较大，建议先持续观察，再决定是否调整招生规模。"

        suggestion_items.append(
            {
                "scope_type": "school_major",
                "suggestion_type": suggestion_type,
                "suggestion_level": classify_level(suggestion_type, row, growth_pct),
                "school_name": school_name,
                "major_name": major_name,
                "industry_name": dominant_industry,
                "discipline_category": row.get("discipline_category") or "",
                "target_name": f"{school_name} / {major_name}",
                "trigger_reason": trigger_reason,
                "metric_summary": "；".join(support_signals[:4]),
                "supporting_signals": support_signals,
                "explanation": explanation,
                "employment_rate": round(employment_rate, 1),
                "avg_salary": round(avg_salary, 2),
                "avg_match_score": round(avg_match_score, 4),
                "forecast_growth_pct": growth_pct,
                "rule_lift": round(top_rule_lift, 4),
                "strategic_ratio": round(strategic_ratio * 100, 1),
                "sample_size": total_sample_size,
                "priority_score": round(float(row.get("priority_score") or 0), 2),
                "evidence_summary": row.get("evidence_summary") or "",
            }
        )

    industry_groups = {}
    for item in suggestion_items:
        if item["scope_type"] != "school_major":
            continue
        if item["suggestion_type"] not in {"建议扩招", "建议稳招", "建议加强实践培养"}:
            continue
        if item["industry_name"] in {"", "未标注", "常规行业"}:
            continue
        key = (item["school_name"], item["industry_name"])
        bucket = industry_groups.setdefault(
            key,
            {
                "school_name": item["school_name"],
                "industry_name": item["industry_name"],
                "major_names": [],
                "employment_rates": [],
                "avg_salaries": [],
                "strategic_ratios": [],
                "rule_lifts": [],
            },
        )
        bucket["major_names"].append(item["major_name"])
        bucket["employment_rates"].append(item["employment_rate"])
        bucket["avg_salaries"].append(item["avg_salary"])
        bucket["strategic_ratios"].append(item["strategic_ratio"])
        bucket["rule_lifts"].append(item["rule_lift"])

    for bucket in industry_groups.values():
        if len(bucket["major_names"]) < 2:
            continue
        avg_employment = sum(bucket["employment_rates"]) / len(bucket["employment_rates"])
        avg_salary = sum(bucket["avg_salaries"]) / len(bucket["avg_salaries"])
        avg_strategic = sum(bucket["strategic_ratios"]) / len(bucket["strategic_ratios"])
        avg_rule_lift = sum(bucket["rule_lifts"]) / len(bucket["rule_lifts"])
        if avg_employment < max(84, employment_median) or avg_rule_lift < 2:
            continue

        suggestion_items.append(
            {
                "scope_type": "industry_direction",
                "suggestion_type": "建议重点扶持方向",
                "suggestion_level": "高" if avg_strategic >= max(strategic_median * 100, 18) else "中",
                "school_name": bucket["school_name"],
                "major_name": "",
                "industry_name": bucket["industry_name"],
                "discipline_category": "",
                "target_name": f"{bucket['school_name']} / {bucket['industry_name']}",
                "trigger_reason": "该方向关联强、就业质量较高，具备形成特色方向的基础。",
                "metric_summary": f"覆盖专业 {len(bucket['major_names'])} 个；平均就业率 {avg_employment:.1f}%；平均薪资 {avg_salary:.0f} 元",
                "supporting_signals": [
                    f"覆盖专业：{'、'.join(bucket['major_names'][:3])}",
                    f"平均就业率 {avg_employment:.1f}%",
                    f"平均薪资 {avg_salary:.0f} 元",
                    f"规则提升度均值 {avg_rule_lift:.2f}",
                ],
                "explanation": f"{bucket['school_name']} 在 {bucket['industry_name']} 方向已形成多专业支撑，且就业与规则关联表现较强，建议作为重点扶持的行业方向持续投入。",
                "employment_rate": round(avg_employment, 1),
                "avg_salary": round(avg_salary, 2),
                "avg_match_score": 0,
                "forecast_growth_pct": None,
                "rule_lift": round(avg_rule_lift, 4),
                "strategic_ratio": round(avg_strategic, 1),
                "sample_size": len(bucket["major_names"]),
                "priority_score": round(avg_employment + avg_rule_lift * 8 + avg_strategic * 0.2, 2),
                "evidence_summary": f"重点覆盖专业：{'、'.join(bucket['major_names'][:4])}",
            }
        )

    type_summary = {}
    for item in suggestion_items:
        type_summary[item["suggestion_type"]] = type_summary.get(item["suggestion_type"], 0) + 1

    suggestion_items = sorted(
        suggestion_items,
        key=lambda item: (
            {"高": 3, "中": 2, "低": 1}.get(item["suggestion_level"], 0),
            item["priority_score"],
            item["employment_rate"],
            item["avg_salary"],
        ),
        reverse=True,
    )

    return {
        "items": suggestion_items,
        "summary": {
            "total": len(suggestion_items),
            "type_summary": type_summary,
            "salary_median": round(salary_median, 2),
            "employment_median": round(employment_median, 1),
            "match_median": round(match_median, 4),
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


@app.route("/api/health", methods=["GET"])
def health():
    try:
        with DB_ENGINE.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify(
            {
                "success": True,
                "message": "backend is running",
                "data_source": "mysql",
            }
        )
    except SQLAlchemyError as exc:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"MySQL connection failed: {exc}",
                }
            ),
            500,
        )


@app.route("/api/employment-summary", methods=["GET"])
def get_employment_summary():
    sql = """
        SELECT
            s.school_name AS school_name,
            s.origin_place AS origin_place,
            s.school_level AS school_level,
            a.major_name AS major_name,
            COALESCE(a.edu_level, s.edu_name) AS edu_level,
            e.leading_industry_tag AS leading_industry_tag,
            a.discipline_category AS discipline_category,
            ROUND(AVG(CAST(e.avg_salary AS DECIMAL(10, 2))), 2) AS avg_salary,
            COUNT(*) AS emp_count,
            ROUND(AVG(CASE WHEN e.leading_industry_tag = :strategic_tag THEN 1 ELSE 0 END), 4) AS high_tech_ratio
        FROM dim_student s
        INNER JOIN fact_academic a ON s.student_id = a.student_id
        INNER JOIN fact_employment e ON s.student_id = e.student_id
        GROUP BY
            s.school_name,
            s.origin_place,
            s.school_level,
            a.major_name,
            COALESCE(a.edu_level, s.edu_name),
            e.leading_industry_tag,
            a.discipline_category
        ORDER BY avg_salary DESC, emp_count DESC
    """
    data = fetch_rows(sql, {"strategic_tag": TXT_STRATEGIC})
    return success_response(data)


@app.route("/api/salary-forecast", methods=["GET"])
def get_salary_forecast():
    sql = """
        SELECT
            track_rank AS track_rank,
            forecast_month AS forecast_month,
            track AS track,
            major_name AS major_name,
            category AS category,
            predicted_salary AS predicted_salary,
            DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s') AS update_time
        FROM ads_salary_forecast
        ORDER BY track_rank, forecast_month
    """
    return success_response(fetch_rows(sql))


@app.route("/api/salary-forecast-evaluation", methods=["GET"])
def get_salary_forecast_evaluation():
    metrics_sql = """
        SELECT
            metric_name,
            metric_value,
            metric_label,
            metric_unit,
            sample_size,
            train_window_size,
            test_window_size,
            metric_desc
        FROM ads_salary_forecast_eval
        ORDER BY
            CASE metric_name
                WHEN 'MAE' THEN 1
                WHEN 'RMSE' THEN 2
                WHEN 'MAPE' THEN 3
                ELSE 99
            END
    """
    backtest_sql = """
        SELECT
            track_rank,
            forecast_month,
            track,
            major_name,
            category,
            actual_salary,
            predicted_salary,
            abs_error,
            dataset_split
        FROM ads_salary_forecast_backtest
        ORDER BY track_rank, forecast_month
    """
    return success_response(
        {
            "metrics": fetch_rows(metrics_sql),
            "backtest": fetch_rows(backtest_sql),
        }
    )


@app.route("/api/enrollment-matching", methods=["GET"])
def get_enrollment_matching():
    sql = """
        SELECT
            major_name AS target_major,
            background_dim AS top_potential_student_id,
            matching_score AS matching_score,
            sample_size AS sample_size
        FROM ads_enrollment_matching
        ORDER BY major_name, matching_score DESC
    """
    return success_response(fetch_rows(sql))


@app.route("/api/enrollment-matching-evaluation", methods=["GET"])
def get_enrollment_matching_evaluation():
    sql = """
        SELECT
            metric_name,
            metric_value,
            metric_label,
            metric_desc,
            k_value,
            evaluated_profiles,
            eval_mode
        FROM ads_enrollment_matching_eval
        ORDER BY
            CASE metric_name
                WHEN 'Precision@K' THEN 1
                WHEN 'Recall@K' THEN 2
                WHEN 'HitRate@K' THEN 3
                ELSE 99
            END
    """
    return success_response(fetch_rows(sql))


@app.route("/api/major-matching-rules", methods=["GET"])
def get_major_matching_rules():
    sql = """
        SELECT
            antecedent,
            consequent,
            support,
            confidence,
            lift
        FROM ads_major_matching_rules
        ORDER BY lift DESC, confidence DESC
    """
    return success_response(fetch_rows(sql))


@app.route("/api/training-program-optimization", methods=["GET"])
def get_training_program_optimization():
    sql = """
        SELECT
            school_name,
            school_level,
            discipline_category,
            major_name,
            major_type,
            employment_count,
            employment_rate_estimate,
            avg_salary,
            strategic_ratio,
            high_skill_ratio,
            dominant_industry,
            dominant_skill_level,
            matched_rule_count,
            top_rule_support,
            top_rule_confidence,
            top_rule_lift,
            priority_score,
            action_type,
            recommended_courses,
            recommended_skills,
            recommended_practice,
            recommended_structure,
            rule_evidence,
            evidence_summary,
            explanation
        FROM ads_training_program_suggestions
        ORDER BY priority_score DESC, top_rule_lift DESC, avg_salary DESC
    """
    return success_response(fetch_rows(sql))


@app.route("/api/job-recommendation", methods=["GET"])
def get_job_recommendation():
    student_id = request.args.get("student_id", type=str)
    sql = """
        SELECT
            student_id AS student_id,
            student_name AS student_name,
            employer_name AS recommended_job,
            industry_type AS industry_type,
            leading_industry_tag AS leading_industry_tag,
            company_scale AS company_scale,
            cosine_similarity AS matching_score,
            recommend_reason AS recommend_reason,
            rank_no AS rank_no
        FROM ads_job_recommendation
        WHERE (:student_id IS NULL OR student_id = :student_id)
        ORDER BY student_id, rank_no
    """
    return success_response(fetch_rows(sql, {"student_id": student_id if student_id else None}))


@app.route("/api/job-recommendation-evaluation", methods=["GET"])
def get_job_recommendation_evaluation():
    sql = """
        SELECT
            metric_name,
            metric_value,
            metric_label,
            metric_desc,
            sample_size,
            eval_mode
        FROM ads_job_recommendation_eval
        ORDER BY
            CASE metric_name
                WHEN 'AvgTop1Similarity' THEN 1
                WHEN 'AvgTopKSimilarity' THEN 2
                WHEN 'HighConfidenceRatio' THEN 3
                ELSE 99
            END
    """
    return success_response(fetch_rows(sql))


@app.route("/api/model-metrics", methods=["GET"])
def get_model_metrics():
    salary_metrics = fetch_rows(
        """
        SELECT
            'salary_forecast' AS module_key,
            metric_name,
            metric_label,
            metric_value,
            metric_desc
        FROM ads_salary_forecast_eval
        """
    )
    enrollment_metrics = fetch_rows(
        """
        SELECT
            'enrollment_matching' AS module_key,
            metric_name,
            metric_label,
            metric_value,
            metric_desc
        FROM ads_enrollment_matching_eval
        """
    )
    rule_metrics = fetch_rows(
        """
        SELECT
            'rule_mining' AS module_key,
            'AvgSupport' AS metric_name,
            '平均支持度' AS metric_label,
            ROUND(AVG(support), 4) AS metric_value,
            '反映规则覆盖样本的平均比例，值越高说明规则覆盖面越广。' AS metric_desc
        FROM ads_major_matching_rules
        UNION ALL
        SELECT
            'rule_mining' AS module_key,
            'AvgConfidence' AS metric_name,
            '平均置信度' AS metric_label,
            ROUND(AVG(confidence), 4) AS metric_value,
            '反映前项出现时后项同时出现的稳定性，值越高说明规则可靠性越强。' AS metric_desc
        FROM ads_major_matching_rules
        UNION ALL
        SELECT
            'rule_mining' AS module_key,
            'AvgLift' AS metric_name,
            '平均提升度' AS metric_label,
            ROUND(AVG(lift), 4) AS metric_value,
            '反映规则相比随机命中的增益倍数，大于 1 表示存在正向关联。' AS metric_desc
        FROM ads_major_matching_rules
        """
    )
    job_metrics = fetch_rows(
        """
        SELECT
            'job_recommendation' AS module_key,
            metric_name,
            metric_label,
            metric_value,
            metric_desc
        FROM ads_job_recommendation_eval
        """
    )
    return success_response(salary_metrics + enrollment_metrics + rule_metrics + job_metrics)


@app.route("/api/regional-warnings", methods=["GET"])
def get_regional_warnings():
    return success_response(build_regional_warnings())


@app.route("/api/gov/school-detail", methods=["GET"])
def get_gov_school_detail():
    school_name = request.args.get("school_name", type=str)
    if not school_name:
        return jsonify({"success": False, "message": "school_name is required"}), 400
    data = build_gov_school_detail(school_name)
    if not data:
        return jsonify({"success": False, "message": "school not found"}), 404
    return success_response(data)


@app.route("/api/gov/major-detail", methods=["GET"])
def get_gov_major_detail():
    school_name = request.args.get("school_name", type=str)
    major_name = request.args.get("major_name", type=str)
    if not school_name or not major_name:
        return (
            jsonify({"success": False, "message": "school_name and major_name are required"}),
            400,
        )
    data = build_gov_major_detail(school_name, major_name)
    if not data:
        return jsonify({"success": False, "message": "major not found"}), 404
    return success_response(data)


@app.route("/api/gov/school-benchmark-overview", methods=["GET"])
def get_gov_school_benchmark_overview():
    return success_response(build_gov_school_benchmark_overview())


@app.route("/api/gov/school-benchmark-major", methods=["GET"])
def get_gov_school_benchmark_major():
    major_name = request.args.get("major_name", type=str)
    if not major_name:
        return jsonify({"success": False, "message": "major_name is required"}), 400
    return success_response(build_gov_major_benchmark(major_name))


@app.route("/api/major-structure-advice", methods=["GET"])
def get_major_structure_advice():
    return success_response(build_major_structure_advice())


@app.route("/api/report/generate", methods=["POST"])
def generate_report():
    try:
        data = request.get_json() or {}

        prompt = data.get("prompt", "")
        current_page = data.get("currentPage", "report")
        report_type = data.get("reportType", "management")
        report_length = data.get("reportLength", "standard")
        modules = data.get("modules", [])
        chart_data = data.get("chartData", {})
        filters = data.get("filters", {})
        summary = data.get("summary", {})

        filters["currentPage"] = current_page

        prompt_text = build_report_prompt(
            prompt=prompt,
            summary=summary,
            chart_data=chart_data,
            filters=filters,
            report_type=report_type,
            report_length=report_length,
            modules=modules,
        )

        report = call_llm(prompt_text)

        return jsonify({"success": True, "report": report})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
