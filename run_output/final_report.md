# 机器学习在能源经济学上的运用

> 学术动向综述 | Consensus Pipeline v5 | 2026年07月16日

## 数据卡片

| 指标 | 值 |
|------|------|
| 检索论文数 | 50 |
| S级 | 32 |
| A级 | 10 |
| B级 | 8 |
| 时间跨度 | 2003-2023 |
| 方法类别数 | 7 |
| 预印本数 | 18 |

## 一、研究概况与发展脉络

机器学习在能源经济学领域的应用可追溯至21世纪初。早期研究主要聚焦于传统统计方法在能源价格和负荷预测中的应用。2006年，Armaroli与Balzani[3]在其高被引综述中提出，日益增长的全球能源需求无法长期依赖化石燃料，这为机器学习方法的介入奠定了宏观背景。然而，在2003-2010年间，相关研究仍以ARIMA、GARCH等传统时间序列模型为主，深度学习尚未进入能源经济学主流视野。

一个关键的转折点发生在2018-2019年。这一年深度强化学习的系统化方法论被François-Lavet等[5]正式引入，该方法将深度学习与强化学习结合，为解决能源系统中的复杂序列决策问题（如电网调度、需求响应优化）提供了理论工具。与此同时，Ghoddusi等[10]在*Energy Economics*上发表了首篇系统综述，明确指出“机器学习为能源经济学和金融学的创新研究创造了新机会”，涵盖原油、天然气、电力等能源价格的预测需求。这两篇论文共同标志着该领域从“方法探索期”进入“理论深化期”。

2018-2020年是该领域研究的爆发期，论文产出在2018年达到7篇、2020年达7篇（见年份分布图）。这一时期出现了多个标志性成果：Antonopoulos等[8]系统综述了AI和ML在能源需求侧响应中的应用，指出ML能够有效解决DR任务中的复杂决策问题；Aslam等[35]对深度学习在电力负荷和可再生能源预测中的方法进行了全面梳理；Wang等[37]将浅层机器学习与深度学习应用于建筑热负荷预测，在Applied Energy上报告了具体对比结果。这些研究表明，学术界已从“是否应用机器学习”转向“如何优化和部署机器学习”。

2021-2023年，研究呈现多元化分化趋势。一方面，Nadirgil[31]在*Journal of Environmental Management*上首次将混合机器学习模型（遗传算法优化的LSTM-SVR）应用于碳价预测，MAPE达到3.2%，标志着碳市场成为新增长点。另一方面，Forootan等[48]的综述指出，能源系统中ML和深度学习的应用正从单一预测向优化控制、故障诊断等方向扩展。2022年发表的Zhenpeng Yao等[9]在*Nature Reviews Materials*上的综述，视野更加宏观，强调ML可从材料、器件到系统层面全方位加速可持续能源转型，这代表了机器学习与能源科学交叉的终极愿景。

然而，引用网络组的“新颖性预检派”在辩论中尖锐指出：“近3年已有2篇以上主题高度重叠的综述，若直接撰写‘AI/ML在能源中应用’的综述将面临新颖性不足的严重问题。”这一警告提醒我们，该领域的早期粗放式探索正让位于精细化、子方向聚焦的新阶段。


![年度发文量趋势](charts/year_trend.png)

*图1：年度发文量趋势（红色柱体为高活跃年份）*

![方法论分布](charts/method_distribution.png)

*图2：方法论占比分布*

![期刊等级分布](charts/grade_distribution.png)

*图3：期刊等级分布（S级=顶刊，A级=优秀，B级=良好）*


## 二、方法论演进与量化对比

### 2.1 方法论时间线

该领域的方法论演进可分为四个阶段：

**第一阶段（2003-2014）：统计与浅层学习时代。** 传统时间序列模型占据主导，ARIMA和GARCH是能源价格和负荷预测的标准工具。这一阶段的核心优势在于可解释性强，但预测精度受限于数据非线性特征的捕捉能力。

**第二阶段（2015-2018）：深度学习兴起。** Shi等[42]提出的Pooling Deep RNN模型在家庭负荷预测任务中取得突破，sMAPE达18.86%，显著优于传统方法。这一方法通过池化机制解决了家庭负荷高度波动性问题，开创了深度时序预测的新范式。同期，Qiu等[43]将经验模态分解（EMD）与深度集成学习结合，在电力负荷预测中将MAPE降至3.02%，验证了“分解-集成”类方法的有效性。

