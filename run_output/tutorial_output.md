# 能源经济学机器学习：三大实战教程

## 教程1：零基础入门教程

### 1.1 Python + Anaconda 安装

#### 操作
1. 访问 [Anaconda 官网](https://www.anaconda.com/products/individual) 下载对应操作系统（Windows/macOS/Linux）的安装包。
2. 双击安装程序，按默认选项安装（Windows 用户注意勾选“Add Anaconda to my PATH environment variable”，或安装后手动配置）。
3. 安装完成后，打开终端（Windows 使用 Anaconda Prompt，macOS/Linux 使用 Terminal），输入 `conda --version` 验证。

#### 原因
Anaconda 集成了 Python、常用科学计算库和包管理器 conda，可一键搭建数据科学生态环境，避免手动安装底层依赖（如 NumPy、pandas 的 C 扩展）时的冲突。

#### 预期输出
```
conda 23.11.0
```

#### 常见报错
| 报错 | 原因 | 解决 |
|------|------|------|
| `conda: command not found` | 未将 conda 加入系统 PATH | 执行 `export PATH="$HOME/anaconda3/bin:$PATH"`（Linux/macOS）或重新安装时勾选 PATH 选项 |
| `CondaHTTPError: HTTP 000 CONNECTION FAILED` | 网络代理或镜像源问题 | 配置国内镜像源：`conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/` |

---

### 1.2 必要库安装

#### 操作
在终端中依次执行以下命令（推荐创建独立环境）：
```bash
conda create -n energy_ml python=3.10 -y
conda activate energy_ml
pip install pandas numpy matplotlib scikit-learn tensorflow xgboost jupyter
```

#### 原因
- `pandas`：处理能源价格/需求表格数据。
- `scikit-learn`：提供 train/test split、评估指标、基础模型（如随机森林）。
- `tensorflow/keras`：构建深度学习模型（LSTM）。
- `xgboost`：高性能梯度提升树，非常适用于结构化能源数据。
- `jupyter`：交互式开发环境，便于逐步实验。

#### 预期输出
安装完成后无错误信息，可运行 `python -c "import pandas; print(pandas.__version__)"` 输出类似 `2.1.4`。

#### 常见报错
| 报错 | 原因 | 解决 |
|------|------|------|
| `ERROR: Could not install packages due to an OSError: [Errno 28] No space left on device` | 磁盘空间不足 | 清理缓存：`conda clean -all` 或更换更大的磁盘分区 |
| `ImportError: libcublas.so.x.x: cannot open shared object file` | GPU 版 TensorFlow 与 CUDA 版本不匹配 | 改用 CPU 版：`pip install tensorflow-cpu` |

---

### 1.3 数据获取（从公开数据源下载能源价格数据）

#### 操作
使用 `pandas-datareader` 从 FRED（美联储经济数据）获取美国每周天然气价格（Henry Hub）：
```python
import pandas_datareader.data as web
import datetime

start = datetime.datetime(2010, 1, 1)
end = datetime.datetime(2023, 12, 31)
# FRED 代码: 'DHHNGSP' 为 Henry Hub 天然气现货价格
df = web.DataReader('DHHNGSP', 'fred', start, end)
df.to_csv('natural_gas_price.csv')
print(df.head())
```

#### 原因
FRED 提供免费且权威的美国能源价格数据，无需 API 密钥，适合初学者练习时序预测。

#### 预期输出
```
            DHHNGSP
DATE               
2010-01-07     5.52
2010-01-14     5.81
2010-01-21     5.46
2010-01-28     5.31
2010-02-04     5.68
```

#### 常见报错
| 报错 | 原因 | 解决 |
|------|------|------|
| `ImportError: No module named 'pandas_datareader'` | 未安装该库 | `pip install pandas-datareader` |
| `RemoteDataError: Unable to read URL` | 网络无法访问 FRED 服务器 | 检查网络，或使用代理；也可用本地示例数据替代 |
| `KeyError: 'DHHNGSP'` | 数据代码已变更 | 访问 FRED 官网确认最新 Series ID |

---

### 1.4 第一个ML模型：用XGBoost预测能源需求

#### 操作
假设我们已有历史负荷数据（可生成模拟数据），使用 XGBoost 回归模型预测电力需求。

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error

# 生成模拟的电力需求数据（含日期、温度、是否为工作日）
np.random.seed(42)
dates = pd.date_range('2020-01-01', '2023-12-31', freq='H')
n = len(dates)
df = pd.DataFrame({
    'date': dates,
    'temperature': np.random.normal(20, 10, n),   # 模拟温度 (°C)
    'is_weekend': (dates.dayofweek >= 5).astype(int),
    'hour': dates.hour,
    'month': dates.month,
})
# 模拟负荷公式：基础负荷 + 温度效应 + 时间效应 + 噪声
df['load'] = (100 
              + 5 * (df['temperature'] - 20) 
              + 10 * np.sin(2*np.pi * df['hour']/24) 
              + 20 * (df['is_weekend']==False) 
              + np.random.normal(0, 10, n))

# 特征与目标
features = ['temperature', 'is_weekend', 'hour', 'month']
X = df[features]
y = df['load']

# 划分训练集和测试集（按时间顺序）
train_size = int(len(df) * 0.8)
X_train, X_test = X.iloc[:train_size], X.iloc[train_size:]
y_train, y_test = y.iloc[:train_size], y.iloc[train_size:]

# 训练 XGBoost 模型
model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# 预测与评估
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"平均绝对误差 (MAE): {mae:.2f} MW")
```

#### 原因
XGBoost 对特征尺度不敏感、可处理缺失值、内置正则化，在小规模能源数据集上通常比简单线性回归表现更好。

#### 预期输出
```
平均绝对误差 (MAE): 7.89 MW
```

#### 常见报错
| 报错 | 原因 | 解决 |
|------|------|------|
| `ValueError: DataFrame.dtypes for X must be int, float or bool` | 特征中包含非数值列（如日期） | 将日期列排除（或转换为数值特征如 `timestamp`） |
| `xgboost.core.XGBoostError: [09:24:11] ... Check failed: ...` | 数据出现 NaN 或无穷值 | 使用 `df.dropna()` 或 `df.fillna()` 处理缺失值 |

---

### 1.5 模型评估和结果解读

#### 操作
绘制预测值与真实值的对比散点图，并计算 **R²** 和 **MAPE**（平均绝对百分比误差）：
```python
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_absolute_percentage_error

