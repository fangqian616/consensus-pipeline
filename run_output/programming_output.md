好的，以下我将以能源经济学机器学习领域技术专家的身份，系统性地完成您提出的三大任务。所有输出均为中文，格式为Markdown。

---

# 任务1：技术选型分析

在能源经济学（尤其是碳价预测）场景下，不同机器学习模型在时序建模、特征捕捉、非线性和多因素交互方面各有利弊。下表对常用方案进行对比分析。

| 方案名称 | 适用场景 | 成熟度评级 | 推荐理由 |
|---------|---------|-----------|---------|
| **LSTM / GRU** | 纯时序预测，利用历史价格自身规律，适合中长期碳价趋势捕捉 | ★★★★☆ | 擅长捕捉长期依赖，对非平稳时序有较好建模能力；成熟度高，Keras/TensorFlow支持完善；但需较多数据且对超参数敏感 |
| **XGBoost / LightGBM** | 特征驱动预测，当有丰富的经济、能源、政策等外生特征（如原油、天然气、气温、宏观经济指标）时表现优异 | ★★★★★ | 处理混合类型特征、缺失值、对异常值鲁棒；训练快可调参；在Kaggle等竞赛中证明效果；但需高质量特征工程 |
| **Transformer（注意力机制）** | 长序列建模，捕捉多变量间复杂依赖，适合高频碳价或波动性预测 | ★★★☆☆ | 理论上能处理任意长度依赖，但数据量需求大（通常需数万样本），训练成本高；在碳价小样本场景下易过拟合，成熟度相对低 |
| **混合模型（CNN-LSTM, Attention-XGBoost等）** | 同时利用时序模式和特征驱动信号，综合提升预测稳定性和准确率 | ★★★★☆ | 取长补短：CNN提取局部模式，LSTM捕捉长期依赖，XGBoost提升非线性拟合；适合碳价这类受多因素驱动且具有周期性的复杂系统 |

**选型建议**：
- **若数据特征丰富（能源价格、政策事件等）**：优先采用 **XGBoost/LightGBM** 或 **混合模型**。
- **若仅有时序价格数据（如碳配额期货合约）**：选用 **LSTM/GRU** 作为基线，后续可尝试叠加注意力。
- **若追求可解释性与工业部署稳定性**：首选 **LightGBM**。
- **若希望发表高水平论文或探索前沿**：可尝试 **Transformer** + 因果发现（参考论文“Toward Causal Representation Learning”）。

综合碳价预测典型场景（特征多、数据量中等、对可解释性有一定要求），我推荐 **LSTM + XGBoost 混合模型**，既能利用时序规律，又能融合多种驱动因素。

---

# 任务2：碳价预测完整代码

以下代码实现了一个可直接运行的 **LSTM + XGBoost 混合碳价预测项目**。项目流程：
1. 模拟生成公开数据（可替换为真实API数据）。
2. 数据预处理与特征工程（滞后、滑动统计、技术指标）。
3. 构建LSTM模型提取时序特征。
4. 将LSTM输出作为新特征与原始特征拼接，训练XGBoost。
5. 预测评估（RMSE, MAE, R²）。

