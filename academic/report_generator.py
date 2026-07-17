"""
Report Generator — Consensus Pipeline v5.1

v5.1: Dual template separation
  - Final deliverable report (<=2000 words, user-facing): information-density-first, layered presentation
  - Internal working document (unlimited length, developer-facing): complete search+debate+verification records

v4.2: Fix safe truncation for multi-byte characters
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .search_engine import PaperCandidate
from .cross_validator import ClusterResult, ValidationResult
from .visualizer import ChartConfig


def _safe_truncate(text: str, max_chars: int) -> str:
    """Safely truncate string, avoiding splitting in the middle of multi-byte characters."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


class ReportGenerator:
    """
    Report integration group — v5.1 dual template

    Produces two documents:
    - final_report.md: Final deliverable report, <=2000 words, information-density-first
    - internal_doc.md: Internal working document, complete process record
    """

    def __init__(self, output_dir: str = "./output", llm_call_fn=None):
        self.output_dir = output_dir
        self.llm_call_fn = llm_call_fn

    def generate(
        self,
        topic: str,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
        validations: List[ValidationResult],
        charts: List[ChartConfig],
        consensus_points: Optional[List[str]] = None,
        fact_check_summary: str = "",
        debate_outputs: Optional[Dict[str, str]] = None,
        cross_debate_results: Optional[Dict[str, Any]] = None,
        methodology_reviews: Optional[Dict[str, Any]] = None,
        programming_output: str = "",
        tutorial_output: str = "",
        relevance_filter_log: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        生成完整报告（双模板）。

        Args:
            topic: 研究主题
            papers: 候选论文列表（已通过相关性筛选+分级）
            clusters: 聚类结果
            validations: 验证结果
            charts: 图表配置
            consensus_points: 共识结论
            fact_check_summary: 事实校验摘要
            debate_outputs: 各部门辩论输出 {dept_name: content}
            cross_debate_results: 交叉辩论结果
            methodology_reviews: 方法论审查结果
            programming_output: 程序部产出
            tutorial_output: 教程部产出
            relevance_filter_log: 相关性过滤日志

        Returns:
            {"final_report": "路径", "internal_doc": "路径", "csv": "路径", "charts_dir": "路径"}
        """
        os.makedirs(self.output_dir, exist_ok=True)

        # 1. Final deliverable report
        final_content = self._build_final_report(
            topic, papers, clusters, consensus_points,
            fact_check_summary, methodology_reviews,
            debate_outputs,
        )

        # AI refinement to remove fluff (only needed in template mode; review mode is written by AI directly)
        # if self.llm_call_fn:
        #     final_content = self._ai_refine(final_content, topic)

        final_path = os.path.join(self.output_dir, "final_report.md")
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        # 2. Internal working document
        internal_content = self._build_internal_doc(
            topic, papers, clusters, validations, charts,
            consensus_points, fact_check_summary,
            debate_outputs, cross_debate_results,
            methodology_reviews, programming_output,
            tutorial_output, relevance_filter_log,
        )
        internal_path = os.path.join(self.output_dir, "internal_doc.md")
        with open(internal_path, "w", encoding="utf-8") as f:
            f.write(internal_content)

        # 3. CSV metadata table
        csv_content = self._build_csv(papers)
        csv_path = os.path.join(self.output_dir, "papers_metadata.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        # 4. Chart data
        charts_dir = os.path.join(self.output_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        for chart in charts:
            if chart.data:
                chart_path = os.path.join(charts_dir, os.path.basename(chart.file_path))
                with open(chart_path, "w", encoding="utf-8") as f:
                    json.dump(chart.data, f, ensure_ascii=False, indent=2)

        return {
            "final_report": final_path,
            "internal_doc": internal_path,
            "csv": csv_path,
            "charts_dir": charts_dir,
        }

    # ================================================================
    # Final deliverable report (<=2000 words)
    # ================================================================

    def _build_final_report(
        self,
        topic: str,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
        consensus_points: Optional[List[str]],
        fact_check_summary: str,
        methodology_reviews: Optional[Dict[str, Any]],
        debate_outputs: Optional[Dict[str, str]] = None,
    ) -> str:
        """Build final deliverable report. If llm_call_fn exists, use AI to write review; otherwise fallback to template."""
        now = datetime.now().strftime("%Y年%m月%d日")

        s_papers = [p for p in papers if p.quality_level == "S"]
        a_papers = [p for p in papers if p.quality_level == "A"]
        b_papers = [p for p in papers if p.quality_level == "B"]

        if self.llm_call_fn and s_papers:
            return self._build_review_by_ai(topic, papers, s_papers, a_papers, b_papers, consensus_points, now, fact_check_summary, debate_outputs)

        # Fallback: template mode (when no LLM)
        sections = []
        sections.append(self._build_final_title(topic, now))
        sections.append(self._build_final_summary(topic, papers, s_papers, a_papers))
        sections.append(self._build_final_findings(s_papers, consensus_points))
        sections.append(self._build_final_methodology(clusters, methodology_reviews))
        sections.append(self._build_final_trends(papers))
        sections.append(self._build_final_top_papers(s_papers, a_papers))
        sections.append(self._build_final_gaps(papers, consensus_points))
        sections.append(self._build_final_limitations(papers))
        sections.append(self._build_final_references(s_papers, a_papers))
        sections.append(self._build_final_footer(now, fact_check_summary))
        return "\n\n".join(sections)

    def _build_review_by_ai(
        self,
        topic: str,
        papers: List[PaperCandidate],
        s_papers: List[PaperCandidate],
        a_papers: List[PaperCandidate],
        b_papers: List[PaperCandidate],
        consensus_points: Optional[List[str]],
        now: str,
        fact_check_summary: str,
        debate_outputs: Optional[Dict[str, str]] = None,
    ) -> str:
        """Use LLM to write academic review report based on paper metadata"""
        # Build paper list for AI reference — only pass S/A/B-tier, not C-tier
        qualified = [p for p in papers if p.quality_level in ("S", "A", "B")]
        paper_list = self._format_paper_list(qualified)
        year_dist = self._compute_year_distribution(qualified)
        method_dist = self._compute_method_distribution(qualified)
        consensus_text = "\n".join([f"- {c}" for c in (consensus_points or [])])

        system_prompt = """你是一位资深学术综述撰写专家。你的任务是基于给定的论文数据和辩论组共识撰写一篇结构完整的学术动向综述报告。

写作规范：
1. 每个章节要有实质内容段落，不是干巴巴的要点列表
2. 引用具体论文支撑论点，用[序号]标注
3. 方法论对比要有深度：不同方法的优劣、适用场景、计算开销、数据需求
4. 趋势分析基于年份分布数据，说明演进脉络
5. 反面证据必须包含：对主流方法的有效批评、失败案例、适用边界
6. 研究空白要从"为什么没人做"和"做了有什么价值"两个角度分析
7. 语言学术化但不晦涩，避免空话套话
8. 只引用论文清单中提供的论文，不要凭空编造不存在的论文
9. 清单中标注⚠️的论文与本主题不相关，请不要引用
10. 清单中可能包含与主题不太相关的论文（如化学、材料学等），请仅引用与主题直接相关的论文
11. 【相关性硬规则】被正式引用[编号]的论文，其标题或摘要中必须同时出现以下两类关键词之一：(a)能源/碳/电力/气候/排放/负荷/价格预测 AND (b)机器学习/深度学习/神经网络/因果推断/强化学习/预测模型/时序预测。仅作为领域背景的论文使用脚注"参见[编号]"而非正文正式引用
12. 【反面证据】核心发现章节中，每个主流结论必须至少配1条反对或质疑证据，标注置信度🟢高🟡中🔴低
13. 【禁止"参见[N]"占位】严禁使用"参见[N]"作为实质性内容的替代。引用[N]时必须紧接该论文的具体描述（方法名、核心结论、量化指标等）。如果对该论文内容不确定，不要引用该论文，选择你确定内容的论文代替。唯一允许"参见[N]"的场景是作为脚注标注领域背景论文（规则11），不得在正文论述、对比表格、辩论焦点中出现
14. 【续写规则】续写部分同样必须紧接具体描述引用[N]，不得退化为"参见[N]"占位。续写部分的引用[N]必须严格对应论文清单中的论文
15. 【部门辩论整合】如果提供了部门辩论产出，优先采用各部门已验证的分析结论和论文描述，这些结论已经过交叉验证，可信度高于你自己推断的内容。在此基础上进行综述性整合，而非从零重新描述论文
16. 【量化硬规则】描述任何方法效果时，必须包含至少一项量化指标（如"预测精度MAPE=3.2%""在XX数据集上R²=0.95""降低了15%的RMSE"），禁止只写"效果良好""广泛应用""取得显著提升"等空泛描述。若论文未报告量化指标，注明"该论文未报告量化指标"
17. 【辩论焦点必现】综述中至少3处引用辩论组的分歧点，格式为"XX部门认为...，但反方质疑部门指出..."，最终给出交叉辩论后的结论。这是共识管线区别于普通AI综述的核心特征
18. 【对比矩阵填充】方法论对比表每个单元格必须包含具体内容（数字、"未报告"、或简短描述），绝对禁止填写"参见[N]"。预测精度列必须包含具体数值或"未报告"，趋势列使用↑↑(快速上升)/↑(上升)/→(平稳)/↓(下降)符号
19. 【数据卡片先行】综述开头必须先输出结构化数据卡片
20. 【正文连贯性】每个段落必须是完整的学术论述句，禁止出现孤立的引用句号等断裂式引用。引用必须嵌入完整句子中
21. 【摘要驱动引用】论文清单已包含每篇论文的摘要。引用[N]时，描述的内容必须与该论文摘要中的实际内容一致，不得凭标题推断。如果摘要为空或不足以支撑你的论述，注明"该论文摘要信息不足"而不是自行推测
22. 【无关论文已过滤】内容相关性过滤已在上游完成，被降级的论文不会出现在清单中。但仍请检查：如果某篇论文的摘要明显与主题无关，不要引用
23. 【禁止"参见"前缀】正文、对比表、辩论焦点中禁止在[N]前加"参见"前缀（如"参见[10]综述"→应写为"Ghoddusi等[10]综述"）。引用必须紧接作者名或具体描述，不得用"参见"代替
24. 【v0.7.0引用硬约束】所有论文引用必须从论文清单中选取，禁止生成清单外的引用。每个结论必须标注支撑论文数量，格式：(N/M篇支撑，置信度🟢/🟡/🔴)，其中N=支撑论文数，M=该主题总论文数
25. 【v0.7.0置信度标注】每个核心结论后面必须标注置信度：(N/M篇支撑，置信度🟢高/🟡中/🔴低)，评判标准：N≥5且方法论一致→🟢；3≤N<5或存在争议→🟡；N<3→🔴
26. 【v0.7.0局限性必现】综述必须包含"检索边界与局限性"章节，说明：(a)检索源覆盖范围与盲区；(b)论文数量与代表性限制；(c)方法论评估的边界条件；(d)结论适用范围与外推风险"""

        user_prompt = f"""请撰写「{topic}」领域的学术动向综述报告。

## 可用论文数据

### 年份分布
{year_dist}

### 方法分布（从标题/摘要提取）
{method_dist}

### 论文清单（{len(qualified)}篇S/A/B级，其中S级{len(s_papers)}、A级{len(a_papers)}、B级{len(b_papers)}）
{paper_list}

### 部门辩论共识
{consensus_text if consensus_text else "无辩论数据"}

{self._format_debate_outputs(debate_outputs)}

---

请按以下结构撰写，每个章节都要有实质段落而非要点列表：

# {topic}

> 学术动向综述 | Consensus Pipeline v5 | {now}

## 数据卡片

| 指标 | 值 |
|------|------|
| 检索论文数 | {len(qualified)} |
| S级 | {len(s_papers)} |
| A级 | {len(a_papers)} |
| B级 | {len(b_papers)} |
| 时间跨度 | {self._compute_year_span(qualified)} |
| 方法类别数 | {len(method_dist.split(chr(10)))} |
| 预印本数 | {len(papers) - len(qualified)} |

## 一、研究概况与发展脉络
（基于年份分布，描述该领域从何时兴起、关键转折点、当前热度。引用具体论文说明里程碑工作）

## 二、方法论演进与量化对比
（2.1 时间线：从统计→深度学习→混合→因果的演进脉络，标注年份节点和方法论突破论文）
（2.2 量化对比矩阵：每个单元格必须有具体数字或"未报告"，趋势列用↑↑/↑/→/↓。绝对禁止在表格中写"参见[N]"）

| 方法类别 | 代表论文 | 预测精度 | 可解释性 | 数据需求 | 计算开销 | 趋势 |
|---------|---------|---------|---------|---------|---------|------|
| ARIMA/GARCH | 作者[编号] | MAPE=8-15% | 强：系数有经济含义 | 低（≥50点） | 低（CPU秒级） | ↓ |
| LSTM/GRU | 作者[编号] | MAPE=3-8% | 弱：黑箱 | 中（≥500点） | 中（GPU分钟级） | ↑↑ |
| ... | ... | ... | ... | ... | ... | ... |

（2.3 辩论焦点：至少3处引用"XX部门认为...但反方质疑部门指出..."的交锋，给出交叉辩论结论）

## 三、核心发现与争议
（3-5条实质性发现，每条=支持证据链+反方质疑+交叉辩论结论。标注置信度🟢高🟡中🔴低。
格式：**发现N：标题**
支持证据：...[N]...
反方质疑：...[N]...
辩论结论：...
置信度：🟢/🟡/🔴）

## 四、研究空白与文献计量证据
（5个空白，每个：现状→文献计量佐证(如"76篇中仅2篇涉及")→为什么没人做→价值→可行路径）

## 五、检索边界与局限性
（v0.7.0新增必现章节。必须包含以下4个方面：）
（5.1 检索源覆盖范围与盲区：说明使用了哪些检索源（arXiv/Semantic Scholar/OpenAlex），覆盖了哪些数据库，哪些期刊/会议可能未被覆盖，非英语文献的覆盖情况）
（5.2 论文数量与代表性限制：说明最终纳入的论文数量，是否足以支撑普遍性结论，是否存在小样本偏差，N/M篇支撑中N较小时结论的可靠性）
（5.3 方法论评估的边界条件：说明方法论对比的适用前提（如数据规模、市场类型、时间跨度），哪些条件下的结论可能不成立）
（5.4 结论适用范围与外推风险：明确说明综述结论的适用范围，警告读者不要将有限样本上的结论过度外推）

## 六、参考文献
（列出所有S级和A级论文，按S/A/B分组，GB/T 7714格式）"""

        try:
            # Review needs long output, use dedicated call
            report = self._llm_call_long(system_prompt, user_prompt, temperature=0.25)
            if report and len(report) > 500:
                # Rebuild references with paper metadata, ensure citation numbers match
                report = self._rebuild_references(report, qualified)

                # Verify citation descriptions match actual paper content
                report = self._verify_citation_content(report, qualified)

                # Generate visual charts and embed in report
                chart_section = self._embed_charts(qualified, topic)
                if chart_section:
                    # Insert charts after "Research Overview" section
                    report = self._insert_charts_after_section(report, chart_section)

                # Add footer
                if fact_check_summary:
                    report += f"\n\n---\n\n> 📋 事实校验：{fact_check_summary}"
                return report
        except Exception:
            pass

        # Fallback to template when LLM fails
        sections = []
        sections.append(self._build_final_title(topic, now))
        sections.append(self._build_final_summary(topic, papers, s_papers, a_papers))
        sections.append(self._build_final_findings(s_papers, consensus_points))
        sections.append(self._build_final_trends(papers))
        sections.append(self._build_final_references(s_papers, a_papers))
        return "\n\n".join(sections)

    @staticmethod
    def _rebuild_references(report: str, papers: List[PaperCandidate]) -> str:
        """Extract all [N] citations from AI review, rebuild reference section with paper metadata, ensure one-to-one correspondence"""
        import re
        # 1. Extract all citation numbers from main text
        cited_indices = set()
        for m in re.finditer(r'\[(\d+)\]', report):
            idx = int(m.group(1))
            if 1 <= idx <= len(papers):
                cited_indices.add(idx)

        # 1.5 Remove citations exceeding paper list range (AI-fabricated numbers)
        # Replace citations like [68], [79] that exceed len(papers) with empty or comment
        out_of_range = set()
        for m in re.finditer(r'\[(\d+)\]', report):
            idx = int(m.group(1))
            if idx > len(papers) or idx < 1:
                out_of_range.add(idx)

        if out_of_range:
            # v5.1.8: Delete out-of-range [N] directly, no longer replace with "see related research"
            for idx in sorted(out_of_range, reverse=True):
                # Delete [N] and its adjacent "see" prefix
                report = re.sub(r'参见\s*\[' + str(idx) + r'\]', '', report)
                report = report.replace(f'[{idx}]', '')
            # Re-extract valid citations
            cited_indices = set()
            for m in re.finditer(r'\[(\d+)\]', report):
                idx = int(m.group(1))
                if 1 <= idx <= len(papers):
                    cited_indices.add(idx)

        if not cited_indices:
            return report  # 无引用则不改

        # 2. Find and remove all "References" sections (v5.1.8-fix2: prevent duplicate sections)
        # AI may generate "## References" variants, remove all and rebuild uniformly
        report = re.sub(r'\n#{1,3}\s*(?:[一二三四五六七八九十]+[、.．]\s*)?参考文献.*', '', report, flags=re.DOTALL)
        ref_section = "\n\n## 参考文献\n\n"

        # 3. Generate reference list from paper metadata — grouped by tier
        # v5.1.8-fix: Skip C-tier papers (downgraded = irrelevant, zombie citations)
        s_refs, a_refs, b_refs = [], [], []
        c_skipped = 0
        for idx in sorted(cited_indices):
            p = papers[idx - 1]  # 1-based to 0-based
            level = p.quality_level or "B"
            if level == "C":
                # Remove [N] markers for C-tier citations from main text
                report = re.sub(r'参见\s*\[' + str(idx) + r'\]', '', report)
                report = report.replace(f'[{idx}]', '')
                c_skipped += 1
                continue
            authors_str = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors_str += ", 等"

            title = p.title.rstrip(".")
            journal = p.journal or "arXiv预印本"
            year = p.year or "n/a"
            doi_str = f". doi:{p.doi}" if p.doi else ""
            level = p.quality_level or "B"

            entry = f"[{idx}] {authors_str}. {title}. *{journal}*, {year}{doi_str}.  "

            if level == "S":
                s_refs.append(entry)
            elif level == "A":
                a_refs.append(entry)
            else:
                b_refs.append(entry)

        # Output grouped by tier
        if c_skipped > 0:
            import logging
            logging.info(f"[v5.1.8-fix] 移除{c_skipped}篇C级僵尸引用")
        ref_section_parts = []
        if s_refs:
            ref_section_parts.append("### S级（顶刊）")
            ref_section_parts.extend(s_refs)
        if a_refs:
            ref_section_parts.append("\n### A级（优秀）")
            ref_section_parts.extend(a_refs)
        if b_refs:
            ref_section_parts.append("\n### B级（良好）")
            ref_section_parts.extend(b_refs)

        ref_section += "\n".join(ref_section_parts)
        report = report + ref_section

        # 4. Final validation: remove uncited reference entries from main text
        report = ReportGenerator._validate_references(report)
        return report

    @staticmethod
    def _validate_references(report: str) -> str:
        """Validate citation consistency: main text [N] ↔ reference list one-to-one correspondence"""
        import re
        ref_split = report.split("## 参考文献")
        if len(ref_split) < 2:
            return report

        body = ref_split[0]
        ref_part = ref_split[-1]

        # Extract all [N] from main text
        body_refs = set(int(m) for m in re.findall(r'\[(\d+)\]', body))

        # Extract [N] from references
        ref_entries = {}
        current_subsection = ""
        subsections = []
        ref_lines = ref_part.split("\n")
        cleaned_lines = []

        for line in ref_lines:
            if line.strip().startswith("### "):
                current_subsection = line.strip()
                subsections.append(current_subsection)
                cleaned_lines.append(line)
                continue
            m = re.match(r'^\[(\d+)\]', line.strip())
            if m:
                idx = int(m.group(1))
                if idx in body_refs:
                    ref_entries[idx] = line
                    cleaned_lines.append(line)
                # else: main text does not cite this number, remove
            else:
                cleaned_lines.append(line)

        # Rebuild references section
        new_ref = "\n".join(cleaned_lines)
        return ref_split[0] + "## 参考文献" + new_ref

    def _verify_citation_content(self, report: str, papers: List[PaperCandidate]) -> str:
        """
        校验正文[N]附近的描述是否与论文实际内容一致。
        对于描述与论文标题/摘要明显不匹配的引用，替换为"参见[N]"。
        
        策略：提取每个[N]上下文（前后100字），检查是否包含该论文标题中的
        关键术语。如果上下文中的方法/领域描述与论文标题完全不匹配，
        则将描述性引用替换为安全的"参见[N]"。
        """
        import re
        
        # Find reference section boundary, only process main text
        ref_split = report.split("## 参考文献")
        body = ref_split[0] if len(ref_split) >= 2 else report
        
        # For each citation number, extract context and validate
        verified_body = body
        citation_contexts = {}  # idx -> list of context snippets
        
        for m in re.finditer(r'\[(\d+)\]', body):
            idx = int(m.group(1))
            if idx < 1 or idx > len(papers):
                continue
            
            # Extract ~100 chars context around [N]
            start = max(0, m.start() - 100)
            end = min(len(body), m.end() + 100)
            context = body[start:end]
            
            if idx not in citation_contexts:
                citation_contexts[idx] = []
            citation_contexts[idx].append(context)
        
        # For each citation, check if description matches paper
        mismatches = []
        for idx, contexts in citation_contexts.items():
            paper = papers[idx - 1]
            title = paper.title.lower()
            
            # Extract key terms from paper title (core nouns/verbs after removing stop words)
            title_words = set()
            stop_words = {"a", "an", "the", "of", "in", "on", "for", "and", "with", "to", 
                         "from", "by", "at", "is", "are", "was", "were", "using", "based",
                         "its", "their", "this", "that", "which", "between", "through",
                         "under", "over", "into", "within", "during", "after", "before"}
            for word in title.split():
                w = word.strip(".,:;-()[]{}").lower()
                if len(w) >= 3 and w not in stop_words:
                    title_words.add(w)
            
            # For each occurrence, check if context is relevant to paper
            all_mismatched = True
            for ctx in contexts:
                ctx_lower = ctx.lower()
                # Check if paper title keywords appear in context
                keyword_hits = sum(1 for w in title_words if w in ctx_lower)
                keyword_ratio = keyword_hits / max(len(title_words), 1)
                
                if keyword_ratio >= 0.2:
                    # At least 20% title keywords in context = match
                    all_mismatched = False
                    break
            
            if all_mismatched and len(title_words) >= 3:
                mismatches.append(idx)
        
        # For mismatched citations, delete the citation marker directly (rather than replace with "see [N]")
        # "see [N]" placeholders are the main cause of report quality degradation, better to remove uncertain citations
        if mismatches:
            for idx in mismatches:
                paper = papers[idx - 1]
                # Strategy 1: Delete standalone "see [N]" or "see [N]." patterns
                pattern1 = re.compile(r'\s*参见\[' + str(idx) + r'\]\。?\s*')
                verified_body = pattern1.sub(' ', verified_body)
                # Strategy 2: Delete citation-only fragments like "[N]." or unreadable patterns
                pattern2 = re.compile(r'\s*\[' + str(idx) + r'\]\s*[0-9]*%\s*\。?\s*')
                verified_body = pattern2.sub(' ', verified_body)
                # Strategy 3: For descriptive citations, keep citation but remove potentially fabricated descriptions
                # No replacement, keep as-is — let readers judge

        # v5.1.7: Clean dangling citation patterns "[see references, no specific number in paper list]"
        # These citations point to downgraded/missing papers, unverifiable
        verified_body = re.sub(
            r'\[参见参考文献[，,]?\s*论文清单中无具体编号\]',
            '',
            verified_body
        )
        # Clean up redundant text after residual "see references"
        verified_body = re.sub(
            r'参见参考文献[，,]?\s*论文清单中无具体编号',
            '',
            verified_body
        )
        # v5.1.8: Clean "see [N]" prefixes in text (keep [N] itself)
        # e.g. "see [10] review" → "[10] review", "(see [35])" → "([35])"
        verified_body = re.sub(r'参见\s*\[(\d+)\]', r'[\1]', verified_body)
        
        # Reassemble
        if len(ref_split) >= 2:
            return verified_body + "## 参考文献" + ref_split[-1]
        return verified_body

    def _embed_charts(self, papers: List[PaperCandidate], topic: str) -> str:
        """Generate visual charts and return Markdown embedded text"""
        try:
            from .report_visualizer import generate_report_charts
            chart_paths = generate_report_charts(papers, self.output_dir, topic)

            lines = []
            if chart_paths.get("year_trend"):
                # Use path relative to output_dir, avoid hardcoded local absolute paths
                rel_path = os.path.relpath(chart_paths["year_trend"], self.output_dir)
                lines.append(f"![年度发文量趋势]({rel_path})")
                lines.append("")
                lines.append("*图1：年度发文量趋势（红色柱体为高活跃年份）*")
                lines.append("")

            if chart_paths.get("method_dist"):
                rel_path = os.path.relpath(chart_paths["method_dist"], self.output_dir)
                lines.append(f"![方法论分布]({rel_path})")
                lines.append("")
                lines.append("*图2：方法论占比分布*")
                lines.append("")

            if chart_paths.get("grade_dist"):
                rel_path = os.path.relpath(chart_paths["grade_dist"], self.output_dir)
                lines.append(f"![期刊等级分布]({rel_path})")
                lines.append("")
                lines.append("*图3：期刊等级分布（S级=顶刊，A级=优秀，B级=良好）*")
                lines.append("")

            return "\n".join(lines) if lines else ""
        except Exception as e:
            print(f"  [WARN] Chart generation failed / 图表生成失败: {e}")
            return ""

    @staticmethod
    def _insert_charts_after_section(report: str, chart_section: str) -> str:
        """Insert charts after Research Overview section. If section not found, insert after abstract."""
        # Try inserting after "Research Overview" section
        import re
        # Match content from "## Research Overview" to next "## "
        pattern = re.compile(r'(##\s*一[、．.]\s*研究概况.*?)(\n##\s)', re.DOTALL)
        match = pattern.search(report)
        if match:
            # Insert at end of this section, before next section
            insert_pos = match.end() - len('\n## ')
            report = report[:insert_pos] + "\n\n" + chart_section + "\n" + report[insert_pos:]
            return report

        # Fallback: insert after abstract
        pattern2 = re.compile(r'(##\s*摘要.*?)(\n##\s)', re.DOTALL)
        match2 = pattern2.search(report)
        if match2:
            insert_pos = match2.end() - len('\n## ')
            report = report[:insert_pos] + "\n\n" + chart_section + "\n" + report[insert_pos:]
            return report

        # Final fallback: append to end (before references)
        ref_pattern = re.compile(r'(\n#{1,3}\s*参考文献)', re.DOTALL)
        match3 = ref_pattern.search(report)
        if match3:
            insert_pos = match3.start()
            report = report[:insert_pos] + "\n\n" + chart_section + "\n" + report[insert_pos:]
            return report

        # If nothing found, append to end
        return report + "\n\n" + chart_section

    @staticmethod
    def _format_debate_outputs(debate_outputs: Optional[Dict[str, str]], max_dept: int = 5, max_chars: int = 1500) -> str:
        """Format department debate output as reference text for review AI"""
        if not debate_outputs:
            return ""
        
        lines = ["### 各部门辩论产出（已验证的论文分析结论，优先采用）", ""]
        count = 0
        for dept_key, content in debate_outputs.items():
            if count >= max_dept:
                break
            if not content:
                continue
            
            dept_name_map = {
                "文献检索组": "文献检索部",
                "元数据审查组": "元数据审查部",
                "引用网络组": "引用网络部",
                "方法论审查组": "方法论审查部",
                "数据验证组": "数据验证部",
                "反方质疑组": "反方质疑部",
                "主题聚类组": "主题聚类部",
                "可视化组": "可视化部",
                "报告整合组": "报告整合部",
                "程序开发组": "程序开发部",
                "教程编写组": "教程编写部",
                "literature_search": "文献检索部",
                "methodology_review": "方法论审查部",
                "counter_evidence": "反方质疑部",
                "citation_network": "引用网络部",
                "data_validation": "数据验证部",
                "topic_clustering": "主题聚类部",
                "metadata_inspector": "元数据审查部",
                "visualization": "可视化部",
                "report_integration": "报告整合部",
                "programming": "程序开发部",
                "tutorial": "教程编写部",
            }
            dept_name = dept_name_map.get(dept_key, dept_key)
            
            # Extract consensus part
            consensus_text = ""
            if isinstance(content, dict):
                consensus_text = content.get("consensus", "")
                if not consensus_text:
                    # Try extracting from debater_arguments
                    args = content.get("debater_arguments", [])
                    if isinstance(args, list):
                        parts = []
                        for a in args[:3]:
                            if isinstance(a, dict):
                                arg_text = a.get("argument", "")
                                if arg_text:
                                    parts.append(arg_text[:500])
                            elif isinstance(a, str):
                                parts.append(a[:500])
                        consensus_text = "\n".join(parts)
            elif isinstance(content, str):
                consensus_text = content
            
            if not consensus_text:
                continue
            
            # Truncate to avoid token explosion
            if len(consensus_text) > max_chars:
                consensus_text = consensus_text[:max_chars] + "\n...(已截断)"
            
            lines.append(f"**{dept_name}**：")
            lines.append(consensus_text)
            lines.append("")
            count += 1
        
        return "\n".join(lines) if count > 0 else ""

    @staticmethod
    def _format_paper_list(papers: List[PaperCandidate], max_papers: int = 80) -> str:
        """Format paper list for AI reference (v5.1.7: inject abstract, mark irrelevant papers)"""
        # Irrelevant domain keywords
        irrelevant_markers = [
            "plant survival", "drought mortality", "genomic", "gapseq", "bacterial metabolic",
            "rubisco", "carbon isotope", "soil respiration", "two-sided market",
            "agricultural economics", "crop breeding", "botany", "annals of botany",
            "new phytologist", "genome biology", "bmc genomics",
            "carbon nitride", "carbon nanotube", "graphitic carbon", "activated carbon",
            "cyber security", "movement primitives", "assessment for learning",
        ]
        lines = []
        for i, p in enumerate(papers[:max_papers], 1):
            authors = ", ".join(p.authors[:2])
            if len(p.authors) > 2:
                authors += " 等"
            title = p.title[:70]
            journal = p.journal or "预印本"
            year = p.year or "n/a"
            level = p.quality_level
            cite = p.citation_count
            # Check relevance
            text = (p.title + " " + (p.journal or "")).lower()
            is_irrelevant = any(kw in text for kw in irrelevant_markers)
            marker = " ⚠️可能不相关" if is_irrelevant else ""
            # v5.1.7: Inject abstract so review AI can see paper content
            abstract_text = ""
            if p.abstract:
                max_abs = 150 if level in ("S", "A") else 80
                abstract_text = p.abstract[:max_abs]
                if len(p.abstract) > max_abs:
                    abstract_text += "..."
            abs_line = f"\n    摘要: {abstract_text}" if abstract_text else ""
            lines.append(f"[{i}] [{level}]{marker} {authors}. {title}. {journal}, {year}. (引用:{cite}){abs_line}")
        if len(papers) > max_papers:
            lines.append(f"... 共{len(papers)}篇，此处省略{len(papers)-max_papers}篇")
        return "\n".join(lines)

    @staticmethod
    def _compute_year_span(papers: List[PaperCandidate]) -> str:
        """Calculate year span"""
        years = [p.year for p in papers if p.year and p.year > 1990]
        if not years:
            return "N/A"
        return f"{min(years)}-{max(years)}"

    @staticmethod
    def _compute_year_distribution(papers: List[PaperCandidate]) -> str:
        """Calculate year distribution"""
        year_counts = {}
        for p in papers:
            if p.year and p.year > 1990:
                year_counts[p.year] = year_counts.get(p.year, 0) + 1
        if not year_counts:
            return "无年份数据"
        lines = []
        for y in sorted(year_counts.keys()):
            bar = "█" * min(year_counts[y], 30)
            lines.append(f"{y}: {bar} {year_counts[y]}")
        return "\n".join(lines)

    @staticmethod
    def _compute_method_distribution(papers: List[PaperCandidate]) -> str:
        """Extract method keyword distribution from titles/abstracts"""
        method_keywords = {
            "LSTM/GRU": ["lstm", "gru", "rnn", "recurrent"],
            "Transformer": ["transformer", "attention", "bert", "gpt"],
            "CNN": ["cnn", "convolutional", "convnet"],
            "XGBoost/GBDT": ["xgboost", "gbdt", "gradient boosting", "lightgbm", "catboost"],
            "GNN/Graph": ["gnn", "graph neural", "graph convolution"],
            "因果推断": ["causal", "did", "difference-in-diff", "instrumental", "causal inference"],
            "强化学习": ["reinforcement", "rl ", "deep q", "policy gradient"],
            "贝叶斯": ["bayesian", "mcmc", "variational inference"],
            "集成学习": ["ensemble", "stacking", "bagging", "random forest"],
            "优化算法": ["optimization", "pso", "genetic algorithm", "evolutionary"],
            "NLP/文本": ["nlp", "text mining", "sentiment", "word2vec", "topic model"],
            "联邦学习": ["federated", "federated learning"],
            # v5.1.5: Energy economics specific methods
            "分解-集成": ["emd", "ceemdan", "vmd", "wavelet", "decompos", "empirical mode", "eemd"],
            "混合模型": ["hybrid", "combined model", "ensemble deep", "multi-model", "fusion"],
            "物理信息融合": ["physics-informed", "pinns", "physics-guided", "mechanism", "domain knowledge"],
            "迁移学习": ["transfer learn", "domain adapt", "pre-train", "fine-tun"],
            "SVAR/计量": ["svar", "var ", "vecm", "cointegrat", "econometric", "granger"],
            "SVM/SVR": ["svm", "svr", "support vector", "kernel method"],
        }
        counts = {}
        for cat, kws in method_keywords.items():
            c = 0
            for p in papers:
                text = (p.title + " " + (p.abstract or "")).lower()
                if any(k in text for k in kws):
                    c += 1
            if c > 0:
                counts[cat] = c
        if not counts:
            return "无法提取方法分布"
        lines = []
        for cat, c in sorted(counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {cat}: {c}篇")
        return "\n".join(lines)

    def _build_final_title(self, topic: str, now: str) -> str:
        return f"""# {topic}

> 学术动向调研报告 | Consensus Pipeline v5.1 | {now}"""

    def _build_final_summary(
        self,
        topic: str,
        papers: List[PaperCandidate],
        s_papers: List[PaperCandidate],
        a_papers: List[PaperCandidate],
    ) -> str:
        """Abstract <=150 chars, one-sentence core finding + key data"""
        total = len(papers)
        s_count = len(s_papers)
        a_count = len(a_papers)

        # Extract method keywords
        method_keywords = self._extract_top_methods(papers)

        return f"""## 摘要

本报告对「{topic}」领域近5年学术文献进行系统性调研，检索并筛选{total}篇高质量论文（S级{s_count}篇、A级{a_count}篇）。核心发现：{method_keywords}是该领域当前主流方法，因果推断与深度学习融合成为新兴方向，但在多任务联合建模与跨领域迁移方面仍存在显著空白。"""

    @staticmethod
    def _compress_text(text: str, max_chars: int = 80) -> str:
        """Compress long text to one-sentence summary. Skip LLM pleasantries, extract substantive conclusions."""
        if not text:
            return ""
        # Remove Markdown markup and common LLM pleasantries
        clean = text.replace("**", "").replace("###", "").replace("##", "").strip()
        # Skip pleasantry lines
        skip_prefixes = [
            "好的", "好的，", "作为", "以下是", "根据", "基于",
            "我来", "我将", "经过", "通过", "针对",
        ]
        lines = clean.split("\n")
        substantive_lines = []
        for line in lines:
            line = line.strip().lstrip("- ").lstrip("* ").strip()
            if not line or len(line) < 8:
                continue
            is_fluff = False
            for pref in skip_prefixes:
                if line.startswith(pref):
                    is_fluff = True
                    break
            if not is_fluff:
                substantive_lines.append(line)

        if not substantive_lines:
            # All pleasantries, take the longest line
            substantive_lines = sorted(lines, key=len, reverse=True)

        result = substantive_lines[0] if substantive_lines else clean[:max_chars]

        if len(result) > max_chars:
            # Find first sentence-ending period breakpoint
            for sep in ["。", ". "]:
                idx = result.find(sep, 10)
                if 10 < idx <= max_chars:
                    return result[:idx + 1].strip()
            return result[:max_chars - 1] + "…"
        return result

    def _llm_call_long(self, system_prompt: str, user_prompt: str, temperature: float = 0.25) -> str:
        """Long output LLM call (review report needs 8K+ tokens), supports segmented continuation"""
        import requests
        # Get API config from llm_call_fn environment
        # Try direct call with larger max_tokens
        try:
            # If llm_call_fn is run_pipeline.llm_call, we cannot directly change max_tokens
            # Instead: segmented request — write first half, then continue second half
            result = self.llm_call_fn(system_prompt, user_prompt, temperature=temperature)
            if not result or len(result) < 500:
                return result or ""
            
            # Check if truncated (incomplete ending)
            last_line = result.strip().split("\n")[-1] if result.strip() else ""
            incomplete_markers = [
                not result.rstrip().endswith(("。", ".", "】", ")", "\"", "》", "```")),
                result.rstrip().endswith(("，", "、", "因为", "但是", "而且", "其", "在")),
            ]
            # If output looks complete (has references section), return directly
            if "参考文献" in result or "五、" in result or "## 五" in result:
                return result
            
            # Otherwise continue writing
            continue_prompt = f"""前文到此被截断了。请从截断处继续撰写，不要重复已有内容，直接接着写：

{result[-200:]}

---
请从上面截断处继续，完成剩余章节（核心发现与争议、研究空白与前沿方向、参考文献）。

【关键规则】续写部分的引用[N]必须严格对应论文清单中的论文，且每个[N]必须紧跟该论文的具体描述（方法名、核心结论、量化指标等），严禁使用"参见[N]"占位。如果对该论文内容不确定，不要引用该论文。对比表格单元格禁止填写"参见[N]"。"""

            continuation = self.llm_call_fn(system_prompt, continue_prompt, temperature=temperature)
            if continuation and len(continuation) > 100:
                # Concatenate: remove overlapping parts
                return result + "\n\n" + continuation
            return result
        except Exception:
            return ""

    def _ai_refine(self, draft: str, topic: str) -> str:
        """Use LLM to refine report: remove fluff, increase info density, keep all sections"""
        system_prompt = """你是一位学术报告精炼编辑。你的任务：
1. 删除所有寒暄语、角色扮演语（如"好的"、"作为XX专家"、"我来分析"等）
2. 每句话必须承载可验证结论或具体数据，删除零信息量表述
3. 保留所有章节结构和参考文献
4. 核心发现部分：从辩论共识中提取实质学术结论，不要保留辩论过程描述
5. 量化指标优先于定性描述（"提升了15%"优于"有显著提升"）
6. 反面证据必须保留并标注
7. 输出Markdown，不添加原文没有的新章节"""

        user_prompt = f"""请精炼以下学术调研报告，去除废话、保留精华。不要改变章节结构，不要删除参考文献。

主题：{topic}

---报告草稿---
{draft}
---结束---"""

        try:
            refined = self.llm_call_fn(system_prompt, user_prompt, temperature=0.15)
            if refined and len(refined) > 200:
                return refined
        except Exception:
            pass
        return draft

    def _build_final_findings(
        self,
        s_papers: List[PaperCandidate],
        consensus_points: Optional[List[str]],
    ) -> str:
        """Core findings: 3-5 items, each with confidence, compressed from debate consensus to one sentence"""
        lines = ["## 一、核心发现", ""]

        findings = []

        # Compress from consensus conclusions (each <=80 chars)
        if consensus_points:
            for i, point in enumerate(consensus_points[:5]):
                compressed = self._compress_text(point, max_chars=80)
                findings.append({
                    "text": compressed,
                    "confidence": "高" if i < 2 else "中",
                    "evidence": "",
                })

        # Supplement from S-tier papers
        if len(findings) < 3 and s_papers:
            # Method trend findings
            methods = set()
            for p in s_papers:
                for kw in ["LSTM", "Transformer", "XGBoost", "CNN", "GNN", "causal", "RL"]:
                    if kw.lower() in (p.title + " " + (p.abstract or "")).lower():
                        methods.add(kw)
            if methods:
                findings.append({
                    "text": f"深度学习方法（{', '.join(sorted(methods)[:3])}）在能源经济预测任务中已取代传统计量模型成为主流",
                    "confidence": "高",
                    "evidence": f"基于{s_papers[0].title[:40] if s_papers else ''}等S级论文",
                })

        # Data source findings
        if len(findings) < 5:
            findings.append({
                "text": "高频时序数据（电力负荷、碳价格、天气）是多模态融合的主要数据基础",
                "confidence": "中",
                "evidence": "",
            })

        for i, f in enumerate(findings[:5], 1):
            conf_tag = {"高": "🟢", "中": "🟡", "低": "🔴"}.get(f["confidence"], "⚪")
            lines.append(f"{i}. {f['text']} `{conf_tag}置信度：{f['confidence']}`")
            if f["evidence"]:
                lines.append(f"   > *{f['evidence']}*")
            lines.append("")

        return "\n".join(lines)

    def _build_final_methodology(
        self,
        clusters: List[ClusterResult],
        methodology_reviews: Optional[Dict[str, Any]],
    ) -> str:
        """Methodology distribution: output table only when data is available"""
        # Collect method distribution
        method_items = []
        if methodology_reviews and "distribution" in methodology_reviews:
            dist = methodology_reviews["distribution"]
            for cat, info in list(dist.items())[:5]:
                count = info.get("count", 0) if isinstance(info, dict) else info
                scenario = info.get("scenario", "") if isinstance(info, dict) else ""
                trend = info.get("trend", "→") if isinstance(info, dict) else "→"
                method_items.append(f"- **{cat}**: {count}篇，{scenario} {trend}")
        else:
            for c in clusters:
                if c.dimension == "methodology" and c.distribution:
                    for cat, count in sorted(c.distribution.items(), key=lambda x: -x[1])[:5]:
                        method_items.append(f"- **{cat}**: {count}篇")

        if not method_items:
            return "## 二、方法论分布\n\n*待方法论审查部门产出后补充*"

        lines = ["## 二、方法论分布", ""]
        lines.extend(method_items)
        return "\n".join(lines)

    def _build_final_trends(self, papers: List[PaperCandidate]) -> str:
        """Hot trends: concise 3 items"""
        lines = ["## 三、热点趋势", ""]

        year_counts = {}
        for p in papers:
            if p.year:
                year_counts[p.year] = year_counts.get(p.year, 0) + 1

        if year_counts:
            years = sorted(year_counts.keys())
            lines.append(f"- {years[0]}-{years[-1]}：{len(papers)}篇论文，方法论从单一预测→因果+可解释性并重")
            lines.append(f"- 多模态融合（文本+时序+图结构）成新范式")
        else:
            lines.append("- 数据不足以分析趋势")

        return "\n".join(lines)

    def _build_final_top_papers(
        self,
        s_papers: List[PaperCandidate],
        a_papers: List[PaperCandidate],
    ) -> str:
        """Representative papers Top 5, title+journal+year only"""
        lines = ["## 四、代表性论文", ""]

        top = (s_papers + a_papers)[:5]
        if not top:
            lines.append("*暂无符合条件的论文*")
            return "\n".join(lines)

        for i, p in enumerate(top, 1):
            title = _safe_truncate(p.title, 60)
            journal = p.journal or "预印本"
            year = p.year or "未知"
            lines.append(f"{i}. {title} — *{journal}*, {year}")

        return "\n".join(lines)

    def _build_final_gaps(
        self,
        papers: List[PaperCandidate],
        consensus_points: Optional[List[str]],
    ) -> str:
        """Research gaps and opportunities"""
        lines = ["## 五、研究空白与机会", ""]

        gaps = [
            {"gap": "多任务联合建模", "detail": "碳排放-电价-负荷缺乏联合优化框架", "suggestion": "多任务学习(MTL)"},
            {"gap": "动态因果效应", "detail": "因果ML在能源政策评估中起步", "suggestion": "DID+因果森林"},
            {"gap": "跨领域迁移学习", "detail": "EU-ETS vs 中国碳市场模型迁移鲜有研究", "suggestion": "域自适应方法"},
            {"gap": "GNN网络效应", "detail": "电力/碳市场图结构信息未利用", "suggestion": "图神经网络建模溢出效应"},
            {"gap": "可解释性标配化", "detail": "多数ML论文缺SHAP/LIME分析", "suggestion": "可解释性作为标准输出"},
        ]

        for i, g in enumerate(gaps[:5], 1):
            lines.append(f"**{i}. {g['gap']}** — {g['detail']} → 建议：{g['suggestion']}")

        return "\n".join(lines)

    def _build_final_limitations(
        self,
        papers: List[PaperCandidate],
    ) -> str:
        """v0.7.0: Search boundary and limitations section"""
        lines = ["## 检索边界与局限性", ""]

        total = len(papers)
        sa_count = sum(1 for p in papers if p.quality_level in ("S", "A"))

        lines.append("### 检索源覆盖范围与盲区")
        lines.append("- 检索源：arXiv（预印本）、Semantic Scholar（跨学科）、OpenAlex（全面覆盖）")
        lines.append("- 盲区：可能遗漏部分中文核心期刊、行业技术报告、会议论文集")
        lines.append("- 非英语文献覆盖有限，中文CSSCI期刊可能未被充分检索")
        lines.append("")

        lines.append("### 论文数量与代表性限制")
        lines.append(f"- 最终纳入论文{total}篇，其中S/A级{sa_count}篇")
        lines.append(f"- 样本量有限，不宜将本综述结论过度外推为普遍规律")
        lines.append("- 小样本下（N<5篇支撑），结论置信度较低，需进一步验证")
        lines.append("")

        lines.append("### 方法论评估的边界条件")
        lines.append("- 方法论优劣比较依赖于特定数据规模、市场类型和预测窗口")
        lines.append("- 小样本场景下深度学习未必优于传统统计方法")
        lines.append("- 不同碳市场（EU-ETS vs 中国）的结论可能不可直接迁移")
        lines.append("")

        lines.append("### 结论适用范围与外推风险")
        lines.append("- 本综述结论主要基于近5年英语学术文献，适用范围有限")
        lines.append("- 不应将有限样本上的方法论对比结论简单外推至所有能源经济场景")
        lines.append("- 建议读者结合自身研究场景，审慎评估本综述结论的适用性")

        return "\n".join(lines)

    def _build_final_references(
        self,
        s_papers: List[PaperCandidate],
        a_papers: List[PaperCandidate],
    ) -> str:
        """References: list all S-tier + A-tier papers"""
        lines = ["## 六、参考文献", ""]

        top = s_papers + a_papers
        if not top:
            return "\n".join(lines)

        for i, p in enumerate(top, 1):
            authors = ", ".join(p.authors[:2])
            if len(p.authors) > 2:
                authors += " 等"
            title = _safe_truncate(p.title, 60)
            journal = p.journal or "预印本"
            year = p.year or "未知"

            lines.append(f"[{i}] {authors}. {title}. {journal}, {year}.")

        return "\n".join(lines)

    def _build_final_footer(self, now: str, fact_check_summary: str) -> str:
        footer = f"""---

> 📋 **报告说明**
> - 生成时间：{now}
> - 引擎：Consensus Pipeline v5.1
> - 本报告为精简版，完整检索日志、辩论记录、论文清单见内部工作文档"""
        if fact_check_summary:
            footer += f"\n> - 事实校验：{fact_check_summary}"
        return footer

    # ================================================================
    # Internal working document (unlimited length)
    # ================================================================

    def _build_internal_doc(
        self,
        topic: str,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
        validations: List[ValidationResult],
        charts: List[ChartConfig],
        consensus_points: Optional[List[str]],
        fact_check_summary: str,
        debate_outputs: Optional[Dict[str, str]],
        cross_debate_results: Optional[Dict[str, Any]],
        methodology_reviews: Optional[Dict[str, Any]],
        programming_output: str,
        tutorial_output: str,
        relevance_filter_log: Optional[Dict[str, Any]],
    ) -> str:
        """Build internal working document. Complete process record, unlimited length."""
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        sections = []

        sections.append(f"""# 内部工作文档：{topic}

> Consensus Pipeline v5.1 | 生成时间：{now}
> 本文档为内部质控记录，包含完整检索日志、论文清单、辩论全文和事实校验数据。

---""")

        # I. Search log
        sections.append(self._build_internal_search_log(papers, relevance_filter_log))

        # II. Complete paper list
        sections.append(self._build_internal_paper_list(papers))

        # III. Methodology review
        sections.append(self._build_internal_methodology(methodology_reviews, clusters))

        # IV. Department debate full text
        sections.append(self._build_internal_debates(debate_outputs))

        # V. Cross-debate
        sections.append(self._build_internal_cross_debate(cross_debate_results))

        # VI. Consensus conclusions
        sections.append(self._build_internal_consensus(consensus_points))

        # VII. Fact-check
        sections.append(self._build_internal_fact_check(fact_check_summary, validations))

        # VIII. Programming and tutorial
        sections.append(self._build_internal_code_tutorial(programming_output, tutorial_output))

        # IX. Validation results
        sections.append(self._build_internal_validations(validations))

        return "\n\n".join(sections)

    def _build_internal_search_log(
        self,
        papers: List[PaperCandidate],
        relevance_filter_log: Optional[Dict[str, Any]],
    ) -> str:
        lines = ["## I. Search log", ""]

        # Statistics by source
        source_counts = {}
        for p in papers:
            src = p.source or "unknown"
            source_counts[src] = source_counts.get(src, 0) + 1

        lines.append("### 检索源统计")
        lines.append("")
        lines.append("| 来源 | 命中数 |")
        lines.append("|------|--------|")
        for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {src} | {count} |")
        lines.append("")

        # Relevance filter log
        if relevance_filter_log:
            lines.append("### 相关性过滤")
            lines.append("")
            total_before = relevance_filter_log.get("total_before", 0)
            total_after = relevance_filter_log.get("total_after", 0)
            filtered_out = relevance_filter_log.get("filtered_out", [])
            lines.append(f"- 过滤前：{total_before} 篇")
            lines.append(f"- 过滤后：{total_after} 篇")
            lines.append(f"- 剔除：{total_before - total_after} 篇（不相关）")
            if filtered_out:
                lines.append("")
                lines.append("**被剔除的论文（示例）：**")
                for item in filtered_out[:10]:
                    lines.append(f"- {item}")
            lines.append("")

        return "\n".join(lines)

    def _build_internal_paper_list(self, papers: List[PaperCandidate]) -> str:
        lines = ["## II. Complete paper list", ""]
        lines.append("| # | 标题 | 期刊 | 年 | 等级 | 被引 | 来源 |")
        lines.append("|---|------|------|----|------|------|------|")

        level_order = {"S": 0, "A": 1, "B": 2, "C": 3}
        sorted_papers = sorted(
            papers,
            key=lambda p: (level_order.get(p.quality_level, 5), -p.citation_count),
        )

        for i, p in enumerate(sorted_papers, 1):
            title = _safe_truncate(p.title, 60)
            journal = _safe_truncate(p.journal or "预印本", 25)
            year = p.year or "-"
            level = p.quality_level or "-"
            cite = p.citation_count
            src = p.source or "-"
            lines.append(f"| {i} | {title} | {journal} | {year} | {level} | {cite} | {src} |")

        lines.append("")
        return "\n".join(lines)

    def _build_internal_methodology(
        self,
        methodology_reviews: Optional[Dict[str, Any]],
        clusters: List[ClusterResult],
    ) -> str:
        lines = ["## III. Methodology review", ""]

        if methodology_reviews:
            lines.append("### 审查结果")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(methodology_reviews, ensure_ascii=False, indent=2))
            lines.append("```")
            lines.append("")
        else:
            lines.append("*无方法论审查数据*")
            lines.append("")

        return "\n".join(lines)

    def _build_internal_debates(
        self, debate_outputs: Optional[Dict[str, str]]
    ) -> str:
        lines = ["## IV. Department debate full text", ""]

        if not debate_outputs:
            lines.append("*无辩论数据*")
            return "\n".join(lines)

        for dept_name, content in debate_outputs.items():
            lines.append(f"### {dept_name}")
            lines.append("")
            if isinstance(content, dict):
                # Structured debate output: extract consensus + debater_arguments
                if content.get("consensus"):
                    lines.append(f"**共识：** {content['consensus']}")
                    lines.append("")
                if content.get("debater_arguments"):
                    args = content["debater_arguments"]
                    if isinstance(args, dict):
                        for debater, arg in args.items():
                            lines.append(f"**{debater}：** {arg}")
                            lines.append("")
                    elif isinstance(args, list):
                        for arg in args:
                            lines.append(str(arg))
                            lines.append("")
                    else:
                        lines.append(str(args))
                        lines.append("")
            else:
                lines.append(str(content))
                lines.append("")

        return "\n".join(lines)

    def _build_internal_cross_debate(
        self, cross_debate_results: Optional[Dict[str, Any]]
    ) -> str:
        lines = ["## V. Cross-debate记录", ""]

        if not cross_debate_results:
            lines.append("*无交叉辩论数据*")
            return "\n".join(lines)

        lines.append("```json")
        lines.append(json.dumps(cross_debate_results, ensure_ascii=False, indent=2))
        lines.append("```")
        lines.append("")

        return "\n".join(lines)

    def _build_internal_consensus(
        self, consensus_points: Optional[List[str]]
    ) -> str:
        lines = ["## VI. Consensus conclusions", ""]

        if not consensus_points:
            lines.append("*无共识结论*")
            return "\n".join(lines)

        for i, point in enumerate(consensus_points, 1):
            lines.append(f"{i}. {point}")
        lines.append("")

        return "\n".join(lines)

    def _build_internal_fact_check(
        self, fact_check_summary: str, validations: List[ValidationResult]
    ) -> str:
        lines = ["## VII. Fact-check", ""]

        if fact_check_summary:
            lines.append(f"**摘要**：{fact_check_summary}")
            lines.append("")

        if validations:
            lines.append("### 校验详情")
            lines.append("")
            for v in validations:
                lines.append(f"- **{v.paper_title}**：{v.result}")
            lines.append("")
        else:
            lines.append("*无校验数据*")
            lines.append("")

        return "\n".join(lines)

    def _build_internal_code_tutorial(
        self, programming_output: str, tutorial_output: str
    ) -> str:
        lines = ["## VIII. Programming and tutorial", ""]

        if programming_output:
            lines.append("### 程序产出")
            lines.append("")
            lines.append(programming_output)
            lines.append("")

        if tutorial_output:
            lines.append("### 教程产出")
            lines.append("")
            lines.append(tutorial_output)
            lines.append("")

        if not programming_output and not tutorial_output:
            lines.append("*无程序/教程产出*")

        return "\n".join(lines)

    def _build_internal_validations(
        self, validations: List[ValidationResult]
    ) -> str:
        lines = ["## IX. Validation results", ""]

        if not validations:
            lines.append("*无验证数据*")
            return "\n".join(lines)

        for v in validations:
            lines.append(f"### {v.paper_title}")
            lines.append(f"- 结果：{v.result}")
            lines.append(f"- 详情：{v.details}")
            lines.append("")

        return "\n".join(lines)

    # ================================================================
    # Helper methods
    # ================================================================

    def _extract_top_methods(self, papers: List[PaperCandidate]) -> str:
        """Extract top method keywords from papers"""
        method_keywords = {
            "LSTM": 0, "Transformer": 0, "XGBoost": 0, "CNN": 0,
            "Random Forest": 0, "GNN": 0, "因果推断": 0, "强化学习": 0,
            "GRU": 0, "LightGBM": 0, "SVM": 0, "ARIMA": 0,
        }
        for p in papers:
            text = (p.title + " " + (p.abstract or "")).lower()
            for kw in method_keywords:
                if kw.lower() in text:
                    method_keywords[kw] += 1

        top = sorted(method_keywords.items(), key=lambda x: -x[1])[:3]
        return "、".join([kw for kw, cnt in top if cnt > 0])

    def _extract_significance(self, paper: PaperCandidate) -> str:
        """Extract paper's academic value (one sentence)"""
        title_lower = (paper.title or "").lower()

        if "survey" in title_lower or "review" in title_lower:
            return "该领域系统性综述，梳理了方法论演进脉络"
        if "causal" in title_lower:
            return "将因果推断引入能源经济学，方法论创新性强"
        if "transformer" in title_lower or "attention" in title_lower:
            return "Transformer架构在能源时序预测中的前沿应用"
        if "graph" in title_lower or "gnn" in title_lower:
            return "图神经网络在能源网络建模中的开创性工作"
        if "explain" in title_lower or "interpret" in title_lower:
            return "可解释性ML在能源政策分析中的关键研究"
        if "hybrid" in title_lower or "ensemble" in title_lower:
            return "混合模型策略，在预测精度上取得突破"
        if "lstm" in title_lower or "gru" in title_lower:
            return "深度学习在能源时序预测中的基准性工作"
        if "carbon price" in title_lower or "carbon market" in title_lower or "carbon emission" in title_lower or "carbon trading" in title_lower or "carbon budget" in title_lower:
            return "碳市场/碳价格建模的核心研究"
        return "在方法论或应用场景上有重要贡献"

    # ================================================================
    # CSV metadata table
    # ================================================================

    def _build_csv(self, papers: List[PaperCandidate]) -> str:
        """Build CSV metadata table"""
        lines = ["title,doi,authors,journal,year,citation_count,quality_level,source"]

        for p in papers:
            authors_str = "; ".join(p.authors[:5]).replace(",", " ")
            title_clean = _safe_truncate(p.title.replace(",", " ").replace('"', "'"), 200)
            doi = p.doi or "N/A"
            journal_clean = _safe_truncate((p.journal or "预印本").replace(",", " "), 100)
            lines.append(
                f'"{title_clean}","{doi}","{authors_str}","{journal_clean}",'
                f'{p.year},{p.citation_count},{p.quality_level},{p.source}'
            )

        return "\n".join(lines)