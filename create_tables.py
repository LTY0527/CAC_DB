"""
MySQL 表结构初始化脚本
用于创建 CAC_DB 数据仓库的所有必要表
"""

import io
import logging
from sqlalchemy import create_engine, text
import sys
from datetime import datetime
import os
import sys
from config import DB_SETTINGS, DB_URL_PYMYSQL
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ================================================================
# 日志配置
# ================================================================
log_file = f"create_tables_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DB_CONNECTION_STRING = DB_URL_PYMYSQL

def get_db_engine():
    """创建数据库连接引擎"""
    try:
        engine = create_engine(DB_CONNECTION_STRING, pool_pre_ping=True)
        logger.info(" 数据库连接引擎创建成功")
        return engine
    except Exception as e:
        logger.error(f" 数据库连接引擎创建失败: {str(e)}")
        raise

def create_tables():
    """创建所有表结构"""
    try:
        engine = get_db_engine()
        
        with engine.begin() as conn:
            
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            
            # ============================================================
            # 1. dim_student - 学生维度表
            # ============================================================
            logger.info("\n【创建表】 dim_student (学生维度表)")
            conn.execute(text("DROP TABLE IF EXISTS dim_student;"))
            conn.execute(text("""

                
                CREATE TABLE dim_student (
                    student_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学生ID',
                    student_name VARCHAR(100) NOT NULL COMMENT '学生姓名',
                    id_card VARCHAR(20) UNIQUE COMMENT '身份证号',
                    gender VARCHAR(10) COMMENT '性别',
                    origin_region_code VARCHAR(20) COMMENT '原籍地区编码',
                    origin_place VARCHAR(100) COMMENT '原籍地点',
                    created_at VARCHAR(100) COMMENT '创建时间',
                    school_name VARCHAR(100) COMMENT '学校名称',
                    school_level VARCHAR(50) COMMENT '学校等级',
                    edu_name VARCHAR(20) COMMENT '教育类型(本科/硕士/博士)',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据库创建时间',
                    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据库更新时间',
                    
                    INDEX idx_school (school_name),
                    INDEX idx_edu_level (edu_name),
                    INDEX idx_origin_place (origin_place)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
                COMMENT='学生维度表：存储学生基本信息';
            """))
            logger.info("   dim_student 表创建成功")
            
            # ============================================================
            # 2. dim_company - 企业维度表
            # ============================================================
            logger.info("\n【创建表】 dim_company (企业维度表)")
            conn.execute(text("DROP TABLE IF EXISTS dim_company;"))
            conn.execute(text("""
                
                
                CREATE TABLE dim_company (
                    company_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '企业ID',
                    employer_name VARCHAR(255) NOT NULL UNIQUE COMMENT '企业名称',
                    company_scale VARCHAR(50) COMMENT '企业规模(大型/中型/小型)',
                    is_top_500 TINYINT DEFAULT 0 COMMENT '是否为500强企业',
                    is_listed TINYINT DEFAULT 0 COMMENT '是否为上市企业',
                    strategic_tags JSON COMMENT '战略标签(JSON)',
                    reg_capital DECIMAL(15, 2) DEFAULT 0.00 COMMENT '注册资本',
                    last_year_revenue DECIMAL(15, 2) DEFAULT 0.00 COMMENT '去年营收',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据库创建时间',
                    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据库更新时间',
                    
                    INDEX idx_company_scale (company_scale),
                    INDEX idx_is_top_500 (is_top_500),
                    INDEX idx_is_listed (is_listed)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
                COMMENT='企业维度表：存储企业基本信息';
            """))
            logger.info("   dim_company 表创建成功")
            
            # ============================================================
            # 3. fact_academic - 学业成绩事实表
            # ============================================================
            logger.info("\n【创建表】 fact_academic (学业成绩事实表)")
            conn.execute(text("DROP TABLE IF EXISTS fact_academic;"))
            conn.execute(text("""
              
                
                CREATE TABLE fact_academic (
                    academic_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '学业记录ID',
                    student_id INT NOT NULL COMMENT '学生ID',
                    edu_level VARCHAR(20) COMMENT '教育等级',
                    major_code VARCHAR(20) COMMENT '专业代码',
                    major_name VARCHAR(100) COMMENT '专业名称',
                    discipline_category VARCHAR(100) COMMENT '学科分类',
                    major_category VARCHAR(100) COMMENT '专业分类',
                    skill_level VARCHAR(20) COMMENT '技能等级(初/中/高)',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据库创建时间',
                    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据库更新时间',
                    
                    FOREIGN KEY (student_id) REFERENCES dim_student(student_id) ON DELETE CASCADE,
                    INDEX idx_student_id (student_id),
                    INDEX idx_major_code (major_code),
                    INDEX idx_major_name (major_name),
                    INDEX idx_skill_level (skill_level)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
                COMMENT='学业成绩事实表：存储学生专业及成绩信息';
            """))
            logger.info("   fact_academic 表创建成功")
            
            # ============================================================
            # 4. fact_employment - 就业事实表
            # ============================================================
            logger.info("\n【创建表】 fact_employment (就业事实表)")
            conn.execute(text("DROP TABLE IF EXISTS fact_employment;"))
            conn.execute(text("""
                
                CREATE TABLE fact_employment (
                    emp_id INT PRIMARY KEY AUTO_INCREMENT COMMENT '就业记录ID',
                    student_id INT NOT NULL COMMENT '学生ID',
                    employer_name VARCHAR(255) COMMENT '雇主名称',
                    avg_salary DECIMAL(10, 2) DEFAULT 0.00 COMMENT '平均薪资',
                    first_insured_date DATE COMMENT '首次参保日期',
                    sh_insurance_status TINYINT DEFAULT 0 COMMENT '上海社保状态',
                    leading_industry_tag VARCHAR(50) COMMENT '行业标签',
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据库创建时间',
                    updated_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '数据库更新时间',
                    
                    FOREIGN KEY (student_id) REFERENCES dim_student(student_id) ON DELETE CASCADE,
                    INDEX idx_student_id (student_id),
                    INDEX idx_first_insured_date (first_insured_date),
                    INDEX idx_sh_insurance_status (sh_insurance_status),
                    INDEX idx_leading_industry_tag (leading_industry_tag)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
                COMMENT='就业事实表：存储学生就业信息';
            """))
            logger.info("   fact_employment 表创建成功")
            
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        
        logger.info("\n 所有表创建成功！")
        return True
        
    except Exception as e:
        import traceback
        logger.error(" 表创建失败:")
        logger.error(traceback.format_exc())
        return False

def verify_tables(engine):
    """验证表是否创建成功"""
    logger.info("\n【验证表结构】")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = :database_name
                AND TABLE_NAME IN ('dim_student', 'dim_company', 'fact_academic', 'fact_employment')
            """), {"database_name": DB_SETTINGS["database"]})
            tables = [row[0] for row in result]
            
            if len(tables) == 4:
                logger.info("验证成功，所有表都已创建:")
                for table in sorted(tables):
                    logger.info(f"  - {table}")
                return True
            else:
                logger.warning(f" 发现 {len(tables)}/4 个表: {tables}")
                return False
    except Exception as e:
        logger.error(f"验证失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("="*70)
    logger.info("数据库表结构初始化")
    logger.info("="*70)
    
    try:
        engine = get_db_engine()
        success = create_tables()
        
        if success:
            verify_tables(engine)
            logger.info("\n" + "="*70)
            logger.info(" 初始化完成，数据库已准备就绪")
            logger.info("="*70)
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f" 初始化失败: {str(e)}")
        sys.exit(1)
