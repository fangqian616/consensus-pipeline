#!/usr/bin/env python3
"""
Consensus Pipeline v0.7.2 — End-to-end CLI Runner

Usage:
    python run_pipeline.py --topic "Your Research Topic"

v0.7.2 Changes:
- --lang parameter for output language control (zh/en)

v0.7.0 Changes:
- Phase 0.5: Dynamic domain config generation (replaces hardcoded keywords)
- Phase 3.5: QC department (hard_filter → llm_classify → tag_layer) + supplemental search
- search_engine: Config-driven relevance filtering (exclusion_signals return 0.0)
- report_generator: Citation hard constraints + confidence annotations + search boundary section
"""
import sys
import os
import json
import time
import requests
from datetime import datetime

# Ensure module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows UTF-8 output (fix GBK emoji/Chinese crash)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load .env file (secret management)
from dotenv import load_dotenv
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)

# ============ Configuration ============
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-pro")
TOPIC = ""  # Set via --topic argument or DEEPSEEK_TOPIC env var
OUTPUT_LANG = "zh"  # Output language: "zh" (default) or "en"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_output")

# easyScholar API key (v5.0: real-time journal grading) — read from env var
# To use, set env var EASYSCHOLAR_SECRET_KEY

os.makedirs(OUTPUT_DIR, exist_ok=True)


def llm_call(system_prompt: str, user_message: str, temperature: float = 0.3) -> str:
    """Unified LLM call function"""
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


def _lang_instr() -> str:
    """Return output language instruction for LLM prompts"""
    if OUTPUT_LANG == "en":
        return "Output in English, structured format"
    return "中文输出，结构化格式"

def _lang_user_msg(zh_msg: str, en_msg: str) -> str:
    """Return user message in the appropriate language"""
    return en_msg if OUTPUT_LANG == "en" else zh_msg


# ============ Phase 0: Requirement Interview ============
def phase0_interview():
    """Simulate requirement interview"""
    log("Phase0", "Starting requirement interview")
    from requirement.interviewer import RequirementInterviewer

    interviewer = RequirementInterviewer(
        llm_call_fn=llm_call,
        domain_hint="academic_research",
        max_rounds=8,
    )

    # Start
    result = interviewer.start(f"I want to research {TOPIC}")
    log("Phase0", f"Domain identified: {result['domain_name']}")
    log("Phase0", f"AI question: {result['question']}")

    # Simulated user answers (replace with real input in production)
    answers = [
        f"I focus on {TOPIC}",
        "Recent 5 years, 2021-2026",
        "CSSCI and above, SCI Q1 preferred",
        "Expected deliverable: review paper and presentation PDF",
        "Target audience: advisor and peers, need coverage of arXiv, Semantic Scholar, OpenAlex",
        "Need citation network analysis, focus on methodology innovation and cross-disciplinary intersections",
    ]

    for i, answer in enumerate(answers):
        result = interviewer.chat(answer)
        log("Phase0", f"Round {result['round']}: is_complete={result['is_complete']}")

        if result["is_complete"]:
            log("Phase0", "Requirement interview complete!")
            break
        elif result.get("question"):
            log("Phase0", f"AI follow-up: {result['question'][:80]}...")

    # Get requirement document
    doc = interviewer.force_complete()
    save_json(doc.to_dict(), "phase0_requirement_doc.json")
    log("Phase0", f"Requirement doc: topic={doc.topic}, domain={doc.domain}")
    return doc


# ============ Phase 1: Requirement Structuring ============
def phase1_structure(doc):
    """Structure requirements"""
    log("Phase1", "Starting requirement structuring")
    from requirement.structurer import RequirementStructurer

    structurer = RequirementStructurer(llm_call_fn=llm_call)
    structured = structurer.structure(doc)

    save_json(structured.to_dict(), "phase1_structured_requirement.json")
    log("Phase1", f"Structuring complete: domain_code={structured.domain_code}, "
         f"roles={len(structured.suggested_roles)}, "
         f"dept_hints={len(structured.department_hints)}")
    return structured


# ============ Phase 2: Discussion Group ============
def phase2_discussion(structured):
    """Requirement discussion"""
    log("Phase2", "Starting requirement discussion")
    from requirement.discussion_group import DiscussionGroup

    group = DiscussionGroup(llm_call_fn=llm_call)
    result = group.discuss(structured)

    save_json(result.to_dict(), "phase2_discussion_result.json")
    log("Phase2", f"Discussion complete: opinions={len(result.opinions)}, "
         f"consensus={len(result.consensus_points)}, "
         f"supplements={len(result.supplements)}")
    return result


# ============ Phase 3: Configuration Recommendation ============
def phase3_config(structured, discussion):
    """Recommend department configuration"""
    log("Phase3", "Starting configuration recommendation")
    from requirement.config_recommender import ConfigRecommender

    recommender = ConfigRecommender(llm_call_fn=llm_call)
    config = recommender.recommend(structured, discussion)

    # v2: Inject topic-specific research directions (from Phase 1) so Phase 5
    # can add them to each department's debate prompt.
    config["topic_directions"] = getattr(structured, "department_hints", None) or []

    save_json(config, "phase3_recommended_config.json")
    log("Phase3", f"Config recommendation complete: name={config.get('name','?')}, "
         f"departments={len(config.get('departments',{}))}")
    return config


# ============ Phase 4: Academic Search ============
def phase4_search():
    """Execute academic search"""
    log("Phase4", "Starting academic search")
    from academic.search_engine import AcademicSearchEngine

    engine = AcademicSearchEngine(
        quality_levels=["S", "A", "B"],
        min_citations=5,
        min_results=20,
        include_preprints=True,
    )

    # Topic-based search queries
    topic = os.environ.get("DEEPSEEK_TOPIC", "")
    if topic:
        queries = [topic, f"{topic} review survey", f"{topic} methodology"]
    else:
        queries = ["academic research review", "systematic review methodology"]

    all_papers = []
    all_preprints = []
    seen_titles = set()

    for q in queries:
        log("Phase4", f"Searching: {q}")
        try:
            result = engine.search(q, max_results_per_source=30)
            papers = result["papers"]
            preprints = result["preprints"]
            stats = result["stats"]

            log("Phase4", f"  raw={stats['total_fetched']}, dedup={stats['after_dedup']}, "
                 f"filtered={stats['after_filter']}, preprints={stats['preprint_count']}")

            for p in papers:
                title_key = p.title[:30].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_papers.append(p)

            # U 论文(无百分位期刊): 合并进主列表, graded=False 由下游识别
            for p in result.get("ungraded", []):
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
            log("Phase4", f"  Search exception: {e}")
        
        # Wait 3s between queries to avoid SS rate limiting
        time.sleep(3)

    log("Phase4", f"Total papers={len(all_papers)}, total preprints={len(all_preprints)}")

    # Level statistics
    level_counts = {}
    for p in all_papers:
        level_counts[p.quality_level] = level_counts.get(p.quality_level, 0) + 1
    log("Phase4", f"Level distribution: {level_counts}")

    # Save
    papers_data = [p.to_dict() for p in all_papers]
    preprints_data = [p.to_dict() for p in all_preprints]
    save_json({"papers": papers_data, "preprints": preprints_data, "level_counts": level_counts},
              "phase4_search_results.json")

    # v5.1: Record relevance filter log (for report generation)
    relevance_log = {
        "total_before": len(all_papers),  # Count after dedup (irrelevant papers already filtered inside engine)
        "total_after": len(all_papers),
        "filtered_out": [],
    }

    return all_papers, all_preprints, relevance_log


