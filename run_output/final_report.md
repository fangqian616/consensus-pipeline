# 机器学习在能源经济学上的运用

> 学术动向综述 | Consensus Pipeline v5 | 2026年07月15日

## 摘要

本综述基于2019-2023年间发表的67篇S/A/B级论文，系统梳理机器学习在能源经济学中的研究格局。研究发现，该领域自2018年起进入爆发式增长期，2019-2022年间贡献了超过一半的文献量。方法论格局呈现“深度学习主导、多元方法并存”的特征，其中LSTM/GRU在时序预测中表现突出，但面临可解释性困境；集成学习和因果推断方法在政策评估中崭露头角。核心争议集中在“复杂模型是否必然优于简单基线”以及“黑箱模型在能源政策制定中的适用边界”。研究空白主要包括：因果推断在能源政策评估中的方法论不成熟、物理信息神经网络在能源市场的应用缺失、以及联邦学习在分布式能源系统场景下的隐私-效率权衡。未来方向应将方法论创新与实际政策问题深度耦合，推动从“预测能力”向“因果解释能力”的范式转型。

## 一、研究概况与发展脉络

### 1.1 萌芽与奠基期（2003-2017年）

机器学习在能源经济学领域的学术探索可追溯至21世纪初，但早期研究呈现零星分布特征。2003年至2017年间，年度发文量长期维持在1-2篇的低水平，且主题高度分散。这一时期的核心贡献主要来自两个方向：一是传统时间序列方法在能源需求预测中的基准建立，二是对能源系统复杂性的初步认识。

2006年，Armaroli与Balzani在《Angewandte Chemie International Edition》上发表的关于未来能源供应挑战的综述论文[5]，系统梳理了化石燃料枯竭、气候变化与能源转型之间的相互关联，为后续机器学习在能源领域的应用奠定了问题基础。这篇论文的引用量高达1909次，其核心论点——能源系统的复杂性和不确定性需要新的分析工具——成为后续研究的理论起点。

2009年，Rysman的两边市场经济学论文[6]虽然主要聚焦于平台经济理论，但其提出的双边市场概念后来被广泛应用于能源市场设计研究。这一时期的能源经济学研究仍以经典计量经济学方法为主导，机器学习尚未成为主流分析工具。

转折点出现在2016-2017年。2017年，Shi等人提出的池化深度循环神经网络用于家庭负荷预测[59]以及Qiu等人提出的基于经验模态分解的集成深度学习用于负荷需求预测[60]，标志着深度学习开始系统性进入能源预测领域。这两篇论文的共同特点是：采用端到端的深度学习架构，对比传统统计模型（如ARIMA、SVR）并展示显著优势，同时开始关注模型的可分解性和可解释性。Shi等人的研究在家庭负荷预测任务上，将平均绝对百分比误差（MAPE）从传统方法的15%左右降低至8%以下[59]，这一成果引发了学术界对深度学习方法的高度关注。

### 1.2 爆发式增长期（2018-2020年）

2018年是该领域发展的分水岭。年度发文量从前一年的2篇骤增至7篇，增幅达250%。这一爆发并非偶然，而是由多重因素共同驱动：深度学习方法在计算机视觉和自然语言处理领域的突破性进展形成技术溢出效应；能源系统智能化转型的现实需求；以及顶级期刊开始重视跨学科研究的政策导向。

2018年最具标志性的事件是Makridakis等人的论文[18]在《PLoS ONE》上发表。这篇论文系统比较了统计方法与机器学习方法在预测任务中的表现，基于M4竞赛数据集得出一个具有冲击性的结论：在多数预测任务中，简单的统计方法（如指数平滑、ARIMA）与复杂的机器学习方法表现相当，甚至在某些场景下更优。这一研究引发了学术界对“深度学习万能论”的深刻反思，也成为后续所有能源预测研究必须引用的方法论基准。

同年，François-Lavet等人发表的深度强化学习综述[7]，以及Veers关于风能科学挑战的论文[8]，分别从方法论端和应用端为机器学习-能源交叉研究提供了理论支撑。特别是Veers等明确指出，风能系统需要在湍流预测、叶片控制、场群优化等环节引入机器学习和人工智能技术[8]，这种来自工程科学领域的明确需求信号极大地推动了研究的应用落地。

