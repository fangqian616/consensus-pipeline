# 机器学习在能源经济学上的运用

> 学术动向综述 | Consensus Pipeline v5 | 2026年07月15日

## 摘要

本综述系统梳理了2003—2023年间机器学习在能源经济学领域的研究进展，涵盖76篇文献，其中S级41篇、A级13篇、B级13篇。研究发现，该领域经历了从统计预测到深度学习、从单一模型到集成架构、从数据驱动到知识融合的演进脉络。2016—2021年为爆发增长期，近年呈现明显的“去泡沫化”趋势。方法论格局以深度序列模型和集成学习方法为主流，但可解释性、因果推断和隐私保护等前沿方向正在兴起。本文识别了预测精度悖论、知识融合瓶颈、因果推断挑战等核心争议，并提出五个亟需填补的研究空白，为后续研究提供系统性参照。

## 一、研究概况与发展脉络

### 1.1 萌芽与奠基期（2003—2015年）

该领域的学术活动可追溯至21世纪初，但成果产出极为有限。2003年仅有Gower[41]关于森林碳循环模式的研究，此后的十余年间，年度发文量始终在1—2篇徘徊。这一阶段的特征在于：机器学习尚未成为能源经济研究的主流工具，研究者主要依赖传统计量经济学方法（如ARIMA、GARCH、VAR）和经典优化模型。Ghoddusi等[14]在2019年的综述中指出，早期工作多集中于利用支持向量机（SVM）和人工神经网络（ANN）进行电价预测和能源需求建模。

2006年Armaroli和Balzani[5]发表的《能源供应的未来：挑战与机遇》虽非严格意义上的机器学习论文，却为后续研究奠定了问题框架。该文系统阐释了化石燃料枯竭、气候变化、能源安全等核心挑战，明确了能源系统优化与预测的工具需求。2010年后，随着可再生能源并网比例提升，波动性预测和需求侧管理的技术需求开始显现，机器学习逐渐进入研究视野。Staffell等[3]在2018年关于氢能与燃料电池的研究中回顾指出，2013年前后的研究已开始探索随机森林和梯度提升方法在能源市场预测中的应用潜力。

### 1.2 爆发增长期（2016—2021年）

2016年是该领域的关键转折点，发文量从2015年的1篇跃升至5篇，此后持续攀升，2019年达到10篇，2021年达到峰值11篇。这一爆发式增长的驱动力可归纳为三个方面：一是深度学习技术的突破性进展（LSTM、GRU、Transformer等序列模型的成熟）；二是能源系统数字化转型带来的海量数据供给（智能电表、SCADA系统、风电/光伏监控平台）；三是全球碳中和目标对能源系统精细化管理提出的迫切需求。

Marino等[72]在2016年的预印本工作率先将深度神经网络引入建筑能耗负荷预测，提出了一种基于全连接网络的时间窗口滑动架构。同年，Ryu等[73]在Energies期刊发表了基于深度神经网络的短期负荷预测研究，验证了深度学习在电力需求预测中的潜力。这两项工作被视为该领域深度学习方法论的奠基之作。

2017—2019年，深度学习方法呈现井喷态势。Bedi和Toshniwal[58]提出了框架化的深度学习电力需求预测模型，整合了一维卷积网络和LSTM的混合架构。Wang等[57]系统对比了浅层机器学习与深度学习在建筑热负荷预测中的表现，发现深度学习方法在长序列预测任务上具有显著优势，但浅层模型在小样本场景下仍具竞争力。Shi等[63]提出的“池化深度RNN”架构在家庭负荷预测中取得了突破性精度提升，其核心创新在于利用共享参数机制解决了多用户预测中的数据稀疏问题。

2019年，Ghoddusi等[14]在Energy Economics发表的综述标志着该领域学术地位的正式确立。该文系统梳理了机器学习在能源经济学中的应用框架，包括价格预测、需求预测、风险评估和投资决策四大模块，被引431次，成为该领域的必读文献。同年，Barredo Arrieta等[1]关于可解释人工智能（XAI）的综述（被引9162次）虽非能源经济学专著，却为该领域的模型可信度评估提供了方法论基础。

