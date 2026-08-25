#!/usr/bin/env python3
"""
Consensus Pipeline v2 — Full Pipeline Entry Point
=================================================
v1 管线全流程 + v2 表态量化 + 动态终止判定

Phase 0: 需求调研 (v1)
Phase 0.5: 域配置生成 (v1)
Phase 1: 需求结构化 (v1)
Phase 2: 需求讨论 (v1)
Phase 3: 配置推荐 (v1)
Phase 3.5: QC 质量门控 (v1)
Phase 4: 文献检索 + 补充检索 (v1)
Phase 5: 部门辩论 ← **v2 替换**: StanceTracker + CV 量化 + 影子/真终止
Phase 6: 交叉辩论 (v1)
Phase 7: 综述报告 (v1)

前置条件: 运行 setup_v2_full.py 将 v1 文件拉入当前目录
依赖: stance_quant_v2.py (本目录)

用法:
    python run_pipeline_v2.py --topic "你的研究课题"
    python run_pipeline_v2.py --topic "Your topic" --lang en
    python run_pipeline_v2.py --topic "..." --shadow       # 影子模式(不真停)
    python run_pipeline_v2.py --topic "..." --max-rounds 8 # 最大轮次
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime

# ============ 路径检查 ============
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _script_dir)

# 检查 v1 核心文件是否存在
_v1_required = ["run_pipeline.py", "quality_controller.py",
                "domain_config_generator.py"]
_v1_dirs = ["requirement", "academic", "templates"]

_missing = [f for f in _v1_required if not os.path.exists(os.path.join(_script_dir, f))]
_missing += [d for d in _v1_dirs if not os.path.isdir(os.path.join(_script_dir, d))]

if _missing:
    print(f"[ERROR] 缺少 v1 文件: {_missing}")
    print("请先运行: python setup_v2_full.py")
    sys.exit(1)

# 检查 v2 核心文件
if not os.path.exists(os.path.join(_script_dir, "stance_quant_v2.py")):
    print("[ERROR] 缺少 stance_quant_v2.py")
    sys.exit(1)

# ============ Import v1 管线 ============
import run_pipeline as v1

# ============ Import v2 量化模块 ============
from stance_quant_v2 import StanceTracker, check_termination

# ============ v2 配置 ============
V2_CONFIG = {
    "shadow_mode": True,          # True=只记录不真停; False=达到条件真终止
    "max_rounds": 8,              # 单部门最大辩论轮次
    "min_rounds": 3,              # 最少辩论轮次(不判终止)
    "llm_debate_temp": 0.4,       # 辩论温度
    "llm_consensus_temp": 0.2,    # 共识整合温度
    "fail_rate_threshold": 0.20,  # 解析失败率门
    "verbose": True,              # 详细日志
}


# ============ v2 Phase 5: 部门辩论(量化增强版) ============

# v1 论文过滤映射(直接复用)
DEPT_PAPER_FILTERS = v1.DEPT_PAPER_FILTERS


def _filter_papers_for_dept(dept_key, papers, top_n=40):
    """复用 v1 论文过滤"""
    return v1._filter_papers_for_dept(dept_key, papers, top_n)


def _build_papers_summary(papers, max_abstract=300):
    """复用 v1 论文摘要构建"""
    return v1._build_papers_summary(papers, max_abstract)


def _debate_department_v2(dept_key, dept_name, debaters, papers_summary,
                          rounds_unused, output_dir, topic_directions=None):
    """
    v2 部门辩论: StanceTracker 采集表态 + CV 量化 + 动态终止

    rounds_unused: 保留参数兼容 v1 签名, v2 不使用(轮次由 CV 决定)
    output_dir: 运行输出目录(用于 StanceTracker 日志)
    """
    log = v1.log
    llm_call = v1.llm_call
    lang_instr = v1._lang_instr()
    lang_msg = v1._lang_user_msg

    debater_list = []
    for key, info in debaters.items():
        debater_list.append({
            "key": key,
            "name": info.get("en_name" if v1.OUTPUT_LANG == "en" else "zh_name", key),
            "style": info.get("en_style" if v1.OUTPUT_LANG == "en" else "zh_style", ""),
        })

    # 部门任务 prompt
    dept_prompt_map = {
        "literature_search": "请基于以下论文列表，评估文献检索的覆盖度和质量分布，给出评估性判断（覆盖是否充分、有何缺口、如何改进），而非仅罗列统计数字。",
        "metadata_inspector": "请基于以下论文列表，评估元数据完整性，指出关键缺口及其影响。",
        "citation_network": "请基于以下论文列表，评估引用网络结构，识别核心与缺失节点。",
        "methodology_review": "请基于以下论文列表，从方法论维度进行系统评估，明确优劣判断。",
        "data_validation": "请基于以下论文列表，评估核心结论的交叉验证是否成立。",
        "counter_evidence": "请基于以下论文列表，主动寻找与主流结论矛盾的证据。",
        "topic_clustering": "请基于以下论文列表，评估主题聚类结构，指出分布是否均衡、有何盲区。",
        "visualization": "请基于以下论文列表，评估应如何设计核心图表，并说明取舍理由。",
        "report_integration": "请基于以下论文列表和各部门观点，整合为学术综述，对关键结论给出倾向性判断。",
        "programming": "请基于以下论文列表，评估主流工具链的取舍，并给出架构设计与关键代码骨架。",
        "tutorial": "请基于以下论文列表，编写教程，并对最佳实践给出判断。",
    }
    task_prompt = dept_prompt_map.get(dept_key,
        f"请基于以下论文列表，从{dept_name}角度给出专业分析。")

    # v2: Inject topic-specific research directions (from Phase 1)
    topic_context = v1._build_topic_direction_context(topic_directions)

    # ============ 创建 StanceTracker ============
    tracker = StanceTracker(
        run_id=f"v2_{dept_key}_{datetime.now().strftime('%Y%m%d_%H%M')}",
        topic=v1.TOPIC,
        log_dir=output_dir,
    )

    arguments = []
    max_r = V2_CONFIG["max_rounds"]
    min_r = V2_CONFIG["min_rounds"]

    for round_num in range(1, max_r + 1):
        round_label = f"Round {round_num}/{max_r}"
        if round_num > 1:
            log("Phase5-v2", f"  --- {round_label} ---")

        parse_ok = 0
        parse_total = 0

        for debater in debater_list:
            # 构建上下文(R2+ 含历史论点)
            prev_context = ""
            if round_num > 1 and arguments:
                prev_args = []
                for a in arguments:
                    tag = f"辩手「{a['debater']}」" if a['role'] != debater['key'] else f"你（上一轮）"
                    prev_args.append(f"{tag}: {a['argument'][:800]}")
                prev_context = f"""

