# -*- coding: utf-8 -*-
"""
LSTM 岗位需求人数预测脚本。

预测目标：岗位需求人数 demand_count，而非薪资。
数据优先级：
1. ads_job_demand_monthly.demand_count
2. fact_job_demand.SUM(recruit_count)
3. fact_employment + fact_academic 的就业吸纳人数代理指标

输出：
- ads_job_demand_forecast
- ads_job_demand_forecast_eval
- ads_job_demand_forecast_backtest
"""

from __future__ import annotations

import io
import logging
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL_PYMYSQL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

try:
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.preprocessing import MinMaxScaler
except ImportError as exc:  # pragma: no cover - 环境缺少依赖时给出中文提示
    raise RuntimeError("缺少 scikit-learn，请先安装 requirements.txt 中的依赖。") from exc

try:
    import tensorflow as tf
    from tensorflow.keras.layers import Dense, Dropout, Input, LSTM
    from tensorflow.keras.models import Sequential
except ImportError:
    tf = None
    Dense = Dropout = Input = LSTM = Sequential = None


SEED = 42
LOOK_BACK = 6
FORECAST_HORIZON_MONTHS = 12
TEST_RATIO = 0.2
MAX_TRACK_COUNT = 8
MIN_MONTHS = LOOK_BACK + 3
LSTM_EPOCHS = int(os.getenv("JOB_DEMAND_LSTM_EPOCHS", "50"))

LOG_FILE = f"lstm_job_demand_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class TrackResult:
    track: str
    major_name: str
    job_category: str
    industry_tag: str
    city: str
    forecast_df: pd.DataFrame
    backtest_df: pd.DataFrame
    mae: float
    rmse: float
    mape: float
    train_window_size: int
    test_window_size: int
    total_demand: float
    growth_score: float


def set_random_seed() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    if tf is not None:
        tf.random.set_seed(SEED)


def get_db_engine():
    engine = create_engine(DB_URL_PYMYSQL, pool_pre_ping=True, pool_recycle=3600)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return engine


def table_exists(engine, table_name: str) -> bool:
    with engine.connect() as conn:
        exists = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).scalar()
    return bool(exists)


def table_row_count(engine, table_name: str) -> int:
    if not table_exists(engine, table_name):
        return 0
    with engine.connect() as conn:
        return int(conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar() or 0)


def safe_mape(actual_values, predicted_values) -> float:
    actual = np.asarray(actual_values, dtype=float)
    predicted = np.asarray(predicted_values, dtype=float)
    denominator = np.where(np.abs(actual) < 1e-6, np.nan, actual)
    values = np.abs((actual - predicted) / denominator) * 100
    values = values[~np.isnan(values)]
    return float(np.mean(values)) if len(values) else 0.0


def load_from_ads_monthly(engine) -> pd.DataFrame:
    query = """
        SELECT
            major_name,
            job_category,
            industry_tag,
            COALESCE(city, '全市') AS city,
            demand_month,
            SUM(demand_count) AS demand_count
        FROM ads_job_demand_monthly
        WHERE major_name IS NOT NULL
          AND job_category IS NOT NULL
          AND demand_month IS NOT NULL
        GROUP BY major_name, job_category, industry_tag, COALESCE(city, '全市'), demand_month
    """
    return pd.read_sql(query, engine)


def load_from_fact_job_demand(engine) -> pd.DataFrame:
    query = """
        SELECT
            major_name,
            job_category,
            leading_industry_tag AS industry_tag,
            COALESCE(city, '全市') AS city,
            DATE_FORMAT(publish_date, '%%Y-%%m') AS demand_month,
            SUM(GREATEST(0, COALESCE(recruit_count, 1))) AS demand_count
        FROM fact_job_demand
        WHERE publish_date IS NOT NULL
          AND major_name IS NOT NULL
          AND job_category IS NOT NULL
        GROUP BY major_name, job_category, leading_industry_tag, COALESCE(city, '全市'), DATE_FORMAT(publish_date, '%%Y-%%m')
    """
    return pd.read_sql(query, engine)