2019年达到第一个研究高潮，年度发文9篇。Ghoddusi等的综述论文《Machine learning in energy economics and finance: A review》[14]成为该领域的里程碑之作。该文系统梳理了机器学习在能源价格预测、需求预测、风险管理、投资组合优化四大方向的应用，首次提出了“能源经济学的机器学习方法谱系”这一概念框架。论文不仅总结了各类方法的优劣，还识别出若干研究空白，如因果方法在能源政策评估中的应用有限、可解释性方法在能源金融市场中的缺失等。这篇论文的引用量达431次，表明其已成为该领域的标准参考文献。

与此同时，Bedi和Toshniwal提出的深度学习框架用于电力需求预测[54]，以及Wang等人在建筑热负荷预测中对比浅层机器学习与深度学习方法[53]，标志着研究从方法论探讨向实际系统应用的深化。特别是Wang等人的工作，通过系统对比支持向量回归、随机森林、深度神经网络等方法在建筑热负荷预测中的表现，发现特征工程和领域知识的引入比模型复杂度本身更为关键[53]，这一发现为后续研究提供了重要方法论启示。

2020年的8篇论文延续了这一趋势，但研究主题明显趋于聚焦。Antonopoulos等的人工智能与机器学习在能源需求侧管理中的应用综述[12]，以及Somu等提出的建筑能耗预测深度学习框架[52]，将研究领域从宏观预测延伸至微观管理。Nam等提出的基于深度学习的可再生能源场景预测模型[56]，则标志着研究开始关注新能源系统的特殊性与复杂性。

### 1.3 深化与分化期（2021-2023年）

2021-2023年间，该领域进入深化与分化并存的阶段。一方面，年度发文量维持在较高水平（2021年11篇、2022年9篇、2023年5篇），表明研究热度不减；另一方面，主题开始从“通用方法验证”向“特定问题解法”分化。

2021年，Ağbulut的论文聚焦于交通部门能源需求与CO₂排放的预测[55]，标志着研究开始从宏观能源系统向特定终端部门渗透。同年，Kumari等人针对太阳辐照度预测任务提出深度学习集成模型[61]，将研究范围扩展到可再生能源的短期波动性预测。这两篇论文的共同特点是：针对特定应用场景设计专用模型架构，而不是简单套用通用深度学习模板。

2022年，Yao等在《Nature Reviews Materials》上发表的论文《Machine learning for a sustainable energy future》[13]将研究视角从“机器学习优化能源系统”提升至“机器学习推动可持续能源转型”的战略高度。该文指出，机器学习在材料发现、电池设计、催化剂优化等领域的应用可能比其在预测任务中的贡献更具变革意义[13]。这一观点促使研究者开始关注机器学习在能源供给侧（而非仅需求侧）的应用价值。

2023年的研究呈现方法论多元化和问题精细化特征。Nadirgil在碳价预测中系统比较了多种混合机器学习模型[41]，Wazirali等人则对微电网场景下的能量和负荷预测方法进行了全面综述[66]。这些工作表明，该领域已进入“精细化验证”阶段——不再满足于展示某种方法在某个任务上的表现，而是开始系统审视方法的适用边界、数据需求、计算代价等实践问题。

## 二、方法论格局与对比

### 2.1 深度学习系列：从通用架构到领域适配

深度学习是当前能源经济学研究中使用最广泛的方法类别，但其内部存在显著分化。

**LSTM/GRU等循环架构**是该领域的主流选择。Shi等人在2017年提出的池化深度循环神经网络（Pooling Deep RNN）[59]是这一方向的开创性工作，其核心创新在于：将全局共享的池化层与个体细化的循环层相结合，在保持预测精度的同时降低了模型参数量。这一设计的优势在于能够同时利用群体模式和个体异质性，特别适用于用户级负荷预测这种“数据稀疏但群体规律性显著”的任务。然而，该方法的计算开销较大，训练时间随序列长度呈指数级增长，在超短期（分钟级）预测任务中可能面临实时性挑战。

