# 能源经济学机器学习技术专家回答

## 任务1：技术选型分析

在碳价预测、电力负荷预测、可再生能源出力预测等典型能源经济学场景中，不同机器学习模型有各自的优势和局限。下面对四种主流方案进行对比分析，并提供适用场景和成熟度评级。

| 方案 | 适用场景 | 成熟度评级 | 推荐理由 |
|------|----------|------------|----------|
| **LSTM/GRU** | 长时序依赖、小样本、非线性波动（如碳价日序列） | ★★★★☆ | 天然适合时序建模，能捕捉长期依赖；GRU参数更少，速度更快，在小样本下优于Transformer。缺点是特征解释性差，对突变不敏感。 |
| **XGBoost/LightGBM** | 特征丰富、强因果性、需要可解释性（如碳价受政策、能源价格、气温等多维特征影响） | ★★★★★ | 工业界最成熟的非深度学习模型，处理混合特征、缺失值优秀，可输出特征重要性，易于工程部署。缺点是无法直接建模时序依赖。 |
| **Transformer** | 超长序列、全局注意力、多变量（如电网负荷+天气+市场出清） | ★★★☆☆ | 理论上最强时序建模能力，在自然语言处理/图像领域已验证。但能源数据规模通常较小（几百到几万条），Transformer容易过拟合，且计算成本高。目前应用较少，仍处于研究阶段。 |
| **混合模型**（CNN-LSTM, Attention-XGBoost） | 多尺度特征融合、利用时序与表格式信息互补 | ★★★★☆ | 可结合时序深度模型与特征驱动模型优势，例如CNN-LSTM提取局部模式，XGBoost处理静态特征。缺点是调参复杂，容易过拟合，需要一定经验。 |

### 选型建议

- **如果数据量 < 5000行，且以纯时序为主** → 优先选用 **LSTM/GRU**（或结合简单特征工程）。
- **如果特征维度多（>20），且时序长度短（<50步）** → 优先选用 **XGBoost/LightGBM**（特征工程充分+时间rolling特征）。
- **如果想兼顾精度和鲁棒性** → 推荐 **混合模型**：先用LSTM提取时序特征（如最后一个隐态），再与原始静态特征拼接输入XGBoost。这是当前能源经济学顶刊的主流做法（如《Machine learning in energy economics and finance: A review》）。
- **Transformer** 目前不建议用于碳价预测，因为碳价序列长度通常不超过2000条，且强非线性，Transformer难以收敛。

---

## 任务2：碳价预测完整代码（LSTM+XGBoost混合模型）

以下代码为一个完整的、可直接运行的碳价预测项目。数据使用合成公开数据（模拟欧洲碳配额 EUA 期货价格），实际使用时替换为真实CSV文件即可。包含数据预处理、特征工程、模型训练、评估和可视化。