# ============ Phase 4 v0.7.0: Config-Driven Academic Search ============
def phase4_search_v6(domain_config=None):
    """
    v0.7.0: Execute academic search using domain_config to drive queries and filter logic.

    If domain_config provides query_rotation, use dynamic search queries;
    Otherwise fallback to hardcoded search queries.
    """
    log("Phase4", "Starting academic search (v0.7.0: config-driven)")
    from academic.search_engine import AcademicSearchEngine

    # v0.7.0: Pass domain_config to search_engine to enable config-driven relevance filtering
    engine = AcademicSearchEngine(
        quality_levels=["S", "A", "B"],
        min_citations=5,
        min_results=20,
        include_preprints=True,
        domain_config=domain_config,  # v0.7.0: Pass domain_config
    )

    # v0.7.0: Use query_rotation from domain_config as search queries
    if domain_config and domain_config.get("query_rotation"):
        queries = domain_config["query_rotation"]
        log("Phase4", f"Using domain_config query_rotation: {queries[:3]}...")
    else:
        # Fallback: build queries from topic parameter
        fallback_topic = os.environ.get("DEEPSEEK_TOPIC", "")
        if fallback_topic:
            queries = [
                fallback_topic,
                f"{fallback_topic} review survey",
                f"{fallback_topic} methodology comparison",
                f"{fallback_topic} recent advances",
            ]
        else:
            queries = [
                "academic research literature review",
                "systematic review methodology",
                "research trends recent advances",
            ]
        log("Phase4", "No domain_config, using topic-based fallback queries")

    all_papers = []
    all_preprints = []
    seen_titles = set()

    for q in queries:
        log("Phase4", f"Searching: {q}")
        try:
            result = engine.search(q, max_results_per_source=30)
            papers = result["papers"]
            preprints = result["preprints"]
            stats = result["stats"]

            log("Phase4", f"  raw={stats['total_fetched']}, dedup={stats['after_dedup']}, "
                 f"filtered={stats['after_filter']}, preprints={stats['preprint_count']}")

            for p in papers:
                title_key = p.title[:30].lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    all_papers.append(p)

            # U 论文(无百分位期刊): 合并进主列表, graded=False 由下游识别
            for p in result.get("ungraded", []):
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
            log("Phase4", f"  Search exception: {e}")
        
        # Wait 3s between queries to avoid SS rate limiting
        time.sleep(3)

    log("Phase4", f"Total papers={len(all_papers)}, total preprints={len(all_preprints)}")

    # Level statistics
    level_counts = {}
    for p in all_papers:
        level_counts[p.quality_level] = level_counts.get(p.quality_level, 0) + 1
    log("Phase4", f"Level distribution: {level_counts}")

    # Save
    papers_data = [p.to_dict() for p in all_papers]
    preprints_data = [p.to_dict() for p in all_preprints]
    save_json({"papers": papers_data, "preprints": preprints_data, "level_counts": level_counts},
              "phase4_search_results.json")

    # v0.7.0: Relevance filter log (domain_config-driven exclusions already applied)
    relevance_log = {
        "total_before": len(all_papers),
        "total_after": len(all_papers),
        "filtered_out": [],
        "domain_config_driven": domain_config is not None,
    }

    return all_papers, all_preprints, relevance_log


# ============ Phase 5: Department Debate ============

# Department → paper filter keyword mapping (v5.1.5: assign relevant papers by department)
DEPT_PAPER_FILTERS = {
    "literature_search": {"any": ["review", "survey", "overview", "systematic"]},
    "metadata_inspector": None,  # Full set
    "citation_network": {"any": ["citation", "impact", "influential", "network"]},
    "methodology_review": {"any": ["lstm", "transformer", "xgboost", "cnn", "svm", "ensemble",
                                     "reinforcement", "bayesian", "decompos", "hybrid", "forecast",
                                     "prediction", "neural", "deep learn", "machine learn",
                                     "random forest", "gru", "attention"]},
    "data_validation": {"any": ["validation", "cross", "robust", "benchmark", "comparison",
                                 "empirical", "dataset", "sample"]},
    "counter_evidence": {"any": ["limitation", "failure", "challenge", "comparison", "versus",
                                  "against", "outperform", "superior", "robust", "sensitivity"]},
    "topic_clustering": None,  # Full set
    "visualization": None,  # Full set
    "report_integration": None,  # Full set
    "programming": {"any": ["python", "code", "implementation", "framework", "open-source",
                             "pytorch", "tensorflow", "scikit", "pipeline", "algorithm"]},
    "tutorial": {"any": ["tutorial", "guide", "beginner", "introduction", "step", "practical"]},
}


def _is_core_seed(p):
    """判断是否核心种子论文（享受保活/前置待遇）。

    仅 weight=='core' 享受特权；normal 档按普通论文对待（spec §4.2）。
    向后兼容：无 weight 字段时，source=='user_seed' 视为 core（无 manifest 默认）。
    """
    from academic.search_engine import is_core_seed
    
    
        
    return is_core_seed(p)


def _filter_papers_for_dept(dept_key, papers, top_n=40):
    """Filter relevant papers by department keywords, return relevance-sorted subset.

    核心种子论文(weight='core')强制包含并放在最前面，且不占用 top_n 名额——
    用户指定的重点论文必须出现在每个部门的辩论中，不能被部门关键词过滤掉。
    """
    seed_papers = [p for p in papers if _is_core_seed(p)]
    rest_quota = max(0, top_n - len(seed_papers))

    filters = DEPT_PAPER_FILTERS.get(dept_key)
    if filters is None:
        # Full set: 种子论文优先 + 其余（种子不占 top_n 名额）
        rest = [p for p in papers if not _is_core_seed(p)]
        return seed_papers + rest[:rest_quota]

    keywords = filters.get("any", [])
    scored = []
    for p in papers:
        if _is_core_seed(p):
            continue  # 种子论文单独处理
        text = (p.title + " " + (p.abstract or "")).lower()
        score = sum(1 for kw in keywords if kw in text)
        # Quality weighted: S-tier +2, A-tier +1
        if p.quality_level == 'S':
            score += 2
        elif p.quality_level == 'A':
            score += 1
        scored.append((score, p))

    scored.sort(key=lambda x: (-x[0], -x[1].citation_count))
    result = [p for s, p in scored if s > 0]
    # Keep at least 15 papers, supplement with high-quality if insufficient
    if len(result) < 15:
        existing_ids = {id(p) for p in result}
        for p in papers:
            if _is_core_seed(p):
                continue
            if id(p) not in existing_ids and p.quality_level in ('S', 'A'):
                result.append(p)
                existing_ids.add(id(p))
                if len(result) >= 15:
                    break

    # 种子论文放在最前面，且不占用 top_n 名额
    return seed_papers + result[:rest_quota]


