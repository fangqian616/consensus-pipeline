---
AIGC:
    Label: "1"
    ContentProducer: 001191110102MACQD9K64018705
    ProduceID: 3946566099419012_0/project_7662589641924722984-files/对接文件/journal_registry_extension.md
    ReservedCode1: ""
    ContentPropagator: 001191110102MACQD9K64028705
    PropagateID: 3946566099419012#1784116308585
    ReservedCode2: ""
---
# 期刊注册表扩展

> 本文档为 Consensus Pipeline 项目扩展期刊注册表，从当前约60个期刊扩展到300+。所有期刊以Markdown表格呈现，方便小夏解析。每个期刊必须标注ISSN，这是后续 easyScholar API 查询的关键。

---

## 说明

### 学科分类体系

| 分类代码 | 学科名称 | 说明 |
|---------|---------|------|
| `cs-ai` | 计算机科学/AI | 含ML/DL/AI会议与期刊 |
| `energy-econ` | 能源经济学 | 能源政策、能源市场、能源预测 |
| `economics` | 经济学 | 微观/宏观/计量/发展经济学 |
| `management` | 管理学 | 战略管理、创新管理、组织行为 |
| `environmental` | 环境科学 | 环境政策、气候变化、可持续发展 |
| `statistics` | 统计学/计量 | 统计方法、计量经济学 |
| `operations-research` | 运筹学 | 优化、决策科学、供应链 |
| `chinese-cssci` | 中文CSSCI | 中文社会科学引文索引 |
| `interdisciplinary` | 综合/交叉 | Nature、Science等综合期刊 |

### 等级标准

| 等级 | 标准 |
|:----:|------|
| **S** | 顶刊/顶会，IF>10（或CS领域公认顶会），方法论创新标杆 |
| **A** | 权威期刊/会议，IF>4，方法论参考价值高 |
| **B** | 领域重要期刊，IF>1.5，可纳入检索范围 |

### 会议标注

对于计算机/AI领域的顶级会议，在"期刊名"列标注会议缩写，在"备注"列标注"会议"。

---

## 一、cs-ai — 计算机科学/AI（共35个）

