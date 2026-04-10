import io
import os
import random
import sys

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy import create_engine, text
from tensorflow.keras.layers import Dense, Dropout, Input, LSTM
from tensorflow.keras.models import Sequential

from config import DB_URL


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

SEED = 42
FORECAST_HORIZON_MONTHS = 12
LOOK_BACK = 6
TEST_RATIO = 0.2
DEFAULT_TRACK_COUNT = 5
MAX_TRACK_COUNT = 10
MIN_MONTHS = LOOK_BACK + 6
MIN_SAMPLE_COUNT = 1800
MIN_FORECAST_SPAN_RATIO = 0.01
MAX_TRACKS_PER_CATEGORY = 2


def set_random_seed():
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def safe_mape(actual_values, predicted_values):
    actual = np.array(actual_values, dtype=float)
    predicted = np.array(predicted_values, dtype=float)
    denominator = np.where(np.abs(actual) < 1e-6, np.nan, actual)
    mape = np.abs((actual - predicted) / denominator) * 100
    mape = mape[~np.isnan(mape)]
    return float(np.mean(mape)) if len(mape) else 0.0


def build_sequences(scaled_values, months):
    feature_rows = []
    target_rows = []
    target_months = []

    for index in range(len(scaled_values) - LOOK_BACK):
        feature_rows.append(scaled_values[index : index + LOOK_BACK, 0])
        target_rows.append(scaled_values[index + LOOK_BACK, 0])
        target_months.append(months[index + LOOK_BACK])

    x_data = np.array(feature_rows)
    y_data = np.array(target_rows)
    x_data = np.reshape(x_data, (x_data.shape[0], x_data.shape[1], 1))
    return x_data, y_data, target_months