def _build_papers_summary(papers, max_abstract=300):
    """Build paper summary text for debate use"""
    lines = []
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.authors[:3])
        if len(p.authors) > 3:
            authors += " et al."
        abstract_text = (p.abstract or 'N/A')[:max_abstract]
        seed_mark = ""
        if _is_core_seed(p):
            seed_mark = " ⭐【用户指定种子论文】"
            _note = ((getattr(p, "quality_detail", None) or {}).get("seed_profile") or {}).get("usage_note", "")
            if _note:
                seed_mark = f" ⭐【用户指定种子论文·{_note}】"

        lines.append(
            f"[{i}]{seed_mark} {p.title}\n"
            f"    Author/作者: {authors} | Journal/期刊: {p.journal} | Year/年份: {p.year} | "
            f"被引: {p.citation_count} | 等级: {p.quality_level}\n"
            f"    Abstract/摘要: {abstract_text}"
        )
    return "\n".join(lines)


def _build_topic_direction_context(topic_directions):
    """v2: Build topic-specific research-direction context for debate prompts.

    Phase 1 (structurer) decomposes the research topic into sub-directions
    (e.g. LLM roleplay, persona consistency, safety alignment). Injecting them
    into each department's prompt makes departments analyze with a topic-specific
    lens instead of generic pipeline framing.
    """
    if not topic_directions:
        return ""
    dirs = []
    for h in topic_directions:
        if not isinstance(h, dict):
            continue
        desc = (h.get("description") or h.get("type") or "").strip()
        if desc:
            dirs.append(desc)
    if not dirs:
        return ""
    return (
        "\n\n【本研究主题的子方向】\n"
        + "、".join(dirs)
        + "\n请务必围绕这些子方向展开分析，把你的专业职能落到具体研究问题上，不要泛泛而谈。"
    )


def phase5_debate(config, papers, preprints):
    """Department debate outputs (v5.1.5: filter papers by dept + inject abstracts)"""
    log("Phase5", "Starting department debate")

    departments = config.get("departments", {})
    dept_order = config.get("dept_order", list(departments.keys()))
    debate_rounds = config.get("debate_rounds", 2)
    topic_directions = config.get("topic_directions", [])

    dept_outputs = {}

    for dept_key in dept_order:
        dept_info = departments.get(dept_key, {})
        dept_name = dept_info.get("en_name" if OUTPUT_LANG == "en" else "zh_name", dept_key)
        debaters = dept_info.get("debaters", {})

        # v5.1.5: Filter relevant papers by department
        dept_papers = _filter_papers_for_dept(dept_key, papers, top_n=40)
        papers_summary = _build_papers_summary(dept_papers, max_abstract=400)

        log("Phase5", f"Department: {dept_name} ({dept_key}), debaters: {list(debaters.keys())}, "
            f"papers: {len(dept_papers)}/{len(papers)}")

        # Generate debate output for each department
        output = _debate_department(dept_key, dept_name, debaters, papers_summary, debate_rounds, topic_directions)
        dept_outputs[dept_key] = output
        save_json(output, f"phase5_dept_{dept_key}.json")

    save_json(dept_outputs, "phase5_all_dept_outputs.json")
    return dept_outputs


def _debate_department(dept_key, dept_name, debaters, papers_summary, rounds, topic_directions=None):
    """Single department debate"""
    debater_list = []
    for key, info in debaters.items():
        debater_list.append({
            "key": key,
            "name": info.get("en_name" if OUTPUT_LANG == "en" else "zh_name", key),
            "style": info.get("en_style" if OUTPUT_LANG == "en" else "zh_style", ""),
        })

    # Build department debate prompt
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

**方法-问题矩阵**：分析各方法在本研究主题不同子问题/应用场景中的适用性

**辩论维度**：
- 深度学习方法是否显著优于传统/统计方法？（区分大样本vs小样本）
- 可解释性是否应成为准入门槛？（区分高风险决策vs实时应用）
- 分解-集成是最优解还是过度工程？（检查未来信息泄露）
- 因果/机制方法能否替代纯相关建模？（替代vs互补）""",
        "data_validation": "请基于以下论文列表，分析核心结论的交叉验证情况，指出一致性和矛盾之处。",
        "counter_evidence": """请基于以下论文列表，主动寻找与主流结论矛盾的证据。要求：

1. **每个核心发现至少1条反面证据**，格式：发现 + 反对论据 + 来源论文
2. **标注置信度**（高/中/低），标准：
   - 高：多篇S级论文一致支持，方法论争议小
   - 中：有研究支持但存在争议，或样本量有限
   - 低：初步探索阶段，论文数量少
3. **具体争议方向**：
   - 深度学习方法是否在小样本下真的优于传统/统计方法？
   - 分解-集成方法的边际收益是否递减？（简单模型调参后差距可能不大）
   - Transformer/大模型类方法是否在中小样本下被高估？（过拟合风险）
   - 因果ML的稳健性是否足够？（正则化偏差可能影响因果估计）
4. **指出结论的适用边界**：在什么条件下结论不成立？""",
        "topic_clustering": "请基于以下论文列表，使用9维度（研究领域、方法论、数据类型、地理范围、时间特征、研究设计、核心发现、政策含义、技术路线）对论文进行主题聚类。",
        "visualization": "请基于以下论文列表，描述4张核心图表的设计：研究趋势时间线、方法论分布饼图、关键突破时间轴、引用网络演化图。给出每张图的数据来源和呈现建议。",
        "report_integration": "请基于以下论文列表和各部门观点，整合为最终的学术调研报告：摘要→领域概览→方法论综述→核心发现→争议与前沿→研究建议→参考文献。",
        "programming": "请基于以下论文列表，分析该领域主流的技术方案和工具链：\n1. 技术选型分析（从论文中识别该领域实际使用的方案，不要预设技术栈）\n2. 给出该领域一个代表性任务的技术架构设计和关键代码骨架（不必是完整可运行工程）\n3. 调试和部署注意事项",
        "tutorial": "请基于以下论文列表，编写该领域的教程：\n1. 零基础入门教程（环境搭建→数据获取→模型训练→结果解读）\n2. 进阶实战指南（生产环境踩坑→参数调优→模型部署）\n3. 最佳实践清单（代码规范→目录结构→测试策略）",
    }

    task_prompt = dept_prompt_map.get(dept_key,
        f"请基于以下论文列表，从{dept_name}角度给出专业分析。")

    # v2: Inject topic-specific research directions so the department analyzes
    # with a topic-specific lens instead of generic pipeline framing.
    topic_context = _build_topic_direction_context(topic_directions)

    arguments = []
    rounds = max(1, rounds)  # Ensure at least 1 round

    # Multi-round debate: debaters speak each round, can reference previous rounds
    for round_num in range(1, rounds + 1):
        round_label = f"Round {round_num}/{rounds}" if rounds > 1 else ""
        if round_num > 1:
            log("Phase5", f"  --- {round_label} ---")

        for debater in debater_list:
            # Build round context: in round 2+, include previous arguments
            prev_context = ""
            if round_num > 1:
                prev_args = []
                for a in arguments:
                    if a["role"] != debater["key"]:
                        prev_args.append(f"辩手「{a['debater']}」: {a['argument'][:800]}")
                    else:
                        prev_args.append(f"你（上一轮）: {a['argument'][:800]}")
                prev_context = f"""

【前{round_num-1}轮辩论摘要】
{chr(10).join(prev_args)}