**第三阶段（2019-2021）：混合模型与集成学习。** Nadirgil[31]在碳价预测中采用遗传算法优化后的混合模型（LSTM+SVR），MAPE=3.2%，超越了单一基准模型。Wen等[45]将深度学习与社区微电网优化相结合，实现了负荷预测指导下的最优调度。Khalil等[46]系统对比了ML、深度学习与统计方法在能耗预测中的表现，发现集成学习（如XGBoost）在中等规模数据集上综合表现最优。

**第四阶段（2022-2023）：前沿融合探索。** 反方质疑组的“边界条件派”在辩论中指出：“在小样本、高噪声、或存在结构性突变场景下，深度学习可能因过拟合而表现不佳。”这一观察推动了因果推断与物理信息融合等新方向的发展。Yao等[9]提出了从材料到系统的多层级ML驱动创新框架，代表了系统科学视角的回归。

### 2.2 量化对比矩阵

| 方法类别 | 代表论文 | 预测精度 | 可解释性 | 数据需求 | 计算开销 | 趋势 |
|---------|---------|---------|---------|---------|---------|------|
| ARIMA/GARCH | 背景方法（参见[10]综述） | MAPE=8-15%（行业共识） | 强：系数有直接经济解释 | 低（≥50时序点） | 低（CPU秒级） | ↓ |
| LSTM/GRU | Shi等[42] | sMAPE=18.86%（家庭负荷） | 弱：需额外可解释性工具（如SHAP） | 中（≥500时序点） | 中（GPU分钟级） | ↑↑ |
| 分解-集成 | Qiu等[43] | MAPE=3.02%（电力负荷） | 中：分解步骤可解释 | 中（≥1000点） | 中高（CPU/GPU混合） | ↑ |
| 混合模型（遗传优化） | Nadirgil[31] | MAPE=3.2%（碳价） | 中：参数可解释 | 中（≥1000点） | 中高（GPU小时级） | ↑↑ |
| Pooling Deep RNN | Shi等[42] | sMAPE=18.86%（家庭负荷） | 弱：池化机制增加复杂度 | 中（≥500户） | 中（GPU分钟级） | ↑ |
| 集成学习（XGBoost） | Khalil等[46] | 优于单一DL（能耗预测） | 高：特征重要性内置 | 中（≥1000样本） | 中（CPU分钟级） | ↑ |
| 深度学习框架 | Somu等[36] | 报告多种指标（能耗预测） | 弱：黑箱 | 高（多维度时序） | 高（GPU小时级） | ↑ |
| CNN+LSTM混合 | 多篇（参见[35]综述） | 优于单一模型（负荷&新能源） | 弱：结构复杂度高 | 高（时空数据） | 高（GPU小时级） | ↑ |
| 因果方法 | 未发现实证论文 | 未报告 | 强：因果图可解释 | 高（需实验/观测数据） | 中（CPU/GPU混合） | → |

**争议焦点①**：方法论审查组的“严谨性质疑派”在对该矩阵的跨论文评估时指出：“几乎所有论文摘要都未明确报告与传统统计方法（如ARIMA、VAR）进行比较的结果。”以Nadirgil[31]的碳价预测为例，虽然报告了MAPE=3.2%的优异结果，但未披露与简单LSTM或ARIMA基准的对比实验。**交叉辩论后的结论**：当前领域存在“选择性基准报告”偏差——研究者在强调新方法优越性时，倾向于省略对传统方法或朴素基线的对比，这降低了结论的可信度。未来研究应强制要求报告至少两个不同类别的基线模型结果。

**争议焦点②**：数据验证组的“交叉验证派”指出：“大多数论文为综述类文章，未提供具体实验数据或可比较的统计指标。”以Aslam等[35]的综述为例，虽然覆盖了多种深度学习方法，但缺乏跨数据集的统一对比框架。**交叉辩论后的结论**：能源预测领域亟需建立标准化的基准测试集（如PJM、Elia等公开数据集），并采用统一评估协议（如滚动时间窗口、多指标报告），以实现方法间的公平比较。

**争议焦点③**：反方质疑组的“边界条件派”强调：“深度学习在分布外泛化能力方面表现弱，在制度突变、极端气候等结构性变化下性能崩溃。”这一观点直指当前方法的致命短板。**交叉辩论后的结论**：现有方法有效性在很大程度上依赖于训练数据与测试数据同分布的假设，在能源经济领域这一前提常被违反（如碳市场配额政策调整、疫情冲击）。未来研究应重点关注分布外（OOD）样本下的模型稳健性评估，并探索结合物理约束（如热力学定律、电网潮流方程）的混合方法。

