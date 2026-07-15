## 任务1：技术选型分析

在能源经济学（特别是碳价预测、电价预测、负荷预测等）中，时间序列依赖性与多特征驱动并存。以下对比四种主流方案，结合领域特点给出选型建议。

| 方案 | 名称 | 适用场景 | 成熟度评级 | 推荐理由 |
|------|------|----------|------------|----------|
| 1️⃣ | LSTM / GRU | 长序列时序预测，如碳价日度序列、负荷曲线 | ★★★★★ | 擅长捕捉时间依赖和非线性；GRU计算更快，适合金融高频；在碳价等金融时间序列上已有大量实证 |
| 2️⃣ | XGBoost / LightGBM | 高维特征驱动的预测，如同时输入原油、天然气、政策指数等 | ★★★★★ | 对表格特征极其鲁棒，自带正则化，可解释性较好（SHAP）；训练快，适合特征工程丰富的场景 |
| 3️⃣ | Transformer | 长距离依赖的序列预测，多变量联合建模 | ★★★☆☆ | 在能源领域尚处探索期，小样本下易过拟合；适合超长窗口（>100步）且计算资源充足时使用 |
| 4️⃣ | 混合模型 CNN-LSTM / Attention-XGBoost | 既需提取局部时序模式，又需融合多特征 | ★★★★☆ | 结合互补优势：CNN提取短期模式+LSTM建模长程，或用Attention加权特征后输入XGBoost；在碳价预测竞赛中频繁夺冠 |

**选型建议**：若特征维度>20且需要高可解释性 → **XGBoost/LightGBM**；若纯时序依赖强且样本充足 → **LSTM/GRU**；若两者兼具且追求极致精度 → **CNN-LSTM 或 Attention+XGBoost**（本文任务2即采用LSTM + XGBoost混合模型）。Transformer建议在数据量大（>10万条）、窗口长（>200）时尝试，否则性价比不高。

---

## 任务2：碳价预测完整代码（LSTM + XGBoost 混合模型）

