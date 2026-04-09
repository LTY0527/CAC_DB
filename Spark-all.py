import io
import sys
import traceback

from pyspark.sql.functions import avg, col, count, desc, round, when

from spark_common import create_spark_session, load_joined_dataset, write_dataframe_to_mysql


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


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

        print("[ADS] 正在写入 ads_employment_summary ...")
        write_dataframe_to_mysql(ads_summary, "ads_employment_summary")

        print("[ADS] 正在写入 ads_school_kpi ...")
        write_dataframe_to_mysql(school_kpi, "ads_school_kpi")

        print("[ADS] 特征加工与聚合结果写入完成。")
        return True

    except Exception as exc:
        print(f"[ADS] 运行失败: {exc}")
        traceback.print_exc()
        return False
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(0 if run_data_aggregation() else 1)