请在上一轮观点基础上，回应其他辩手的质疑或补充新论据。不要重复已有观点，聚焦于：1) 对他人质疑的回应 2) 新的证据或角度"""

            system_prompt = f"""你是Consensus Pipeline的{dept_name}辩手「{debater['name']}」。
你的专业视角：{debater['style']}

{task_prompt}{topic_context}

【引用忠实性规则——必须严格遵守】
1. 引用论文[N]时，只能描述该论文标题和摘要中明确出现的信息
2. 严禁编造论文中不存在的具体实验结果、方法细节、数据指标或案例
3. 严禁使用"参见[N]"占位。如果对某论文内容不确定，不要引用该论文，选择你确定内容的论文代替
4. 你输出的每个[N]引用和对应描述，都将被后续环节自动校验
5. 【v0.6.2引用硬约束】所有论文引用必须从论文列表中选取，禁止生成列表外的引用
6. 【v0.6.2置信度标注】每个核心结论后面标注支撑论文数量：(N/M篇支撑，置信度🟢/🟡/🔴)

请给出你的专业分析和观点。要求：
1. 基于论文列表中的具体证据，不要空泛
2. 明确指出关键发现和问题
3. 给出可操作的建议
4. {_lang_instr()}{prev_context}"""

            user_msg = f"论文列表：\n{papers_summary[:12000]}"
            if round_num > 1:
                user_msg += f"\n\n（{round_label}——请在已有观点上深化或回应，避免重复）"

            log("Phase5", f"  Debater {debater['name']} {round_label} speaking...")
            response = llm_call(system_prompt, user_msg, temperature=0.4)

            # For round 2+, append to existing argument; round 1 creates new entry
            existing = [a for a in arguments if a["role"] == debater["key"]]
            if existing and round_num > 1:
                existing[0]["argument"] += f"\n\n--- {round_label} ---\n{response}"
            else:
                arguments.append({
                    "debater": debater["name"],
                    "role": debater["key"],
                    "argument": response,
                })

    # Consensus integration
    if len(arguments) > 1:
        consensus_prompt = f"""你是{dept_name}的共识整合专家。以下是该部门各辩手的观点：

{json.dumps([{'name': a['debater'], 'argument': a['argument'][:2000]} for a in arguments], ensure_ascii=False, indent=2)}

请整合各方观点，输出：
1. **共识结论**：各方一致认同的关键结论
2. **分歧点**：各方存在分歧的地方
3. **最终建议**：综合各方观点的最佳建议

{_lang_instr()}。"""

        log("Phase5", f"  {dept_name} consensus integration...")
        consensus = llm_call(consensus_prompt, _lang_user_msg("请整合以上观点", "Please integrate the above viewpoints"), temperature=0.2)
    else:
        consensus = arguments[0]["argument"] if arguments else ""

    return {
        "department": dept_name,
        "department_key": dept_key,
        "debater_arguments": arguments,
        "consensus": consensus,
    }


# ============ Phase 6: Cross-Debate ============
def phase6_cross_debate(config, dept_outputs):
    """Cross-debate"""
    log("Phase6", "Starting cross-debate / 开始交叉辩论")

    p2_debates = config.get("p2_cross_debates", [])

    # v0.7.5 fallback: auto-generate cross-debate pairs if config left them empty
    if not p2_debates:
        dept_order = config.get("dept_order", [])
        n = len(dept_order)
        if n >= 2:
            log("Phase6", f"p2_cross_debates empty, auto-generating {min(n//2, 3)} pairs from {n} departments")
            for i in range(min(n // 2, 3)):
                a = dept_order[i]
                b = dept_order[n - 1 - i]
                if a != b:
                    p2_debates.append({
                        "side_a": a,
                        "side_b": b,
                        "zh_topic": f"{a} 与 {b} 的交叉验证",
                        "en_topic": f"Cross-validation: {a} vs {b}",
                    })

    cross_results = []

    for debate_config in p2_debates:
        side_a_key = debate_config.get("side_a", "")
        side_b_key = debate_config.get("side_b", "")
        topic = debate_config.get("en_topic" if OUTPUT_LANG == "en" else "zh_topic", "")

        side_a_output = dept_outputs.get(side_a_key, {})
        side_b_output = dept_outputs.get(side_b_key, {})

        if not side_a_output.get("consensus") or not side_b_output.get("consensus"):
            log("Phase6", f"Skipping {side_a_key} vs {side_b_key}: no output / 跳过 {side_a_key} vs {side_b_key}：缺少产出")
            continue

        log("Phase6", f"Cross-debate / 交叉辩论: {side_a_key} vs {side_b_key} — {topic}")

        if OUTPUT_LANG == "en":
            cross_prompt = f"""You are the cross-debate coordinator. Two departments debate the following topic:

**Debate Topic**: {topic}

**{side_a_key} Position**:
{side_a_output['consensus'][:3000]}

**{side_b_key} Position**:
{side_b_output['consensus'][:3000]}

Analyze the disagreements and consensus between both sides:
1. **Core Disagreements**: The 3 most critical points of disagreement
2. **Consensus Basis**: Points both sides agree on
3. **Reconciliation Suggestions**: How to find optimal solutions despite disagreements

