import os
import sys

# 1. 环境初始化（确保与算法模块一致）
os.environ['HADOOP_HOME'] = r'D:\hadoop'
os.environ['hadoop.home.dir'] = r'D:\hadoop'
os.environ['PATH'] = r'D:\hadoop\bin;' + os.environ['PATH']

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, round, when
from config import JAR_PATH, DB_SETTINGS

def run_data_aggregation():
    print("📊 [数据聚合模块] 正在构建 ADS 应用数据层...")

    # 2. 初始化 Spark 引擎
    spark = SparkSession.builder \
        .appName("SHU_Employment_Aggregation") \
        .config("spark.jars", JAR_PATH) \
        .master("local[*]") \
        .getOrCreate()

    db_properties = {
        "user": DB_SETTINGS["user"],
        "password": DB_SETTINGS["password"],
        "driver": DB_SETTINGS["driver"],
        "serverTimezone": "Asia/Shanghai"
    }
    jdbc_url = f"jdbc:mysql://{DB_SETTINGS['host']}:{DB_SETTINGS['port']}/{DB_SETTINGS['database']}"

    try:
        # 3. 加载 DWD 明细层数据
        df_academic = spark.read.jdbc(url=jdbc_url, table="fact_academic", properties=db_properties)
        df_employment = spark.read.jdbc(url=jdbc_url, table="fact_employment", properties=db_properties)

        # 4. 构建核心聚合逻辑 (多维分析视图)
        # 关联学籍与就业数据，计算各维度的深度 KPI
        full_df = df_academic.join(df_employment, "student_id")

        # 聚合指标 A：专业-学历-产业分布 综合视图
        # 这是为大屏的“就业结构图”和“薪资排行”准备的
        ads_summary = full_df.groupBy("major_name", "edu_level", "leading_industry_tag") \
            .agg(
                round(avg("avg_salary"), 2).alias("avg_salary"),
                count("student_id").alias("emp_count")
            )

        # 5. 持久化至 MySQL (ads_employment_summary)
        # 使用 overwrite 模式，确保每次运行都是最新的统计结果
        ads_summary.write.jdbc(
            url=jdbc_url,
            table="ads_employment_summary",
            mode="overwrite",
            properties=db_properties
        )

        # 额外补充：生成全校总览 KPI (可选，供大屏顶部数字使用)
        # 如：总平均薪资、先导产业入职占比
        total_kpi = full_df.agg(
            round(avg("avg_salary"), 2).alias("school_avg_salary"),
            count("student_id").alias("total_graduates")
        )
        total_kpi.write.jdbc(url=jdbc_url, table="ads_school_kpi", mode="overwrite", properties=db_properties)

        print("✅ ads_employment_summary 表已成功填充。")
        print("✅ ads_school_kpi 表（总览指标）已同步生成。")

    except Exception as e:
        print(f"🚨 聚合模块运行失败，原因: {e}")
        import traceback
        traceback.print_exc()
    finally:
        spark.stop()

if __name__ == "__main__":
    run_data_aggregation()