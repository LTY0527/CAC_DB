import pandas as pd
from sqlalchemy import create_engine, text, event
import logging
import time
import os
import sys
from datetime import datetime
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# ================================================================
# 日志配置
# ================================================================
log_file = f"mysql_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ================================================================
# 数据库配置 (使用 pymysql 驱动获得最高稳定性)
# ================================================================
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'bigdata',
    'charset': 'utf8mb4'
}

DB_CONNECTION_STRING = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"

# ================================================================
# 四张表配置 (维度表 + 事实表)
# ================================================================
IMPORT_TASKS = [
    {
        'file': 'dim_student.csv', 
        'table': 'dim_student',
        'description': '学生维度表',
        'primary_key': 'student_id'
    },
    {
        'file': 'dim_company.csv', 
        'table': 'dim_company',
        'description': '企业维度表',
        'primary_key': 'company_id'
    },
    {
        'file': 'fact_academic.csv', 
        'table': 'fact_academic',
        'description': '学业成绩事实表',
        'primary_key': 'academic_id'
    },
    {
        'file': 'fact_employment.csv', 
        'table': 'fact_employment',
        'description': '就业事实表',
        'primary_key': 'emp_id'
    }
]

def get_db_engine():
    """
    创建数据库连接引擎，配置连接池
    """
    try:
        engine = create_engine(
            DB_CONNECTION_STRING,
            # 连接池配置
            pool_size=10,           # 连接池大小
            max_overflow=20,        # 最大溢出连接数
            pool_pre_ping=True,     # 每次获取连接前检测连接有效性
            pool_recycle=3600,      # 1小时回收过期连接
            echo=False
        )
        logger.info(" 数据库连接引擎创建成功")
        return engine
    except Exception as e:
        logger.error(f" 数据库连接引擎创建失败: {str(e)}")
        raise

def verify_database_connection(engine):
    """
    验证数据库连接是否可用
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info(" 数据库连接验证成功")
            return True
    except Exception as e:
        logger.error(f"数据库连接验证失败: {str(e)}")
        return False

def create_tables_if_not_exist(engine):
    """
    自动创建表结构（如果表不存在）
    """
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # dim_student 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_student (
                student_id INT PRIMARY KEY AUTO_INCREMENT,
                student_name VARCHAR(100) NOT NULL,
                id_card VARCHAR(20) UNIQUE,
                gender VARCHAR(10),
                origin_region_code VARCHAR(20),
                origin_place VARCHAR(100),
                created_at VARCHAR(100),
                school_name VARCHAR(100),
                school_level VARCHAR(50),
                edu_name VARCHAR(20),
                INDEX idx_school (school_name),
                INDEX idx_edu_level (edu_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))
        logger.info("   dim_student 表结构检查完成")
        
        # dim_company 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_company (
                company_id INT PRIMARY KEY AUTO_INCREMENT,
                employer_name VARCHAR(255) NOT NULL UNIQUE,
                company_scale VARCHAR(50),
                is_top_500 TINYINT,
                is_listed TINYINT,
                strategic_tags JSON,
                reg_capital DECIMAL(15, 2),
                last_year_revenue DECIMAL(15, 2),
                INDEX idx_company_scale (company_scale)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))
        logger.info("   dim_company 表结构检查完成")
        
        # fact_academic 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_academic (
                academic_id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT NOT NULL,
                edu_level VARCHAR(20),
                major_code VARCHAR(20),
                major_name VARCHAR(100),
                discipline_category VARCHAR(100),
                major_category VARCHAR(100),
                skill_level VARCHAR(20),
                FOREIGN KEY (student_id) REFERENCES dim_student(student_id) ON DELETE CASCADE,
                INDEX idx_student_id (student_id),
                INDEX idx_major_code (major_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))
        logger.info("   fact_academic 表结构检查完成")
        
        # fact_employment 表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_employment (
                emp_id INT PRIMARY KEY AUTO_INCREMENT,
                student_id INT NOT NULL,
                employer_name VARCHAR(255),
                avg_salary DECIMAL(10, 2),
                first_insured_date DATE,
                sh_insurance_status TINYINT,
                leading_industry_tag VARCHAR(50),
                FOREIGN KEY (student_id) REFERENCES dim_student(student_id) ON DELETE CASCADE,
                INDEX idx_student_id (student_id),
                INDEX idx_first_insured_date (first_insured_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """))
        logger.info("   fact_employment 表结构检查完成")
        
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