def build_lstm_model():
    model = Sequential(
        [
            Input(shape=(LOOK_BACK, 1)),
            LSTM(50, return_sequences=True),
            Dropout(0.1),
            LSTM(50, return_sequences=False),
            Dropout(0.1),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mae")
    return model


def load_major_salary_data(engine):
    query = """
        SELECT
            e.first_insured_date,
            a.major_name,
            COALESCE(a.discipline_category, '未分类') AS category,
            e.avg_salary
        FROM fact_employment e
        INNER JOIN fact_academic a ON e.student_id = a.student_id
        WHERE e.first_insured_date IS NOT NULL
          AND a.major_name IS NOT NULL
          AND e.avg_salary IS NOT NULL
    """
    raw_df = pd.read_sql(query, engine)
    if raw_df.empty:
        raise RuntimeError("fact_employment 与 fact_academic 中没有可用于预测的有效记录。")

    raw_df["date"] = pd.to_datetime(raw_df["first_insured_date"])
    raw_df["avg_salary"] = raw_df["avg_salary"].astype(float)
    raw_df["month"] = raw_df["date"].dt.to_period("M").dt.to_timestamp("M")
    return raw_df


def compute_monthly_profiles(raw_df):
    monthly_df = (
        raw_df.groupby(["major_name", "category", "month"])["avg_salary"]
        .mean()
        .reset_index()
        .sort_values(["major_name", "month"])
    )
    profiles = []

    for (major_name, category), group in monthly_df.groupby(["major_name", "category"]):
        values = group["avg_salary"].astype(float)
        month_count = len(group)
        recent_values = values.tail(min(6, month_count))
        avg_salary = float(values.mean())
        history_span_ratio = float((values.max() - values.min()) / avg_salary) if avg_salary else 0.0
        recent_span_ratio = (
            float((recent_values.max() - recent_values.min()) / recent_values.mean())
            if recent_values.mean()
            else 0.0
        )
        recent_growth_ratio = (
            float(abs(recent_values.iloc[-1] - recent_values.iloc[0]) / recent_values.mean())
            if len(recent_values) >= 2 and recent_values.mean()
            else 0.0
        )
        salary_std = float(values.std(ddof=0)) if len(values) > 1 else 0.0

        profiles.append(
            {
                "major_name": major_name,
                "category": category,
                "month_count": month_count,
                "avg_salary": avg_salary,
                "salary_std": salary_std,
                "history_span_ratio": history_span_ratio,
                "recent_span_ratio": recent_span_ratio,
                "recent_growth_ratio": recent_growth_ratio,
            }
        )

    return pd.DataFrame(profiles)


def summarize_track_candidates(raw_df):
    sample_summary = (
        raw_df.groupby(["major_name", "category"])
        .agg(sample_count=("avg_salary", "size"))
        .reset_index()
    )
    monthly_profiles = compute_monthly_profiles(raw_df)
    summary = sample_summary.merge(monthly_profiles, on=["major_name", "category"], how="inner")
    summary = summary[
        (summary["month_count"] >= MIN_MONTHS)
        & (summary["sample_count"] >= MIN_SAMPLE_COUNT)
    ].copy()
    if summary.empty:
        raise RuntimeError("没有满足最小样本量与时间跨度要求的专业序列，无法生成专业薪资预测。")

    def rank_series(column_name):
        return summary[column_name].rank(pct=True, method="average")

    summary["sample_rank"] = rank_series("sample_count")
    summary["month_rank"] = rank_series("month_count")
    summary["std_rank"] = rank_series("salary_std")
    summary["history_span_rank"] = rank_series("history_span_ratio")
    summary["recent_span_rank"] = rank_series("recent_span_ratio")
    summary["recent_growth_rank"] = rank_series("recent_growth_ratio")

    summary["selection_score"] = (
        summary["sample_rank"] * 0.28
        + summary["month_rank"] * 0.12
        + summary["std_rank"] * 0.18
        + summary["history_span_rank"] * 0.22
        + summary["recent_span_rank"] * 0.12
        + summary["recent_growth_rank"] * 0.08
    )

    return summary.sort_values(
        by=[
            "selection_score",
            "history_span_ratio",
            "recent_growth_ratio",
            "sample_count",
        ],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def select_candidate_tracks(raw_df):
    candidates = summarize_track_candidates(raw_df)
    selected_rows = []
    category_counter = {}

    for _, row in candidates.iterrows():
        category = row["category"]
        if category_counter.get(category, 0) >= MAX_TRACKS_PER_CATEGORY:
            continue
        selected_rows.append(row.to_dict())
        category_counter[category] = category_counter.get(category, 0) + 1
        if len(selected_rows) >= MAX_TRACK_COUNT:
            break

    if len(selected_rows) < DEFAULT_TRACK_COUNT:
        for _, row in candidates.iterrows():
            major_name = row["major_name"]
            if any(item["major_name"] == major_name for item in selected_rows):
                continue
            selected_rows.append(row.to_dict())
            if len(selected_rows) >= DEFAULT_TRACK_COUNT:
                break

    if len(selected_rows) < DEFAULT_TRACK_COUNT:
        raise RuntimeError(f"有效专业序列不足，仅找到 {len(selected_rows)} 条。")

    return pd.DataFrame(selected_rows).reset_index(drop=True)


def build_major_timeseries(raw_df, major_name):
    major_df = raw_df[raw_df["major_name"] == major_name].copy()
    ts_data = (
        major_df.groupby("month")["avg_salary"]
        .mean()
        .sort_index()
        .to_frame(name="avg_salary")
    )
    ts_data = ts_data.ffill().bfill()
    if len(ts_data) < MIN_MONTHS:
        raise RuntimeError(f"{major_name} 月度样本不足，仅有 {len(ts_data)} 个月。")
    return ts_data


def train_single_track(track_meta, ts_data):
    set_random_seed()
    values = ts_data.values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(values)
    months = list(ts_data.index)

    x_data, y_data, target_months = build_sequences(scaled_data, months)
    if len(x_data) < 6:
        raise RuntimeError(f"{track_meta['track']} 有效滑动窗口不足，仅 {len(x_data)} 条。")

    test_size = max(1, int(len(x_data) * TEST_RATIO))
    split_index = len(x_data) - test_size
    if split_index < 1:
        raise RuntimeError(f"{track_meta['track']} 训练集窗口不足。")

    x_train, x_test = x_data[:split_index], x_data[split_index:]
    y_train, y_test = y_data[:split_index], y_data[split_index:]
    test_months = target_months[split_index:]

    model = build_lstm_model()
    model.fit(x_train, y_train, epochs=80, batch_size=8, verbose=0)

    test_predictions_scaled = model.predict(x_test, verbose=0).reshape(-1, 1)
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1)).reshape(-1)
    y_test_predicted = scaler.inverse_transform(test_predictions_scaled).reshape(-1)

    mae = float(mean_absolute_error(y_test_actual, y_test_predicted))
    rmse = float(np.sqrt(mean_squared_error(y_test_actual, y_test_predicted)))
    mape = safe_mape(y_test_actual, y_test_predicted)

    backtest_df = pd.DataFrame(
        {
            "track": track_meta["track"],
            "major_name": track_meta["major_name"],
            "category": track_meta["category"],
            "track_rank": 0,
            "forecast_month": [month.strftime("%Y-%m") for month in test_months],
            "actual_salary": np.round(y_test_actual, 2),
            "predicted_salary": np.round(y_test_predicted, 2),
            "abs_error": np.round(np.abs(y_test_actual - y_test_predicted), 2),
            "dataset_split": "test",
        }
    )

    current_window = scaled_data[-LOOK_BACK:].reshape(1, LOOK_BACK, 1)
    future_predictions = []
    for _ in range(FORECAST_HORIZON_MONTHS):
        prediction = model.predict(current_window, verbose=0)
        future_predictions.append(prediction[0])
        next_point = prediction.reshape(1, 1, 1)
        current_window = np.concatenate([current_window[:, 1:, :], next_point], axis=1)

    future_forecast = scaler.inverse_transform(future_predictions).reshape(-1)
    forecast_df = pd.DataFrame(
        [
            {
                "track": track_meta["track"],
                "major_name": track_meta["major_name"],
                "category": track_meta["category"],
                "track_rank": 0,
                "forecast_month": (ts_data.index[-1] + pd.DateOffset(months=offset)).strftime("%Y-%m"),
                "predicted_salary": round(float(result), 2),
            }
            for offset, result in enumerate(future_forecast, start=1)
        ]
    )

    forecast_span_ratio = (
        float((forecast_df["predicted_salary"].max() - forecast_df["predicted_salary"].min()) / forecast_df["predicted_salary"].mean())
        if forecast_df["predicted_salary"].mean()
        else 0.0
    )

    return {
        "major_name": track_meta["major_name"],
        "category": track_meta["category"],
        "forecast_df": forecast_df,
        "backtest_df": backtest_df,
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "forecast_span_ratio": forecast_span_ratio,
        "train_window_size": len(x_train),
        "test_window_size": len(x_test),
    }


def reorder_tracks(candidate_df, track_results):
    quality_df = candidate_df.merge(
        pd.DataFrame(
            [
                {
                    "major_name": item["major_name"],
                    "category": item["category"],
                    "forecast_span_ratio": item["forecast_span_ratio"],
                }
                for item in track_results
            ]
        ),
        on=["major_name", "category"],
        how="left",
    )
    quality_df["forecast_span_ratio"] = quality_df["forecast_span_ratio"].fillna(0.0)
    quality_df["display_candidate"] = quality_df["forecast_span_ratio"] >= MIN_FORECAST_SPAN_RATIO
    quality_df["display_score"] = (
        quality_df["selection_score"] * 0.58
        + quality_df["history_span_ratio"] * 1.6
        + quality_df["recent_growth_ratio"] * 1.2
        + quality_df["forecast_span_ratio"] * 5.5
    )

    ordered_df = quality_df.sort_values(
        by=[
            "display_candidate",
            "display_score",
            "forecast_span_ratio",
            "selection_score",
            "sample_count",
        ],
        ascending=[False, False, False, False, False],
    ).reset_index(drop=True)

    if ordered_df["display_candidate"].sum() < DEFAULT_TRACK_COUNT:
        ordered_df = ordered_df.sort_values(
            by=["display_score", "selection_score", "sample_count"],
            ascending=[False, False, False],
        ).reset_index(drop=True)

    ordered_df["track_rank"] = ordered_df.index + 1
    return ordered_df


def attach_final_rank(dataframe, rank_map):
    dataframe["track_rank"] = dataframe["major_name"].map(rank_map).astype(int)
    return dataframe.sort_values(["track_rank", "forecast_month"]).reset_index(drop=True)


def build_metric_rows(metric_rows):
    sample_size = int(sum(len(row["backtest_df"]) for row in metric_rows))
    train_window_size = int(sum(row["train_window_size"] for row in metric_rows))
    test_window_size = int(sum(row["test_window_size"] for row in metric_rows))

    return pd.DataFrame(
        [
            {
                "metric_name": "MAE",
                "metric_value": round(float(np.mean([row["mae"] for row in metric_rows])), 4),
                "metric_label": "平均绝对误差",
                "metric_unit": "元",
                "sample_size": sample_size,
                "train_window_size": train_window_size,
                "test_window_size": test_window_size,
                "metric_desc": "反映预测值与真实值之间的平均偏差，越低说明整体误差越小。",
            },
            {
                "metric_name": "RMSE",
                "metric_value": round(float(np.mean([row["rmse"] for row in metric_rows])), 4),
                "metric_label": "均方根误差",
                "metric_unit": "元",
                "sample_size": sample_size,
                "train_window_size": train_window_size,
                "test_window_size": test_window_size,
                "metric_desc": "对较大预测偏差更敏感，越低说明极端误差控制得越好。",
            },
            {
                "metric_name": "MAPE",
                "metric_value": round(float(np.mean([row["mape"] for row in metric_rows])), 4),
                "metric_label": "平均绝对百分比误差",
                "metric_unit": "%",
                "sample_size": sample_size,
                "train_window_size": train_window_size,
                "test_window_size": test_window_size,
                "metric_desc": "用于衡量预测误差占真实值的相对比例，便于答辩时解释模型可信度。",
            },
        ]
    )


def train_and_forecast():
    print("[LSTM] 启动薪资需求预测...")
    set_random_seed()

    try:
        engine = create_engine(DB_URL)
        raw_df = load_major_salary_data(engine)
        candidate_tracks = select_candidate_tracks(raw_df)
        print("[LSTM] 已选出候选专业序列：")
        for row in candidate_tracks.itertuples():
            print(
                f"  {row.major_name}（{row.category}）"
                f" sample={row.sample_count}, months={row.month_count}, "
                f"history_span={row.history_span_ratio:.3f}, trend={row.recent_growth_ratio:.3f}"
            )

        track_results = []
        for row in candidate_tracks.itertuples():
            ts_data = build_major_timeseries(raw_df, row.major_name)
            result = train_single_track(
                {
                    "track": row.major_name,
                    "major_name": row.major_name,
                    "category": row.category,
                },
                ts_data,
            )
            track_results.append(result)
            print(
                f"[LSTM] {row.major_name}: train={result['train_window_size']}, "
                f"test={result['test_window_size']}, forecast_span={result['forecast_span_ratio']:.3f}, "
                f"MAE={result['mae']:.2f}"
            )

        ordered_tracks = reorder_tracks(candidate_tracks, track_results)
        rank_map = dict(zip(ordered_tracks["major_name"], ordered_tracks["track_rank"]))

        forecast_frames = []
        backtest_frames = []
        for result in track_results:
            forecast_frames.append(attach_final_rank(result["forecast_df"], rank_map))
            backtest_frames.append(attach_final_rank(result["backtest_df"], rank_map))

        forecast_df = pd.concat(forecast_frames, ignore_index=True)
        backtest_df = pd.concat(backtest_frames, ignore_index=True)
        metrics_df = build_metric_rows(track_results)

        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast"))
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast_eval"))
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast_backtest"))
            forecast_df.to_sql("ads_salary_forecast", conn, if_exists="append", index=False)
            metrics_df.to_sql("ads_salary_forecast_eval", conn, if_exists="append", index=False)
            backtest_df.to_sql("ads_salary_forecast_backtest", conn, if_exists="append", index=False)

        print("[LSTM] 默认展示的前 5 条曲线：")
        for row in ordered_tracks.head(DEFAULT_TRACK_COUNT).itertuples():
            print(
                f"  Rank {row.track_rank}: {row.major_name}（{row.category}）"
                f" forecast_span={row.forecast_span_ratio:.3f}, score={row.display_score:.3f}"
            )

        print(
            f"[LSTM] 预测结果已写入 ads_salary_forecast，"
            f"tracks={ordered_tracks.shape[0]}, default_display={DEFAULT_TRACK_COUNT}, rows={len(forecast_df)}"
        )
        print(
            f"[LSTM] 评估结果已写入 ads_salary_forecast_eval / ads_salary_forecast_backtest，"
            f"MAE={metrics_df.loc[metrics_df.metric_name == 'MAE', 'metric_value'].iloc[0]:.2f}, "
            f"RMSE={metrics_df.loc[metrics_df.metric_name == 'RMSE', 'metric_value'].iloc[0]:.2f}, "
            f"MAPE={metrics_df.loc[metrics_df.metric_name == 'MAPE', 'metric_value'].iloc[0]:.2f}%"
        )
        return True
    except Exception as exc:
        print(f"[LSTM] 运行失败: {exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if train_and_forecast() else 1)
