# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL


TABLE_COLUMNS = {
    "dim_industry": {
        "is_shanghai_leading_industry": "TINYINT DEFAULT 0",
        "leading_industry_name": "VARCHAR(64) NULL",
        "leading_industry_code": "VARCHAR(32) NULL",
        "policy_direction_tags": "TEXT NULL",
    },
    "dim_enterprise": {
        "is_shanghai_leading_enterprise": "TINYINT DEFAULT 0",
        "leading_industry_name": "VARCHAR(64) NULL",
        "leading_industry_code": "VARCHAR(32) NULL",
        "is_six_key_field": "TINYINT DEFAULT 0",
        "is_four_new_track": "TINYINT DEFAULT 0",
        "is_five_future_industry": "TINYINT DEFAULT 0",
        "registered_capital": "DECIMAL(18,2) NULL",
        "established_date": "DATE NULL",
        "registered_address": "VARCHAR(255) NULL",
        "is_listed": "TINYINT DEFAULT 0",
        "is_world_500": "TINYINT DEFAULT 0",
        "is_china_500": "TINYINT DEFAULT 0",
        "is_industry_top_100": "TINYINT DEFAULT 0",
        "annual_revenue": "DECIMAL(18,2) NULL",
        "annual_profit": "DECIMAL(18,2) NULL",
        "annual_tax": "DECIMAL(18,2) NULL",
    },
    "fact_job_posting": {
        "is_shanghai_leading_job": "TINYINT DEFAULT 0",
        "leading_industry_name": "VARCHAR(64) NULL",
        "leading_industry_code": "VARCHAR(32) NULL",
        "job_title": "VARCHAR(128) NULL",
        "job_category": "VARCHAR(128) NULL",
        "contract_type": "VARCHAR(64) NULL",
    },
    "fact_employment": {
        "is_shanghai_leading_employment": "TINYINT DEFAULT 0",
        "leading_industry_name": "VARCHAR(64) NULL",
        "leading_industry_code": "VARCHAR(32) NULL",
        "social_security_status": "VARCHAR(64) NULL",
        "first_shanghai_insurance_month": "VARCHAR(16) NULL",
    },
}


def table_exists(conn, table: str) -> bool:
    return bool(conn.execute(text("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema=DATABASE() AND table_name=:table
    """), {"table": table}).scalar())


def columns(conn, table: str) -> set[str]:
    return {
        row[0]
        for row in conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema=DATABASE() AND table_name=:table
        """), {"table": table})
    }


