import os
import sys
import  traceback
from pyspark.sql import SparkSession
from pyspark.ml.fpm import FPGrowth
from config import DB_SETTINGS, jdbc_url, SPARK_CONFIG, KPI_TARGETS
from pyspark.sql.functions import array, col, lit, concat, array_distinct

def run_fp_growth_analysis():
    # --- 核心修复：强制指定 Python 解释器环境 ---
    # 解决“系统找不到指定路径”的问题
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

    # 1. 初始化 Spark 会话
    # 使用 config.py 中定义的本地 JAR 路径
    spark = SparkSession.builder \
        .appName(SPARK_CONFIG["app_name"]) \
        .master(SPARK_CONFIG["master"]) \
        .config("spark.driver.extraClassPath", SPARK_CONFIG["jar_path"]) \
        .config("spark.executor.extraClassPath", SPARK_CONFIG["jar_path"]) \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")
    print(f"🚀 Spark 引擎已启动，正在读取上海大学试点数据...")

    try:
        jdbc_options = {
            "url": jdbc_url,
            "dbtable": """(
                        SELECT a.discipline_category, a.major_category, a.major_name, 
                               a.skill_level, s.school_level, e.leading_industry_tag 
                        FROM fact_academic a
                        JOIN dim_student s ON a.student_id = s.student_id
                        JOIN fact_employment e ON a.student_id = e.student_id
                    ) as enhanced_data""",
            "user": DB_SETTINGS["user"],
            "password": DB_SETTINGS["password"],
            "driver": DB_SETTINGS["driver"]
        }

        # 核心修正：options 接收一个字典对象
        df = spark.read.format("jdbc").options(**jdbc_options).load()

        # 3. 特征工程 (保持在 try 块内)
        basket_df = df.select(
            array_distinct(
                array(
                    concat(lit("学科:"), col("discipline_category")),
                    concat(lit("分类:"), col("major_category")),
                    concat(lit("专业:"), col("major_name")),
                    concat(lit("等级:"), col("skill_level")),
                    concat(lit("层级:"), col("school_level")),
                    concat(lit("目标:"), col("leading_industry_tag"))
                )
            ).alias("items")
        )

        # 4. 训练模型
        print("💡 正在执行多维关联规则挖掘...")
        fp_growth = FPGrowth(itemsCol="items", minSupport=0.005, minConfidence=0.3)
        model = fp_growth.fit(basket_df)

        # 5. 处理结果
        rules = model.associationRules.sort("lift", ascending=False)
        rules.filter(col("consequent").cast("string").contains("目标:三大先导")).show(20, truncate=False)

        # 6. 核心规则提取与持久化 (必须确保缩进在 try 块内！)
        print("📤 正在将分析结果推送至可视化数据层...")
        final_rules = rules.select(
            col("antecedent").cast("string").alias("antecedent"),
            col("consequent").cast("string").alias("consequent"),
            col("confidence"),
            col("lift")
        ).limit(20)

        # 7. 写入 MySQL
        final_rules.write.format("jdbc").options(
            url=jdbc_url,
            dbtable="ads_major_matching_rules",
            user=DB_SETTINGS["user"],
            password=DB_SETTINGS["password"],
            driver=DB_SETTINGS["driver"]
        ).mode("overwrite").save()

        print("✅ 可视化数据层已同步。")

    except Exception as e:
        print(f"🚨 运行失败：{e}")
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    run_fp_growth_analysis()