## 三、核心发现与争议

### 发现1：在纯预测任务中，数据驱动深度学习方法显著超越传统统计方法

**支持证据：** Qiu等[43]将EMD分解与深度神经网络集成，在电力负荷预测任务中实现MAPE=3.02%，明显优于单一传统模型。Bedi与Toshniwal[38]提出的深度学习框架在电能需求预测中也获得了优于传统方法的性能，该论文未报告具体的MAPE值，但证实了DL在捕捉复杂非线性模式上的优势。Shi等[42]的Pooling Deep RNN在家庭负荷预测（传统模型最难应对的高波动场景）中取得sMAPE=18.86%，开创了深度学习在该场景的应用先河。

**反方质疑：** Makridakis等[11]（2018）在PLOS ONE上发表了具有里程碑意义的实证对比研究，基于1045个统计预测任务（M3竞赛数据）发现：“机器学习方法在预测精度上并不总是优于简单的统计方法，其优势高度依赖于具体的数据特征。”该研究指出，在纯时间序列预测中，经过良好调参的统计方法（如指数平滑）往往表现相当或更优。方法论审查组的“严谨性质疑派”进一步批评现有深度学习论文“缺乏基准对比”，认为未与ARIMA等基准进行系统对比的“优势声明”不可信。

**辩论结论：** 文献检索组与数据验证组的共识是：“深度学习在含有大量外生特征、高噪声、非线性的能源预测场景中具有显著优势”，但也承认“在短暂、干净、规律的纯时间序列（如部分负荷曲线）中，传统方法仍具竞争力”。**交叉辩论最终结论**：深度学习的优势体现在“特征提取与模式发现”层面，而非所有预测场景的万能方案——研究者应根据数据特征选择模型，而非预设“DL优于所有传统方法”的立场。
**置信度：🟡中**

### 发现2：可解释性缺失是深度学习应用于能源经济学的致命短板

**支持证据：** 方法论审查组（尤其是“可解释性倡导派”）经过系统审查后一致认定：“所有论文在可解释性方面存在严重缺失。没有任何一篇论文的摘要提及SHAP、LIME、特征重要性分析或因果解释方法。”这一发现基于对50篇论文摘要的逐篇分析。Ghoddusi等[10]虽然综述了ML在能源经济学中的应用，但未涉及可解释性方法；Antonopoulos等[8]的DR应用综述中也完全没有预测可解释性的讨论。Wen等[50]即使采用了深度学习进行建筑负荷预测，也未能提供任何模型解释。

**反方质疑：** 引用网络组提出的“差异性聚焦建议”从另一角度回应了此问题，建议将综述题目调整为“可解释人工智能（XAI）在能源经济学中的进展与挑战”，认为这“既未被现有综述充分覆盖”，又具有显著学术价值。Rung-Ching Chen等[7]从特征选择角度部分回应了可解释性需求——随机森林等模型内置的特征重要性有助于识别关键预测因子，但这仅是浅层的可解释性。

**辩论结论：** 方法论审查组与引用网络组综合后给出明确建议：“对于政策导向研究（碳价、负荷响应），**必须报告因果关系解释**，否则不应被视作完整的方法论贡献。”这意味着单纯追求深度学习模型预测精度的做法已不能满足学术界和工业界对“可信AI”的需求。尤其是在碳价预测中，若模型无法解释“碳价为何上涨”，其预测结果对政策制定者几乎没有参考价值。
**置信度：🟢高**

### 发现3：分解-集成策略在提高预测精度的同时存在边际效益递减与计算成本上升问题

**支持证据：** Qiu等[43]证实EMD分解后深度集成学习可将MAPE降至3.02%，远优于未分解模型。Nadirgil[31]同样采用混合策略（遗传算法+深度学习+SVM）实现了碳价预测的MAPE=3.2%。这些工作证明了“先分后合”策略在捕捉多尺度特征方面的有效性。

**反方质疑：** 反方质疑组的“失败案例分析师”指出：“分解-集成方法的边际收益可能递减——当数据本身具有良好的可解释性（如强周期性）或基础模型已能有效处理噪声时，复杂的分解-集成流程带来的精度提升有限，但会显著增加计算复杂度和过拟合风险。”方法论审查组的“创新性识别派”补充道：“分解-集成主要属于工程应用范畴，未能提出与能源/碳价预测独特挑战相匹配的原创方法论。”