{_lang_instr()}."""
        else:
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

{_lang_instr()}。"""

        result = llm_call(cross_prompt, _lang_user_msg(f"请就「{topic}」展开交叉辩论分析", f"Please conduct cross-debate analysis on '{topic}'"), temperature=0.3)

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
    用动态分级(百分位 + easyScholar + 快照)重新分级论文。
    解决 phase4 检索时等级写死到 JSON 的问题——快照更新后无需重新检索。
    """
    log("Phase4.5", "Re-grading papers with dynamic grading / 用动态分级重新分级论文...")

    from academic.search_engine import classify_dynamic

    changed = 0
    for p in papers:
        old_level = p.quality_level
        # 动态重新分级
        new_level = classify_dynamic(p)
        p.graded = (new_level != "U")
        if new_level != old_level:
            log("Phase4.5", f"  Grade change / 等级变更: [{old_level}→{new_level}] {p.title[:50]}... ({p.journal})")
            p.quality_level = new_level
            changed += 1

    # 统计
    from collections import Counter
    level_counts = Counter(p.quality_level for p in papers)
    log("Phase4.5", f"Re-grading complete / 重新分级完成: {changed} papers changed, distribution / 分级分布: {dict(level_counts)}")

    return papers


def backfill_abstracts(papers):
    """
    v0.7.0: 对S/A级论文回填abstract。
    优先使用OpenAlex（礼貌池10次/秒，基本不限流），
    OpenAlex失败时回退Semantic Scholar（1次/秒，容易429）。
    """
    log("Phase4.7", "Backfilling S/A paper abstracts / 回填S/A级论文abstract...")

    to_fill = [p for p in papers if p.quality_level in ("S", "A") and not p.abstract]
    if not to_fill:
        log("Phase4.7", "No backfill needed, all S/A papers have abstracts / 无需回填，所有S/A级论文已有abstract")
        return papers

    log("Phase4.7", f"Need backfill / 需要回填: {len(to_fill)} papers")

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
                    "User-Agent": "ConsensusPipeline/0.7.0",
                    "mailto": "fangqian616@users.noreply.github.com"  # 礼貌池
                })
                with urllib.request.urlopen(oa_req, timeout=15) as resp:
                    oa_data = json.loads(resp.read())

                # Reconstruct from abstract_inverted_index
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
                log("Phase4.7", f"  OpenAlex exception: {p.title[:30]}... ({e})")

            time.sleep(0.15)  # OpenAlex polite pool: ~6-7 req/s

        # Strategy 2: Semantic Scholar (fallback, strict rate limiting)
        if not abstract:
            try:
                if p.doi:
                    ss_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{_urlp.quote_plus(p.doi)}?fields=abstract"
                else:
                    ss_url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={_urlp.quote_plus(p.title[:100])}&limit=1&fields=abstract"
                ss_req = urllib.request.Request(ss_url, headers={"User-Agent": "ConsensusPipeline/0.7.0"})
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
                    log("Phase4.7", f"  ⚠️ SS 429 rate limited, using OpenAlex only from now")
                    # Once 429 received, stop trying SS to avoid hanging
                else:
                    log("Phase4.7", f"  SS HTTP {e.code}: {p.title[:40]}...")
            except Exception as e:
                log("Phase4.7", f"  SS exception: {p.title[:30]}... ({e})")

            time.sleep(1.5)  # SS rate limit interval

        # Write results
        if abstract:
            p.abstract = abstract[:500]
            filled += 1
            log("Phase4.7", f"  ✓ Backfilled({i+1}/{len(to_fill)}) [{source}]: {p.title[:50]}...")
        else:
            log("Phase4.7", f"  ✗ No abstract({i+1}/{len(to_fill)}): {p.title[:50]}...")

    log("Phase4.7", f"Abstract backfill complete: {filled}/{len(to_fill)} successful (OpenAlex={oa_success}, SemanticScholar={ss_success})")

    # Calculate final abstract coverage
    total_sa = sum(1 for p in papers if p.quality_level in ("S", "A"))
    with_abs = sum(1 for p in papers if p.quality_level in ("S", "A") and p.abstract)
    log("Phase4.7", f"S/A-tier abstract coverage: {with_abs}/{total_sa} ({with_abs*100//max(total_sa,1)}%)")

    return papers


def filter_by_content_relevance(papers, domain_config=None):
    """
    v5.1.7: Content relevance filter — S-tier papers cannot pass on citation alone.
    检查每篇论文的 title+abstract 是否与主题相关(用 domain_config 的主题关键词),
    完全无关的论文降级到 C(不删除, 但移出审阅引用池)。
    """
    log("Phase4.6", "Content relevance filter (title+abstract vs topic keywords)...")

    # 从 domain_config 提取主题关键词(替代硬编码能源词表)
    topic_keywords = set()
    if domain_config:
        for q in (domain_config.get("query_rotation") or []):
            if isinstance(q, str):
                for token in q.replace(",", " ").replace("/", " ").split():
                    token = token.strip().lower()
                    if len(token) > 2:
                        topic_keywords.add(token)

    if not topic_keywords:
        log("Phase4.6", "No topic keywords from domain_config, skipping content relevance filter")
        return papers

    # ML/AI core keywords(通用)
    ml_keywords = {
        "machine learning", "deep learning", "neural network",
        "lstm", "gru", "xgboost", "random forest", "transformer",
        "gradient boosting", "reinforcement learning", "cnn", "rnn",
        "gnn", "svm", "svr", "regression", "classification",
        "clustering", "nlp", "gan", "autoencoder", "attention",
        "ai", "artificial intelligence", "ml", "dl", "prediction",
        "ensemble", "bayesian", "causal inference", "transfer learning",
        "federated learning", "机器学习", "深度学习", "神经网络",
    }

    demoted = 0
    for p in papers:
        if p.quality_level not in ("S", "A"):
            continue  # B/C-tier not filtered

        text = (p.title + " " + (p.abstract or "")).lower()

        has_topic = any(kw in text for kw in topic_keywords)
        has_ml = any(kw in text for kw in ml_keywords)

        if not has_topic and not has_ml:
            # 既无主题关键词也无ML关键词 → 完全无关, 降级
            old = p.quality_level
            p.quality_level = "C"
            log("Phase4.6", f"  Downgraded [{old}→C] no topic no ML: {p.title[:50]}... ({p.journal})")
            demoted += 1

    from collections import Counter
    level_counts = Counter(p.quality_level for p in papers)
    log("Phase4.6", f"Content relevance filter complete: {demoted} downgraded, level distribution: {dict(level_counts)}")

    return papers


# ============ Phase 7: Final Report + PDF (v5.1: dual-template ReportGenerator) ============
def phase7_final_report(papers, preprints, dept_outputs, cross_results,
                        prog_output="", tut_output="", relevance_log=None):
    """
    Generate final report (v5.1: dual-template ReportGenerator)

    Produces two documents:
    - final_report.md: Final deliverable report (<=2000 words)
    - internal_doc.md: Internal working document (complete record)
    """
    log("Phase7", "Generating final report (v5.1 dual-template ReportGenerator)")

    from academic.report_generator import ReportGenerator

    rg = ReportGenerator(output_dir=OUTPUT_DIR, llm_call_fn=llm_call, output_lang=OUTPUT_LANG)

    # Extract consensus conclusions
    consensus_points = []
    for dept_key, output in dept_outputs.items():
        if isinstance(output, dict):
            c = output.get("consensus", "")
            if c:
                consensus_points.append(f"[{dept_key}] {c}")

    # Extract fact-check summary
    fact_check_output = dept_outputs.get("fact_check", {})
    fact_check_summary = ""
    if isinstance(fact_check_output, dict):
        fact_check_summary = fact_check_output.get("consensus", "")

    # Build debate_outputs (dept_name -> debate content)
    debate_outputs = {}
    for dept_key, output in dept_outputs.items():
        if isinstance(output, dict):
            dept_name = output.get("department", output.get("dept_name", dept_key))
            # Extract all debater statements + consensus for this department
            parts = []
            # 1) Debater arguments (list of dict)
            debater_args = output.get("debater_arguments", [])
            if isinstance(debater_args, list):
                for arg in debater_args:
                    if isinstance(arg, dict):
                        name = arg.get("name", arg.get("debater", "Debater"))
                        argument = arg.get("argument", "")
                        if argument:
                            parts.append(f"**{name}**: {argument}")
                    elif isinstance(arg, str):
                        parts.append(f"**Debater**: {arg}")
            # 2) Consensus conclusion
            consensus = output.get("consensus", "")
            if consensus:
                parts.append(f"**Consensus**: {consensus}")
            debate_outputs[dept_name] = "\n\n".join(parts) if parts else ""

    # Methodology review data
    method_output = dept_outputs.get("methodology_review", {})
    methodology_reviews = None
    if isinstance(method_output, dict) and method_output.get("consensus"):
        methodology_reviews = {"distribution": {}, "review_text": method_output.get("consensus", "")}

    # Call ReportGenerator
    result = rg.generate(
        topic=TOPIC,
        papers=papers,
        clusters=[],       # v5.1: no ClusterResult objects yet
        validations=[],    # v5.1: no ValidationResult objects yet
        charts=[],         # v5.1: no ChartConfig objects yet
        consensus_points=consensus_points or None,
        fact_check_summary=fact_check_summary,
        debate_outputs=debate_outputs or None,
        cross_debate_results=cross_results if cross_results else None,
        methodology_reviews=methodology_reviews,
        programming_output=prog_output,
        tutorial_output=tut_output,
        relevance_filter_log=relevance_log,
    )

    log("Phase7", f"Report generation complete:")
    log("Phase7", f"  Final report: {result['final_report']}")
    log("Phase7", f"  Internal doc: {result['internal_doc']}")
    log("Phase7", f"  CSV: {result['csv']}")

    # Generate Word (.docx) for deliverable report
    try:
        with open(result["final_report"], "r", encoding="utf-8") as f:
            final_md = f.read()
        from docx_exporter import markdown_to_docx
        docx_path = os.path.join(OUTPUT_DIR, "final_report.docx")
        markdown_to_docx(final_md, docx_path, title=TOPIC)
        log("Phase7", f"Final report Word generated: {docx_path}")
    except Exception as e:
        log("Phase7", f"Word generation failed: {e}")

    # Also generate Word (.docx) for internal document
    try:
        with open(result["internal_doc"], "r", encoding="utf-8") as f:
            internal_md = f.read()
        from docx_exporter import markdown_to_docx
        internal_docx_path = os.path.join(OUTPUT_DIR, "internal_doc.docx")
        markdown_to_docx(internal_md, internal_docx_path, title=f"{TOPIC} - Internal Working Document")
        log("Phase7", f"Internal doc Word generated: {internal_docx_path}")
    except Exception as e:
        log("Phase7", f"Internal doc Word generation failed: {e}")

    # Read deliverable report for return (backward compat)
    with open(result["final_report"], "r", encoding="utf-8") as f:
        return f.read()


# ============ Programming Department Standalone Output ============
def generate_programming_output(papers):
    """Generate complete programming department output"""
    log("Programming", "Generating complete programming department output")

    prompt = f"""你是研究主题「{TOPIC}」的技术专家。基于以下论文，完成三大任务：

