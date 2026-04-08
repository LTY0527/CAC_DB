import io
import os
import sys
import traceback
from pathlib import Path

from sqlalchemy import create_engine
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.ml.recommendation import ALS
from pyspark.sql import Window
from pyspark.sql.functions import avg, col, concat, count, dense_rank, explode, lit, round, sqrt, when

from config import DB_URL
from spark_common import DB_PROPERTIES, create_spark_session, jdbc_url, load_joined_dataset

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
TXT_DOCTOR = "\u535a\u58eb"
TXT_MASTER = "\u7855\u58eb"
TXT_TOP_SCHOOL = "\u53cc\u4e00\u6d41\u5efa\u8bbe\u9ad8\u6821"
TXT_KEY_SCHOOL = "\u5e02\u5c5e\u91cd\u70b9\u9ad8\u6821"
TXT_FEATURED_MAJOR = "\u7279\u8272\u4e13\u4e1a"
TXT_ENGINEERING = "\u5de5\u5b66"
TXT_SCIENCE = "\u7406\u5b66"
TXT_MEDICINE = "\u533b\u5b66"
TXT_SKILL_HIGH = "\u9ad8"
TXT_SKILL_MID = "\u4e2d"
TXT_STRATEGIC = "\u4e09\u5927\u5148\u5bfc"
TXT_LARGE = "\u5927\u578b"
TXT_FINANCE = "\u73b0\u4ee3\u91d1\u878d"
TXT_SMART_MFG = "\u667a\u80fd\u5236\u9020"
TXT_NEW_MATERIAL = "\u65b0\u6750\u6599"
DB_ENGINE = create_engine(DB_URL)


def build_als_matching(df):
    training_df = (
        df.select("student_id", "origin_place", "school_level", "major_name", "avg_salary")
        .dropna()
        .filter(col("avg_salary") > 0)
    )

    major_model = StringIndexer(inputCol="major_name", outputCol="major_index", handleInvalid="skip").fit(training_df)
    indexed_df = major_model.transform(training_df)

    als = ALS(
        userCol="student_id",
        itemCol="major_index",
        ratingCol="avg_salary",
        coldStartStrategy="drop",
        nonnegative=True,
        rank=8,
        maxIter=12,
        regParam=0.08,
    )
    model = als.fit(indexed_df)

    recs = model.recommendForAllUsers(10).select("student_id", explode("recommendations").alias("rec")).select(
        "student_id",
        col("rec.major_index").alias("major_index"),
        col("rec.rating").alias("pred_rating"),
    )

    major_lookup = indexed_df.select("major_name", "major_index").dropDuplicates(["major_index"])
    student_bg = indexed_df.select(
        "student_id",
        concat(col("origin_place"), lit("|"), col("school_level")).alias("background_dim"),
    ).dropDuplicates(["student_id"])

    return (
        recs.join(major_lookup, "major_index", "left")
        .join(student_bg, "student_id", "left")
        .groupBy("background_dim", "major_name")
        .agg(round(avg("pred_rating"), 4).alias("matching_score"), count("student_id").alias("sample_size"))
        .orderBy(col("matching_score").desc())
    )