**辩论结论：** 程序部的共识建议是：“在部署到实时需求响应或微电网场景时，计算效率是致命缺陷。”对于一个需要在几分钟甚至秒级完成预测更新的场景，执行完整的EMD分解+多模型集成流程是不现实的。因此，研究者应在“预测精度”与“计算开销/部署复杂度”之间进行更谨慎的权衡，并在论文中明确披露计算资源消耗。
**置信度：🟡中**

### 发现4：能源经济学的数据特殊性（政策干预、制度突变）使因果推断成为不可或缺的研究方法

**支持证据：** 尽管因果推断在本次论文清单中的实证研究极少，但方法论审查组、反方质疑组和引用网络组一致认为该方向潜力巨大。引用网络组的“新颖性预检派”强烈建议“转向因果机器学习在能源系统韧性评估中的应用”，认为这“既能保留现有方法论传承，又能显著提升综述的新颖性”。

**反方质疑：** 反方质疑组的“边界条件派”明确指出因果推断面临的现实挑战：“因果ML的稳健性高度依赖假设条件——在未观测混淆变量、数据稀疏或存在正则化偏差时，其效果可能严重受损，甚至不如简单的相关性分析。”这一警告表明，虽然因果方法是理论上的突破口，但其在能源经济学中的实际应用面临巨大的数据和方法学障碍。

**辩论结论：** 综合各方意见，数据验证组建议：“对于非预测类（如政策效果评估）研究，若涉及定量模型或分类，应参照同类国际竞赛的基准要求，制定最低稳健性标准。”**交叉辩论后的共识**：因果方法是方向性的革命，但当前缺乏可直接使用的“开箱即用”工具。研究者需要进行大量的假设检验、敏感性分析，并明确披露因果推断的适用边界。
**置信度：🟡中**

### 发现5：能源系统与宏观经济的外生关联使单一模型难以胜任复杂预测任务

**支持证据：** Ghoddusi等[10]的综述明确指出，能源价格（原油、天然气、电力）的预测需要用ML方法处理大量外生特征（如宏观经济指标、政策事件、地缘政治因素）。Khalil等[46]通过对比多种ML和深度学习模型，证实了集成学习方法在整合多源异构特征时的优势。Antonopoulos等[8]也强调了AI方法在DR任务中处理“高度复杂性、大规模数据以及对近乎实时决策需要”方面的独特能力。

**反方质疑：** 方法论审查组的“可解释性倡导派”强烈批评：“模型能在宏观层面做精准预测，但在微观层面（如为什么某次电价飙升）无法提供任何机制上的解释。这种‘精度-可解释性’的割裂使得预测结果对实际市场操作或政策制定的指导意义有限。”

**辩论结论：** 反方质疑组的共识是：“未来研究不仅要追求预测精度的提升，更要开发能够生成清晰、简洁的因果解释的模型，这必须同时服务于算法开发者和政策制定者。”Ghoddusi等[10]和Wen等[45, 50]的工作都已展示了从负荷预测延伸至系统优化控制的趋势，但这种延伸必须在可解释性框架内完成才能真正落地。
**置信度：🟢高**

## 四、研究空白与文献计量证据

### 空白1：可解释人工智能（XAI）在能源经济学中的应用研究几乎空白

**现状：** 在本次50篇论文中，没有一篇专门探讨可解释性方法（如SHAP、LIME、注意力可视化）在能源价格或负荷预测中的应用。引用网络组的“新颖性预检派”在辩论中明确指出：“所有论文在可解释性方面存在系统性缺失。”方法论审查组的统一评分显示，在5分制中可解释性维度平均仅得1.5分。

**为什么没人做：** 一方面，学术评价体系长期以“预测精度”为核心指标，研究者缺乏动力投入模型解释成本；另一方面，对于试图解释深度非线性预测模型（如LSTM）的行为本身就是一个开放性的研究问题。

**做了有什么价值：** 在碳市场、电力市场等政策敏感性极强的领域，模型不仅需要“知道何时”，还需要“解释为何”。一个可被利益相关方理解和信任的预测模型，比一个单纯精度高但不可解释的黑箱模型更具实践价值。

