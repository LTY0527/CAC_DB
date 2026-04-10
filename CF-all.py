import io
import os
import sys
import traceback
from builtins import round as py_round
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.ml.recommendation import ALS
from pyspark.sql import Window
from pyspark.sql.functions import abs as spark_abs, avg, col, collect_set, concat, count, dense_rank, explode, hash as spark_hash, lit, round as spark_round, sqrt, when

from config import DB_URL
from spark_common import create_spark_session, load_joined_dataset

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
TOP_K = 3
TXT_DOCTOR = "博士"
TXT_MASTER = "硕士"
TXT_TOP_SCHOOL = "双一流建设高校"
TXT_KEY_SCHOOL = "市属重点高校"
TXT_FEATURED_MAJOR = "特色专业"
TXT_ENGINEERING = "工学"
TXT_SCIENCE = "理学"
TXT_MEDICINE = "医学"
TXT_SKILL_HIGH = "高"
TXT_SKILL_MID = "中"
TXT_STRATEGIC = "三大先导"
TXT_LARGE = "大型"
TXT_FINANCE = "现代金融"
TXT_SMART_MFG = "智能制造"
TXT_NEW_MATERIAL = "新材料"
DB_ENGINE = create_engine(DB_URL, pool_pre_ping=True)


def persist_result(df, table_name: str):
    output_mode = os.environ.get("MATCHING_OUTPUT_MODE", "jdbc").lower()
    output_path = OUTPUT_DIR / f"{table_name}.csv"

    pandas_df = df.toPandas()
    if output_mode == "csv":
        pandas_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"[Matching] 已写出本地结果: {output_path}, rows={len(pandas_df)}")
        return pandas_df

    try:
        pandas_df.to_sql(
            name=table_name,
            con=DB_ENGINE,
            if_exists="replace",
            index=False,
            chunksize=5000,
            method="multi",
        )
        print(f"[Matching] 已写入数据表: {table_name}, rows={len(pandas_df)}")
        return pandas_df
    except Exception as exc:
        raise RuntimeError(f"[Matching] JDBC 写入失败: table={table_name}, error={exc}") from exc


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
        .agg(spark_round(avg("pred_rating"), 4).alias("matching_score"), count("student_id").alias("sample_size"))
        .orderBy(col("matching_score").desc())
    )