【前{round_num-1}轮辩论摘要】
{chr(10).join(prev_args)}

请在上一轮观点基础上，回应其他辩手的质疑或补充新论据。不要重复已有观点。"""

            system_prompt = f"""你是Consensus Pipeline的{dept_name}辩手「{debater['name']}」。
你的专业视角：{debater['style']}

{task_prompt}{topic_context}

【引用忠实性规则】
1. 引用论文[N]时，只能描述该论文标题和摘要中明确出现的信息
2. 严禁编造论文中不存在的具体实验结果
3. 严禁使用[N]占位
4. 所有引用必须从论文列表中选取
5. 每个核心结论标注支撑论文数量

请给出你的专业分析和观点。{lang_instr}{prev_context}"""

            # R2+ 拼入表态块（让辩手输出结构化立场 JSON）
            if round_num > 1 and tracker.arguments:
                stance_block = tracker.get_stance_block()
                if stance_block:
                    system_prompt += "\n\n" + stance_block

            user_msg = f"论文列表：\n{papers_summary[:12000]}"
            if round_num > 1:
                user_msg += f"\n\n（{round_label}——请深化或回应）"

            log("Phase5-v2", f"  {debater['name']} {round_label} speaking...")
            response = llm_call(system_prompt, user_msg,
                              temperature=V2_CONFIG["llm_debate_temp"])

            parse_total += 1
            if response and len(response.strip()) > 50:
                parse_ok += 1

            # 记录参数到 tracker
            tracker.record_debater_stance(
                debater_id=debater['key'],
                raw_output=response,
                prompt_tokens=0,
                completion_tokens=0,
            )

            # 存/追加参数到 arguments 列表(供共识整合用)
            existing = [a for a in arguments if a["role"] == debater["key"]]
            if existing and round_num > 1:
                existing[0]["argument"] += f"\n\n--- {round_label} ---\n{response}"
            else:
                arguments.append({
                    "debater": debater["name"],
                    "role": debater["key"],
                    "argument": response,
                })

        # ============ R1 后: 论点抽取 + 回放表态记录 ============
        if round_num == 1:
            round1_transcript = "\n\n".join(
                f"[{a['debater']}]: {a['argument']}" for a in arguments
            )
            extracted = tracker.extract_arguments(
                round1_transcript,
                lambda prompt: llm_call(prompt, "", temperature=0.2),
            )
            if extracted:
                log("Phase5-v2", f"  抽取 {len(extracted)} 个论点")
                # 持久化
                args_path = os.path.join(output_dir, f"{dept_key}_arguments.json")
                with open(args_path, "w", encoding="utf-8") as f:
                    json.dump(extracted, f, ensure_ascii=False, indent=2)
                # 回放 R1 表态记录(extract_arguments 之前 arg_ids 为空,
                # record_debater_stance 会静默跳过,现在论点已就绪,重新录入)
                for a in arguments:
                    tracker.record_debater_stance(
                        debater_id=a['role'],
                        raw_output=a['argument'],
                        prompt_tokens=0,
                        completion_tokens=0,
                    )
                log("Phase5-v2", f"  回放 {len(arguments)} 条 R1 表态")

        # ============ 本轮完成: 计算 CV + 影子判定 ============
        fail_rate = 1.0 - (parse_ok / parse_total) if parse_total > 0 else 0.0
        summary = tracker.finish_round(round_num, fail_rate=fail_rate)

        log("Phase5-v2",
            f"  R{round_num}: CV={summary.get('overall', 'N/A')}, "
            f"fail_rate={fail_rate:.0%}, "
            f"termination={summary.get('termination', {})}")

        # ============ 终止判定 ============
        if round_num >= min_r:
            termination = summary.get("termination", (False, None))
            should_stop = termination[0] if isinstance(termination, tuple) else False
            reason = termination[1] if isinstance(termination, tuple) else ""

            if should_stop:
                if V2_CONFIG["shadow_mode"]:
                    log("Phase5-v2",
                        f"  [SHADOW] 触发终止: {reason} — 影子模式,继续辩论")
                else:
                    log("Phase5-v2",
                        f"  [STOP] 触发终止: {reason} — 实际终止")
                    break

    # ============ 共识整合 ============
    tracker_summary = tracker.get_summary()

    if len(arguments) > 1:
        consensus_prompt = f"""你是{dept_name}的共识整合专家。以下是该部门各辩手经过多轮辩论后的观点：

