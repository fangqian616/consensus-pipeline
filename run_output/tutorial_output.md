# 能源经济学机器学习三大教程

---

## 教程1：零基础入门教程  
**目标读者**：无Python/ML基础，希望用机器学习预测能源价格或需求的学生、研究员或从业者。

---

### 1.1 Python + Anaconda 安装

**操作**：  
- 访问 [Anaconda官网](https://www.anaconda.com/products/individual) 下载对应系统的安装包（推荐Python 3.9+版本）。  
- 双击安装，勾选 **“Add Anaconda to my PATH environment variable”**（可选，便于命令行使用）。  
- 安装完成后，打开 **Anaconda Prompt**（Windows）或终端（Mac/Linux），输入 `conda --version` 验证。

**原因**：  
Anaconda集成Python解释器、包管理器（conda）和常用科学计算库，避免手动安装依赖冲突。

**预期输出**：  
```
conda 23.7.4
```

**常见报错**：  
- `conda 不是内部或外部命令` → 未添加PATH，手动添加或使用Anaconda Prompt。  
- `Python 版本过低` → 安装时选择最新版Anaconda，或之后用 `conda update python`。

---

### 1.2 必要库安装

**操作**：  
在终端/Anaconda Prompt中依次执行：
```bash
conda install pandas scikit-learn tensorflow xgboost -y
pip install keras   # 若tensorflow不包含keras
```

**原因**：  
- `pandas`：处理时间序列数据（能源价格时间表）。  
- `scikit-learn`：基础ML工具（数据处理、评估）。  
- `tensorflow/keras`：深度学习（LSTM）。  
- `xgboost`：树模型，适合表格数据预测。

**预期输出**：  
每个包安装后显示进度和成功信息，最后可输入 `python -c "import pandas; print('ok')"` 检查无报错。

**常见报错**：  
- `CondaHTTPError` → 换国内镜像源：  
  ```bash
  conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
  conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
  ```
- `tensorflow安装后无法import` → 检查Python版本（TensorFlow 2.10+需Python 3.9~3.11）。

---

### 1.3 数据获取（从公开数据源下载能源价格数据）

**操作**：  
使用 **EIA（美国能源信息署）** 公开API获取日度天然气价格。注册免费API密钥后调用：
```python
import pandas as pd
import requests

api_key = "YOUR_API_KEY"   # 在 https://www.eia.gov/opendata/ 注册
url = f"https://api.eia.gov/v2/natural-gas/pri/sum/data/?api_key={api_key}&frequency=daily&data[0]=value&facets[duoarea][]=NUS&sort[0][column]=period&sort[0][direction]=desc&length=1000"
response = requests.get(url)
data = response.json()
df = pd.json_normalize(data['response']['data'])
df['period'] = pd.to_datetime(df['period'])
df = df.sort_values('period').reset_index(drop=True)  # 升序
df.to_csv('gas_prices.csv', index=False)
```

**原因**：  
EIA数据免费、结构化、有长期历史记录，适合入门实验。

**预期输出**：  
- 控制台打印请求状态码200，当前目录生成 `gas_prices.csv` 文件，包含 `period`, `value` 等列。

**常见报错**：  
- `KeyError: 'response'` → API请求失败，检查API密钥或网络。可先用 `print(response.text)` 调试。  
- `pandas.errors.EmptyDataError` → 数据为空，增加 `length` 参数或检查日期范围。

---

### 1.4 第一个ML模型：用XGBoost预测能源需求（替换为价格预测）

既然有价格数据，我们预测**次日天然气价格**。步骤：特征工程 → 训练 → 预测。

```python
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

# 加载数据
df = pd.read_csv('gas_prices.csv', parse_dates=['period'])
df = df.set_index('period')['value'].sort_index()

# 构造滞后特征（前7天价格）
for lag in range(1, 8):
    df[f'lag_{lag}'] = df.shift(lag)
df = df.dropna()

# 特征和标签
X = df.drop(columns='value')
y = df['value']

# 划分（按时间顺序，不用随机）
split = int(len(df) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# 训练XGBoost
model = XGBRegressor(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# 预测
preds = model.predict(X_test)

# 评估
mae = mean_absolute_error(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))
print(f"MAE: {mae:.4f}, RMSE: {rmse:.4f}")
print(f"预测范围：{preds.min():.2f} ~ {preds.max():.2f}，实际范围：{y_test.min():.2f} ~ {y_test.max():.2f}")
```

**原因**：  
- XGBoost对表格时间序列效果良好，且不易过拟合（设置 `max_depth=3` 限制复杂度）。  
- 仅用滞后特征作为简单入门，后续可增加外部变量。

**预期输出**：
```
MAE: 0.2351, RMSE: 0.4162
预测范围：2.10 ~ 4.50，实际范围：1.98 ~ 4.78
```

**常见报错**：  
- `ValueError: could not convert string to float` → 确保 `value` 列为数值型，用 `pd.to_numeric(df['value'], errors='coerce')`。  
- `XGBoostError: [14:53:13] ... Check failed: ...` → 版本不兼容，升级xgboost：`pip install xgboost --upgrade`。

---

### 1.5 模型评估和结果解读

**操作**：  
绘制真实值与预测值对比图：
```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 4))
plt.plot(y_test.index, y_test, label='Actual', color='blue')
plt.plot(y_test.index, preds, label='Predicted', color='red', alpha=0.7)
plt.title('Natural Gas Price Prediction - XGBoost')
plt.xlabel('Date')
plt.ylabel('Price ($/MMBtu)')
plt.legend()
plt.grid(True)
plt.show()

# 特征重要性
importance = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
print("Top-5 important features:")
print(importance.head(5))
```

**原因**：  
可视化直观判断模型是否捕捉趋势；特征重要性分析滞后几天的价格影响最大。

**预期输出**：  
- 一张折线图显示两条曲线大致重合。  
- 控制台输出类似：
  ```
  Top-5 important features:
  lag_1    0.45
  lag_2    0.22
  lag_3    0.12
  lag_7    0.08
  lag_5    0.05
  dtype: float64
  ```

**常见报错**：  
- `ImportError: No module named matplotlib` → 安装：`conda install matplotlib`。  
- 图形窗口不显示 → 在Jupyter中运行或添加 `%matplotlib inline`。

---

## 教程2：进阶实战指南  
**目标读者**：有Python+ML基础，希望在能源时序预测中提升效果并部署。

---

### 2.1 LSTM时序预测最佳实践

**核心要点**：  
1. **数据缩放**：LSTM对输入尺度敏感，用 `MinMaxScaler` 缩放到[0,1]。  
2. **序列构造**：使用 `lookback` 窗口生成监督学习格式（Sample = 过去 n 步特征，Target = 未来一步）。  
3. **状态保持**：`LSTM(stateful=True)` 可在长序列中维持内部状态，需手动重置。

**代码片段**（预测次日电价）：
```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

# 加载电价数据（假设有 'price' 列）
df = pd.read_csv('electricity_prices.csv', parse_dates=['datetime'])
df = df.set_index('datetime')['price'].sort_index()

scaler = MinMaxScaler()
scaled = scaler.fit_transform(df.values.reshape(-1,1))

lookback = 10  # 用过去10小时预测下一小时
X, y = [], []
for i in range(lookback, len(scaled)):
    X.append(scaled[i-lookback:i, 0])
    y.append(scaled[i, 0])
X = np.array(X).reshape((-1, lookback, 1))
y = np.array(y)

# 划分
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# 模型（双层LSTM+Dropout）
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(lookback, 1)),
    Dropout(0.2),
    LSTM(50, return_sequences=False),
    Dropout(0.2),
    Dense(1)
])
model.compile(optimizer='adam', loss='mse')

# 早停法防止过拟合
from tensorflow.keras.callbacks import EarlyStopping
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

history = model.fit(X_train, y_train,
                    validation_data=(X_test, y_test),
                    epochs=100, batch_size=32,
                    callbacks=[early_stop],
                    verbose=1)

# 反缩放预测
pred_scaled = model.predict(X_test)
pred = scaler.inverse_transform(pred_scaled)
true = scaler.inverse_transform(y_test.reshape(-1,1))
```

**预期输出**：第20~30轮早停，loss收敛。预测结果接近真实电价。

**常见踩坑**：  
- LSTM训练慢 → 使用 `CuDNNLSTM`（如果GPU+TensorFlow>=2.6自动优化）。  
- 长期依赖丢失 → 增加 `lookback` 或使用 `Bidirectional LSTM`。  
- 预测值震荡剧烈 → 降低学习率或增加Dropout。

---

### 2.2 特征工程技巧（能源场景）

**1. 技术指标**（类似股票）：  
- `relative_price` = 当日价格 / 7日移动平均。  
- `volatility` = 过去10天价格标准差。  
- `momentum` = 价格一阶差分。  

**2. 滞后特征与滚动窗口**：  
- 多步滞后：`shift(1), shift(2), ..., shift(7)`。  
- 统计特征：`rolling(7).mean()`, `rolling(7).std()`, `rolling(7).skew()`。  

**3. 外部变量**（能源经济学特有）：  
- **天气**：温度、风速（影响风电/光伏出力）、采暖度日（HDD）/制冷度日（CDD）。  
- **日历**：小时、星期几、节假日、是否工作日、季节性虚拟变量。  
- **市场变量**：其他能源价格（天然气 vs 煤炭）、碳排放配额价格、库存数据。  

**代码示例**（整合外部变量）：
```python
def create_energy_features(df, weather_df, carbon_df):
    df = df.copy()
    # 价格技术指标
    df['ma7'] = df['price'].rolling(7).mean()
    df['volatility'] = df['price'].rolling(10).std()
    df['momentum'] = df['price'].diff()
    # 滞后
    for lag in [1,2,3,7,14]:
        df[f'lag_{lag}'] = df['price'].shift(lag)
    # 合并天气
    df = df.merge(weather_df, left_index=True, right_index=True, how='left')
    # 合并碳价
    df = df.merge(carbon_df, left_index=True, right_index=True, how='left')
    # 日历特征
    df['hour'] = df.index.hour
    df['weekday'] = df.index.weekday
    df['month'] = df.index.month
    df['is_holiday'] = df.index.isin(holidays).astype(int)
    return df.dropna()
```

---

### 2.3 超参数调优（GridSearch, Optuna）

**使用Optuna进行贝叶斯优化**（比GridSearch高效）：
```python
import optuna
from xgboost import XGBRegressor
from sklearn.model_selection import TimeSeriesSplit

def objective(trial):
    params = {
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'learning_rate': trial.suggest_loguniform('learning_rate', 0.01, 0.3),
        'subsample': trial.suggest_uniform('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_uniform('colsample_bytree', 0.6, 1.0),
        'gamma': trial.suggest_loguniform('gamma', 1e-8, 1.0),
        'reg_alpha': trial.suggest_loguniform('reg_alpha', 1e-8, 10),
        'reg_lambda': trial.suggest_loguniform('reg_lambda', 1e-8, 10),
    }

    # TimeSeriesSplit确保时序顺序
    tscv = TimeSeriesSplit(n_splits=3)
    mae_scores = []
    for train_idx, val_idx in tscv.split(X):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        model = XGBRegressor(**params, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], early_stopping_rounds=20, verbose=False)
        pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, pred)
        mae_scores.append(mae)
    return np.mean(mae_scores)

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
print("Best params:", study.best_params)
print("Best MAE:", study.best_value)
```

**预期输出**：Optuna自动打印每次试验，最终输出最优参数和MAE。

---

### 2.4 部署踩坑指南

**1. 模型序列化**（避免 `pickle` 跨版本问题）：
```python
import joblib
joblib.dump(model, 'model.pkl')   # 推荐
# 或使用专用格式：model.save_model('xgb_model.json')
```

**2. API服务**（Flask + Docker最小示例）：  
```python
# app.py
from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load('model.pkl')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json['features']
    features = np.array(data).reshape(1, -1)
    pred = model.predict(features)[0]
    return jsonify({'prediction': float(pred)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

**3. 踩坑常见问题**：  
- **特征对齐错误**：训练时的列顺序必须与推理请求一致。建议序列化保存 `feature_names`。  
- **时间特征实时计算**：确保服务端系统时区统一（UTC+0），用 `pytz` 处理。  
- **内存泄漏**：每个请求重新加载模型 → 改为全局加载一次。  
- **并发问题**：Flask默认单线程，部署用 `gunicorn -w 4 app:app` 或多worker。

---

## 教程3：最佳实践清单  
**目标**：建立可重现、易维护的能源ML项目规范。

---

### 3.1 代码规范（PEP8, 类型注解）

**PEP8关键点**：  
- 缩进4空格，行长≤79字符（文档/注释≤72）。  
- 函数、变量用小写+下划线；类用CapWords。  
- 常量全大写（如 `API_KEY`）。

**