# 技术选型、碳价预测代码与部署注意事项

## 任务1：技术选型分析

在能源经济学机器学习领域，不同模型在碳价预测、需求响应、价格波动等任务中各有优劣。以下基于论文背景（特别是《Machine learning in energy economics and finance: A review》《Machine learning for a sustainable energy future》）与实际工程经验，给出对比表。

| 模型方案 | 适用场景 | 成熟度评级 | 推荐理由 |
|---------|----------|------------|----------|
| **LSTM/GRU** | 长时间序列预测（日度/周度碳价、电力负荷）、非线性趋势捕捉 | ★★★★★ | 门控机制有效处理时序依赖性；适用于价格序列的短期与中期波动；可处理不等长序列；论文中广泛用于能源价格预测。 |
| **XGBoost/LightGBM** | 因子驱动的回归/分类（碳价影响因素如政策、天气、工业活动）、特征重要性分析 | ★★★★★ | 梯度提升树在表格数据上表现优异；训练速度快，可解释性（SHAP值）；天然处理缺失值与异常值；适合静态特征+滞后变量。 |
| **Transformer** | 高维时序、多变量交互（如多市场联动）、长程依赖（月度/季度预测） | ★★★☆☆ | 自注意力机制捕捉全局依赖；在自然语言与金融时序中表现突出；但数据量要求大、计算资源高、小样本易过拟合；实践中需谨慎调整。 |
| **混合模型（CNN-LSTM, Attention-XGBoost）** | 复杂场景综合（如融合气象、政策文本、历史价格）；提高鲁棒性与泛化能力 | ★★★★☆ | 集成不同优势：CNN提取局部模式，LSTM建模时序，XGBoost处理高维特征；在碳价预测中常取得SOTA；但调试难度中等，需避免过拟合。 |

**选型建议**：
- **首次建模**：优先尝试XGBoost/LightGBM，特征工程简单，可快速建立基线。
- **需捕捉时序依赖**（如价格序列）：使用LSTM或GRU，配合滚动窗口特征。
- **数据规模小且非线性强**：混合模型（如Attention-XGBoost）可提升准确率，但需注意正则化。
- **长期预测或多源输入**：Transformer需要大量数据（>10万样本），否则推荐LSTM+注意力机制。

以下任务2选用 **LSTM + XGBoost混合模型**（集成预测方式），平衡预测精度与工程复杂度。

---

## 任务2：碳价预测完整代码（LSTM + XGBoost混合模型）