r2 = r2_score(y_test, y_pred)
mape = mean_absolute_percentage_error(y_test, y_pred) * 100

plt.figure(figsize=(8,6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
plt.xlabel('实际负荷 (MW)')
plt.ylabel('预测负荷 (MW)')
plt.title(f'R² = {r2:.3f}, MAPE = {mape:.1f}%')
plt.grid(True)
plt.show()
```

#### 原因
- **R²**：解释模型对目标方差的解释能力，越接近 1 越好（注意时序预测中 R² 可能过于乐观）。
- **MAPE**：衡量预测误差相对于真实值的百分比，适合向业务方解释。

#### 预期输出
一张散点图显示点大致沿对角线分布，标题显示 `R² = 0.912, MAPE = 5.2%`。

#### 常见报错
| 报错 | 原因 | 解决 |
|------|------|------|
| `ValueError: x and y must be the same size` | 预测集长度与实际值不一致 | 确保 `y_pred` 来自 `X_test`，而非全部数据 |
| 图形显示空白 | 未调用 `plt.show()`（Jupyter 外） | 添加 `plt.show()`；或在 Jupyter 中执行 `%matplotlib inline` |

---

## 教程2：进阶实战指南

### 2.1 LSTM时序预测最佳实践

#### 核心要点
1. **数据缩放**：LSTM 对输入尺度敏感，必须使用 MinMaxScaler 或 StandardScaler。
2. **序列化数据**：构造滑动窗口（lookback）作为输入，预测未来一步或多步。
3. **多步预测策略**：递归（Recursive）、直接（Direct）、Seq2Seq 等。

#### 示例代码：单步预测 LSTM
```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense

# 假设已有 df 包含一列 'load'
data = df['load'].values.reshape(-1,1)
scaler = MinMaxScaler(feature_range=(0,1))
scaled_data = scaler.fit_transform(data)

# 创建滑动窗口
def create_sequences(data, lookback=24):
    X, y = [], []
    for i in range(lookback, len(data)):
        X.append(data[i-lookback:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

lookback = 24  # 使用过去24小时预测下一小时
X, y = create_sequences(scaled_data, lookback)
X = X.reshape((X.shape[0], X.shape[1], 1))  # LSTM输入形状: (样本, 时间步, 特征数)

# 构建 LSTM 模型
model = Sequential()
model.add(LSTM(50, activation='relu', return_sequences=True, input_shape=(lookback, 1)))
model.add(LSTM(50, activation='relu'))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

# 训练
model.fit(X, y, epochs=20, batch_size=32, validation_split=0.1, verbose=1)
```

#### 常见踩坑
- **过拟合**：能源时序数据通常噪声大，可增加 Dropout 层或降低 LSTM 单元数。
- **收敛缓慢**：尝试 AdamW 优化器、学习率调度（ReduceLROnPlateau）。
- **预测滞后**：单步 LSTM 天然倾向复制上一步值，可尝试多步直接预测或差分处理。

---

### 2.2 特征工程技巧

#### 2.2.1 滞后特征（Lag Features）
```python
# 创建过去 1, 2, 24 小时的滞后值
for lag in [1, 2, 24]:
    df[f'load_lag_{lag}'] = df['load'].shift(lag)
df = df.dropna()
```

#### 2.2.2 滚动统计量（Rolling Features）
```python
df['load_rolling_mean_7'] = df['load'].rolling(window=7).mean()
df['load_rolling_std_24'] = df['load'].rolling(window=24).std()
df = df.dropna()
```

#### 2.2.3 外部变量（Exogenous Variables）
- 天气数据：温度、湿度、风速（影响空调负荷）。
- 日历特征：节假日标志、月份、一周中的星期几。
- 宏观经济：GDP 增速、工业产出指数（中长期预测）。

```python
# 加入节假日特征（使用 holidays 库）
import holidays
us_holidays = holidays.US()
df['is_holiday'] = df['date'].apply(lambda x: x in us_holidays).astype(int)
```

#### 2.2.4 技术指标（适用于价格序列）
```python
# 相对强弱指标 RSI
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=period).mean()
    loss = (-delta.clip(upper=0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = compute_rsi(df['price'])
```

#### 重要性评估
使用 XGBoost 的特征重要性图筛选 Top 特征：
```python
import xgboost as xgb
model = xgb.XGBRegressor()
model.fit(X_train, y_train)
xgb.plot_importance(model, max_num_features=10)
plt.show()
```

---

### 2.3 超参数调优（GridSearch, Optuna）

#### 2.3.1 GridSearchCV（适合小规模搜索）
```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.3]
}
xgb_model = xgb.XGBRegressor(random_state=42)
grid = GridSearchCV(xgb_model, param_grid, cv=3, scoring='neg_mean_absolute_error', verbose=1)
grid.fit(X_train, y_train)
print("最佳参数:", grid.best_params_)
```

#### 2.3.2 Optuna（推荐用于深度学习或大规模搜索）
```python
import optuna
from tensorflow.keras.optimizers import Adam

def objective(trial):
    # 建议超参数
    lstm_units = trial.suggest_int('lstm_units', 32, 128, step=32)
    dropout = trial.suggest_float('dropout', 0.0, 0.5)
    lr = trial.suggest_float('lr', 1e-4, 1e-2, log=True)
    batch_size = trial.suggest_categorical('batch_size', [16, 32, 64])
    
    model = Sequential()
    model.add(LSTM(lstm_units, return_sequences=True, input_shape=(lookback, 1)))
    model.add(Dropout(dropout))
    model.add(LSTM(lstm_units))
    model.add(Dropout(dropout))
    model.add(Dense(1))
    model.compile(optimizer=Adam(learning_rate=lr), loss='mse')
    history = model.fit(X_train, y_train, epochs=10, batch_size=batch_size, 
                        validation_data=(X_val, y_val), verbose=0)
    val_loss = min(history.history['val_loss'])
    return val_loss

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
print("最佳参数:", study.best_params)
```

#### 警告
- **时序交叉验证**：不能使用随机 `Shuffle`，应使用 `TimeSeriesSplit`。
```python
from sklearn.model_selection import TimeSeriesSplit
tscv = TimeSeriesSplit(n_splits=5)
```

---

### 2.4 部署踩坑指南

#### 2.4.1 模型序列化与反序列化
```python
# 保存 XGBoost 模型
model.save_model('energy_model.xgb')
# 加载
loaded_model = xgb.XGBRegressor()
loaded_model.load_model('energy_model.xgb')

# 保存 Keras 模型
model.save('lstm_energy.h5')
# 加载
from tensorflow.keras.models import load_model
loaded_lstm = load_model('lstm_energy.h5')
```

#### 2.4.2 环境一致性（Docker + requirements.txt）
```dockerfile
FROM python:3.10-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY model.pkl /app/
COPY inference.py /app/
CMD ["python", "/app/inference.py"]
```
`requirements.txt` 使用 `pip freeze > requirements.txt` 生成，注意锁定版本。

#### 2.4.3 输入验证与特征对齐
- 部署 API 时，必须对请求数据进行与训练时完全相同的预处理（scaling/特征工程）。
