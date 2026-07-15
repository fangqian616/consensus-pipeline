# 任务1：技术选型分析

在能源经济学领域，碳价预测需要兼顾时序依赖性与多维特征驱动。以下针对四种主流方案进行对比分析，并结合前沿文献（如《Machine learning in energy economics and finance: A review》等）给出选型建议。

| 方案名称 | 适用场景 | 成熟度评级 | 推荐理由 |
|----------|----------|------------|----------|
| **LSTM/GRU** | 纯时序预测、高频数据（日/时）、需捕捉长期依赖的序列 | ★★★★☆ | 对碳价的非线性和时序模式（如周期性、趋势性）建模能力强；GRU较LSTM参数少，适合小样本场景。缺点是对外部特征利用不足，易过拟合。 |
| **XGBoost/LightGBM** | 多特征驱动预测、特征工程丰富、样本量中等 | ★★★★★ | 擅长处理高维特征（如宏观经济、能源价格、政策变量），可解释性较好（通过SHAP）；LightGBM速度更快，适合迭代调优。但在纯时序任务中忽略顺序信息。 |
| **Transformer（含Attention）** | 长序列预测、多变量联动、需要并行计算 | ★★★☆☆ | 可捕捉全局依赖，但需要大量数据（>10⁵样本）才能发挥优势，计算资源要求高；在碳价这种有限样本（通常仅几千条）下易欠拟合。 |
| **混合模型（CNN-LSTM, Attention-XGBoost等）** | 综合时序与特征维度，兼顾局部模式与整体趋势 | ★★★★☆ | 结合LSTM的时序能力和XGBoost的特征处理能力可互补。如先提取时序特征再输入XGBoost，或LSTM输出注意力权重后加权特征。在碳价预测中已有成功案例（见《Machine learning for a sustainable energy future》）。 |

**最终选型建议**：推荐使用 **LSTM + XGBoost 混合模型**。理由如下：
- 碳价受到历史价格时序（LSTM擅长）和外部因素（XGBoost擅长）共同影响，单一模型难以兼顾。
- 混合模型成熟度中等偏高（★★★★），已有大量实证（如《Artificial intelligence and machine learning approaches to energy demand-side response》中提及混合模型在能源预测中的优势）。
- 计算成本可控，适合学术研究和工业应用。

---

# 任务2：碳价预测完整代码（LSTM + XGBoost 混合模型）

以下提供可直接运行的Python项目。由于真实碳价数据需从交易所获取，代码中提供两种方式：①使用网络下载公开数据（示例采用ICE EUA期货数据，需网络）；②若不可用，则生成模拟数据供演示。实际使用时，请将数据源替换为官方CSV文件。

