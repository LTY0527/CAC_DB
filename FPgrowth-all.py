from pyspark.sql.functions import col, lit, array, array_distinct, concat, round # 必须包含 round
import  traceback
from pyspark.sql import SparkSession
from pyspark.ml.fpm import FPGrowth
from config import DB_SETTINGS, jdbc_url, SPARK_CONFIG, KPI_TARGETS
from pyspark.sql.functions import array, col, lit, concat, array_distinct
import os
import sys
# 必须在创建 SparkSession 之前设置！
os.environ['HADOOP_HOME'] = r'D:\hadoop'
os.environ['PATH'] = os.environ['HADOOP_HOME'] + r'\bin;' + os.environ['PATH']
# --- 1. 配置区 (请根据你的实际环境修改 JAR 路径) ---
# 务必使用绝对路径，避免之前的 FileNotFoundException
JAR_PATH = r"D:\PythonProject\libs\mysql-connector-java-8.0.11.jar"
DB_SETTINGS = {
    "url": "jdbc:mysql://localhost:3306/bigdata?useSSL=false&serverTimezone=Asia/Shanghai",
    "user": "root",
    "password": "123456",
    "driver": "com.mysql.cj.jdbc.Driver"
}
def run_fp_growth_analysis():
    # 强制指定 Python 解释器，防止 Windows 环境下的路径映射错误
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

    print("🚀 [关联规则模块] 正在启动 FPGrowth 挖掘引擎...")

    # 2. 初始化 Spark
    spark = SparkSession.builder \
        .appName("SHU_Employment_FPGrowth") \
        .master("local[*]") \
        .config("spark.jars", JAR_PATH) \
        .config("spark.driver.extraClassPath", JAR_PATH) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    try:
        # 3. 加载数据 (通过 SQL 预连接三张表)
        # 注意：此处显式指定 a.major_name 等，避免之前的 Ambiguous Reference 错误
        # 同时将 edu_name 纳入，因为学历对就业影响巨大
        sql_query = """
            (
                SELECT 
                    a.discipline_category, 
                    a.major_name, 
                    a.skill_level, 
                    s.school_level, 
                    s.edu_name, 
                    e.leading_industry_tag 
                FROM fact_academic a
                JOIN dim_student s ON a.student_id = s.student_id
                JOIN fact_employment e ON a.student_id = e.student_id
            ) as training_data
        """

        df = spark.read.format("jdbc") \
            .option("url", DB_SETTINGS["url"]) \
            .option("dbtable", sql_query) \
            .option("user", DB_SETTINGS["user"]) \
            .option("password", DB_SETTINGS["password"]) \
            .option("driver", DB_SETTINGS["driver"]) \
            .load()

        # 4. 特征工程：构建“属性篮子”
        # 修正：去掉了不存在的 major_category，加入了 edu_name
        print("📦 正在转换特征空间为交易篮子格式...")
        basket_df = df.select(
            array_distinct(
                array(
                    concat(lit("门类:"), col("discipline_category")),
                    concat(lit("专业:"), col("major_name")),
                    concat(lit("学历:"), col("edu_name")),
                    concat(lit("技能:"), col("skill_level")),
                    concat(lit("学校:"), col("school_level")),
                    concat(lit("结果:"), col("leading_industry_tag"))
                )
            ).alias("items")
        )

        # 5. 模型训练
        # minSupport: 支持度，0.01 表示该组合至少占总体的 1%
        # minConfidence: 置信度，0.3 表示前提发生时，结论发生的概率至少 30%
        print("💡 正在扫描数据频繁项集...")
        fp_growth = FPGrowth(itemsCol="items", minSupport=0.01, minConfidence=0.3)
        model = fp_growth.fit(basket_df)

        # 6. 提取并过滤高价值规则
        # 重点关注：哪些特征组合会导致“结果:三大先导”
        print("🔍 正在过滤目标关联规则 (Target: 三大先导)...")
        rules = model.associationRules

        # 将结果列转为字符串进行过滤
        target_rules = rules.filter(
            col("consequent").cast("string").contains("结果:三大先导")
        ).sort(col("lift").desc())  # 按提升度(Lift)排序，反映关联的强度

        target_rules.show(10, truncate=False)

        # 7. 持久化至 MySQL (ads_major_matching_rules)
        print("📤 正在将挖掘出的规则推送至分析层...")
        final_to_save = target_rules.select(
            col("antecedent").cast("string").alias("antecedent"),
            col("consequent").cast("string").alias("consequent"),
            round(col("confidence"), 4).alias("confidence"),
            round(col("lift"), 4).alias("lift")
        )

        final_to_save.write.format("jdbc") \
            .option("url", DB_SETTINGS["url"]) \
            .option("dbtable", "ads_major_matching_rules") \
            .option("user", DB_SETTINGS["user"]) \
            .option("password", DB_SETTINGS["password"]) \
            .option("driver", DB_SETTINGS["driver"]) \
            .mode("overwrite") \
            .save()

        print(f"✅ 挖掘任务完成，已存入 ads_major_matching_rules 表。")

    except Exception as e:
        print(f"🚨 FPGrowth 模块运行异常: {e}")
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    run_fp_growth_analysis()