> **关键缺口**：当前注册表完全没有AI/ML会议和期刊。ML论文大量发表在AI会议/期刊上，这是必须填补的缺口。

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| NeurIPS (Conference on Neural Information Processing Systems) | — | A | cs-ai | — | — | 会议；ML/DL领域顶会，方法论创新优于期刊 |
| ICML (International Conference on Machine Learning) | — | A | cs-ai | — | — | 会议；ML理论/方法顶会 |
| ICLR (International Conference on Learning Representations) | — | A | cs-ai | — | — | 会议；DL表征学习顶会 |
| AAAI Conference on Artificial Intelligence | — | A | cs-ai | — | — | 会议；AI综合顶会 |
| IJCAI (International Joint Conference on AI) | — | A | cs-ai | — | — | 会议；AI综合顶会 |
| CVPR (Conference on Computer Vision and Pattern Recognition) | — | A | cs-ai | — | — | 会议；计算机视觉顶会，时间序列/图像分析相关 |
| ACL (Association for Computational Linguistics) | — | A | cs-ai | — | — | 会议；NLP顶会，文本分析相关 |
| KDD (ACM SIGKDD Conference) | — | A | cs-ai | — | — | 会议；数据挖掘顶会 |
| Journal of Machine Learning Research (JMLR) | 1532-4435 | A | cs-ai | 6.8 | Q1 | ML理论顶刊，开源 |
| IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI) | 0162-8828 | S | cs-ai | 24.0 | Q1 | AI/ML/模式识别顶刊 |
| IEEE Transactions on Neural Networks and Learning Systems (TNNLS) | 2162-237X | A | cs-ai | 10.4 | Q1 | 神经网络与学习系统 |
| Artificial Intelligence | 0004-3702 | A | cs-ai | 14.0 | Q1 | AI领域旗舰期刊 |
| Machine Learning | 0885-6125 | A | cs-ai | 5.2 | Q1 | ML经典期刊 |
| Neural Networks | 0893-6080 | A | cs-ai | 8.2 | Q1 | 神经网络 |
| Pattern Recognition | 0031-3203 | A | cs-ai | 8.5 | Q1 | 模式识别 |
| IEEE Transactions on Knowledge and Data Engineering (TKDE) | 1041-4347 | A | cs-ai | 9.2 | Q1 | 数据工程与知识发现 |
| ACM Computing Surveys | 0360-0300 | A | cs-ai | 16.3 | Q1 | 计算综述 |
| IEEE Transactions on Fuzzy Systems | 1063-6706 | A | cs-ai | 11.6 | Q1 | 模糊系统 |
| Neurocomputing | 0925-2312 | B | cs-ai | 5.5 | Q1 | 神经计算 |
| Expert Systems with Applications | 0957-4174 | A | cs-ai | 8.5 | Q1 | 专家系统应用 |
| Engineering Applications of Artificial Intelligence | 0952-1976 | A | cs-ai | 7.8 | Q1 | AI工程应用 |
| Applied Soft Computing | 1568-4946 | A | cs-ai | 8.3 | Q1 | 软计算 |
| Information Sciences | 0020-0255 | A | cs-ai | 8.8 | Q1 | 信息科学 |
| Knowledge-Based Systems | 0950-7051 | A | cs-ai | 8.2 | Q1 | 知识系统 |
| Data Mining and Knowledge Discovery | 1384-5810 | A | cs-ai | 5.4 | Q1 | 数据挖掘 |
| ACM Transactions on Intelligent Systems and Technology | 2157-6904 | A | cs-ai | 5.8 | Q1 | 智能系统 |
| Neural Computing and Applications | 0941-0643 | B | cs-ai | 5.6 | Q1 | 神经计算应用 |
| Journal of Artificial Intelligence Research (JAIR) | 1076-9757 | A | cs-ai | 4.8 | Q1 | AI研究 |
| Swarm and Evolutionary Computation | 2210-6502 | A | cs-ai | 8.9 | Q1 | 群智能与进化计算 |
| IEEE Computational Intelligence Magazine | 1556-603X | A | cs-ai | 9.3 | Q1 | 计算智能 |
| Cognitive Computation | 1866-9956 | B | cs-ai | 4.2 | Q1 | 认知计算 |
| AI Magazine | 0738-4602 | B | cs-ai | 2.1 | Q3 | AI综述 |
| International Journal of Intelligent Systems | 0884-8173 | A | cs-ai | 7.2 | Q1 | 智能系统 |
| Complex & Intelligent Systems | 2199-4536 | B | cs-ai | 4.5 | Q1 | 复杂智能系统 |
| IEEE Transactions on Emerging Topics in Computational Intelligence | 2471-285X | A | cs-ai | 6.8 | Q1 | 计算智能新兴主题 |

---

