# 任务1：技术选型分析

在能源经济学机器学习领域（以碳价预测为例），不同模型在处理时序依赖、特征交互、长距离依赖等方面各有优劣。下表对比主流方案：

| 方案 | 适用场景 | 成熟度评级 | 推荐理由 |
|------|----------|------------|----------|
| **LSTM/GRU** | 纯时序预测（如日度碳价序列） | ★★★★★ | 天然适合序列建模，可捕捉长期依赖；RNN变体均经过大量验证，调参指南成熟。 |
| **XGBoost/LightGBM** | 特征驱动预测（多因子：宏观经济、政策、天气、成交量等） | ★★★★★ | 对结构化数据高效，内置正则化、特征重要性、缺失值处理；集成学习泛化能力强，Kaggle竞赛首选。 |
| **Transformer** | 长序列、多变量、跨模态（文本+数值，如新闻情绪+价格） | ★★★★ | 自注意力机制可捕获全局依赖，但需要大量训练数据且计算开销大；在金融时间序列中仍处于探索期。 |
| **混合模型** (CNN-LSTM, Attention-XGBoost, LSTM-XGBoost) | 复杂模式提取：先CNN降维局部模式，再LSTM建模时序；或以LSTM/Attention提取特征后输入梯度提升树 | ★★★★ | 结合深度学习特征提取能力与树模型非线性拟合优势，在碳价预测竞赛中常获最优成绩；但调参复杂、易过拟合。 |

**选型建议**：碳价预测通常同时依赖**时序自相关性**（如趋势、季节）和**外部因子**（如能源价格、政策动向）。建议以 **XGBoost/LightGBM 作为基线**（快速验证、可解释），若需提升精度可级联 **LSTM 提取时序隐状态**作为特征输入 XGBoost（混合模型），或使用 **Attention 增强特征**后再用 LightGBM。对于仅依赖历史价格的纯序列预测，LSTM/GRU 足够。

---

# 任务2：碳价预测完整代码（LSTM + XGBoost 混合模型）

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Tuple, List, Optional

# 数据预处理
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split

# 模型
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from xgboost import XGBRegressor

# 评估
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ------------------------------------------------------------
# 1. 数据获取（此处使用模拟数据，实际可替换为公开数据集）
# ------------------------------------------------------------
def generate_synthetic_carbon_price(
    n: int = 1500,
    seed: int = 42
) -> pd.DataFrame:
    """
    生成模拟碳价时间序列及特征（欧元/吨CO2）
    - 趋势 + 季节性 + 噪音
    - 额外特征：天然气价格（模拟）、煤炭价格（模拟）、波动率、成交量
    """
    np.random.seed(seed)
    dates = pd.date_range(start='2020-01-01', periods=n, freq='D')
    t = np.arange(n)
    # 趋势 + 正弦季节（年度周期） + 随机游走 + 噪声
    trend = 0.02 * t
    seasonal = 5 * np.sin(2 * np.pi * t / 365)
    random_walk = np.cumsum(np.random.randn(n) * 0.5)
    noise = np.random.randn(n) * 1.0
    price = 40 + trend + seasonal + random_walk + noise
    price = np.clip(price, 10, 100)  # 碳价合理范围

    df = pd.DataFrame({'price': price}, index=dates)
    # 添加模拟外部特征
    df['gas_price'] = 20 + 5 * np.sin(2*np.pi * t/180) + np.random.randn(n)*1.5
    df['coal_price'] = 60 + 10 * np.cos(2*np.pi * t/365) + np.random.randn(n)*3
    df['volatility'] = df['price'].pct_change().rolling(10).std().fillna(0)
    df['volume'] = 1000 + 200 * np.sin(2*np.pi * t/30) + np.random.poisson(50, n)
    return df

# 获取数据
df = generate_synthetic_carbon_price(n=1500)
print("数据预览：")
print(df.head())
print(f"数据范围：{df.index[0]} 至 {df.index[-1]}")