def build_cosine_job_matching(df):
    student_df = (
        df.withColumn("edu_score", when(col("edu_name") == TXT_DOCTOR, 3.0).when(col("edu_name") == TXT_MASTER, 2.0).otherwise(1.0))
        .withColumn(
            "school_score",
            when(col("school_level") == TXT_TOP_SCHOOL, 3.0).when(col("school_level") == TXT_KEY_SCHOOL, 2.0).otherwise(1.0),
        )
        .withColumn(
            "major_score",
            when(col("major_type") == TXT_FEATURED_MAJOR, 3.0)
            .when(col("discipline_category").isin(TXT_ENGINEERING, TXT_SCIENCE, TXT_MEDICINE), 2.5)
            .otherwise(1.5),
        )
        .withColumn("skill_score", when(col("skill_level") == TXT_SKILL_HIGH, 3.0).when(col("skill_level") == TXT_SKILL_MID, 2.0).otherwise(1.0))
    )

    student_df = VectorAssembler(
        inputCols=["edu_score", "school_score", "major_score", "skill_score"],
        outputCol="student_features",
    ).transform(student_df)

    job_df = (
        df.select("employer_name", "industry_type", "leading_industry_tag", "company_scale")
        .dropDuplicates(["employer_name"])
        .withColumn(
            "job_edu_score",
            when(col("leading_industry_tag") == TXT_STRATEGIC, 2.3).when(col("company_scale") == TXT_LARGE, 2.0).otherwise(1.3),
        )
        .withColumn(
            "job_industry_score",
            when(col("leading_industry_tag") == TXT_STRATEGIC, 3.0)
            .when(col("industry_type").isin(TXT_FINANCE, TXT_SMART_MFG, TXT_NEW_MATERIAL), 2.5)
            .otherwise(1.5),
        )
        .withColumn(
            "job_skill_score",
            when(col("leading_industry_tag") == TXT_STRATEGIC, 2.8).when(col("company_scale") == TXT_LARGE, 2.2).otherwise(1.4),
        )
    )

    job_df = VectorAssembler(
        inputCols=["job_edu_score", "job_industry_score", "job_skill_score"],
        outputCol="job_features",
    ).transform(job_df)

    candidate_pairs = student_df.select(
        "student_id",
        "student_name",
        "industry_type",
        "leading_industry_tag",
        "student_features",
    ).join(
        job_df.select("employer_name", "industry_type", "leading_industry_tag", "job_features"),
        on=["industry_type", "leading_industry_tag"],
        how="inner",
    )

    scored = (
        candidate_pairs.withColumn("student_arr", vector_to_array("student_features"))
        .withColumn("job_arr", vector_to_array("job_features"))
        .withColumn("s1", col("student_arr")[0])
        .withColumn("s2", col("student_arr")[1])
        .withColumn("s4", col("student_arr")[3])
        .withColumn("j1", col("job_arr")[0])
        .withColumn("j2", col("job_arr")[1])
        .withColumn("j3", col("job_arr")[2])
        .withColumn("dot_product", col("s1") * col("j1") + col("s2") * col("j2") + col("s4") * col("j3"))
        .withColumn("student_norm", sqrt(col("s1") * col("s1") + col("s2") * col("s2") + col("s4") * col("s4")))
        .withColumn("job_norm", sqrt(col("j1") * col("j1") + col("j2") * col("j2") + col("j3") * col("j3")))
        .withColumn("cosine_similarity", round(col("dot_product") / (col("student_norm") * col("job_norm")), 6))
    )

    ranking = Window.partitionBy("student_id").orderBy(col("cosine_similarity").desc(), col("employer_name"))
    return (
        scored.withColumn("rank_no", dense_rank().over(ranking))
        .filter(col("rank_no") <= 3)
        .select("student_id", "student_name", "employer_name", "cosine_similarity", "rank_no")
        .orderBy("student_id", "rank_no")
    )


def persist_result(df, table_name: str):
    output_mode = os.environ.get("MATCHING_OUTPUT_MODE", "jdbc").lower()
    output_path = OUTPUT_DIR / f"{table_name}.csv"

    if output_mode == "csv":
        df.toPandas().to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[Matching] \u5df2\u5199\u51fa\u672c\u5730\u7ed3\u679c: {output_path}")
        return

    try:
        pandas_df = df.toPandas()
        pandas_df.to_sql(
            name=table_name,
            con=DB_ENGINE,
            if_exists="replace",
            index=False,
            chunksize=5000,
            method="multi",
        )
        print(f"[Matching] \u5df2\u5199\u5165\u6570\u636e\u8868: {table_name}")
    except Exception as exc:
        print(f"[Matching] JDBC \u5199\u5165\u5931\u8d25\uff0c\u81ea\u52a8\u56de\u9000\u5230\u672c\u5730 CSV: {exc}")
        df.toPandas().to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[Matching] \u5df2\u5199\u51fa\u672c\u5730\u7ed3\u679c: {output_path}")


def run_matching_pipeline():
    spark = create_spark_session("SHU_Employment_CF_Refactor")

    try:
        print("[Matching] \u6b63\u5728\u52a0\u8f7d\u56db\u8868\u5173\u8054\u6570\u636e...")
        df = load_joined_dataset(spark).cache()

        print("[Matching] \u6b63\u5728\u8ba1\u7b97 ALS \u62db\u751f\u5339\u914d\u7ed3\u679c...")
        als_result = build_als_matching(df)
        persist_result(als_result, "ads_enrollment_matching")

        print("[Matching] \u6b63\u5728\u8ba1\u7b97\u4eba\u5c97\u5339\u914d\u63a8\u8350\u7ed3\u679c...")
        cosine_result = build_cosine_job_matching(df)
        persist_result(cosine_result, "ads_job_recommendation")

        print("[Matching] ALS \u4e0e\u4eba\u5c97\u5339\u914d\u7ed3\u679c\u5904\u7406\u5b8c\u6210\u3002")
    except Exception as exc:
        print(f"[Matching] \u8fd0\u884c\u5931\u8d25: {exc}")
        traceback.print_exc()
    finally:
        spark.stop()


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    run_matching_pipeline()
