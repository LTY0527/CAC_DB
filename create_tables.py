# -*- coding: utf-8 -*-
"""
数据库表结构初始化脚本。

本脚本面向“基于数据集团多源异构数据的高校需求—招生—培养—就业—监测
一体化平台”，创建基础维度/事实表、岗位需求事实表、清洗日志表、算法
链路日志表、岗位需求预测 ADS 表和安全审计表。适配 MySQL 8.x。
"""

from __future__ import annotations

import io
import logging
import sys
from datetime import datetime

from sqlalchemy import create_engine, text

from config import DB_SETTINGS, DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

LOG_FILE = f"create_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


CORE_TABLES = [
    "dim_student",
    "dim_company",
    "fact_academic",
    "fact_employment",
    "fact_job_demand",
    "ods_cleaning_log",
    "ads_job_demand_monthly",
    "ads_job_skill_heatmap",
    "ads_major_supply_demand_gap",
    "ads_job_demand_forecast",
    "ads_job_demand_forecast_eval",
    "ads_job_demand_forecast_backtest",
    "ads_algorithm_chain_log",
    "sys_audit_log",
]


def get_db_engine():
    """创建数据库连接引擎。"""
    engine = create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("数据库连接成功：%s/%s", DB_SETTINGS["host"], DB_SETTINGS["database"])
    return engine