def clear_table_data(conn, table_name):
    """
    清空表中已有数据（保留表结构和约束）
    """
    try:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conn.execute(text(f"TRUNCATE TABLE {table_name};"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        logger.info(f"   {table_name} 历史数据已清空")
        return True
    except Exception as e:
        logger.warning(f"   {table_name} 清空失败（表可能不存在）: {str(e)}")
        return False

def validate_csv_file(file_path):
    """
    验证 CSV 文件的有效性
    """
    if not os.path.exists(file_path):
        logger.error(f" CSV 文件不存在: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig', nrows=1)
        logger.info(f"   CSV 文件验证成功: {file_path}")
        return df
    except Exception as e:
        logger.error(f" CSV 文件读取失败: {file_path}, 错误: {str(e)}")
        return None

def import_single_table(engine, task):
    """
    导入单个表的数据
    """
    file_path = task['file']
    table_name = task['table']
    description = task['description']
    
    logger.info(f"\n【开始导入】 {description} [{table_name}]")
    logger.info(f"  数据源文件: {file_path}")
    
    # 1. 验证文件存在
    if not os.path.exists(file_path):
        logger.warning(f"   跳过：文件不存在")
        return False
    
    try:
        # 2. 读取 CSV 文件
        logger.info(f"   正在读取 CSV 文件...")
        start_time = time.time()
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        read_time = time.time() - start_time
        logger.info(f"   读取完成，耗时 {read_time:.2f}s，共 {len(df)} 条记录，{len(df.columns)} 列")
        
        # 3. 数据清洗与转换
        logger.info(f"  → 正在清洗数据...")
        if table_name == 'fact_employment':
            df['first_insured_date'] = pd.to_datetime(df['first_insured_date']).dt.date
            logger.info(f"   日期字段已转换为 DATE 类型")
        
        # 4. 数据类型验证
        logger.info(f"  → 正在验证数据类型...")
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            logger.warning(f"  ⚠ 发现空值字段: {dict(null_counts[null_counts > 0])}")
        
        # 5. 执行数据库写入
        with engine.begin() as conn:
            # 清空旧数据
            clear_table_data(conn, table_name)
            
            # 批量写入新数据
            logger.info(f"  → 正在执行批量插入...")
            write_start = time.time()
            df.to_sql(
                name=table_name,
                con=conn,
                if_exists='append',      # 数据表已清空，使用 append 模式
                index=False,
                chunksize=2000,          # 每批次 2000 条记录
                method='multi'           # 使用多值 INSERT 提升性能
            )
            write_time = time.time() - write_start
        
        total_time = time.time() - start_time
        logger.info(f"【完成】 {table_name} - {len(df)} 条记录, 总耗时 {total_time:.2f}s (写入耗时 {write_time:.2f}s)")
        return True
        
    except Exception as e:
        import traceback
        logger.error(f"【失败】 {table_name} 导入异常:")
        logger.error(traceback.format_exc())
        return False

def import_all_data():
    """
    主导入流程：按顺序导入四张表
    """
    logger.info("="*70)
    logger.info("开始执行数据仓库同步任务")
    logger.info("="*70)
    
    try:
        # 1. 创建数据库连接
        engine = get_db_engine()
        
        # 2. 验证数据库连接
        if not verify_database_connection(engine):
            logger.error("数据库连接失败，任务中止")
            return False
        
        # 3. 创建表结构
        logger.info("\n【步骤 1】 创建/检查表结构")
        try:
            create_tables_if_not_exist(engine)
            logger.info(" 所有表结构已就绪")
        except Exception as e:
            logger.error(f" 表结构创建失败: {str(e)}")
            return False
        
        # 4. 导入数据
        logger.info("\n【步骤 2】 导入数据")
        success_count = 0
        for task in IMPORT_TASKS:
            if import_single_table(engine, task):
                success_count += 1
        
        # 5. 显示统计信息
        logger.info("\n" + "="*70)
        logger.info(f"数据导入完成: {success_count}/{len(IMPORT_TASKS)} 个表成功")
        if success_count == len(IMPORT_TASKS):
            logger.info(" 所有数据已成功写入 MySQL 数据库")
        logger.info("="*70)
        
        return success_count == len(IMPORT_TASKS)
        
    except Exception as e:
        import traceback
        logger.error("导入过程出现致命异常:")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = import_all_data()
    sys.exit(0 if success else 1)