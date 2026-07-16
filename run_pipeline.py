#!/usr/bin/env python3
"""
Consensus Pipeline v6.0 端到端运行脚本
主题：机器学习在能源经济学上的运用调研

v6.0 变更：
- Phase 0.5: 动态生成领域配置（替代硬编码关键词）
- Phase 3.5: QC审校（hard_filter → llm_classify → tag_layer）+ 补充搜索
- search_engine: 配置驱动的相关性过滤（exclusion_signals直接返回0.0）
- report_generator: 引用硬约束 + 置信度标注 + 检索边界与局限性章节
"""
import sys
import os
import json
import time
import requests
from datetime import datetime

# 确保模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载.env文件（密钥管理）
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)

# ============ 配置 ============
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = "deepseek-v4-pro"
TOPIC = "机器学习在能源经济学上的运用"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_output")

# easyScholar API密钥（v5.0：实时期刊分级）— 从环境变量读取
# 如需使用，请设置环境变量 EASYSCHOLAR_SECRET_KEY

os.makedirs(OUTPUT_DIR, exist_ok=True)


def llm_call(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    """统一的LLM调用函数"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": temperature,
        "max_tokens": 8192,
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  [LLM ERROR] {e}")
        return ""


def log(stage: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{stage}] {msg}")


def save_json(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log("SAVE", f"→ {path}")
    return path


def save_text(text, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    log("SAVE", f"→ {path}")
    return path


# ============ Phase 0: 需求调研 ============
def phase0_interview():
    """模拟需求调研访谈"""
    log("Phase0", "开始需求调研访谈")
    from requirement.interviewer import RequirementInterviewer

    interviewer = RequirementInterviewer(
        llm_call_fn=llm_call,
        domain_hint="academic_research",
        max_rounds=8,
    )

    # 开始
    result = interviewer.start("我想调研机器学习在能源经济学中的应用")
    log("Phase0", f"领域识别: {result['domain_name']}")
    log("Phase0", f"AI提问: {result['question']}")

    # 模拟用户回答
    answers = [
        "我关注碳价预测和能源需求预测，方法论偏机器学习（LSTM、XGBoost等）",
        "近5年，2021-2026年的论文",
        "CSSCI及以上，SCI Q1为主",
        "预期交付综述论文和组会汇报PDF",
        "目标受众是导师和同门，需要覆盖arXiv、Semantic Scholar、OpenAlex三个源",
        "需要引用网络分析，关注方法论创新和跨学科交叉点",
    ]

    for i, answer in enumerate(answers):
        result = interviewer.chat(answer)
        log("Phase0", f"Round {result['round']}: is_complete={result['is_complete']}")

        if result["is_complete"]:
            log("Phase0", "需求调研完成！")
            break
        elif result.get("question"):
            log("Phase0", f"AI追问: {result['question'][:80]}...")

    # 获取需求文档
    doc = interviewer.force_complete()
    save_json(doc.to_dict(), "phase0_requirement_doc.json")
    log("Phase0", f"需求文档: topic={doc.topic}, domain={doc.domain}")
    return doc


# ============ Phase 1: 需求结构化 ============
def phase1_structure(doc):
    """结构化需求"""
    log("Phase1", "开始需求结构化")
    from requirement.structurer import RequirementStructurer

    structurer = RequirementStructurer(llm_call_fn=llm_call)
    structured = structurer.structure(doc)

    save_json(structured.to_dict(), "phase1_structured_requirement.json")
    log("Phase1", f"结构化完成: domain_code={structured.domain_code}, "
         f"roles={len(structured.suggested_roles)}, "
         f"dept_hints={len(structured.department_hints)}")
    return structured


# ============ Phase 2: 讨论组 ============
def phase2_discussion(structured):
    """需求讨论"""
    log("Phase2", "开始需求讨论")
    from requirement.discussion_group import DiscussionGroup

    group = DiscussionGroup(llm_call_fn=llm_call)
    result = group.discuss(structured)

    save_json(result.to_dict(), "phase2_discussion_result.json")
    log("Phase2", f"讨论完成: opinions={len(result.opinions)}, "
         f"consensus={len(result.consensus_points)}, "
         f"supplements={len(result.supplements)}")
    return result


# ============ Phase 3: 配置推荐 ============
def phase3_config(structured, discussion):
    """推荐部门配置"""
    log("Phase3", "开始配置推荐")
    from requirement.config_recommender import ConfigRecommender

    recommender = ConfigRecommender(llm_call_fn=llm_call)
    config = recommender.recommend(structured, discussion)

    save_json(config, "phase3_recommended_config.json")
    log("Phase3", f"配置推荐完成: name={config.get('name','?')}, "
         f"departments={len(config.get('departments',{}))}")
    return config


# ============ Phase 4: 学术检索 ============
def phase4_search():
    """执行学术检索"""
    log("Phase4", "开始学术检索")
    from academic.search_engine import AcademicSearchEngine

    engine = AcademicSearchEngine(
        quality_levels=["S", "A", "B"],
        min_citations=5,
        min_results=20,
        include_preprints=True,
    )

    # 多关键词检索
    queries = [
        "machine learning energy economics",
        "ML carbon price prediction",
        "deep learning energy demand forecasting",
    ]

    all_papers = []
    all_preprints = []
    seen_titles = set()

    for q in queries:
        log("Phase4", f"检索: {q}")
        try:
            result = engine.search(q, max_results_per_source=30)
            papers = result["papers"]
            preprints = result["preprints"]
            stats = result["stats"]

            log("Phase4", f"  原始={stats['total_fetched']}, 去重={stats['after_dedup']}, "
                 f"筛选={stats['after_filter']}, 预印本={stats['preprint_count']}")

            for p in papers:
                title_key = p.title[:30].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_papers.append(p)

            for p in preprints:
                title_key = p.title[:30].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_preprints.append(p)

        except Exception as e:
            log("Phase4", f"  检索异常: {e}")
        
        # 每个query间隔3秒，避免SS限流
        time.sleep(3)

    log("Phase4", f"总论文={len(all_papers)}, 总预印本={len(all_preprints)}")

    # 等级统计
    level_counts = {}
    for p in all_papers:
        level_counts[p.quality_level] = level_counts.get(p.quality_level, 0) + 1
    log("Phase4", f"等级分布: {level_counts}")

    # 保存
    papers_data = [p.to_dict() for p in all_papers]
    preprints_data = [p.to_dict() for p in all_preprints]
    save_json({"papers": papers_data, "preprints": preprints_data, "level_counts": level_counts},
              "phase4_search_results.json")

    # v5.1: 记录相关性过滤日志（用于报告生成）
    relevance_log = {
        "total_before": len(all_papers),  # 去重后的数量（已在engine内部过滤了不相关论文）
        "total_after": len(all_papers),
        "filtered_out": [],
    }

    return all_papers, all_preprints, relevance_log


# ============ Phase 4 v6.0: 配置驱动的学术检索 ============
def phase4_search_v6(domain_config=None):
    """
    v6.0: 执行学术检索，使用domain_config驱动搜索词和过滤逻辑。

    如果domain_config提供了query_rotation，使用动态搜索词；
    否则回退到硬编码搜索词。
    """
    log("Phase4", "开始学术检索（v6.0: 配置驱动）")
    from academic.search_engine import AcademicSearchEngine

    # v6.0: 如果有domain_config，传入search_engine以启用配置驱动的相关性过滤
    engine = AcademicSearchEngine(
        quality_levels=["S", "A", "B"],
        min_citations=5,
        min_results=20,
        include_preprints=True,
        domain_config=domain_config,  # v6.0: 传入domain_config
    )

    # v6.0: 使用domain_config中的query_rotation作为搜索词
    if domain_config and domain_config.get("query_rotation"):
        queries = domain_config["query_rotation"]
        log("Phase4", f"使用domain_config的query_rotation: {queries[:3]}...")
    else:
        # 回退到硬编码搜索词
        queries = [
            "machine learning energy economics",
            "ML carbon price prediction",
            "deep learning energy demand forecasting",
        ]
        log("Phase4", "无domain_config，使用硬编码搜索词")

    all_papers = []
    all_preprints = []
    seen_titles = set()

    for q in queries:
        log("Phase4", f"检索: {q}")
        try:
            result = engine.search(q, max_results_per_source=30)
            papers = result["papers"]
            preprints = result["preprints"]
            stats = result["stats"]

            log("Phase4", f"  原始={stats['total_fetched']}, 去重={stats['after_dedup']}, "
                 f"筛选={stats['after_filter']}, 预印本={stats['preprint_count']}")

            for p in papers:
                title_key = p.title[:30].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_papers.append(p)

            for p in preprints:
                title_key = p.title[:30].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_preprints.append(p)

        except Exception as e:
            log("Phase4", f"  检索异常: {e}")
        
        # 每个query间隔3秒，避免SS限流
        time.sleep(3)

    log("Phase4", f"总论文={len(all_papers)}, 总预印本={len(all_preprints)}")

    # 等级统计
    level_counts = {}
    for p in all_papers:
        level_counts[p.quality_level] = level_counts.get(p.quality_level, 0) + 1
    log("Phase4", f"等级分布: {level_counts}")

    # 保存
    papers_data = [p.to_dict() for p in all_papers]
    preprints_data = [p.to_dict() for p in all_preprints]
    save_json({"papers": papers_data, "preprints": preprints_data, "level_counts": level_counts},
              "phase4_search_results.json")

    # v6.0: 相关性过滤日志（domain_config驱动的排除已在内完成）
    relevance_log = {
        "total_before": len(all_papers),
        "total_after": len(all_papers),
        "filtered_out": [],
        "domain_config_driven": domain_config is not None,
    }

    return all_papers, all_preprints, relevance_log


# ============ Phase 5: 部门辩论 ============

# 部门→论文筛选关键词映射（v5.1.5: 按部门分配相关论文）
DEPT_PAPER_FILTERS = {
    "literature_search": {"any": ["review", "survey", "overview", "systematic"]},
    "metadata_inspector": None,  # 全量
    "citation_network": {"any": ["citation", "impact", "influential", "network"]},
    "methodology_review": {"any": ["lstm", "transformer", "xgboost", "cnn", "svm", "ensemble",
                                     "reinforcement", "bayesian", "decompos", "hybrid", "forecast",
                                     "prediction", "neural", "deep learn", "machine learn",
                                     "random forest", "gru", "attention"]},
    "data_validation": {"any": ["validation", "cross", "robust", "benchmark", "comparison",
                                 "empirical", "dataset", "sample"]},
    "counter_evidence": {"any": ["limitation", "failure", "challenge", "comparison", "versus",
                                  "against", "outperform", "superior", "robust", "sensitivity"]},
    "topic_clustering": None,  # 全量
    "visualization": None,  # 全量
    "report_integration": None,  # 全量
    "programming": {"any": ["python", "code", "implementation", "framework", "open-source",
                             "pytorch", "tensorflow", "scikit", "pipeline", "algorithm"]},
    "tutorial": {"any": ["tutorial", "guide", "beginner", "introduction", "step", "practical"]},
}


def _filter_papers_for_dept(dept_key, papers, top_n=40):
    """按部门关键词筛选相关论文，返回按相关性排序的子集"""
    filters = DEPT_PAPER_FILTERS.get(dept_key)
    if filters is None:
        # 全量，但限制数量
        return papers[:top_n]

    keywords = filters.get("any", [])
    scored = []
    for p in papers:
        text = (p.title + " " + (p.abstract or "")).lower()
        score = sum(1 for kw in keywords if kw in text)
        # 质量加权：S级+2, A级+1
        if p.quality_level == 'S':
            score += 2
        elif p.quality_level == 'A':
            score += 1
        scored.append((score, p))

    scored.sort(key=lambda x: (-x[0], -x[1].citation_count))
    result = [p for s, p in scored if s > 0]
    # 至少保留15篇，不足则补充高质量论文
    if len(result) < 15:
        existing_ids = {id(p) for p in result}
        for p in papers:
            if id(p) not in existing_ids and p.quality_level in ('S', 'A'):
                result.append(p)
                existing_ids.add(id(p))
                if len(result) >= 15:
                    break
    return result[:top_n]


def _build_papers_summary(papers, max_abstract=300):
    """构建论文摘要文本供辩论使用"""
    lines = []
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.authors[:3])
        if len(p.authors) > 3:
            authors += " et al."
        abstract_text = (p.abstract or 'N/A')[:max_abstract]
        lines.append(
            f"[{i}] {p.title}\n"
            f"    作者: {authors} | 期刊: {p.journal} | 年份: {p.year} | "
            f"被引: {p.citation_count} | 等级: {p.quality_level}\n"
            f"    摘要: {abstract_text}"
        )
    return "\n".join(lines)


def phase5_debate(config, papers, preprints):
    """各部门辩论产出（v5.1.5: 按部门筛选论文+注入abstract）"""
    log("Phase5", "开始部门辩论")

    departments = config.get("departments", {})
    dept_order = config.get("dept_order", list(departments.keys()))
    debate_rounds = config.get("debate_rounds", 2)

    dept_outputs = {}

    for dept_key in dept_order:
        dept_info = departments.get(dept_key, {})
        dept_name = dept_info.get("zh_name", dept_key)
        debaters = dept_info.get("debaters", {})

        # v5.1.5: 按部门筛选相关论文
        dept_papers = _filter_papers_for_dept(dept_key, papers, top_n=40)
        papers_summary = _build_papers_summary(dept_papers, max_abstract=400)

        log("Phase5", f"部门: {dept_name} ({dept_key}), 辩手: {list(debaters.keys())}, "
            f"论文: {len(dept_papers)}/{len(papers)}")

        # 为每个部门生成辩论产出
        output = _debate_department(dept_key, dept_name, debaters, papers_summary, debate_rounds)
        dept_outputs[dept_key] = output
        save_json(output, f"phase5_dept_{dept_key}.json")

    save_json(dept_outputs, "phase5_all_dept_outputs.json")
    return dept_outputs


def _debate_department(dept_key, dept_name, debaters, papers_summary, rounds):
    """单个部门辩论"""
    debater_list = []
    for key, info in debaters.items():
        debater_list.append({
            "key": key,
            "name": info.get("zh_name", key),
            "style": info.get("zh_style", ""),
        })

    # 构建部门辩论prompt
    dept_prompt_map = {
        "literature_search": "请基于以下论文列表，分析文献检索的覆盖度和质量分布，指出检索策略的优缺点，提出补充建议。",
        "metadata_inspector": "请基于以下论文列表，审查元数据完整性，指出DOI缺失、作者信息不全等问题。",
        "citation_network": "请基于以下论文列表，分析引用网络结构，识别核心高影响力论文和学术传承脉络。",
        "methodology_review": """请基于以下论文列表，从7个维度对方法论进行系统评估：

**7维度评估框架**（每维度1-5分）：
1. 预测精度（权重0.25）：多数据集验证？RMSE/MAE是否显著优于基准？
2. 计算效率（权重0.10）：训练/推理时间？可扩展性？
3. 可解释性（权重0.15）：SHAP/LIME分析？特征重要性？
4. 数据需求（权重0.10）：最小样本量？对缺失值鲁棒性？
5. 稳健性（权重0.15）：跨市场验证？统计检验？敏感性分析？
6. 创新程度（权重0.15）：原创方法还是标准应用？
7. 可复现性（权重0.10）：代码开源？数据公开？

**方法-问题矩阵**：分析各方法在碳价预测/负荷预测/政策评估/碳排放核算/新能源消纳中的适用性

**辩论维度**：
- 深度学习是否在碳价预测中显著优于统计方法？（区分大样本vs小样本）
- 可解释性是否应成为准入门槛？（区分政策评估vs实时预测）
- 分解-集成是最优解还是过度工程？（检查未来信息泄露）
- 因果ML能否替代传统计量？（替代vs互补）""",
        "data_validation": "请基于以下论文列表，分析核心结论的交叉验证情况，指出一致性和矛盾之处。",
        "counter_evidence": """请基于以下论文列表，主动寻找与主流结论矛盾的证据。要求：

1. **每个核心发现至少1条反面证据**，格式：发现 + 反对论据 + 来源论文
2. **标注置信度**（高/中/低），标准：
   - 高：多篇S级论文一致支持，方法论争议小
   - 中：有研究支持但存在争议，或样本量有限
   - 低：初步探索阶段，论文数量少
3. **具体争议方向**：
   - 深度学习在碳价预测中是否真的优于统计方法？（小样本下可能不成立）
   - 分解-集成方法的边际收益是否递减？（简单模型调参后差距可能不大）
   - Transformer在能源时序预测中是否被高估？（中小样本过拟合风险）
   - 因果ML的稳健性是否足够？（正则化偏差可能影响因果估计）
4. **指出结论的适用边界**：在什么条件下结论不成立？""",
        "topic_clustering": "请基于以下论文列表，使用9维度（研究领域、方法论、数据类型、地理范围、时间特征、研究设计、核心发现、政策含义、技术路线）对论文进行主题聚类。",
        "visualization": "请基于以下论文列表，描述4张核心图表的设计：研究趋势时间线、方法论分布饼图、关键突破时间轴、引用网络演化图。给出每张图的数据来源和呈现建议。",
        "report_integration": "请基于以下论文列表和各部门观点，整合为最终的学术调研报告：摘要→领域概览→方法论综述→核心发现→争议与前沿→研究建议→参考文献。",
        "programming": "请基于以下论文列表，分析该领域主流的机器学习模型和工具链：\n1. 技术选型分析（对比LSTM/XGBoost/Transformer等方案）\n2. 给出碳价预测的完整可运行Python代码\n3. 调试和部署注意事项",
        "tutorial": "请基于以下论文列表，编写该领域的教程：\n1. 零基础入门教程（环境搭建→数据获取→模型训练→结果解读）\n2. 进阶实战指南（生产环境踩坑→参数调优→模型部署）\n3. 最佳实践清单（代码规范→目录结构→测试策略）",
    }

    task_prompt = dept_prompt_map.get(dept_key,
        f"请基于以下论文列表，从{dept_name}角度给出专业分析。")

    arguments = []

    # 每位辩手独立发言
    for debater in debater_list:
        system_prompt = f"""你是Consensus Pipeline的{dept_name}辩手「{debater['name']}」。
你的专业视角：{debater['style']}

{task_prompt}

【引用忠实性规则——必须严格遵守】
1. 引用论文[N]时，只能描述该论文标题和摘要中明确出现的信息
2. 严禁编造论文中不存在的具体实验结果、方法细节、数据指标或案例
3. 严禁使用"参见[N]"占位。如果对某论文内容不确定，不要引用该论文，选择你确定内容的论文代替
4. 你输出的每个[N]引用和对应描述，都将被后续环节自动校验
5. 【v6.0引用硬约束】所有论文引用必须从论文列表中选取，禁止生成列表外的引用
6. 【v6.0置信度标注】每个核心结论后面标注支撑论文数量：(N/M篇支撑，置信度🟢/🟡/🔴)

请给出你的专业分析和观点。要求：
1. 基于论文列表中的具体证据，不要空泛
2. 明确指出关键发现和问题
3. 给出可操作的建议
4. 中文输出，结构化格式"""

        user_msg = f"论文列表：\n{papers_summary[:12000]}"

        log("Phase5", f"  辩手 {debater['name']} 发言中...")
        response = llm_call(system_prompt, user_msg, temperature=0.4)

        arguments.append({
            "debater": debater["name"],
            "role": debater["key"],
            "argument": response,
        })

    # 共识整合
    if len(arguments) > 1:
        consensus_prompt = f"""你是{dept_name}的共识整合专家。以下是该部门各辩手的观点：

{json.dumps([{'name': a['debater'], 'argument': a['argument'][:2000]} for a in arguments], ensure_ascii=False, indent=2)}

请整合各方观点，输出：
1. **共识结论**：各方一致认同的关键结论
2. **分歧点**：各方存在分歧的地方
3. **最终建议**：综合各方观点的最佳建议

中文输出，结构化格式。"""

        log("Phase5", f"  {dept_name} 共识整合中...")
        consensus = llm_call(consensus_prompt, "请整合以上观点", temperature=0.2)
    else:
        consensus = arguments[0]["argument"] if arguments else ""

    return {
        "department": dept_name,
        "department_key": dept_key,
        "debater_arguments": arguments,
        "consensus": consensus,
    }


# ============ Phase 6: 交叉辩论 ============
def phase6_cross_debate(config, dept_outputs):
    """交叉辩论"""
    log("Phase6", "开始交叉辩论")

    p2_debates = config.get("p2_cross_debates", [])
    cross_results = []

    for debate_config in p2_debates:
        side_a_key = debate_config.get("side_a", "")
        side_b_key = debate_config.get("side_b", "")
        topic = debate_config.get("zh_topic", "")

        side_a_output = dept_outputs.get(side_a_key, {})
        side_b_output = dept_outputs.get(side_b_key, {})

        if not side_a_output.get("consensus") or not side_b_output.get("consensus"):
            log("Phase6", f"跳过 {side_a_key} vs {side_b_key}：缺少产出")
            continue

        log("Phase6", f"交叉辩论: {side_a_key} vs {side_b_key} — {topic}")

        cross_prompt = f"""你是交叉辩论协调员。两组部门就以下主题展开辩论：

**辩论主题**: {topic}

**{side_a_key}方观点**:
{side_a_output['consensus'][:3000]}

**{side_b_key}方观点**:
{side_b_output['consensus'][:3000]}

请分析双方的分歧和共识，输出：
1. **核心分歧**：双方最关键的3个分歧点
2. **共识基础**：双方都认同的要点
3. **协调建议**：如何在分歧中找到最优解

中文输出，结构化格式。"""

        result = llm_call(cross_prompt, f"请就「{topic}」展开交叉辩论分析", temperature=0.3)

        cross_results.append({
            "side_a": side_a_key,
            "side_b": side_b_key,
            "topic": topic,
            "result": result,
        })

    save_json(cross_results, "phase6_cross_debate_results.json")
    return cross_results


# ============ Phase 4.5: 重新分级论文（v5.1.3） ============
def reclassify_papers(papers):
    """
    用最新注册表+easyScholar重新分级论文。
    解决phase4检索时等级写死到JSON的问题——注册表更新后无需重新检索。
    """
    log("Phase4.5", "用最新注册表重新分级论文...")

    from academic.journal_classifier import classify_journal_enhanced

    changed = 0
    for p in papers:
        old_level = p.quality_level
        # 重新分类
        result = classify_journal_enhanced(p.journal or "", use_easyscholar=True)
        new_level = result.get("level", old_level)
        if new_level != old_level:
            log("Phase4.5", f"  等级变更: [{old_level}→{new_level}] {p.title[:50]}... ({p.journal})")
            p.quality_level = new_level
            changed += 1

    # 统计
    from collections import Counter
    level_counts = Counter(p.quality_level for p in papers)
    log("Phase4.5", f"重新分级完成: {changed}篇变更, 分级分布: {dict(level_counts)}")

    return papers


def backfill_abstracts(papers):
    """
    v6.0: 对S/A级论文回填abstract。
    优先使用OpenAlex（礼貌池10次/秒，基本不限流），
    OpenAlex失败时回退Semantic Scholar（1次/秒，容易429）。
    """
    log("Phase4.7", "回填S/A级论文abstract...")

    to_fill = [p for p in papers if p.quality_level in ("S", "A") and not p.abstract]
    if not to_fill:
        log("Phase4.7", "无需回填，所有S/A级论文已有abstract")
        return papers

    log("Phase4.7", f"需要回填: {len(to_fill)}篇")

    import urllib.request
    import urllib.parse as _urlp

    filled = 0
    oa_success = 0  # OpenAlex成功计数
    ss_success = 0  # Semantic Scholar成功计数

    for i, p in enumerate(to_fill):
        abstract = ""
        source = ""

        # 策略1: OpenAlex（优先，限流宽松）
        if not abstract:
            try:
                if p.doi:
                    oa_url = f"https://api.openalex.org/works/doi:{_urlp.quote_plus(p.doi)}?select=id,abstract_inverted_index"
                else:
                    oa_url = f"https://api.openalex.org/works?search={_urlp.quote_plus(p.title[:200])}&per_page=1&select=id,abstract_inverted_index"
                oa_req = urllib.request.Request(oa_url, headers={
                    "User-Agent": "ConsensusPipeline/6.0",
                    "mailto": "consensus-pipeline@research.org"  # 礼貌池
                })
                with urllib.request.urlopen(oa_req, timeout=15) as resp:
                    oa_data = json.loads(resp.read())

                # 从abstract_inverted_index还原
                aii = None
                if "abstract_inverted_index" in oa_data and oa_data["abstract_inverted_index"]:
                    aii = oa_data["abstract_inverted_index"]
                elif "results" in oa_data and oa_data["results"]:
                    for r in oa_data["results"]:
                        if r.get("abstract_inverted_index"):
                            aii = r["abstract_inverted_index"]
                            break

                if aii:
                    word_positions = []
                    for word, positions in aii.items():
                        for pos in positions:
                            word_positions.append((pos, word))
                    word_positions.sort()
                    abstract = " ".join(w for _, w in word_positions)
                    source = "OpenAlex"
                    oa_success += 1

            except urllib.error.HTTPError as e:
                log("Phase4.7", f"  OpenAlex HTTP {e.code} for: {p.title[:40]}...")
            except Exception as e:
                log("Phase4.7", f"  OpenAlex异常: {p.title[:30]}... ({e})")

            time.sleep(0.15)  # OpenAlex礼貌池：~6-7次/秒

        # 策略2: Semantic Scholar（回退，限流严格）
        if not abstract:
            try:
                if p.doi:
                    ss_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{_urlp.quote_plus(p.doi)}?fields=abstract"
                else:
                    ss_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={_urlp.quote_plus(p.title[:100])}&limit=1&fields=abstract"
                ss_req = urllib.request.Request(ss_url, headers={"User-Agent": "ConsensusPipeline/6.0"})
                with urllib.request.urlopen(ss_req, timeout=15) as resp:
                    ss_data = json.loads(resp.read())

                if "abstract" in ss_data and ss_data["abstract"]:
                    abstract = ss_data["abstract"]
                    source = "SemanticScholar"
                    ss_success += 1
                elif "data" in ss_data and ss_data["data"]:
                    for item in ss_data["data"]:
                        if item.get("abstract"):
                            abstract = item["abstract"]
                            source = "SemanticScholar"
                            ss_success += 1
                            break

            except urllib.error.HTTPError as e:
                if e.code == 429:
                    log("Phase4.7", f"  ⚠️ SS 429限流，后续仅用OpenAlex")
                    # 一旦429就不再尝试SS，避免卡死
                else:
                    log("Phase4.7", f"  SS HTTP {e.code}: {p.title[:40]}...")
            except Exception as e:
                log("Phase4.7", f"  SS异常: {p.title[:30]}... ({e})")

            time.sleep(1.5)  # SS限流间隔

        # 写入结果
        if abstract:
            p.abstract = abstract[:500]
            filled += 1
            log("Phase4.7", f"  ✓ 回填({i+1}/{len(to_fill)}) [{source}]: {p.title[:50]}...")
        else:
            log("Phase4.7", f"  ✗ 无abstract({i+1}/{len(to_fill)}): {p.title[:50]}...")

    log("Phase4.7", f"abstract回填完成: {filled}/{len(to_fill)}篇成功 (OpenAlex={oa_success}, SemanticScholar={ss_success})")

    # 统计最终abstract覆盖率
    total_sa = sum(1 for p in papers if p.quality_level in ("S", "A"))
    with_abs = sum(1 for p in papers if p.quality_level in ("S", "A") and p.abstract)
    log("Phase4.7", f"S/A级abstract覆盖率: {with_abs}/{total_sa} ({with_abs*100//max(total_sa,1)}%)")

    return papers


def filter_by_content_relevance(papers):
    """
    v5.1.7: 内容相关性过滤——S级论文也不能仅凭期刊名入选。
    检查每篇论文的标题+abstract是否与主题（能源+ML）相关，
    不相关的论文降级为C（不删除，但不进入综述引用池）。
    """
    log("Phase4.6", "内容相关性过滤（标题+abstract vs 主题关键词）...")

    # 能源领域核心词
    energy_keywords = {
        "energy", "electricity", "carbon", "power", "renewable",
        "solar", "wind", "oil", "gas", "fuel", "climate",
        "emission", "grid", "load", "price", "demand", "supply",
        "forecast", "market", "nuclear", "hydrogen", "battery",
        "能源", "电力", "碳", "电价", "负荷", "预测",
        "pv", "photovoltaic", "consumption", "heating", "cooling",
        "building energy", "smart grid", "microgrid", "storage",
        "coal", "petroleum", "lng", "cng", "thermal",
    }

    # ML/AI核心词
    ml_keywords = {
        "machine learning", "deep learning", "neural network",
        "lstm", "gru", "xgboost", "random forest", "transformer",
        "gradient boosting", "reinforcement learning", "cnn", "rnn",
        "gnn", "svm", "svr", "regression", "classification",
        "clustering", "nlp", "gan", "autoencoder", "attention",
        "ai", "artificial intelligence", "ml", "dl", "prediction",
        "forecasting model", "time series", "optimization algorithm",
        "ensemble", "bayesian", "causal inference", "transfer learning",
        "federated learning", "机器学习", "深度学习", "神经网络",
        "分解-集成", "混合模型", "集成学习",
    }

    demoted = 0
    for p in papers:
        if p.quality_level not in ("S", "A"):
            continue  # B/C级不过滤，本来引用概率低

        text = (p.title + " " + (p.abstract or "")).lower()

        has_energy = any(kw in text for kw in energy_keywords)
        has_ml = any(kw in text for kw in ml_keywords)

        if not has_energy and not has_ml:
            # 完全不相关（化学/生物/纯社科等）
            old = p.quality_level
            p.quality_level = "C"
            log("Phase4.6", f"  降级 [{old}→C] 无能源无ML: {p.title[:50]}... ({p.journal})")
            demoted += 1
        elif has_ml and not has_energy:
            # ML论文但不涉及能源领域（网络安全/医学/自然语言等）
            old = p.quality_level
            p.quality_level = "C"
            log("Phase4.6", f"  降级 [{old}→C] 有ML无能源: {p.title[:50]}... ({p.journal})")
            demoted += 1
        elif has_energy and not has_ml:
            # 能源论文但无ML——保留但标注（可作为领域背景引用）
            pass

    from collections import Counter
    level_counts = Counter(p.quality_level for p in papers)
    log("Phase4.6", f"内容相关性过滤完成: {demoted}篇降级, 分级分布: {dict(level_counts)}")

    return papers


# ============ Phase 7: 最终报告 + PDF（v5.1: 双模板 ReportGenerator） ============
def phase7_final_report(papers, preprints, dept_outputs, cross_results,
                        prog_output="", tut_output="", relevance_log=None):
    """
    生成最终报告（v5.1: 调用 ReportGenerator 双模板）

    产出两份文档：
    - final_report.md：最终交付报告（≤2000字）
    - internal_doc.md：内部工作文档（完整记录）
    """
    log("Phase7", "生成最终报告（v5.1 双模板 ReportGenerator）")

    from academic.report_generator import ReportGenerator

    rg = ReportGenerator(output_dir=OUTPUT_DIR, llm_call_fn=llm_call)

    # 提取共识结论
    consensus_points = []
    for dept_key, output in dept_outputs.items():
        if isinstance(output, dict):
            c = output.get("consensus", "")
            if c:
                consensus_points.append(f"[{dept_key}] {c}")

    # 提取事实校验摘要
    fact_check_output = dept_outputs.get("fact_check", {})
    fact_check_summary = ""
    if isinstance(fact_check_output, dict):
        fact_check_summary = fact_check_output.get("consensus", "")

    # 构建 debate_outputs（部门名→辩论内容）
    debate_outputs = {}
    for dept_key, output in dept_outputs.items():
        if isinstance(output, dict):
            dept_name = output.get("department", output.get("dept_name", dept_key))
            # 提取该部门所有辩手发言 + 共识
            parts = []
            # 1) 辩手论点（list of dict）
            debater_args = output.get("debater_arguments", [])
            if isinstance(debater_args, list):
                for arg in debater_args:
                    if isinstance(arg, dict):
                        name = arg.get("name", arg.get("debater", "辩手"))
                        argument = arg.get("argument", "")
                        if argument:
                            parts.append(f"**{name}**: {argument}")
                    elif isinstance(arg, str):
                        parts.append(f"**辩手**: {arg}")
            # 2) 共识结论
            consensus = output.get("consensus", "")
            if consensus:
                parts.append(f"**共识**: {consensus}")
            debate_outputs[dept_name] = "\n\n".join(parts) if parts else ""

    # 方法论审查数据
    method_output = dept_outputs.get("methodology_review", {})
    methodology_reviews = None
    if isinstance(method_output, dict) and method_output.get("consensus"):
        methodology_reviews = {"distribution": {}, "review_text": method_output.get("consensus", "")}

    # 调用 ReportGenerator
    result = rg.generate(
        topic=TOPIC,
        papers=papers,
        clusters=[],       # v5.1暂无ClusterResult对象
        validations=[],    # v5.1暂无ValidationResult对象
        charts=[],         # v5.1暂无ChartConfig对象
        consensus_points=consensus_points or None,
        fact_check_summary=fact_check_summary,
        debate_outputs=debate_outputs or None,
        cross_debate_results=cross_results if cross_results else None,
        methodology_reviews=methodology_reviews,
        programming_output=prog_output,
        tutorial_output=tut_output,
        relevance_filter_log=relevance_log,
    )

    log("Phase7", f"报告生成完成:")
    log("Phase7", f"  交付报告: {result['final_report']}")
    log("Phase7", f"  内部文档: {result['internal_doc']}")
    log("Phase7", f"  CSV: {result['csv']}")

    # 交付报告生成PDF
    try:
        with open(result["final_report"], "r", encoding="utf-8") as f:
            final_md = f.read()
        from pdf_exporter import markdown_to_pdf
        pdf_path = os.path.join(OUTPUT_DIR, "final_report.pdf")
        markdown_to_pdf(final_md, pdf_path, title=TOPIC)
        log("Phase7", f"交付报告PDF已生成: {pdf_path}")
    except Exception as e:
        log("Phase7", f"PDF生成失败: {e}")

    # 内部文档也生成PDF
    try:
        with open(result["internal_doc"], "r", encoding="utf-8") as f:
            internal_md = f.read()
        from pdf_exporter import markdown_to_pdf
        internal_pdf_path = os.path.join(OUTPUT_DIR, "internal_doc.pdf")
        markdown_to_pdf(internal_md, internal_pdf_path, title=f"{TOPIC} - 内部工作文档")
        log("Phase7", f"内部文档PDF已生成: {internal_pdf_path}")
    except Exception as e:
        log("Phase7", f"内部文档PDF生成失败: {e}")

    # 读取交付报告返回（兼容旧逻辑）
    with open(result["final_report"], "r", encoding="utf-8") as f:
        return f.read()


# ============ 程序部独立输出 ============
def generate_programming_output(papers):
    """生成程序部完整产出"""
    log("Programming", "生成程序部完整产出")

    prompt = f"""你是能源经济学机器学习领域的技术专家。基于以下论文，完成三大任务：

## 任务1：技术选型分析
对比以下方案，给出选型建议：
- LSTM/GRU（时序预测）
- XGBoost/LightGBM（特征驱动预测）
- Transformer（注意力机制）
- 混合模型（CNN-LSTM, Attention-XGBoost等）

每个方案给出：名称、适用场景、成熟度评级(★~★★★★★)、推荐理由

## 任务2：碳价预测完整代码
写一个完整的、可直接运行的Python碳价预测项目代码：
- 使用LSTM + XGBoost混合模型
- 数据从公开数据集获取
- 包含数据预处理、特征工程、模型训练、预测评估
- 有中文注释和类型注解

## 任务3：调试与部署注意事项
列出常见风险点和修复方案

相关论文：
{json.dumps([{'title': p.title, 'journal': p.journal, 'year': p.year, 'level': p.quality_level} for p in papers[:15]], ensure_ascii=False, indent=2)}"""

    result = llm_call(prompt, "请完成以上三大任务，中文输出，Markdown格式", temperature=0.3)
    save_text(result, "programming_output.md")
    return result


# ============ 教程部独立输出 ============
def generate_tutorial_output(papers):
    """生成教程部完整产出"""
    log("Tutorial", "生成教程部完整产出")

    prompt = f"""你是能源经济学机器学习领域的教学专家。基于以下论文，完成三大教程：

## 教程1：零基础入门教程
从环境安装开始，逐步教读者：
1. Python + Anaconda 安装
2. 必要库安装（pandas, scikit-learn, tensorflow/keras, xgboost）
3. 数据获取（从公开数据源下载能源价格数据）
4. 第一个ML模型：用XGBoost预测能源需求
5. 模型评估和结果解读

每步格式：操作 → 原因 → 预期输出 → 常见报错

## 教程2：进阶实战指南
面向有基础的读者：
1. LSTM时序预测最佳实践
2. 特征工程技巧（技术指标、滞后特征、外部变量）
3. 超参数调优（GridSearch, Optuna）
4. 部署踩坑指南

## 教程3：最佳实践清单
1. 代码规范（PEP8, 类型注解）
2. 项目目录结构
3. 实验管理（MLflow, Weights&Biases）
4. 反模式清单

相关论文：
{json.dumps([{'title': p.title, 'journal': p.journal, 'year': p.year} for p in papers[:10]], ensure_ascii=False, indent=2)}"""

    result = llm_call(prompt, "请完成以上三大教程，中文输出，Markdown格式，代码块用python标记", temperature=0.3)
    save_text(result, "tutorial_output.md")
    return result


# ============ 补充搜索（v6.0） ============
def supplement_search(domain_config, dedup_registry, round_num):
    """
    补充搜索：用query_rotation中不同的query，排除已见论文。

    v6.0: 当QC审校后有效论文不足15篇时，用domain_config中的
    query_rotation进行补充搜索，避免检索枯竭。

    Args:
        domain_config: 领域配置（含query_rotation）
        dedup_registry: 去重注册表（seen + excluded）
        round_num: 补充搜索轮次

    Returns:
        新论文列表
    """
    queries = domain_config.get("query_rotation", [])
    if not queries:
        log("Supplement", "query_rotation为空，无法补充搜索")
        return []

    # 第round_num轮用第round_num组query（循环使用）
    query = queries[round_num % len(queries)]
    log("Supplement", f"第{round_num}轮补充搜索，使用query: {query}")

    # 构建已见论文标题集合，用于排除
    seen_titles = set()
    for entry in dedup_registry.get("seen", []):
        title = entry.get("title", "")[:30].lower() if isinstance(entry, dict) else str(entry)[:30].lower()
        seen_titles.add(title)
    for entry in dedup_registry.get("excluded", []):
        title = entry.get("title", "")[:30].lower() if isinstance(entry, dict) else str(entry)[:30].lower()
        seen_titles.add(title)

    # 执行搜索
    from academic.search_engine import AcademicSearchEngine
    engine = AcademicSearchEngine(
        quality_levels=["S", "A", "B"],
        min_citations=3,  # 补充搜索放宽引用要求
        min_results=10,
        include_preprints=True,
        domain_config=domain_config,  # v6.0: 传入domain_config
    )

    try:
        result = engine.search(query, max_results_per_source=20)
        new_papers = result["papers"]

        # 排除已见论文
        filtered = []
        for p in new_papers:
            title_key = p.title[:30].lower()
            if title_key not in seen_titles:
                filtered.append(p)

        log("Supplement", f"搜索到{len(new_papers)}篇，去重后{len(filtered)}篇新论文")
        return filtered

    except Exception as e:
        log("Supplement", f"补充搜索异常: {e}")
        return []


# ============ 自我评估 ============
def self_evaluation(report, papers, dept_outputs):
    """自我评估不足"""
    log("Eval", "进行自我评估")

    papers_info = f"论文数={len(papers)}, "
    level_counts = {}
    for p in papers:
        level_counts[p.quality_level] = level_counts.get(p.quality_level, 0) + 1
    papers_info += f"等级分布={level_counts}"

    depts_info = ", ".join(f"{k}:{len(v.get('debater_arguments',[]))}辩手"
                           for k, v in dept_outputs.items())

    prompt = f"""请对以下学术调研进行客观的自我评估，指出不足和改进方向：

**调研主题**: {TOPIC}
**论文数量与质量**: {papers_info}
**参与部门**: {depts_info}

**报告摘要（前2000字）**:
{report[:2000]}

请从以下维度评估：
1. **文献覆盖度**：检索源是否充分？是否遗漏重要期刊/论文？
2. **方法论深度**：方法论分析是否到位？有没有浅尝辄止？
3. **反面证据**：是否充分寻找了反面证据？还是只做了正向综述？
4. **交叉验证**：核心结论是否经过多源验证？
5. **实用性**：程序和教程是否真的可运行？
6. **报告质量**：结构是否完整？逻辑是否清晰？
7. **整体评分**：满分10分，给出评分和理由

中文输出，每条不足给出改进建议。"""

    result = llm_call(prompt, "请给出客观的自我评估", temperature=0.2)
    save_text(result, "self_evaluation.md")
    return result


# ============ 主流程 ============
def main():
    start_time = time.time()
    log("MAIN", f"========== 共识管线 v6.0 端到端运行 ==========")
    log("MAIN", f"主题: {TOPIC}")
    log("MAIN", f"模型: {MODEL}")
    log("MAIN", f"输出目录: {OUTPUT_DIR}")

    # v6.0: 领域配置，初始为空，Phase 0.5后填充
    domain_config = None

    try:
        # Phase 0: 需求调研
        doc = phase0_interview()

        # Phase 0.5: 动态生成领域配置（v6.0新增）
        log("Phase0.5", "动态生成领域配置...")
        from domain_config_generator import generate_domain_config
        domain_config = generate_domain_config(TOPIC, llm_call, output_dir=OUTPUT_DIR)
        save_json(domain_config, "phase0.5_domain_config.json")
        log("Phase0.5", f"领域配置生成完成: exclusion_signals={len(domain_config.get('exclusion_signals', []))}, "
             f"query_rotation={len(domain_config.get('query_rotation', []))}, "
             f"tier_layers={list(domain_config.get('tier_definitions', {}).keys())}")

        # Phase 1: 结构化
        structured = phase1_structure(doc)

        # Phase 2: 讨论
        discussion = phase2_discussion(structured)

        # Phase 3: 配置推荐
        config = phase3_config(structured, discussion)

        # Phase 4: 学术检索（v6.0: 传入domain_config）
        # 修改phase4_search以使用domain_config
        papers, preprints, relevance_log = phase4_search_v6(domain_config)

        if not papers:
            log("MAIN", "⚠️ 未检索到论文，使用回退数据")
            papers = []

        # Phase 4.5: 用最新注册表重新分级论文（v5.1.3）
        papers = reclassify_papers(papers)

        # Phase 4.6: 内容相关性过滤（v5.1.7，保留作为双保险）
        papers = filter_by_content_relevance(papers)

        # Phase 4.7: 回填S/A级论文abstract（v5.1.7）
        papers = backfill_abstracts(papers)

        # Phase 3.5: QC审校（v6.0新增，在检索+分级+过滤之后、部门辩论之前）
        log("Phase3.5", "开始QC审校...")
        from quality_controller import QualityController
        qc = QualityController(llm_call_fn=llm_call, domain_config=domain_config, output_dir=OUTPUT_DIR)

        # 第一轮审校
        papers, excluded_ids, qc_stats = qc.run_qc(papers)
        log("Phase3.5", f"QC第一轮: 通过={len(papers)}, 排除={len(excluded_ids)}, "
            f"hard_filter排除={qc_stats['hard_filter_excluded']}, "
            f"llm分类排除={qc_stats['llm_classify_rejected']}")

        # 如果有效<15，补充搜索（最多3轮）
        supplement_round = 0
        while len(papers) < 15 and supplement_round < 3:
            supplement_round += 1
            log("Phase3.5", f"有效论文不足15篇（当前{len(papers)}篇），启动第{supplement_round}轮补充搜索")
            # 用query_rotation中不同的query
            # 排除已见论文（dedup_registry）
            # 新论文过QC
            new_papers = supplement_search(domain_config, qc.dedup_registry, supplement_round)
            if len(new_papers) < 5:
                log("Phase3.5", "搜索枯竭，停止补充")
                break

            # 新论文也过一遍QC
            new_papers, new_excluded, new_stats = qc.run_qc(new_papers)
            log("Phase3.5", f"新论文QC: 通过={len(new_papers)}, 排除={len(new_excluded)}")

            papers.extend(new_papers)
            # 对合并后的论文再做一轮完整QC（去重+过滤）
            papers, excluded_ids, qc_stats = qc.run_qc(papers)
            log("Phase3.5", f"第{supplement_round}轮后: 有效={len(papers)}")

            # 避免API限流
            time.sleep(3)

        log("Phase3.5", f"QC完成: 最终有效论文={len(papers)}")
        save_json(qc_stats, "phase3.5_qc_stats.json")

        # 保存QC后的论文（供下游使用）
        papers_data = [p.to_dict() for p in papers]
        save_json(papers_data, "phase3.5_qc_papers.json")

        # Phase 5: 部门辩论
        dept_outputs = phase5_debate(config, papers, preprints)

        # Phase 6: 交叉辩论
        cross_results = phase6_cross_debate(config, dept_outputs)

        # 程序部独立输出
        prog_output = generate_programming_output(papers)

        # 教程部独立输出
        tut_output = generate_tutorial_output(papers)

        # Phase 7: 最终报告（v5.1: 双模板 + 程序教程接入 + 相关性日志）
        report = phase7_final_report(papers, preprints, dept_outputs, cross_results,
                                     prog_output=prog_output, tut_output=tut_output,
                                     relevance_log=relevance_log)

        # v6.0: 引用校验（报告生成后，比对CSV删除无效引用）
        log("Phase7.5", "引用校验...")
        from quality_controller import QualityController
        qc_validate = QualityController(llm_call_fn=llm_call, domain_config=domain_config, output_dir=OUTPUT_DIR)
        csv_path = os.path.join(OUTPUT_DIR, "papers_metadata.csv")
        report = qc_validate.validate_citations(report, csv_path)
        # 保存校验后的报告
        save_text(report, "final_report_validated.md")
        log("Phase7.5", "引用校验完成")

        # 自我评估
        evaluation = self_evaluation(report, papers, dept_outputs)

        elapsed = time.time() - start_time
        log("MAIN", f"========== 全流程完成！耗时 {elapsed:.1f}s ==========")
        log("MAIN", f"产出文件目录: {OUTPUT_DIR}")

        # 打印文件清单
        for f in sorted(os.listdir(OUTPUT_DIR)):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            log("MAIN", f"  📄 {f} ({size:,} bytes)")

    except Exception as e:
        log("ERROR", f"流程异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