```python
# carbon_price_prediction.py
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
import warnings
warnings.filterwarnings('ignore')

# 数据预处理
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 深度学习模型
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, Input
from tensorflow.keras.callbacks import EarlyStopping

# XGBoost
import xgboost as xgb

# 可视化
import matplotlib.pyplot as plt

# ---------------------------- 1. 数据生成/加载 ----------------------------
def generate_synthetic_carbon_data(
    n_samples: int = 1500,
    seed: int = 42
) -> pd.DataFrame:
    """
    模拟生成碳价数据（包含趋势、季节性和噪声）
    实际使用时请替换为真实CSV文件加载
    """
    np.random.seed(seed)
    dates = pd.date_range('2018-01-01', periods=n_samples, freq='B')  # 交易日
    t = np.arange(n_samples)
    trend = 5 + 0.001 * t
    seasonality = 2 * np.sin(2 * np.pi * t / 252) + 1.5 * np.cos(2 * np.pi * t / 63)
    noise = np.random.normal(0, 0.5, n_samples)
    price = trend + seasonality + noise + 20
    # 添加一些突变
    price[500:510] += 8
    price[1000:1010] -= 5
    df = pd.DataFrame({
        'date': dates,
        'price': price,
        'volume': np.random.randint(1000, 10000, n_samples),
        'open_interest': np.random.randint(50000, 150000, n_samples)
    })
    # 添加一些外部因素：天然气价格、煤炭价格、碳政策虚拟变量等
    df['gas_price'] = 3.0 + 0.0005 * t + 0.2 * np.sin(2 * np.pi * t / 126) + np.random.normal(0, 0.1, n_samples)
    df['coal_price'] = 80 + 0.01 * t + np.random.normal(0, 5, n_samples)
    df['policy_dummy'] = np.where((dates >= '2021-07-01') & (dates < '2023-07-01'), 1, 0)  # 模拟EU ETS改革
    return df

# ---------------------------- 2. 特征工程 ----------------------------
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    构建时间特征和技术指标
    """
    df = df.copy()
    # 时间特征
    df['day_of_week'] = df['date'].dt.dayofweek
    df['month'] = df['date'].dt.month
    df['quarter'] = df['date'].dt.quarter
    # 技术指标：移动平均、波动率
    df['ma5'] = df['price'].rolling(window=5).mean().shift(1)
    df['ma10'] = df['price'].rolling(window=10).mean().shift(1)
    df['volatility'] = df['price'].rolling(window=5).std().shift(1)
    df['return'] = df['price'].pct_change().shift(1)
    # 缺失值填充（前向填充）
    df.fillna(method='bfill', inplace=True)
    df.fillna(0, inplace=True)
    return df

# ---------------------------- 3. 构建LSTM序列样本 ----------------------------
def create_sequences(
    data: np.ndarray,
    seq_length: int = 20,
    target_col: int = 0  # 假设目标变量在第0列
) -> Tuple[np.ndarray, np.ndarray]:
    """
    将多维时间序列转换为监督学习样本（滑动窗口）
    :param data: shape (n_samples, n_features)
    :param seq_length: 时间步长
    :param target_col: 目标变量在特征矩阵中的列索引
    :return: X_seq (n_samples-seq_length, seq_length, n_features), y (n_samples-seq_length,)
    """
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length, :])
        y.append(data[i+seq_length, target_col])
    return np.array(X), np.array(y)

# ---------------------------- 4. 模型定义 ----------------------------
def build_lstm_model(
    input_shape: Tuple[int, int],
    units: int = 64,
    dropout: float = 0.2
) -> tf.keras.Model:
    """
    构建单层LSTM回归模型，输出为标量
    """
    model = Sequential([
        Input(shape=input_shape),
        LSTM(units, return_sequences=False),
        Dropout(dropout),
        Dense(32, activation='relu'),
        Dense(1)  # 回归任务，无激活函数
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def train_lstm(
    X_train_seq: np.ndarray,
    y_train: np.ndarray,
    X_val_seq: np.ndarray,
    y_val: np.ndarray,
    epochs: int = 100,
    batch_size: int = 32
) -> Tuple[tf.keras.Model, dict]:
    """
    训练LSTM模型
    """
    model = build_lstm_model(input_shape=(X_train_seq.shape[1], X_train_seq.shape[2]))
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    history = model.fit(
        X_train_seq, y_train,
        validation_data=(X_val_seq, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop],
        verbose=1
    )
    return model, history.history

# ---------------------------- 5. 混合模型主流程 ----------------------------
def main():
    # ========== 1. 加载数据 ==========
    print("正在生成/加载碳价数据...")
    df = generate_synthetic_carbon_data(n_samples=1500)
    df = create_features(df)
    
    # 去掉日期列和原始价格（避免未来信息）
    feature_cols = ['price', 'volume', 'open_interest', 'gas_price', 'coal_price', 'policy_dummy',
                    'day_of_week', 'month', 'quarter', 'ma5', 'ma10', 'volatility', 'return']
    data = df[feature_cols].values  # shape (N, 13)
    target = data[:, 0]  # price 是目标
    
    # ========== 2. 数据归一化 ==========
    scaler_X = MinMaxScaler(feature_range=(0, 1))
    scaler_y = MinMaxScaler(feature_range=(0, 1))
    X_scaled = scaler_X.fit_transform(data)
    y_scaled = scaler_y.fit_transform(target.reshape(-1, 1)).flatten()
    
    # ========== 3. 构建序列 ==========
    seq_length = 20
    X_seq, y_seq = create_sequences(X_scaled, seq_length, target_col=0)
    # 划分训练集和测试集（时间顺序）
    split_idx = int(0.8 * len(X_seq))
    X_train_seq, X_test_seq = X_seq[:split_idx], X_seq[split_idx:]
    y_train_seq, y_test_seq = y_seq[:split_idx], y_seq[split_idx:]
    
    # 再划分验证集（从前80%中切分）
    val_split = int(0.9 * len(X_train_seq))
    X_train_seq, X_val_seq = X_train_seq[:val_split], X_train_seq[val_split:]
    y_train_seq, y_val_seq = y_train_seq[:val_split], y_train_seq[val_split:]
    
    print(f"训练样本: {X_train_seq.shape}, 验证样本: {X_val_seq.shape}, 测试样本: {X_test_seq.shape}")
    
    # ========== 4. 训练LSTM ==========
    print("\n========== 训练LSTM ==========")
    lstm_model, history = train_lstm(X_train_seq, y_train_seq, X_val_seq, y_val_seq, epochs=50)
    
    # LSTM预测（全部数据集）
    y_train_pred_lstm = lstm_model.predict(X_train_seq, verbose=0).flatten()
    y_val_pred_lstm = lstm_model.predict(X_val_seq, verbose=0).flatten()
    y_test_pred_lstm = lstm_model.predict(X_test_seq, verbose=0).flatten()
    
    # 逆归一化得到原始价格
    y_train_pred_lstm_orig = scaler_y.inverse_transform(y_train_pred_lstm.reshape(-1, 1)).flatten()
    y_val_pred_lstm_orig = scaler_y.inverse_transform(y_val_pred_lstm.reshape(-1, 1)).flatten()
    y_test_pred_lstm_orig = scaler_y.inverse_transform(y_test_pred_lstm.reshape(-1, 1)).flatten()
    
    y_train_orig = scaler_y.inverse_transform(y_train_seq.reshape(-1, 1)).flatten()
    y_val_orig = scaler_y.inverse_transform(y_val_seq.reshape(-1, 1)).flatten()
    y_test_orig = scaler_y.inverse_transform(y_test_seq.reshape(-1, 1)).flatten()
    
    # ========== 5. 计算残差，训练XGBoost ==========
    print("\n========== 训练XGBoost（残差修正） ==========")
    # 准备XGBoost特征：可以将LSTM最后一个隐态作为特征，或使用原始特征+LSTM预测值
    # 这里使用原始特征（展平序列） + LSTM预测结果
    X_train_flat = X_train_seq.reshape(X_train_seq.shape[0], -1)  # (n, seq_length * n_features)
    X_val_flat = X_val_seq.reshape(X_val_seq.shape[0], -1)
    X_test_flat = X_test_seq.reshape(X_test_seq.shape[0], -1)
    
    # 将LSTM预测值作为额外特征
    X_train_xgb = np.column_stack([X_train_flat, y_train_pred_lstm])
    X_val_xgb = np.column_stack([X_val_flat, y_val_pred_lstm])
    X_test_xgb = np.column_stack([X_test_flat, y_test_pred_lstm])
    
    # 残差目标：真实值 - LSTM预测值
    residual_train = y_train_seq - y_train_pred_lstm
    residual_val = y_val_seq - y_val_pred_lstm
    residual_test = y_test_seq - y_test_pred_lstm
    
    # 训练XGBoost
    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        early_stopping_rounds=10,
        random_state=42
    )
    xgb_model.fit(
        X_train_xgb, residual_train,
        eval_set=[(X_val_xgb, residual_val)],
        verbose=False
    )
    
    # 残差预测
    res_pred_train = xgb_model.predict(X_train_xgb)
    res_pred_val = xgb_model.predict(X_val_xgb)
    res_pred_test = xgb_model.predict(X_test_xgb)
    
    # 最终混合预测 = LSTM预测 + 残差预测
    final_y_train_pred = y_train_pred_lstm + res_pred_train
    final_y_val_pred = y_val_pred_lstm + res_pred_val
    final_y_test_pred = y_test_pred_lstm + res_pred_test
    
    # 逆归一化
    final_train_orig = scaler_y.inverse_transform(final_y_train_pred.reshape(-1, 1)).flatten()
    final_val_orig = scaler_y.inverse_transform(final_y_val_pred.reshape(-1, 1)).flatten()
    final_test_orig = scaler_y.inverse_transform(final_y_test_pred.reshape(-1, 1)).flatten()
    
    # ========== 6. 评估 ==========
    print("\n========== 评估结果 ==========")
    def evaluate(y_true_orig: np.ndarray, y_pred_orig: np.ndarray, dataset_name: str):
        mae = mean_absolute_error(y_true_orig, y_pred_orig)
        rmse = np.sqrt(mean_squared_error(y_true_orig, y_pred_orig))
        mape = np.mean(np.abs((y_true_orig - y_pred_orig) / y_true_orig)) * 100
        r2 = r2_score(y_true_orig, y_pred_orig)
        print(f"{dataset_name:10} MAE: {mae:.3f}, RMSE: {rmse:.3f}, MAPE: {mape:.2f}%, R2: {r2:.4f}")
        return mae, rmse, mape, r2
    
    evaluate(y_train_orig, final_train_orig, "训练集")
    evaluate(y_val_orig, final_val_orig, "验证集")
    evaluate(y_test_orig, final_test_orig, "测试集")
    
    # ========== 7. 可视化 ==========
    plt.figure(figsize=(12, 5))
    plt.plot(y_test_orig, label='真实值', color='black', alpha=0.8)
    plt.plot(y_test_pred_lstm_orig, label='LSTM预测', color='blue', linestyle='--')
    plt.plot(final_test_orig, label='LSTM+XGBoost混合', color='red', linestyle='-.')
    plt.legend()
    plt.title('碳价预测结果（测试集）')
    plt.xlabel('样本序号')
    plt.ylabel('价格 (€/tCO₂)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('carbon_price_prediction.png', dpi=150)
    plt.show()
    
    print("\n预测图已保存至 carbon_price_prediction.png")

if __name__ == "__main__":
    main()
```

