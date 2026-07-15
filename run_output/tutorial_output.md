# 能源经济学机器学习实战教程

## 教程1：零基础入门教程

### 1.1 Python + Anaconda 安装

**操作**  
1. 访问 [Anaconda官网](https://www.anaconda.com/products/individual) 下载对应操作系统（Windows/macOS/Linux）的 Individual Edition 安装包。  
2. 双击安装，**务必勾选“Add Anaconda to my PATH environment variable”**（Windows用户）。  
3. 安装完成后，打开终端（Windows：Anaconda Prompt；macOS/Linux：终端），输入 `python --version` 确认安装成功。

**原因**  
Anaconda集成了Python、Jupyter Notebook及数百个常用科学计算库，避免手动逐个安装包时遇到依赖冲突。

**预期输出**  
```
Python 3.9.13
```

**常见报错**  
- `'python' 不是内部或外部命令` → 未将Anaconda加入PATH，重新安装时勾选该选项，或手动添加环境变量。  
- macOS/Linux下提示权限不足 → 使用 `sudo sh Anaconda3-xxx.sh` 安装到 `/opt/anaconda3` 等非用户目录（推荐安装到用户目录 `/home/username/anaconda3` 以避免权限问题）。

### 1.2 必要库安装

**操作**  
在终端（或Anaconda Prompt）中依次执行：
```bash
conda install pandas scikit-learn matplotlib seaborn
pip install xgboost tensorflow keras optuna mlflow
```

**原因**  
- `pandas`：数据处理与时间序列分析核心库。  
- `scikit-learn`：提供标准化、交叉验证、基础模型接口。  
- `xgboost`：梯度提升树，在能源需求预测中表现优异。  
- `tensorflow`/`keras`：深度学习框架，用于LSTM等序列模型。  
- `optuna`：超参数自动调优工具。  
- `mlflow`：实验跟踪与模型管理。  

**预期输出**  
每个安装命令完成后显示 `Successfully installed ...` 或 `# All requested packages already installed.`

**常见报错**  
- `conda: command not found` → 未正确激活Anaconda，尝试用 `conda init` 初始化shell。  
- pip安装时网络超时 → 更换国内镜像源：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple xgboost`。  
- TensorFlow安装后无法导入 → 检查Python版本与TensorFlow版本兼容性（推荐Python 3.8-3.10）。

### 1.3 数据获取（从公开数据源下载能源价格数据）

**操作**  
使用`pandas_datareader`或直接从Kaggle/UCI下载。以下演示从美国能源信息署（EIA）获取电价数据（需免费API Key，或使用法国RTE的公开数据集）。  
简化版：使用`sklearn.datasets`的模拟数据作为起步，但这里给出真实数据获取流程。

```python
# 方法1：利用 yfinance 获取原油期货价格（作为能源价格代理）
import yfinance as yf
import pandas as pd

# 下载WTI原油期货日数据（CL=F）
oil = yf.download('CL=F', start='2018-01-01', end='2023-12-31')
oil.to_csv('oil_prices.csv')
print(oil.head())
```

**原因**  
真实的能源数据（电价、天然气、原油）易于从金融数据接口获取，且具有明显时间序列特征，适合ML建模入门。

**预期输出**  
```
                  Open        High         Low       Close   Volume  Dividends  Stock Splits
Date                                                                                        
2018-01-02  60.419998  60.570000  60.049999  60.330002  601932          0             0
...
```

**常见报错**  
- `ImportError: No module named 'yfinance'` → 执行 `pip install yfinance`。  
- 获取不到数据 → 检查日期格式为 `YYYY-MM-DD`，网络允许访问雅虎财经。  
- 数据为空 → 节假日无交易，尝试调整日期范围。

### 1.4 第一个ML模型：用XGBoost预测能源需求

**操作**  
使用开源数据集“Hourly Energy Consumption”（可从Kaggle下载，或模拟）。以下使用模拟的日用电量数据训练XGBoost回归模型。

```python
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

# 生成模拟数据：日期、温度、假日标记、历史负荷
np.random.seed(42)
dates = pd.date_range('2020-01-01', periods=1000, freq='D')
temp = 20 + 10 * np.sin(2*np.pi * dates.dayofyear / 365) + np.random.normal(0, 2, 1000)
holiday = (dates.dayofweek >= 5).astype(int)  # 周末标记
lag1_load = np.roll(50 + 5 * np.sin(2*np.pi * dates.dayofyear / 365) + temp/10 + np.random.normal(0, 3, 1000), 1)
lag1_load[0] = np.nan

data = pd.DataFrame({
    'date': dates,
    'temp': temp,
    'holiday': holiday,
    'lag1_load': lag1_load,
    'load': 50 + 5 * np.sin(2*np.pi * dates.dayofyear / 365) + temp/10 + np.random.normal(0, 3, 1000)
})
data.dropna(inplace=True)

# 特征与目标
X = data[['temp', 'holiday', 'lag1_load']]
y = data['load']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# 训练XGBoost
model = xgb.XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1)
model.fit(X_train, y_train)

