import os
import sys
import traceback
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.sql.functions import col, lit, udf, round as spark_round
from pyspark.sql.types import StructType, StructField, StringType, FloatType

# ==========================================
# 1. 环境与配置强制初始化
# ==========================================
os.environ['HADOOP_HOME'] = r'D:\hadoop'
os.environ['PATH'] = os.environ['HADOOP_HOME'] + r'\bin;' + os.environ['PATH']
os.environ['PYSPARK_PYTHON'] = sys.executable

# 核心：必须使用本地驱动的绝对路径
JAR_PATH = r"D:\PythonProject\libs\mysql-connector-java-8.0.11.jar"

DB_SETTINGS = {
    "url": "jdbc:mysql://localhost:3306/bigdata?useSSL=false&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true",
    "user": "root",
    "password": "123456",  # <--- 请在此处输入正确密码
    "driver": "com.mysql.cj.jdbc.Driver"
}


def run_job_recommendation():
    print("🚀 [就业推荐模块] 正在启动 10 万级分布式匹配引擎...")

    # 2. 强化 SparkSession 初始化
    spark = SparkSession.builder \
        .appName("Job_Recommendation_Scale_10W") \
        .master("local[*]") \
        .config("spark.jars", JAR_PATH) \
        .config("spark.driver.extraClassPath", JAR_PATH) \
        .config("spark.executor.extraClassPath", JAR_PATH) \
        .config("spark.driver.memory", "10g") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    try:
        # 3. 数据加载 (fact_academic 是 DWD 层事实表)
        print("📥 正在加载 10 万学生特征数据...")
        query = """
            (SELECT a.student_id, a.major_name, a.skill_level, s.edu_name 
             FROM fact_academic a
             JOIN dim_student s ON a.student_id = s.student_id) as stu_data
        """
        df_student = spark.read.format("jdbc").options(
            url=DB_SETTINGS["url"],
            dbtable=query,
            user=DB_SETTINGS["user"],
            password=DB_SETTINGS["password"],
            driver=DB_SETTINGS["driver"]
        ).load()

        # 4. 定义岗位靶标数据
        job_data = [
            ("计算机科学与技术", "高级", "硕士", "先导产业研发岗"),
            ("计算机科学与技术", "中级", "本科", "互联网技术岗"),
            ("金融学", "高级", "本科", "金融分析岗")
        ]
        df_jobs = spark.createDataFrame(job_data, ["major_name", "skill_level", "edu_name", "target_job"])

        # 5. 特征数字化 (StringIndexer)
        cols_to_idx = ["major_name", "skill_level", "edu_name"]

        # 统一编码空间
        combined_df = df_student.select(cols_to_idx).union(df_jobs.select(cols_to_idx))

        temp_stu = df_student
        temp_job = df_jobs
        for c in cols_to_idx:
            indexer = StringIndexer(inputCol=c, outputCol=c + "_idx").fit(combined_df)
            temp_stu = indexer.transform(temp_stu)
            temp_job = indexer.transform(temp_job)

        # 向量化
        assembler = VectorAssembler(inputCols=[c + "_idx" for c in cols_to_idx], outputCol="features")
        stu_features = assembler.transform(temp_stu).select("student_id", "features")

        # 将岗位特征收集到 Driver 端（因为只有 3 个岗位，collect 是安全的）
        job_features = assembler.transform(temp_job).select("target_job", "features").collect()

        # 6. 高性能余弦相似度计算 (Vectorized UDF)
        def get_best_match(stu_vec):
            best_score = 0.0
            best_job = "待定"
            for job in job_features:
                v2 = job.features
                # 余弦相似度计算逻辑
                dot = float(stu_vec.dot(v2))
                norm = float(stu_vec.norm(2)) * float(v2.norm(2))
                score = dot / norm if norm > 0 else 0.0
                if score > best_score:
                    best_score = score
                    best_job = job.target_job
            return (best_job, float(best_score))

        # 定义返回结构
        schema = "struct<job:string, score:float>"
        match_udf = udf(get_best_match, schema)

        print("💡 正在执行 10W x 3 矩阵计算...")
        result_df = stu_features.withColumn("match", match_udf(col("features"))) \
            .select(
            col("student_id"),
            col("match.job").alias("recommended_job"),
            spark_round(col("match.score"), 4).alias("matching_score")
        )

        # 7. 写入数据库
        print(f"📤 正在写入分析结果 (ads_job_recommendation)...")
        result_df.write.format("jdbc").options(
            url=DB_SETTINGS["url"],
            dbtable="ads_job_recommendation",
            user=DB_SETTINGS["user"],
            password=DB_SETTINGS["password"],
            driver=DB_SETTINGS["driver"]
        ).mode("overwrite").save()

        print("✅ 任务圆满完成。10 万条数据推荐已生成。")

    except Exception as e:
        print(f"🚨 运行失败: {e}")
        traceback.print_exc()
    finally:
        if 'spark' in locals(): spark.stop()


if __name__ == "__main__":
    run_job_recommendation()