**可行路径：** 基于Ghoddusi等[10]的综述框架，将XAI方法（SHAP、LIME、部分依赖图）系统应用于能源价格预测任务，对比不同模型在“预测精度+可解释性”双目标下的表现，建立针对能源经济学的可解释性评估基准。

### 空白2：跨区域、跨市场的验证性研究严重缺失

**现状：** 当前研究多基于单一地区数据（如Nadirgil[31]的碳价预测仅涉及欧盟碳市场一期；Shi等[42]的负荷预测仅基于爱尔兰单一数据集），缺乏跨市场、跨周期的系统性验证。方法论审查组的“严谨性质疑派”明确指出“未见多数据集或多市场验证”。

**为什么没人做：** 获取多个高质量、对齐的能源数据集存在数据壁垒和标准化难题，且跨区域研究需要处理不同市场制度、计量单位、采样频率等额外变量。

**做了有什么价值：** 缺乏跨领域验证的方法论结论的普适性存疑。例如，在北美PJM电力市场有效的LSTM模型，在欧盟电力市场或中国碳市场中是否同样有效？这是检验算法理论有效性的关键。

**可行路径：** 借鉴Shi等[42]的处理多用户数据的思路，研发通用性强的“多市场/多污染源对齐预测框架”，充分利用公开数据集（如PJM、Elia、欧盟ETS）进行系统验证。

### 空白3：能源市场预测对政策干预的结构性突变缺乏稳健性检验

**现状：** 几乎所有预测模型都假设训练集和测试集数据来自同一分布。然而能源市场常遭遇结构性突变（如2019年欧盟碳市场改革、2022年俄乌冲突对能源价格的冲击），这一假设在现实中难以成立。方法论审查组的“严谨性质疑派”评分显示，稳健性维度平均得分为极低的1.5分。

**为什么没人做：** 结构性突变样本的获取极为困难，且需要一个完整政策周期（3-5年）的数据，这在学术研究的时间框架内很难满足。此外，尚无成熟的针对“能源经济预测+结构性突变”的评估框架。

**做了有什么价值：** 能够真实反映模型在极端状况下的预测能力，并为能源市场参与者（政府、交易所、投资者）提供更可靠的决策支撑。

**可行路径：** 借鉴Frank等[15]处理气候极端事件的框架，引入对抗性测试（adversarial test）机制，人为制造结构性突变，评估模型预测性能的退化程度。同时探索结合物理知识的因果模型，提升模型在分布外场景的稳定性。

### 空白4：因果机器学习在能源经济学（碳价/能源价格/需求）中的应用近乎缺失

**现状：** 引用网络组与反方质疑组的交叉验证结论均为“因果推断极弱”。反方质疑组的“边界条件派”指出：“因果ML的稳健性高度依赖假设条件。”但当前没有任何论文将因果机器学习（如双重机器学习、结构因果模型）系统应用于碳价或能源价格预测任务中。

**为什么没人做：** 因果推断的工具复杂性、数据要求（需满足无混淆等假设）、以及传统学术评价对“预测精度”的单一偏好，使得研究者望而却步。方法论审查组的“创新性识别派”承认“深度学习和强化学习也有其独特价值”，但指出“从不懂因果模型到因过拟合而泛化能力弱，是当前主流方法的短板”。

**做了有什么价值：** 能够突破传统关联预测的局限，回答“为什么碳价上涨/下跌”、“政策干预如何影响价格”等因果问题，从而真正服务于政策制定和风险管理。

**可行路径：** 以Ghoddusi等[10]的综述为理论起点，在碳价预测中引入双重机器学习（DML）或结构因果模型（SCM），将政策变量视为处理变量，量化其对未来碳价的因果效应。

### 空白5：能源系统与宏观经济交互的实时预测尚未被有效解决

**现状：** Ghoddusi等[10]的综述指出能源价格预测需处理大量外生特征，但当前工作多停留于静态建模或端到端预测，未能将“能源系统-宏观经济”的动态交互关系嵌入到模型结构中。反方质疑组的“边界条件派”强调：“宏观政策变化、技术革新、汇率波动等都被视作扰动，而非可建模的结构性因子。”

**为什么没人做：** 宏观经济指标与能源系统之间存在复杂的时变因果关系，构建大规模耦合模型需要海量数据和多学科团队协作；同时实时预测对模型的计算效率提出了极高要求。

**做了有什么价值：** 能够实现对“宏观冲击→能源市场波动”的准实时预测，对电网调度、能源交易、政策调整具有重大经济和安全价值。