{json.dumps([{'name': a['debater'], 'argument': a['argument'][:2000]} for a in arguments], ensure_ascii=False, indent=2)}

v2 量化摘要:
{tracker_summary}

请整合各方观点，输出：
1. **共识结论**：各方一致认同的关键结论
2. **分歧点**：各方存在分歧的地方
3. **最终建议**：综合各方观点的最佳建议

{lang_instr}。"""

        log("Phase5-v2", f"  {dept_name} 共识整合...")
        consensus = llm_call(consensus_prompt,
                           lang_msg("请整合以上观点", "Please integrate the above viewpoints"),
                           temperature=V2_CONFIG["llm_consensus_temp"])
    else:
        consensus = arguments[0]["argument"] if arguments else ""

    return {
        "department": dept_name,
        "department_key": dept_key,
        "debater_arguments": arguments,
        "consensus": consensus,
        "v2_summary": tracker_summary,
    }


def phase5_debate_v2(config, papers, preprints, output_dir):
    """v2 部门辩论: 全部门遍历,每个部门使用 StanceTracker"""
    v1.log("Phase5-v2", "Starting v2 stance-aware department debate")
    v1.log("Phase5-v2", f"  shadow_mode={V2_CONFIG['shadow_mode']}, "
           f"max_rounds={V2_CONFIG['max_rounds']}, "
           f"min_rounds={V2_CONFIG['min_rounds']}")

    departments = config.get("departments", {})
    dept_order = config.get("dept_order", list(departments.keys()))
    topic_directions = config.get("topic_directions", [])

    state = _load_state(output_dir)
    completed = set(state.get("phase5_depts_completed", []))

    dept_outputs = {}

    for dept_key in dept_order:
        if dept_key in completed:
            saved = _load_json_file(output_dir, f"phase5_dept_{dept_key}.json")
            if isinstance(saved, dict):
                dept_outputs[dept_key] = saved
                v1.log("Phase5-v2", f"Resume: 跳过已完成部门 {dept_key}")
                continue

        dept_info = departments.get(dept_key, {})
        dept_name = dept_info.get(
            "en_name" if v1.OUTPUT_LANG == "en" else "zh_name", dept_key)
        debaters = dept_info.get("debaters", {})

        dept_papers = _filter_papers_for_dept(dept_key, papers, top_n=40)
        papers_summary = _build_papers_summary(dept_papers, max_abstract=400)

        v1.log("Phase5-v2",
               f"Department: {dept_name} ({dept_key}), "
               f"debaters: {list(debaters.keys())}, "
               f"papers: {len(dept_papers)}/{len(papers)}")

        output = _debate_department_v2(
            dept_key, dept_name, debaters, papers_summary,
            rounds_unused=0, output_dir=output_dir,
            topic_directions=topic_directions)
        dept_outputs[dept_key] = output
        # 部门输出落盘(原子) + 更新状态
        _atomic_write_json(output_dir, f"phase5_dept_{dept_key}.json", output)
        state["phase5_depts_completed"] = list(dept_outputs.keys())
        state["current_phase"] = "5"
        state["current_dept"] = dept_key
        _save_state(output_dir, state)

    v1.log("Phase5-v2", f"All departments complete: {len(dept_outputs)}")
    return dept_outputs


# ============ 辅助函数: 补充检索/QC/报告(透传 v1) ============

def _load_chat_config():
    """加载聊天需求调研生成的配置（run_output/phase3_recommended_config.json）。"""
    p = os.path.join(_script_dir, "run_output", "phase3_recommended_config.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("departments"):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _run_phases_0_to_4(skip_requirement=False):
    """执行 Phase 0 ~ Phase 4(全部 v1)。skip_requirement=True 时复用聊天生成的
    配置(Phase 0-3)，只重跑域配置(0.5) + 检索(4) + QC(3.5)。"""
    log = v1.log

    # Phase 0.5: 域配置（独立于 Phase 0-3，检索必需）
    log("Phase0.5", "Dynamically generating domain config...")
    from domain_config_generator import generate_domain_config
    domain_config = generate_domain_config(v1.TOPIC, v1.llm_call,
                                           output_dir=v1.OUTPUT_DIR)
    v1.save_json(domain_config, "phase0.5_domain_config.json")

    if skip_requirement:
        # 复用聊天需求调研生成的配置，跳过 Phase 0-3
        config = _load_chat_config()
        if config is None:
            log("ERROR", "--skip-requirement 但找不到 run_output/phase3_recommended_config.json，"
                         "请先运行需求调研(run_requirement_research)，或去掉该参数")
            raise SystemExit(1)
        log("Skip-Requirement", f"复用聊天配置: {len(config.get('departments', {}))} 个部门")
    else:
        # Phase 0
        doc = v1.phase0_interview()

        # Phase 1
        structured = v1.phase1_structure(doc)

        # Phase 2
        discussion = v1.phase2_discussion(structured)

        # Phase 3
        config = v1.phase3_config(structured, discussion)

    # Phase 4
    papers, preprints, relevance_log = v1.phase4_search_v6(domain_config)

    # Phase 4.5-4.7
    papers = v1.reclassify_papers(papers)
    papers = v1.filter_by_content_relevance(papers, domain_config=domain_config)
    papers = v1.backfill_abstracts(papers)

    # Phase 3.5: QC
    log("Phase3.5", "Starting QC review...")
    from quality_controller import QualityController
    qc = QualityController(llm_call_fn=v1.llm_call,
                          domain_config=domain_config,
                          output_dir=v1.OUTPUT_DIR)
    papers, excluded_ids, qc_stats = qc.run_qc(papers)
    log("Phase3.5", f"QC round 1: passed={len(papers)}, excluded={len(excluded_ids)}")

    # 补充检索
    supplement_round = 0
    while len(papers) < 15 and supplement_round < 3:
        supplement_round += 1
        log("Phase3.5", f"Valid < 15 ({len(papers)}), supplement round {supplement_round}")
        new_papers = v1.supplement_search(domain_config, qc.dedup_registry,
                                          supplement_round)
        if len(new_papers) < 5:
            log("Phase3.5", "Search exhausted")
            break
        new_papers, new_excluded, _ = qc.run_qc(new_papers)
        papers.extend(new_papers)
        papers, excluded_ids, qc_stats = qc.run_qc(papers)
        log("Phase3.5", f"After round {supplement_round}: valid={len(papers)}")
        time.sleep(3)

    v1.save_json(qc_stats, "phase3.5_qc_stats.json")
    v1.save_json([p.to_dict() for p in papers], "phase3.5_qc_papers.json")

    return config, papers, preprints, relevance_log


def phase4_9_fulltext_fetch(papers, output_dir, time_budget_s=900):
    """Phase 4.9: 辩论前批量获取全文（本地 fulltext_papers/ + OA 自动爬）。

    零用户参与——只做自动可得的部分；用户手动补录在 Phase 5.5 断点
    （辩论确定「缺失但必要」后）+ Phase 7.7 兜底。返回 fulltext_cache:
    dict[doi, fulltext_text]，并持久化到 phase4.9_fulltext_cache.json。

    time_budget_s: OA 爬取的总时间预算（默认 15 分钟），超时跳过剩余论文
    （本地匹配不受预算限制，因为它是内存查找、几乎瞬时）。
    """
    import time as _time
    from requirement.citation_verifier import ReferenceResolver, set_progress_hook

    log = v1.log
    resolver = ReferenceResolver(search_fn=None)

    def _prog(stage, done, total):
        try:
            with open(os.path.join(output_dir, "phase4.9_fulltext_progress.json"), "w", encoding="utf-8") as _f:
                json.dump({"stage": stage, "done": done, "total": total}, _f, ensure_ascii=False)
        except Exception:
            pass

    set_progress_hook(_prog)
    fulltext_cache = {}
    total = len(papers)
    log("Phase4.9", f"全文获取: 对 {total} 篇论文尝试本地+OA全文 (预算 {time_budget_s}s)")

    _t_start = _time.time()
    for i, p in enumerate(papers, 1):
        doi = (getattr(p, "doi", "") or "").strip()
        if not doi:
            continue
        # 超预算：跳过剩余（本地已匹配的已缓存，未匹配的留给辩论用摘要）
        if _time.time() - _t_start > time_budget_s:
            log("Phase4.9", f"OA 爬取超预算，跳过剩余 {total - i + 1} 篇")
            break
        try:
            ft = resolver.fetch_fulltext(doi)
            if ft and len(ft) >= 500:
                fulltext_cache[doi] = ft[:30000]
        except Exception:
            continue
        if i % 25 == 0 or i == total:
            log("Phase4.9", f"全文获取 {i}/{total}, 已得 {len(fulltext_cache)} 篇")

    log("Phase4.9", f"全文获取完成: {len(fulltext_cache)}/{total} 篇有全文")
    _cache_path = os.path.join(output_dir, "phase4.9_fulltext_cache.json")
    try:
        with open(_cache_path, "w", encoding="utf-8") as _f:
            json.dump(fulltext_cache, _f, ensure_ascii=False)
        log("Phase4.9", f"全文缓存已保存 → {_cache_path}")
    except Exception as _e:
        log("Phase4.9", f"全文缓存保存失败: {_e}")
    set_progress_hook(None)
    return fulltext_cache


def _verify_llm_raises(system_prompt, user_prompt):
    """原子校验的 LLM 调用：单独用更强模型（默认 pro，可用 DEEPSEEK_VERIFY_MODEL 覆盖）。

    NLI 的 entail/contradict 判别需要强模型——flash 会全判 neutral 导致 0% verified。
    生成走 flash（快），校验走 pro（准）。失败时 RAISE（CitationVerifier 依赖此约定）。
    """
    import os
    import requests
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    model = os.environ.get("DEEPSEEK_VERIFY_MODEL", "deepseek-v4-pro")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={"model": model,
                  "messages": [
                      {"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt},
                  ],
                  "temperature": 0.3, "max_tokens": 8192},
            timeout=180,
        )
        resp.raise_for_status()
        result = resp.json()["choices"][0]["message"]["content"]
        if not result:
            raise RuntimeError("empty LLM response")
        return result
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {str(e)[:160]}")


def _atomic_verify_and_fix(report_text, papers=None, max_rounds=2):
    """Phase 7.7: 原子事实校验（引用锚定 NLI）→ 修正 → 再校验 循环。

    把报告的原子事实论断逐条对引用摘要做 NLI，产出 verified/partially/
    contradicted/unverified 计数；对 contradicted/unverified 论断做定向修正后
    重跑，最多 max_rounds 轮。逐条明细写入 citation_verification.json。
    """
    log = v1.log
    try:
        from requirement.citation_verifier import CitationVerifier
    except Exception as e:
        log("Phase7.7", f"CitationVerifier unavailable: {e}")
        return report_text

    # search_fn：AcademicSearchEngine 拉摘要（app.py 原流程的关键，缺失→标题级→0%）
    def _search_fn(query, max_results=5):
        try:
            from academic.search_engine import AcademicSearchEngine
            engine = AcademicSearchEngine(quality_levels=["S", "A", "B"], min_results=max_results)
            result = engine.search(query, max_results_per_source=max(20, max_results * 4))
            ps = result["papers"] + result.get("preprints", [])[:3]
            return [{"title": p.title, "doi": p.doi, "abstract": p.abstract} for p in ps[:max_results]]
        except Exception:
            return []

    # papers_data：管线缓存的论文（title/doi 供匹配，abstract 供 NLI）
    papers_data = []
    for p in (papers or []):
        if hasattr(p, "to_dict"):
            papers_data.append(p.to_dict())
        elif isinstance(p, dict):
            papers_data.append(p)

    verifier = CitationVerifier(
        llm_call_fn=_verify_llm_raises,
        search_fn=_search_fn,
        language=v1.OUTPUT_LANG,
        max_claims=20,
        max_contexts=15,
    )

    current = report_text
    last_cv = None
    for rnd in range(1, max_rounds + 1):
        try:
            cv = verifier.verify(current, papers_data=papers_data if papers_data else None)
        except Exception as e:
            log("Phase7.7", f"round {rnd} verify error: {e}")
            break
        last_cv = cv
        log("Phase7.7", f"round {rnd}: {cv.summary}")

        failed = [c for c in cv.claim_verifications
                  if c.status in ("contradicted", "unverified")]
        if not failed:
            log("Phase7.7", "no contradicted/unverified claims — done")
            break

        # 修正：追加"原子校验与修正建议"说明（长报告无法整体重写；标题级/
        # 全文本缺失的 unverified 也无法靠改写修复，只能标注需人工核实）。
        note = _build_correction_note(cv, v1.OUTPUT_LANG)
        if note and "## 原子校验与修正建议" not in current:
            current = current.rstrip() + "\n\n" + note + "\n"
            log("Phase7.7", f"round {rnd} appended correction note — re-verify next round")
        else:
            log("Phase7.7", f"round {rnd} note already present / no fixable — stop")
            break

    if last_cv is not None:
        v1.save_json(last_cv.to_dict(), "citation_verification.json")
    return current


def _build_correction_note(cv, lang):
    """把未通过校验的原子论断整理成修正建议说明（确定性，不依赖 LLM）。

    v0.13: 区分「引用错位」（摘要与全文均 neutral）与「真缺全文」（仅摘要 neutral，
    全文未抓到）——前者标注需核对引用编号，后者标注需核实全文。
    """
    def _has_fulltext_neutral(c):
        return any(
            getattr(n, "evidence", "") == "fulltext" and getattr(n, "label", "") == "neutral"
            for n in (c.nli_results or [])
        )

    if lang == "zh":
        lines = ["## 原子校验与修正建议", ""]
        lines.append(f"**校验摘要**：{cv.summary}")
        lines.append("")
        lines.append("**未通过校验的论断（需人工核实/修正）**：")
        any_failed = False
        for c in cv.claim_verifications:
            if c.status in ("contradicted", "unverified"):
                any_failed = True
                if c.status == "contradicted":
                    act = "删除或改写"
                elif _has_fulltext_neutral(c):
                    act = "⚠️ 引用可能错位（摘要与全文均不支持，请核对引用编号与论文归属）"
                else:
                    act = "加限定语或核实全文"
                lines.append(f"- [{c.status}] {c.claim.text} → {act}")
        if not any_failed:
            lines.append("- 无")
        return "\n".join(lines)
    else:
        lines = ["## Atomic Verification & Correction Notes", ""]
        lines.append(f"**Verification summary**: {cv.summary}")
        lines.append("")
        lines.append("**Failed claims (need human review/correction)**:")
        any_failed = False
        for c in cv.claim_verifications:
            if c.status in ("contradicted", "unverified"):
                any_failed = True
                if c.status == "contradicted":
                    act = "remove or rewrite"
                elif _has_fulltext_neutral(c):
                    act = "⚠️ possible citation mismatch (abstract AND full text do not support; check citation number/attribution)"
                else:
                    act = "hedge or verify against fulltext"
                lines.append(f"- [{c.status}] {c.claim.text} -> {act}")
        if not any_failed:
            lines.append("- none")
        return "\n".join(lines)


def _run_phases_6_to_7(config, papers, preprints, dept_outputs, relevance_log):
    """执行 Phase 6 ~ Phase 7(全部 v1)"""
    log = v1.log

    # Phase 6: 交叉辩论
    cross_results = v1.phase6_cross_debate(config, dept_outputs)

    # Programming / Tutorial 独立产出
    prog_output = v1.generate_programming_output(papers)
    tut_output = v1.generate_tutorial_output(papers)

    # Phase 7: 综述报告
    report = v1.phase7_final_report(
        papers, preprints, dept_outputs, cross_results,
        prog_output=prog_output, tut_output=tut_output,
        relevance_log=relevance_log)

    # Phase 7.5: 引用验证
    log("Phase7.5", "Citation validation...")
    from quality_controller import QualityController
    qc_val = QualityController(llm_call_fn=v1.llm_call,
                               domain_config=None,
                               output_dir=v1.OUTPUT_DIR)
    csv_path = os.path.join(v1.OUTPUT_DIR, "papers_metadata.csv")
    if os.path.exists(csv_path):
        report = qc_val.validate_citations(report, csv_path)
    # Phase 7.6: 种子论文引用存在性检查（D层，5）
    report = v1.check_seed_citations(report, papers)

    # Phase 7.7: 原子事实校验（引用锚定 NLI）→ 修正 → 再校验
    report = _atomic_verify_and_fix(report, papers)

    v1.save_text(report, "final_report_validated.md")
    log("Phase7.5", "Citation validation + atomic verification complete")

    return report


# ============ 断点续跑辅助 (Model A 地基) ============

STATE_FILENAME = "v2_run_state.json"


def _atomic_write_json(output_dir, filename, data):
    """原子写入: 先写 .tmp 再 os.replace, 避免崩溃留下半截文件。"""
    path = os.path.join(output_dir, filename)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    return path


def _load_json_file(output_dir, filename):
    """读取输出目录下的 JSON 文件; 不存在/损坏返回 None。"""
    path = os.path.join(output_dir, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


def _load_state(output_dir):
    return _load_json_file(output_dir, STATE_FILENAME) or {}


def _save_state(output_dir, state):
    _atomic_write_json(output_dir, STATE_FILENAME, state)


def _reconstruct_papers(items):
    """从 dict 列表重建 PaperCandidate 列表。"""
    import dataclasses
    from academic.search_engine import PaperCandidate
    fields = {f.name for f in dataclasses.fields(PaperCandidate)}
    out = []
    for d in (items or []):
        if isinstance(d, dict):
            out.append(PaperCandidate(**{k: d[k] for k in fields if k in d}))
    return out


def _load_config(output_dir):
    return _load_json_file(output_dir, "phase3_recommended_config.json")


def _load_papers(output_dir):
    data = _load_json_file(output_dir, "phase3.5_qc_papers.json")
    if not isinstance(data, list):
        return None
    return _reconstruct_papers(data)


def _load_preprints(output_dir):
    data = _load_json_file(output_dir, "phase4_search_results.json")
    if not isinstance(data, dict):
        return []
    return _reconstruct_papers(data.get("preprints", []))


def _run_single_dept(dept_key, config, papers, preprints, output_dir):
    """只跑一个部门的辩论(隔离测试用)。"""
    dept_info = config.get("departments", {}).get(dept_key, {})
    if not dept_info:
        v1.log("ERROR", f"部门 {dept_key} 不在 config 的 departments 中")
        return {}
    dept_name = dept_info.get("en_name" if v1.OUTPUT_LANG == "en" else "zh_name", dept_key)
    debaters = dept_info.get("debaters", {})
    dept_papers = _filter_papers_for_dept(dept_key, papers, top_n=40)
    papers_summary = _build_papers_summary(dept_papers, max_abstract=400)
    v1.log("Phase5-v2", f"[单部门] {dept_name} ({dept_key}), debaters={list(debaters.keys())}, papers={len(dept_papers)}/{len(papers)}")
    output = _debate_department_v2(dept_key, dept_name, debaters, papers_summary,
                                   rounds_unused=0, output_dir=output_dir,
                                   topic_directions=config.get("topic_directions", []))
    _atomic_write_json(output_dir, f"phase5_dept_{dept_key}.json", output)
    return {dept_key: output}


# ============ Main ============

def main():
    parser = argparse.ArgumentParser(description="Consensus Pipeline v2 (stance-aware)")
    parser.add_argument("--topic", type=str, required=True, help="研究课题")
    parser.add_argument("--lang", type=str, default="zh", choices=["zh", "en"])
    parser.add_argument("--shadow", action="store_true", default=True,
                       help="影子模式:只记录不真停(默认)")
    parser.add_argument("--real-stop", action="store_true",
                       help="真实终止模式:达到条件实际停止辩论")
    parser.add_argument("--max-rounds", type=int, default=8,
                       help="单部门最大辩论轮次(默认8)")
    parser.add_argument("--min-rounds", type=int, default=3,
                       help="最少辩论轮次(默认3)")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="输出目录(默认自动生成)")
    parser.add_argument("--resume", action="store_true",
                       help="断点续跑: 跳过 Phase 0-4.5+QC, 从磁盘加载中间产物")
    parser.add_argument("--skip-requirement", action="store_true",
                       help="跳过 Phase 0-3 需求调研, 复用 run_output/phase3_recommended_config.json(聊天已生成)")
    parser.add_argument("--only-dept", type=str, default=None,
                       help="只跑指定部门的辩论(如 literature_search), 隔离测试用")
    args = parser.parse_args()

    # v2 配置
    if args.real_stop:
        V2_CONFIG["shadow_mode"] = False
    V2_CONFIG["max_rounds"] = args.max_rounds
    V2_CONFIG["min_rounds"] = args.min_rounds

    # 输出目录
    date_str = datetime.now().strftime("%Y%m%d")
    topic_tag = args.topic[:20].replace(" ", "_").replace("/", "_")
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(_script_dir, "v2_run_output",
                                  f"{date_str}_{topic_tag}")
    os.makedirs(output_dir, exist_ok=True)

    # 配置 v1 模块全局变量
    v1.TOPIC = args.topic
    v1.OUTPUT_LANG = args.lang
    v1.OUTPUT_DIR = output_dir

    start_time = time.time()
    v1.log("MAIN-v2", "=" * 50)
    v1.log("MAIN-v2", "Consensus Pipeline v2 — Stance-Aware Full Run")
    v1.log("MAIN-v2", f"Topic: {args.topic}")
    v1.log("MAIN-v2", f"Lang: {v1.OUTPUT_LANG}")
    v1.log("MAIN-v2", f"Shadow mode: {V2_CONFIG['shadow_mode']}")
    v1.log("MAIN-v2", f"Max rounds: {V2_CONFIG['max_rounds']}")
    v1.log("MAIN-v2", f"Output: {output_dir}")
    v1.log("MAIN-v2", "=" * 50)

    # 保存运行配置
    v1.save_json({
        "topic": args.topic,
        "lang": args.lang,
        "v2_config": V2_CONFIG,
        "start_time": datetime.now().isoformat(),
    }, "v2_run_config.json")

    state = _load_state(output_dir)

    try:
        # Phase 0 ~ 4.5+QC: 支持 --resume 跳过
        config = papers = preprints = relevance_log = None
        if args.resume:
            config = _load_config(output_dir)
            papers = _load_papers(output_dir)
            preprints = _load_preprints(output_dir)
            relevance_log = {"domain_config_driven": True, "resumed": True}
            if config is None or papers is None:
                v1.log("ERROR", "resume 失败: 缺少有效的 phase3_recommended_config.json / phase3.5_qc_papers.json")
                return
            v1.log("MAIN-v2", f"Resume: 跳过 Phase 0-4.5+QC, 加载 config + {len(papers)} papers + {len(preprints)} preprints")
        else:
            v1.log("MAIN-v2", ">>> Phase 0-4: v1 管线(调研/结构化/检索/QC)")
            config, papers, preprints, relevance_log = _run_phases_0_to_4(
                skip_requirement=args.skip_requirement)
            state["phases_completed"] = ["0", "0.5", "1", "2", "3", "3.5", "4"]
            state["current_phase"] = "5"
            _save_state(output_dir, state)

        # Phase 4.8: 种子论文导入
        papers = v1.merge_seed_papers(papers)

        # Phase 4.9: 辩论前全文自动获取（本地 + OA 爬，零用户参与）
        fulltext_cache = phase4_9_fulltext_fetch(papers, output_dir)
        state["fulltext_cache_size"] = len(fulltext_cache)
        _save_state(output_dir, state)

        # Phase 5: v2 辩论(量化增强)
        v1.log("MAIN-v2", ">>> Phase 5: v2 辩论(StanceTracker + 动态终止)")
        if args.only_dept:
            dept_outputs = _run_single_dept(args.only_dept, config, papers, preprints, output_dir)
            v1.log("MAIN-v2", f"[隔离测试] 单部门 {args.only_dept} 完成, 退出(跳过 Phase 6-7)")
            return
        dept_outputs = phase5_debate_v2(config, papers, preprints, output_dir)

        # Phase 6 ~ 7: v1 管线
        v1.log("MAIN-v2", ">>> Phase 6-7: v1 管线(交叉辩论/综述/验证)")
        report = _run_phases_6_to_7(config, papers, preprints,
                                    dept_outputs, relevance_log)

        # 完成
        elapsed = time.time() - start_time
        v1.log("MAIN-v2", f"Pipeline v2 complete! Elapsed {elapsed:.1f}s")

        # 汇总 v2 数据
        v2_summaries = {}
        for dk, do in dept_outputs.items():
            v2_summaries[dk] = do.get("v2_summary", "")
        v1.save_json(v2_summaries, "v2_all_dept_summaries.json")

        # 文件清单
        for f in sorted(os.listdir(output_dir)):
            size = os.path.getsize(os.path.join(output_dir, f))
            v1.log("MAIN-v2", f"  {f} ({size:,} bytes)")

    except Exception as e:
        v1.log("ERROR", f"Pipeline v2 exception: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