```python
"""
碳价预测：LSTM + XGBoost 混合模型
数据来源：使用 yfinance 获取布伦特原油期货价格作为示例（碳价公开数据获取困难，
实际应用请替换为欧盟碳配额EUA期货（如 yfinance 代码 "EUA=F"）或自行接入ICE/EEX数据）
功能：数据预处理→特征工程→LSTM提取时序特征→XGBoost融合预测→评估
作者：能源ML专家
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import xgboost as xgb
import matplotlib.pyplot as plt
from typing import Tuple, Optional, List, Dict

# ---------------------------- 1. 数据获取（公开数据集）-------------------------
# 使用布伦特原油期货（BZ=F）作为示例碳价序列（实际可替换为 EUA=F 或 CO2 指数）
def fetch_data(ticker: str = "BZ=F", start: str = "2010-01-01",
               end: str = "2025-01-01") -> pd.DataFrame:
    """
    从 Yahoo Finance 获取期货价格数据
    Args:
        ticker: 合约代码（例：布伦特原油 "BZ=F"，碳配额 "EUA=F"）
        start: 起始日期
        end: 结束日期
    Returns:
        DataFrame 包含 'Close' 列
    """
    data = yf.download(ticker, start=start, end=end, progress=False)
    return data[['Close']].rename(columns={'Close': 'price'})

# ---------------------------- 2. 特征工程 -------------------------
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    构造特征：滞后值、移动平均、波动率、日收益率、星期哑变量
    Args:
        df: 包含 'price' 列的 DataFrame
    Returns:
        添加特征后的 DataFrame
    """
    df = df.copy()
    # 日收益率（百分比）
    df['return'] = df['price'].pct_change() * 100
    # 滞后1~5天价格
    for lag in range(1, 6):
        df[f'lag_{lag}'] = df['price'].shift(lag)
    # 5天移动平均
    df['ma5'] = df['price'].rolling(5).mean()
    # 20天移动平均
    df['ma20'] = df['price'].rolling(20).mean()
    # 5天波动率（标准差）
    df['volatility5'] = df['return'].rolling(5).std()
    # 星期几（0=周一，4=周五）
    df['weekday'] = df.index.weekday
    # 周一生效因子（部分能源价格有周内效应）
    df['is_monday'] = (df['weekday'] == 0).astype(int)
    # 删除缺失值（前20天因滚动窗口产生缺失）
    df = df.dropna()
    return df

def prepare_lstm_data(df: pd.DataFrame, seq_len: int = 20,
                      target_col: str = 'price') -> Tuple[np.ndarray, np.ndarray]:
    """
    为LSTM准备序列数据：使用前 seq_len 天的价格预测第 seq_len+1 天价格
    Args:
        df: 含 'price' 的 DataFrame
        seq_len: 时间窗口长度
        target_col: 目标列名
    Returns:
        (X_lstm, y) 形状 (样本数, seq_len, 1) 和 (样本数,)
    """
    prices = df[target_col].values.reshape(-1, 1)
    scaler_price = MinMaxScaler(feature_range=(0, 1))
    prices_scaled = scaler_price.fit_transform(prices)
    
    X, y = [], []
    for i in range(seq_len, len(prices_scaled)):
        X.append(prices_scaled[i-seq_len:i, 0])
        y.append(prices_scaled[i, 0])
    return np.array(X).reshape(-1, seq_len, 1), np.array(y), scaler_price

# ---------------------------- 3. LSTM模型训练 -------------------------
def build_lstm_model(seq_len: int = 20) -> Sequential:
    """
    构建单层LSTM回归模型
    Args:
        seq_len: 时间步长
    Returns:
        Keras Sequential 模型
    """
    model = Sequential([
        LSTM(64, return_sequences=False, input_shape=(seq_len, 1)),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

# ---------------------------- 4. 主流程 -------------------------
def main():
    # ========== 数据加载与特征工程 ==========
    print("[INFO] 下载公开数据（布伦特原油期货作示例）...")
    df = fetch_data()
    print(f"[INFO] 数据范围：{df.index[0].date()} ~ {df.index[-1].date()}, 共 {len(df)} 条")
    
    df = create_features(df)
    print(f"[INFO] 特征构建完成，特征列：{list(df.columns)}")
    
    # ========== 划分训练/测试集（时间序列不能随机打乱）==========
    split_date = "2023-01-01"   # 2023年之前为训练
    train = df[df.index < split_date].copy()
    test = df[df.index >= split_date].copy()
    print(f"[INFO] 训练集：{len(train)} 条，测试集：{len(test)} 条")
    
    # ========== 准备LSTM输入 ==========
    seq_len = 20
    # 训练集LSTM数据
    X_train_lstm, y_train_lstm, scaler_price = prepare_lstm_data(train, seq_len)
    # 测试集LSTM数据（使用与训练集相同的scaler）
    test_prices = test['price'].values.reshape(-1, 1)
    test_prices_scaled = scaler_price.transform(test_prices)
    X_test_lstm, y_test_lstm = [], []
    for i in range(seq_len, len(test_prices_scaled)):
        X_test_lstm.append(test_prices_scaled[i-seq_len:i, 0])
        y_test_lstm.append(test_prices_scaled[i, 0])
    X_test_lstm = np.array(X_test_lstm).reshape(-1, seq_len, 1)
    y_test_lstm = np.array(y_test_lstm)
    
    # ========== 训练LSTM ==========
    print("\n[INFO] 训练LSTM...")
    lstm_model = build_lstm_model(seq_len)
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    history = lstm_model.fit(
        X_train_lstm, y_train_lstm,
        validation_split=0.1,
        epochs=100,
        batch_size=32,
        callbacks=[early_stop],
        verbose=1
    )
    
    # LSTM预测（归一化后）
    lstm_pred_train_scaled = lstm_model.predict(X_train_lstm, verbose=0)
    lstm_pred_test_scaled = lstm_model.predict(X_test_lstm, verbose=0)
    # 逆变换回原始价格
    lstm_pred_train = scaler_price.inverse_transform(lstm_pred_train_scaled.reshape(-1, 1)).flatten()
    lstm_pred_test = scaler_price.inverse_transform(lstm_pred_test_scaled.reshape(-1, 1)).flatten()
    y_train_actual = scaler_price.inverse_transform(y_train_lstm.reshape(-1, 1)).flatten()
    y_test_actual = scaler_price.inverse_transform(y_test_lstm.reshape(-1, 1)).flatten()
    
    # ========== 准备XGBoost特征 ==========
    # 注意：LSTM预测基于价格序列，XGBoost使用更多特征（包括LSTM预测值）
    # 需要对齐时间索引：LSTM输出比原始数据滞后seq_len天
    def build_xgboost_features(original_df: pd.DataFrame, lstm_pred: np.ndarray,
                               seq_len: int) -> pd.DataFrame:
        """
        拼接原始特征与LSTM预测值，形成XGBoost的输入特征矩阵
        Args:
            original_df: 原始特征 DataFrame（已包含所有工程特征）
            lstm_pred: LSTM预测结果（长度 = len(original_df) - seq_len）
            seq_len: 窗口长度
        Returns:
            DataFrame 特征矩阵，索引与 lstm_pred 对齐
        """
        # 原始数据从第seq_len行开始与lstm_pred对齐
        base_df = original_df.iloc[seq_len:].reset_index(drop=True)
        base_df['lstm_pred'] = lstm_pred
        return base_df
    
    train_features = build_xgboost_features(train, lstm_pred_train, seq_len)
    test_features = build_xgboost_features(test, lstm_pred_test, seq_len)
    
    # XGBoost目标值：对应日期当天的实际价格（已对齐）
    xgb_y_train = y_train_actual
    xgb_y_test = y_test_actual
    
    # 选择特征列（排除目标列和索引列）
    exclude_cols = ['price', 'index']  # 'index'可能不存在
    xgb_cols = [c for c in train_features.columns if c not in exclude_cols]
    X_xgb_train = train_features[xgb_cols].values
    X_xgb_test = test_features[xgb_cols].values
    
    # ========== 训练XGBoost ==========
    print("\n[INFO] 训练XGBoost...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(X_xgb_train, xgb_y_train,
                  eval_set=[(X_xgb_train, xgb_y_train), (X_xgb_test, xgb_y_test)],
                  verbose=False)
    
    # ========== 预测与评估 ==========
    y_pred_train = xgb_model.predict(X_xgb_train)
    y_pred_test = xgb_model.predict(X_xgb_test)
    
    def evaluate(y_true: np.ndarray, y_pred: np.ndarray, title: str) -> Dict:
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        print(f"\n========== {title} ==========")
        print(f"MAE  : {mae:.4f}")
        print(f"RMSE : {rmse:.4f}")
        print(f"R²   : {r2:.4f}")
        print(f"MAPE : {mape:.2f}%")
        return {'MAE': mae, 'RMSE': rmse, 'R2': r2, 'MAPE': mape}
    
    train_metrics = evaluate(y_pred_train, xgb_y_train, "训练集")
    test_metrics = evaluate(y_pred_test, xgb_y_test, "测试集")
    
    # ========== 可视化 ==========
    plt.figure(figsize=(12, 5))
    # 测试集预测对比
    dates_test = test_features.index  # 与test对齐的日期
    plt.plot(dates_test, xgb_y_test, label='实际价格', color='blue')
    plt.plot(dates_test, y_pred_test, label='预测价格(LSTM+XGBoost)', color='red', linestyle='--')
    plt.title('碳价预测结果 (测试集)')
    plt.xlabel('日期')
    plt.ylabel('价格')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('carbon_price_prediction.png', dpi=150)
    plt.show()
    
    # 特征重要性
    importance = xgb_model.feature_importances_
    feat_imp = pd.Series(importance, index=xgb_cols).sort_values(ascending=False)
    print("\n[INFO] 前10重要特征:")
    print(feat_imp.head(10))
    
    print("\n[SUCCESS] 项目运行完成！")

if __name__ == "__main__":
    main()
```