## 二、energy-econ — 能源经济学（共35个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| Energy Economics | 0140-9883 | S | energy-econ | 9.0 | Q1 | 能源经济学旗舰期刊 |
| Energy Policy | 0301-4215 | S | energy-econ | 9.3 | Q1 | 能源政策 |
| Applied Energy | 0306-2619 | S | energy-econ | 11.2 | Q1 | 能源应用 |
| Renewable and Sustainable Energy Reviews | 1364-0321 | S | energy-econ | 15.9 | Q1 | 可再生能源综述 |
| Energy | 0360-5442 | A | energy-econ | 9.0 | Q1 | 能源综合 |
| Renewable Energy | 0960-1481 | A | energy-econ | 8.7 | Q1 | 可再生能源 |
| Journal of Cleaner Production | 0959-6526 | A | energy-econ | 11.1 | Q1 | 清洁生产 |
| Resources, Conservation and Recycling | 0921-3449 | A | energy-econ | 13.2 | Q1 | 资源循环 |
| IEEE Transactions on Power Systems | 0885-8950 | A | energy-econ | 7.6 | Q1 | 电力系统 |
| IEEE Transactions on Smart Grid | 1949-3053 | A | energy-econ | 9.4 | Q1 | 智能电网 |
| Electric Power Systems Research | 0378-7796 | B | energy-econ | 3.9 | Q1 | 电力系统研究 |
| International Journal of Electrical Power & Energy Systems | 0142-0615 | A | energy-econ | 5.8 | Q1 | 电力与能源系统 |
| Energy Conversion and Management | 0196-8904 | A | energy-econ | 10.4 | Q1 | 能源转换与管理 |
| Applied Thermal Engineering | 1359-4311 | B | energy-econ | 6.4 | Q1 | 应用热工程 |
| Sustainable Energy Technologies and Assessments | 2213-1388 | B | energy-econ | 7.2 | Q1 | 可持续能源技术 |
| Energy Reports | 2352-4847 | B | energy-econ | 5.2 | Q1 | 能源报告 |
| Journal of Energy Storage | 2352-152X | A | energy-econ | 9.4 | Q1 | 储能 |
| Energy and AI | 2666-5468 | A | energy-econ | 8.3 | Q1 | 能源+AI交叉 |
| Advances in Applied Energy | 2666-7924 | A | energy-econ | 7.8 | Q1 | 应用能源进展 |
| Energy Strategy Reviews | 2211-467X | B | energy-econ | 5.5 | Q1 | 能源战略 |
| Energy for Sustainable Development | 0973-0826 | B | energy-econ | 4.6 | Q1 | 可持续能源发展 |
| Utilities Policy | 0957-1787 | B | energy-econ | 3.2 | Q2 | 公用事业政策 |
| Energy Research & Social Science | 2214-6296 | A | energy-econ | 6.9 | Q1 | 能源社会科学 |
| Global Environmental Change | 0959-3780 | S | energy-econ | 8.9 | Q1 | 全球环境变化 |
| Climate Policy | 1469-3062 | B | energy-econ | 4.2 | Q1 | 气候政策 |
| Carbon Management | 1758-3004 | B | energy-econ | 3.5 | Q2 | 碳管理 |
| Greenhouse Gases: Science and Technology | 2152-3878 | B | energy-econ | 3.1 | Q2 | 温室气体 |
| Mitigation and Adaptation Strategies for Global Change | 1381-2386 | B | energy-econ | 4.0 | Q1 | 减缓与适应 |
| Environmental Innovation and Societal Transitions | 2210-4224 | A | energy-econ | 7.5 | Q1 | 环境创新 |
| Technological Forecasting and Social Change | 0040-1625 | A | energy-econ | 10.5 | Q1 | 技术预测 |
| International Journal of Sustainable Energy | 1478-6451 | B | energy-econ | 2.8 | Q3 | 可持续能源 |
| Frontiers in Energy Research | 2296-598X | B | energy-econ | 3.4 | Q2 | 能源研究前沿 |
| Sustainable Energy & Fuels | 2398-4902 | B | energy-econ | 5.1 | Q1 | 可持续能源与燃料 |
| Journal of Modern Power Systems and Clean Energy | 2196-5625 | B | energy-econ | 4.8 | Q1 | 现代电力系统与清洁能源 |
| CSEE Journal of Power and Energy Systems | 2096-0042 | B | energy-econ | 5.8 | Q1 | 中国电机工程学会电力与能源系统 |

---