# 预测与评估
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
print(f"MAE: {mae:.2f}, RMSE: {rmse:.2f}")

# 特征重要性
print("Feature importance:", model.feature_importances_)
```

**原因**  
XGBoost能自动处理缺失值、非线性关系，且速度快，非常适合作为机器学习入门模型。

**预期输出**  
```
MAE: 3.21, RMSE: 4.05
Feature importance: [0.12 0.05 0.83]
```

**常见报错**  
- `ValueError: The label must consist of integer labels` → 若分类任务需设置 `objective='binary:logistic'`，回归任务保持默认。  
- 数据含NaNs → 使用 `model.fit(X_train, y_train, verbose=False)`，XGBoost能处理缺失，但建议先填充。  
- `shuffle=False` 忘记设置 → 时间序列不应随机打乱，否则数据泄漏。

### 1.5 模型评估和结果解读

**操作**  
绘制预测与真实值的对比图，并计算误差指标。

```python
import matplotlib.pyplot as plt

plt.figure(figsize=(12,4))
plt.plot(y_test.index, y_test.values, label='Actual')
plt.plot(y_test.index, y_pred, label='Predicted', linestyle='--')
plt.title('Load Prediction - XGBoost')
plt.xlabel('Date')
plt.ylabel('Load (MW)')
plt.legend()
plt.show()
```

**原因**  
可视化能直观发现模型是否捕捉到趋势和周期，误差指标提供量化评价。

**预期输出**  
一张时序对比图，预测曲线基本跟随真实曲线，但在峰值处略有偏差。

**常见报错**  
- 索引不匹配导致绘图错位 → 使用 `y_test.reset_index(drop=True)` 或对齐索引。  
- 中文乱码 → 添加 `plt.rcParams['font.sans-serif'] = ['SimHei']` 和 `plt.rcParams['axes.unicode_minus'] = False`。

---  

## 教程2：进阶实战指南

### 2.1 LSTM时序预测最佳实践

**数据预处理**  
- 使用 `MinMaxScaler` 将数据缩放到 [0,1]，避免梯度爆炸。  
- 构造滑动窗口序列（lookback）。  
- 务必使用 **时间顺序** 划分训练/验证/测试（不能随机抽样）。

**模型结构建议**  
```python
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def build_lstm(lookback, n_features):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=(lookback, n_features)))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model
```

**训练技巧**  
- 使用 `EarlyStopping` 防止过拟合：`callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10)`。  
- 如果数据量很大，采用 `generator` 方式边训练边生成批次，避免内存爆炸。  

**常见坑**  
- 时间序列的差分处理：对于非平稳序列，先做一阶差分（`df['load_diff'] = df['load'].diff()`），预测后再逆差分。  
- 避免使用`shuffle=True`，要保证训练样本按时间顺序送入LSTM。  
- 预测多步（multi-step）时，可使用递归预测、seq2seq或Transformer。

### 2.2 特征工程技巧

| 特征类型 | 示例 | 实现方法 |
|----------|------|----------|
| **时间特征** | 小时、星期几、月份、是否工作日 | `pd.DatetimeIndex.dt.hour` |
| **滞后特征** | lag1, lag7, lag24（小时级） | `df['lag1'] = df['load'].shift(1)` |
| **滚动窗口统计** | 过去7天均值、标准差 | `df['roll_mean7'] = df['load'].rolling(7).mean()` |
| **外部变量** | 温度、风速、GDP增长率 | 从气象站下载或使用API（如OpenWeatherMap） |
| **技术指标** | 能源价格走势的移动平均线、RSI | 参考金融特征工程，用`ta`库（`pip install ta`） |

**注意事项**  
- 滞后特征不能泄露未来信息：只允许使用当前时刻以前的数据。  
- 使用`pandas`的`shift`时注意对齐索引，训练集需删除NaN行。  
- 对于强周期性（如电力负荷），加入正弦/余弦编码（`sin(2π*dayofyear/365)`等）比单纯数值更有效。

### 2.3 超参数调优（GridSearch, Optuna）

**GridSearch（网格搜索）——适用于小规模参数组合**  
```python
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV

