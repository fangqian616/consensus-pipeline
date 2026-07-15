# 能源经济学机器学习实战教程

## 教程1：零基础入门教程

### 1.1 安装 Python + Anaconda

**操作**  
访问 [Anaconda官网](https://www.anaconda.com/download) 下载对应操作系统的 Anaconda 安装包（推荐 Python 3.9+ 版本），双击运行并按照默认设置完成安装。安装完成后，打开终端（Windows 下为 Anaconda Prompt，macOS/Linux 为普通终端），输入 `conda --version` 验证。

**原因**  
Anaconda 集成了 Python 解释器、包管理器 conda 以及数百个常用科学计算库，避免手动配置环境的繁琐过程。对于刚接触 Python 的用户，这是最省心的一站式方案。

**预期输出**  
```
conda 23.11.0   # 版本号可能不同，但出现即表示安装成功
```

**常见报错**  
- **“conda 不是内部或外部命令”**：安装时未勾选“Add Anaconda to my PATH environment variable”。解决方法：重新安装时勾选该选项，或手动将 Anaconda 的 Scripts 目录添加到系统环境变量。  
- **“conda... permission denied”**：Mac/Linux 下权限不足。尝试 `sudo conda --version` 或使用 `chmod` 调整安装目录权限。

### 1.2 安装必要库

**操作**  
在终端（或 Anaconda Prompt）中依次执行以下命令：

```bash
conda install pandas scikit-learn xgboost tensorflow keras -c conda-forge
```

如果网络较慢，可先更换为国内镜像源（如清华源）后再安装。

**原因**  
- `pandas`：处理时间序列数据（如电价、负荷）的核心库。  
- `scikit-learn`：提供经典机器学习模型（回归、分类）及评估工具。  
- `xgboost`：梯度提升树算法，在能源预测任务中经常获得最优性能。  
- `tensorflow/keras`：深度学习框架，用于 LSTM 等时序模型搭建（后续教程会用到）。  

**预期输出**  
```
Collecting package metadata (current_repodata.json): done
Solving environment: done
...
Proceed ([y]/n)? y
...
Extracting packages ... done
```

**常见报错**  
- **“CondaHTTPError: HTTP 000 CONNECTION FAILED”**：网络无法访问 conda-forge 默认源。解决方案：配置清华镜像源 `conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/`。  
- **“PackageNotFoundError: xgboost”**：默认 conda 源缺少该包，请务必指定 `-c conda-forge`。

### 1.3 获取能源价格数据

**操作**  
从公开数据源（如 [ENSO](https://data.open-power-system-data.org/time_series/) 或 [Kaggle 上的电力负荷数据集](https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set)）下载 CSV 文件。为演示简便，我们用以下 Python 代码生成模拟的能源需求数据：

```python
import pandas as pd
import numpy as np

# 生成 2020-01-01 到 2023-12-31 的每小时间隔时间序列
dates = pd.date_range(start='2020-01-01', end='2023-12-31', freq='H')
np.random.seed(42)
demand = 100 + 50 * np.sin(np.pi * dates.hour / 24) + 30 * np.sin(2 * np.pi * dates.dayofyear / 365) + np.random.normal(0, 10, len(dates))
df = pd.DataFrame({'datetime': dates, 'demand': demand})
df.to_csv('energy_demand.csv', index=False)
print("数据已保存至 energy_demand.csv")
```

**原因**  
使用真实世界公开发布的数据能更贴近实际分析场景，但教学时模拟数据可避免下载权限、数据清理等干扰。后续可轻松替换为真实数据。

**预期输出**  
```
数据已保存至 energy_demand.csv
```

**常见报错**  
- **“FileNotFoundError: [Errno 2] No such file or directory”**：保存路径权限不足。请使用绝对路径或确认当前工作目录。  
- **“ModuleNotFoundError: No module named 'pandas'”**：说明 pandas 未安装成功，请返回上一步检查。

### 1.4 第一个 ML 模型：XGBoost 预测能源需求

**操作**  
在项目文件夹中创建 `first_model.py`，写入以下代码：

```python
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 读取数据
df = pd.read_csv('energy_demand.csv', parse_dates=['datetime'])

# 构造特征：年、月、日、星期几、小时、是否为周末
df['year'] = df['datetime'].dt.year
df['month'] = df['datetime'].dt.month
df['day'] = df['datetime'].dt.day
df['weekday'] = df['datetime'].dt.weekday
df['hour'] = df['datetime'].dt.hour
df['is_weekend'] = (df['weekday'] >= 5).astype(int)

# 滞后特征：前 1 小时、前 24 小时、前 48 小时的需求
df['lag_1'] = df['demand'].shift(1)
df['lag_24'] = df['demand'].shift(24)
df['lag_48'] = df['demand'].shift(48)

# 删除包含 NaN 的行（由于 lag 引入）
df = df.dropna()

# 定义特征和目标
features = ['year', 'month', 'day', 'weekday', 'hour', 'is_weekend', 'lag_1', 'lag_24', 'lag_48']
X = df[features]
y = df['demand']

# 划分训练集与测试集（按时间顺序，不随机打乱）
split_idx = int(len(X) * 0.8)
X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

# 训练 XGBoost 回归模型
model = xgb.XGBRegressor(n_estimators=200, learning_rate=0.1, max_depth=6, random_state=42)
model.fit(X_train, y_train)

# 预测
y_pred = model.predict(X_test)

# 评估
mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
print(f"MAE: {mae:.2f}, RMSE: {rmse:.2f}")

# 查看特征重要性
importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
print("特征重要性：\n", importances)
```

运行代码：`python first_model.py`

**原因**  
XGBoost 能够自动处理非线性关系和特征交互，在能源预测场景中通常表现优异。我们添加了时间特征和滞后特征，这是时序预测的经典做法。

**预期输出**  
```
MAE: 7.89, RMSE: 10.12
特征重要性：
 lag_24      0.4532
 lag_1       0.2321
 hour        0.1287
 ...
```

（数值会因随机种子略有差异，但滞后 24 小时特征一般最重要）

**常见报错**  
- **“ValueError: The feature names should match...”**：当使用 `shift` 后输入 X 包含 NaN，已删除 NaN 则不会出现。  
- **“xgboost.core.XGBoostError: [19:02:29] /workspace/src/data/...”**：通常是因为数据包含无穷大或非数值。检查 `df.info()` 确认数据类型。

### 1.5 模型评估与结果解读

**操作**  
观察上一步输出的 MAE（平均绝对误差）和 RMSE（均方根误差）。  
- MAE ≈ 7.89 表示平均预测值与实际值的绝对差异约 7.89 个单位（能源需求单位设为 MW 或 MWh）。  
- RMSE ≈ 10.12 说明较大的误差（如极端天气导致的需求尖峰）被平方后更显著，对异常值更敏感。  

结合特征重要性分析：  
- `lag_24`（前 24 小时需求）最重要 → 能源需求存在日周期性。  
- `hour` 和 `lag_1` 重要性较高 → 日内模式明显。  
- `is_weekend` 重要性较低 → 在该模拟数据中，周末效应不明显（实际数据中通常显著）。  

**常见问题**  
- “MAE 是 7.89，平均需求是 100，误差率 8%，算好吗？”  
  回答：对于小时级能源预测，10% 以内的 MAPE（平均绝对百分比误差）可以接受，但工程应用希望将误差控制在 5% 以内。可通过调整特征和超参数改善。

---

## 教程2：进阶实战指南

### 2.1 LSTM 时序预测最佳实践

**操作**  
LSTM 适合捕捉长期依赖关系。以下代码展示一个简单的 LSTM 模型，使用滚动窗口构建样本：

```python
import numpy as np
import pandas as pd
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

# 加载数据
df = pd.read_csv('energy_demand.csv', parse_dates=['datetime'])
data = df['demand'].values.reshape(-1, 1)

# 归一化
scaler = MinMaxScaler(feature_range=(0, 1))
data_scaled = scaler.fit_transform(data)

# 创建序列样本 (look_back=48)
look_back = 48
X_lstm, y_lstm = [], []
for i in range(look_back, len(data_scaled)):
    X_lstm.append(data_scaled[i-look_back:i, 0])
    y_lstm.append(data_scaled[i, 0])
X_lstm, y_lstm = np.array(X_lstm), np.array(y_lstm)
X_lstm = X_lstm.reshape(X_lstm.shape[0], X_lstm.shape[1], 1)  # (samples, timesteps, features)

# 划分
split = int(0.8 * len(X_lstm))
X_train, X_test = X_lstm[:split], X_lstm[split:]
y_train, y_test = y_lstm[:split], y_lstm[split:]

# 构建 LSTM 模型
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(look_back, 1)))
model.add(Dropout(0.2))
model.add(LSTM(units=50))
model.add(Dropout(0.2))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mean_squared_error')

# 训练
history = model.fit(X_train, y_train, epochs=20, batch_size=32, validation_split=0.1, verbose=1)

# 预测与反归一化
y_pred_scaled = model.predict(X_test)
y_pred = scaler.inverse_transform(y_pred_scaled)
y_true = scaler.inverse_transform(y_test.reshape(-1, 1))

# 评估
from sklearn.metrics import mean_absolute_error
print("LSTM MAE:", mean_absolute_error(y_true, y_pred))
```

**最佳实践**  
- **MinMaxScaler 而非 StandardScaler**：对时序数据，MinMaxScaler 能保留 0-1 范围，LSTM 收敛更稳定。  
- **足够的 look_back**：至少覆盖一个完整周期（如 24 小时或 24 * 7 小时）。  
- **使用 Dropout 防止过拟合**：`0.2` 是常用值，能源序列中不宜过高。  
- **监控验证损失**：设置 `EarlyStopping` 回调，避免训练过度。

### 2.2 特征工程技巧

**操作**  
1. **技术指标**：计算滚动均值（MA）、滚动标准差（Bolinger Bands）、动量（价格变化率）。  
2. **滞后特征**：不仅做滞后 1/24/48 小时，还可添加滞后 7 天（168 小时）捕捉星期规律。  
3. **外部变量**：温度、风速（从气象站 API 获取），节假日标记，电价（对需求预测有价值）。  

示例代码（接续原始 df）：

```python
# 滚动均值（过去 24 小时的均值）
df['rolling_mean_24'] = df['demand'].rolling(window=24).mean()
# 动量（当前对前 24 小时的变化率）
df['momentum_24'] = df['demand'].pct_change(periods=24)
# 引入虚拟外部变量：气温（假设获取）
df['temperature'] = ...  # 需通过 API 或公开数据集获得
# 滞后 7 天
df['lag_168'] = df['demand'].shift(168)
```

**原因**  
能源需求受气象、社会活动影响显著，引入外部变量可大幅提升模型泛化能力。滚动统计量能平滑噪声，动量则捕捉趋势变化。

### 2.3 超参数调优 (GridSearch, Optuna)

**操作**  
使用 `Optuna` 自动搜索 XGBoost 最佳参数：

```python
import optuna
import xgboost as xgb
from sklearn.metrics import mean_absolute_error

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 500),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
    }
    model = xgb.XGBRegressor(**params, random_state=42)
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
    y_pred = model.predict(X_test)
    return mean_absolute_error(y_test, y_pred)

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=50)
print("最佳参数:", study.best_params)
print("最佳 MAE:", study.best_value)
```

**常见陷阱**  
- **TimeSeriesSplit**：能源时序必须使用时间顺序切分验证集，不可使用随机交叉验证（会泄露未来信息）。结合 Optuna，可使用 `TimeSeriesSplit` 作为交叉验证器。

### 2.4 部署踩坑指南

| 问题 | 现象 | 解决方案 |
|------|------|----------|
| **模型序列化与版本兼容** | 在服务器加载 `.joblib` 或 `.h5` 文件时报错，因 scikit-learn / keras 版本不同。 | 使用 `pip freeze` 记录依赖版本，在 Docker 中重现相同环境。 |
| **特征对齐** | 线上实时预测时，输入特征顺序或处理方式与训练时不一致。 | 将特征工程封装为 `Pipeline`，部署时序列化整个 Pipeline。 |
| **时间序列的实时特征** | 滞后特征（如 `lag_1`）需要历史数据缓存，否则线上无法计算。 | 使用 Redis 或数据库存储最近 N 条真实值，API 每次请求时拼接。 |
| **吞吐量不足** | 深度模型推理慢，高并发下响应超时。 | 转换为 ONNX 或 TensorRT 加速，或使用异步处理、负载均衡。 |
| **冷启动问题** | 模型上线初期无历史数据，无法计算滞后特征。 | 使用初始默认值（如平均需求）回填，或用规则模型兜底。 |

---

## 教程3：最佳实践清单

### 3.1 代码规范 (PEP 8, 类型注解)

**操作**  
- 遵循 PEP 8：使用 4 空格缩进、行长度 ≤79 字符、函数名小写加下划线。  
- 添加类型注解提高可读性：

```python
from typing import Tuple, Optional
import pandas as pd

def compute_features(df: pd.DataFrame, lookback: int = 48) -> pd.DataFrame:
    """
    构造时间特征和滞后特征。
    :param df: 包含 'datetime' 和 'demand' 列的 DataFrame
    :param lookback: 滞后步长
    :return: 包含新特征的 DataFrame
    """
    # 实现...
```

**原因**  
能源项目通常需要团队协作，清晰的代码风格和类型注解能减少 bug 并加快代码审查。

### 3.2 项目目录结构

推荐结构：

```
energy_prediction/
├── data/
│   ├── raw/                  # 原始 CSV
│   ├── processed/            # 清洗后数据
│   └── external/             # 外部源数据（天气等）
├── notebooks/                # 探索性分析 (EDA)
├── src/
│   ├── features/             # 特征工程模块
│   │   ├── build_features.py
│   │   └── __init__.py
│   ├── models/               # 模型定义与训练
│   │   ├── train.py
│   │   ├── predict.py
│   │   └── __init__.py
│   └── utils/                # 通用工具函数
├── configs/                  # 配置文件（YAML/JSON）
├── scripts/                  # 部署脚本、调度任务
├── tests/                    # 单元测试
│   └── test_features.py
├── experiments/              # MLflow 实验记录
├── requirements.txt
├── Dockerfile
└── README.md
```

### 3.3 实验管理 (MLflow, Weights & Biases)

**操作**  
使用 MLflow 对每一次训练进行记录：

```python
import mlflow
import mlflow.xgboost

with mlflow.start_run():
    mlflow.log_params(params)          # 记录超参数
    mlflow.log_metric("mae", mae)      # 记录评估指标
    mlflow.xgboost.log_model(model, "model")  # 保存模型
    mlflow.log_artifact("features.csv")       # 记录特征文件
```

**原因**  
能源预测项目常需要多次实验调参，手动记录参数和结果容易混乱。MLflow 提供中央追踪，支持可视化对比不同实验的指标，便于复现和回溯。

**推荐**：对于深度模型，使用 Weights & Biases (wandb)，可以自动记录训练曲线、梯度直方图，更容易发现过拟合。

### 3.4 反模式清单 (Anti-patterns)

| 反模式 | 描述 | 正确做法 |
|--------|------|----------|
| **数据泄露** | 计算滞后特征时，训练集和测试集混淆（例如使用未来数据计算滚动均值）。 | 务必按照时间顺序划分，且特征计算只能在数据内部进行，不可跨越切割点。 |
| **忽略可解释性** | 只追求模型精度，不分析预测结果背后的原因，导致业务方不信任。 | 使用 SHAP（SHapley Additive exPlanations）解释特征对预测的贡献，相关论文（如 [Explainable Artificial Intelligence (XAI)](#)）强调查询理解。 |
| **忽视数据漂移** | 模型在训练集上表现好，线上几个月后精度骤降，因为没有监测特征分布变化。 | 定期用统计检验（如 KS 检验）对比线上特征和训练集特征分布；使用 drift 检测工具（如 Evidently AI）。 |
| **单点预测而非区间预测** | 只输出点预测，无法表达不确定性，影响能源调度决策。 | 使用分位数回归（如 XGBoost quantile）或贝叶斯方法输出预测区间。 |
| **过度工程** | 在简单问题上使用深度学习，导致训练成本高、调试复杂。 | 先用线性回归、树模型作为基线，如果基线足够好则无需深度模型。 |
| **安全与隐私忽视** | 直接使用包含用户信息的智能电表数据，违反 GDPR 或当地法规。 | 使用联邦学习（如论文 [Advances and Open Problems in Federated Learning](#)）或差分隐私技术。 |

---

*注：本教程部分概念参考了以下论文的思想：可解释 AI (XAI)、联邦学习、能源系统挑战等。在实际项目中，请根据具体场景选择合适的方法。*