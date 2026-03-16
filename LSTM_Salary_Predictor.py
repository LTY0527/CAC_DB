import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from config import DB_URL

# 隐藏 TensorFlow 调试日志
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def train_and_forecast():
    print("🚀 启动 LSTM 薪资预测引擎...")

    # 1. 从 MySQL 读取历史薪资数据
    engine = create_engine(DB_URL)
    query = "SELECT first_insured_date, avg_salary FROM fact_employment ORDER BY first_insured_date ASC"
    df = pd.read_sql(query, engine)

    # 2. 数据预处理
    df['date'] = pd.to_datetime(df['first_insured_date'])
    df.set_index('date', inplace=True)
    monthly_data = df['avg_salary'].resample('ME').mean().ffill().values.reshape(-1, 1)

    if len(monthly_data) < 10:
        print("🚨 数据量不足以进行时间序列训练（当前点数: {}）。".format(len(monthly_data)))
        return

    # 3. 归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(monthly_data)

    # 4. 构造滑动窗口 (Look-back=3)
    look_back = 3
    X, y = [], []
    for i in range(len(scaled_data) - look_back):
        X.append(scaled_data[i:(i + look_back), 0])
        y.append(scaled_data[i + look_back, 0])
    X, y = np.array(X), np.array(y)
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    # 5. 构建模型
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(look_back, 1)),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error')

    print("💡 正在训练深度学习模型...")
    model.fit(X, y, epochs=50, batch_size=4, verbose=0)

    # 6. 滚动预测未来 3 个月
    last_window = scaled_data[-look_back:].reshape(1, look_back, 1)
    predictions_scaled = []
    current_batch = last_window

    for _ in range(3):
        pred = model.predict(current_batch, verbose=0)
        predictions_scaled.append(pred[0])
        current_batch = np.append(current_batch[:, 1:, :], [pred.reshape(1, 1)], axis=1)

    # 逆归一化
    forecast_results = scaler.inverse_transform(predictions_scaled)

    # ==========================================
    # 7. 结果持久化 (存入 MySQL)
    # ==========================================
    print("\n" + "=" * 30)
    print("📈 预测结果持久化中...")

    last_date = df.index[-1]
    forecast_list = []

    for i, res in enumerate(forecast_results):
        forecast_date = last_date + pd.offsets.MonthEnd(i + 1)
        pred_val = float(res[0])
        forecast_list.append({
            'forecast_month': forecast_date.strftime('%Y-%m'),
            'predicted_salary': round(pred_val, 2)
        })
        print(f"日期: {forecast_date.strftime('%Y-%m')} | 预测起薪: ¥{pred_val:.2f}")

    df_forecast = pd.DataFrame(forecast_list)

    # 写入数据库逻辑
    try:
        with engine.begin() as conn:
            # 先清空旧的预测结果，确保看板展示的是最新的
            conn.execute(text("TRUNCATE TABLE ads_salary_forecast"))
            # 写入新结果
            df_forecast.to_sql('ads_salary_forecast', conn, if_exists='append', index=False)
        print("✅ 结果已成功更新至 ads_salary_forecast 表。")
    except Exception as e:
        print(f"🚨 数据库写入失败: {e}")

    print("=" * 30)


if __name__ == "__main__":
    train_and_forecast()