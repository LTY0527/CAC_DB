import os
import sys
import traceback
import time

# ==========================================
# 1. 环境初始化（必须位于所有 PySpark 导入之前）
# ==========================================
os.environ['HADOOP_HOME'] = r'D:\hadoop'
os.environ['PATH'] = os.environ['HADOOP_HOME'] + r'\bin;' + os.environ['PATH']
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import StringIndexer, IndexToString, MinMaxScaler, VectorAssembler
from pyspark.sql.functions import col, explode, round, avg, coalesce, udf
from pyspark.sql.types import FloatType

# 【关键点】确保路径完全正确，建议放在不含中文和空格的目录下
JAR_PATH = r"D:\PythonProject\libs\mysql-connector-java-8.0.11.jar"


def run_enrollment_cf():
    print("🚀 [招生匹配模块] 启动 10 万级数据深度计算引擎...")

    # ==========================================
    # 2. 初始化 Spark 引擎（针对单机 10W 数据极致调优）
    # ==========================================
    spark = SparkSession.builder \
        .appName("Enrollment_Matching_10W_Scale") \
        .master("local[*]") \
        .config("spark.jars", JAR_PATH) \
        .config("spark.driver.extraClassPath", JAR_PATH) \
        .config("spark.executor.extraClassPath", JAR_PATH) \
        .config("spark.driver.memory", "10g") \
        .config("spark.executor.memory", "10g") \
        .config("spark.sql.shuffle.partitions", "50") \
        .config("spark.memory.fraction", "0.8") \
        .config("spark.driver.maxResultSize", "2g") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    # 验证驱动是否加载成功
    try:
        spark._jvm.java.lang.Class.forName("com.mysql.cj.jdbc.Driver")
        print("✅ 驱动类探测成功，环境就绪。")
    except:
        print(f"❌ 驱动加载失败！请检查文件是否存在: {JAR_PATH}")
        return

    # 数据库配置
    DB_SETTINGS = {
        "host": "localhost",
        "port": "3306",
        "user": "root",
        "password": "123456",  # 请务必在此处填入正确密码
        "database": "bigdata"
    }

    # 【优化】开启 rewriteBatchedStatements 提升 10W 条数据的写入速度
    jdbc_url = (f"jdbc:mysql://{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"
                "?useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true"
                "&rewriteBatchedStatements=true")

    db_properties = {
        "user": DB_SETTINGS["user"],
        "password": DB_SETTINGS["password"],
        "driver": "com.mysql.cj.jdbc.Driver"
    }

    try:
        # 3. 数据加载
        print("📥 正在从 MySQL 读取 10 万级原始数据...")
        query = """
            (SELECT CAST(student_id AS SIGNED) as student_id, major_name, avg_salary 
             FROM fact_academic 
             JOIN fact_employment USING(student_id)) as raw_data
        """
        raw_df = spark.read.jdbc(url=jdbc_url, table=query, properties=db_properties)

        # 4. 特征工程 (Scaling & Indexing)
        # --- 核心优化 A: 薪资缩放 (无需 Python UDF, 使用 Spark 原生算子) ---
        from pyspark.ml.functions import vector_to_array

        assembler = VectorAssembler(inputCols=["avg_salary"], outputCol="salary_vec")
        df_vec = assembler.transform(raw_df)

        scaler = MinMaxScaler(inputCol="salary_vec", outputCol="scaled_salary_vec", min=1.0, max=10.0)
        scaler_model = scaler.fit(df_vec)
        df_scaled = scaler_model.transform(df_vec)

        # 核心修正：使用 vector_to_array 提取 rating，并将结果列存入 df_ready
        df_ready = df_scaled.withColumn("rating_arr", vector_to_array("scaled_salary_vec")) \
            .withColumn("rating", col("rating_arr")[0]) \
            .drop("rating_arr", "salary_vec", "scaled_salary_vec")

        # --- 3. 数字化专业标签 ---
        major_indexer = StringIndexer(inputCol="major_name", outputCol="major_index", handleInvalid="skip")
        major_model = major_indexer.fit(df_ready)  # 此处确保使用 df_ready

        # 将数字化后的 DataFrame 存入 df_indexed
        df_indexed = major_model.transform(df_ready).repartition(20)

        # --- 4. ALS 模型训练 ---
        print(f"💡 正在执行矩阵分解... 当前样本量: {df_indexed.count()}")
        als = ALS(
            userCol="student_id",
            itemCol="major_index",
            ratingCol="rating",
            coldStartStrategy="drop",
            nonnegative=True,
            rank=4,  # 10万条数据建议保持低 rank
            maxIter=10,
            regParam=0.1,
            intermediateStorageLevel="MEMORY_AND_DISK"
        )
        # 确保此处训练的是 df_indexed
        model = als.fit(df_indexed)

        # 6. 生成结果与兜底
        print("📊 正在生成全专业匹配矩阵...")
        major_recs = model.recommendForAllItems(25)  # 减少单专业推荐数以节省内存

        converter = IndexToString(inputCol="major_index", outputCol="target_major", labels=major_model.labels)

        recs_exploded = major_recs.select(
            col("major_index"),
            explode(col("recommendations")).alias("rec")
        ).select(
            col("major_index"),
            col("rec.student_id").alias("top_potential_student_id"),
            col("rec.rating").alias("matching_score")
        )

        df_with_names = converter.transform(recs_exploded)
        major_avgs = df_indexed.groupBy("major_name").agg(avg("rating").alias("major_avg_rating"))

        # 解决歧义并持久化
        result_final = df_with_names.join(
            major_avgs,
            df_with_names.target_major == major_avgs.major_name,
            how="left"
        ).select(
            "target_major",
            col("top_potential_student_id"),
            round(coalesce(col("matching_score"), col("major_avg_rating") * 0.7), 4).alias("matching_score")
        ).filter(col("matching_score") > 0)

        # 7. 持久化至 MySQL
        print(f"📤 正在分批写入应用层 ADS 表 (总记录数: {result_final.count()})...")
        result_final.write.jdbc(
            url=jdbc_url,
            table="ads_enrollment_matching",
            mode="overwrite",
            properties=db_properties
        )

        print("✅ [招生匹配模块] 10 万级数据分析圆满成功。")

    except Exception as e:
        print(f"🚨 运行异常: {e}")
        traceback.print_exc()
    finally:
        if 'spark' in locals() and spark:
            time.sleep(2)  # 缓冲延迟，减少 WinError 10038 几率
            spark.stop()


if __name__ == "__main__":
    run_enrollment_cf()