def evaluate_enrollment_matching(df, top_k=TOP_K):
    evaluation_df = (
        df.select(
            concat(col("origin_place"), lit("|"), col("school_level")).alias("background_dim"),
            "major_name",
            "avg_salary",
        )
        .dropna()
        .filter(col("avg_salary") > 0)
        .groupBy("background_dim", "major_name")
        .agg(avg("avg_salary").alias("rating"), count("*").alias("interaction_count"))
    )

    if evaluation_df.count() < 20:
        return pd.DataFrame(
            [
                {
                    "metric_name": "Precision@K",
                    "metric_value": 0.0,
                    "metric_label": f"Precision@{top_k}",
                    "metric_desc": "样本不足，无法完成稳定评估。",
                    "k_value": top_k,
                    "evaluated_profiles": 0,
                    "eval_mode": "近似评估",
                }
            ]
        )

    profile_indexer = StringIndexer(inputCol="background_dim", outputCol="background_index", handleInvalid="skip").fit(evaluation_df)
    major_indexer = StringIndexer(inputCol="major_name", outputCol="major_index", handleInvalid="skip").fit(evaluation_df)
    indexed_df = major_indexer.transform(profile_indexer.transform(evaluation_df))

    train_df, test_df = indexed_df.randomSplit([0.8, 0.2], seed=42)
    train_profiles = train_df.select("background_index").distinct()
    test_df = test_df.join(train_profiles, "background_index", "inner")

    if test_df.count() == 0:
        return pd.DataFrame(
            [
                {
                    "metric_name": "Precision@K",
                    "metric_value": 0.0,
                    "metric_label": f"Precision@{top_k}",
                    "metric_desc": "测试画像在训练集中不可见，无法计算 Precision@K。",
                    "k_value": top_k,
                    "evaluated_profiles": 0,
                    "eval_mode": "近似评估",
                }
            ]
        )

    als = ALS(
        userCol="background_index",
        itemCol="major_index",
        ratingCol="rating",
        coldStartStrategy="drop",
        nonnegative=True,
        rank=6,
        maxIter=10,
        regParam=0.1,
    )
    model = als.fit(train_df)

    target_profiles = test_df.select("background_index").distinct()
    recommendations = (
        model.recommendForUserSubset(target_profiles, top_k)
        .select("background_index", explode("recommendations").alias("rec"))
        .select("background_index", col("rec.major_index").alias("major_index"))
        .groupBy("background_index")
        .agg(collect_set("major_index").alias("predicted_items"))
        .toPandas()
    )
    actual = (
        test_df.groupBy("background_index")
        .agg(collect_set("major_index").alias("actual_items"))
        .toPandas()
    )

    merged = actual.merge(recommendations, on="background_index", how="inner")
    if merged.empty:
        evaluated_profiles = 0
        precision_at_k = 0.0
        recall_at_k = 0.0
        hit_rate_at_k = 0.0
    else:
        precision_scores = []
        recall_scores = []
        hit_scores = []
        for _, row in merged.iterrows():
            actual_items = set(row["actual_items"] or [])
            predicted_items = set(row["predicted_items"] or [])
            hits = actual_items & predicted_items
            precision_scores.append(len(hits) / top_k if top_k else 0.0)
            recall_scores.append(len(hits) / len(actual_items) if actual_items else 0.0)
            hit_scores.append(1.0 if hits else 0.0)

        evaluated_profiles = len(merged)
        precision_at_k = float(sum(precision_scores) / evaluated_profiles)
        recall_at_k = float(sum(recall_scores) / evaluated_profiles)
        hit_rate_at_k = float(sum(hit_scores) / evaluated_profiles)

    return pd.DataFrame(
        [
            {
                "metric_name": "Precision@K",
                "metric_value": py_round(precision_at_k, 4),
                "metric_label": f"Precision@{top_k}",
                "metric_desc": "近似评估：按生源画像背景维度划分训练/测试后，Top-K 推荐中命中真实专业的平均比例。",
                "k_value": top_k,
                "evaluated_profiles": evaluated_profiles,
                "eval_mode": "近似评估",
            },
            {
                "metric_name": "Recall@K",
                "metric_value": py_round(recall_at_k, 4),
                "metric_label": f"Recall@{top_k}",
                "metric_desc": "近似评估：测试集中真实专业被 Top-K 推荐覆盖的平均比例。",
                "k_value": top_k,
                "evaluated_profiles": evaluated_profiles,
                "eval_mode": "近似评估",
            },
            {
                "metric_name": "HitRate@K",
                "metric_value": py_round(hit_rate_at_k, 4),
                "metric_label": f"HitRate@{top_k}",
                "metric_desc": "近似评估：至少命中一个真实专业的背景画像占比。",
                "k_value": top_k,
                "evaluated_profiles": evaluated_profiles,
                "eval_mode": "近似评估",
            },
        ]
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
    ).transform(student_df).select(
        "student_id",
        "student_name",
        "major_name",
        "industry_type",
        "leading_industry_tag",
        "student_features",
    )

    employer_stats = df.groupBy("employer_name").agg(count("*").alias("historical_count")).cache()
    max_historical_count = employer_stats.agg({"historical_count": "max"}).collect()[0][0] or 1
    employer_major_stats = df.groupBy("employer_name", "major_name").agg(count("*").alias("major_match_count"))

    job_df = (
        df.select("employer_name", "industry_type", "leading_industry_tag", "company_scale")
        .dropDuplicates(["employer_name"])
        .join(employer_stats, "employer_name", "left")
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
        "major_name",
        "industry_type",
        "leading_industry_tag",
        "student_features",
    ).join(
        job_df.select("employer_name", "industry_type", "leading_industry_tag", "company_scale", "historical_count", "job_features"),
        on=["industry_type", "leading_industry_tag"],
        how="inner",
    ).join(
        employer_major_stats,
        on=["employer_name", "major_name"],
        how="left",
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
        .withColumn("cosine_similarity", spark_round(col("dot_product") / (col("student_norm") * col("job_norm")), 6))
        .withColumn("major_match_count", when(col("major_match_count").isNull(), lit(0)).otherwise(col("major_match_count")))
        .withColumn("major_affinity", col("major_match_count") / col("historical_count"))
        .withColumn("popularity_penalty", (col("historical_count") / lit(float(max_historical_count))) * lit(0.18))
        .withColumn("major_bonus", col("major_affinity") * lit(0.12))
        .withColumn("diversity_jitter", (spark_abs(spark_hash(col("student_id"), col("employer_name"))) % lit(1000)) / lit(1000.0) * lit(0.03))
        .withColumn("ranking_score", spark_round(col("cosine_similarity") + col("major_bonus") - col("popularity_penalty") + col("diversity_jitter"), 6))
        .withColumn(
            "recommend_reason",
            concat(
                lit("该岗位与学生当前匹配的行业方向为"),
                col("industry_type"),
                lit("，产业标签为"),
                col("leading_industry_tag"),
                lit("，企业规模为"),
                col("company_scale"),
                lit("，并结合该专业历史去向与热门企业分布做了排序修正。"),
            ),
        )
    )

    ranking = Window.partitionBy("student_id").orderBy(col("ranking_score").desc(), col("cosine_similarity").desc(), col("employer_name"))
    return (
        scored.withColumn("rank_no", dense_rank().over(ranking))
        .filter(col("rank_no") <= TOP_K)
        .select(
            "student_id",
            "student_name",
            "employer_name",
            "industry_type",
            "leading_industry_tag",
            "company_scale",
            "cosine_similarity",
            "ranking_score",
            "recommend_reason",
            "rank_no",
        )
        .orderBy("student_id", "rank_no")
    )


