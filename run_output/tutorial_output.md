# 能源经济学机器学习实战教程

本教程基于能源经济学领域的经典研究与前沿技术（包括可解释AI、联邦学习、氢能系统、风能预测等），系统讲解从零基础到工程最佳实践的机器学习应用。教程分为三个部分，适合不同层次的读者。

---

## 教程1：零基础入门教程

### 目标
从环境搭建开始，完成第一个能源需求预测模型（XGBoost），掌握数据获取、模型训练与评估的基本流程。

---

### 1. Python + Anaconda 安装

**操作**  
1. 访问 [Anaconda 官网](https://www.anaconda.com/download) 下载对应操作系统的安装包。  
2. 运行安装程序，**务必勾选“Add Anaconda to my PATH environment variable”**（否则需手动配置）。  
3. 安装完成后打开终端（Windows 用 Anaconda Prompt），输入 `conda --version` 验证。

**原因**  
Anaconda 集成了 Python 解释器、包管理器（conda）和常用库，避免手动配置环境，特别适合数据科学新手。

**预期输出**  
```
conda 23.3.1
```

**常见报错**  
- `'conda' 不是内部或外部命令`：未添加环境变量，重新安装并勾选选项，或手动在系统环境变量中添加 Anaconda 的 Scripts 目录。  
- `conda 版本过低`：执行 `conda update conda` 升级。

---

### 2. 必要库安装

**操作**  
在终端中依次执行：
```bash
conda install pandas scikit-learn xgboost
pip install tensorflow keras
```
> 注：tensorflow 和 keras 推荐用 pip 安装避免 conda 版本冲突；若使用 GPU 版本可替换为 `tensorflow-gpu`。

**原因**  
- `pandas`：数据处理与时间序列操作。  
- `scikit-learn`：基础机器学习工具（评估指标、数据分割）。  
- `xgboost`：流行的梯度提升模型，在能源预测中表现优秀。  
- `tensorflow/keras`：用于深度学习（后续教程会用到 LSTM）。  

**预期输出**  
每个库安装完成后会显示 `Successfully installed ...` 或无报错退出。

**常见报错**  
- `CondaHTTPError`：网络问题，更换国内镜像（如清华源）。
- `ERROR: Could not install packages due to an OSError`：权限问题，加 `--user` 参数或用管理员身份运行。  
- `tensorflow` 安装后无法导入：检查 Python 版本是否匹配（推荐 Python 3.7~3.10）。

---

### 3. 数据获取（公开能源价格数据）

**操作**  
从美国能源信息署（EIA）或欧洲输电系统运营商网络（ENTSO-E）下载电力负荷或价格数据。  
示例：使用 `pandas_datareader` 获取 EIA 数据：
```python
import pandas_datareader as pdr
import datetime

# 需要先注册EIA API key（免费）
api_key = "your_eia_api_key"
df = pdr.data.DataReader("ELEC.CONS_US_TOT", "eia", start="2015-01-01", end="2023-12-31", api_key=api_key)
```
若不想注册，也可直接加载本地 CSV（例如从 [Kaggle “Hourly Energy Consumption”](https://www.kaggle.com/datasets/robikscube/hourly-energy-consumption) 下载）。

**原因**  
能源数据通常以时间序列形式发布，公开 API 提供标准化访问方式，免去爬虫编写。

**预期输出**  
一个 `pandas.DataFrame`，索引为时间，列名为指标（如“消费量”）。

**常见报错**  
- `KeyError: 'ELEC.CONS_US_TOT'`：检查 EIA API 的正确 Series ID（EIA 官网查询）。  
- `RemoteDataError: Unable to read URL`：网络问题或 API Key 无效。  
- 本地 CSV 有缺失值：后续用 `df.fillna()` 处理。

---

### 4. 第一个ML模型：用XGBoost预测能源需求

**操作**  
假设数据包含两列：时间（datetime）和需求（demand）。我们将构建滞后特征，训练 XGBoost 回归模型。
```python
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# 加载数据
df = pd.read_csv("energy_demand.csv", parse_dates=["timestamp"], index_col="timestamp")
demand = df["demand"]

# 生成滞后特征（前24小时）
for lag in [1, 2, 3, 24]:
    demand[f"lag_{lag}h"] = demand.shift(lag)

# 删除 NaN
data = demand.dropna()
X = data.drop("demand", axis=1)
y = data["demand"]

# 按时间顺序分割（不要打乱）
X_train = X.iloc[:-168]  # 前一个月
y_train = y.iloc[:-168]
X_test  = X.iloc[-168:]  # 最后一周
y_test  = y.iloc[-168:]

# 训练 XGBoost
model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
model.fit(X_train, y_train)

# 预测
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"MAE: {mae:.2f}")
```

**原因**  
- 滞后特征捕捉时间依赖性，是时序预测的关键技巧。  
- 不随机打乱数据，避免时间泄露。  
- XGBoost 对缺失值鲁棒，可以直接使用。

**预期输出**  
```
MAE: 123.45
```
（具体数值取决于数据）

**常见报错**  
- `ValueError: cannot shift with missing index`：检查索引是否为 datetime 且无重复。  
- `XGBoostError: Need to call fit or load_model`：确保模型已 fit。  
- `MAE 极大`：检查数据标准化或异常值（可用 `df.describe()` 查看范围）。

---

### 5. 模型评估和结果解读

**操作**  
绘制实际值与预测值对比图，计算多种指标。
```python
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_percentage_error, r2_score

plt.figure(figsize=(12, 5))
plt.plot(y_test.index, y_test, label="Actual")
plt.plot(y_test.index, y_pred, label="Predicted", alpha=0.7)
plt.legend()
plt.title("Energy Demand Forecast – XGBoost")
plt.show()

mape = mean_absolute_percentage_error(y_test, y_pred) * 100
r2 = r2_score(y_test, y_pred)
print(f"MAPE: {mape:.2f}%")
print(f"R²: {r2:.3f}")
```

**原因**  
- 可视化直观检查模型是否捕捉趋势与周期（如早晚高峰）。  
- MAPE 和 R² 常用于能源行业评估；MAPE 需警惕实际值接近 0 时数值爆炸。  

**预期输出**  
一个趋势接近的对比图，以及指标数值（例如 MAPE 5%~15% 为合理范围）。  

**常见报错**  
- `TypeError: 'numpy.float64' object is not iterable`：检查 y_test 和 y_pred 是否一维。  
- `MAPE = inf`：实际值中有 0，改用 MAE 或 sMAPE。

---

## 教程2：进阶实战指南

### 目标
掌握 LSTM 时序预测的最佳实践、高级特征工程、超参数调优及模型部署要点。

---

### 1. LSTM时序预测最佳实践

**操作**  
使用 Keras 构建 LSTM 模型，注意数据标准化、序列生成器、状态管理。
```python
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import numpy as np

# 数据准备（假设 demand 已加载）
scaler = MinMaxScaler(feature_range=(0,1))
demand_scaled = scaler.fit_transform(demand.values.reshape(-1,1))

# 生成序列（窗口=24）
def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(seq_len, len(data)):
        X.append(data[i-seq_len:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

seq_len = 24
X_seq, y_seq = create_sequences(demand_scaled, seq_len)

# 分割
split = int(0.8 * len(X_seq))
X_train, X_test = X_seq[:split], X_seq[split:]
y_train, y_test = y_seq[:split], y_seq[split:]

# 重塑为 [samples, timesteps, features]
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
X_test  = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

# 构建模型
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(seq_len, 1)),
    Dropout(0.2),
    LSTM(50, return_sequences=False),
    Dropout(0.2),
    Dense(1)
])
model.compile(optimizer='adam', loss='mse')

# 训练
history = model.fit(X_train, y_train, epochs=30, batch_size=32, validation_data=(X_test, y_test), verbose=1)

# 预测并逆标准化
pred_scaled = model.predict(X_test)
pred = scaler.inverse_transform(pred_scaled)
true = scaler.inverse_transform(y_test.reshape(-1,1))
```

**原因**  
- LSTM 擅长捕获长期依赖，适合电力负荷（周期性强）。  
- 标准化避免梯度爆炸；`return_sequences=True` 堆叠 LSTM 层。  
- Dropout 防止过拟合。  

**预期输出**  
训练 loss 下降，验证 loss 平稳；预测值量级与实际一致。  

**常见报错**  
- `ValueError: Input 0 of layer "lstm" is incompatible`：检查输入形状（samples, timesteps, features）。  
- `loss = nan`：学习率过大或数据未标准化，降低 `lr` 或设置 `clipnorm`。  
- 预测效果差：尝试不同窗口长度（如 48, 168）或增加神经元。

---

### 2. 特征工程技巧

**操作**  
添加日历特征、天气外部变量、滚动窗口统计量。
```python
# 从时间索引提取特征
df["hour"] = df.index.hour
df["dayofweek"] = df.index.dayofweek
df["month"] = df.index.month
df["is_holiday"] = df.index.isin(us_holidays)  # 需预先定义节假日列表

# 滞后特征与滚动统计
df["lag_1h"] = df["demand"].shift(1)
df["lag_24h"] = df["demand"].shift(24)
df["rolling_mean_7d"] = df["demand"].rolling(window=168).mean().shift(1)  # 7天滚动
df["rolling_std_24h"] = df["demand"].rolling(window=24).std().shift(1)

# 外部变量（温度、风速等）
df = pd.merge(df, weather_data, left_index=True, right_index=True, how="left")
```

**原因**  
- 能源需求与时间模式（早晚、工作日/周末、季节）强相关。  
- 滚动统计捕捉近期趋势和波动性。  
- 室外温度是电力负荷（尤其制冷/制热）的关键解释变量。  
- 注意滞后特征必须使用**过去**值，避免未来信息泄露。  

**预期输出**  
特征数量增加，模型性能提升（MAE 下降 5%~20%）。  

**常见报错**  
- `KeyError`：检查天气数据时间索引对齐。  
- 引入未来信息：滚动窗口 `shift(1)` 确保只包含历史。  
- 多重共线性：LSTM 和树模型对共线性不敏感，但线性模型需注意。

---

### 3. 超参数调优（GridSearch, Optuna）

**操作**  
使用 Optuna 自动调参（适用于 XGBoost 和 LSTM）。
```python
import optuna
import xgboost as xgb

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000, step=100),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0)
    }
    model = xgb.XGBRegressor(**params, early_stopping_rounds=10)
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    pred = model.predict(X_val)
    return mean_absolute_error(y_val, pred)

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
best_params = study.best_params
```

**原因**  
- 调参能显著提升性能，尤其 `learning_rate` 和 `n_estimators` 需平衡。  
- Optuna 使用 Tree-structured Parzen Estimator (TPE) 比 GridSearch 高效。  

**预期输出**  
最优参数及对应的最佳 MAPE。  

**常见报错**  
- `optuna.exceptions.TrialPruned`：设置 `timeout` 或减少 `n_trials`。  
- 验证集过小导致不稳定：使用时间序列交叉验证（TimeSeriesSplit）。  
- LSTM 调参注意 epochs 和 batch_size 配合，避免训练时间过长。

---

### 4. 部署踩坑指南

**操作**  
将模型保存为 `.pkl` 或 `.h5`，使用 Flask 封装成 REST API。
```python
import joblib
from flask import Flask, request, jsonify

app = Flask(__name__)
model = joblib.load("xgb_demand.pkl")   # 或 keras.models.load_model()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    # 预处理（特征构建、标准化等）
    features = preprocess(data['timestamp'])
    pred = model.predict(features)
    return jsonify({'forecast': pred[0]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**踩坑点**  
1. **依赖环境不一致**：使用 Docker 打包 Python 环境（`FROM python:3.8-slim`）。  
2. **预处理差异**：训练时的 scaler 必须 joblib 保存并在 API 中加载。  
3. **请求延迟**：LSTM 推理较慢，可使用 ONNX 或 TensorRT 加速。  
4. **时序状态维护**：LSTM 有状态预测时需小心滑动窗口，避免重复加载历史。  
5. **监控与日志**：添加 Prometheus 指标（预测值、模型版本、异常检测）。  

**预期输出**  
API 返回 JSON 预测值，postman 测试通过。  

**常见报错**  
- `ModuleNotFoundError`：requirements.txt 遗漏库（如 `xgboost`）。  
- `ValueError: feature_names mismatch`：预测输入特征顺序需与训练时完全一致（使用 `pd.DataFrame` 并保证列顺序）。

---

## 教程3：最佳实践清单

### 目标
建立标准化代码规范、项目结构、实验记录与常见反模式，帮助团队协作与可复现研究。

---

### 1. 代码规范（PEP8, 类型注解）

**PEP8 核心要点**  
- 缩进使用 4 个空格，不要混用 Tab。  
- 行长度 ≤ 79（文档/注释）或 99（代码）。  
- 导入按标准库、第三方、本地模块分组，每个组空一行。  
- 变量命名：`lower_case_with_underscores`；类名 `CapWords`；常量 `ALL_CAPS`。  

**类型注解示例**  
```python
from typing import List, Optional
import pandas as pd

def load_data(path: str, start_date: Optional[str] = None) -> pd.DataFrame:
    """Load energy consumption data."""
    df = pd.read_csv(path, parse_dates=['timestamp'], index_col='timestamp')
    if start_date:
        df = df[df.index >= start_date]
    return df

def create_lag_features(df: pd.DataFrame, cols: List[str], lags: List[int]) -> pd.DataFrame:
    for col in cols:
        for lag in lags:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
    return df
```

**原因**  
- 类型注解提升代码可读性，IDE 自动补全。  
- 遵循 PEP8 的代码便于同行 review，减少 lint 警告。  

---

### 2. 项目目录结构

推荐结构：
```
energy_project/
├── data/
│   ├── raw/          # 原始数据（不修改）
│   └── processed/    # 清洗后的数据
├── notebooks/        # EDA 与原型实验
├── src/
│   ├── data/         # 数据加载、预处理
│   ├── features/     # 特征工程
│   ├── models/       # 训练脚本、模型定义
│   └── utils/        # 工具函数（日志、评估等）
├── configs/
│   ├── params.yaml   # 超参数配置文件
│   └── paths.yaml    # 路径配置
├── models/           # 保存的模型文件
├── reports/          # 结果图表与报告
├── tests/            # 单元测试
├── requirements.txt
├── setup.py
└── README.md
```

**原因**  
- 分离数据、代码、配置，便于版本控制与复现。  
- `configs/` 集中管理参数，避免硬编码。  
- `tests/` 保证关键函数（如预处理、特征生成）的鲁棒性。  

---

### 3. 实验管理（MLflow, Weights&Biases）

**使用 MLflow 记录实验**  
```python
import mlflow

mlflow.set_experiment("energy_forecast_xgb")
with mlflow.start_run():
    # 记录参数
    mlflow.log_params({"n_estimators": 100, "max_depth": 5})
    
    # 训练模型...
    
    # 记录指标
    mlflow.log_metrics({"mae": mae, "r2": r2})
    
    # 保存模型
    mlflow.xgboost.log_model(model, "model")
    
    # 记录图表
    mlflow.log_figure(plt.gcf(), "actual_vs_pred.png")
```

**原因**  
- 自动追溯每次实验的参数、指标与产物，方便对比。  
- 与团队共享最佳实验。  
- 模型注册中心可管理不同版本。  

**Weights&Biases 替代方案**  
- 使用 `wandb.init()` 并自动记录 PyTorch / TensorFlow 训练曲线。  
- 适合深度学习场景，可视化更直观。  

---

### 4. 反模式清单

| 反模式 | 说明 | 正确做法 |
|--------|------|----------|
| **对时序数据随机打乱** | `train_test_split(X, y, random_state=42)` 会破坏时间顺序，导致未来信息泄漏。 | 使用 `TimeSeriesSplit` 或固定时间分割。 |
| **使用未来信息做特征** | 例如用 `shift(-1)` 或滚动窗口不 `shift()`。 | 所有特征只能依赖历史时刻，必要时用 `shift(1)`。 |
| **在拟合前标准化整个数据集** | `scaler.fit_transform(all_data)` 用了未分离的测试集信息。 | 先分割，再 `fit` 训练集，`transform` 测试集。 |
| **忽视数据泄露** | 在特征工程中使用了整个序列的统计量（如均值）。 | 滚动窗口必须 `shift()`，避免未来数据参与当前计算。 |
| **网格搜索时使用全量数据** | GridSearchCV 内部的交叉验证可能用到了未来。 | 使用 `TimeSeriesSplit` 作为 cv 策略。 |
| **调参时代码与模型耦合** | 参数硬编码在脚本中，不易复现。 | 使用配置文件（YAML/JSON）或实验管理工具。 |
| **单一模型不评估不确定性** | 只输出点预测，忽略置信区间。 | 使用分位数回归、dropout 蒙特卡洛或集成模型。 |
| **忽略可解释性** | 使用黑箱模型而不做任何解释。 | 结合 SHAP 或 LIME，参照《Explainable AI》论文方法。 |
| **不记录数据版本** | 训练后忘记数据来源，无法复现。 | 使用 DVC 或 delta 表记录数据版本。 |
| **部署后不做监控** | 模型上线后性能下降未被发现（概念漂移）。 | 定期回测，监控预测误差与特征分布变化。 |

**原因**  
- 时序预测的常见陷阱会导致模型看似优秀但实际不可用。  
- 遵守最佳实践能提升结果可信度与可复现性，符合《Toward Causal Representation Learning》等研究对稳健性的强调。  

---

> **扩展阅读**：可结合本教程中引用的论文深入理解——例如 《Explainable Artificial Intelligence》指导模型解释，《Advances in Federated Learning》启发分布式能源数据训练，而《Grand challenges in the science of wind energy》和 《The role of hydrogen and fuel cells》则提供了具体的应用场景。