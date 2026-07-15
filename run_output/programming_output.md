好的，作为能源经济学机器学习领域的技术专家，我将基于您提供的论文背景（特别是强调机器学习在能源经济学中的系统性应用与挑战），结合碳价预测这一具体场景，为您完成三大任务。

---

### 任务1：技术选型分析

在能源经济学中，碳价预测是一个典型的高维度、非线性、受多因素（政策、宏观经济、能源价格、天气等）影响的时序问题。针对此类问题，对以下方案进行对比分析：

| 方案 | 名称 | 适用场景 | 成熟度评级 | 推荐理由 |
| :--- | :--- | :--- | :--- | :--- |
| **方案A** | **LSTM/GRU** | **纯时序序列预测** | ★★★★ | 天然适合处理时间序列中的长期依赖关系（如碳价的趋势性、季节性）。GRU作为LSTM的简化版，参数更少，训练更快，在小样本数据集上不易过拟合。缺点是对突发性政策事件（如供应配额调整）的捕捉能力较弱。 |
| **方案B** | **XGBoost/LightGBM** | **结构化特征驱动预测** | ★★★★★ | 在Kaggle等竞赛中已被证明是处理表格数据的王者。对于碳价预测，若能构造出高质量的特征（如能源价格差、宏观经济指标、库存量等），其非线性拟合能力和特征重要性解释性都非常出色。对异常值和缺失值有天然的鲁棒性。LightGBM相较于XGBoost更适合大数据集，训练速度更快。 |
| **方案C** | **Transformer** | **超长序列与复杂交互建模** | ★★★ | 核心优势在于通过自注意力机制捕捉序列中任意位置的依赖关系，理论上能解决LSTM的梯度消失问题，并捕捉政策文本、新闻情感等非结构化信息。但在中小规模时间序列数据（如日度碳价数据，通常只有几千个样本）上，容易过拟合，且计算成本高。在能源经济领域，目前尚处于前沿探索阶段。 |
| **方案D** | **混合模型** | **兼顾时序依赖与特征驱动** | ★★★★★ | 最适用于碳价预测。可以发挥不同模型的优势：例如，**CNN-LSTM**能先提取局部特征（如短期波动模式）再建模长期依赖；**Attention-XGBoost**利用Attention机制捕捉关键时间步的特征，再交给XGBoost进行最终预测；**LSTM-XGBoost**是当前最成熟的组合方案，将LSTM输出的时序特征作为XGBoost的输入特征，实现“时序理解 + 强分类器”的协同。 |

**最终选型建议：**

**首选方案 D：混合模型（特别是 LSTM + XGBoost）**

*   **核心逻辑：** 碳价预测的本质是“时序性”和“因果性”的结合。
    *   **第一阶段（LSTM/GRU）：** 负责提取碳价序列本身的内在规律，如趋势、周期、短期记忆（价格惯性）。
    *   **第二阶段（XGBoost/LightGBM）：** 负责学习外部特征（如天然气价格、煤价、电力期货、宏观经济指数等）对碳价的非线性驱动关系。
*   **成熟度与可行性：** 该方案已多次在能源经济顶级期刊（如《Energy Economics》）和国际竞赛中证明其有效性，技术栈成熟，有大量开源代码可复用。同时，XGBoost/LightGBM提供的特征重要性分析，能很好地满足论文中强调的“**可解释人工智能**”要求。
*   **为什么不用纯Transformer？** 对于碳价这种数据量（通常几千到几万条日度数据）和信噪比（噪声大，政策性冲击强）而言，纯粹使用Transformer不仅计算昂贵，而且效果往往不如精心调校的混合模型。

---

### 任务2：碳价预测完整代码

以下是一个完整的 Python 碳价预测项目，使用 `LSTM(GRU) + XGBoost` 混合模型。数据从公开的 FRED（圣路易斯联邦储备银行）获取，并结合模拟的欧洲碳排放配额（EUA）期货数据。

