# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import DB_URL

TABLE_ORDER = [
    "sys_audit_log", "sys_user_account",
    "ads_algorithm_chain_log", "ads_job_recommendation", "ads_major_optimization", "ads_training_rules",
    "ads_school_compare_summary",
    "ads_leading_industry_employment_summary",
    "ads_enrollment_matching", "ads_job_demand_forecast_backtest", "ads_job_demand_forecast_eval",
    "ads_job_demand_forecast", "ads_job_demand_features",
    "fact_policy_signal", "fact_course_skill", "fact_enrollment_plan", "fact_employment",
    "fact_graduate", "fact_job_posting", "dim_enterprise", "dim_job_category", "dim_industry",
    "bridge_school_major", "dim_major_catalog", "dim_school",
]

DDL = [
    """CREATE TABLE IF NOT EXISTS dim_school (
        school_id VARCHAR(20) PRIMARY KEY, school_name VARCHAR(100) NOT NULL UNIQUE,
        school_type VARCHAR(100), city VARCHAR(50), district VARCHAR(50),
        discipline_strength_tags TEXT, major_count INT, first_class_major_count INT,
        industry_affinity TEXT, salary_level_factor DECIMAL(8,4),
        employment_stability_factor DECIMAL(8,4), research_factor DECIMAL(8,4),
        application_factor DECIMAL(8,4), policy_response_factor DECIMAL(8,4),
        INDEX idx_school_city (city), INDEX idx_school_name (school_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS dim_major_catalog (
        major_code VARCHAR(20) PRIMARY KEY, major_name VARCHAR(120) NOT NULL UNIQUE,
        discipline_category VARCHAR(50), major_class VARCHAR(80), degree_type VARCHAR(50),
        study_years INT, is_controlled TINYINT, is_special TINYINT,
        is_new_strategy_major TINYINT, policy_direction_tags TEXT,
        is_real_display_major TINYINT DEFAULT 0,
        is_catalog_placeholder TINYINT DEFAULT 0,
        display_priority INT DEFAULT 0,
        salary_rank_weight DECIMAL(8,4) DEFAULT 0,
        industry_trend_tags TEXT,
        INDEX idx_major_discipline (discipline_category), INDEX idx_major_class (major_class),
        INDEX idx_major_display (is_real_display_major, is_catalog_placeholder, display_priority)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS bridge_school_major (
        school_id VARCHAR(20), major_code VARCHAR(20), is_enrolling TINYINT,
        is_ace_major TINYINT, is_first_class_major TINYINT,
        school_major_strength_score DECIMAL(8,2), historical_enrollment_scale INT,
        major_status VARCHAR(50), PRIMARY KEY (school_id, major_code),
        INDEX idx_bridge_school (school_id), INDEX idx_bridge_major (major_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS dim_industry (
        industry_id INT PRIMARY KEY, industry_name VARCHAR(100) NOT NULL,
        is_shanghai_leading_industry TINYINT DEFAULT 0,
        leading_industry_name VARCHAR(64) NULL,
        leading_industry_code VARCHAR(32) NULL,
        policy_direction_tags TEXT, base_growth_factor DECIMAL(8,4),
        INDEX idx_industry_name (industry_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS dim_job_category (
        job_category_id INT PRIMARY KEY, job_category_name VARCHAR(100) NOT NULL,
        industry_id INT, job_group VARCHAR(100), computer_related TINYINT,
        skill_tags TEXT, compatible_major_classes TEXT, salary_min_base INT,
        salary_max_base INT, demand_growth_level VARCHAR(20), policy_direction_tags TEXT,
        INDEX idx_job_industry (industry_id), INDEX idx_job_computer (computer_related)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS dim_enterprise (
        enterprise_id INT PRIMARY KEY, enterprise_name VARCHAR(160), industry_id INT,
        city VARCHAR(50), district VARCHAR(50), enterprise_scale VARCHAR(50),
        ownership_type VARCHAR(50), is_high_tech TINYINT, is_specialized_new TINYINT,
        is_shanghai_leading_enterprise TINYINT DEFAULT 0,
        leading_industry_name VARCHAR(64) NULL,
        leading_industry_code VARCHAR(32) NULL,
        is_six_key_field TINYINT DEFAULT 0,
        is_four_new_track TINYINT DEFAULT 0,
        is_five_future_industry TINYINT DEFAULT 0,
        registered_capital DECIMAL(18,2) NULL,
        established_date DATE NULL,
        registered_address VARCHAR(255) NULL,
        is_listed TINYINT DEFAULT 0,
        is_world_500 TINYINT DEFAULT 0,
        is_china_500 TINYINT DEFAULT 0,
        is_industry_top_100 TINYINT DEFAULT 0,
        annual_revenue DECIMAL(18,2) NULL,
        annual_profit DECIMAL(18,2) NULL,
        annual_tax DECIMAL(18,2) NULL,
        salary_factor DECIMAL(8,4), hiring_stability_factor DECIMAL(8,4),
        INDEX idx_ent_industry (industry_id), INDEX idx_ent_city (city)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS fact_job_posting (
        posting_id BIGINT PRIMARY KEY, enterprise_id INT, industry_id INT, job_category_id INT,
        month VARCHAR(20), city VARCHAR(50), demand_count INT, salary_min INT, salary_max INT,
        education_required VARCHAR(30), experience_level VARCHAR(30), skill_tags TEXT,
        preferred_major_codes TEXT, policy_direction_tags TEXT, school_preference_level DECIMAL(8,2),
        is_shanghai_leading_job TINYINT DEFAULT 0,
        leading_industry_name VARCHAR(64) NULL,
        leading_industry_code VARCHAR(32) NULL,
        job_title VARCHAR(128) NULL,
        job_category VARCHAR(128) NULL,
        contract_type VARCHAR(64) NULL,
        INDEX idx_post_month (month), INDEX idx_post_city (city),
        INDEX idx_post_industry_job (industry_id, job_category_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS fact_graduate (
        graduate_id BIGINT PRIMARY KEY, school_id VARCHAR(20), major_code VARCHAR(20),
        graduation_year INT, gender VARCHAR(10), degree_level VARCHAR(20), gpa_level VARCHAR(10),
        skill_tags TEXT, internship_count INT, certification_tags TEXT, job_intention_tags TEXT,
        INDEX idx_grad_school (school_id), INDEX idx_grad_major (major_code), INDEX idx_grad_year (graduation_year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS fact_employment (
        employment_id BIGINT PRIMARY KEY, graduate_id BIGINT, school_id VARCHAR(20), major_code VARCHAR(20),
        enterprise_id INT, industry_id INT, job_category_id INT, employment_month VARCHAR(20),
        salary INT, employment_type VARCHAR(40), city VARCHAR(50), match_score DECIMAL(8,2),
        is_major_related TINYINT, social_security_verified TINYINT, employment_quality_level VARCHAR(20),
        is_shanghai_leading_employment TINYINT DEFAULT 0,
        leading_industry_name VARCHAR(64) NULL,
        leading_industry_code VARCHAR(32) NULL,
        social_security_status VARCHAR(64) NULL,
        first_shanghai_insurance_month VARCHAR(16) NULL,
        INDEX idx_emp_school (school_id), INDEX idx_emp_major (major_code),
        INDEX idx_emp_industry_job (industry_id, job_category_id), INDEX idx_emp_month (employment_month),
        INDEX idx_emp_city (city)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_leading_industry_employment_summary (
        summary_id BIGINT PRIMARY KEY AUTO_INCREMENT,
        school_id VARCHAR(20), school_name VARCHAR(100), month VARCHAR(20),
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
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_school_compare_summary (
        summary_id BIGINT PRIMARY KEY AUTO_INCREMENT,
        school_id VARCHAR(20), school_name VARCHAR(100),
        major_code VARCHAR(20), major_name VARCHAR(120), discipline_category VARCHAR(50),
        employment_count INT, graduate_count INT, employment_rate DECIMAL(10,4),
        avg_salary DECIMAL(12,2),
        high_quality_employment_count INT, high_quality_employment_rate DECIMAL(10,4),
        leading_industry_employment_count INT, leading_industry_employment_rate DECIMAL(10,4),
        top_industry_name VARCHAR(100), top_industry_count INT, top_industry_rate DECIMAL(10,4),
        industry_distribution_json JSON NULL,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_school_compare_scope (school_id, major_code),
        INDEX idx_school_compare_major (major_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS fact_enrollment_plan (
        plan_id BIGINT PRIMARY KEY, school_id VARCHAR(20), major_code VARCHAR(20), year INT,
        planned_quota INT, actual_enrollment INT, applicant_count INT, first_choice_rate DECIMAL(8,4),
        admission_score_avg INT, enrollment_satisfaction_score DECIMAL(8,2),
        INDEX idx_enroll_school_major_year (school_id, major_code, year), INDEX idx_enroll_year (year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS fact_course_skill (
        course_id BIGINT PRIMARY KEY, school_id VARCHAR(20), major_code VARCHAR(20),
        course_name VARCHAR(180), skill_tags TEXT, course_type VARCHAR(50), practice_hours INT,
        industry_alignment_score DECIMAL(8,2), INDEX idx_course_school_major (school_id, major_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS fact_policy_signal (
        policy_id BIGINT PRIMARY KEY, month VARCHAR(20), policy_direction VARCHAR(80),
        industry_id INT, major_code VARCHAR(20), policy_heat DECIMAL(8,2), city_support_score DECIMAL(8,2),
        strategy_level VARCHAR(50), description TEXT,
        INDEX idx_policy_month (month), INDEX idx_policy_industry_major (industry_id, major_code)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_job_demand_features (
        feature_id BIGINT PRIMARY KEY AUTO_INCREMENT, month VARCHAR(20), school_id VARCHAR(20),
        school_name VARCHAR(100), major_code VARCHAR(20), major_name VARCHAR(120),
        industry_id INT, industry_name VARCHAR(100), job_category_id INT, job_category_name VARCHAR(100),
        demand_count_sum DECIMAL(14,2), posting_count INT, avg_salary DECIMAL(12,2),
        policy_heat DECIMAL(8,2), employment_rate DECIMAL(8,4), match_score DECIMAL(8,4),
        avg_match_score DECIMAL(8,4), skill_gap_score DECIMAL(8,4), enrollment_pressure DECIMAL(8,4),
        school_major_strength_score DECIMAL(8,2), major_strength_score DECIMAL(8,2),
        school_industry_affinity DECIMAL(8,4),
        INDEX idx_features_main (month, school_id, major_code, industry_id, job_category_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_job_demand_forecast (
        forecast_id BIGINT PRIMARY KEY AUTO_INCREMENT, school_id VARCHAR(20), school_name VARCHAR(100),
        major_code VARCHAR(20), major_name VARCHAR(120), industry_id INT, industry_name VARCHAR(100),
        job_category_id INT, job_category_name VARCHAR(100), forecast_month VARCHAR(20),
        predicted_demand_count DECIMAL(14,2), lower_bound DECIMAL(14,2), upper_bound DECIMAL(14,2),
        avg_salary DECIMAL(12,2), demand_growth_rate DECIMAL(10,4), demand_level VARCHAR(30),
        mape DECIMAL(8,4), model_name VARCHAR(80), track VARCHAR(220), track_rank INT,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_forecast_main (school_id, major_code, industry_id, job_category_id, forecast_month)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_job_demand_forecast_eval (
        id BIGINT PRIMARY KEY AUTO_INCREMENT, metric_name VARCHAR(50), metric_value DECIMAL(12,4),
        metric_label VARCHAR(100), metric_unit VARCHAR(30), sample_size INT, train_window_size INT,
        test_window_size INT, metric_desc TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_job_demand_forecast_backtest (
        id BIGINT PRIMARY KEY AUTO_INCREMENT, school_id VARCHAR(20), major_code VARCHAR(20),
        industry_id INT, job_category_id INT, forecast_month VARCHAR(20),
        actual_demand_count DECIMAL(14,2), predicted_demand_count DECIMAL(14,2),
        abs_error DECIMAL(14,2), dataset_split VARCHAR(20),
        INDEX idx_backtest_key (school_id, major_code, industry_id, job_category_id, forecast_month)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_enrollment_matching (
        matching_id BIGINT PRIMARY KEY AUTO_INCREMENT, school_id VARCHAR(20), school_name VARCHAR(100),
        major_code VARCHAR(20), major_name VARCHAR(120), year INT,
        match_score DECIMAL(8,4), matching_score DECIMAL(8,4), sample_count INT, sample_size INT,
        enrollment_quota INT, applicant_count INT, employment_rate DECIMAL(8,4), avg_salary DECIMAL(12,2),
        demand_growth_rate DECIMAL(10,4), policy_heat DECIMAL(8,2), recommendation_type VARCHAR(30),
        recommendation_action VARCHAR(40), recommendation_reason TEXT, precision_at_k DECIMAL(8,4),
        job_demand_growth_score DECIMAL(8,4), employment_quality_score DECIMAL(8,4), salary_score DECIMAL(8,4),
        enrollment_heat_score DECIMAL(8,4), policy_heat_score DECIMAL(8,4),
        school_major_strength_score DECIMAL(8,4), explanation TEXT,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_matching_main (school_id, major_code, year)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_training_rules (
        rule_id BIGINT PRIMARY KEY AUTO_INCREMENT, rule_title VARCHAR(120), antecedents TEXT, consequents TEXT,
        support DECIMAL(8,4), confidence DECIMAL(8,4), lift DECIMAL(8,4), evidence_score DECIMAL(8,4),
        related_major_code VARCHAR(20), related_major_name VARCHAR(120),
        related_job_category_id INT, related_job_category_name VARCHAR(100), suggestion TEXT,
        INDEX idx_rule_major_job (related_major_code, related_job_category_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_major_optimization (
        optimization_id BIGINT PRIMARY KEY AUTO_INCREMENT, school_id VARCHAR(20), school_name VARCHAR(100),
        major_code VARCHAR(20), major_name VARCHAR(120), discipline_category VARCHAR(50),
        primary_suggestion_type VARCHAR(30), secondary_tags JSON NULL, suggestion_type VARCHAR(50),
        suggestion_level VARCHAR(20), suggestion_title VARCHAR(160), suggestion_reason TEXT,
        employment_rate DECIMAL(8,4), avg_salary DECIMAL(12,2), demand_growth_rate DECIMAL(10,4),
        skill_gap_score DECIMAL(8,4), policy_heat DECIMAL(8,2), match_score DECIMAL(8,4),
        avg_match_score DECIMAL(8,4), evidence_score DECIMAL(8,4), rule_evidence_score DECIMAL(8,4),
        priority_score DECIMAL(10,2), explanation TEXT, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_major_opt (school_id, major_code, primary_suggestion_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_job_recommendation (
        recommendation_id BIGINT PRIMARY KEY AUTO_INCREMENT, graduate_id BIGINT, school_id VARCHAR(20),
        school_name VARCHAR(100), major_code VARCHAR(20), major_name VARCHAR(120), enterprise_id INT,
        enterprise_name VARCHAR(160), industry_id INT, industry_name VARCHAR(100),
        job_category_id INT, job_category_name VARCHAR(100), similarity_score DECIMAL(8,4),
        matching_score DECIMAL(8,4), confidence_level VARCHAR(20), predicted_demand_count DECIMAL(14,2),
        salary_reference DECIMAL(12,2), rank_no INT, reason_text TEXT, recommendation_reason TEXT,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_job_rec_grad (graduate_id), INDEX idx_job_rec_school_major (school_id, major_code),
        INDEX idx_job_rec_enterprise (enterprise_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sys_user_account (
        user_id BIGINT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(64) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL, hash_algo VARCHAR(32) NOT NULL DEFAULT 'scrypt',
        hash_version VARCHAR(32) NOT NULL DEFAULT 'v1', role VARCHAR(32) NOT NULL, school_id VARCHAR(32) NULL,
        display_name VARCHAR(64), email VARCHAR(128), phone VARCHAR(32), account_status VARCHAR(32) NOT NULL DEFAULT 'active',
        failed_login_count INT NOT NULL DEFAULT 0, failed_attempts INT NOT NULL DEFAULT 0,
        last_failed_login_at DATETIME NULL, lock_until DATETIME NULL, last_login_at DATETIME NULL,
        password_updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_user_role (role), INDEX idx_user_school (school_id), INDEX idx_user_status (account_status)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sys_audit_log (
        audit_id BIGINT PRIMARY KEY AUTO_INCREMENT, user_id BIGINT NULL, username VARCHAR(64),
        role VARCHAR(32), school_id VARCHAR(32) NULL, action VARCHAR(80), module VARCHAR(120), ip VARCHAR(80),
        detail_json JSON NULL, action_type VARCHAR(64) NULL, module_name VARCHAR(100) NULL,
        target_type VARCHAR(64) NULL, target_id VARCHAR(128) NULL, request_path VARCHAR(255) NULL,
        request_method VARCHAR(16) NULL, result_status VARCHAR(20) NULL, message VARCHAR(255) NULL,
        ip_address VARCHAR(64) NULL, user_agent VARCHAR(255) NULL, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_audit_user (user_id), INDEX idx_audit_created (created_at),
        INDEX idx_audit_module (module), INDEX idx_audit_module_name (module_name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS ads_algorithm_chain_log (
        chain_id BIGINT PRIMARY KEY AUTO_INCREMENT, batch_id VARCHAR(80), stage_order INT,
        stage_name VARCHAR(120), input_tables TEXT, output_tables TEXT, algorithm_name VARCHAR(120),
        status VARCHAR(30), row_count INT, started_at DATETIME, finished_at DATETIME,
        cost_seconds DECIMAL(10,2), error_message TEXT, created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    engine = create_engine(DB_URL, pool_pre_ping=True)
    with engine.begin() as conn:
        if args.reset:
            conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            for table in TABLE_ORDER:
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
        for ddl in DDL:
            conn.execute(text(ddl))
    print("数据库表结构初始化完成。")


if __name__ == "__main__":
    main()