def evaluate_job_recommendation(cosine_pdf):
    if cosine_pdf.empty:
        return pd.DataFrame()

    top1 = cosine_pdf[cosine_pdf["rank_no"] == 1].copy()
    topk = cosine_pdf[cosine_pdf["rank_no"] <= TOP_K].copy()
    avg_top1 = float(top1["cosine_similarity"].mean()) if not top1.empty else 0.0
    avg_topk = float(topk["cosine_similarity"].mean()) if not topk.empty else 0.0
    high_conf_ratio = float((top1["cosine_similarity"] >= 0.9).mean()) if not top1.empty else 0.0

    return pd.DataFrame(
        [
            {
                "metric_name": "AvgTop1Similarity",
                "metric_value": py_round(avg_top1, 4),
                "metric_label": "Top1 平均相似度",
                "metric_desc": "Top1 推荐结果的平均余弦相似度，反映模型对首推岗位的匹配强度。",
                "sample_size": int(len(top1)),
                "eval_mode": "相似度统计",
            },
            {
                "metric_name": "AvgTopKSimilarity",
                "metric_value": py_round(avg_topk, 4),
                "metric_label": f"Top{TOP_K} 平均相似度",
                "metric_desc": "Top-K 推荐列表的平均余弦相似度，用于观察候选岗位整体匹配水平。",
                "sample_size": int(len(topk)),
                "eval_mode": "相似度统计",
            },
            {
                "metric_name": "HighConfidenceRatio",
                "metric_value": py_round(high_conf_ratio, 4),
                "metric_label": "高相似度占比",
                "metric_desc": "Top1 推荐中相似度不低于 0.90 的学生占比，属于可运行的可信度统计指标。",
                "sample_size": int(len(top1)),
                "eval_mode": "相似度统计",
            },
        ]
    )


def run_matching_pipeline():
    spark = create_spark_session("SHU_Employment_CF_Refactor")

    try:
        print("[Matching] 正在加载四表关联数据...")
        df = load_joined_dataset(spark).cache()

        print("[Matching] 正在计算 ALS 招生匹配结果...")
        als_result = build_als_matching(df)
        persist_result(als_result, "ads_enrollment_matching")

        print("[Matching] 正在评估 ALS 招生匹配效果...")
        enrollment_eval_pdf = evaluate_enrollment_matching(df, TOP_K)
        enrollment_eval_pdf.to_sql(
            name="ads_enrollment_matching_eval",
            con=DB_ENGINE,
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )

        print("[Matching] 正在计算人岗匹配推荐结果...")
        cosine_result = build_cosine_job_matching(df)
        cosine_pdf = persist_result(cosine_result, "ads_job_recommendation")

        print("[Matching] 正在统计余弦推荐可信度...")
        job_eval_pdf = evaluate_job_recommendation(cosine_pdf)
        job_eval_pdf.to_sql(
            name="ads_job_recommendation_eval",
            con=DB_ENGINE,
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi",
        )

        print("[Matching] ALS 与人岗匹配结果处理完成。")
        return True
    except Exception as exc:
        print(f"[Matching] 运行失败: {exc}")
        traceback.print_exc()
        return False
    finally:
        spark.stop()


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    sys.exit(0 if run_matching_pipeline() else 1)