## 三、economics — 经济学（共32个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| American Economic Review | 0002-8282 | S | economics | 11.5 | Q1 | 经济学顶刊 |
| Econometrica | 0012-9682 | S | economics | 8.6 | Q1 | 计量经济学顶刊 |
| Journal of Political Economy | 0022-3808 | S | economics | 9.8 | Q1 | 政治经济学顶刊 |
| Quarterly Journal of Economics | 0033-5533 | S | economics | 13.2 | Q1 | 经济学顶刊 |
| Review of Economic Studies | 0034-6527 | S | economics | 7.5 | Q1 | 经济研究评论 |
| Journal of Econometrics | 0304-4076 | S | economics | 6.8 | Q1 | 计量经济学 |
| Review of Economics and Statistics | 0034-6535 | A | economics | 5.9 | Q1 | 经济学与统计评论 |
| Economic Journal | 0013-0133 | A | economics | 5.4 | Q1 | 经济学杂志 |
| Journal of Economic Literature | 0022-0515 | S | economics | 10.8 | Q1 | 经济学文献综述 |
| Journal of Economic Perspectives | 0895-3309 | S | economics | 8.9 | Q1 | 经济学展望 |
| European Economic Review | 0014-2921 | A | economics | 4.5 | Q1 | 欧洲经济评论 |
| International Economic Review | 0020-6598 | A | economics | 4.2 | Q1 | 国际经济评论 |
| Journal of Economic Growth | 1381-4338 | A | economics | 5.6 | Q1 | 经济增长 |
| Journal of Human Resources | 0022-166X | A | economics | 5.3 | Q1 | 人力资源 |
| Journal of Development Economics | 0304-3878 | A | economics | 5.2 | Q1 | 发展经济学 |
| Journal of Public Economics | 0047-2727 | A | economics | 4.8 | Q1 | 公共经济学 |
| Journal of Environmental Economics and Management | 0095-0696 | A | economics | 5.8 | Q1 | 环境经济学 |
| Resource and Energy Economics | 0928-7655 | A | economics | 4.1 | Q1 | 资源与能源经济学 |
| American Economic Journal: Applied Economics | 1945-7782 | A | economics | 7.2 | Q1 | 应用经济学 |
| American Economic Journal: Economic Policy | 1945-7731 | A | economics | 6.8 | Q1 | 经济政策 |
| Journal of the European Economic Association | 1542-4766 | A | economics | 5.5 | Q1 | 欧洲经济协会 |
| Oxford Bulletin of Economics and Statistics | 0305-9049 | B | economics | 2.8 | Q2 | 牛津经济与统计 |
| Econometric Theory | 0266-4666 | A | economics | 3.2 | Q1 | 计量理论 |
| Journal of Applied Econometrics | 0883-7252 | A | economics | 4.0 | Q1 | 应用计量经济学 |
| Econometric Reviews | 0747-4938 | B | economics | 2.5 | Q2 | 计量评论 |
| Empirical Economics | 0377-7332 | B | economics | 2.2 | Q2 | 实证经济学 |
| Applied Economics | 0003-6846 | B | economics | 2.0 | Q2 | 应用经济学 |
| Applied Economics Letters | 1350-4851 | B | economics | 1.3 | Q3 | 应用经济学快报 |
| Economics Letters | 0165-1765 | B | economics | 1.8 | Q2 | 经济学快报 |
| World Development | 0305-750X | A | economics | 6.0 | Q1 | 世界发展 |
| Oxford Review of Economic Policy | 0266-903X | A | economics | 4.5 | Q1 | 牛津经济政策评论 |
| Annual Review of Economics | 1941-1383 | S | economics | 9.8 | Q1 | 经济学年度评论 |

---

## 四、management — 管理学（共22个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| Academy of Management Journal | 0001-4273 | S | management | 10.5 | Q1 | 管理学顶刊 |
| Academy of Management Review | 0363-7425 | S | management | 12.0 | Q1 | 管理评论顶刊 |
| Administrative Science Quarterly | 0001-8392 | S | management | 9.3 | Q1 | 管理科学 |
| Strategic Management Journal | 0143-2095 | S | management | 8.8 | Q1 | 战略管理 |
| Organization Science | 1047-7039 | S | management | 7.5 | Q1 | 组织科学 |
| Management Science | 0025-1909 | S | management | 7.2 | Q1 | 管理科学 |
| Organization Studies | 0170-8406 | A | management | 5.6 | Q1 | 组织研究 |
| Journal of Management Studies | 0022-2380 | A | management | 6.8 | Q1 | 管理研究 |
| Research Policy | 0048-7333 | A | management | 9.5 | Q1 | 研究政策，创新管理 |
| Journal of Business Ethics | 0167-4544 | A | management | 6.8 | Q1 | 商业伦理 |
| Journal of Management | 0149-2063 | A | management | 9.0 | Q1 | 管理学 |
| British Journal of Management | 1045-3172 | A | management | 5.5 | Q1 | 英国管理 |
| International Journal of Management Reviews | 1460-8545 | A | management | 8.5 | Q1 | 管理评论 |
| Academy of Management Perspectives | 1558-9080 | A | management | 6.2 | Q1 | 管理视角 |
| Journal of Operations Management | 0272-6963 | A | management | 7.8 | Q1 | 运营管理 |
| Production and Operations Management | 1059-1478 | A | management | 5.2 | Q1 | 生产与运营管理 |
| Omega | 0305-0483 | A | management | 8.2 | Q1 | 管理科学 |
| Management and Organization Review | 1740-8776 | B | management | 3.5 | Q2 | 管理与组织评论 |
| Asian Business & Management | 1472-4782 | B | management | 3.2 | Q2 | 亚洲商业管理 |
| IEEE Transactions on Engineering Management | 0018-9391 | A | management | 6.5 | Q1 | 工程管理 |
| Technovation | 0166-4972 | A | management | 8.4 | Q1 | 技术创新 |
| R&D Management | 0033-6807 | A | management | 5.5 | Q1 | 研发管理 |

---

