# 三大教程：能源经济学中的机器学习应用

---

## 教程1：零基础入门教程

### 1. Python + Anaconda 安装

#### **操作**
1. 访问 [Anaconda 官网](https://www.anaconda.com/products/individual) 下载对应操作系统（Windows/macOS/Linux）的安装包。
2. 双击安装，选择 **“Just Me”**（推荐）或 **“All Users”**。  
   - Windows 用户务必勾选 **“Add Anaconda to my PATH environment variable”**（否则后续需手动配置）。
3. 安装完成后，打开终端（Windows 搜索 “Anaconda Prompt”），输入：
   ```bash
   conda --version
   ```

#### **原因**
- Anaconda 自带 Python、包管理器 conda 及常用科学计算库，避免手动配置环境变量和依赖冲突。
- 能源数据分析频繁使用 pandas、scikit-learn、TensorFlow 等，Anaconda 提供开箱即用的集成环境。

#### **预期输出**
```
conda 23.x.x
```

#### **常见报错**
- **`conda 不是内部或外部命令`**：未将 Anaconda 添加到 PATH。重新安装时勾选 “Add to PATH”，或手动添加环境变量（Windows：路径 `C:\Users\你的用户名\anaconda3\Scripts`）。
- **`python 版本冲突`**：安装后创建独立环境（见下节）解决。

### 2. 必要库安装

#### **操作**
创建并激活虚拟环境（推荐，避免与系统 Python 冲突）：
```bash
conda create -n energy_ml python=3.9
conda activate energy_ml
```

在新环境中安装核心库：
```bash
pip install pandas scikit-learn tensorflow xgboost matplotlib jupyter
```

#### **原因**
- **pandas**：处理 CSV、Excel 等能源时间序列数据。
- **scikit-learn**：提供数据预处理（标准化、训练-测试拆分）、传统 ML 模型（随机森林等）。
- **TensorFlow/Keras**：构建深度学习模型（LSTM 等）。
- **XGBoost**：梯度提升树，在能源预测竞赛中表现优异。
- **matplotlib**：可视化能源价格/需求曲线。
- **jupyter**：交互式编程，便于探索性数据分析。

#### **预期输出**
无报错，终端返回结束信息。可验证：
```bash
python -c "import pandas; print(pandas.__version__)"
```

#### **常见报错**
- **`ModuleNotFoundError: No module named 'tensorflow'`**：pip 未安装成功。尝试 `conda install tensorflow`（conda 版本更稳定）。
- **`pip install 速度慢`**：使用国内镜像，如 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple 包名`。
- **`numpy 冲突`**：尽量通过 conda 安装，或先升级 numpy：`pip install --upgrade numpy`。

### 3. 数据获取（从公开数据源下载能源价格数据）

#### **操作**
以美国能源信息署（EIA）的电力需求数据为例。  
使用 `pandas-datareader` 从 FRED（联邦储备经济数据）获取 **PJECOWV**（西部电力需求）：
```python
import pandas_datareader.data as web
import datetime

start = datetime.datetime(2015, 1, 1)
end = datetime.datetime(2022, 12, 31)

# PJECOWV：西部电网电力需求（百万千瓦时）
df = web.DataReader("PJECOWV", "fred", start, end)
df.to_csv("energy_demand.csv")
print(df.head())
```

#### **原因**
- FRED、EIA 提供免费、规范的能源时序数据，适合初学者练习。
- 真实数据包含噪声、缺失值，贴近实际工程场景。

#### **预期输出**
```
            PJECOWV
DATE               
2015-01-01   6002.0
2015-01-02   6010.0
...             ...
```
并生成 `energy_demand.csv` 文件。

#### **常见报错**
- **`ImportError: No module named 'pandas_datareader'`**：`pip install pandas-datareader`。
- **`RemoteDataError: Unable to connect to FRED`**：检查网络，FRED 需科学上网或使用国内镜像（如 `web.DataReader(..., data_source='eia')` 需注册 API key）。

### 4. 第一个ML模型：用XGBoost预测能源需求

#### **操作**
基于历史需求预测未来一周的需求（滞后特征）：
```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import xgboost as xgb

# 读取数据
df = pd.read_csv("energy_demand.csv", index_col=0, parse_dates=True)
# 构造滞后特征（前7天）
for i in range(1, 8):
    df[f'lag_{i}'] = df['PJECOWV'].shift(i)
df = df.dropna()

# 划分特征和标签
X = df[[f'lag_{i}' for i in range(1, 8)]]
y = df['PJECOWV']

# 训练集（前80%），测试集（后20%）
split = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]

# 训练XGBoost
model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