# ------------------------------------------------------------
# 2. 特征工程
# ------------------------------------------------------------
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    创建时序特征和滞后特征
    """
    data = df.copy()
    # 滞后特征
    for lag in [1, 2, 3, 7]:
        data[f'price_lag_{lag}'] = data['price'].shift(lag)
    # 滚动统计
    for window in [5, 10, 20]:
        data[f'price_ma_{window}'] = data['price'].rolling(window).mean()
        data[f'price_std_{window}'] = data['price'].rolling(window).std()
    # 外部特征的滞后
    for col in ['gas_price', 'coal_price']:
        data[f'{col}_lag1'] = data[col].shift(1)
    # 时间特征
    data['dayofweek'] = data.index.dayofweek
    data['month'] = data.index.month
    data['quarter'] = data.index.quarter
    return data

df_feat = create_features(df)
# 丢弃含有NaN的行
df_feat = df_feat.dropna()
print(f"特征工程后数据形状: {df_feat.shape}")

# ------------------------------------------------------------
# 3. 划分训练集和测试集（按时间顺序）
# ------------------------------------------------------------
train_size = int(len(df_feat) * 0.8)
train_df = df_feat.iloc[:train_size]
test_df = df_feat.iloc[train_size:]

X_cols = [c for c in train_df.columns if c != 'price']
y_col = 'price'

X_train_raw = train_df[X_cols].values
y_train_raw = train_df[y_col].values.reshape(-1, 1)
X_test_raw = test_df[X_cols].values
y_test_raw = test_df[y_col].values.reshape(-1, 1)

# 标准化
scaler_X = StandardScaler()
scaler_y = StandardScaler()
X_train_scaled = scaler_X.fit_transform(X_train_raw)
X_test_scaled = scaler_X.transform(X_test_raw)
y_train_scaled = scaler_y.fit_transform(y_train_raw).ravel()
y_test_scaled = scaler_y.transform(y_test_raw).ravel()

# ------------------------------------------------------------
# 4. 构建LSTM数据（需要滑动窗口形成3D序列）
# ------------------------------------------------------------
def create_sequences(
    X: np.ndarray,
    y: np.ndarray,
    window: int = 10
) -> Tuple[np.ndarray, np.ndarray]:
    """
    将特征矩阵转换为LSTM所需的 [samples, timesteps, features] 格式
    """
    X_seq, y_seq = [], []
    for i in range(window, len(X)):
        X_seq.append(X[i-window:i, :])
        y_seq.append(y[i])
    return np.array(X_seq), np.array(y_seq)

WINDOW = 10
X_train_seq, y_train_seq = create_sequences(X_train_scaled, y_train_scaled, WINDOW)
X_test_seq, y_test_seq = create_sequences(X_test_scaled, y_test_scaled, WINDOW)
n_features = X_train_seq.shape[2]
print(f"LSTM输入形状: X_train_seq {X_train_seq.shape}, y_train_seq {y_train_seq.shape}")

# ------------------------------------------------------------
# 5. 训练LSTM模型
# ------------------------------------------------------------
lstm_model = Sequential([
    LSTM(64, activation='tanh', return_sequences=True, input_shape=(WINDOW, n_features)),
    Dropout(0.2),
    LSTM(32, activation='tanh', return_sequences=False),
    Dropout(0.2),
    Dense(16, activation='relu'),
    Dense(1)
])
lstm_model.compile(optimizer='adam', loss='mse', metrics=['mae'])
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = lstm_model.fit(
    X_train_seq, y_train_seq,
    validation_data=(X_test_seq, y_test_seq),
    epochs=50,
    batch_size=32,
    callbacks=[early_stop],
    verbose=1
)

# 得到LSTM预测（训练集和测试集）
y_train_pred_lstm_scaled = lstm_model.predict(X_train_seq, verbose=0).ravel()
y_test_pred_lstm_scaled = lstm_model.predict(X_test_seq, verbose=0).ravel()

# 反标准化LSTM预测
y_train_pred_lstm = scaler_y.inverse_transform(y_train_pred_lstm_scaled.reshape(-1,1)).ravel()
y_test_pred_lstm = scaler_y.inverse_transform(y_test_pred_lstm_scaled.reshape(-1,1)).ravel()

print(f"LSTM训练集MAE: {mean_absolute_error(scaler_y.inverse_transform(y_train_seq.reshape(-1,1)).ravel(), y_train_pred_lstm):.2f}")
print(f"LSTM测试集MAE: {mean_absolute_error(scaler_y.inverse_transform(y_test_seq.reshape(-1,1)).ravel(), y_test_pred_lstm):.2f}")

# ------------------------------------------------------------
# 6. 构建XGBoost模型（使用原始特征 + LSTM预测值作为额外特征）
# ------------------------------------------------------------
# 注意：为确保特征对齐，XGBoost使用与LSTM窗口对应的时间点
# 由于LSTM窗口导致前WINDOW个样本丢失，XGBoost也使用对应的样本
# 但XGBoost的原始特征需要与LSTM输出对齐（去掉前WINDOW个样本）
X_train_xgb = X_train_scaled[WINDOW:]   # 与LSTM序列对齐
y_train_xgb = y_train_scaled[WINDOW:]   # 真实值（标准化）
X_test_xgb = X_test_scaled[WINDOW:]     # 与LSTM序列对齐
y_test_xgb = y_test_scaled[WINDOW:]     # 真实值（标准化）

# 拼接LSTM预测值作为新特征
X_train_xgb_aug = np.column_stack([X_train_xgb, y_train_pred_lstm_scaled])
X_test_xgb_aug = np.column_stack([X_test_xgb, y_test_pred_lstm_scaled])

# 训练XGBoost
xgb_model = XGBRegressor(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    verbosity=0
)
xgb_model.fit(
    X_train_xgb_aug, y_train_xgb,
    eval_set=[(X_train_xgb_aug, y_train_xgb), (X_test_xgb_aug, y_test_xgb)],
    verbose=False
)

# ------------------------------------------------------------
# 7. 预测与评估
# ------------------------------------------------------------
y_pred_train_scaled = xgb_model.predict(X_train_xgb_aug)
y_pred_test_scaled = xgb_model.predict(X_test_xgb_aug)

# 反标准化
y_train_true = scaler_y.inverse_transform(y_train_xgb.reshape(-1, 1)).ravel()
y_test_true = scaler_y.inverse_transform(y_test_xgb.reshape(-1, 1)).ravel()
y_pred_train = scaler_y.inverse_transform(y_pred_train_scaled.reshape(-1, 1)).ravel()
y_pred_test = scaler_y.inverse_transform(y_pred_test_scaled.reshape(-1, 1)).ravel()

# 计算指标
def evaluate(y_true: np.ndarray, y_pred: np.ndarray, name: str) -> None:
    """打印评估指标"""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"[{name}] RMSE: {rmse:.2f}, MAE: {mae:.2f}, R2: {r2:.4f}")