## 五、environmental — 环境科学（共22个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| Environmental Research Letters | 1748-9326 | A | environmental | 6.8 | Q1 | 环境研究快报 |
| Science of the Total Environment | 0048-9697 | A | environmental | 9.8 | Q1 | 总体环境科学 |
| Atmospheric Environment | 1352-2310 | A | environmental | 5.5 | Q1 | 大气环境 |
| Environmental Science & Technology | 0013-936X | S | environmental | 11.4 | Q1 | 环境科学与技术 |
| Environmental Pollution | 0269-7491 | A | environmental | 8.9 | Q1 | 环境污染 |
| Journal of Environmental Management | 0301-4797 | A | environmental | 8.7 | Q1 | 环境管理 |
| Ecological Economics | 0921-8009 | A | environmental | 6.6 | Q1 | 生态经济学 |
| Annual Review of Environment and Resources | 1543-5938 | S | environmental | 14.5 | Q1 | 环境与资源年度评论 |
| Climatic Change | 0165-0009 | A | environmental | 5.3 | Q1 | 气候变化 |
| International Journal of Greenhouse Gas Control | 1750-5836 | A | environmental | 4.8 | Q1 | 温室气体控制 |
| Journal of Industrial Ecology | 1088-1980 | A | environmental | 5.8 | Q1 | 产业生态学 |
| Environmental Impact Assessment Review | 0195-9255 | A | environmental | 6.2 | Q1 | 环境影响评估 |
| Waste Management | 0956-053X | A | environmental | 8.1 | Q1 | 废物管理 |
| Resources Policy | 0301-4207 | A | environmental | 8.6 | Q1 | 资源政策 |
| Land Use Policy | 0264-8377 | A | environmental | 6.0 | Q1 | 土地利用政策 |
| Ecological Indicators | 1470-160X | B | environmental | 5.8 | Q1 | 生态指标 |
| Natural Hazards | 0921-030X | B | environmental | 3.5 | Q2 | 自然灾害 |
| Environmental Modelling & Software | 1364-8152 | A | environmental | 5.6 | Q1 | 环境建模与软件 |
| Earth's Future | 2328-4277 | A | environmental | 8.8 | Q1 | 地球未来 |
| One Earth | 2590-3322 | A | environmental | 14.0 | Q1 | 地球可持续 |
| Communications Earth & Environment | 2662-4435 | A | environmental | 8.0 | Q1 | 地球与环境通讯 |
| npj Climate and Atmospheric Science | 2397-3722 | A | environmental | 7.5 | Q1 | 气候与大气科学 |

---

## 六、chinese-cssci — 中文CSSCI（共32个）

> 中文期刊的ISSN和CN号可能因数据库而异，以下为常用标识。无ISSN的标注CN号。

| 期刊名 | ISSN/CN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| 经济研究 | 0577-9154 | S | chinese-cssci | — | — | 经济学顶刊，CSSCI |
| 管理世界 | 1002-5502 | S | chinese-cssci | — | — | 管理学顶刊，CSSCI |
| 中国社会科学 | 1002-4921 | S | chinese-cssci | — | — | 综合社科顶刊，CSSCI |
| 中国工业经济 | 1006-480X | A | chinese-cssci | — | — | CSSCI |
| 世界经济 | 1002-9621 | A | chinese-cssci | — | — | CSSCI |
| 经济学动态 | 1002-8390 | A | chinese-cssci | — | — | CSSCI |
| 数量经济技术经济研究 | 1000-3894 | A | chinese-cssci | — | — | CSSCI |
| 中国软科学 | 1005-0566 | A | chinese-cssci | — | — | CSSCI |
| 科研管理 | 1000-2995 | A | chinese-cssci | — | — | CSSCI |
| 科学学研究 | 1003-2053 | A | chinese-cssci | — | — | CSSCI |
| 中国管理科学 | 1003-207X | A | chinese-cssci | — | — | CSSCI |
| 系统工程理论与实践 | 1000-6788 | A | chinese-cssci | — | — | CSSCI |
| 资源科学 | 1007-7588 | A | chinese-cssci | — | — | CSSCI |
| 地理学报 | 0375-5444 | A | chinese-cssci | — | — | CSSCI |
| 生态学报 | 1000-0933 | A | chinese-cssci | — | — | CSSCI |
| 中国人口·资源与环境 | 1002-2104 | A | chinese-cssci | — | — | CSSCI |
| 管理评论 | 1003-1952 | B | chinese-cssci | — | — | CSSCI |
| 管理科学学报 | 1007-9807 | A | chinese-cssci | — | — | CSSCI |
| 南开管理评论 | 1008-3448 | A | chinese-cssci | — | — | CSSCI |
| 会计研究 | 1003-2886 | B | chinese-cssci | — | — | CSSCI |
| 金融研究 | 1002-7246 | A | chinese-cssci | — | — | CSSCI |
| 统计研究 | 1002-4565 | A | chinese-cssci | — | — | CSSCI |
| 财经研究 | 1001-9952 | B | chinese-cssci | — | — | CSSCI |
| 经济管理 | 1002-5766 | B | chinese-cssci | — | — | CSSCI |
| 改革 | 1003-7543 | B | chinese-cssci | — | — | CSSCI |
| 经济科学 | 1002-5839 | B | chinese-cssci | — | — | CSSCI |
| 经济评论 | 1005-3425 | B | chinese-cssci | — | — | CSSCI |
| 经济学家 | 1003-5656 | B | chinese-cssci | — | — | CSSCI |
| 当代经济科学 | 1002-2848 | B | chinese-cssci | — | — | CSSCI |
| 财经科学 | 1000-8306 | B | chinese-cssci | — | — | CSSCI |
| 经济纵横 | 1007-7685 | B | chinese-cssci | — | — | CSSCI |
| 城市与环境研究 | 2095-851X | B | chinese-cssci | — | — | CSSCI |

