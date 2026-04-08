from pathlib import Path
import sys
from datetime import date, datetime
from decimal import Decimal
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
            forecast_month AS forecast_month,
            predicted_salary AS predicted_salary,
            DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s') AS update_time
        FROM ads_salary_forecast
        ORDER BY forecast_month
    """
    return success_response(fetch_rows(sql))


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


@app.route("/api/major-matching-rules", methods=["GET"])
def get_major_matching_rules():
    sql = """
        SELECT
            antecedent,
            consequent,
            confidence,
            lift
        FROM ads_major_matching_rules
        ORDER BY lift DESC, confidence DESC
    """
    return success_response(fetch_rows(sql))


@app.route("/api/job-recommendation", methods=["GET"])
def get_job_recommendation():
    sql = """
        SELECT
            student_id AS student_id,
            student_name AS student_name,
            employer_name AS recommended_job,
            cosine_similarity AS matching_score
        FROM ads_job_recommendation
        WHERE rank_no = 1
        ORDER BY student_id
    """
    return success_response(fetch_rows(sql))


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