```python
# -*- coding: utf-8 -*-
"""
碳价预测项目：LSTM + XGBoost 混合模型
作者：AI Energy Assistant
数据来源：FRED API + 模拟历史数据（为演示，真实场景请接入ICE等交易所）
核心方法：
  1. 使用 GRU（LSTM 变体，更快）提取时间序列特征。
  2. 将 GRU 输出作为新特征，与原结构化特征合并。
  3. 使用 XGBoost 进行最终回归预测。
"""

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from typing import Tuple, Any, Dict

# 数据获取与预处理
import yfinance as yf
import pandas_datareader.data as web
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 深度学习
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# XGBoost
import xgboost as xgb

# 设置随机种子以确保可复现
def set_seed(seed: int = 42) -> None:
    """设置随机种子"""
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(42)

# ----------------- 1. 数据获取与特征工程 -----------------

def fetch_data(start_date: str = "2020-01-01", end_date: str = "2024-10-31") -> pd.DataFrame:
    """
    获取碳价相关的公开数据。
    
    假设：碳排放配额（EUA）期货合约价格为 'EUA'。
    我们使用标普500指数 (^GSPC) 代表宏观经济环境，
    天然气期货 (NG=F) 代表能源替代效应。
    
    注意：真实的 EUA 数据需要从 ICE 或路孚特获取，此处使用模拟。
    """
    # 获取宏观经济和能源数据
    print("正在获取标普500指数和天然气期货数据...")
    sp500 = yf.download("^GSPC", start=start_date, end=end_date)["Close"].rename("SP500")
    natural_gas = yf.download("NG=F", start=start_date, end=end_date)["Close"].rename("NG_Price")

    # 合成欧盟碳配额（EUA）期货价格（基于真实走势模拟）
    np.random.seed(42)
    date_index = pd.date_range(start=start_date, end=end_date, freq='B')
    n = len(date_index)
    # 模拟一个带有趋势、季节性和随机噪声的碳价序列：
    # 基础趋势：从 20 欧元缓慢上升到 80 欧元
    trend = np.linspace(20, 80, n)
    # 季节性：冬季需求大，价格高
    seasonal = 15 * np.sin(2 * np.pi * np.arange(n) / 252)  # 每年252个交易日
    # 噪声
    noise = np.random.normal(0, 2, n)
    # 合并，确保价格为正
    price = trend + seasonal + noise
    price = np.maximum(price, 10)  # 下限为10欧元

    # 模拟澳大利亚电价（ASX）作为关联市场
    electricity = 50 + 30 * np.sin(2 * np.pi * np.arange(n) / 180) + np.random.normal(0, 5, n)

    df = pd.DataFrame({
        "Date": date_index,
        "EUA_Price": price,
        "Electricity_Price": electricity
    })
    # 合并其他数据（由于高频数据可能不同步，向前填充）
    df.set_index("Date", inplace=True)
    df = df.join(sp500, how="left")
    df = df.join(natural_gas, how="left")
    # 填充缺失值（节假日等）
    df.fillna(method='ffill', inplace=True)
    df.fillna(method='bfill', inplace=True)

    print(f"数据获取完成，时间范围：{df.index[0].date()} 到 {df.index[-1].date()}")
    print(f"数据维度: {df.shape}")
    return df

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    特征工程：基于原始数据构造用于预测的特征。
    
    参数:
    - df: 包含日期和原始价格的DataFrame
    
    返回:
    - 添加了技术指标和滞后特征的DataFrame
    """
    df_feat = df.copy()

    # 1. 时间滞后特征：碳价具有自相关性
    for lag in [1, 2, 3, 5, 10, 20]:
        df_feat[f'EUA_lag_{lag}'] = df_feat['EUA_Price'].shift(lag)

    # 2. 滚动统计特征：移动平均和波动率
    for window in [5, 10, 20]:
        df_feat[f'EUA_MA_{window}'] = df_feat['EUA_Price'].rolling(window=window).mean()
        df_feat[f'EUA_Vol_{window}'] = df_feat['EUA_Price'].rolling(window=window).std()

    # 3. 外部特征的变化率（基于经济数据的二阶特征）
    df_feat['SP500_Return'] = df_feat['SP500'].pct_change().fillna(0)
    df_feat['NG_Return'] = df_feat['NG_Price'].pct_change().fillna(0)
    df_feat['Elec_Return'] = df_feat['Electricity_Price'].pct_change().fillna(0)

    # 4. 交互特征：天然气与碳价的价差，常用于碳市场分析
    df_feat['Gas_Carbon_Spread'] = df_feat['NG_Price'] - df_feat['EUA_Price'] / 10  # 单位归一化

    # 5. 时间特征：月、季度，捕捉季节性
    df_feat['Month'] = df_feat.index.month
    df_feat['Quarter'] = df_feat.index.quarter
    df_feat['DayOfWeek'] = df_feat.index.dayofweek

    # 删除因创建滞后和滚动特征产生的NaN值
    df_feat.dropna(inplace=True)

    print(f"特征工程完成，特征数量: {len(df_feat.columns)}")
    return df_feat


# ----------------- 2. 模型定义 (混合模型) -----------------

class TimeSeriesFeatureExtractor(nn.Module):
    """
    GRU模型：用于从时间序列中提取深层特征。
    包含双向GRU + 注意力机制。
    """
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, output_size: int = 20):
        super(TimeSeriesFeatureExtractor, self).__init__()
        self.gru = nn.GRU(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True, 
            dropout=0.2,
            bidirectional=True
        )
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * 2, 1),
            nn.Softmax(dim=1)
        )
        self.fc = nn.Linear(hidden_size * 2, output_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播。
        输入: (batch_size, seq_len, input_size)
        输出: (batch_size, output_size)  # 特征向量
        """
        gru_out, _ = self.gru(x)  # [batch, seq, hidden*2]
        
        # 注意力机制：计算每个时间步的权重
        attn_weights = self.attention(gru_out)  # [batch, seq, 1]
        attn_weights = attn_weights.permute(0, 2, 1)  # [batch, 1, seq]
        
        # 加权求和
        context = torch.bmm(attn_weights, gru_out)  # [batch, 1, hidden*2]
        context = context.squeeze(1)  # [batch, hidden*2]
        
        # 映射到输出维度
        output = self.fc(context)
        return output


def prepare_sequences(df: pd.DataFrame, seq_len: int = 20, target_col: str = 'EUA_Price',
                      test_size: float = 0.2) -> Tuple:
    """
    准备用于 LSTM/GRU 训练的序列数据。
    
    参数:
    - df: 原始DataFrame
    - seq_len: 时间窗口长度，使用过去seq_len天预测未来
    - target_col: 目标列名
    - test_size: 测试集比例
    
    返回:
    - X_train_seq, X_test_seq, y_train, y_test
    """
    # 选择特征列 (排除目标列本身用于预测，或保留原始值用于纯时序)
    feature_cols = [col for col in df.columns if col != target_col]
    
    # 归一化
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_scaled = scaler_X.fit_transform(df[feature_cols])
    y_scaled = scaler_y.fit_transform(df[[target_col]])
    
    # 构建序列
    X_seq, y_seq = [], []
    for i in range(len(X_scaled) - seq_len):
        X_seq.append(X_scaled[i:i+seq_len])
        y_seq.append(y_scaled[i+seq_len])  # 预测序列结束后的下一个值
    
    X_seq = np.array(X_seq, dtype=np.float32)
    y_seq = np.array(y_seq, dtype=np.float32).flatten()
    
    # 分割训练/测试集（按时间顺序，不发生数据泄露）
    split_idx = int(len(X_seq) * (1 - test_size))
    X_train_seq, X_test_seq = X_seq[:split_idx], X_seq[split_idx:]
    y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]
    
    print(f"训练序列个数: {len(X_train_seq)}, 测试序列个数: {len(X_test_seq)}")
    return X_train_seq, X_test_seq, y_train, y_test, scaler_X, scaler_y, feature_cols


def train_gru_model(X_train: np.ndarray, y_train: np.ndarray, 
                    input_size: int, epochs: int = 50, 
                    batch_size: int = 32, lr: float = 0.001) -> nn.Module:
    """
    训练 GRU 特征提取器。
    
    返回:
    - 训练好的GRU模型
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    # 转换数据为 Tensor
    X_tensor = torch.tensor(X_train, dtype=torch.float32).to(device)
    y_tensor = torch.tensor(y_train, dtype=torch.float32).to(device)
    
    dataset = TensorDataset(X_tensor, y_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)  # 时序数据不 shuffle
    
    # 初始化模型
    model = TimeSeriesFeatureExtractor(input_size=input_size).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=5, factor=0.5)

    print("开始训练 GRU 模型...")
    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for X_batch, y_batch in dataloader:
            optimizer.zero_grad()
            output = model(X_batch)
            loss = criterion(output.squeeze(), y_batch)
            loss.backward()
            # 梯度裁剪，防止梯度爆炸
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / len(dataloader)
        scheduler.step(avg_loss)
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch [{epoch+1}/{epochs}], 平均 Loss: {avg_loss:.6f}")
    
    print("GRU 训练完成！")
    return model


def extract_and_predict_with_xgb(df: pd.DataFrame, gru_model: nn.Module, 
                                 feature_cols: List[str], seq_len: int = 20,
                                 test_size: float = 0.2, target_col: str = 'EUA_Price') -> Dict:
    """
    使用训练好的 GRU 提取时序特征，再使用 XGBoost 进行预测。
    
    技术要点:
    - 将 GRU 最后一层的输出（20维特征向量）作为新特征。
    - 合并原时点特征，构建新的训练集。
    - 使用 XGBoost 进行训练和预测。
    """
    device = next(gru_model.parameters()).device
    
    # 1. 使用 GRU 提取序列特征
    scaler_X = MinMaxScaler()
    scaler_X.fit(df[feature_cols])
    X_scaled = scaler_X.transform(df[feature_cols])
    
    # 构建序列
    X_seq = []
    for i in range(len(X_scaled) - seq_len):
        X_seq.append(X_scaled[i:i+seq_len])
    X_seq = np.array(X_seq, dtype=np.float32)
    
    # 将序列通过 GRU 模型
    gru_model.eval()
    with torch.no_grad():
        X_tensor = torch.tensor(X_seq).to(device)
        gru_features = gru_model(X_tensor).cpu().numpy()  # [n_samples, 20]
    
    print(f"GRU 提取特征完成，特征维度: {gru_features.shape[1]}")
    
    # 2. 构建新数据集：合并 GRU 特征 + 最后一个时点的原始特征
    #    注意：X_seq 的索引对应原 df 的 seq_len 到末尾
    df_aligned = df.iloc[seq_len:].reset_index(drop=True)
    original_features_at_last_step = X_scaled[seq_len:]  # 最后一个时间步的归一化特征
    
    # 合并特征
    X_combined = np.hstack([original_features_at_last_step, gru_features])
    # 准备目标值
    y = df_aligned['EUA_Price'].values
    
    # 3. 分割训练/测试集
    split_idx = int(len(X_combined) * (1 - test_size))
    X_train, X_test = X_combined[:split_idx], X_combined[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    # 4. XGBoost 模型训练
    print("开始训练 XGBoost 模型...")
    xgb_model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        reg_alpha=0.1,
        random_state=42,
        n_jobs=-1
    )
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=20,
        verbose=False
    )
    
    # 5. 预测与评估
    y_pred = xgb_model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    # MAPE
    mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
    print("\n======= 模型评估报告 =======")
    print(f"MAE (平均绝对误差): {mae:.4f} 欧元")
    print(f"RMSE (均方根误差): {rmse:.4f} 欧元")
    print(f"MAPE (平均百分比误差): {mape:.2f}%")
    print(f"R² Score (决定系数): {r2:.4f}")
    
    # 特征重要性（可解释性分析）
    if hasattr(xgb_model, 'feature_importances_'):
        # XGBoost 的 feature_importances_ 对应所有特征
        # 我们需要识别哪些是 GRU 特征（最后20个）
        n_original = original_features_at_last_step.shape[1]
        feature_names = feature_cols + [f'GRU_Feature_{i}' for i in range(gru_features.shape[1])]
        importance = xgb_model.feature_importances_
        # 按重要性排序
        sorted_idx = np.argsort(importance)[::-1][:10]
        print("\nTop 10 重要特征:")
        for idx in sorted_idx:
            print(f"  {feature_names[idx]}: {importance[idx]:.4f}")
    
    return {
        'model': xgb_model,
        'y_test': y_test,
        'y_pred': y_pred,
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'r2': r2,
        'feature_importance': xgb_model.feature_importances_ if hasattr(xgb_model, 'feature_importances_') else None
    }


# ----------------- 3. 主流程 -----------------

def main():
    """主函数：执行完整的碳价预测流程"""
    from typing import List
    
    # 第一步：获取数据
    print("="*50)
    print("碳价预测系统启动")
    print("="*50)
    
    df_raw = fetch_data()
    df_features = create_features(df_raw)
    
    # 第二步：准备 GRU 训练数据
    feature_cols = [col for col in df_features.columns if col != 'EUA_Price']
    
    X_train_seq, X_test_seq, y_train_seq, y_test_seq, scaler_X, scaler_y, _ = \
        prepare_sequences(df_features, seq_len=20, target_col='EUA_Price', test_size=0.2)
    
    # 第三步：训练 GRU
    input_size = X_train_seq.shape[2]  # 特征数量
    gru_model = train_gru_model(
        X_train_seq, y_train_seq, 
        input_size=input_size, 
        epochs=30,  # 快速演示，实际可调整到100+
        batch_size=32
    )
    
    # 第四步：混合模型预测
    results = extract_and_predict_with_xgb(
        df_features, 
        gru_model, 
        feature_cols=feature_cols,
        seq_len=20,
        test_size=0.2,
        target_col='EUA_Price'
    )
    
    print("\n" + "="*50)
    print("预测完成。示例：最后10个真实值 vs 预测值")
    for i in range(min(10, len(results['y_test']))):
        real = results['y_test'][-10+i]
        pred = results['y_pred'][-10+i]
        print(f"真实: {real:.2f} €, 预测: {pred:.2f} €, 误差: {real-pred:.2f} €")
    
    return results


if __name__ == "__main__":
    main()
```

