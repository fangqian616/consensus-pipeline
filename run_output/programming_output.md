好的，作为一名能源经济学机器学习领域的技术专家，我将基于您提供的论文列表和我的专业知识，为您完成三大任务。我将以中文、Markdown格式输出。

---

### 任务1：技术选型分析

在能源经济学，特别是碳价预测领域，不同的机器学习模型有其独特的优势和适用场景。以下是对您提出的四种方案的对比分析及选型建议。

| 方案名称 | 适用场景 | 成熟度评级 | 推荐理由 |
| :--- | :--- | :--- | :--- |
| **LSTM/GRU** | 纯时间序列预测、捕捉长期依赖关系、数据具有明显时序模式。 | ★★★★★ | **成熟度高**，是时间序列预测的经典深度学习模型。GRU作为LSTM的简化变体，计算效率更高。其“门控”机制能有效处理碳价序列中的记忆效应和趋势。但需要足够的时序数据量，且对特征工程依赖相对较低。 |
| **XGBoost/LightGBM** | 特征驱动预测、高维特征空间、需要模型可解释性（特征重要性）、数据包含大量结构性特征（如宏观经济指标、天气、政策变量）。 | ★★★★★ | **成熟度极高**，是Kaggle等竞赛中的常胜将军。在处理表格型数据、非线性关系和特征交互方面表现优异。LightGBM相比XGBoost训练速度更快，内存占用更小。在碳价预测中，如果大量外部影响因素（如能源价格、股票指数、政策事件）被量化，该方案优势巨大。缺点是缺乏对时间序列长期依赖的显式建模。 |
| **Transformer** | 长序列建模、捕捉序列中的远距离依赖关系、多变量时间序列预测。 | ★★★★☆ | 近年来最先进的序列模型。多头自注意力机制能同时关注序列中任意位置的信息，理论上在处理长期交互方面优于LSTM。但**成熟度相对较低**，对数据量和计算资源要求高，训练不稳定，在小数据集上容易过拟合。在碳价预测中，除非数据量极大，否则其优势可能不如LSTM，且有被更高效的Informer、Autoformer等变体取代的趋势。 |
| **混合模型 (CNN-LSTM, Attention-XGBoost等)** | 充分利用不同模型的优势、应对复杂时间序列+特征工程问题、追求更高预测精度。 | ★★★★☆ | **为解决单一模型瓶颈而设计的范本**。`CNN-LSTM`: CNN提取局部特征（如短期波动模式），LSTM处理长序列依赖。`Attention-XGBoost`: 用注意力机制为时间步或特征动态加权，再送入XGBoost进行稳健预测。`LSTM+XGBoost`: (本项目推荐) LSTM提取时序深层特征，XGBoost作为强学习器进行最终预测或特征组合。**成熟度中等**，但效果往往最好，是工程实践中的优选。 |

**选型建议**：

1.  **初级或快速原型**：推荐 **XGBoost/LightGBM**。它们上手快、效果稳定、可解释性强，是建立基准模型的绝佳选择。
2.  **专注时间序列动态**：推荐 **LSTM/GRU**。如果数据量充足（例如每日或每小时数据），且主要依赖历史碳价本身进行预测，LSTM是核心模型。
3.  **追求极致精度与鲁棒性**：**强烈推荐使用混合模型**，特别是 **LSTM + XGBoost**。`LSTM`负责从复杂的时间序列中提取深层特征（如潜在趋势、周期），而`XGBoost`则利用这些特征和原始特征进行更稳健的预测，这正是本代码所实践的。

### 任务2：碳价预测完整代码（LSTM + XGBoost混合模型）

以下是一个完整的、可直接运行的Python项目。由于公开的欧盟碳配额(EUA)期货数据通常来自金融数据提供商（如Wind, Refinitiv），本例将使用一个**模拟数据集**（可以认为是真实数据的典型形态）来演示完整流程，并在注释中说明如何替换为真实数据源（如Yahoo Finance或Investing.com的EOD数据）。代码包含丰富的中文注释和类型注解。

