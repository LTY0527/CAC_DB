import os
import sys
from sqlalchemy import create_engine, text

# ==========================================
# 1. 环境初始化（必须位于所有 PySpark 导入之前）
# ==========================================
os.environ['HADOOP_HOME'] = r'D:\hadoop'
os.environ['hadoop.home.dir'] = r'D:\hadoop'
os.environ['PATH'] = r'D:\hadoop\bin;' + os.environ['PATH']

from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import StringIndexer, IndexToString
from pyspark.sql.functions import col, explode
from config import JAR_PATH, DB_SETTINGS

def run_enrollment_cf():
    print("🚀 [招生匹配模块] 引擎启动中...")

    # ==========================================
    # 2. 强制修复 MySQL 服务端时区与连接环境
    # ==========================================
    try:
        temp_db_url = f"mysql+pymysql://{DB_SETTINGS['user']}:{DB_SETTINGS['password']}@{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
        temp_engine = create_engine(temp_db_url)
        with temp_engine.connect() as conn:
            # 修正：SQLAlchemy 2.0+ 执行原始 SQL 需使用 text()
            conn.execute(text("SET GLOBAL time_zone = '+8:00';"))
            conn.execute(text("SET time_zone = '+8:00';"))
            conn.commit()
        print("✅ MySQL 服务端时区已强制修正为 +8:00")
    except Exception as e:
        print(f"⚠️ 尝试修改服务端时区失败（权限或版本问题），将依赖 JDBC 参数注入: {e}")

    # ==========================================
    # 3. 初始化 SparkSession（资源配比优化）
    # ==========================================
    spark = SparkSession.builder \
        .appName("Enrollment_Matching_ALS") \
        .master("local[2]") \
        .config("spark.jars", JAR_PATH) \
        .config("spark.driver.memory", "6g") \
        .config("spark.executor.memory", "6g") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.default.parallelism", "4") \
        .getOrCreate()

    db_properties = {
        "user": DB_SETTINGS["user"],
        "password": DB_SETTINGS["password"],
        "driver": DB_SETTINGS["driver"],
        "serverTimezone": "Asia/Shanghai",
        "useSSL": "false",
        "allowPublicKeyRetrieval": "true"
    }
    jdbc_url = f"jdbc:mysql://{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"

    try:
        # ==========================================
        # 4. 数据加载与预处理
        # ==========================================
        # 提取学生专业与薪资的关系矩阵
        query = """
                (SELECT a.student_id, a.major_name, e.avg_salary 
                 FROM fact_academic a 
                 JOIN fact_employment e ON a.student_id = e.student_id
                 LIMIT 10000) as raw_performance
        """
        df = spark.read.jdbc(url=jdbc_url, table=query, properties=db_properties)

        # 数字化专业标签
        major_indexer = StringIndexer(inputCol="major_name", outputCol="major_index")
        major_model = major_indexer.fit(df)
        df_indexed = major_model.transform(df)

        # 类型强制转换以适配 ALS 矩阵分解
        df_final = df_indexed.select(
            col("student_id").cast("integer"),
            col("major_index").cast("integer"),
            col("avg_salary").cast("float")
        )

        # ==========================================
        # 5. 模型训练（ALS 参数精调）
        # ==========================================
        print("💡 正在执行 10 万级矩阵分解。目标：挖掘生源背景与专业的深度契合度...")
        als = ALS(
            userCol="student_id",
            itemCol="major_index",
            ratingCol="avg_salary",
            coldStartStrategy="drop",
            nonnegative=True,
            rank=4,            # 隐藏特征数，设为 8 以平衡泛化与精确度
            maxIter=10,         # 增加迭代次数确保收敛
            regParam=0.01       # 降低正则化系数，允许模型更好地捕捉模拟数据的信号
        )
        model = als.fit(df_final)

        # ==========================================
        # 6. 结果映射与质量过滤
        # ==========================================
        # 为每个专业推荐前 15 名最具有代表性的生源样本（扩大基数进行过滤）
        major_recs = model.recommendForAllItems(15)

        converter = IndexToString(inputCol="major_index", outputCol="target_major", labels=major_model.labels)

        final_recs = major_recs.select(
            col("major_index"),
            explode(col("recommendations")).alias("rec")
        ).select(
            col("major_index"),
            col("rec.student_id").alias("top_potential_student_id"),
            col("rec.rating").alias("matching_score")
        )

        # 将评分映射到 0-1 之间（可选，为了让前端展示更直观）
        # 这里直接保留原始预测薪资趋势分
        result_df = converter.transform(final_recs).select(
            "target_major",
            "top_potential_student_id",
            col("matching_score").cast("decimal(10,4)")
        ).filter(col("matching_score") > 0) # 过滤掉所有计算失败的 0 分行

        # ==========================================
        # 7. 持久化至 MySQL (ADS 层)
        # ==========================================
        result_df.write.jdbc(
            url=jdbc_url,
            table="ads_enrollment_matching",
            mode="overwrite",
            properties=db_properties
        )

        print("✅ [招生匹配模块] 运行成功！结果已存入 ads_enrollment_matching 表。")

    except Exception as e:
        print(f"🚨 后端引擎运行崩溃: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    run_enrollment_cf()