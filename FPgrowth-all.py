import io
import sys
import traceback

from sqlalchemy import create_engine
from pyspark.ml.fpm import FPGrowth
from pyspark.sql.functions import array, array_distinct, col, round

from config import DB_URL
from spark_common import create_spark_session, load_joined_dataset, write_dataframe_to_mysql
from training_program_suggester import build_training_program_suggestions


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
DB_ENGINE = create_engine(DB_URL, pool_pre_ping=True)


def run_fp_growth_analysis():
    spark = create_spark_session("SHU_Employment_FPGrowth_Refactor")

    try:
        print("[FP-Growth] 正在加载四表关联数据...")
        df = load_joined_dataset(spark)

        basket_df = df.select(
            array_distinct(
                array(
                    col("school_level_tag"),
                    col("major_type_tag"),
                    col("discipline_tag"),
                    col("major_tag"),
                    col("skill_tag"),
                    col("industry_tag"),
                    col("leading_industry_label"),
                )
            ).alias("items")
        )

        print("[FP-Growth] 正在训练关联规则模型...")
        model = FPGrowth(itemsCol="items", minSupport=0.008, minConfidence=0.35).fit(basket_df)

        rules = model.associationRules
        golden_rules = (
            rules.filter(
                (
                    col("antecedent").cast("string").contains("院校层次:双一流建设高校")
                    | col("antecedent").cast("string").contains("专业类型:特色专业")
                )
                & col("consequent").cast("string").contains("产业标签:三大先导")
                & (col("lift") > 2.0)
            )
            .select(
                col("antecedent").cast("string").alias("antecedent"),
                col("consequent").cast("string").alias("consequent"),
                round(col("support"), 4).alias("support"),
                round(col("confidence"), 4).alias("confidence"),
                round(col("lift"), 4).alias("lift"),
            )
            .orderBy(col("lift").desc(), col("confidence").desc())
        )

        preview_count = golden_rules.limit(20).count()
        print(f"[FP-Growth] 规则预览数量: {preview_count}")

        print("[FP-Growth] 正在写入 ads_major_matching_rules ...")
        write_dataframe_to_mysql(golden_rules, "ads_major_matching_rules")

        print("[FP-Growth] 正在生成培养方案优化建议 ...")
        joined_pdf = df.select(
            "student_id",
            "school_name",
            "school_level",
            "discipline_category",
            "major_name",
            "major_type",
            "skill_level",
            "industry_type",
            "leading_industry_tag",
            "avg_salary",
        ).toPandas()
        rules_pdf = golden_rules.toPandas()
        suggestions_pdf = build_training_program_suggestions(joined_pdf, rules_pdf)
        suggestions_pdf.to_sql(
            name="ads_training_program_suggestions",
            con=DB_ENGINE,
            if_exists="replace",
            index=False,
            chunksize=2000,
            method="multi",
        )
        print(f"[FP-Growth] 培养方案建议写入完成, rows={len(suggestions_pdf)}")
        print("[FP-Growth] 关联规则结果写入完成。")
        return True

    except Exception as exc:
        print(f"[FP-Growth] 运行失败: {exc}")
        traceback.print_exc()
        return False
    finally:
        spark.stop()


if __name__ == "__main__":
    sys.exit(0 if run_fp_growth_analysis() else 1)
