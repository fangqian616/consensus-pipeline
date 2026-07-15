# 能源经济学机器学习实战三大教程

## 教程1：零基础入门教程
### 从零搭建你的第一个能源需求预测模型

本教程基于以下论文的核心思想：
- **《Selecting critical features for data classification based on machine learning methods》**（Journal of Big Data, 2020）—— 强调特征选择的重要性。
- **《An Introduction to Deep Reinforcement Learning》**（Foundations and Trends® in Machine Learning, 2018）—— 但本教程先从经典XGBoost入手。
- **《The role of hydrogen and fuel cells in the global energy system》**（Energy & Environmental Science, 2018）—— 能源系统数据驱动方法。

---

#### 步骤1：安装Python与Anaconda

**操作：**
1. 访问 [Anaconda官网](https://www.anaconda.com/products/distribution) 下载适用于你操作系统的安装包。
2. 运行安装程序，勾选 **“Add Anaconda to my PATH environment variable”**（Windows）或使用默认选项。
3. 安装完成后，打开终端（macOS/Linux）或 Anaconda Prompt（Windows），输入：
   ```bash
   python --version
   ```
   预期输出：`Python 3.9.x` 或更高版本（如 `3.10.13`）。

**原因：** Anaconda 自带 Python 及最常用的数据科学库，能避免环境冲突。能源经济学中经常需要处理时间序列数据，而 `pandas`、`numpy` 等预装库直接可用。

**常见报错：**
- **`python 不是内部或外部命令`**：未将 Anaconda 加入 PATH。解决方案：在安装时勾选 PATH 选项，或手动添加路径。
- **`conda: command not found`**：未激活 Anaconda。解决方案：关闭终端重新打开，或运行 `source ~/.bashrc` 刷新环境变量。

---

#### 步骤2：安装必要库

**操作：**
1. 创建独立环境（推荐）：
   ```bash
   conda create -n energy_ml python=3.10 -y
   conda activate energy_ml
   ```
2. 安装核心库：
   ```bash
   pip install pandas numpy scikit-learn xgboost matplotlib jupyter
   ```
   可选安装深度学习框架（本教程暂不需要，但可先安装）：
   ```bash
   pip install tensorflow
   # 或 pip install keras tensorflow
   ```

**原因：**
- `pandas`：处理能源时间序列数据（每日电价、负荷等）。
- `scikit-learn`：提供数据预处理、评价指标等工具。
- `xgboost`：梯度提升模型，在能源预测竞赛中表现优异（参考 [Kaggle 全球能源预测竞赛](https://www.kaggle.com/competitions/global-energy-forecasting)）。
- `matplotlib` & `jupyter`：可视化与交互式开发。

**预期输出：**
安装过程中显示进度条，最终无报错。验证：
```bash
pip list | grep -E "pandas|sklearn|xgboost"
```
输出类似：
```
pandas               2.0.3
scikit-learn         1.3.2
xgboost              2.0.3
```

**常见报错：**
- **`pip install` 超时**：使用国内镜像，如：
  ```bash
  pip install -i https://pypi.tuna.tsinghua.edu.cn/simple 包名
  ```
- **`xgboost` 安装失败**：Windows 用户需安装 Visual C++ Redistributable。或使用 `conda install -c conda-forge xgboost`。

---

#### 步骤3：获取能源价格数据

**操作：**
1. 使用公开数据集 **PJM Hourly Energy Consumption Data**（美国独立系统运营商）。
   - 数据来源：https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption
   - 或直接使用 `pandas-datareader` 从 FRED 下载：
     ```python
     import pandas_datareader.data as web
     import datetime
     start = datetime.datetime(2020, 1, 1)
     end = datetime.datetime(2023, 12, 31)
     # 获取电力需求数据（如 ID: INDPRO）
     df = web.DataReader('INDPRO', 'fred', start, end)
     df.head()
     ```
2. 如果 Kaggle 无法访问，可使用模拟数据或本地 CSV。这里我们演示从本地读取 `energy_data.csv`，假设包含 `date` 和 `load` 两列。

**原因：** 能源经济学核心任务之一是预测负荷（需求）或价格。PJM 数据免费且规范，适用于入门。论文《The Future of Energy Supply》（Angewandte Chemie, 2006）强调数据驱动对未来能源系统的重要性。

**预期输出：**
```
        date    load
0 2020-01-01   24567
1 2020-01-02   25678
2 2020-01-03   26789
```

**常见报错：**
- **`pandas-datareader` 未安装**：执行 `pip install pandas-datareader`。
- **网络问题导致无法下载 FRED 数据**：改用本地 CSV。若使用 Kaggle 数据，需先下载数据集并放到 `./data/` 目录。

---

#### 步骤4：第一个ML模型——用XGBoost预测能源需求

**操作：**
1. 加载数据并进行基本预处理：
   ```python
   import pandas as pd
   import numpy as np
   from xgboost import XGBRegressor
   from sklearn.model_selection import train_test_split
   from sklearn.metrics import mean_absolute_error

   # 读取数据（假设已有 energy_data.csv）
   df = pd.read_csv('energy_data.csv', parse_dates=['date'])
   df['hour'] = df['date'].dt.hour
   df['dayofweek'] = df['date'].dt.dayofweek
   df['month'] = df['date'].dt.month
   df['lag_1'] = df['load'].shift(1)
   df = df.dropna()

   features = ['hour', 'dayofweek', 'month', 'lag_1']
   X = df[features]
   y = df['load']

   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
   ```
2. 训练XGBoost模型：
   ```python
   model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
   model.fit(X_train, y_train)
   ```
3. 预测并评估：
   ```python
   y_pred = model.predict(X_test)
   mae = mean_absolute_error(y_test, y_pred)
   print(f'MAE: {mae:.2f} MW')
   ```

**原因：** XGBoost 结构简单、鲁棒性强，适合作为入门模型。时间滞后特征（lag_1）是能源负荷预测的经典技巧，参考《Selecting critical features for data classification based on machine learning methods》（该文虽针对分类，但特征选择思想通用）。

**预期输出：**
```
MAE: 523.47 MW
```
进一步可视化：
```python
import matplotlib.pyplot as plt
plt.figure(figsize=(12,5))
plt.plot(y_test.values[:100], label='True')
plt.plot(y_pred[:100], label='Predicted')
plt.legend()
plt.show()
```

**常见报错：**
- **`ValueError: could not convert string to float`**：日期列未正确解析。确保 `parse_dates` 参数正确，或使用 `df['date'] = pd.to_datetime(df['date'])`。
- **`shuffle=False` 导致时间泄露**：时间序列不能随机打乱，这里用 `shuffle=False` 保留顺序。若验证集不在时间上一致，可能出现负延迟，需改用时间序列交叉验证。

---

#### 步骤5：模型评估与结果解读

**操作：**
1. 计算更多指标：
   ```python
   from sklearn.metrics import mean_squared_error, r2_score
   rmse = np.sqrt(mean_squared_error(y_test, y_pred))
   r2 = r2_score(y_test, y_pred)
   print(f'RMSE: {rmse:.2f} MW, R²: {r2:.3f}')
   ```
2. 特征重要性分析（可解释性，呼应论文《Explainable Artificial Intelligence (XAI)》, Information Fusion, 2019）：
   ```python
   import xgboost as xgb
   xgb.plot_importance(model, importance_type='weight')
   plt.title('Feature Importance')
   plt.show()
   ```
3. 残差分析：
   ```python
   residuals = y_test - y_pred
   plt.scatter(y_pred, residuals, alpha=0.5)
   plt.axhline(y=0, color='r', linestyle='--')
   plt.xlabel('Predicted')
   plt.ylabel('Residual')
   plt.show()
   ```

**原因：** 单一 MAE 不足以判断模型好坏，需结合 RMSE（惩罚大误差）、R²（解释方差）。特征重要性可判断哪些变量贡献大（如 lag_1 通常最重要），残差分析检验是否异方差或存在系统偏差。

**预期输出：**
```
RMSE: 678.12 MW, R²: 0.894
```
- 特征重要性图：`lag_1` 最高，其次 `hour`。
- 残差图：点随机分布在零线附近，无明显模式。

**常见报错：**
- **`plt.show()` 不显示图形**：在 Jupyter 中需添加 `%matplotlib inline`，或在代码最后调用 `plt.show()`。
- **`R²` 为负**：模型比简单均值更差，原因可能是特征不足或过拟合。可尝试增加 `max_depth`、使用更多滞后特征。

---

### 教程1小结
你已经完成了从环境安装到第一个能源需求预测模型的完整流程。记住：入门阶段不必追求完美指标，理解每一步的“为什么”更重要。论文中提到的**特征选择**和**可解释性**将成为你后续优化的方向。

---

## 教程2：进阶实战指南
### 面向有基础的能源经济学机器学习实践者

基于论文《Advances and Open Problems in Federated Learning》（Foundations and Trends® in ML, 2020）、《An Introduction to Deep Reinforcement Learning》（2018）、《Toward Causal Representation Learning》（Proceedings of the IEEE, 2021）等提出的前沿思想，本指南聚焦三大实战模块。

---

#### 1. LSTM时序预测最佳实践

**背景：** 能源负荷/价格具有强时序依赖性和非线性特征。论文《The Science of Wind Energy》（Science, 2019）中指出，可再生能源的间歇性需要复杂时间序列模型。LSTM 可捕捉长短期依赖。

**最佳实践代码：**
```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# 数据准备（以单变量负荷为例）
df = pd.read_csv('energy_data.csv', parse_dates=['date'], index_col='date')
data = df['load'].values.reshape(-1, 1)
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data)

def create_sequences(data, lookback=24):
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

lookback = 48  # 用过去48小时预测下一小时
X, y = create_sequences(scaled_data, lookback)
X = X.reshape((X.shape[0], X.shape[1], 1))  # 增加特征维度

# 划分训练/测试（保留时间顺序）
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# 构建模型
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(lookback, 1)))
model.add(Dropout(0.2))
model.add(LSTM(units=50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(units=1))

model.compile(optimizer='adam', loss='mean_squared_error')
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(X_train, y_train, 
                    validation_data=(X_test, y_test),
                    epochs=100, batch_size=32,
                    callbacks=[early_stop],
                    verbose=0)

# 反标准化预测结果
y_pred_scaled = model.predict(X_test)
y_pred = scaler.inverse_transform(y_pred_scaled)
y_true = scaler.inverse_transform(y_test.reshape(-1,1))

# 评估
from sklearn.metrics import mean_absolute_error
print(f'LSTM MAE: {mean_absolute_error(y_true, y_pred):.2f}')
```

**关键要点：**
- **lookback 长度**：根据能源周期选择（电力可选用24h/48h/168h）。
- **归一化**：LSTM 对尺度敏感，必须归一化。
- **Dropout**：防止过拟合，尤其在训练数据少时。
- **EarlyStopping**：避免无意义训练，节省时间。
- **验证集划分**：严格按时间顺序，不能随机。

**常见坑：**
- **未正确处理时间戳**：确保 `index_col='date'`，且无重复索引。
- **形状错误**：LSTM 输入需 `(samples, timesteps, features)`，单变量时特征维度为1。
- **过拟合**：若训练 loss 持续下降，验证 loss 上升，减少 `units` 或增加 `Dropout`。

---

#### 2. 特征工程技巧

**背景：** 论文《Selecting critical features for data classification based on machine learning methods》（Journal of Big Data, 2020）指出，特征选择可提升模型泛化性。在能源预测中，除基础时间特征外，外部变量和滞后特征至关重要。

**技巧1：滞后特征与滚动统计**
```python
def add_lag_features(df, target_col='load', lags=[1,24,48,168]):
    for lag in lags:
        df[f'lag_{lag}'] = df[target_col].shift(lag)
    # 滚动均值
    df['rolling_mean_24'] = df[target_col].rolling(window=24).mean().shift(1)
    df['rolling_std_24'] = df[target_col].rolling(window=24).std().shift(1)
    df['min_24h'] = df[target_col].rolling(window=24).min().shift(1)
    df['max_24h'] = df[target_col].rolling(window=24).max().shift(1)
    return df.dropna()
```

**技巧2：技术指标（类似股票市场，但用于能源价格）**
- 相对强弱指标（RSI）：判断价格过度波动。
- 移动平均线（MA10, MA30）：趋势判断。
- 布林带宽度：波动率特征。

```python
def add_technical_indicators(df, price_col='price'):
    df['ma10'] = df[price_col].rolling(10).mean()
    df['ma30'] = df[price_col].rolling(30).mean()
    delta = df[price_col].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    # 布林带
    std20 = df[price_col].rolling(20).std()
    df['bollinger_upper'] = df[price_col].rolling(20).mean() + 2*std20
    df['bollinger_lower'] = df[price_col].rolling(20).mean() - 2*std20
    return df
```

**技巧3：外部变量（气象、节假日）**
- 气温、风速（可免费获取：NOAA GHCND）。
- 节假日哑变量：使用 `holidays` 库。
```python
import holidays
us_holidays = holidays.UnitedStates()
df['is_holiday'] =