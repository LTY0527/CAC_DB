import traceback

from pyspark.ml.fpm import FPGrowth
from pyspark.sql.functions import array, array_distinct, col, round

from spark_common import DB_PROPERTIES, create_spark_session, jdbc_url, load_joined_dataset

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
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
                round(col("confidence"), 4).alias("confidence"),
                round(col("lift"), 4).alias("lift"),
            )
            .orderBy(col("lift").desc(), col("confidence").desc())
        )

        golden_rules.show(20, truncate=False)

        print("[FP-Growth] 正在写入 ads_major_matching_rules ...")
        golden_rules.write.jdbc(
            url=jdbc_url,
            table="ads_major_matching_rules",
            mode="overwrite",
            properties=DB_PROPERTIES,
        )
        print("[FP-Growth] 黄金路径规则写入完成。")

    except Exception as exc:
        print(f"[FP-Growth] 运行失败: {exc}")
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    run_fp_growth_analysis()
