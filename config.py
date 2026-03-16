import os

# ==========================================
# 0. 基础路径配置 (确保 JAR 包精准定位)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 修正：确保此处文件名与你 libs 文件夹下的文件名完全一致
JAR_PATH = os.path.join(BASE_DIR, "libs", "mysql-connector-java-8.0.11.jar")

# ==========================================
# 1. MySQL 数据库配置
# ==========================================
DB_SETTINGS = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456", # 确认密码已修改
    "database": "bigdata",
    "driver": "com.mysql.cj.jdbc.Driver"
}

# 构造 SQLAlchemy 连接字符串 (用于 data_factory.py)
DB_URL = f"mysql+mysqlconnector://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"

# 构造 Spark JDBC 连接 URL (用于 Spark_FP_Growth.py)
# 增加 serverTimezone 以避免 8.0 系列驱动常见的时区报错
# 建议直接替换 config.py 中的 JDBC_URL

# 修正后的 JDBC URL 构造逻辑
# 修正后的 JDBC URL 构造逻辑
jdbc_url = (
    f"jdbc:mysql://{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
    "?serverTimezone=Asia/Shanghai&useSSL=false&allowPublicKeyRetrieval=true"
)

# ==========================================
# 2. Hadoop & Spark 配置
# ==========================================
SPARK_CONFIG = {
    "app_name": "SHU_Employment_Analysis",
    "master": "local[*]",
    "hdfs_path": "hdfs://localhost:9000/user/data/",
    "jar_path": JAR_PATH # 核心：使用本地 JAR，不再使用远程 packages
}

# ==========================================
# 3. 业务逻辑指标 (KPI)
# ==========================================
KPI_TARGETS = {
    "matching_rate_improvement": 0.325,
    "mismatch_rate_reduction": 0.15,
    "data_accuracy_min": 0.995,
    "latency_max_seconds": 2
}