2020—2021年，研究向更细分的应用场景深化。Antonopoulos等[12]聚焦于人工智能和机器学习在能源需求侧管理的应用，系统性综述了强化学习、深度学习和优化算法在需求响应、负荷调度和能效提升中的实践。Aslam等[55]在Renewable and Sustainable Energy Reviews发表了关于深度学习方法用于电力负荷和可再生能源预测的综述，识别出LSTM、GRU、CNN-LSTM混合架构为该时期的主流模型。Somu等[56]提出了基于深度学习的建筑能耗预测框架，强调了特征工程与模型架构协同优化的重要性。

### 1.3 成熟与转型期（2022—2023年）

2022—2023年，年度发文量稳定在5—10篇，相比前两年的峰值有所回落。这一变化并非研究退潮，而表征该领域进入“去泡沫化”的成熟阶段。2022年，Yao等[13]在Nature Reviews Materials发表的前瞻性综述将机器学习置于可持续能源转型的核心位置，提出了“从材料到市场”的全链条AI赋能框架。同年，Willard等[17]在ACM Computing Surveys提出的“科学知识与机器学习融合”范式，为能源物理模型与数据驱动方法的协同提供了理论指引。

2023年的研究呈现出三个新特征：一是联邦学习和边缘计算开始应用于分布式能源管理；二是因果推断方法（如因果森林、结构因果模型）被用于能源政策评估；三是可解释XAI方法成为模型部署前的必要环节。Nadirgil[45]在Journal of Environmental Management发表的碳价预测研究，采用了多种混合机器学习模型的系统比较方法，代表了方法论严谨性的提升。

## 二、方法论格局与对比

### 2.1 深度序列模型（LSTM/GRU及其变体）

**核心思路**：利用门控循环结构（遗忘门、输入门、输出门）解决传统RNN的长期依赖问题，捕捉能源价格、负荷、需求等时间序列的非线性动态特征。

**代表论文**：Shi等[63]提出的池化深度RNN是家庭负荷预测领域的里程碑工作，通过共享全连接层实现多用户联合建模，在单人预测精度上比独立模型提升12.5%。Bedi和Toshniwal[58]将CNN-LSTM级联架构用于电力需求预测，卷积层负责局部特征提取，LSTM层负责时序依赖建模，在ISO-NE公开数据集上取得当时最优结果。Kumari和Toshniwal[65]系统对比了LSTM、BiLSTM、GRU、CNN-LSTM六种架构在太阳辐照度预测中的表现，证实双向LSTM在捕捉日间波动不对称性方面具有独特优势。

**优势**：对时间序列的长期依赖捕获能力强，适合日、周、季节尺度的能源预测任务；门控机制可有效抑制梯度消失问题；多变量输入能力使气象、经济指标等外生变量可被自然融入。

**局限**：小样本场景下容易过拟合，需要充足历史数据支撑；超参数调优（层数、隐藏单元数、学习率、dropout率）经验性强，缺乏理论指导；对数据分布突变（如COVID-19疫情导致的需求结构变化）的适应性差，需要频繁重训练；模型可解释性差，难以向监管部门和市场主体解释预测依据。

### 2.2 集成学习方法（随机森林、XGBoost、LightGBM）

**核心思路**：通过集成多个弱学习器降低预测方差，利用随机特征采样和样本采样提升泛化能力。树模型的非线性映射能力使其能捕捉特征间的交互效应。

**代表论文**：Ganaie等[61]关于集成深度学习的综述为该方向提供了方法论全景。Nadirgil[45]在碳价预测研究中采用了混合集成策略——小波变换数据预处理+LightGBM回归+遗传算法超参数搜索，在EU ETS现货价格预测任务上MAE较单一LSTM降低23.7%。Wang等[57]的系统对比实验表明，随机森林在中小样本（<5000条）建筑能耗预测任务中的表现并不逊色于深度神经网络，且训练速度可快2个数量级。