tscv = TimeSeriesSplit(n_splits=3)
param_grid = {
    'n_estimators': [50, 100],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.05, 0.1]
}
grid = GridSearchCV(XGBRegressor(), param_grid, cv=tscv, scoring='neg_mean_absolute_error')
grid.fit(X_train, y_train)
print("Best params:", grid.best_params_)
```

**Optuna（贝叶斯优化）——推荐用于深度学习**  
```python
import optuna
import tensorflow as tf

def objective(trial):
    lookback = trial.suggest_int('lookback', 24, 168, step=24)
    units = trial.suggest_categorical('units', [32, 64, 128])
    dropout = trial.suggest_float('dropout', 0.1, 0.4)
    lr = trial.suggest_loguniform('lr', 1e-4, 1e-2)
    
    # 构建模型、训练、返回验证损失
    model = build_lstm(lookback, n_features)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=lr), loss='mse')
    # 使用早停，返回最低val_loss
    history = model.fit(X_train, y_train, validation_data=(X_val, y_val),
                        epochs=50, batch_size=64, verbose=0,
                        callbacks=[tf.keras.callbacks.EarlyStopping(patience=5)])
    return min(history.history['val_loss'])

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=20)
print("Best trial:", study.best_trial.params)
```

**调优通用原则**  
- 时间序列：必须使用 **`TimeSeriesSplit`** 或按时间顺序划分的验证集，不能随机交叉验证。  
- 先粗调后精调：先用少量试验探索范围，再局部精细搜索。  
- 关注 `learning_rate` 与 `n_estimators` 的平衡（XGBoost）或 `batch_size` 与 `lr` 的配合（深度学习）。

### 2.4 部署踩坑指南

**常见问题及解决方案**  

| 问题 | 原因 | 解决 |
|------|------|------|
| 模型文件太大  | 未压缩或保存了完整计算图 | 使用 `model.save('model.keras')` 或 `pickle.dump(model, ...)` 但尽量保存轻量化格式（如ONNX） |
| 预测时特征组装出错  | 生产环境特征的顺序/名称与训练不一致 | 使用 `Pipeline` 封装预处理；保存特征列名清单 |
| 模型漂移（数据分布变化） | 能源模式随季节/政策变化 | 实施定期重训练（每小时/每天），并监控预测误差 |
| 延迟过高  | 模型推理速度慢（如LSTM批量预测） | 使用TensorRT、ONNX Runtime加速；或将模型部署为REST API，通过异步批处理降低延迟 |
| 环境依赖差异  | 开发环境与部署环境Python版本或库版本不一致 | 使用Docker容器化；记录 `requirements.txt` 或使用Conda环境导出 |
| 数据不足或NaN  | 传感器故障或网络中断 | 在API入口做数据校验，若缺失则用最后一刻值填充并打标记；开发备用模型（如用温度替代历史负荷） |

**推荐部署流程**  
1. 将模型导出为ONNX格式（支持跨平台推理）。  
2. 使用Flask/FastAPI封装模型，提供`/predict` POST接口。  
3. 使用Docker构建镜像。  
4. 部署到云服务器或边缘计算节点（如树莓派）并设置定时任务获取新数据。

---  

## 教程3：最佳实践清单

### 3.1 代码规范（PEP8, 类型注解）

**基本规则**  
- 缩进：4个空格（不要用Tab）。  
- 行宽：不超过79字符（PEP8）或100字符（团队约定）。  
- 命名：函数/变量用小写+下划线（`predict_load`）；类用驼峰（`LoadPredictor`）；常量全大写（`MAX_LOOKBACK=168`）。  
- 导入顺序：标准库→第三方库→本地模块，每组用空行隔开。  
- 类型注解：提升代码可读性与IDE支持。  

**示例**  
```python
from typing import List, Optional
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator

class LoadForecaster:
    """电力负荷预测器，支持XGBoost和LSTM。
    
    Parameters
    ----------
    model_type : str, optional
        模型类型，可选 'xgb' 或 'lstm'，默认 'xgb'
    lookback : int, optional
        回看窗口长度，默认 168
    """
    def __init__(self, model_type: str = 'xgb', lookback: int = 168) -> None:
        self.model_type = model_type
        self.lookback = lookback
        self.model: Optional[BaseEstimator] = None
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'LoadForecaster':
        # 训练逻辑
        return self