**说明**：  
1. 数据来源：yfinance 公开API，默认下载布伦特原油作为碳价示例；实际使用时将 `ticker` 改为 `"EUA=F"` 或使用其他碳配额价格源。  
2. 混合逻辑：LSTM仅使用价格序列预测（捕获时序依赖），XGBoost接受全部工程特征 + LSTM预测值作为新特征，进行最终预测。  
3. 运行需安装依赖：`pip install yfinance pandas numpy scikit-learn tensorflow xgboost matplotlib`。

---

## 任务3：调试与部署注意事项

| 风险点 | 具体表现 | 修复方案 |
|--------|----------|----------|
| **数据泄露（Data Leakage）** | 使用未来信息构造滞后/滚动特征（如计算移动平均时包含了未来值） | 确保所有特征只依赖历史数据；使用 `shift()` 明确滞后；按时间顺序划分训练/测试集 |
| **过拟合（Overfitting）** | LSTM epoch过多或XGBoost树过深，测试集误差远大于训练集 | 早停（EarlyStopping）、正则化（Dropout、L1/L2）、减小树深度、增大 subsample |
| **分布漂移（Concept Drift）** | 碳市场政策变化（如EU ETS改革）导致历史模式失效 | 定期用新数据重训练（滚动窗口）；加入在线学习或增量更新（如XGBoost的热启动） |
| **归一化不一致** | 训练和测试使用不同scaler变换导致预测偏差 | 用训练集fit scaler，然后在测试集上仅transform；保存scaler.pkl供推理使用 |
| **时间对齐错误** | LSTM输出与原始索引偏移（因window长度）导致特征拼接错位 | 严格按索引切片，使用 `iloc[seq_len:]` 对齐；可视化检查预测日期与实际日期 |
| **资源消耗（内存/显存）** | LSTM序列过长或batch_size过大导致OOM | 减小seq_len、batch_size；使用生成器（`tf.keras.utils.Sequence`）流式加载；XGBoost开启 `tree_method='gpu_hist'`（需GPU） |
| **部署预测延迟** | 每次预测需重新运行整个LSTM+XGBoost pipeline | 将训练好的模型序列化（`model.save` + `joblib.dump`）；预测时仅执行前向传播，避免重复特征工程 |
| **数据缺失（Missing Values）** | 某些日期无数据（节假日、交易所休息） | 前向填充（ffill）或插值；训练时注意使用 `dropna` 后对齐索引 |
| **可解释性不足** | 混合模型内部逻辑复杂，难以向业务方解释 | 利用SHAP分析XGBoost特征重要性；单独评估LSTM贡献（如比较有无LSTM特征的效果） |
| **依赖版本冲突** | TensorFlow 2.x 与 XGBoost 1.x 的 API 差异 | 在 `requirements.txt` 中锁定版本；使用 Docker 容器化部署 |
| **API数据不稳定** | yfinance 断连或数据格式变化 | 增加异常捕获与重试逻辑；本地缓存数据；预备备用数据源（如Quandl、FRED） |

**部署建议**：
- 建立CI/CD流水线，定期（如每周）重新训练模型并更新至生产环境；  
- 使用轻量级推理服务（如Flask + ONNX转LSTM，或将XGBoost模型转换为 `treelite`格式）；  
- 监控预测误差漂移，设置告警阈值（如MAPE超过10%则触发人工干预）；  
- 保留预测记录用于事后归因分析，支持模型版本回溯。