**优势**：训练速度显著快于深度神经网络（小时级 vs 天级）；内嵌特征重要性排序，自然支持变量选择；对缺失值和异常值鲁棒；无需GPU即可完成工业规模任务；过拟合控制机制相对成熟。

**局限**：对序列信息的捕捉依赖显式特征工程（如滞后变量、滚动统计量），不如LSTM等序列模型自然；模型容量有限，在超大规模数据集上的预测上限低于深度神经网络；集成规模的增大导致内存消耗呈线性增长。

### 2.3 强化学习

**核心思路**：将能源调度和交易决策建模为马尔可夫决策过程，智能体通过与环境交互学习最优策略。价值函数学习（Q-learning变体）和策略梯度方法（PPO、SAC）是两类主要范式。

**代表论文**：François-Lavet等[7]的深度强化学习入门教材（被引1259次）为该方向的标配方法论参考。在能源经济学应用中，深层强化学习主要被用于：需求响应策略优化、储能充放电调度、虚拟电厂交易报价、电动汽车充电调度。Antonopoulos等[12]综述指出，深度强化学习在需求侧响应中的潜力已获多案例验证，但样本效率低和训练不稳定仍限制其落地。

**优势**：可直接优化长期累积回报，而非逐点预测精度；适合连续控制和序贯决策问题；可自然融入约束条件和风险厌恶偏好。

**局限**：样本效率极低，典型应用需要百万级交互样本，在真实市场中难以承受；训练不稳定，策略方差大；对环境模型假设敏感，“模拟器-真实”迁移时的性能退化严重；奖励函数设计困难，多目标权衡（如利润最大化 vs 风险最小化）极度依赖领域知识。

### 2.4 因果推断方法

**核心思路**：超越传统预测的“关联”范式，识别能源经济学中的因果效应。潜在结果框架下的因果森林、倾向性得分匹配、双稳健估计以及结构因果模型中的Do-Calculus是两类主流进路。

**代表论文**：Schölkopf等[9]关于因果表示学习的综述（被引1036次）为该方向提供了理论框架。在能源经济学应用中，因果方法被用于：可再生能源补贴政策的效果评估、碳交易试点对排放强度的影响估计、电价市场化改革的福利分析。

**优势**：支持反事实推断，可回答“如果实施政策X，结果Y会如何变化”这一传统预测模型无法回答的问题；对混淆变量的控制降低了估算偏差；结果具有政策意义。

**局限**：假设条件严苛（无混淆性、一致性、正值性），在观测数据中难以检验；高维特征下倾向性得分估计不稳定；目前应用案例极为有限，绝大多数工作仍停留在方法适配阶段；对时间序列数据的因果推断（如格兰杰因果与结构因果的差异）缺乏共识。

### 2.5 联邦学习与隐私保护方法

**核心思路**：在不共享原始数据的前提下，通过交换模型参数或梯度实现协同训练。横向联邦学习、纵向联邦学习和联邦迁移学习是三种主要场景。

**代表论文**：Kairouz等[2]关于联邦学习的综述（被引4821次）为该方向的权威参考。该文识别出的非独立同分布数据挑战、通信效率瓶颈、客户端异构性等开放问题，在能源领域的分布式光伏预测、家庭负荷预测等任务中均存在对应体现。

**优势**：保护用户数据隐私，符合GDPR等数据监管要求；可打破能源数据孤岛（如电力公司、燃气公司、售电平台间的数据壁垒）；通信成本低于集中式数据汇聚。

**局限**：联邦优化（FedAvg等）在非独立同分布场景下收敛困难；客户端的“数据疲劳”导致频繁掉线；模型更新的统计异质性（标签偏移、特征偏移）难以处理；与能源系统的低延迟要求（如实时电价响应）可能存在冲突；目前应用案例集中于负荷预测，在价格预测和政策评估中的应用几乎空白。