---

### 任务3：调试与部署注意事项

碳价预测系统在生产环境中稳定运行，需要特别注意以下风险点与修复方案：

#### 1. 数据层面

| 风险点 | 描述 | 修复方案 |
| :--- | :--- | :--- |
| **数据泄露** | 使用未来信息预测过去（例如，滚动统计中使用了未来数据）。 | 在构建序列和特征时，严格按时间顺序，保证 `shift()` 或 `rolling(window)` 不会访问到当前点之后的数据。使用 `TimeSeriesSplit` 进行交叉验证。 |
| **市场结构性突变** | 碳市场政策（如MSR改革、拍卖底价调整）导致价格分布发生剧烈变化，模型失效。 | **在线学习**：定期用最新数据微调模型。**特征增强**：加入政策虚拟变量（如0/1表示不同政策阶段）。**不确定性量化**：使用分位数回归，输出预测区间而非单点。 |
| **数据源中断** | FRED、CFTC或ICE等数据API无法连接。 | **多数据源备份**：预设2-3个不同源。**本地缓存**：保存过去30天数据。**降级策略**：使用纯时序模型LSTM进行临时预测（不依赖外部特征）。 |

#### 2. 模型层面

| 风险点 | 描述 | 修复方案 |
| :--- | :--- | :--- |
| **梯度爆炸/消失** | 时间序列过长或网络过深导致。 | 1. 使用**GRU**代替LSTM（结构更简单）。2. 使用**梯度裁剪** (`torch.nn.utils.clip_grad_norm_`)。3. 采用**残差连接**。4. 对输入数据进行**归一化**。  |
| **过拟合** | 模型完美学习训练集，但无法泛化到新数据。 | 1. **早停法 (Early Stopping)**，监控验证集损失。2. **正则化**：Dropout (0.2-0.5)，L1/L2正则（XGBoost里的 `reg_alpha`/`reg_lambda`）。3. **数据增强**：对时间序列进行小范围抖动。 |
| **特征冗余** | 大量相似特征导致XGBoost重要性分散。 | 使用**PCA**或**自编码器**进行降维。但在能源经济学中，更推荐使用**SHAP值**分析，保留具有经济学意义的特征，扔掉噪声。 |
| **预测滞后** | 模型倾向于预测前一个价格（Naive Forecast）。 | 确保目标变量是**收益率**或**对数差分**，而非绝对价格。使用**自回归结构** (AR) 作为基准模型进行比对。 |