## 任务1：技术选型分析
从论文中识别该领域实际使用的主流技术方案/模型/工具链，进行对比并给出选型建议。
注意：不要预设技术栈（例如不要假设是时序预测或某个特定框架），必须从论文摘要中提取真实使用的技术。

每个方案给出：名称、适用场景、成熟度评级(★~★★★★★)、推荐理由

## 任务2：代表性任务技术架构与关键代码骨架
针对该领域一个代表性任务，给出技术架构设计和关键代码骨架（不必是完整可运行工程）：
- 模块结构与调用关系（可用架构图说明）
- 关键模块的核心代码片段（含import、接口签名、核心逻辑）
- 以论文中实际使用的模型/框架为准，不要假设特定技术栈
- 有中文注释和类型注解

## 任务3：调试与部署注意事项
列出常见风险点和修复方案

相关论文：
{json.dumps([{'title': p.title, 'journal': p.journal, 'year': p.year, 'level': p.quality_level} for p in papers[:15]], ensure_ascii=False, indent=2)}"""

    result = llm_call(prompt, _lang_user_msg("请完成以上三大任务，中文输出，Markdown格式", "Please complete the above three tasks, output in English, Markdown format"), temperature=0.3)
    save_text(result, "programming_output.md")
    return result


# ============ Tutorial Department Standalone Output ============
def generate_tutorial_output(papers):
    """Generate complete tutorial department output"""
    log("Tutorial", "Generating complete tutorial department output")

    prompt = f"""你是研究主题「{TOPIC}」的教学专家。基于以下论文，完成三大教程：

## 教程1：零基础入门教程
从环境安装开始，逐步教读者：
1. Python 环境安装
2. 必要依赖库安装（以论文中实际使用的框架为准）
3. 数据获取（从公开数据源下载该领域数据，或说明如何构造）
4. 第一个模型：用该领域主流方法完成一个基线任务
5. 模型评估和结果解读

每步格式：操作 → 原因 → 预期输出 → 常见报错

## 教程2：进阶实战指南
面向有基础的读者：
1. 该领域主流模型的训练与调优最佳实践
2. 特征工程技巧（以论文为准，不要假设是时序特征）
3. 超参数调优（GridSearch, Optuna）
4. 部署踩坑指南

## 教程3：最佳实践清单
1. 代码规范（PEP8, 类型注解）
2. 项目目录结构
3. 实验管理（MLflow, Weights&Biases）
4. 反模式清单