Qiu等人提出的经验模态分解（EMD）集成深度学习[60]代表了另一种思路：先通过EMD将原始时间序列分解为多个本征模态函数，再分别用不同深度学习模型进行预测并集成输出。这一方法在非平稳、非线性序列（如电价序列、可再生能源出力序列）上表现优异，但其潜在风险同样显著。方法论审查组的辩论明确指出，分解-集成范式可能因边界效应或数据划分不当而引入未来信息，导致预测精度被严重高估。这一批评在实际应用中已被多次验证：在滚动预测设定下，EMD-LSTM模型的表现往往下降至与简单ARIMA模型相当的水平。

**卷积神经网络（CNN）** 在能源经济学中的应用相对较少，但近年来呈现增长趋势。Aslam等人的综述[51]指出，CNN在空间相关特征提取方面具有天然优势，特别适用于多站点负荷预测和区域级能源需求预测。然而，CNN对时序依赖性的捕获能力弱于循环架构，在长期预测任务中表现有限。

**深度强化学习（DRL）** 是另一个重要方向。François-Lavet等人的综述[7]系统介绍了DRL在能源系统优化中的应用潜力，包括储能调度、需求响应、微电网运行等。DRL的核心优势在于能够处理序贯决策问题，在实时、动态的能源市场环境中表现出独特价值。但其局限性同样突出：样本效率低、训练过程不稳定、对奖励函数设计高度敏感。在能源经济学应用中，这些问题被进一步放大——能源系统的状态空间巨大（涉及价格、负荷、新能源出力、设备状态等多个维度），而真实环境中的采样成本极高。

### 2.2 集成学习：稳健性的保障与“平均化陷阱”

集成学习方法在能源经济学研究中具有独特地位。Ganaie等人对集成深度学习的综述[57]是该方向的权威参考，系统总结了Bagging、Boosting、Stacking等集成策略在深度学习场景下的应用。

在能源预测任务中，随机森林和梯度提升树（如XGBoost、LightGBM）是应用最广泛的集成方法。这类方法的优势体现在多个维度：能够自动处理非线性关系；具有良好的特征重要性解释能力；对异常值和缺失数据鲁棒；计算效率相对于深度学习显著更高。

Storm等在农业经济学领域的机器学习应用综述[15]虽然不直接聚焦能源，但提供了重要的方法论洞见：在一些预测任务中，简单的集成方法（如随机森林）能够达到甚至超越复杂深度学习模型的预测精度，而计算成本仅为后者的十分之一到百分之一。这一发现与Makridakis等人的结论[18]形成呼应，共同构成对“深度学习万能论”的有力挑战。

然而，集成学习也存在“平均化陷阱”：当弱学习器之间的误差高度相关时，集成效果将大打折扣；在极端值预测（如电价尖峰、负荷异常峰值）中，集成方法往往倾向于低估变化幅度。这一局限性在能源市场的风险管理应用中尤为突出，因为尾部风险恰恰是决策者最为关注的。

### 2.3 因果推断：方法论的“蓝海”与挑战

因果推断在能源经济学中的应用是近年兴起的前沿方向。Schölkopf等人的因果表示学习综述[9]为该方向提供了理论基础，其核心思想是：传统的深度学习只能学习到关联关系，而无法区分因果和混淆，在政策评估和反事实推断任务中可能导致严重偏差。

在能源经济学场景中，这一问题的现实意义十分突出。例如，在评估碳市场价格对减排效果的影响时，传统回归方法可能因遗漏变量（如经济周期、技术进步、政策偏好）而得出有偏估计；而因果森林、双机器学习等因果推断方法能够更稳健地估计处理效应。

但当前因果推断在能源经济学中的应用存在显著方法论短板。方法论审查组的辩论指出：纯粹的深度学习模型在应用于政策评估时，“方法误用风险极高”。具体表现在：因果推断的识别假设（如非混淆性、一致性、无干扰性）在实际能源市场环境中往往难以满足；能源系统中的时空依赖性和网络效应进一步增加了识别难度；此外，现有因果方法在面板数据和高维混杂变量场景下的表现仍需进一步的实证验证。