---

## 七、statistics — 统计学/计量（共17个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| Journal of the Royal Statistical Society: Series B (Statistical Methodology) | 1369-7412 | S | statistics | 5.8 | Q1 | 统计方法学顶刊 |
| Annals of Statistics | 0090-5364 | S | statistics | 4.5 | Q1 | 统计学年鉴 |
| Journal of the American Statistical Association (JASA) | 0162-1459 | S | statistics | 4.8 | Q1 | 美国统计学会 |
| Biometrika | 0006-3444 | A | statistics | 3.5 | Q1 | 生物统计 |
| Journal of the Royal Statistical Society: Series A (Statistics in Society) | 0964-1998 | A | statistics | 3.2 | Q1 | 社会统计 |
| Journal of the Royal Statistical Society: Series C (Applied Statistics) | 0035-9254 | A | statistics | 2.8 | Q2 | 应用统计 |
| Annals of Applied Statistics | 1932-6157 | A | statistics | 3.0 | Q1 | 应用统计学年鉴 |
| Scandinavian Journal of Statistics | 0303-6898 | B | statistics | 2.1 | Q2 | 斯堪的纳维亚统计 |
| Computational Statistics & Data Analysis | 0167-9473 | A | statistics | 2.5 | Q1 | 计算统计与数据分析 |
| Statistics and Computing | 0960-3174 | A | statistics | 3.2 | Q1 | 统计与计算 |
| Journal of Computational and Graphical Statistics | 1061-8600 | A | statistics | 2.8 | Q1 | 计算与图形统计 |
| Statistical Science | 0883-4237 | A | statistics | 3.5 | Q1 | 统计科学 |
| Journal of Business & Economic Statistics | 0735-0015 | A | statistics | 5.2 | Q1 | 商业与经济统计 |
| Econometrics and Statistics | 2452-3062 | B | statistics | 2.0 | Q2 | 计量经济学与统计 |
| TEST | 1133-0686 | B | statistics | 1.8 | Q3 | 西班牙统计 |
| Statistics in Medicine | 0277-6715 | A | statistics | 2.7 | Q1 | 医学统计 |
| Statistical Methods in Medical Research | 0962-2802 | A | statistics | 2.5 | Q1 | 医学统计方法 |

---