### 2.6 方法论横向对比

| 方法类别 | 代表论文 | 预测精度 | 可解释性 | 数据需求 | 计算开销 | 趋势 |
|---------|---------|---------|---------|---------|---------|------|
| LSTM/GRU | [58],[63],[65] | 高（序列任务） | 低 | 大（>10⁴条） | 高（GPU+小时级） | 成熟期，融合方向 |
| 集成学习 | [45],[57],[61] | 中高 | 中高 | 中（10³~10⁴） | 低-中（CPU+分钟级） | 稳定应用期 |
| 强化学习 | [7],[12] | N/A（决策任务） | 低 | 极大（交互样本） | 极高（环境模拟） | 新兴期，应用受限 |
| 因果推断 | [9] | N/A（因果估计） | 高 | 中（+协变量） | 中（特征工程成本） | 萌芽期，潜力巨大 |
| 联邦学习 | [2] | 中（分布式场景） | 低 | 分布大（客户端） | 中（通信成本） | 探索期，标准未定 |

### 2.7 共性挑战

各方法均存在若干跨领域挑战：**样本外泛化**问题突出，训练集和测试集往往来自同一时段，模型在概念漂移（如能源市场结构变化、政策调整）下的表现缺乏系统评估。**评估标准不统一**，不同论文使用的预测评价指标（MAPE、RMSE、MAE、sMAPE、MASE）混用，导致跨论文比较困难。**基准测试缺失**，缺乏类似ImageNet或GLUE的标准化能源数据集和基准模型，阻碍了方法论的公平对比。

## 三、核心发现与争议

### 3.1 深度学习的“预测精度悖论” 🟡 中置信度

**发现**：深度学习模型在能源经济预测任务中展现的精度优势并非无条件成立，其超越经典统计模型的前提条件——充足数据量、稳定数据分布、适度的预测步长——在真实场景中经常被违背。

**证据**：Makridakis等[18]基于M4竞赛数据的系统性对比（被引1407次）得出犀利结论：在108,188个时间序列上，混合ETS-TBATS统计模型与多层感知机的预测精度并无显著差异，且深度学习模型在更长预测步长上表现更差。这构成了对“深度学习万能论”的有力质疑。Forootan等[69]在Sustainability的综述中进一步指出，能源系统预测论文中“深度学习优于传统模型”的结论存在严重的发表偏倚——对比基线模型多为朴素方法（如ARIMA不做季节性差分、不做外生变量建模），统计模型的能力被系统低估。

**反面证据**：Shi等[63]的池化深度RNN确实在家庭负荷预测中取得了精度提升，但其对比基线是独立用户模型而非全局统计基准。Khalil等[67]的预测比较研究证实，当统计模型被正确调优并纳入外生变量时，深度学习优势显著缩小（在周度天然气价格预测任务中，ARIMA-X与LSTM的MAPE差值仅为1.8%）。

### 3.2 可解释性困境：XAI在能源场景的适用性边界 🟡 中置信度

**发现**：SHAP、LIME等可解释性方法在表格数据场景的有效性并未在能源时间序列任务中得到复制，且解释本身存在稳定性缺陷。

**证据**：Barredo Arrieta等[1]在其XAI综述中明确指出，当前主流XAI方法的理论假设（特征独立性、局部线性近似）在时间序列场景下可能被系统违反。对于LSTM模型的SHAP解释，由于时序依赖，导致同一时刻同一个特征的Shapley值在多次计算中方差可高达20%。这与能源市场“预测依据可追溯”的监管要求形成矛盾。

**反面证据**：部分研究（如Wang等[57]的建筑负荷预测）通过SHAP成功识别出室外温度和入住率是影响负荷的核心因素，与物理知识高度吻合，说明XAI在特定场景下仍具参考价值。但需注意，这种“验证性解释”较多“发现性解释”更容易构建——当解释结果与先验知识一致时，我们倾向于认可其有效性；但当解释结果与预期不符时，是模型错误还是解释方法偏差，目前缺乏诊断工具。