```python
"""
碳价预测混合模型：LSTM + XGBoost
依赖：pip install numpy pandas xgboost tensorflow scikit-learn matplotlib joblib
（若无法使用模拟数据，可替换为真实API，详见注释）
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Any
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from xgboost import XGBRegressor
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# 设置随机种子，保证可重复性
np.random.seed(42)

# ──────────────────────────────────────────────
# 1. 生成模拟碳价数据（可替换为真实数据）
# ──────────────────────────────────────────────
def generate_synthetic_carbon_data(n_samples: int = 1500) -> pd.DataFrame:
    """
    生成包含碳价、原油价格、天然气价格、气温、工业指数的模拟数据集。
    Returns:
        DataFrame: 列包括 'date', 'carbon_price', 'crude_oil', 'natural_gas', 
                   'temperature', 'industrial_index'
    """
    dates = pd.date_range(start='2018-01-01', periods=n_samples, freq='D')
    np.random.seed(42)
    # 模拟碳价（均值30，带趋势和季节性）
    t = np.arange(n_samples)
    trend = 0.01 * t + 20
    seasonal = 5 * np.sin(2 * np.pi * t / 365)
    noise = np.random.normal(0, 2, n_samples)
    carbon_price = trend + seasonal + noise

    # 辅助特征（与碳价相关）
    crude_oil = 60 + 10 * np.sin(2 * np.pi * t / 365) + np.random.normal(0, 3, n_samples)
    natural_gas = 3 + 0.5 * np.sin(2 * np.pi * t / 180) + np.random.normal(0, 0.5, n_samples)
    temperature = 15 + 10 * np.sin(2 * np.pi * (t - 15) / 365) + np.random.normal(0, 2, n_samples)
    industrial_index = 100 + 0.02 * t + np.random.normal(0, 5, n_samples)

    df = pd.DataFrame({
        'date': dates,
        'carbon_price': carbon_price,
        'crude_oil': crude_oil,
        'natural_gas': natural_gas,
        'temperature': temperature,
        'industrial_index': industrial_index
    })
    df.set_index('date', inplace=True)
    return df

# ──────────────────────────────────────────────
# 2. 特征工程
# ──────────────────────────────────────────────
def create_features(df: pd.DataFrame, lag_days: int = 5, window_size: int = 7) -> pd.DataFrame:
    """
    创建时序特征：
    - 滞后特征（lag）
    - 滑动统计（均值、标准差）
    - 技术指标（RSI）
    Args:
        df: 原始数据框（必须包含 'carbon_price' 列）
        lag_days: 滞后天数
        window_size: 滑动窗口大小
    Returns:
        添加了特征列的数据框（丢弃NaN后）
    """
    df = df.copy()
    target = 'carbon_price'
    # 滞后特征
    for lag in range(1, lag_days + 1):
        df[f'lag_{lag}'] = df[target].shift(lag)
        df[f'crude_lag_{lag}'] = df['crude_oil'].shift(lag)
        df[f'gas_lag_{lag}'] = df['natural_gas'].shift(lag)
    # 滑动统计
    df[f'price_roll_mean_{window_size}'] = df[target].rolling(window=window_size).mean().shift(1)
    df[f'price_roll_std_{window_size}'] = df[target].rolling(window=window_size).std().shift(1)
    df[f'vol_roll_mean_{window_size}'] = df['crude_oil'].rolling(window=window_size).mean().shift(1)
    # RSI (相对强弱指标)
    delta = df[target].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    # 丢弃NaN
    df.dropna(inplace=True)
    return df

# ──────────────────────────────────────────────
# 3. 数据准备（训练/测试分割，缩放）
# ──────────────────────────────────────────────
def prepare_data(df: pd.DataFrame, test_ratio: float = 0.2,
                 lstm_seq_len: int = 10) -> dict:
    """
    将数据分割为训练/测试集，并进行标准化（Min-Max）。
    返回字典包含：
        X_train, y_train, X_test, y_test (原始缩放)
        scaler_y, scaler_X
        X_train_lstm, X_test_lstm (用于LSTM的三维序列)
        feature_columns
    """
    feature_cols = [c for c in df.columns if c != 'carbon_price']
    target_col = 'carbon_price'

    # 先缩放所有特征和目标
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    X_scaled = scaler_X.fit_transform(df[feature_cols])
    y_scaled = scaler_y.fit_transform(df[[target_col]]).flatten()

    # 时序分割（不能随机打乱）
    split_idx = int(len(df) * (1 - test_ratio))
    X_train_scaled = X_scaled[:split_idx]
    y_train_scaled = y_scaled[:split_idx]
    X_test_scaled = X_scaled[split_idx:]
    y_test_scaled = y_scaled[split_idx:]

    # 构建LSTM需要的序列数据（滑动窗口）
    def create_sequences(X: np.ndarray, y: np.ndarray, seq_len: int) -> Tuple[np.ndarray, np.ndarray]:
        X_seq, y_seq = [], []
        for i in range(seq_len, len(X)):
            X_seq.append(X[i - seq_len:i, :])  # (seq_len, n_features)
            y_seq.append(y[i])
        return np.array(X_seq), np.array(y_seq)

    X_train_lstm, y_train_lstm = create_sequences(X_train_scaled, y_train_scaled, lstm_seq_len)
    X_test_lstm, y_test_lstm = create_sequences(X_test_scaled, y_test_scaled, lstm_seq_len)

    # 对齐XGBoost的标签（从序列最后一天取特征）
    X_train_xgb = X_train_scaled[lstm_seq_len:]  # 与LSTM序列的最后一个时间步对齐
    X_test_xgb = X_test_scaled[lstm_seq_len:]
    y_train_xgb = y_train_scaled[lstm_seq_len:]
    y_test_xgb = y_test_scaled[lstm_seq_len:]

    return {
        'X_train_lstm': X_train_lstm,
        'y_train_lstm': y_train_lstm,
        'X_test_lstm': X_test_lstm,
        'y_test_lstm': y_test_lstm,
        'X_train_xgb': X_train_xgb,
        'y_train_xgb': y_train_xgb,
        'X_test_xgb': X_test_xgb,
        'y_test_xgb': y_test_xgb,
        'scaler_y': scaler_y,
        'scaler_X': scaler_X,
        'feature_columns': feature_cols,
        'lstm_seq_len': lstm_seq_len
    }

# ──────────────────────────────────────────────
# 4. 构建LSTM模型
# ──────────────────────────────────────────────
def build_lstm_model(input_shape: Tuple[int, int]) -> Sequential:
    """
    构建单层LSTM + Dropout + Dense回归模型。
    Args:
        input_shape: (timesteps, n_features)
    Returns:
        未编译的Keras模型
    """
    model = Sequential([
        LSTM(50, activation='tanh', return_sequences=False, input_shape=input_shape),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    return model

# ──────────────────────────────────────────────
# 5. 混合模型管道
# ──────────────────────────────────────────────
def train_hybrid_model(data_dict: dict,
                       lstm_epochs: int = 50,
                       lstm_batch_size: int = 32,
                       xgb_params: dict = None) -> Tuple[Any, Any, Any]:
    """
    训练LSTM和XGBoost混合模型。
    - 第一步：训练LSTM，提取序列特征（输出预测作为新特征）
    - 第二步：将LSTM原始输出、残差等作为XGBoost的额外特征
    这里采用简单集成：将LSTM预测值与XGBoost预测值加权平均（可调权重）。
    更复杂的可级联：LSTM hidden state + 原始特征 -> XGBoost。
    为简化，我们使用**堆叠法**：
      1. 用LSTM对训练集做预测，得到 y_pred_lstm_train
      2. 将 y_pred_lstm_train 作为新特征拼接到 X_train_xgb 上
      3. 训练XGBoost
    Returns:
        lstm_model, xgb_model, data_dict (更新后含额外特征)
    """
    # 训练LSTM
    lstm_model = build_lstm_model(
        input_shape=(data_dict['X_train_lstm'].shape[1], data_dict['X_train_lstm'].shape[2])
    )
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    history = lstm_model.fit(
        data_dict['X_train_lstm'], data_dict['y_train_lstm'],
        validation_data=(data_dict['X_test_lstm'], data_dict['y_test_lstm']),
        epochs=lstm_epochs, batch_size=lstm_batch_size,
        callbacks=[early_stop], verbose=0
    )
    # LSTM预测（缩放域）
    lstm_pred_train_scaled = lstm_model.predict(data_dict['X_train_lstm'], verbose=0).flatten()
    lstm_pred_test_scaled = lstm_model.predict(data_dict['X_test_lstm'], verbose=0).flatten()

    # 将LSTM预测作为新特征添加到XGBoost的特征矩阵中
    X_train_xgb_aug = np.column_stack([
        data_dict['X_train_xgb'],
        lstm_pred_train_scaled
    ])
    X_test_xgb_aug = np.column_stack([
        data_dict['X_test_xgb'],
        lstm_pred_test_scaled
    ])

    # 更新data_dict保存增强特征
    data_dict['X_train_xgb_aug'] = X_train_xgb_aug
    data_dict['X_test_xgb_aug'] = X_test_xgb_aug

    # 训练XGBoost
    if xgb_params is None:
        xgb_params = {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
    xgb_model = XGBRegressor(**xgb_params)
    xgb_model.fit(
        X_train_xgb_aug, data_dict['y_train_xgb'],
        eval_set=[(X_test_xgb_aug, data_dict['y_test_xgb'])],
        early_stopping_rounds=10, verbose=0
    )
    return lstm_model, xgb_model, data_dict

# ──────────────────────────────────────────────
# 6. 评估与可视化
# ──────────────────────────────────────────────
def evaluate_model(lstm_model: Sequential, xgb_model: XGBRegressor,
                   data_dict: dict, scaler_y: MinMaxScaler) -> dict:
    """
    反标准化预测值，计算RMSE, MAE, R²，并打印。
    Returns:
        字典包含各项指标
    """
    # LSTM预测
    lstm_pred_train_scaled = lstm_model.predict(data_dict['X_train_lstm'], verbose=0).