### 2.4 新兴方法：联邦学习与物理信息融合

联邦学习和物理信息神经网络（PINN）是近年来开始进入能源经济学领域的两个前沿方向。

**联邦学习**方面，Kairouz等人的权威综述[2]提出了在保护数据隐私前提下的分布式机器学习框架。在能源场景中，联邦学习的价值尤为突出：不同能源用户、社区或企业的负荷数据涉及用户隐私，难以集中存储；而联邦学习允许在不共享原始数据的前提下训练共享模型。然而，Zhu等人的研究揭示了关键挑战：在非独立同分布数据场景下，联邦学习模型的收敛速度显著下降；用户间的异构性可能导致模型性能剧烈波动。这一“非独立同分布”问题在能源系统中十分普遍——不同用户的用电习惯、气候条件、设备类型天然存在巨大差异。

**物理信息融合**方面，Willard等人的综述[17]探讨了将科学知识（如物理定律、领域约束）嵌入机器学习模型的多种路径。在能源经济学中，这一范式具有独特价值：能源系统受物理定律（如能量守恒、热电联产效率曲线）严格约束，而纯数据驱动模型往往无法保证预测结果的物理一致性。例如，在新能源出力预测中，物理信息神经网络可以保证预测值不超过物理上可能的出力上限，从而避免违反直觉的预测结果。然而，该方向的研究仍处于早期阶段，其在能源经济学（相对于能源工程）中的应用更是凤毛麟角。

### 2.5 方法论对比矩阵

下表从六个关键维度对主要方法类别进行横向对比，为研究者选择合适方法提供参考。

| 方法类别 | 代表论文 | 预测精度 | 可解释性 | 数据需求 | 计算开销 | 趋势 |
|---------|---------|---------|---------|---------|---------|------|
| LSTM/GRU | [59] [60] | 高（短期） | 低 | 中-高 | 高 | 成熟期，潜力有限 |
| CNN | [51] | 中-高（空间相关） | 低 | 高 | 高 | 增长期，场景专化 |
| 深度强化学习 | [7] | 不适用（序贯决策） | 低 | 极高（环境交互） | 极高 | 探索期，落地困难 |
| 随机森林/XGBoost | [15] [18] | 中-高 | 中-高 | 低-中 | 低-中 | 成熟期，通用首选 |
| 因果推断 | [9] | 不适用（政策评估） | 高 | 高（识别假设） | 中 | 快速增长期，蓝海

## 参考文献

