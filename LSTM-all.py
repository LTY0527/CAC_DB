import io
import os
import sys

import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import Dense, Dropout, Input, LSTM
from tensorflow.keras.models import Sequential


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DB_URL = "mysql+pymysql://root:123456@localhost:3306/bigdata?charset=utf8mb4"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
FORECAST_HORIZON_MONTHS = 12
LOOK_BACK = 6
TEST_RATIO = 0.2


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


def train_and_forecast():
    print("[LSTM] 启动需求预测引擎...")

    try:
        engine = create_engine(DB_URL)
        query = """
        SELECT first_insured_date, avg_salary
        FROM fact_employment
        WHERE first_insured_date IS NOT NULL
        ORDER BY first_insured_date ASC
        """
        raw_df = pd.read_sql(query, engine)

        if raw_df.empty:
            raise RuntimeError("fact_employment 中没有可用于预测的有效记录。")

        raw_df["date"] = pd.to_datetime(raw_df["first_insured_date"])
        ts_data = raw_df.groupby(pd.Grouper(key="date", freq="ME"))["avg_salary"].mean().to_frame()
        ts_data = ts_data.ffill()

        if len(ts_data) < LOOK_BACK + 6:
            raise RuntimeError(f"月度样本不足，当前仅 {len(ts_data)} 个月，无法稳定完成训练/测试评估。")

        values = ts_data.values
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(values)
        months = list(ts_data.index)

        x_data, y_data, target_months = build_sequences(scaled_data, months)
        if len(x_data) < 6:
            raise RuntimeError(f"有效滑动窗口不足，当前仅 {len(x_data)} 条，无法完成模型评估。")

        test_size = max(1, int(len(x_data) * TEST_RATIO))
        if len(x_data) - test_size < 1:
            raise RuntimeError("训练集样本不足，请增加时间序列长度后再运行。")

        split_index = len(x_data) - test_size
        x_train, x_test = x_data[:split_index], x_data[split_index:]
        y_train, y_test = y_data[:split_index], y_data[split_index:]
        test_months = target_months[split_index:]

        model = build_lstm_model()
        print(
            f"[LSTM] 训练集窗口数={len(x_train)}, 测试集窗口数={len(x_test)}, "
            f"预测周期={FORECAST_HORIZON_MONTHS}个月"
        )
        model.fit(x_train, y_train, epochs=100, batch_size=8, verbose=0)

        test_predictions_scaled = model.predict(x_test, verbose=0).reshape(-1, 1)
        y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1)).reshape(-1)
        y_test_predicted = scaler.inverse_transform(test_predictions_scaled).reshape(-1)

        mae = float(mean_absolute_error(y_test_actual, y_test_predicted))
        rmse = float(np.sqrt(mean_squared_error(y_test_actual, y_test_predicted)))
        mape = safe_mape(y_test_actual, y_test_predicted)

        backtest_df = pd.DataFrame(
            {
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

        future_forecast = scaler.inverse_transform(future_predictions)
        last_date = ts_data.index[-1]
        forecast_df = pd.DataFrame(
            [
                {
                    "forecast_month": (last_date + pd.DateOffset(months=offset)).strftime("%Y-%m"),
                    "predicted_salary": round(float(result[0]), 2),
                }
                for offset, result in enumerate(future_forecast, start=1)
            ]
        )

        metrics_df = pd.DataFrame(
            [
                {
                    "metric_name": "MAE",
                    "metric_value": round(mae, 4),
                    "metric_label": "平均绝对误差",
                    "metric_unit": "元",
                    "sample_size": len(y_test_actual),
                    "train_window_size": len(x_train),
                    "test_window_size": len(x_test),
                    "metric_desc": "测试集上预测值与真实值的平均绝对偏差，越低越好。",
                },
                {
                    "metric_name": "RMSE",
                    "metric_value": round(rmse, 4),
                    "metric_label": "均方根误差",
                    "metric_unit": "元",
                    "sample_size": len(y_test_actual),
                    "train_window_size": len(x_train),
                    "test_window_size": len(x_test),
                    "metric_desc": "测试集上更强调大误差的预测偏差指标，越低越好。",
                },
                {
                    "metric_name": "MAPE",
                    "metric_value": round(mape, 4),
                    "metric_label": "平均绝对百分比误差",
                    "metric_unit": "%",
                    "sample_size": len(y_test_actual),
                    "train_window_size": len(x_train),
                    "test_window_size": len(x_test),
                    "metric_desc": "测试集上预测误差占真实值的平均比例，越低越好。",
                },
            ]
        )

        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast"))
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast_eval"))
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast_backtest"))
            forecast_df.to_sql("ads_salary_forecast", conn, if_exists="append", index=False)
            metrics_df.to_sql("ads_salary_forecast_eval", conn, if_exists="append", index=False)
            backtest_df.to_sql("ads_salary_forecast_backtest", conn, if_exists="append", index=False)

        print(
            f"[LSTM] 预测结果已写入 ads_salary_forecast, horizon={FORECAST_HORIZON_MONTHS}个月, rows={len(forecast_df)}"
        )
        print(
            f"[LSTM] 评估结果已写入 ads_salary_forecast_eval / ads_salary_forecast_backtest, "
            f"MAE={mae:.2f}, RMSE={rmse:.2f}, MAPE={mape:.2f}%"
        )
        return True
    except Exception as exc:
        print(f"[LSTM] 运行失败: {exc}")
        return False


if __name__ == "__main__":
    sys.exit(0 if train_and_forecast() else 1)