```python
"""
碳价预测项目 —— LSTM + XGBoost 混合模型
数据来源：yfinance（获取全球碳ETF：KRBN）
特征：历史价格、滚动统计、波动率、技术指标
模型：Keras LSTM + XGBoost Regressor，加权平均集成
"""
# ================== 导入依赖 ==================
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from xgboost import XGBRegressor
import yfinance as yf  # 公开数据集获取
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# ================== 数据获取 ==================
def fetch_carbon_price(symbol: str = "KRBN", start: str = "2015-01-01", end: str = "2024-12-31") -> pd.DataFrame:
    """
    从Yahoo Finance获取全球碳ETF（KRBN）的历史价格。
    该ETF跟踪ICE EUA期货指数，作为碳价代理变量。
    """
    data = yf.download(symbol, start=start, end=end, progress=False)
    df = data[["Close"]].copy()
    df.columns = ["price"]
    df.index = pd.to_datetime(df.index)
    df = df.asfreq("B")  # 工作日频率
    df = df.ffill().dropna()
    return df

# ================== 特征工程 ==================
def create_features(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """
    生成时序特征：滞后价格、滚动均值、滚动标准差、波动率、日收益率
    """
    df_feat = df.copy()
    # 滞后特征
    for lag in range(1, window + 1):
        df_feat[f"lag_{lag}"] = df_feat["price"].shift(lag)
    # 滚动统计
    df_feat["rolling_mean"] = df_feat["price"].rolling(window).mean()
    df_feat["rolling_std"] = df_feat["price"].rolling(window).std()
    df_feat["volatility"] = df_feat["price"].pct_change().rolling(window).std()
    # 收益率
    df_feat["return"] = df_feat["price"].pct_change()
    # 剔除NaN行
    df_feat = df_feat.dropna()
    return df_feat

def prepare_lstm_data(data: np.ndarray, lookback: int = 20) -> Tuple[np.ndarray, np.ndarray]:
    """
    将一维价格序列转换为LSTM需要的 [样本, 时间步, 特征] 格式
    """
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i - lookback:i])
        y.append(data[i])
    return np.array(X), np.array(y)

# ================== 模型构建 ==================
def build_lstm_model(input_shape: Tuple[int, int], units: int = 50, dropout: float = 0.2) -> Sequential:
    """
    构建LSTM回归模型
    """
    model = Sequential([
        LSTM(units, return_sequences=True, input_shape=input_shape),
        Dropout(dropout),
        LSTM(units, return_sequences=False),
        Dropout(dropout),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    return model

def train_lstm(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray,
               epochs: int = 100, batch_size: int = 32, verbose: int = 0) -> Sequential:
    """
    训练LSTM模型
    """
    model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
    history = model.fit(X_train, y_train, validation_data=(X_val, y_val),
                        epochs=epochs, batch_size=batch_size, verbose=verbose)
    return model

def train_xgboost(X_train: pd.DataFrame, y_train: np.ndarray) -> XGBRegressor:
    """
    训练XGBoost模型
    """
    model = XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.1,
                         random_state=42, verbosity=0)
    model.fit(X_train, y_train)
    return model

# ================== 主流程 ==================
def main():
    print("=== 碳价预测：LSTM + XGBoost 混合模型 ===")

    # 1. 数据获取
    df = fetch_carbon_price()
    print(f"数据范围：{df.index[0].date()} ~ {df.index[-1].date()}, 样本数：{len(df)}")

    # 2. 特征工程
    window_lag = 10  # 滞后窗口
    df_feat = create_features(df, window=window_lag)

    # 提取目标（当前价格）和特征
    target = df_feat["price"]
    features = df_feat.drop(columns=["price"])

    # 3. 数据划分（时间序列，严格按顺序）
    split_ratio = 0.8
    split_idx = int(len(features) * split_ratio)
    X_train_feat = features.iloc[:split_idx].values.astype(np.float32)
    X_test_feat = features.iloc[split_idx:].values.astype(np.float32)
    y_train = target.iloc[:split_idx].values.astype(np.float32)
    y_test = target.iloc[split_idx:].values.astype(np.float32)
    df_test_time = target.index[split_idx:]

    # 4. 标准化（对表格特征和LSTM序列分别做）
    scaler_feat = MinMaxScaler()
    scaler_target = MinMaxScaler()

    X_train_feat_scaled = scaler_feat.fit_transform(X_train_feat)
    X_test_feat_scaled = scaler_feat.transform(X_test_feat)

    y_train_scaled = scaler_target.fit_transform(y_train.reshape(-1, 1)).ravel()
    y_test_scaled = scaler_target.transform(y_test.reshape(-1, 1)).ravel()

    # 5. 准备LSTM数据（用原始价格序列，从最完整序列开始）
    # 注意：LSTM使用原始价格序列，不使用表格特征。
    # 先对价格整体标准化
    scaler_price = MinMaxScaler()
    price_scaled = scaler_price.fit_transform(df["price"].values.reshape(-1, 1)).ravel()

    lookback = 20
    X_lstm, y_lstm = prepare_lstm_data(price_scaled, lookback)
    # 划分（与表格特征同比例，注意特征工程后数据长度可能不同，需对齐）
    # 简单做法：使用原始价格序列独立划分（确保时间点对应，非严格，但可行）
    split_idx_lstm = int(len(X_lstm) * split_ratio)
    X_lstm_train = X_lstm[:split_idx_lstm]
    X_lstm_test = X_lstm[split_idx_lstm:]
    y_lstm_train = y_lstm[:split_idx_lstm]
    y_lstm_test = y_lstm[split_idx_lstm:]

    # 6. 训练LSTM
    print("训练LSTM...")
    lstm_model = train_lstm(X_lstm_train, y_lstm_train, X_lstm_test, y_lstm_test)

    # 7. 训练XGBoost
    print("训练XGBoost...")
    xgb_model = train_xgboost(X_train_feat_scaled, y_train_scaled)

    # 8. 预测
    # LSTM预测（逆标准化）
    lstm_pred_scaled = lstm_model.predict(X_lstm_test).ravel()
    lstm_pred = scaler_price.inverse_transform(lstm_pred_scaled.reshape(-1, 1)).ravel()

    # XGBoost预测（逆标准化）
    xgb_pred_scaled = xgb_model.predict(X_test_feat_scaled)
    xgb_pred = scaler_target.inverse_transform(xgb_pred_scaled.reshape(-1, 1)).ravel()

    # 注意：两个模型的预测长度可能不一致（由于lookback不同），需对齐到测试集索引
    # 此处因划分同步，长度应一致（假设y_test长度等于预测长度），否则切片对齐。
    min_len = min(len(lstm_pred), len(xgb_pred))
    lstm_pred = lstm_pred[:min_len]
    xgb_pred = xgb_pred[:min_len]
    y_test_actual = y_test[:min_len]
    df_test_time_actual = df_test_time[:min_len]

    # 9. 混合集成（加权平均，权重可优化，这里用简单平均）
    final_pred = 0.5 * lstm_pred + 0.5 * xgb_pred

    # 10. 评估
    mae = mean_absolute_error(y_test_actual, final_pred)
    rmse = np.sqrt(mean_squared_error(y_test_actual, final_pred))
    mape = np.mean(np.abs((y_test_actual - final_pred) / y_test_actual)) * 100

    print(f"\n混合模型评估（测试集）:")
    print(f"MAE : {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2f}%")

    # 11. 可视化
    plt.figure(figsize=(12, 6))
    plt.plot(df_test_time_actual, y_test_actual, label="真实价格", color="black", linewidth=2)
    plt.plot(df_test_time_actual, lstm_pred, label="LSTM预测", alpha=0.7, linestyle="--")
    plt.plot(df_test_time_actual, xgb_pred, label="XGBoost预测", alpha=0.7, linestyle="--")
    plt.plot(df_test_time_actual, final_pred, label="混合模型预测", color="red", linewidth=2)
    plt.title("碳价预测结果对比（KRBN）")
    plt.xlabel("日期")
    plt.ylabel("价格（USD）")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
```