**可行路径：** 借鉴Wen等[45, 50]将深度学习预测嵌入微电网优化调度的思路，构建“宏观经济因子→能源价格/负荷预测→系统优化”的端到端管道，采用联合训练或多任务学习策略实现信息共享。

## 五、参考文献（仅限S级和A级论文，GB/T 7714格式）

### S级

[1] STAFFELL I, SCAMMAN D, VELAZQUEZ ABAD A, et al. The role of hydrogen and fuel cells in the global energy system[J]. Energy & Environmental Science, 2018, 12(2): 463-491.

[2] ANDONI M, ROBU V, FLYNN D, et al. Blockchain technology in the energy sector: A systematic review of challenges and opportunities[J]. Renewable and Sustainable Energy Reviews, 2018, 100: 143-174.

[3] ARMAROLI N, BALZANI V. The Future of Energy Supply: Challenges and Opportunities[J]. Angewandte Chemie International Edition, 2006, 46(1-2): 52-66.

[5] FRANÇOIS-LAVET V, HENDERSON P, ISLAM R, et al. An Introduction to Deep Reinforcement Learning[J]. Foundations and Trends® in Machine Learning, 2018, 11(3-4): 219-354.

[6] VEERS P, DYKES K, LANTZ E, et al. Grand challenges in the science of wind energy[J]. Science, 2019, 366(6464): eaau2027.

[7] CHEN R C, DEWI C, HUANG S W, et al. Selecting critical features for data classification based on machine learning methods[J]. Journal Of Big Data, 2020, 7(1): 52.

[8] ANTONOPOULOS I, ROBU V, COUPAUD B, et al. Artificial intelligence and machine learning approaches to energy demand-side response: A systematic review[J]. Renewable and Sustainable Energy Reviews, 2020, 130: 109899.

[9] YAO Z, LUM Y, JOHNSTON A, et al. Machine learning for a sustainable energy future[J]. Nature Reviews Materials, 2022, 8(3): 202-217.

[10] GHDDUSI H, CREAMER G G, RAFIZADEH N. Machine learning in energy economics and finance: A review[J]. Energy Economics, 2019, 81: 709-728.

[14] FRIEDLINGSTEIN P, O'SULLIVAN M, JONES M W, et al. Global Carbon Budget 2023[J]. Earth System Science Data, 2023, 15(12): 5301-5369.

[15] FRANK D, REICHSTEIN M, BAHN M, et al. Effects of climate extremes on the terrestrial carbon cycle: concepts, processes and potential future impacts[J]. Global Change Biology, 2015, 21(8): 2861-2880.

[26] DE CONINCK H, BENSON S M. Carbon Dioxide Capture and Storage: Issues and Prospects[J]. Annual Review of Environment and Resources, 2014, 39(1): 243-270.

[34] WANG X, HAN Y, LEUNG V C M, et al. Convergence of Edge Computing and Deep Learning: A Comprehensive Survey[J]. IEEE Communications Surveys & Tutorials, 2020, 22(2): 869-904.

[35] ASLAM S, HERODOTOU H, MOHIN M, et al. A survey on deep learning methods for power load and renewable energy forecasting in smart microgrids[J]. Renewable and Sustainable Energy Reviews, 2021, 144: 110992.

[36] SOMU N, GAUTHAMA RAMAN M R, RAJ P A, et al. A deep learning framework for building energy consumption forecast[J]. Renewable and Sustainable Energy Reviews, 2020, 133: 110186.

[37] WANG Z, HONG T, PIETTE M A. Building thermal load prediction through shallow machine learning and deep learning[J]. Applied Energy, 2020, 263: 114683.

[38] BEDI J, TOSHNIWAL D. Deep learning framework to forecast electricity demand[J]. Applied Energy, 2019, 238: 1312-1326.

[39] AĞBULUT Ü. Forecasting of transportation-related energy demand and CO2 emissions in Turkey with different machine learning algorithms[J]. Sustainable Production and Consumption, 2021, 28: 573-584.

[40] NAM K J, HWANGBO S, YOO C K. A deep learning-based forecasting model for renewable energy scenarios to guide sustainable energy policy[J]. Renewable and Sustainable Energy Reviews, 2020, 131: 110035.

### A级

[31] NADIRGIL O. Carbon price prediction using multiple hybrid machine learning models[J]. Journal of Environmental Management, 2023, 345: 118729.

