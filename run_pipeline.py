#!/usr/bin/env python3
"""
Consensus Pipeline v4.5 端到端运行脚本
主题：机器学习在能源经济学上的运用调研
"""
import sys
import os
import json
import time
import requests
from datetime import datetime

# 确保模块路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============ 配置 ============
API_URL = "https://api.deepseek.com/v1/chat/completions"
API_KEY = "DEEPSEEK_API_KEY_REMOVED"
MODEL = "deepseek-v4-flash"
TOPIC = "机器学习在能源经济学上的运用"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_output")

# easyScholar API密钥（v5.0：实时期刊分级）
os.environ["EASYSCHOLAR_SECRET_KEY"] = "EASYSCHOLAR_KEY_REMOVED"

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
        "max_tokens": 4096,
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


# ============ Phase 5: 部门辩论（简化版） ============
def phase5_debate(config, papers, preprints):
    """各部门辩论产出"""
    log("Phase5", "开始部门辩论")

    departments = config.get("departments", {})
    dept_order = config.get("dept_order", list(departments.keys()))
    debate_rounds = config.get("debate_rounds", 2)

    # 准备论文摘要供辩论使用
    papers_summary = _build_papers_summary(papers)

    dept_outputs = {}

    for dept_key in dept_order:
        dept_info = departments.get(dept_key, {})
        dept_name = dept_info.get("zh_name", dept_key)
        debaters = dept_info.get("debaters", {})

        log("Phase5", f"部门: {dept_name} ({dept_key}), 辩手: {list(debaters.keys())}")

        # 为每个部门生成辩论产出
        output = _debate_department(dept_key, dept_name, debaters, papers_summary, debate_rounds)
        dept_outputs[dept_key] = output
        save_json(output, f"phase5_dept_{dept_key}.json")

    save_json(dept_outputs, "phase5_all_dept_outputs.json")
    return dept_outputs


def _build_papers_summary(papers):
    """构建论文摘要文本供辩论使用"""
    lines = []
    for i, p in enumerate(papers[:50], 1):  # 扩展到50篇
        authors = ", ".join(p.authors[:3])
        if len(p.authors) > 3:
            authors += " et al."
        abstract_text = p.abstract[:300] if p.abstract else 'N/A'
        lines.append(
            f"[{i}] {p.title}\n"
            f"    作者: {authors} | 期刊: {p.journal} | 年份: {p.year} | "
            f"被引: {p.citation_count} | 等级: {p.quality_level}\n"
            f"    摘要: {abstract_text}"
        )
    return "\n".join(lines)


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
3. 如果你对某论文的具体内容不确定，写"参见[N]"，不要凭空编造描述
4. 你输出的每个[N]引用和对应描述，都将被后续环节自动校验

请给出你的专业分析和观点。要求：
1. 基于论文列表中的具体证据，不要空泛
2. 明确指出关键发现和问题
3. 给出可操作的建议
4. 中文输出，结构化格式"""

        user_msg = f"论文列表：\n{papers_summary[:8000]}"

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
            dept_name = output.get("dept_name", dept_key)
            # 提取该部门所有辩手发言
            parts = []
            for role, content in output.items():
                if role not in ("dept_name", "consensus") and isinstance(content, str):
                    parts.append(f"**{role}**: {content}")
            debate_outputs[dept_name] = "\n\n".join(parts) if parts else output.get("consensus", "")

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
    log("MAIN", f"========== 共识管线 v4.5 端到端运行 ==========")
    log("MAIN", f"主题: {TOPIC}")
    log("MAIN", f"模型: {MODEL}")
    log("MAIN", f"输出目录: {OUTPUT_DIR}")

    try:
        # Phase 0: 需求调研
        doc = phase0_interview()

        # Phase 1: 结构化
        structured = phase1_structure(doc)

        # Phase 2: 讨论
        discussion = phase2_discussion(structured)

        # Phase 3: 配置推荐
        config = phase3_config(structured, discussion)

        # Phase 4: 学术检索
        papers, preprints, relevance_log = phase4_search()

        if not papers:
            log("MAIN", "⚠️ 未检索到论文，使用回退数据")
            papers = []

        # Phase 4.5: 用最新注册表重新分级论文（v5.1.3）
        papers = reclassify_papers(papers)

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