def create_tables() -> bool:
    """创建或重建核心数据仓库表。"""
    engine = get_db_engine()

    ddl_statements = [
        """
        CREATE TABLE dim_student (
            student_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学生ID',
            student_name VARCHAR(100) NOT NULL COMMENT '学生姓名',
            id_card VARCHAR(20) UNIQUE COMMENT '身份证号',
            gender VARCHAR(10) COMMENT '性别',
            origin_region_code VARCHAR(20) COMMENT '生源地区编码',
            origin_place VARCHAR(100) COMMENT '生源地',
            created_at VARCHAR(100) COMMENT '源系统创建时间',
            school_name VARCHAR(100) COMMENT '学校名称',
            school_level VARCHAR(50) COMMENT '学校层次',
            edu_name VARCHAR(20) COMMENT '学历层次',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_school (school_name),
            INDEX idx_edu_level (edu_name),
            INDEX idx_origin_place (origin_place)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='学生维度表：存储学生画像基础信息'
        """,
        """
        CREATE TABLE dim_company (
            company_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '企业ID',
            employer_name VARCHAR(255) NOT NULL UNIQUE COMMENT '企业名称',
            company_scale VARCHAR(50) COMMENT '企业规模',
            is_top_500 TINYINT DEFAULT 0 COMMENT '是否500强企业',
            is_listed TINYINT DEFAULT 0 COMMENT '是否上市企业',
            strategic_tags JSON COMMENT '战略标签JSON数组',
            reg_capital DECIMAL(15,2) DEFAULT 0.00 COMMENT '注册资本',
            last_year_revenue DECIMAL(15,2) DEFAULT 0.00 COMMENT '上年营收',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_company_scale (company_scale),
            INDEX idx_is_top_500 (is_top_500),
            INDEX idx_is_listed (is_listed)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='企业维度表：存储企业基础画像'
        """,
        """
        CREATE TABLE fact_academic (
            academic_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学业记录ID',
            student_id INT NOT NULL COMMENT '学生ID',
            edu_level VARCHAR(20) COMMENT '学历层次',
            major_code VARCHAR(20) COMMENT '专业代码',
            major_name VARCHAR(100) COMMENT '专业名称',
            discipline_category VARCHAR(100) COMMENT '学科门类',
            major_category VARCHAR(100) COMMENT '专业大类',
            skill_level VARCHAR(20) COMMENT '技能等级',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            CONSTRAINT fk_academic_student FOREIGN KEY (student_id) REFERENCES dim_student(student_id) ON DELETE CASCADE,
            INDEX idx_student_id (student_id),
            INDEX idx_major_code (major_code),
            INDEX idx_major_name (major_name),
            INDEX idx_skill_level (skill_level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='学业事实表：存储学生专业、学历和技能水平'
        """,
        """
        CREATE TABLE fact_employment (
            emp_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '就业记录ID',
            student_id INT NOT NULL COMMENT '学生ID',
            employer_name VARCHAR(255) COMMENT '就业单位',
            avg_salary DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均薪资，仅作为辅助分析字段',
            first_insured_date DATE COMMENT '首次参保日期',
            sh_insurance_status TINYINT DEFAULT 0 COMMENT '上海参保状态',
            leading_industry_tag VARCHAR(50) COMMENT '行业标签',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            CONSTRAINT fk_employment_student FOREIGN KEY (student_id) REFERENCES dim_student(student_id) ON DELETE CASCADE,
            INDEX idx_student_id (student_id),
            INDEX idx_first_insured_date (first_insured_date),
            INDEX idx_sh_insurance_status (sh_insurance_status),
            INDEX idx_leading_industry_tag (leading_industry_tag)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='就业事实表：存储就业去向和薪资辅助信息'
        """,
        """
        CREATE TABLE fact_job_demand (
            demand_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '岗位需求记录ID',
            employer_name VARCHAR(255) COMMENT '企业名称',
            company_id INT NULL COMMENT '企业ID，可关联dim_company',
            job_title VARCHAR(255) NOT NULL COMMENT '岗位名称',
            job_category VARCHAR(100) COMMENT '岗位类别',
            leading_industry_tag VARCHAR(100) COMMENT '行业标签',
            major_name VARCHAR(100) COMMENT '适配专业',
            major_category VARCHAR(100) COMMENT '专业大类',
            city VARCHAR(50) COMMENT '城市',
            publish_date DATE NOT NULL COMMENT '岗位发布日期',
            recruit_count INT DEFAULT 1 COMMENT '招聘人数',
            salary_min DECIMAL(10,2) COMMENT '最低薪资',
            salary_max DECIMAL(10,2) COMMENT '最高薪资',
            salary_avg DECIMAL(10,2) COMMENT '平均薪资',
            education_requirement VARCHAR(50) COMMENT '学历要求',
            experience_requirement VARCHAR(50) COMMENT '经验要求',
            skill_keywords JSON COMMENT '技能关键词JSON数组',
            source_channel VARCHAR(100) COMMENT '数据来源渠道',
            data_batch_id VARCHAR(100) COMMENT '数据批次ID',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            CONSTRAINT fk_job_demand_company FOREIGN KEY (company_id) REFERENCES dim_company(company_id) ON DELETE SET NULL,
            INDEX idx_publish_date (publish_date),
            INDEX idx_major_name (major_name),
            INDEX idx_job_category (job_category),
            INDEX idx_industry_tag (leading_industry_tag),
            INDEX idx_city (city),
            INDEX idx_major_job_month (major_name, job_category, publish_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='岗位需求事实表：存储数据集团企业招聘需求数据'
        """,
        """
        CREATE TABLE ods_cleaning_log (
            log_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '清洗日志ID',
            batch_id VARCHAR(100) COMMENT '数据批次ID',
            source_name VARCHAR(100) COMMENT '数据源名称',
            raw_rows INT DEFAULT 0 COMMENT '原始行数',
            valid_rows INT DEFAULT 0 COMMENT '有效行数',
            invalid_rows INT DEFAULT 0 COMMENT '无效行数',
            duplicate_rows INT DEFAULT 0 COMMENT '重复行数',
            missing_value_rows INT DEFAULT 0 COMMENT '缺失值行数',
            outlier_rows INT DEFAULT 0 COMMENT '异常值行数',
            standardization_desc TEXT COMMENT '清洗标准化说明',
            started_at DATETIME COMMENT '开始时间',
            finished_at DATETIME COMMENT '结束时间',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_batch_source (batch_id, source_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ODS清洗日志表：记录多源异构数据清洗过程'
        """,
        """
        CREATE TABLE ads_job_demand_monthly (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '月度聚合ID',
            major_name VARCHAR(100) COMMENT '专业名称',
            job_category VARCHAR(100) COMMENT '岗位类别',
            industry_tag VARCHAR(100) COMMENT '行业标签',
            city VARCHAR(50) COMMENT '城市',
            demand_month VARCHAR(20) COMMENT '需求月份',
            demand_count DECIMAL(12,2) COMMENT '岗位需求人数',
            company_count INT COMMENT '企业数量',
            avg_salary DECIMAL(10,2) COMMENT '平均薪资',
            skill_keywords_summary JSON COMMENT '技能关键词摘要',
            demand_growth_rate DECIMAL(10,4) COMMENT '环比增长率',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_month_major (demand_month, major_name),
            INDEX idx_major_job (major_name, job_category),
            INDEX idx_city_month (city, demand_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS岗位需求月度特征表'
        """,
        """
        CREATE TABLE ads_job_skill_heatmap (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '技能热力ID',
            major_name VARCHAR(100) COMMENT '专业名称',
            job_category VARCHAR(100) COMMENT '岗位类别',
            skill_name VARCHAR(100) COMMENT '技能名称',
            skill_count INT COMMENT '技能出现次数',
            skill_weight DECIMAL(10,6) COMMENT '技能权重',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_major_job_skill (major_name, job_category, skill_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS岗位技能热力表'
        """,
        """
        CREATE TABLE ads_major_supply_demand_gap (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '供需缺口ID',
            major_name VARCHAR(100) COMMENT '专业名称',
            graduate_count INT COMMENT '毕业生供给人数',
            demand_count DECIMAL(12,2) COMMENT '岗位需求人数',
            gap_count DECIMAL(12,2) COMMENT '供需缺口',
            gap_rate DECIMAL(10,4) COMMENT '供需缺口率',
            gap_level VARCHAR(50) COMMENT '缺口等级',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_major_gap (major_name, gap_level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS专业供需缺口表'
        """,
        """
        CREATE TABLE ads_job_demand_forecast (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '预测结果ID',
            track VARCHAR(255) COMMENT '预测序列名称',
            major_name VARCHAR(100) COMMENT '专业名称',
            job_category VARCHAR(100) COMMENT '岗位类别',
            industry_tag VARCHAR(100) COMMENT '行业标签',
            city VARCHAR(50) COMMENT '城市',
            track_rank INT COMMENT '序列排序',
            forecast_month VARCHAR(20) COMMENT '预测月份',
            predicted_demand_count DECIMAL(12,2) COMMENT '预测岗位需求人数',
            demand_growth_rate DECIMAL(10,4) COMMENT '预测期增长率',
            demand_level VARCHAR(50) COMMENT '需求等级：高需求/中需求/低需求',
            model_name VARCHAR(50) DEFAULT 'LSTM' COMMENT '模型名称',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_major_month (major_name, forecast_month),
            INDEX idx_job_month (job_category, forecast_month),
            INDEX idx_track_rank (track_rank)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS岗位需求人数预测结果表'
        """,
        """
        CREATE TABLE ads_job_demand_forecast_eval (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '评估结果ID',
            metric_name VARCHAR(50) COMMENT '指标名称',
            metric_value DECIMAL(12,4) COMMENT '指标值',
            metric_label VARCHAR(100) COMMENT '指标中文名',
            metric_unit VARCHAR(20) COMMENT '指标单位',
            sample_size INT COMMENT '样本数量',
            train_window_size INT COMMENT '训练窗口数量',
            test_window_size INT COMMENT '测试窗口数量',
            metric_desc TEXT COMMENT '指标说明',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_metric_name (metric_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS岗位需求人数预测评估表'
        """,
        """
        CREATE TABLE ads_job_demand_forecast_backtest (
            id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '回测结果ID',
            track VARCHAR(255) COMMENT '预测序列名称',
            major_name VARCHAR(100) COMMENT '专业名称',
            job_category VARCHAR(100) COMMENT '岗位类别',
            industry_tag VARCHAR(100) COMMENT '行业标签',
            forecast_month VARCHAR(20) COMMENT '回测月份',
            actual_demand_count DECIMAL(12,2) COMMENT '实际岗位需求人数',
            predicted_demand_count DECIMAL(12,2) COMMENT '预测岗位需求人数',
            abs_error DECIMAL(12,2) COMMENT '绝对误差',
            dataset_split VARCHAR(20) COMMENT '数据集划分',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_backtest_track (track),
            INDEX idx_backtest_month (forecast_month)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS岗位需求人数预测回测表'
        """,
        """
        CREATE TABLE ads_algorithm_chain_log (
            chain_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '算法链路日志ID',
            batch_id VARCHAR(100) COMMENT '数据批次ID',
            stage_order INT COMMENT '阶段序号',
            stage_name VARCHAR(100) COMMENT '阶段名称',
            input_tables TEXT COMMENT '输入表',
            output_tables TEXT COMMENT '输出表',
            algorithm_name VARCHAR(100) COMMENT '算法名称',
            status VARCHAR(50) COMMENT '运行状态',
            row_count INT DEFAULT 0 COMMENT '输出行数',
            started_at DATETIME COMMENT '开始时间',
            finished_at DATETIME COMMENT '结束时间',
            cost_seconds DECIMAL(10,2) COMMENT '耗时秒数',
            error_message TEXT COMMENT '错误信息',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_batch_stage (batch_id, stage_order),
            INDEX idx_stage_status (stage_name, status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='ADS算法链路运行日志表'
        """,
        """
        CREATE TABLE sys_audit_log (
            audit_id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '审计日志ID',
            username VARCHAR(100) COMMENT '用户名',
            role VARCHAR(50) COMMENT '角色',
            action_type VARCHAR(100) COMMENT '操作类型',
            target_module VARCHAR(100) COMMENT '目标模块',
            target_table VARCHAR(100) COMMENT '目标数据表',
            request_path VARCHAR(255) COMMENT '请求路径',
            request_method VARCHAR(20) COMMENT '请求方法',
            ip_address VARCHAR(100) COMMENT 'IP地址',
            user_agent TEXT COMMENT '浏览器或客户端标识',
            success TINYINT DEFAULT 1 COMMENT '是否成功',
            detail TEXT COMMENT '操作详情',
            created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            INDEX idx_username_time (username, created_timestamp),
            INDEX idx_action_type (action_type),
            INDEX idx_role (role)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        COMMENT='系统安全审计日志表'
        """,
    ]

    drop_order = [
        "ads_job_demand_forecast_backtest",
        "ads_job_demand_forecast_eval",
        "ads_job_demand_forecast",
        "ads_major_supply_demand_gap",
        "ads_job_skill_heatmap",
        "ads_job_demand_monthly",
        "ads_algorithm_chain_log",
        "ods_cleaning_log",
        "sys_audit_log",
        "fact_job_demand",
        "fact_employment",
        "fact_academic",
        "dim_company",
        "dim_student",
    ]

    try:
        with engine.begin() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for table_name in drop_order:
                conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

            for ddl in ddl_statements:
                conn.execute(text(ddl))
                table_name = ddl.split("CREATE TABLE", 1)[1].split("(", 1)[0].strip()
                logger.info("已创建表：%s", table_name)

        logger.info("数据库表结构初始化完成，共创建 %s 张核心表。", len(CORE_TABLES))
        return True
    except Exception:
        logger.exception("数据库表结构初始化失败")
        return False


def verify_tables(engine) -> bool:
    """校验核心表是否已创建。"""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = :schema_name
                """
            ),
            {"schema_name": DB_SETTINGS["database"]},
        ).fetchall()
    core_set = set(CORE_TABLES)
    existing = sorted(row[0] for row in rows if row[0] in core_set)
    missing = sorted(set(CORE_TABLES) - set(existing))
    if missing:
        logger.error("表结构校验失败，缺少表：%s", ", ".join(missing))
        return False
    logger.info("表结构校验通过：%s", ", ".join(existing))
    return True


def main() -> int:
    logger.info("=" * 80)
    logger.info("高校需求—招生—培养—就业—监测一体化平台：数据库初始化")
    logger.info("=" * 80)
    success = create_tables()
    if not success:
        return 1
    return 0 if verify_tables(get_db_engine()) else 1


if __name__ == "__main__":
    sys.exit(main())