# 预测与评估
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
print(f"平均绝对误差 (MAE): {mae:.2f} 百万千瓦时")
```

#### **原因**
- 能源需求具有自相关性，使用滞后变量作为特征简单有效。
- XGBoost 对缺失值鲁棒，无需过多特征工程。

#### **预期输出**
```
平均绝对误差 (MAE): 120.34 百万千瓦时
```
（实际数值因数据而异，但 MAE 应在合理范围内。）

#### **常见报错**
- **`ValueError: The feature names should not contain `lag_1``**（罕见）– 检查列名是否有特殊字符。
- **`XGBoostError: Unknown data type`**：确保 X 和 y 均为数值型浮点数。

### 5. 模型评估和结果解读

#### **操作**
绘制预测 vs 真实值曲线，计算更多指标：
```python
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_percentage_error, r2_score

mape = mean_absolute_percentage_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"MAPE: {mape*100:.2f}%")
print(f"R²: {r2:.3f}")

plt.figure(figsize=(10,5))
plt.plot(y_test.index, y_test.values, label='真实需求')
plt.plot(y_test.index, y_pred, label='预测需求')
plt.title('XGBoost 电力需求预测结果')
plt.xlabel('日期')
plt.ylabel('需求量 (百万千瓦时)')
plt.legend()
plt.show()
```

#### **原因**
- **MAE**：绝对误差平均，直观反映平均偏差。
- **MAPE**：相对误差，便于比较不同量级预测。
- **R²**：模型解释方差的比例，越接近1越好。
- 图形化查看趋势和异常点。

#### **预期输出**
控制台输出类似：
```
MAPE: 2.53%
R²: 0.976
```
并展示叠合曲线图，预测与真实基本重合。

#### **常见报错**
- **`ValueError: x and y must have same first dimension`**：绘图时索引长度不一致，确保 y_test 和 y_pred 对齐（已在测试集中对齐）。
- **`matplotlib 中文乱码`**：添加 `plt.rcParams['font.sans-serif']=['SimHei']` 和 `plt.rcParams['axes.unicode_minus']=False`。

---

## 教程2：进阶实战指南

### 1. LSTM时序预测最佳实践

#### **操作步骤**
1. **数据归一化**：LSTM 对输入尺度敏感，使用 MinMaxScaler 压缩到 [0,1]。
2. **构造滑动窗口监督学习**：将时序数据转换为 `(样本数, 时间步长, 特征数)` 三维数组。
3. **定义模型结构**：LSTM 层数 1~2，Dropout 防止过拟合，Dense 输出层。
4. **优化器与损失**：Adam（学习率 0.001），MAE 或 MSE。
5. **加入早停（EarlyStopping）** 防止训练过拟合。

```python
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# 加载数据和归一化
df = pd.read_csv("energy_demand.csv", index_col=0, parse_dates=True)
scaler = MinMaxScaler()
scaled = scaler.fit_transform(df)

# 创建滑动窗口
def create_sequences(data, seq_length=30):
    X, y = [], []
    for i in range(len(data)-seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length])
    return np.array(X), np.array(y)

X, y = create_sequences(scaled, seq_length=30)
# 时间序列切分：前80%训练，剩余测试
split = int(0.8 * len(X))
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# 构建LSTM模型
model = Sequential([
    LSTM(50, activation='relu', return_sequences=True, input_shape=(30, 1)),
    Dropout(0.2),
    LSTM(50, activation='relu'),
    Dropout(0.2),
    Dense(1)
])
model.compile(optimizer='adam', loss='mae')

# 早停
early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
history = model.fit(X_train, y_train, 
                    validation_split=0.2, 
                    epochs=100, 
                    batch_size=32, 
                    callbacks=[early_stop])

# 逆归一化预测
y_pred = model.predict(X_test)
y_pred_actual = scaler.inverse_transform(y_pred)
y_test_actual = scaler.inverse_transform(y_test)
```

#### **原因**
- LSTM 能捕获时间依赖，适合能源日/周/年周期。
- 早停避免无效训练，节省时间。

#### **常见踩坑**
- **`Input 0 of layer lstm is incompatible with the layer: expected ndim=3, found ndim=2`**：确认输入形状 `(batch, timesteps, features)`，数据 X 应为三维。
- **`ValueError: Cannot feed value of shape (32,) for Tensor ...`**：检查 y shape，标签需 `(batch, 1)` 而非 `(batch,)`，可用 `y.reshape(-1,1)`。
- **训练损失不下降**：调整学习率（`Adam(learning_rate=0.001)`），或增加序列长度。

### 2. 特征工程技巧

#### **技术指标**
能源数据中引入气象特征（温度、湿度）可大幅提升预测精度。  
示例：添加移动平均、指数加权移动平均：
```python
df['MA_7'] = df['PJECOWV'].rolling(window=7).mean()
df['EWMA_14'] = df['PJECOWV'].ewm(span=14, adjust=False).mean()
```

#### **滞后特征**
不仅滞后目标变量，也可滞后外部变量。例如气温滞后 1~3 天影响负荷：
```python
for lag in [1,2,3]:
    df[f'lag_temp_{lag}'] = df['temperature'].shift(lag)