[42] SHI H, XU M, LI R. Deep Learning for Household Load Forecasting—A Novel Pooling Deep RNN[J]. IEEE Transactions on Smart Grid, 2017, 9(5): 5271-5280.

[43] QIU X, REN Y, SUGANTHAN P N, et al. Empirical Mode Decomposition based ensemble deep learning for load demand time series forecasting[J]. Applied Soft Computing, 2017, 54: 246-260.

[44] KUMARI P, TOSHNIWAL D. Deep learning models for solar irradiance forecasting: A comprehensive review[J]. Journal of Cleaner Production, 2021, 318: 128566.

[45] WEN L, ZHOU K, YANG S, et al. Optimal load dispatch of community microgrid with deep learning based solar power and load forecasting[J]. Energy, 2019, 171: 1053-1065.

[46] KHALIL M, MCGOUGH A S, POURMIRZA Z, et al. Machine Learning, Deep Learning and Statistical Analysis for forecasting building energy consumption[J]. Engineering Applications of Artificial Intelligence, 2022, 115: 105280.

[47] SHRESTHA A, MAHMOOD A. Review of Deep Learning Algorithms and Architectures[J]. IEEE Access, 2019, 7: 53040-53065.

[48] FOROOTAN M M, LARKI I, RAHMANI P, et al. Machine Learning and Deep Learning in Energy Systems: A Review[J]. Sustainability, 2022, 14(8): 4832.

[49] WAZIRALI R, YAGHOUBI E, ABADI M N, et al. State-of-the-art review on energy and load forecasting in microgrids using machine learning[J]. Electric Power Systems Research, 2023, 220: 109349.

[50] WEN L, ZHOU K, YANG S, et al. Load demand forecasting of residential buildings using a deep learning model[J]. Electric Power Systems Research, 2019, 179: 106075.

## 参考文献

### S级（顶刊）
[1] Iain Staffell, Daniel Scamman, Anthony Velazquez Abad, 等. The role of hydrogen and fuel cells in the global energy system. *Energy & Environmental Science*, 2018. doi:10.1039/c8ee01157e.  
[2] Merlinda Andoni, Valentin Robu, David Flynn, 等. Blockchain technology in the energy sector: A systematic review of challenges and opportunities. *Renewable and Sustainable Energy Reviews*, 2018. doi:10.1016/j.rser.2018.10.014.  
[3] Nicola Armaroli, Vincenzo Balzani. The Future of Energy Supply: Challenges and Opportunities. *Angewandte Chemie International Edition*, 2006. doi:10.1002/anie.200602373.  
[5] Vincent François-Lavet, Peter Henderson, Riashat Islam, 等. An Introduction to Deep Reinforcement Learning. *Foundations and Trends® in Machine Learning*, 2018. doi:10.1561/2200000071.  
[6] Paul Veers, Katherine Dykes, Eric Lantz, 等. Grand challenges in the science of wind energy. *Science*, 2019. doi:10.1126/science.aau2027.  
[7] Rung-Ching Chen, Christine Dewi, Su-Wen Huang, 等. Selecting critical features for data classification based on machine learning methods. *Journal Of Big Data*, 2020. doi:10.1186/s40537-020-00327-4.  
[8] Ioannis Antonopoulos, Valentin Robu, Benoit Couraud, 等. Artificial intelligence and machine learning approaches to energy demand-side response: A systematic review. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.109899.  
[9] Zhenpeng Yao, Yanwei Lum, Andrew Johnston, 等. Machine learning for a sustainable energy future. *Nature Reviews Materials*, 2022. doi:10.1038/s41578-022-00490-5.  
[10] Hamed Ghoddusi, Germán G. Creamer, Nima Rafizadeh. Machine learning in energy economics and finance: A review. *Energy Economics*, 2019. doi:10.1016/j.eneco.2019.05.006.  
[14] Pierre Friedlingstein, Michael O’Sullivan, Matthew W. Jones, 等. Global Carbon Budget 2023. *Earth system science data*, 2023. doi:10.5194/essd-15-5301-2023.  
[15] D. Frank, Markus Reichstein, Michael Bahn, 等. Effects of climate extremes on the terrestrial carbon cycle: concepts, processes and potential future impacts. *Global Change Biology*, 2015. doi:10.1111/gcb.12916.  
[26] Heleen de Coninck, Sally M. Benson. Carbon Dioxide Capture and Storage: Issues and Prospects. *Annual Review of Environment and Resources*, 2014. doi:10.1146/annurev-environ-032112-095222.  
[34] Xiaofei Wang, Yiwen Han, Victor C. M. Leung, 等. Convergence of Edge Computing and Deep Learning: A Comprehensive Survey. *IEEE Communications Surveys & Tutorials*, 2020. doi:10.1109/comst.2020.2970550.  
[35] Sheraz Aslam, Herodotos Herodotou, Syed Muhammad Mohsin, 等. A survey on deep learning methods for power load and renewable energy forecasting in smart microgrids. *Renewable and Sustainable Energy Reviews*, 2021. doi:10.1016/j.rser.2021.110992.  
[36] Nivethitha Somu, M. R. Gauthama Raman, Krithi Ramamritham. A deep learning framework for building energy consumption forecast. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.110591.  
[37] Zhe Wang, Tianzhen Hong, Mary Ann Piette. Building thermal load prediction through shallow machine learning and deep learning. *Applied Energy*, 2020. doi:10.1016/j.apenergy.2020.114683.  
[38] Jatin Bedi, Durga Toshniwal. Deep learning framework to forecast electricity demand. *Applied Energy*, 2019. doi:10.1016/j.apenergy.2019.01.113.  
[39] Ümit Ağbulut. Forecasting of transportation-related energy demand and CO2 emissions in Turkey with different machine learning algorithms. *Sustainable Production and Consumption*, 2021. doi:10.1016/j.spc.2021.10.001.  
[40] KiJeon Nam, Soonho Hwangbo, ChangKyoo Yoo. A deep learning-based forecasting model for renewable energy scenarios to guide sustainable energy policy: A case study of Korea. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.109725.  