def load_from_employment_proxy(engine) -> pd.DataFrame:
    query = """
        SELECT
            a.major_name,
            '就业吸纳' AS job_category,
            COALESCE(e.leading_industry_tag, '未分类行业') AS industry_tag,
            '上海' AS city,
            DATE_FORMAT(e.first_insured_date, '%%Y-%%m') AS demand_month,
            COUNT(e.emp_id) AS demand_count
        FROM fact_employment e
        INNER JOIN fact_academic a ON e.student_id = a.student_id
        WHERE e.first_insured_date IS NOT NULL
          AND a.major_name IS NOT NULL
        GROUP BY a.major_name, COALESCE(e.leading_industry_tag, '未分类行业'), DATE_FORMAT(e.first_insured_date, '%%Y-%%m')
    """
    return pd.read_sql(query, engine)


def load_demand_timeseries(engine) -> tuple[pd.DataFrame, str]:
    """按优先级读取岗位需求时间序列数据。"""
    if table_row_count(engine, "ads_job_demand_monthly") > 0:
        df = load_from_ads_monthly(engine)
        if not df.empty:
            logger.info("读取 ads_job_demand_monthly 作为 LSTM 岗位需求预测输入。")
            return df, "ads_job_demand_monthly.demand_count"

    if table_row_count(engine, "fact_job_demand") > 0:
        df = load_from_fact_job_demand(engine)
        if not df.empty:
            logger.info("ads_job_demand_monthly 不可用，降级读取 fact_job_demand 聚合招聘人数。")
            return df, "fact_job_demand.SUM(recruit_count)"

    df = load_from_employment_proxy(engine)
    if not df.empty:
        logger.warning("fact_job_demand 不可用，当前使用 fact_employment 就业吸纳人数代理指标。")
        return df, "fact_employment.COUNT(emp_id) 代理指标"

    raise RuntimeError("没有可用于岗位需求人数预测的数据，请先导入岗位需求或就业数据。")


def prepare_monthly_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """标准化月度序列字段。"""
    df = raw_df.copy()
    df["demand_month"] = pd.to_datetime(df["demand_month"].astype(str) + "-01", errors="coerce")
    df["demand_count"] = pd.to_numeric(df["demand_count"], errors="coerce").fillna(0).clip(lower=0)
    df = df.dropna(subset=["demand_month", "major_name", "job_category"])
    df["industry_tag"] = df["industry_tag"].fillna("未分类行业")
    df["city"] = df["city"].fillna("全市")
    df["track"] = df["major_name"] + " / " + df["job_category"] + " / " + df["industry_tag"]
    return df


def select_tracks(df: pd.DataFrame) -> pd.DataFrame:
    """选择样本量充足、总需求较高、趋势明显的序列。"""
    profiles = []
    for track_key, group in df.groupby(["track", "major_name", "job_category", "industry_tag", "city"]):
        group = group.sort_values("demand_month")
        month_count = group["demand_month"].nunique()
        total_demand = float(group["demand_count"].sum())
        recent = group.tail(min(6, len(group)))["demand_count"].astype(float)
        if len(recent) >= 2 and recent.iloc[0] > 0:
            growth_score = float((recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0])
        else:
            growth_score = 0.0
        if month_count >= MIN_MONTHS and total_demand > 0:
            profiles.append(
                {
                    "track": track_key[0],
                    "major_name": track_key[1],
                    "job_category": track_key[2],
                    "industry_tag": track_key[3],
                    "city": track_key[4],
                    "month_count": month_count,
                    "total_demand": total_demand,
                    "growth_score": growth_score,
                    "selection_score": total_demand * (1 + max(growth_score, 0)),
                }
            )
    if not profiles:
        raise RuntimeError("没有满足最小月份要求的岗位需求序列，无法执行预测。")
    track_df = pd.DataFrame(profiles).sort_values(["selection_score", "total_demand"], ascending=False)
    return track_df.head(MAX_TRACK_COUNT).reset_index(drop=True)


