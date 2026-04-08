import traceback

from pyspark.sql.functions import avg, col, count, desc, round, when

from spark_common import DB_PROPERTIES, create_spark_session, jdbc_url, load_joined_dataset

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
def run_data_aggregation():
    spark = create_spark_session("SHU_Employment_Aggregation_Refactor")

    try:
        print("[ADS] 正在加载四表关联数据...")
        full_df = load_joined_dataset(spark)

        ads_summary = (
            full_df.groupBy(
                "school_name",
                "school_level",
                "discipline_category",
                "major_name",
                "industry_type",
                "company_scale",
            )
            .agg(
                round(avg("avg_salary"), 2).alias("avg_salary"),
                count("student_id").alias("emp_count"),
                round(avg(when(col("leading_industry_tag") == "三大先导", 1).otherwise(0)), 4).alias("leading_ratio"),
            )
            .orderBy(desc("avg_salary"))
        )

        school_kpi = full_df.groupBy("school_name", "school_level").agg(
            round(avg("avg_salary"), 2).alias("overall_avg_salary"),
            count("student_id").alias("total_graduates"),
            round(avg(when(col("leading_industry_tag") == "三大先导", 1).otherwise(0)), 4).alias("strategic_industry_rate"),
        )

        ads_summary.write.jdbc(url=jdbc_url, table="ads_employment_summary", mode="overwrite", properties=DB_PROPERTIES)
        school_kpi.write.jdbc(url=jdbc_url, table="ads_school_kpi", mode="overwrite", properties=DB_PROPERTIES)
        print("[ADS] 聚合结果写入完成。")

    except Exception as exc:
        print(f"[ADS] 运行失败: {exc}")
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    run_data_aggregation()
