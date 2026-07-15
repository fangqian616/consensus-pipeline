# 教程一：零基础入门教程

## 1. Python + Anaconda 安装  
**操作**：  
访问 [Anaconda 官网](https://www.anaconda.com/products/individual)，下载适合你操作系统的 Anaconda 发行版（推荐 Python 3.9+ 版本）。运行安装程序，勾选“Add Anaconda to my PATH environment variable”（若未勾选，安装后需手动配置 PATH）。  

**原因**：  
Anaconda 集成了 Python 解释器、conda 包管理器以及 Jupyter Notebook 等常用工具，方便管理和切换虚拟环境，避免库版本冲突。  

**预期输出**：  
安装完成后，打开终端（Windows 为 Anaconda Prompt），输入 `python --version` 显示 Python 版本（如 Python 3.9.13），`conda --version` 显示 conda 版本。  

**常见报错**：  
- 报错 `'python' 不是内部或外部命令` → 未将 Anaconda 加入 PATH，重装时勾选或手动添加环境变量。  
- 安装后无法打开 Anaconda Navigator → 尝试以管理员身份运行安装程序，或使用命令行启动 `anaconda-navigator`。  

---

## 2. 必要库安装  
**操作**：  
创建并激活虚拟环境（推荐避免污染 base 环境）：  
```bash
conda create -n energy_ml python=3.9
conda activate energy_ml
```
安装核心库：  
```bash
conda install pandas scikit-learn xgboost jupyter matplotlib seaborn
pip install tensorflow  # 如果 GPU 可用可使用 tensorflow-gpu
pip install keras
```
验证安装：  
```python
import pandas, sklearn, xgboost, tensorflow, keras
print("All imports successful")
```

**原因**：  
- `pandas`：数据处理  
- `scikit-learn`：传统 ML 模型与评价指标  
- `xgboost`：梯度提升树，能源预测常用基线  
- `tensorflow/keras`：深度学习（LSTM）  
- `matplotlib/seaborn`：可视化  

**预期输出**：  
终端逐行安装，最后运行 Python 脚本无报错。  

**常见报错**：  
- 安装 `tensorflow` 时提示 `Could not find a version` → 检查 Python 版本（建议 3.7-3.9），或换用 `conda install tensorflow`。  
- 安装 `xgboost` 失败 → 使用 `pip` 重试，或先安装 `libomp`（macOS）。  

---

## 3. 数据获取（从公开数据源下载能源价格数据）  
**操作**：  
以美国能源信息署（EIA）的电力价格数据为例：  
```python
import pandas as pd

# 直接从 EIA API 获取（需要免费注册获取 API key）
# 这里使用模拟的本地 CSV 示例（真实场景请替换为 API 调用）
url = "https://raw.githubusercontent.com/your-repo/energy_data/main/electricity_prices.csv"
df = pd.read_csv(url, parse_dates=['date'])
df.head()
```
若无 API 条件，可使用 `pandas-datareader` 从 FRED 下载：  
```bash
pip install pandas-datareader
```
```python
import pandas_datareader.data as web
import datetime

start = datetime.datetime(2020, 1, 1)
end = datetime.datetime(2023, 12, 31)
# 能源指数示例（如 WTI 原油价格）
oil = web.DataReader('DCOILWTICO', 'fred', start, end)
oil.head()
```

**原因**：  
公开数据源（EIA、FRED、ENTSO-E）提供高质量、标准化的能源时间序列，适合教学与实验。  

**预期输出**：  
DataFrame 包含日期列和价格/需求列，无缺失值。  

**常见报错**：  
- `URL error` 或无法连接 → 检查网络或使用代理；选择本地数据备份。  
- `ImportError: No module named 'pandas_datareader'` → 使用 `pip install pandas-datareader`。  

---

## 4. 第一个 ML 模型：用 XGBoost 预测能源需求  
**操作**：  
准备数据（特征：气温、节日、滞后价格；目标：次日电力需求）：  
```python
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import numpy as np

# 假设 df 已经包含 'demand','temperature','holiday','lag_price'
X = df[['temperature','holiday','lag_price']].values
y = df['demand'].values

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练 XGBoost 回归模型
model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5)
model.fit(X_train, y_train)

# 预测
y_pred = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"RMSE: {rmse:.2f}")
```

**原因**：  
XGBoost 对表格数据效果优秀，支持缺失值处理，且训练速度快，适合初学者入门。  

**预期输出**：  
模型训练进度条（若 verbose 开启），最终输出 RMSE 值（例如 120.45 MW）。  

**常见报错**：  
- `ValueError: Input contains NaN` → 使用 `df.dropna()` 或填充缺失值。  
- `XGBoostError: does not support categorical features` → 将类别特征（如 holiday）转换为 0/1 数值。  

---

## 5. 模型评估和结果解读  
**操作**：  
绘制预测 vs 真实值散点图，计算更多指标：  
```python
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, r2_score

mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

plt.figure(figsize=(8,6))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
plt.xlabel('Actual Demand')
plt.ylabel('Predicted Demand')
plt.title(f'XGBoost: MAE={mae:.2f}, R2={r2:.3f}')
plt.show()
```

**原因**：  
单一 RMSE 不够直观，R² 解释模型拟合程度，散点图揭示系统性偏差。  

**预期输出**：  
图形显示点大致沿对角线分布，R² > 0.9 说明模型良好。  

**常见报错**：  
- `Matplotlib is currently using a non-GUI backend` → 在代码前添加 `%matplotlib inline`（Jupyter）或切换后端。  
- `Overfitting` 导致 R² 接近 1 但测试误差大 → 简化模型，增加正则化参数 `reg_alpha`/`reg_lambda`。  

---

# 教程二：进阶实战指南  

## 1. LSTM 时序预测最佳实践  
**操作**：  
数据预处理（构造监督学习格式）：  
```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# 读取序列数据（假设单变量）
values = df['demand'].values.reshape(-1,1)
scaler = MinMaxScaler(feature_range=(0,1))
scaled = scaler.fit_transform(values)

def create_sequences(data, lookback=7):
    X, y = [], []
    for i in range(len(data)-lookback):
        X.append(data[i:i+lookback])
        y.append(data[i+lookback])
    return np.array(X), np.array(y)

lookback = 7
X, y = create_sequences(scaled, lookback)
# 按时间顺序划分，不 shuffle（时序数据）
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# LSTM 模型
model = Sequential([
    LSTM(50, activation='relu', return_sequences=True, input_shape=(lookback,1)),
    Dropout(0.2),
    LSTM(50, activation='relu'),
    Dropout(0.2),
    Dense(1)
])
model.compile(optimizer='adam', loss='mse')
history = model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test,y_test), verbose=1)

# 预测并反归一化
pred_scaled = model.predict(X_test)
pred = scaler.inverse_transform(pred_scaled)
true = scaler.inverse_transform(y_test.reshape(-1,1))
rmse = np.sqrt(np.mean((pred - true)**2))
print(f"LSTM RMSE: {rmse:.2f}")
```

**原因**：  
- LSTM 能捕获长期依赖，适用于能源需求/价格序列。  
- 时间序列不能随机打乱，必须按时间顺序划分。  
- 归一化避免 LSTM 梯度爆炸。  

**预期输出**：  
训练 loss 曲线下降，测试 RMSE 通常低于 XGBoost（若数据规律复杂）。  

**常见报错**：  
- `ValueError: Data cardinality is ambiguous` → 检查 X 和 y 长度一致。  
- 训练 loss = nan → 降低学习率（如 `lr=0.001`），检查数据是否有异常值。  
- 过拟合 → 增加 Dropout 率或减少 LSTM 单元数。  

---

## 2. 特征工程技巧  
**操作**：  
生成滞后特征、滚动统计量、外部变量：  
```python
df = df.sort_values('date')  # 确保时间顺序
# 滞后特征
for lag in [1,2,7,14,28]:
    df[f'price_lag_{lag}'] = df['price'].shift(lag)
# 滚动均值与标准差
df['ma_7'] = df['price'].rolling(window=7).mean()
df['std_7'] = df['price'].rolling(window=7).std()
# 日历特征
df['dayofweek'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['is_holiday'] = df['date'].dt.date.isin(holidays).astype(int)  # holidays 需定义
# 外部数据（如温度）直接从其他表 join
df = df.merge(temperature_df, on='date', how='left')
```

**原因**：  
- 能源市场有强自相关性和季节性。  
- 滞后特征捕捉时间依赖；滚动统计量平滑噪声；外部变量（气温、节假日）解释需求变化。  

**预期输出**：  
DataFrame 新增多列，无 NaN 比例过高（建议删除前几行）。  

**常见坑**：  
- 滞后特征导致数据泄露 → 确保仅使用历史信息，且测试集上 shift 时不要用到未来值。  
- 滚动统计量引入未来信息 → 使用 `rolling(..., closed='left')` 或只使用过去的数据。  
- 特征过多导致过拟合 → 结合特征选择（如 SelectKBest 或 SHAP）。  

---

## 3. 超参数调优（GridSearch, Optuna）  
**操作**：  
使用 Optuna 调优 XGBoost（能源需求预测）：  
```python
import optuna
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score

def objective(trial):
    param = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-3, 10.0, log=True),
    }
    model = XGBRegressor(**param, random_state=42)
    score = -cross_val_score(model, X_train, y_train, cv=3, scoring='neg_root_mean_squared_error').mean()
    return score

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)

print("Best params:", study.best_params)
print("Best RMSE:", study.best_value)
```

**原因**：  
- GridSearch 在超参数空间大时效率低，Optuna 使用贝叶斯优化，更快找到更优解。  
- 能源数据通常需要正则化（`reg_alpha`/`reg_lambda`）防止过拟合。  

**预期输出**：  
控制台显示每次试验的分数，最后输出最佳参数组合。  

**常见报错**：  
- Optuna 版本过低 → `pip install optuna --upgrade`。  
- 训练时间过长 → 减小 `n_trials` 或使用 `TPESampler(n_startup_trials=5)`。  
- 和交叉验证配合时时序数据需使用 TimeSeriesSplit → 改用 `TimeSeriesSplit(n_splits=3)`。  

---

## 4. 部署踩坑指南  
**要点**：  
- **模型序列化**：使用 `joblib` 或 `pickle` 保存模型，注意版本兼容（scikit-learn 版本需要相同）。  
- **API 服务**：使用 Flask/FastAPI 封装，示例：  
```python
from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()
model = joblib.load('xgb_demand.pkl')
class InputData(BaseModel):
    temperature: float
    holiday: int
    lag_price: float

@app.post("/predict")
def predict(data: InputData):
    import numpy as np
    pred = model.predict(np.array([[data.temperature, data.holiday, data.lag_price]]))
    return {"predicted_demand": pred[0]}
```
- **延迟与吞吐**：能源预测通常需要批量预测，开启异步模式或使用 TensorFlow Serving。  
- **数据漂移监控**：部署后定期监控特征分布，使用 `alibi-detect` 检测漂移。  

**常见踩坑**：  
- 本地 pickle 模型加载失败 → 尝试使用 `cloudpickle`，或导出 ONNX 格式。  
- API 返回慢 → 使用缓存（`@lru_cache`）或批处理接口。  
- 内存泄漏 → 确保模型预测后不再持有全局引用，或使用进程隔离。  

---

# 教程三：最佳实践清单  

## 1. 代码规范（PEP8, 类型注解）  
**清单**：  
- 使用 4 空格缩进，行长度 ≤ 79 字符。  
- 变量名小写加下划线（`demand_prediction`），类名驼峰（`EnergyModel`）。  
- 函数与类之间空两行，方法之间空一行。  
- 变量与函数添加类型注解：  
```python
def preprocess_data(df: pd.DataFrame, lookback: int = 7) -> Tuple[np.ndarray, np.ndarray]:
    """构造监督学习数据"""
    ...
```  
- 使用 `flake8` 或 `pylint` 自动检查。  

## 2. 项目目录结构  
推荐模板：  
```
energy_ml_project/
├── data/
│   ├── raw/              # 原始下载数据
│   ├── processed/        # 清洗后特征数据
│   └── external/         # 外部数据源
├── notebooks/            # Jupyter 探索分析
├── src/
│   ├── __init__.py
│   ├── data/
│   │   └── make_dataset.py
│   ├── features/
│   │   └── build_features.py
│   ├── models/
│   │   ├── train_model.py
│   │   └── predict_model.py
│   └── visualization/
│       └── visualize.py
├── reports/              # 生成的图表和报告
├── configs/              # YAML 配置文件
├── requirements.txt
└── README.md
```  

## 3. 实验管理（MLflow, Weights&Biases）  
**操作**：  
集成 MLflow 记录参数、指标和模型：  
```python
import mlflow

mlflow.set_experiment("energy_demand_prediction")

with mlflow.start_run():
    params = {'n_estimators': 200, 'max_depth': 5}
    mlflow.log_params(params)
    model = XGBRegressor(**params).fit(X_train, y_train)
    rmse = np.sqrt(mean_squared_error(y_test, model.predict(X_test)))
    mlflow.log_metric("rmse", rmse)
    mlflow.xgboost.log_model(model, "model")
    # 记录特征重要性图
    mlflow.log_artifact("feature_importance.png")
```

**原因**：  
记录实验便于回溯、对比和复现，避免“模型地狱”。  
Weights&Biases 提供云端仪表盘和超参数搜索功能。  

## 4. 反模式清单  
- ❌ **数据泄露**：在特征工程中使用了未来信息（如用未来数据做滚动均值）。  
- ❌ **过拟合小样本**：在能源数据集中使用过于复杂的模型（如大神经网络）而训练集很小。  
- ❌ **忽略时间顺序**：随机打乱时间序列数据进行交叉验证。  
- ❌ **硬编码路径**：将数据路径写在代码中，应使用配置文件或环境变量。  
- ❌ **不做版本控制**：不保存模型、数据和代码快照，导致无法复现。  
- ❌ **忽略异常值**：能源市场常有极端事件（如寒潮、政策突变），直接使用会严重扭曲模型。  
- ❌ **单一指标评价**：仅用 RMSE 忽略预测偏差或业务成本不对称，应同时关注 MAE 和方向准确率。  
- ❌ **不记录日志**：训练信息不打印或保存，遇到错误难以排查。  
- ❌ **无单元测试**：数据处理函数、特征构建函数未测试，导致隐蔽错误。  

---

以上教程涵盖了从零基础到部署的完整路径，融合了能源经济学领域的特殊需求（时序、季节性、外部变量）。建议读者依次完成各教程，并在实际项目中应用最佳实践。