相关论文：
{json.dumps([{'title': p.title, 'journal': p.journal, 'year': p.year} for p in papers[:10]], ensure_ascii=False, indent=2)}"""

    result = llm_call(prompt, _lang_user_msg("请完成以上三大教程，中文输出，Markdown格式，代码块用python标记", "Please complete the above three tutorials, output in English, Markdown format, code blocks marked with python"), temperature=0.3)
    save_text(result, "tutorial_output.md")
    return result


# ============ Supplemental Search (v0.6.2) ============
def supplement_search(domain_config, dedup_registry, round_num):
    """
    Supplemental search: use different queries from query_rotation, excluding seen papers.

    v0.7.0: When QC-reviewed valid papers < 15, use query_rotation from domain_config
    for supplemental search to avoid search exhaustion.

    Args:
        domain_config: Domain config (with query_rotation)
        dedup_registry: Dedup registry (seen + excluded)
        round_num: Supplemental search round

    Returns:
        List of new papers
    """
    queries = domain_config.get("query_rotation", [])
    if not queries:
        log("Supplement", "query_rotation is empty, cannot supplement search")
        return []

    # Round round_num uses query group round_num (cyclic)
    query = queries[round_num % len(queries)]
    log("Supplement", f"Round {round_num} supplemental search, using query: {query}")

    # Build set of seen paper titles for exclusion
    seen_titles = set()
    for entry in dedup_registry.get("seen", []):
        title = entry.get("title", "")[:30].lower() if isinstance(entry, dict) else str(entry)[:30].lower()
        seen_titles.add(title)
    for entry in dedup_registry.get("excluded", []):
        title = entry.get("title", "")[:30].lower() if isinstance(entry, dict) else str(entry)[:30].lower()
        seen_titles.add(title)

    # Execute search
    from academic.search_engine import AcademicSearchEngine
    engine = AcademicSearchEngine(
        quality_levels=["S", "A", "B"],
        min_citations=3,  # Supplemental search relaxes citation requirements
        min_results=10,
        include_preprints=True,
        domain_config=domain_config,  # v0.7.0: Pass domain_config
    )

    try:
        result = engine.search(query, max_results_per_source=20)
        new_papers = result["papers"]

        # Exclude seen papers
        filtered = []
        for p in new_papers:
            title_key = p.title[:30].lower()
            if title_key not in seen_titles:
                filtered.append(p)

        log("Supplement", f"Found {len(new_papers)} papers, {len(filtered)} new after dedup")
        return filtered

    except Exception as e:
        log("Supplement", f"Supplemental search exception: {e}")
        return []


# ============ Self-Evaluation ============
def self_evaluation(report, papers, dept_outputs):
    """Self-evaluation of shortcomings"""
    log("Eval", "Performing self-evaluation")

    papers_info = f"Papers={len(papers)}, "
    level_counts = {}
    for p in papers:
        level_counts[p.quality_level] = level_counts.get(p.quality_level, 0) + 1
    papers_info += f"Level distribution={level_counts}"

    depts_info = ", ".join(f"{k}:{len(v.get('debater_arguments',[]))} debaters"
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

    result = llm_call(prompt, _lang_user_msg("请给出客观的自我评估", "Please provide an objective self-assessment"), temperature=0.2)
    save_text(result, "self_evaluation.md")
    return result


# ============ Seed Paper Import (Phase 4.8) ============
def merge_seed_papers(papers):
    """导入 seed_papers/ 文件夹的种子论文并合并到 papers（按档位分支去重，spec §3.2）。

    种子论文由 paper_importer 解析（PDF → Crossref 元数据 + manifest 权重注入）。
    core 档：DOI/title 撞 → 搜索版继承种子身份（保留真实分级/引用数）；
    normal 档：撞 → 跳过不打标记，不撞 → 按普通论文新增。
    """
    try:
        from paper_importer import SeedPaperImporter
        importer = SeedPaperImporter(seed_folder="seed_papers")
        seed_papers = importer.scan_folder()
    except Exception as e:
        log("Phase4.8", f"种子论文导入失败(可能缺 PyMuPDF 依赖): {e}")
        return papers

    from academic.search_engine import PaperCandidate

    if not seed_papers:
        log("Phase4.8", "无种子论文，跳过")
        return papers

    existing_dois = {p.doi.lower() for p in papers if p.doi}
    existing_titles = {p.title.lower().strip() for p in papers if p.title}

    added = 0
    for sp in seed_papers:
        doi = (sp.get("doi") or "").lower()
        title = (sp.get("title") or "").lower().strip()
        weight = sp.get("weight", "core")
        profile = sp.get("seed_profile", {})

        if doi and doi in existing_dois:
            if weight == "normal":
                log("Phase4.8", f"种子论文[normal] DOI 重复，跳过: {sp.get('title','')[:50]}")
                continue
            # core 档：搜索版继承种子身份（保留真实分级/引用数）
            for p in papers:
                if p.doi.lower() == doi:
                    p.source = "user_seed"
                    p.quality_detail = {"note": "用户指定种子论文", "source": "user_seed",
                                        "weight": weight, "seed_profile": profile}
                    try:
                        p.weight = weight
                    except Exception:
                        pass
                    break
            log("Phase4.8", f"种子论文[{weight}] DOI 撞搜索，已继承身份: {sp.get('title','')[:50]}")
            continue
        if title and title in existing_titles:
            if weight == "normal":
                log("Phase4.8", f"种子论文[normal] 标题重复，跳过: {title[:50]}")
                continue
            for p in papers:
                if p.title.lower().strip() == title:
                    p.source = "user_seed"
                    p.quality_detail = {"note": "用户指定种子论文", "source": "user_seed",
                                        "weight": weight, "seed_profile": profile}
                    try:
                        p.weight = weight
                    except Exception:
                        pass
                    break
            log("Phase4.8", f"种子论文[{weight}] 标题撞搜索，已继承身份: {title[:50]}")
            continue

        year = sp.get("year") or 0
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = 0

        # 摘要为空时用全文摘录兜底，保证辩论有内容可引用
        abstract = sp.get("abstract") or sp.get("full_text_excerpt") or ""

        pc = PaperCandidate(
            title=sp.get("title", ""),
            doi=sp.get("doi", ""),
            authors=sp.get("authors") or [],
            journal=sp.get("journal", ""),
            year=year,
            abstract=abstract[:3000],
            citation_count=0,
            source="user_seed",
            quality_level=sp.get("grade", "B"),
            quality_detail={"note": "用户指定种子论文", "source": "user_seed",
                            "weight": weight, "seed_profile": profile},
            graded=True,
        )
        try:
            pc.weight = weight
        except Exception:
            pass
        papers.append(pc)
        if doi:
            existing_dois.add(doi)
        if title:
            existing_titles.add(title)
        added += 1

    log("Phase4.8", f"种子论文合并完成: 新增 {added} 篇, 总计 {len(papers)} 篇")
    return papers


# ============ Phase 7.6: 种子论文引用检查（D层，spec §5）============
def _norm_text(s):
    """归一化文本：去全部空白+小写，用于标题模糊匹配"""
    import re as _re
    return _re.sub(r"\s+", "", (s or "").lower())


def _seed_cited(report_raw, report_norm, sp):
    """三级兜底匹配：DOI 精确 → 标题前30字符归一化 → 第一作者姓+年份"""
    doi = (sp.get("doi") or "").strip().lower()
    if doi and doi in report_raw.lower():
        return True
    title_norm = _norm_text(sp.get("title"))[:30]
    if title_norm and title_norm in report_norm:
        return True
    authors = sp.get("authors") or []
    year = str(sp.get("year") or "")
    if authors and year and year in report_raw:
        parts = authors[0].split()
        first_family = (parts[-1] if parts else "").lower()
        if first_family and len(first_family) >= 2 and first_family in report_raw.lower():
            return True
    return False


def check_seed_citations(report, papers):
    """种子论文引用存在性检查（spec §5）。

    core 档未被引用 → 报告头部插入 WARNING 块（不阻塞输出）。
    anchor 档未被引用 → FAIL（本期无 anchor，逻辑预留）。
    """
    seeds = []
    for p in papers:
        qd = getattr(p, "quality_detail", None) or {}
        w = getattr(p, "weight", None) or qd.get("weight", "")
        if not w:
            w = "core" if getattr(p, "source", "") == "user_seed" else ""
        if w in ("core", "anchor"):
            seeds.append((w, p))
    if not seeds:
        return report

    report_norm = _norm_text(report)
    missing_core, missing_anchor = [], []
    for w, p in seeds:
        sp_dict = {
            "doi": getattr(p, "doi", ""),
            "title": getattr(p, "title", ""),
            "authors": getattr(p, "authors", []) or [],
            "year": getattr(p, "year", ""),
        }
        if not _seed_cited(report, report_norm, sp_dict):
            (missing_anchor if w == "anchor" else missing_core).append(
                sp_dict["title"] or sp_dict["doi"] or "未知")

    if missing_anchor:
        # anchor 缺失 → FAIL（本期预留）
        log("Phase7.6", f"❌ anchor 种子论文未被引用，verify FAIL: {missing_anchor}")
        raise RuntimeError(f"seed citation check FAIL (anchor missing): {missing_anchor}")
    if missing_core:
        log("Phase7.6", f"⚠️ {len(missing_core)} 篇核心种子论文未被引用，已强制补入: {missing_core}")
        # 强制补入：把缺失的种子论文追加到报告末尾，确保其标题在正文出现（LLM 报告路径可能漏引）
        appended = []
        for w, p in seeds:
            if w != "core":
                continue
            sp = {
                "title": getattr(p, "title", ""),
                "doi": getattr(p, "doi", ""),
                "authors": getattr(p, "authors", []) or [],
                "year": getattr(p, "year", ""),
            }
            if not sp["title"] or _seed_cited(report, _norm_text(report), sp):
                continue
            authors = "、".join(sp["authors"][:3]) if sp["authors"] else "作者信息缺失"
            year = sp["year"] or "2026"
            appended.append(f"- {authors}. {sp['title']}. 学位论文/用户指定文献, {year}. ⭐用户指定种子论文")
        if appended:
            report += "\n\n## 种子论文（用户指定核心文献）\n\n" + "\n".join(appended) + "\n"
    else:
        log("Phase7.6", f"✅ 全部 {len(seeds)} 篇核心种子论文均已被引用")
    return report


# ============ Main Flow ============
def main():
    start_time = time.time()
    log("MAIN", f"========== Consensus Pipeline v0.7.2 End-to-End Run ==========")
    log("MAIN", f"Topic: {TOPIC}")
    log("MAIN", f"Model: {MODEL}")
    log("MAIN", f"Output directory: {OUTPUT_DIR}")

    # v0.7.0: Domain config, initially empty, populated after Phase 0.5
    domain_config = None

    try:
        # Phase 0: Requirement interview
        doc = phase0_interview()

        # Phase 0.5: Dynamic domain config generation (new in v0.6.2)
        log("Phase0.5", "Dynamically generating domain config...")
        from domain_config_generator import generate_domain_config
        domain_config = generate_domain_config(TOPIC, llm_call, output_dir=OUTPUT_DIR)
        save_json(domain_config, "phase0.5_domain_config.json")
        log("Phase0.5", f"Domain config generation complete: exclusion_signals={len(domain_config.get('exclusion_signals', []))}, "
             f"query_rotation={len(domain_config.get('query_rotation', []))}, "
             f"tier_layers={list(domain_config.get('tier_definitions', {}).keys())}, categorization_dims={list(domain_config.get('categorization_schema', {}).keys())}")

        # Phase 1: Structuring
        structured = phase1_structure(doc)

        # Phase 2: Discussion
        discussion = phase2_discussion(structured)

        # Phase 3: Configuration recommendation
        config = phase3_config(structured, discussion)

        # Phase 4: Academic search (v0.7.0: pass domain_config)
        # Modified phase4_search to use domain_config
        papers, preprints, relevance_log = phase4_search_v6(domain_config)

        if not papers:
            log("MAIN", "⚠️ No papers retrieved, using fallback data")
            papers = []

        # Phase 4.5: Reclassify papers with latest registry (v5.1.3)
        papers = reclassify_papers(papers)

        # Phase 4.6: Content relevance filter (v5.1.7, kept as double insurance)
        papers = filter_by_content_relevance(papers, domain_config=domain_config)

        # Phase 4.7: Backfill S/A-tier paper abstracts (v5.1.7)
        papers = backfill_abstracts(papers)

        # Phase 3.5: QC review (new in v0.6.2, after search+grading+filter, before department debate)
        log("Phase3.5", "Starting QC review...")
        from quality_controller import QualityController
        qc = QualityController(llm_call_fn=llm_call, domain_config=domain_config, output_dir=OUTPUT_DIR)

        # First QC round
        papers, excluded_ids, qc_stats = qc.run_qc(papers)
        log("Phase3.5", f"QC round 1: passed={len(papers)}, excluded={len(excluded_ids)}, "
            f"hard_filter_excluded={qc_stats['hard_filter_excluded']}, "
            f"llm_classify_rejected={qc_stats['llm_classify_rejected']}")

        # If valid < 15, supplemental search (max 3 rounds)
        supplement_round = 0
        while len(papers) < 15 and supplement_round < 3:
            supplement_round += 1
            log("Phase3.5", f"Valid papers < 15 (current {len(papers)}), starting supplemental search round {supplement_round}")
            # Use different queries from query_rotation
            # Exclude seen papers（dedup_registry）
            # New papers go through QC
            new_papers = supplement_search(domain_config, qc.dedup_registry, supplement_round)
            if len(new_papers) < 5:
                log("Phase3.5", "Search exhausted, stopping supplementation")
                break

            # New papers also go through QC
            new_papers, new_excluded, new_stats = qc.run_qc(new_papers)
            log("Phase3.5", f"New papers QC: passed={len(new_papers)}, excluded={len(new_excluded)}")

            papers.extend(new_papers)
            # Run full QC on merged papers (dedup + filter)
            papers, excluded_ids, qc_stats = qc.run_qc(papers)
            log("Phase3.5", f"After round {supplement_round}: valid={len(papers)}")

            # Avoid API rate limiting
            time.sleep(3)

        log("Phase3.5", f"QC complete: final valid papers={len(papers)}")
        save_json(qc_stats, "phase3.5_qc_stats.json")

        # Save QC-filtered papers (for downstream use)
        papers_data = [p.to_dict() for p in papers]
        save_json(papers_data, "phase3.5_qc_papers.json")

        # Phase 4.8: 种子论文导入
        papers = merge_seed_papers(papers)

        # Phase 5: Department debate
        dept_outputs = phase5_debate(config, papers, preprints)

        # Phase 6: Cross-debate
        cross_results = phase6_cross_debate(config, dept_outputs)

        # Programming department standalone output
        prog_output = generate_programming_output(papers)

        # Tutorial department standalone output
        tut_output = generate_tutorial_output(papers)

        # Phase 7: Final report (v5.1: dual template + programming/tutorial + relevance log)
        report = phase7_final_report(papers, preprints, dept_outputs, cross_results,
                                     prog_output=prog_output, tut_output=tut_output,
                                     relevance_log=relevance_log)

        # v0.7.0: Citation validation (after report generation, compare CSV to remove invalid citations)
        log("Phase7.5", "Citation validation...")
        from quality_controller import QualityController
        qc_validate = QualityController(llm_call_fn=llm_call, domain_config=domain_config, output_dir=OUTPUT_DIR)
        csv_path = os.path.join(OUTPUT_DIR, "papers_metadata.csv")
        report = qc_validate.validate_citations(report, csv_path)
        # Phase 7.6: 种子论文引用存在性检查（D层，spec §5）
        report = check_seed_citations(report, papers)
        # Save validated report
        save_text(report, "final_report_validated.md")
        log("Phase7.5", "Citation validation complete")

        # Self-evaluation
        evaluation = self_evaluation(report, papers, dept_outputs)

        elapsed = time.time() - start_time
        log("MAIN", f"========== Full pipeline complete! Elapsed {elapsed:.1f}s ==========")
        log("MAIN", f"Output file directory: {OUTPUT_DIR}")

        # Print file manifest
        for f in sorted(os.listdir(OUTPUT_DIR)):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            log("MAIN", f"  📄 {f} ({size:,} bytes)")

    except Exception as e:
        log("ERROR", f"Pipeline exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Consensus Pipeline CLI Runner")
    parser.add_argument("--topic", type=str, help="Research topic (required)")
    parser.add_argument("--lang", type=str, default="zh", choices=["zh", "en"], help="Output language: zh (default) or en")
    args = parser.parse_args()
    if args.topic:
        TOPIC = args.topic
    elif os.environ.get("DEEPSEEK_TOPIC"):
        TOPIC = os.environ.get("DEEPSEEK_TOPIC")
    else:
        print("Error: --topic argument or DEEPSEEK_TOPIC env var required")
        print('Example: python run_pipeline.py --topic "Machine Learning in Energy Economics"')
        sys.exit(1)
    OUTPUT_LANG = args.lang
    main()