def add_columns(conn, logs: list[str]) -> None:
    for table, required in TABLE_COLUMNS.items():
        if not table_exists(conn, table):
            logs.append(f"[跳过] 表不存在：{table}")
            continue
        existing = columns(conn, table)
        for column, ddl in required.items():
            if column in existing:
                logs.append(f"[已存在] {table}.{column}")
                continue
            conn.execute(text(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {ddl}"))
            logs.append(f"[新增字段] {table}.{column} {ddl}")


def ensure_summary_table(conn, logs: list[str]) -> None:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ads_leading_industry_employment_summary (
            summary_id BIGINT PRIMARY KEY AUTO_INCREMENT,
            school_id VARCHAR(20),
            school_name VARCHAR(100),
            month VARCHAR(20),
            total_employment_count INT,
            leading_industry_employment_count INT,
            leading_industry_employment_rate DECIMAL(10,4),
            ai_employment_count INT,
            ic_employment_count INT,
            biomed_employment_count INT,
            avg_salary DECIMAL(12,2),
            leading_avg_salary DECIMAL(12,2),
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_leading_summary_school_month (school_id, month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    logs.append("[已确认] ads_leading_industry_employment_summary")


def backfill(conn, logs: list[str]) -> None:
    conn.execute(text("""
        UPDATE dim_industry
        SET is_shanghai_leading_industry = CASE
                WHEN industry_id=2 OR CONCAT(industry_name,' ',COALESCE(policy_direction_tags,'')) REGEXP '人工智能|算法|机器学习|AI|浜哄伐鏅鸿兘|绠楁硶' THEN 1
                WHEN industry_id=3 OR CONCAT(industry_name,' ',COALESCE(policy_direction_tags,'')) REGEXP '集成电路|芯片|半导体|IC|闆嗘垚鐢佃矾|鑺' THEN 1
                WHEN industry_id IN (6,7) OR CONCAT(industry_name,' ',COALESCE(policy_direction_tags,'')) REGEXP '生物医药|药物|制药|医疗|鐢熺墿|鑽|鍖' THEN 1
                ELSE COALESCE(is_shanghai_leading_industry,0)
            END,
            leading_industry_code = CASE
                WHEN industry_id=2 OR CONCAT(industry_name,' ',COALESCE(policy_direction_tags,'')) REGEXP '人工智能|算法|机器学习|AI|浜哄伐鏅鸿兘|绠楁硶' THEN 'AI'
                WHEN industry_id=3 OR CONCAT(industry_name,' ',COALESCE(policy_direction_tags,'')) REGEXP '集成电路|芯片|半导体|IC|闆嗘垚鐢佃矾|鑺' THEN 'IC'
                WHEN industry_id IN (6,7) OR CONCAT(industry_name,' ',COALESCE(policy_direction_tags,'')) REGEXP '生物医药|药物|制药|医疗|鐢熺墿|鑽|鍖' THEN 'BIOMED'
                ELSE leading_industry_code
            END
    """))
    conn.execute(text("""
        UPDATE dim_industry
        SET leading_industry_name = CASE leading_industry_code
            WHEN 'AI' THEN '人工智能'
            WHEN 'IC' THEN '集成电路'
            WHEN 'BIOMED' THEN '生物医药'
            ELSE leading_industry_name
        END
        WHERE is_shanghai_leading_industry=1
    """))
    conn.execute(text("""
        UPDATE dim_enterprise e
        JOIN dim_industry i ON e.industry_id=i.industry_id
        SET e.is_shanghai_leading_enterprise=COALESCE(i.is_shanghai_leading_industry,0),
            e.leading_industry_name=i.leading_industry_name,
            e.leading_industry_code=i.leading_industry_code,
            e.is_six_key_field=CASE WHEN i.is_shanghai_leading_industry=1 THEN 1 ELSE COALESCE(e.is_six_key_field,0) END,
            e.is_four_new_track=CASE WHEN i.leading_industry_code='AI' THEN 1 ELSE COALESCE(e.is_four_new_track,0) END,
            e.is_five_future_industry=CASE WHEN i.is_shanghai_leading_industry=1 THEN 1 ELSE COALESCE(e.is_five_future_industry,0) END,
            e.registered_capital=COALESCE(e.registered_capital, ROUND(1000 + e.enterprise_id * 7.3, 2)),
            e.established_date=COALESCE(e.established_date, DATE_ADD('2008-01-01', INTERVAL MOD(e.enterprise_id, 5000) DAY)),
            e.registered_address=COALESCE(e.registered_address, CONCAT('上海市', COALESCE(e.district,''), '产业园', e.enterprise_id, '号')),
            e.annual_revenue=COALESCE(e.annual_revenue, ROUND(3000 + e.enterprise_id * 11.7, 2)),
            e.annual_profit=COALESCE(e.annual_profit, ROUND((3000 + e.enterprise_id * 11.7) * 0.12, 2)),
            e.annual_tax=COALESCE(e.annual_tax, ROUND((3000 + e.enterprise_id * 11.7) * 0.035, 2))
    """))
    conn.execute(text("""
        UPDATE fact_job_posting p
        JOIN dim_enterprise e ON p.enterprise_id=e.enterprise_id
        JOIN dim_job_category j ON p.job_category_id=j.job_category_id
        SET p.is_shanghai_leading_job=e.is_shanghai_leading_enterprise,
            p.leading_industry_name=e.leading_industry_name,
            p.leading_industry_code=e.leading_industry_code,
            p.job_title=COALESCE(p.job_title, j.job_category_name),
            p.job_category=COALESCE(p.job_category, j.job_category_name),
            p.contract_type=COALESCE(p.contract_type, '劳动合同')
    """))
    conn.execute(text("""
        UPDATE fact_employment emp
        JOIN dim_enterprise e ON emp.enterprise_id=e.enterprise_id
        SET emp.is_shanghai_leading_employment=e.is_shanghai_leading_enterprise,
            emp.leading_industry_name=e.leading_industry_name,
            emp.leading_industry_code=e.leading_industry_code,
            emp.social_security_status=CASE WHEN emp.social_security_verified=1 THEN '在沪参保' ELSE '未核验' END,
            emp.first_shanghai_insurance_month=CASE WHEN emp.social_security_verified=1 THEN emp.employment_month ELSE emp.first_shanghai_insurance_month END
    """))
    conn.execute(text("TRUNCATE TABLE ads_leading_industry_employment_summary"))
    conn.execute(text("""
        INSERT INTO ads_leading_industry_employment_summary
        (school_id, school_name, month, total_employment_count, leading_industry_employment_count,
         leading_industry_employment_rate, ai_employment_count, ic_employment_count, biomed_employment_count,
         avg_salary, leading_avg_salary)
        SELECT e.school_id, s.school_name, e.employment_month,
               COUNT(*),
               SUM(CASE WHEN e.is_shanghai_leading_employment=1 THEN 1 ELSE 0 END),
               ROUND(AVG(CASE WHEN e.is_shanghai_leading_employment=1 THEN 1 ELSE 0 END),4),
               SUM(CASE WHEN e.leading_industry_code='AI' THEN 1 ELSE 0 END),
               SUM(CASE WHEN e.leading_industry_code='IC' THEN 1 ELSE 0 END),
               SUM(CASE WHEN e.leading_industry_code='BIOMED' THEN 1 ELSE 0 END),
               ROUND(AVG(e.salary),2),
               ROUND(AVG(CASE WHEN e.is_shanghai_leading_employment=1 THEN e.salary END),2)
        FROM fact_employment e
        LEFT JOIN dim_school s ON e.school_id=s.school_id
        GROUP BY e.school_id, s.school_name, e.employment_month
    """))
    logs.append("[回填完成] 三大先导产业标签与就业汇总")


def snapshot(conn) -> dict:
    def scalar(sql: str):
        return conn.execute(text(sql)).scalar() or 0
    return {
        "leading_industry_count": int(scalar("SELECT COUNT(*) FROM dim_industry WHERE is_shanghai_leading_industry=1")),
        "leading_enterprise_count": int(scalar("SELECT COUNT(*) FROM dim_enterprise WHERE is_shanghai_leading_enterprise=1")),
        "leading_job_posting_count": int(scalar("SELECT COUNT(*) FROM fact_job_posting WHERE is_shanghai_leading_job=1")),
        "leading_employment_count": int(scalar("SELECT COUNT(*) FROM fact_employment WHERE is_shanghai_leading_employment=1")),
        "shanghai_university_leading_employment_count": int(scalar("""
            SELECT COUNT(*) FROM fact_employment e
            JOIN dim_school s ON e.school_id=s.school_id
            WHERE s.school_name='上海大学' AND e.is_shanghai_leading_employment=1
        """)),
    }


def main() -> None:
    logs: list[str] = []
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        add_columns(conn, logs)
        ensure_summary_table(conn, logs)
        backfill(conn, logs)
        result = snapshot(conn)
    print("\n".join(logs))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