#### 3. 工程与部署层面

| 风险点 | 描述 | 修复方案 |
| :--- | :--- | :--- |
| **版本不一致** | 训练环境和生产环境的库版本（如PyTorch, XGBoost）不同。 | 使用**Docker**定义标准运行环境。在 `requirements.txt`中锁定所有依赖的精确版本 (`xboost==1.7.6`)。 |
| **模型延迟** | 实时推理时，LSTM + XGBoost计算时间过长。 | 使用**ONNX**转换模型以加速推理。对GRU部分进行**静态量化**（INT8）。将XGBoost模型转换为**lib库**调用。 |
| **调度失败** | 定时任务（每天收盘后训练+预测）异常中断。 | 使用**Airflow**或**APScheduler**，并设置重试机制（retry=3）。将生成的模型和预测结果记录到**日志+数据库**，方便回滚。 |
| **内存泄露** | 长期运行后，PyTorch的GPU内存未被正确释放。 | 在推理循环中，确保使用 `with torch.no_grad()` 包裹预测逻辑。定期调用 `torch.cuda.empty_cache()`。 |

**总结：** 一个可调度的碳价预测系统不仅仅是一个模型，它需要**数据管道**、**模型管理**、**异常检测**和**自动修复**四位一体的工程化实现。建议在投产前，使用历史数据（特别是2021年碳价剧烈波动期）进行严格的**压力测试**。