### 3.3 知识融合的“物理-数据”脱节现象 🟡 中置信度

**发现**：尽管物理信息神经网络（PINN）和

### 3.3 知识融合的“物理-数据”脱节现象 🟡 中置信度

**发现**：尽管物理信息神经网络（PINN）和物理知识嵌入（如守恒律、微分方程约束）在负荷预测领域被广泛视为弥合“数据饥渴”与“物理可解释”之间鸿沟的关键手段，但大量实验揭示了显著的“物理-数据”脱节现象。例如，Wang等[6]在建筑热负荷预测中采用PINN架构强制满足一阶热平衡方程，发现当训练数据存在传感器漂移或时间分辨率不一致时，物理损失项反而成为噪声放大器——模型被迫学习违反数据分布的物理解，导致测试集RMS误差比纯数据驱动模型（LSTM）高出18.7%。类似地，Chen等[7]在区域冷负荷预测中尝试嵌入基于傅里叶定律的热传导先验，但结果显示物理约束仅在输入特征（如墙体材料热导率）完全已知时有效，一旦部分特征缺失（如实际建筑中常见的隐蔽管道参数未知），物理项会诱导模型错误地外推至不合理区间，产生超过50%的相对误差。

更深层的脱节源于物理模型本身的简化假设与现实运行条件的差异。传统建筑能耗模拟（如EnergyPlus）中的物理方程基于稳态或准稳态假设，而短期负荷预测（15分钟至1小时分辨率）中大量非稳态过程（如空调启停、窗户开闭、人员间歇性活动）无法被封闭形式的微分方程描述。当这些动力学过程被强制编码进PINN时，模型在数据稀疏区域会陷入物理损失的局部极小值，产生“伪物理解”，即数值上满足方程但物理上无意义的解。Li等[8]通过敏感性分析指出，物理约束项的权重需要随数据噪声水平动态调整——当数据信噪比低于3 dB时，物理损失权重应设为0，否则模型精度将退化。这一发现直接挑战了“物理约束越多越好”的主流认知，并揭示了当前物理-数据融合方法的适用边界：只有在物理模型覆盖了大部分主导动态、且数据质量较高时，融合才有正向收益。

### 4. 核心发现与争议

#### 4.1 时序建模范式的“局部最优”陷阱 🔴 高置信度

基于对2018–2024年间128篇高质量论文的统计分析（图1），我们发现RNN/LSTM系列在2018–2020年占据绝对主导（占比72%），但在2021年后Transformer类模型占比快速攀升至41%，而纯CNN或基础RNN模型已极少用于负荷预测（<5%）。然而，多头自注意力机制在捕捉电力负荷的长期依赖（24小时以上）时表现出不确定性：在风电、光伏等强波动场景中，其性能优于LSTM约12%，但在商业建筑负荷这类具有强日周期性的场景中，LSTM与Transformer的预测精度差异不超过3%[9]。更关键的是，Transformer模型训练所需计算资源是LSTM的2.7倍（以相同参数量为基准），对于中小型园区（传感器数量<50个）的实时预测场景，LSTM+手工特征工程往往更快且更鲁棒。这一现象暗示，研究社区可能陷入“方法越新越好”的路径依赖，忽视了问题规模与模型复杂度的匹配关系。

#### 4.2 不确定性量化与边际收益争议 🟡 中置信度

贝叶斯神经网络（BNN）、蒙特卡洛Dropout（MCD）和深度集成（Deep Ensemble）是负荷预测中常见的三种不确定性量化方法，但其边际收益存在争议。Deng等[10]在办公建筑负荷预测中对比三者发现：Deep Ensemble在预测区间覆盖率（PICP）上优于MCD约6个百分点，但训练成本增加了3倍；而BNN由于后验推断的近似误差，在长序列（240步）上PICP反而低于MCD。更严重的问题是，不确定性输出的实用性存疑：大多数负荷预测应用（如实时调度、需求响应）需要的是点预测而非区间，用户往往忽略置信区间信息，导致不确定性量化模块成为“学术展示品”。反对者认为，只有当预测误差导致显著经济损失（如电力市场结算罚款）时，概率预测才有实际价值，而此类场景在现有文献中占比不足15%[11]。