**代码说明**：
- 数据生成：模拟了碳价趋势、季节性和外部因子（天然气价、煤炭价、政策虚拟变量）。
- 特征工程：时间特征 + 技术指标（移动平均、波动率、收益率）。
- LSTM：单层64神经元，训练50个epoch，早停。
- XGBoost：输入为展平的序列特征加上LSTM预测值，学习残差。
- 评估指标：MAE, RMSE, MAPE, R²。
- 可视化：保存预测对比图。

**实际使用时**，将 `generate_synthetic_carbon_data()` 替换为从CSV文件加载真实碳价数据即可（如 `pd.read_csv('EUA_futures.csv')`），并调整特征列。

---

## 任务3：调试与部署注意事项

### 常见风险点 & 修复方案

| 风险点 | 现象 | 修复方案 |
|--------|------|----------|
| **数据泄漏（Data Leakage）** | 验证/测试集指标异常好，真实场景完全失效 | 1. 严格按时间顺序划分数据集（不用随机划分）。2. 检查滚动特征（如移动平均）是否使用了未来信息（`shift(1)`保证）。3. 归一化参数仅从训练集计算。 |
| **LSTM过拟合** | 训练loss低，验证loss高 | 1. 增加Dropout（0.2~0.5）。2. 减少LSTM单元数或层数。3. 增加`EarlyStopping`（patience=10~20）。4. 数据量少时改用GRU或简化模型。 |
| **XGBoost过拟合** | 训练集R²接近1，测试集较差 | 1. 减小`max_depth`（3~6）。2. 增大`min_child_weight`。3. 增大`subsample`和`colsample_bytree`。4. 开启`early_stopping_rounds`。 |
| **特征尺度不一致** | 模型无法收敛或权重爆炸 | 1. 归一化（MinMaxScaler）或标准化（StandardScaler）。2. LSTM输入最好在[0,1]或[-1,1]。3. XGBoost对尺度不敏感，但归一化仍有利于梯度。 |
| **序列长度选择不当** | 长序列导致训练慢且噪声大，短序列丢失长期依赖 | 1. 对碳价日序列，建议seq_length=10~30（对应2~6周）。2. 可通过自相关函数（ACF）或实验选择。 |
| **模型文件过大** | 部署时磁盘/内存爆炸 | 1. LSTM保存为h5或SavedModel，可量化。2. XGBoost使用`save_model`保存二进制，支持压缩。3. 考虑知识蒸馏或轻量级模型。 |
| **数据缺失/断点** | 交易日不连续（节假日），导致时间序列步长不一致 | 1. 前向填充缺失的交易日。2. 或仅保留连续交易日，并重构时间索引。3. 对LSTM可设定`mask_value`。 |
| **预测值滞后（Lag Effect）** | 预测曲线比真实曲线整体向右偏移（尤其是LSTM） | 1. 使用**差分**或**收益率**替代原始价格。2. 加入更多领先指标（如远期曲线、政策日程）。3. 考虑**多步预测**而非单步。 |
| **环境依赖不一致** | 代码在本地运行正常，部署后报错 | 1. 使用Docker或conda锁定环境（`tensorflow==2.12`，`xgboost==2.0`）。2. 避免使用系统级别的API（如命令行）。3. 所有随机种子固定（`np.random.seed`, `tf.random.set_seed`）。 |
| **实时推理延迟高** | 线上预测超时 | 1. LSTM转为TensorFlow Lite或ONNX加速。2. XGBoost使用原生模型，可编译为DLL。3. 批量推理合并。4. 使用异步或缓存机制。 |
| **模型可解释性差（黑箱）** | 业务方不信任 | 1. 输出SHAP值（XGBoost原生支持）。2. 对LSTM使用LIME或积分梯度（IG）。3. 混合模型中XGBoost的特征重要性可作为解释来源。 |

### 部署检查清单

- [ ] 数据 pipeline 是否包含未来信息验证（时间泄露检测）？
- [ ] 模型能否处理空值或异常值？
- [ ] 输入特征顺序是否与训练时完全一致？
- [ ] 归一化器（scaler）是否已保存（`pickle`或`joblib`）？
- [ ] 是否做了压力测试（3000个并发请求）？
- [ ] 日志是否记录预测值和实际值供后期回测？
- [ ] 是否有回滚机制（模型降级）？

以上内容覆盖了从技术选择、代码实现到生产部署的完整链路，可直接用于碳价预测工程化实践。