```python
"""
项目：基于LSTM+XGBoost混合模型的碳价预测
作者：AI能源经济专家
功能：
    1. 从模拟数据（或真实CSV）加载碳价数据。
    2. 进行数据预处理和特征工程。
    3. 使用LSTM模型提取时间序列深层特征。
    4. 使用XGBoost模型进行最终预测。
    5. 评估模型性能（MSE, MAE, R²）。
依赖：pip install numpy pandas scikit-learn tensorflow keras xgboost matplotlib
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping
from xgboost import XGBRegressor
import warnings
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')

# 设置随机种子以保证可复现
np.random.seed(42)

# ----------------------------------------------
# 1. 数据加载与预处理 (Data Loading & Preprocessing)
# ----------------------------------------------

def generate_synthetic_carbon_price_data(
    n_points: int = 1000,
    start_price: float = 50.0,
    noise_level: float = 1.0
) -> pd.DataFrame:
    """
    生成模拟的碳价时间序列数据。
    实际应用中，请用 pd.read_csv('carbon_prices.csv') 替代。
    模拟数据包含：日期（假设为每日）、Close（收盘价）、Volume（成交量）、
    以及几个外部特征：天然气价格 (NatGas)、煤炭价格 (Coal)、
    欧盟股票指数 (EU_Stock)。
    """
    dates = pd.date_range(start='2020-01-01', periods=n_points, freq='D')
    
    # 生成一个带趋势和周期性的随机游走收盘价
    trend = np.linspace(0, 15, n_points)
    seasonality = 5 * np.sin(np.linspace(0, 20 * np.pi, n_points))
    random_walk = np.cumsum(np.random.randn(n_points) * noise_level)
    close_prices = start_price + trend + seasonality + random_walk
    close_prices = np.maximum(close_prices, 10)  # 限制最低价
    
    # 生成外部特征
    nat_gas = close_prices * 0.8 + np.random.randn(n_points) * 2
    coal = close_prices * 0.5 + np.random.randn(n_points) * 3
    eu_stock = close_prices * 0.1 + 3000 + np.random.randn(n_points) * 50
    
    df = pd.DataFrame({
        'Date': dates,
        'Close': close_prices,
        'Volume': np.random.randint(1000, 10000, n_points),
        'NatGas': nat_gas,
        'Coal': coal,
        'EU_Stock': eu_stock
    })
    return df

def create_sequences(
    data: np.ndarray,
    seq_length: int = 10
) -> Tuple[np.ndarray, np.ndarray]:
    """
    将时间序列数据转换为监督学习所需的序列格式。
    :param data: 形状 (n_samples, n_features)
    :param seq_length: 用于预测的时间步长（窗口大小）
    :return: X (n_samples-seq_length, seq_length, n_features),
             y (n_samples-seq_length, 1)
    """
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i:i + seq_length, :])  # 输入序列
        ys.append(data[i + seq_length, 0])     # 预测下一个时间步的Close价格
    return np.array(xs), np.array(ys)

def load_and_preprocess_data(
    filepath: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler, np.ndarray, np.ndarray, MinMaxScaler]:
    """
    数据加载与预处理主函数。
    返回用于LSTM训练的X_train/y_train/输入scalar，以及原始y的scalar。
    """
    # 加载数据 (模拟或真实)
    if filepath:
        df = pd.read_csv(filepath, parse_dates=['Date'])
    else:
        df = generate_synthetic_carbon_price_data()
    
    print(f"数据形状: {df.shape}")
    print(f"时间范围: {df['Date'].min()} 至 {df['Date'].max()}")
    
    # ---------- 特征工程 ----------
    # 1. 时间特征衍生
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    
    # 2. 历史特征（滞后特征）
    df['Close_Lag1'] = df['Close'].shift(1)
    df['Close_Lag3'] = df['Close'].shift(3)
    df['Close_MA5'] = df['Close'].rolling(window=5).mean()
    df['Volume_Lag1'] = df['Volume'].shift(1)
    
    # 3. 外部特征变化率
    df['NatGas_Change'] = df['NatGas'].pct_change()
    df['Coal_Change'] = df['Coal'].pct_change()
    df['EU_Stock_Change'] = df['EU_Stock'].pct_change()
    
    # 4. 去掉NaN值
    df = df.dropna().reset_index(drop=True)
    
    # 选择用于建模的特征列
    feature_cols = [
        'Close', 'Volume', 'NatGas', 'Coal', 'EU_Stock',
        'Year', 'Month', 'DayOfWeek',
        'Close_Lag1', 'Close_Lag3', 'Close_MA5', 'Volume_Lag1',
        'NatGas_Change', 'Coal_Change', 'EU_Stock_Change'
    ]
    
    data = df[feature_cols].values
    
    # ---------- 数据归一化 ----------
    # 两个Scaler: 一个用于所有特征（LSTM输入），一个仅用于预测目标Close（便于反归一化）
    scaler_features = MinMaxScaler(feature_range=(0, 1))
    scaler_target = MinMaxScaler(feature_range=(0, 1))
    
    # 对目标（Close）单独拟合
    scaler_target.fit(data[:, 0].reshape(-1, 1))
    # 对所有特征进行归一化
    scaled_data = scaler_features.fit_transform(data)
    
    # ---------- 创建时间序列样本 ----------
    seq_length = 20  # 使用过去20天的数据预测下一天
    X, y = create_sequences(scaled_data, seq_length)
    
    # 执行训练/测试划分 (时间序列必须按时间顺序划分)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # 注意: y_train, y_test 现在是归一化后的值（因为scaled_data中的第一列是归一化后的Close）
    # 我们需要将其值保持在0-1之间，但为了后续反归一化评估，应将y也进行目标缩放
    # 实际上y已经是归一化的，这是因为scaler_target拟合的是原始Close，但在scaled_data中第一列用了不同的scaler
    # 更严谨的做法是：在scaled_data中，第一列也使用scaler_features，但y使用scaler_target单独处理
    # 为简化，这里我们重新计算：实际目标是原始的Close值，我们需要对y做单独缩放。
    
    # 重新提取原始Close值进行单独缩放
    raw_close = data[:, 0]  # 原始Close (第0列)
    _, y_raw = create_sequences(np.column_stack([raw_close, np.zeros_like(raw_close)]), seq_length)
    y_raw = y_raw.reshape(-1, 1)  # 原始未缩放的Close目标值
    
    # 对y_raw进行缩放
    y_scaled = scaler_target.transform(y_raw)
    
    # 重新划分y_scaled
    y_train_scaled = y_scaled[:split_idx].flatten()
    y_test_scaled = y_scaled[split_idx:].flatten()
    
    # y_train_scaled, y_test_scaled 是归一化后的目标值
    # X_train, X_test 是归一化后的特征
    
    print(f"训练样本数: {X_train.shape[0]}, 测试样本数: {X_test.shape[0]}")
    print(f"输入形状: {X_train.shape[1:]} (时间步, 特征数)")
    
    return (X_train, y_train_scaled, X_test, y_test_scaled, 
            scaler_features, scaler_target, df, seq_length, feature_cols)


# ----------------------------------------------
# 2. LSTM模型构建与训练 (LSTM Model)
# ----------------------------------------------

def build_lstm_model(
    input_shape: Tuple[int, int],
    units: int = 64,
    dropout_rate: float = 0.2
) -> Model:
    """
    构建LSTM特征提取模型。
    :param input_shape: (时间步, 特征数)
    :param units: LSTM神经元数量
    :param dropout_rate: Dropout比例，防止过拟合
    :return: Keras模型
    """
    model = Sequential([
        LSTM(units=units, return_sequences=False, input_shape=input_shape),
        Dropout(dropout_rate),
        Dense(units // 2, activation='relu'),
        Dropout(dropout_rate),
        Dense(1)  # 输出层，预测未来一个时间步
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

# ----------------------------------------------
# 3. 混合模型训练流水线 (Hybrid Pipeline)
# ----------------------------------------------

class HybridLSTMXGBoostPredictor:
    """
    LSTM + XGBoost 混合预测器。
    LSTM负责从时间序列中提取深层特征（LSTM层输出向量），
    XGBoost则将这些特征与部分原始统计特征结合，进行最终预测。
    """
    
    def __init__(
        self,
        lstm_units: int = 64,
        lstm_epochs: int = 50,
        lstm_batch_size: int = 32,
        xgb_params: Optional[dict] = None
    ):
        self.lstm_units = lstm_units
        self.lstm_epochs = lstm_epochs
        self.lstm_batch_size = lstm_batch_size
        self.xgb_params = xgb_params or {
            'n_estimators': 200,
            'max_depth': 6,
            '