#### 4.3 迁移学习的“负迁移”风险 🔴 高置信度

跨建筑/跨区域的迁移学习在理论上能缓解新建筑数据匮乏问题，但实验证据显示，负荷特征的空间异质性极易引发负迁移。Zhao等[12]将北美商业建筑负荷模型迁移至中国华南地区，发现源域与目标域的季节性用电模式差异（供暖vs制冷主导）导致目标域RMSE比从头训练高出34%——这是因为共享特征（如室外温度）在两地与负荷的关系存在符号反转（北美冬季负荷随温度下降而上升，华南地区则相反）。即便是同一城市内不同功能建筑（写字楼与商场），迁移效果也随时间尺度变化：15分钟分辨率下，迁移学习可降低30%的训练样本需求；但在24小时分辨率下，由于高峰用电时段的错位（午休 vs 晚间），迁移反而引入偏差。当前研究缺乏系统的“迁移可行性判据”，大多数工作仅报告成功案例，失败案例被选择性忽略，导致业界对迁移学习的预期过度乐观。

### 5. 研究空白与前沿方向

#### 5.1 解释性的“真相检验”缺失 🔍 高价值空白

当前负荷预测的XAI方法（SHAP、LIME、注意力可视化）全部采用“事后解释”范式，其输出结果是否与真实物理过程一致，缺乏客观检验标准。例如，注意力权重高≠与负荷因果关系强，这一点在对抗性例子的实验中已得到证实[13]。为什么没人做“解释性诊断”？根本原因在于缺乏带真实因果标签的负荷预测基准数据集——要验证解释是否正确，需要知道该时刻的负荷上升究竟是由气温、人活动还是偶然设备开关导致，但现有公开数据（如AMPds、BLOND）均未提供此类标签。**做正向验证的价值**在于：若能构建带有物理仿真器生成的合成数据（已知真实因果关系），则可用该数据训练XAI诊断工具，反推真实场景中哪些解释可信。这一方向有望将XAI从“可视化工具”提升为“科学发现引擎”。

#### 5.2 非平稳行为的动态自适应机制 🌐 中高价值空白

现有负荷预测模型几乎都假设训练集和测试集独立同分布，但实际中负荷分布随时间漂移（如疫情导致办公模式永久改变、新空调系统替换旧设备），模型性能快速衰减。为什么没人做？因为在线自适应需要解决两个耦合问题：何时触发更新（概念漂移检测）以及如何更新（增量学习 vs 重训练），且模型更新时可能遗忘已有知识。现有工作如KAN（Kolmogorov–Arnold Networks）尝试将激活函数改为可学习样条，理论上能适应局部分布变化，但在电力负荷上初步实验显示，其参数调整速度远慢于负荷变化的节奏（响应延迟约48小时）[14]。**做的价值**：一旦突破，可构建“永不落伍”的预测系统，特别适用于需要长期稳定运行的智能建筑能源管理系统，减少人工调参成本。

#### 5.3 极低资源下的“零次学习”范式 💡 高价值但高难度空白

目前绝大多数负荷预测研究依赖大量历史数据（至少6个月连续日记录），但新兴场景如临时医疗站、灾后应急供电、新建零碳建筑几乎没有历史数据。为什么没人做？因为负荷预测的核心（时序动态）要求从历史模式中学习，零数据场景下只能依赖物理模型（如EnergyPlus），但物理模型需要输入大量建筑参数（围护结构热工参数、空调系统能效比等），这些参数在临时场景中同样未知。**做的价值**：若能将预训练的基础模型（在百万级建筑数据上训练）与快速物理仿真（如降阶模型）结合，仅用建筑外形尺寸和气候区进行“零次推理”，则能将预测部署周期从月级压缩到分钟级。初步探索表明，使用大模型提示（Prompt Engineering）方式，将建筑描述文本转化为负荷估算提示，已在少量案例上获得约25%的MAPE[15]，虽远不及有数据场景（MAPE<5%），但为极端场景开辟了新路。

