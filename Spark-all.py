import os
import sys
from pyspark.sql.functions import col, avg, count, round, when, desc
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
        .config("spark.driver.extraClassPath", JAR_PATH) \
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
        # 3. 加载明细数据
        # 增加加载 dim_student 以获取学校层次和学历信息
        df_student = spark.read.jdbc(url=jdbc_url, table="dim_student", properties=db_properties)
        df_academic = spark.read.jdbc(url=jdbc_url, table="fact_academic", properties=db_properties)
        df_employment = spark.read.jdbc(url=jdbc_url, table="fact_employment", properties=db_properties)

        # 4. 多表关联 (Join Pipeline)
        # student_id 是关联键
        # 注意：此处将 student 维表与 academic/employment 事实表关联
        # 在第一次 Join 之后，如果 df_academic 里也有 school_name，就删掉它
        full_df = df_student.join(df_academic, "student_id")

        # 检查如果存在重复列名，则剔除
        if "school_name" in df_academic.columns:
            full_df = full_df.drop(df_academic["school_name"])

        # 接着关联第三张表
        full_df = full_df.join(df_employment, "student_id")

        # 5. 构建 ADS 视图 A：专业-学历-行业 深度透视表
        # 修正点：使用 edu_name (学生表字段) 和 discipline_category (学术表字段)
        ads_summary = full_df.groupBy(
            "school_name",
            "major_name",
            "edu_name",
            "leading_industry_tag",
            "discipline_category"
        ).agg(
            round(avg("avg_salary"), 2).alias("avg_salary"),
            count("student_id").alias("emp_count"),
            round(avg(when(col("leading_industry_tag") == "三大先导", 1).otherwise(0)), 4).alias("high_tech_ratio")
        ).orderBy(desc("avg_salary"))

        # 6. 构建 ADS 视图 B：全校核心 KPI 概览
        # 增加“高薪专业 Top3”或“平均起薪”等宏观指标
        school_kpi = full_df.agg(
            round(avg("avg_salary"), 2).alias("overall_avg_salary"),
            count("student_id").alias("total_graduates"),
            # 计算三大先导产业的总入职人数占比
            round(count(when(col("leading_industry_tag") == "三大先导", True)) / count("student_id"), 4).alias(
                "strategic_industry_rate")
        )

        # 7. 持久化至 MySQL
        print("💾 正在写入 ADS 层表...")

        # 写入就业综合摘要表
        ads_summary.write.jdbc(
            url=jdbc_url,
            table="ads_employment_summary",
            mode="overwrite",
            properties=db_properties
        )

        # 写入大屏 KPI 总览表
        school_kpi.write.jdbc(
            url=jdbc_url,
            table="ads_school_kpi",
            mode="overwrite",
            properties=db_properties
        )

        print("✅ ADS 层数据构建完成：ads_employment_summary & ads_school_kpi")

    except Exception as e:
        print(f"🚨 Spark 聚合任务异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if spark:
            spark.stop()


if __name__ == "__main__":
    run_data_aggregation()