## 八、operations-research — 运筹学（共17个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| Operations Research | 0030-364X | S | operations-research | 4.5 | Q1 | 运筹学顶刊 |
| European Journal of Operational Research | 0377-2217 | S | operations-research | 6.4 | Q1 | 欧洲运筹学 |
| Mathematical Programming | 0025-5610 | S | operations-research | 3.8 | Q1 | 数学规划 |
| SIAM Journal on Optimization | 1052-6234 | A | operations-research | 3.2 | Q1 | 优化 |
| INFORMS Journal on Computing | 1091-9856 | A | operations-research | 3.6 | Q1 | 计算运筹 |
| Annals of Operations Research | 0254-5330 | A | operations-research | 4.2 | Q1 | 运筹学年鉴 |
| Computers & Operations Research | 0305-0548 | A | operations-research | 4.5 | Q1 | 计算机与运筹 |
| Journal of Optimization Theory and Applications | 0022-3239 | B | operations-research | 2.8 | Q2 | 优化理论与应用 |
| Optimization Letters | 1862-4472 | B | operations-research | 2.2 | Q2 | 优化快报 |
| Journal of Global Optimization | 0925-5001 | B | operations-research | 2.8 | Q2 | 全局优化 |
| Transportation Research Part E | 1366-5545 | A | operations-research | 8.5 | Q1 | 交通运筹 |
| Networks and Spatial Economics | 1566-113X | B | operations-research | 2.5 | Q2 | 网络与空间经济 |
| OR Spectrum | 0171-6468 | B | operations-research | 2.8 | Q2 | 运筹光谱 |
| Journal of the Operational Research Society | 0160-5682 | A | operations-research | 3.5 | Q1 | 运筹学会 |
| 4OR | 1619-4500 | B | operations-research | 2.0 | Q2 | 运筹学季刊 |
| TOP | 1134-5764 | B | operations-research | 1.8 | Q3 | 西班牙运筹 |
| Optimization Methods and Software | 1055-6788 | B | operations-research | 2.5 | Q2 | 优化方法与软件 |

---

## 九、interdisciplinary — 综合/交叉（共12个）

| 期刊名 | ISSN | 等级 | 学科分类 | 影响因子(2025) | JCR分区 | 备注 |
|--------|------|:----:|---------|:--------------:|:------:|------|
| Nature | 0028-0836 | S | interdisciplinary | 64.8 | Q1 | 综合顶刊，能源+ML交叉论文 |
| Science | 0036-8075 | S | interdisciplinary | 56.9 | Q1 | 综合顶刊 |
| Nature Communications | 2041-1723 | S | interdisciplinary | 16.6 | Q1 | 综合子刊 |
| PNAS (Proceedings of the National Academy of Sciences) | 0027-8424 | S | interdisciplinary | 11.1 | Q1 | 美国科学院院刊 |
| Science Advances | 2375-2548 | A | interdisciplinary | 13.6 | Q1 | 科学进展 |
| Nature Energy | 2058-7546 | S | interdisciplinary | 56.3 | Q1 | 能源子刊，主要学科energy-econ |
| Nature Climate Change | 1758-678X | S | interdisciplinary | 30.3 | Q1 | 气候变化子刊，主要学科environmental |
| Nature Sustainability | 2398-9629 | S | interdisciplinary | 27.6 | Q1 | 可持续子刊，主要学科environmental |
| PLOS ONE | 1932-6203 | B | interdisciplinary | 3.7 | Q2 | 开源综合，谨慎收录 |
| Royal Society Open Science | 2054-5703 | B | interdisciplinary | 3.2 | Q2 | 皇家学会开源 |
| Scientific Reports | 2045-2322 | B | interdisciplinary | 4.6 | Q1 | 综合子刊 |
| iScience | 2589-0042 | A | interdisciplinary | 5.8 | Q1 | Cell综合子刊 |

---

## 十、注册表使用说明

### 10.1 期刊检索优先级
1. **S级**：优先检索，论文进入最终报告的核心发现
2. **A级**：常规检索，论文进入内部文档的完整清单
3. **B级**：补充检索，仅在特定子领域或中文文献中检索

### 10.2 会议论文处理
- 会议论文标注"会议"而非"期刊"
- 会议论文的引用数以Semantic Scholar为准（Google Scholar对会议论文计数偏高）
- 顶会论文（NeurIPS/ICML/ICLR/AAAI/IJCAI）在方法论创新上视为与S级期刊等价

### 10.3 ISSN查询
- 使用 easyScholar API 的 `queryJournalByISSN` 接口验证期刊信息
- 中文期刊优先使用ISSN，无ISSN时使用CN号

### 10.4 扩展维护
- 每季度更新影响因子（来源：JCR 2025-2026）
- 新增期刊需经方法论审查组审核
- 期刊等级每年评审一次，根据实际收录论文质量调整

### 10.5 与现有注册表的合并
- 现有注册表（约60个期刊）保持不变，本表为扩展部分
- 合并时以ISSN为唯一键去重
- 如现有注册表与本表存在等级冲突，以本表为准（基于2025年最新数据）

---

> 本内容由 Coze AI 生成，请遵循相关法律法规及《人工智能生成合成内容标识办法》使用与传播。