```

#### **外部变量**
使用 API 获取日内天气、节假日指示（周末、公共假期）：
```python
from pandas.tseries.holiday import USFederalHolidayCalendar
cal = USFederalHolidayCalendar()
holidays = cal.holidays(start='2015-01-01', end='2022-12-31')
df['is_holiday'] = df.index.isin(holidays).astype(int)
df['day_of_week'] = df.index.dayofweek  # 0=周一
df['month'] = df.index.month
```

#### **原因**
- 技术指标平滑噪声，揭示趋势。
- 滞后特征反映延迟影响。
- 外部变量消除季节性假相关。

#### **常见踩坑**
- **数据泄露**：使用未来信息（如 `shift(-1)`）构造特征。验证特征时间顺序。
- **缺失值过多**：`rolling().mean()` 会引入 NaN，务必 `dropna()` 或填充。

### 3. 超参数调优（GridSearch, Optuna）

#### **GridSearch（适合小规模）**
```python
from sklearn.model_selection import GridSearchCV
from xgboost import XGBRegressor

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.2]
}
model = XGBRegressor(random_state=42)
gs = GridSearchCV(model, param_grid, cv=3, scoring='neg_mean_absolute_error', n_jobs=-1)
gs.fit(X_train, y_train)
print("最佳参数:", gs.best_params_)
```

#### **Optuna（高效采样）**
```python
import optuna

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 300),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.5, 1.0)
    }
    model = XGBRegressor(**params, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    return mean_absolute_error(y_test, pred)

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
print("最佳参数:", study.best_params)
```

#### **原因**
- GridSearch 暴力枚举，适合参数少。
- Optuna 基于贝叶斯优化，调参更高效，适用于深度学习（如 LSTM 神经元数、学习率、Dropout 率）。

#### **常见踩坑**
- **GridSearch 耗时过长**：先粗粒度搜索，或减少交叉验证折数（cv=2）。
- **Optuna 报错 `TrialPruned`**：使用 `optuna.integration.TFkerasPruningCallback` 实现早期剪枝。

### 4. 部署踩坑指南

#### **模型序列化与版本控制**
```python
import joblib
# 保存模型
joblib.dump(model, "energy_model.pkl")
# 加载模型运行预测时，必须使用相同版本库
loaded_model = joblib.load("energy_model.pkl")
```
**坑点**：scikit-learn、XGBoost 版本不一致导致反序列化失败。解决方案：固定环境版本，使用 Docker 容器部署。

#### **预测延迟与吞吐量**
- 在线预测场景：预计算特征，将模型加载到内存一次，避免每请求重新加载。
- 批量预测：使用 `batch_size` 参数加速推理。
- **常见坑**：深度学习模型加载后首次推理慢（TensorFlow 图优化）。解决方法：在服务器启动时做一次 warm-up 推理。

#### **输入数据预处理一致性**
训练时对特征做了 `MinMaxScaler`，部署时必须使用训练时保存的 scaler 对象，重新定义会得到错误缩放。  
```python
# 保存 scaler
joblib.dump(scaler, "scaler.pkl")
# 预测时加载
scaler = joblib.load("scaler.pkl")
scaled_new = scaler.transform(new_data)
```

#### **API 安全与监控**
- 使用 Flask/FastAPI 封装预测接口。
- 添加输入校验，防止格式错误或注入。
- 记录每次请求的延迟和预测结果，异常时告警。

---

## 教程3：最佳实践清单

### 1. 代码规范（PEP8, 类型注解）

- **命名**：变量 `energy_demand`、函数 `train_model()`、类 `DataLoader`（蛇形/驼峰）。
- **行长度**：≤ 79 字符（文档/注释）或 88（black 格式化工具容忍）。
- **导入顺序**：标准库 → 第三方库 → 本地模块，用空行隔开。
- **类型注解**：提高可读性和静态分析能力。
```python
import pandas as pd
from typing import Tuple, Optional

def create_lagged_features(df: pd.DataFrame, column: str, lags: int = 7) -> pd