[2] Peter Kairouz, H. Brendan McMahan, Brendan Avent, 等. Advances and Open Problems in Federated Learning. *Foundations and Trends® in Machine Learning*, 2020. doi:10.1561/2200000083.  
[5] Nicola Armaroli和Vincenzo Balzani. The Future of Energy Supply: Challenges and Opportunities. *Angewandte Chemie International Edition*, 2006. doi:10.1002/anie.200602373.  
[6] Marc Rysman. The Economics of Two-Sided Markets. *The Journal of Economic Perspectives*, 2009. doi:10.1257/jep.23.3.125.  
[7] Vincent François-Lavet, Peter Henderson, Riashat Islam, 等. An Introduction to Deep Reinforcement Learning. *Foundations and Trends® in Machine Learning*, 2018. doi:10.1561/2200000071.  
[8] Paul Veers, Katherine Dykes, Eric Lantz, 等. Grand challenges in the science of wind energy. *Science*, 2019. doi:10.1126/science.aau2027.  
[9] Bernhard Schölkopf, Francesco Locatello, Stefan Bauer, 等. Toward Causal Representation Learning. *Proceedings of the IEEE*, 2021. doi:10.1109/jproc.2021.3058954.  
[12] Ioannis Antonopoulos, Valentin Robu, Benoit Couraud, 等. Artificial intelligence and machine learning approaches to energy demand-side response: A systematic review. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.109899.  
[13] Zhenpeng Yao, Yanwei Lum, Andrew Johnston, 等. Machine learning for a sustainable energy future. *Nature Reviews Materials*, 2022. doi:10.1038/s41578-022-00490-5.  
[14] Hamed Ghoddusi, Germán G. Creamer和Nima Rafizadeh. Machine learning in energy economics and finance: A review. *Energy Economics*, 2019. doi:10.1016/j.eneco.2019.05.006.  
[15] Hugo Storm, Kathy Baylis和Thomas Heckelei. Machine learning in agricultural and applied economics. *European Review of Agricultural Economics*, 2019. doi:10.1093/erae/jbz033.  
[17] Jared Willard, Xiaowei Jia, Shaoming Xu, 等. Integrating Scientific Knowledge with Machine Learning for Engineering and Environmental Systems. *ACM Computing Surveys*, 2022. doi:10.1145/3514228.  
[18] Spyros Makridakis, Evangelos Spiliotis和Vassilios Assimakopoulos. Statistical and Machine Learning forecasting methods: Concerns and ways forward. *PLoS ONE*, 2018. doi:10.1371/journal.pone.0194889.  
[41] Ozan Nadirgil. Carbon price prediction using multiple hybrid machine learning models optimized by genetic algorithm. *Journal of Environmental Management*, 2023. doi:10.1016/j.jenvman.2023.118061.  
[51] Sheraz Aslam, Herodotos Herodotou, Syed Muhammad Mohsin, 等. A survey on deep learning methods for power load and renewable energy forecasting in smart microgrids. *Renewable and Sustainable Energy Reviews*, 2021. doi:10.1016/j.rser.2021.110992.  
[52] Nivethitha Somu, M. R. Gauthama Raman和Krithi Ramamritham. A deep learning framework for building energy consumption forecast. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.110591.  
[53] Zhe Wang, Tianzhen Hong和Mary Ann Piette. Building thermal load prediction through shallow machine learning and deep learning. *Applied Energy*, 2020. doi:10.1016/j.apenergy.2020.114683.  
[54] Jatin Bedi和Durga Toshniwal. Deep learning framework to forecast electricity demand. *Applied Energy*, 2019. doi:10.1016/j.apenergy.2019.01.113.  
[55] Ümit Ağbulut. Forecasting of transportation-related energy demand and CO2 emissions in Turkey with different machine learning algorithms. *Sustainable Production and Consumption*, 2021. doi:10.1016/j.spc.2021.10.001.  
[56] KiJeon Nam, Soonho Hwangbo和ChangKyoo Yoo. A deep learning-based forecasting model for renewable energy scenarios to guide sustainable energy policy: A case study of Korea. *Renewable and Sustainable Energy Reviews*, 2020. doi:10.1016/j.rser.2020.109725.  
[57] M. A. Ganaie, Minghui Hu, A. K. Malik, 等. Ensemble deep learning: A review. *Engineering Applications of Artificial Intelligence*, 2022. doi:10.1016/j.engappai.2022.105151.  
[59] Heng Shi, Minghao Xu和Ran Li. Deep Learning for Household Load Forecasting—A Novel Pooling Deep RNN. *IEEE Transactions on Smart Grid*, 2017. doi:10.1109/tsg.2017.2686012.  
[60] Xueheng Qiu, Ye Ren, Ponnuthurai Nagaratnam Suganthan, 等. Empirical Mode Decomposition based ensemble deep learning for load demand time series forecasting. *Applied Soft Computing*, 2017. doi:10.1016/j.asoc.2017.01.015.  
[61] Pratima Kumari和Durga Toshniwal. Deep learning models for solar irradiance forecasting: A comprehensive review. *Journal of Cleaner Production*, 2021. doi:10.1016/j.jclepro.2021.128566.  
[66] Raniyah Wazirali, Elnaz Yaghoubi, Mohammed Shadi S. Abujazar, 等. State-of-the-art review on energy and load forecasting in microgrids using artificial neural networks, machine learning, and deep learning techniques. *Electric Power Systems Research*, 2023. doi:10.1016/j.epsr.2023.109792.  