def build_track_series(df: pd.DataFrame, meta: pd.Series) -> pd.DataFrame:
    """构造单条预测序列，并补齐缺失月份。"""
    group = df[
        (df["major_name"] == meta["major_name"])
        & (df["job_category"] == meta["job_category"])
        & (df["industry_tag"] == meta["industry_tag"])
        & (df["city"] == meta["city"])
    ].copy()
    ts = group.groupby("demand_month")["demand_count"].sum().sort_index()
    full_index = pd.date_range(ts.index.min(), ts.index.max(), freq="MS")
    ts = ts.reindex(full_index, fill_value=0)
    # 需求人数不应出现负数，缺失月份按 0 处理。
    ts = ts.clip(lower=0)
    return ts.to_frame(name="demand_count")


def build_lstm_model():
    model = Sequential(
        [
            Input(shape=(LOOK_BACK, 1)),
            LSTM(50, return_sequences=True),
            Dropout(0.1),
            LSTM(50),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mae")
    return model


def build_sequences(scaled_values: np.ndarray, months: list[pd.Timestamp]):
    x_rows, y_rows, target_months = [], [], []
    for index in range(len(scaled_values) - LOOK_BACK):
        x_rows.append(scaled_values[index : index + LOOK_BACK, 0])
        y_rows.append(scaled_values[index + LOOK_BACK, 0])
        target_months.append(months[index + LOOK_BACK])
    x_data = np.asarray(x_rows)
    y_data = np.asarray(y_rows)
    return x_data.reshape((x_data.shape[0], x_data.shape[1], 1)), y_data, target_months


def naive_forecast(values: np.ndarray, horizon: int) -> np.ndarray:
    """TensorFlow 不可用时的降级预测，使用近期趋势外推。"""
    clean_values = np.asarray(values, dtype=float).reshape(-1)
    recent = clean_values[-min(6, len(clean_values)) :]
    if len(recent) >= 2:
        monthly_delta = (recent[-1] - recent[0]) / (len(recent) - 1)
    else:
        monthly_delta = 0.0
    current = clean_values[-1]
    forecast = []
    for _ in range(horizon):
        current = max(0, current + monthly_delta)
        forecast.append(current)
    return np.asarray(forecast, dtype=float)


def train_single_track(meta: pd.Series, ts_data: pd.DataFrame) -> TrackResult:
    """训练单条岗位需求序列并生成未来 12 个月预测。"""
    values = ts_data[["demand_count"]].values.astype(float)
    months = list(ts_data.index)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(values)
    x_data, y_data, target_months = build_sequences(scaled_data, months)

    test_size = max(1, int(len(x_data) * TEST_RATIO))
    split_index = max(1, len(x_data) - test_size)
    x_train, x_test = x_data[:split_index], x_data[split_index:]
    y_train, y_test = y_data[:split_index], y_data[split_index:]
    test_months = target_months[split_index:]

    if tf is not None and len(x_train) >= 1:
        model = build_lstm_model()
        model.fit(x_train, y_train, epochs=LSTM_EPOCHS, batch_size=8, verbose=0)
        test_pred_scaled = model.predict(x_test, verbose=0).reshape(-1, 1)
        current_window = scaled_data[-LOOK_BACK:].reshape(1, LOOK_BACK, 1)
        future_scaled = []
        for _ in range(FORECAST_HORIZON_MONTHS):
            prediction = model.predict(current_window, verbose=0)
            future_scaled.append(prediction[0])
            current_window = np.concatenate([current_window[:, 1:, :], prediction.reshape(1, 1, 1)], axis=1)
        future_values = scaler.inverse_transform(np.asarray(future_scaled).reshape(-1, 1)).reshape(-1)
        model_name = "LSTM"
    else:
        logger.warning("TensorFlow 不可用或训练窗口不足，使用近期趋势降级预测：%s", meta["track"])
        y_history = scaler.inverse_transform(y_data.reshape(-1, 1)).reshape(-1)
        test_pred_actual = naive_forecast(y_history[:split_index], len(y_test))
        test_pred_scaled = scaler.transform(test_pred_actual.reshape(-1, 1))
        future_values = naive_forecast(values.reshape(-1), FORECAST_HORIZON_MONTHS)
        model_name = "LSTM-Fallback"

    actual_values = scaler.inverse_transform(y_test.reshape(-1, 1)).reshape(-1)
    predicted_values = scaler.inverse_transform(test_pred_scaled.reshape(-1, 1)).reshape(-1)
    actual_values = np.clip(actual_values, 0, None)
    predicted_values = np.clip(predicted_values, 0, None)
    future_values = np.clip(future_values, 0, None)

    mae = float(mean_absolute_error(actual_values, predicted_values))
    rmse = float(np.sqrt(mean_squared_error(actual_values, predicted_values)))
    mape = safe_mape(actual_values, predicted_values)

    first_future = float(future_values[0]) if len(future_values) else 0.0
    last_future = float(future_values[-1]) if len(future_values) else 0.0
    growth_rate = (last_future - first_future) / first_future if first_future > 0 else 0.0

    backtest_df = pd.DataFrame(
        {
            "track": meta["track"],
            "major_name": meta["major_name"],
            "job_category": meta["job_category"],
            "industry_tag": meta["industry_tag"],
            "forecast_month": [month.strftime("%Y-%m") for month in test_months],
            "actual_demand_count": np.round(actual_values, 2),
            "predicted_demand_count": np.round(predicted_values, 2),
            "abs_error": np.round(np.abs(actual_values - predicted_values), 2),
            "dataset_split": "test",
        }
    )

    forecast_df = pd.DataFrame(
        [
            {
                "track": meta["track"],
                "major_name": meta["major_name"],
                "job_category": meta["job_category"],
                "industry_tag": meta["industry_tag"],
                "city": meta["city"],
                "track_rank": 0,
                "forecast_month": (ts_data.index[-1] + pd.DateOffset(months=offset)).strftime("%Y-%m"),
                "predicted_demand_count": round(float(value), 2),
                "demand_growth_rate": round(float(growth_rate), 4),
                "demand_level": "待分级",
                "model_name": model_name,
            }
            for offset, value in enumerate(future_values, start=1)
        ]
    )

    return TrackResult(
        track=meta["track"],
        major_name=meta["major_name"],
        job_category=meta["job_category"],
        industry_tag=meta["industry_tag"],
        city=meta["city"],
        forecast_df=forecast_df,
        backtest_df=backtest_df,
        mae=mae,
        rmse=rmse,
        mape=mape,
        train_window_size=len(x_train),
        test_window_size=len(x_test),
        total_demand=float(meta["total_demand"]),
        growth_score=float(meta["growth_score"]),
    )


def assign_rank_and_level(forecast_df: pd.DataFrame, track_results: list[TrackResult]) -> pd.DataFrame:
    """按总需求和趋势排序，并生成高/中/低需求等级。"""
    rank_df = pd.DataFrame(
        [
            {
                "track": result.track,
                "rank_score": result.total_demand * (1 + max(result.growth_score, 0)),
            }
            for result in track_results
        ]
    ).sort_values("rank_score", ascending=False)
    rank_map = {track: index + 1 for index, track in enumerate(rank_df["track"])}
    forecast_df["track_rank"] = forecast_df["track"].map(rank_map).astype(int)

    q_high = forecast_df["predicted_demand_count"].quantile(0.70)
    q_mid = forecast_df["predicted_demand_count"].quantile(0.35)

    def level(value: float) -> str:
        if value >= q_high:
            return "高需求"
        if value >= q_mid:
            return "中需求"
        return "低需求"

    forecast_df["demand_level"] = forecast_df["predicted_demand_count"].apply(level)
    return forecast_df.sort_values(["track_rank", "forecast_month"]).reset_index(drop=True)


def build_metric_rows(track_results: list[TrackResult], data_source: str) -> pd.DataFrame:
    sample_size = int(sum(len(result.backtest_df) for result in track_results))
    train_window_size = int(sum(result.train_window_size for result in track_results))
    test_window_size = int(sum(result.test_window_size for result in track_results))
    return pd.DataFrame(
        [
            {
                "metric_name": "MAE",
                "metric_value": round(float(np.mean([result.mae for result in track_results])), 4),
                "metric_label": "平均绝对误差",
                "metric_unit": "人",
                "sample_size": sample_size,
                "train_window_size": train_window_size,
                "test_window_size": test_window_size,
                "metric_desc": f"岗位需求人数预测误差，数据来源：{data_source}。",
            },
            {
                "metric_name": "RMSE",
                "metric_value": round(float(np.mean([result.rmse for result in track_results])), 4),
                "metric_label": "均方根误差",
                "metric_unit": "人",
                "sample_size": sample_size,
                "train_window_size": train_window_size,
                "test_window_size": test_window_size,
                "metric_desc": "对较大预测偏差更敏感，用于衡量岗位需求趋势预测稳定性。",
            },
            {
                "metric_name": "MAPE",
                "metric_value": round(float(np.mean([result.mape for result in track_results])), 4),
                "metric_label": "平均绝对百分比误差",
                "metric_unit": "%",
                "sample_size": sample_size,
                "train_window_size": train_window_size,
                "test_window_size": test_window_size,
                "metric_desc": "衡量预测偏差占真实需求人数的比例，便于答辩解释模型可信度。",
            },
        ]
    )


def persist_results(engine, forecast_df: pd.DataFrame, metrics_df: pd.DataFrame, backtest_df: pd.DataFrame) -> None:
    """清空并写入岗位需求预测结果表。"""
    with engine.begin() as conn:
        for table_name in [
            "ads_job_demand_forecast",
            "ads_job_demand_forecast_eval",
            "ads_job_demand_forecast_backtest",
        ]:
            conn.execute(text(f"TRUNCATE TABLE `{table_name}`"))
        forecast_df.to_sql("ads_job_demand_forecast", conn, if_exists="append", index=False, chunksize=1000, method="multi")
        metrics_df.to_sql("ads_job_demand_forecast_eval", conn, if_exists="append", index=False, chunksize=1000, method="multi")
        backtest_df.to_sql("ads_job_demand_forecast_backtest", conn, if_exists="append", index=False, chunksize=1000, method="multi")


def train_and_forecast() -> bool:
    """主流程：加载数据、训练模型、写入预测结果。"""
    logger.info("=" * 80)
    logger.info("LSTM 岗位需求人数预测启动")
    logger.info("=" * 80)
    set_random_seed()
    if tf is None:
        logger.warning("当前环境未安装 TensorFlow，将使用趋势外推降级方案保证链路可运行。")

    try:
        engine = get_db_engine()
        raw_df, data_source = load_demand_timeseries(engine)
        monthly_df = prepare_monthly_dataframe(raw_df)
        selected_tracks = select_tracks(monthly_df)

        logger.info("已选出 %s 条岗位需求预测序列：", len(selected_tracks))
        for row in selected_tracks.itertuples(index=False):
            logger.info("  %s，月份=%s，总需求=%.0f，近期趋势=%.2f", row.track, row.month_count, row.total_demand, row.growth_score)

        track_results: list[TrackResult] = []
        for _, meta in selected_tracks.iterrows():
            ts_data = build_track_series(monthly_df, meta)
            result = train_single_track(meta, ts_data)
            track_results.append(result)
            logger.info(
                "预测完成：%s，MAE=%.2f，RMSE=%.2f，MAPE=%.2f%%",
                result.track,
                result.mae,
                result.rmse,
                result.mape,
            )

        forecast_df = pd.concat([result.forecast_df for result in track_results], ignore_index=True)
        forecast_df = assign_rank_and_level(forecast_df, track_results)
        backtest_df = pd.concat([result.backtest_df for result in track_results], ignore_index=True)
        metrics_df = build_metric_rows(track_results, data_source)

        persist_results(engine, forecast_df, metrics_df, backtest_df)

        logger.info("岗位需求人数预测结果写入完成：ads_job_demand_forecast=%s 行", len(forecast_df))
        logger.info("评估表=%s 行，回测表=%s 行", len(metrics_df), len(backtest_df))
        logger.info("预测目标字段：predicted_demand_count；历史目标字段：demand_count。")
        logger.info("LSTM 岗位需求人数预测完成。")
        return True
    except Exception:
        logger.exception("LSTM 岗位需求人数预测失败")
        return False


if __name__ == "__main__":
    sys.exit(0 if train_and_forecast() else 1)