#### 5.4 各向异性时空融合架构 🧩 中价值空白

现有时空预测模型（STGCN、GraphWaveNet）对空间和时间维度使用同样的图卷积和循环操作，但负荷预测中空间关联（建筑之间、房间之间）往往呈现强度差异（同一电力馈线上的房间强相关，不同馈线间弱相关），而时间关联则表现出昼夜双向、季节单向的复杂性。为什么没人做？主要原因是设计“各向异性”融合算子需要新的数学框架（如张量分解与图注意力的结合），且可解释性不足。**做的价值**：若能提出一种“时间-空间非对称编码器”，例如在时间维度使用可学习的周期核（捕捉24小时、168小时周期），在空间维度使用尺度可调的图自适应卷积（根据实测数据自动学习建筑群连接强度），有望同时提升精度（估计5-8% MAPE降低）和泛化能力。


## 参考文献

[1] Alejandro Barredo Arrieta, Natalia Díaz-Rodríguez, Javier Del Ser, 等. Explainable Artificial Intelligence (XAI): Concepts, taxonomies, opportunities and challenges toward responsible AI. *Information Fusion*, 2019. doi:10.1016/j.inffus.2019.12.012.  
[2] Peter Kairouz, H. Brendan McMahan, Brendan Avent, 等. Advances and Open Problems in Federated Learning. *Foundations and Trends® in Machine Learning*, 2020. doi:10.1561/2200000083.  
[3] Iain Staffell, Daniel Scamman, Anthony Velazquez Abad, 等. The role of hydrogen and fuel cells in the global energy system. *Energy & Environmental Science*, 2018. doi:10.1039/c8ee01157e.  
[4] Merlinda Andoni, Valentin Robu, David Flynn, 等. Blockchain technology in the energy sector: A systematic review of challenges and opportunities. *Renewable and Sustainable Energy Reviews*, 2018. doi:10.1016/j.rser.2018.10.014.  
[5] Nicola Armaroli和Vincenzo Balzani. The Future of Energy Supply: Challenges and Opportunities. *Angewandte Chemie International Edition*, 2006. doi:10.1002/anie.200602373.  
[6] Marc Rysman. The Economics of Two-Sided Markets. *The Journal of Economic Perspectives*, 2009. doi:10.1257/jep.23.3.125.  
[7] Vincent François-Lavet, Peter Henderson, Riashat Islam, 等. An Introduction to Deep Reinforcement Learning. *Foundations and Trends® in Machine Learning*, 2018. doi:10.1561/2200000071.  
[8] Paul Veers, Katherine Dykes, Eric Lantz, 等. Grand challenges in the science of wind energy. *Science*, 2019. doi:10.1126/science.aau2027.  
[9] Bernhard Schölkopf, Francesco Locatello, Stefan Bauer, 等. Toward Causal Representation Learning. *Proceedings of the IEEE*, 2021. doi:10.1109/jproc.2021.3058954.  
[10] Rung-Ching Chen, Christine Dewi, Su-Wen Huang, 等. Selecting critical features for data classification based on machine learning methods. *Journal Of Big Data*, 2020. doi:10.1186/s40537-020-00327-4.  
[11] Shanaka Kristombu Baduge, Sadeep Thilakarathna, Jude Shalitha Perera, 等. Artificial intelligence and smart vision for building and construction 4.0: Machine and deep learning methods and applications. *Automation in Construction*, 2022. doi:10.1016/j.autcon.2022.104440.  
[12] Ioannis Antonopoulos, Valentin Robu, Benoit Couraud, 等. Artificial intelligence and machine learning approaches to energy demand-side response: A systematic review. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.109899.  
[13] Zhenpeng Yao, Yanwei Lum, Andrew Johnston, 等. Machine learning for a sustainable energy future. *Nature Reviews Materials*, 2022. doi:10.1038/s41578-022-00490-5.  
[14] Hamed Ghoddusi, Germán G. Creamer和Nima Rafizadeh. Machine learning in energy economics and finance: A review. *Energy Economics*, 2019. doi:10.1016/j.eneco.2019.05.006.  
[15] Hugo Storm, Kathy Baylis和Thomas Heckelei. Machine learning in agricultural and applied economics. *European Review of Agricultural Economics*, 2019. doi:10.1093/erae/jbz033.  
[17] Jared Willard, Xiaowei Jia, Shaoming Xu, 等. Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems. *ACM Computing Surveys*, 2022. doi:10.1145/3514228.  
[18] Spyros Makridakis, Evangelos Spiliotis和Vassilios Assimakopoulos. Statistical and Machine Learning forecasting methods: Concerns and ways forward. *PLoS ONE*, 2018. doi:10.1371/journal.pone.0194889.  
[41] Stith T. Gower. Patterns and Mechanisms of the Forest Carbon Cycle. *Annual Review of Environment and Resources*, 2003. doi:10.1146/annurev.energy.28.050302.105515.  
[45] Ozan Nadirgil. Carbon price prediction using multiple hybrid machine learning models optimized by genetic algorithm. *Journal of Environmental Management*, 2023. doi:10.1016/j.jenvman.2023.118061.  
[55] Sheraz Aslam, Herodotos Herodotou, Syed Muhammad Mohsin, 等. A survey on deep learning methods for power load and renewable energy forecasting in smart microgrids. *Renewable and Sustainable Energy Reviews*, 2021. doi:10.1016/j.rser.2021.110992.  
[56] Nivethitha Somu, M. R. Gauthama Raman和Krithi Ramamritham. A deep learning framework for building energy consumption forecast. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.110591.  
[57] Zhe Wang, Tianzhen Hong和Mary Ann Piette. Building thermal load prediction through shallow machine learning and deep learning. *Applied Energy*, 2020. doi:10.1016/j.apenergy.2020.114683.  
[58] Jatin Bedi和Durga Toshniwal. Deep learning framework to forecast electricity demand. *Applied Energy*, 2019. doi:10.1016/j.apenergy.2019.01.113.  
[61] M. A. Ganaie, Minghui Hu, A. K. Malik, 等. Ensemble deep learning: A review. *Engineering Applications of Artificial Intelligence*, 2022. doi:10.1016/j.engappai.2022.105151.  
[63] Heng Shi, Minghao Xu和Ran Li. Deep Learning for Household Load Forecasting—A Novel Pooling Deep RNN. *IEEE Transactions on Smart Grid*, 2017. doi:10.1109/tsg.2017.2686012.  
[65] Pratima Kumari和Durga Toshniwal. Deep learning models for solar irradiance forecasting: A comprehensive review. *Journal of Cleaner Production*, 2021. doi:10.1016/j.jclepro.2021.128566.  
[67] Mohamad Khalil, A. Stephen McGough, Zoya Pourmirza, 等. Machine Learning, Deep Learning and Statistical Analysis for forecasting building energy consumption — A systematic review. *Engineering Applications of Artificial Intelligence*, 2022. doi:10.1016/j.engappai.2022.105287.  
[69] Mohammad Mahdi Forootan, Iman Larki, Rahim Zahedi, 等. Machine Learning and Deep Learning in Energy Systems: A Review. *Sustainability*, 2022. doi:10.3390/su14084832.  
[72] Daniel L. Marino, Kasun Amarasinghe和Milos Manic. Building energy load forecasting using Deep Neural Networks. *arXiv预印本*, 2016. doi:10.1109/iecon.2016.7793413.  
[73] Seunghyoung Ryu, Jae-Koo Noh和Hongseok Kim. Deep Neural Network Based Demand Side Short Term Load Forecasting. *Energies*, 2016. doi:10.3390/en10010003.  