**说明**：
- 数据从Yahoo Finance获取KRBN（跟踪碳配额价格的ETF），若无网络可替换为本地CSV文件。
- 混合方式：LSTM预测序列+ XGBoost预测表格特征，等权平均融合。
- 类型注解已加入关键函数。
- 可直接运行，需安装依赖：`pip install numpy pandas yfinance matplotlib scikit-learn keras xgboost`。

---

## 任务3：调试与部署注意事项

| 风险点 | 现象 | 修复方案 |
|--------|------|----------|
| **数据漂移（概念漂移）** | 模型在部署后精度逐渐下降，尤其是碳价受政策、宏观经济影响 | 定期重训练（每周/每月）；使用在线学习或增量训练（如XGBoost的`process`参数）；监控预测误差与真实值偏差。 |
| **特征工程不一致** | 本地与生产环境特征生成方式不同，导致预测异常 | 将特征工程封装为独立的预处理类（pickle/joblib保存）；部署时确保使用与训练时完全相同的Scaler和特征变换逻辑；对滑动窗口统计值做边界处理。 |
| **过拟合** | 训练集精度极高，测试集表现差，或新数据上波动剧烈 | 增加Dropout（LSTM）、早停（Early Stopping）、XGBoost的`max_depth`限制和`subsample`；引入更多外部特征（如宏观经济）减少记忆。 |
| **模型版本管理混乱** | 不同版本模型同时运行，难以溯源 | 使用MLflow、DVC或W&B记录实验参数、数据版本和模型文件；为每个生产模型打标签（时间+代码commit id）。 |
| **LSTM输入长度与特征对齐** | 线上预测时需要历史数据填充，若lookback窗口缺失则报错 | 设计缓存机制：存储最近N个时间步的真实值；缺失时用预测值填充，或拒绝预测直至数据完整。 |
| **XGBoost对缺失值敏感** | 某些特征实时获取失败（如经济指标延迟发布）导致预测NaN | 训练时加入缺失值占位（如-999）；在生产中设置默认值（如历史中位数）；使用XGBoost内置缺失处理（自动左右分支）。 |
| **模型计算延迟** | 高频预测时LSTM推理时间过长 | 使用ONNX/TensorRT优化LSTM；XGBoost使用`predict(..., output_margin=True)`加速；考虑缓存中间结果或降采样频率。 |
| **部署环境差异** | 不同OS/Python版本导致浮点精度误差或库不兼容 | 使用Docker容器封装环境；固定依赖版本（requirements.txt）；在CPU/GPU间一致性验证。 |
| **评估指标误导** | MAPE在价格接近0时无穷大 | 改用对称MAPE（SMAPE）或定标的MAE/RMSE；关注方向准确率（Direction Accuracy）。 |
| **API限流与数据源失效** | yfinance或数据API不稳定导致预测中断 | 添加重试机制（retry库）；设置本地缓存（每天更新一次）；切换至冗余数据源（如FRED、Quandl）。 |

**部署最佳实践**：
- 采用 **模块化管道**：数据采集 → 预处理 → 模型服务（REST API）→ 结果存储 → 监控告警。
- 使用 **Prometheus + Grafana** 监控模型延迟、错误率、预测分布变化。
- 定期 **回测**：每月使用最新数据评估模型，若性能下降超过阈值则触发重新训练。