```

### 3.2 项目目录结构

```
energy-ml-project/
├── data/                     # 数据文件（不提交git）
│   ├── raw/                  # 原始数据
│   └── processed/            # 预处理后的特征
├── notebooks/                # 探索性分析、实验
│   └── 01_eda.ipynb
├── src/                      # 源代码
│   ├── __init__.py
│   ├── features/             # 特征工程模块
│   │   ├── build_features.py
│   │   └── transformers.py
│   ├── models/               # 模型定义与训练
│   │   ├── train_model.py
│   │   └── predict.py
│   └── deploy/               # 部署相关
│       └── api.py
├── tests/                    # 单元测试
│   └── test_features.py
├── configs/                  # 配置文件（YAML/JSON）
│   └── config.yaml
├── models/                   # 保存的模型文件
├── logs/                     # 训练日志
├── requirements.txt          # Python依赖
├── setup.py                  # 安装脚本
├── README.md
└── .gitignore
```

**关键点**  
- 原始数据始终保留在 `data/raw/`，任何预处理产生的派生文件存入 `processed/`，确保可复现。  
- 配置文件与代码分离，方便切换不同场景（如测试/生产）。  
- 使用`pytest`编写测试，至少覆盖特征构造和模型推理函数。

### 3.3 实验管理（MLflow, Weights & Biases）

**使用MLflow跟踪实验**  
```python
import mlflow
import mlflow.xgboost

with mlflow.start_run():
    # 记录参数
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 5)
    
    # 训练模型...
    
    # 记录指标
    mlflow.log_metric("mae", mae)
    mlflow.log_metric("rmse", rmse)
    
    # 保存模型
    mlflow.xgboost.log_model(model, "model")
```

**最佳实践**  
- 每个实验使用唯一标识（如时间戳或git commit hash），便于回溯。  
- 记录：超参数、训练/验证指标、特征工程方式、数据版本（如用DVC）。  
- 使用MLflow Model Registry管理模型版本，标记“生产就绪”的模型。  
- 对于深度学习，配合Weights & Biases（wandb）可实时监控训练过程、损失曲线、学习率变化等。

### 3.4 反模式清单

| 反模式 | 说明 | 正确做法 |
|--------|------|----------|
| ❌ 时间序列打乱后训练 | 造成数据泄漏，未来信息被用于预测过去 | 使用 `TimeSeriesSplit` 或按时间比例划分 |
| ❌ 特征包含未来信息 | 如用明天的价格特征预测明天的负荷 | 只使用已知特征（滞后、天气预测值） |
| ❌ 使用全局归一化 | 对测试集使用训练集统计量归一化后计算指标看似很好，但会引入未来信息 | 先分训练/测试，再在**训练集**上拟合scaler，变换测试集 |
| ❌ 忽略季节性 | 不使用周期特征，模型无法捕捉年/周/日周期 | 加入正弦/余弦编码、滞后周期值 |
| ❌ 超参数调优使用随机CV | 回看窗口导致时间错乱 | 使用 `TimeSeriesSplit` 或按时间顺序的验证集 |
| ❌ 单一指标评价 | 只用MAE，忽略RMSE（对大误差敏感）或MAPE（适用于不同量级） | 同时使用MAE、RMSE、MAPE、R² |
| ❌ 不进行错误分析 | 模型表现差但未深入分析哪些时段/特征导致 | 绘制残差图、按时间段分组计算误差 |
| ❌ 直接部署未版本控制 | 模型更新后无法回滚 | 使用MLflow Model Registry、DVC管理数据和模型版本 |
| ❌ 忽略外部突发事件 | COVID-19期间用电模式剧变，模型未做适应 | 加入政策/事件特征，或对异常值进行标记并训练鲁棒模型 |
| ❌ 过度拟合历史数据 | 使用过多滞后特征或深度过大的树/层 | 应用早停、正则化（L1/L2、dropout）、交叉验证 |

---

**扩展阅读建议**  
- 关于能源领域可解释性：参考 *Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI* （2019）在模型部署后使用SHAP/LIME解释预测结果。  
- 对于跨地区/隐私敏感场景：参考 *Advances and Open Problems in Federated Learning* （2020）思路，可使用联邦学习训练多个电厂的负荷模型。  
- 特征选择方法：参考 *Selecting critical features for data classification based on machine learning methods* （2020）可结合Filter、Wrapper方法筛选非能源直接相关变量。  

以上三大教程覆盖了从零到生产部署的全流程，请按实际业务需求调整数据源和模型复杂度。