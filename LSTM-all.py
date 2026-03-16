import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input

# 修正：从 DB_URL 或直接定义连接串
DB_URL = "mysql+pymysql://root:123456@localhost:3306/bigdata?charset=utf8mb4"

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def train_and_forecast():
    print("🚀 启动上海高校薪资趋势预测引擎 (基于 LSTM)...")

    # 1. 数据获取
    engine = create_engine(DB_URL)
    # 增加聚合逻辑：按月统计平均薪资，减少噪声
    query = """
    SELECT first_insured_date, avg_salary 
    FROM fact_employment 
    WHERE first_insured_date IS NOT NULL
    ORDER BY first_insured_date ASC
    """
    df = pd.read_sql(query, engine)

    if df.empty:
        print("🚨 数据库中无有效薪资记录，请先运行数据导入脚本。")
        return

    # 2. 时间序列预处理
    df['date'] = pd.to_datetime(df['first_insured_date'])
    # 将离散的就业记录聚合为“月度平均起薪”时间序列
    # 使用 'ME' (Month End) 或 'MS' (Month Start)
    ts_data = df.groupby(pd.Grouper(key='date', freq='ME'))['avg_salary'].mean().to_frame()

    # 填充缺失月份（如果有），模拟数据的连续性
    ts_data = ts_data.ffill()
    values = ts_data.values

    # 学术建议：LSTM 需要足够的时间序列长度
    if len(values) < 12:
        print(f"🚨 样本月度不足（当前仅 {len(values)} 个月），模型难以捕获季节性特征。")
        return

    # 3. 归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(values)

    # 4. 构造滑动窗口 (针对 5 年数据，建议 look_back 设为 6 或 12)
    look_back = 6
    X, y = [], []
    for i in range(len(scaled_data) - look_back):
        X.append(scaled_data[i:(i + look_back), 0])
        y.append(scaled_data[i + look_back, 0])

    X, y = np.array(X), np.array(y)
    # 转换为 LSTM 要求的 [samples, time_steps, features]
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    # 5. 构建改进型 LSTM 模型
    model = Sequential([
        Input(shape=(look_back, 1)),
        LSTM(50, return_sequences=True),
        Dropout(0.1),
        LSTM(50, return_sequences=False),
        Dropout(0.1),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mae')  # 对于薪资预测，MAE 比 MSE 更具鲁棒性

    print(f"💡 正在基于 {len(X)} 个滑动窗口进行深度学习训练...")
    model.fit(X, y, epochs=100, batch_size=8, verbose=0)

    # 6. 滚动预测未来 6 个月（外推法）
    predictions_scaled = []
    # 取最后一段已知窗口
    current_window = scaled_data[-look_back:].reshape(1, look_back, 1)

    for _ in range(6):
        pred = model.predict(current_window, verbose=0)
        predictions_scaled.append(pred[0])
        # 将预测值压入窗口，剔除最早的一个值
        new_point = pred.reshape(1, 1, 1)
        current_window = np.concatenate([current_window[:, 1:, :], new_point], axis=1)

    # 逆归一化
    forecast_results = scaler.inverse_transform(predictions_scaled)

    # 7. 结果持久化
    print("\n" + "=" * 30)
    last_date = ts_data.index[-1]
    forecast_list = []

    for i, res in enumerate(forecast_results):
        # 预测日期为最后已知日期的后 N 个月
        forecast_date = last_date + pd.DateOffset(months=i + 1)
        pred_val = float(res[0])
        forecast_list.append({
            'forecast_month': forecast_date.strftime('%Y-%m'),
            'predicted_salary': round(pred_val, 2)
        })
        print(f"预测期: {forecast_date.strftime('%Y-%m')} | 预计起薪: ¥{pred_val:.2f}")

    df_forecast = pd.DataFrame(forecast_list)

    try:
        with engine.begin() as conn:
            # 确保 ads_salary_forecast 表存在或清空
            conn.execute(text("DROP TABLE IF EXISTS ads_salary_forecast"))
            df_forecast.to_sql('ads_salary_forecast', conn, if_exists='append', index=False)
        print("✅ 预测分析已更新至数据库。")
    except Exception as e:
        print(f"🚨 持久化失败: {e}")


if __name__ == "__main__":
    train_and_forecast()