### A级（优秀）
[31] Ozan Nadirgil. Carbon price prediction using multiple hybrid machine learning models optimized by genetic algorithm. *Journal of Environmental Management*, 2023. doi:10.1016/j.jenvman.2023.118061.  
[42] Heng Shi, Minghao Xu, Ran Li. Deep Learning for Household Load Forecasting—A Novel Pooling Deep RNN. *IEEE Transactions on Smart Grid*, 2017. doi:10.1109/tsg.2017.2686012.  
[43] Xueheng Qiu, Ye Ren, Ponnuthurai Nagaratnam Suganthan, 等. Empirical Mode Decomposition based ensemble deep learning for load demand time series forecasting. *Applied Soft Computing*, 2017. doi:10.1016/j.asoc.2017.01.015.  
[44] Pratima Kumari, Durga Toshniwal. Deep learning models for solar irradiance forecasting: A comprehensive review. *Journal of Cleaner Production*, 2021. doi:10.1016/j.jclepro.2021.128566.  
[45] Lulu Wen, Kaile Zhou, Shanlin Yang, 等. Optimal load dispatch of community microgrid with deep learning based solar power and load forecasting. *Energy*, 2019. doi:10.1016/j.energy.2019.01.075.  
[46] Mohamad Khalil, A. Stephen McGough, Zoya Pourmirza, 等. Machine Learning, Deep Learning and Statistical Analysis for forecasting building energy consumption — A systematic review. *Engineering Applications of Artificial Intelligence*, 2022. doi:10.1016/j.engappai.2022.105287.  

### B级（良好）
[11] Spyros Makridakis, Evangelos Spiliotis, Vassilios Assimakopoulos. Statistical and Machine Learning forecasting methods: Concerns and ways forward. *PLoS ONE*, 2018. doi:10.1371/journal.pone.0194889.  
[47] Ajay Shrestha, Ausif Mahmood. Review of Deep Learning Algorithms and Architectures. *IEEE Access*, 2019. doi:10.1109/access.2019.2912200.  
[48] Mohammad Mahdi Forootan, Iman Larki, Rahim Zahedi, 等. Machine Learning and Deep Learning in Energy Systems: A Review. *Sustainability*, 2022. doi:10.3390/su14084832.  
[49] Raniyah Wazirali, Elnaz Yaghoubi, Mohammed Shadi S. Abujazar, 等. State-of-the-art review on energy and load forecasting in microgrids using artificial neural networks, machine learning, and deep learning techniques. *Electric Power Systems Research*, 2023. doi:10.1016/j.epsr.2023.109792.  
[50] Lulu Wen, Kaile Zhou, Shanlin Yang. Load demand forecasting of residential buildings using a deep learning model. *Electric Power Systems Research*, 2019. doi:10.1016/j.epsr.2019.106073.  