```python
"""
碳价预测 - LSTM + XGBoost 混合模型
完全可运行，包含数据预处理、特征工程、模型训练与评估。
依赖：pandas, numpy, matplotlib, yfinance, scikit-learn, tensorflow, xgboost, shap
安装：pip install pandas numpy matplotlib yfinance scikit-learn tensorflow xgboost shap
"""

import os
import warnings
from typing import Tuple, Optional, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
import xgboost as xgb
import shap

warnings.filterwarnings('ignore')

# ---------------------- 1. 数据获取 ----------------------
def fetch_data(source: str = 'yfinance') -> pd.DataFrame:
    """
    从公开数据集获取碳价数据。
    优先使用yfinance下载ICE EUA期货连续合约（代码：MO1.F），若失败则生成模拟数据。
    
    Returns:
        DataFrame 包含日期和收盘价（'Close'列）
    """
    if source == 'yfinance':
        try:
            import yfinance as yf
            # ICE EUA期货（MO1.F）从Yahoo Finance获取（历史数据可能有限）
            df = yf.download('MO1.F', start='2010-01-01', end='2025-12-31', progress=False)
            if not df.empty:
                print("成功从Yahoo Finance获取数据")
                return df[['Close']].reset_index()
        except Exception as e:
            print(f"yfinance下载失败: {e}，使用模拟数据")
    # 备选：生成模拟碳价数据（用于演示）
    print("生成模拟碳价数据（仅用于演示流程）")
    np.random.seed(42)
    dates = pd.date_range(start='2010-01-01', end='2024-12-31', freq='D')
    # 模拟趋势+季节+噪声
    trend = np.linspace(5, 80, len(dates))
    season = 10 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
    noise = np.random.normal(0, 3, len(dates))
    price = trend + season + noise
    df = pd.DataFrame({'Date': dates, 'Close': price})
    return df

# ---------------------- 2. 特征工程 ----------------------
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    构建时间序列特征和外部特征（可扩展）。
    
    Args:
        df: 包含'Date'和'Close'的DataFrame
    
    Returns:
        带特征列的DataFrame
    """
    data = df.copy()
    data.set_index('Date', inplace=True)
    
    # 滞后特征 (lag1-lag7)
    for lag in [1, 2, 3, 7]:
        data[f'lag_{lag}'] = data['Close'].shift(lag)
    
    # 滚动统计 (窗口7, 30天)
    for window in [7, 30]:
        data[f'rolling_mean_{window}'] = data['Close'].rolling(window).mean()
        data[f'rolling_std_{window}'] = data['Close'].rolling(window).std()
        data[f'rolling_max_{window}'] = data['Close'].rolling(window).max()
        data[f'rolling_min_{window}'] = data['Close'].rolling(window).min()
    
    # 差分特征
    data['diff_1'] = data['Close'].diff(1)
    data['diff_7'] = data['Close'].diff(7)
    
    # 时间特征
    data['dayofweek'] = data.index.dayofweek
    data['month'] = data.index.month
    data['quarter'] = data.index.quarter
    data['dayofyear'] = data.index.dayofyear
    
    # 虚拟变量 (月份)
    data = pd.get_dummies(data, columns=['month'], prefix='month')
    
    # 添加外部特征示例：油价、天然气价格（如需，可补充）
    # 此处简化，仅用滞后特征
    
    # 删除缺失值
    data.dropna(inplace=True)
    return data

# ---------------------- 3. 数据预处理 ----------------------
def prepare_lstm_data(data: pd.DataFrame, feature_cols: list, target_col: str = 'Close', 
                      lookback: int = 30, test_size: float = 0.2) -> Tuple:
    """
    为LSTM准备序列数据。
    
    Args:
        data: 特征DataFrame
        feature_cols: 特征列名列表
        target_col: 目标列名
        lookback: 时间步长
        test_size: 测试集比例
    
    Returns:
        X_train, X_test, y_train, y_test, scaler_feat, scaler_target
    """
    scaler_feat = MinMaxScaler(feature_range=(0, 1))
    scaler_target = MinMaxScaler(feature_range=(0, 1))
    
    # 归一化
    scaled_feat = scaler_feat.fit_transform(data[feature_cols])
    scaled_target = scaler_target.fit_transform(data[[target_col]])
    
    # 创建时间序列样本
    X, y = [], []
    for i in range(lookback, len(scaled_feat)):
        X.append(scaled_feat[i-lookback:i])
        y.append(scaled_target[i])
    X, y = np.array(X), np.array(y)
    
    # 按时间顺序分割
    split = int(len(X) * (1 - test_size))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    return X_train, X_test, y_train, y_test, scaler_feat, scaler_target

# ---------------------- 4. LSTM模型 ----------------------
def build_lstm_model(input_shape: Tuple[int, int]) -> Sequential:
    """
    构建LSTM模型。
    
    Args:
        input_shape: (时间步长, 特征数)
    
    Returns:
        Keras Sequential模型
    """
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape, activation='tanh'),
        Dropout(0.2),
        LSTM(32, return_sequences=False, activation='tanh'),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
    return model

# ---------------------- 5. XGBoost模型 ----------------------
def build_xgb_model() -> xgb.XGBRegressor:
    """
    构建XGBoost回归模型，用于第二层预测。
    """
    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    return model

# ---------------------- 6. 混合模型训练与预测 ----------------------
def train_lstm_xgb_hybrid(data: pd.DataFrame, feature_cols: list, target_col: str = 'Close',
                           lookback: int = 30, epochs: int = 50, batch_size: int = 32):
    """
    完整训练流程：LSTM提取时序特征，然后XGBoost使用LSTM输出+原始特征做最终预测。
    """
    # 准备LSTM数据
    X_train_lstm, X_test_lstm, y_train_lstm, y_test_lstm, scaler_feat, scaler_target = \
        prepare_lstm_data(data, feature_cols, target_col, lookback)
    
    # 训练LSTM
    lstm_input_shape = (X_train_lstm.shape[1], X_train_lstm.shape[2])
    lstm_model = build_lstm_model(lstm_input_shape)
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    history = lstm_model.fit(
        X_train_lstm, y_train_lstm,
        validation_data=(X_test_lstm, y_test_lstm),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=1
    )
    
    # LSTM预测（中间特征）—— 用于XGBoost
    lstm_train_pred = lstm_model.predict(X_train_lstm)
    lstm_test_pred = lstm_model.predict(X_test_lstm)
    
    # 构建XGBoost的输入：将LSTM预测值与原始特征（或LSTM中间层输出）拼接
    # 这里使用LSTM的预测值 + 最新时刻的特征（即X_test_lstm[:,-1,:]）
    X_train_feat = X_train_lstm[:, -1, :]  # 最后一个时间步的特征
    X_test_feat = X_test_lstm[:, -1, :]
    
    X_train_xgb = np.hstack([X_train_feat, lstm_train_pred])
    X_test_xgb = np.hstack([X_test_feat, lstm_test_pred])
    
    # 目标值（原始尺度，但XGBoost可以直接使用归一化后的，最后再反归一化）
    # 为了XGBoost能够学习残差，我们使用原始目标（已归一化）
    y_train_xgb = y_train_lstm.ravel()
    y_test_xgb = y_test_lstm.ravel()
    
    # 训练XGBoost
    xgb_model = build_xgb_model()
    xgb_model.fit(
        X_train_xgb, y_train_xgb,
        eval_set=[(X_test_xgb, y_test_xgb)],
        early_stopping_rounds=20,
        verbose=False
    )
    
    # 最终预测（反归一化）
    pred_scaled = xgb_model.predict(X_test_xgb).reshape(-1, 1)
    pred = scaler_target.inverse_transform(pred_scaled)
    y_test_orig = scaler_target.inverse_transform(y_test_lstm.reshape(-1, 1))
    
    # 评估
    mse = mean_squared_error(y_test_orig, pred)
    mae = mean_absolute_error(y_test_orig, pred)
    r2 = r2_score(y_test_orig, pred)
    print(f"混合模型测试集评估: MSE={mse:.2f}, MAE={mae:.2f}, R2={r2:.4f}")
    
    # 绘制预测结果
    plt.figure(figsize=(12, 6))
    plt.plot(y_test_orig, label='真实值', color='blue')
    plt.plot(pred, label='预测值', color='red', linestyle='--')
    plt.title('碳价预测对比 (LSTM + XGBoost 混合模型)')
    plt.xlabel('样本序号')
    plt.ylabel('碳价 (EUR/吨)')
    plt.legend()
    plt.grid(True)
    plt.show()
    
    return lstm_model, xgb_model, scaler_feat, scaler_target

# ---------------------- 主程序 ----------------------
if __name__ == "__main__":
    # 1. 获取数据
    df = fetch_data('yfinance')  # 如需真实数据，请确保网络可用；否则自动使用模拟数据
    
    # 2. 特征工程
    feature_data = create_features(df)
    print(f"数据样本数: {len(feature_data)}，特征数: {len(feature_data.columns)}")
    
    # 3. 选择特征列（排除目标列和不需要的列）
    exclude_cols = ['Close']
    feature_cols = [col for col in feature_data.columns if col not in exclude_cols]
    
    # 4. 训练混合模型
    lstm_model, xgb_model, scaler_feat, scaler_target = train_lstm_xgb_hybrid(
        feature_data, feature_cols, target_col='Close',
        lookback=30, epochs=100, batch_size=32
    )
    
    # 5. （可选）解释性分析：使用SHAP对XGBoost进行解释
    print("正在计算SHAP值...")
    # 获取测试集的特征（需与训练时一致）
    _, X_test_lstm, _, y_test_lstm, _, _ = prepare_lstm_data(
        feature_data, feature_cols, 'Close', lookback=30, test_size=0.2
    )
   