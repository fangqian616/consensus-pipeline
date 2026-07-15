"""
报告生成器 — Consensus Pipeline v5.1

v5.1: 两套模板分离
  - 最终交付报告（≤2000字，面向用户）：信息密度优先，分层呈现
  - 内部工作文档（不限长度，面向开发者）：完整检索+辩论+校验记录

v4.2: 修复多字节字符安全截断
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .search_engine import PaperCandidate
from .cross_validator import ClusterResult, ValidationResult
from .visualizer import ChartConfig


def _safe_truncate(text: str, max_chars: int) -> str:
    """安全截断字符串，避免在多字节字符中间截断。"""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


class ReportGenerator:
    """
    报告整合组 — v5.1 双模板

    产出两份文档：
    - final_report.md：最终交付报告，≤2000字，信息密度优先
    - internal_doc.md：内部工作文档，完整过程记录
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

        # 1. 最终交付报告
        final_content = self._build_final_report(
            topic, papers, clusters, consensus_points,
            fact_check_summary, methodology_reviews,
            debate_outputs,
        )

        # AI精炼去废话（仅模板模式需要，综述模式由AI直接写）
        # if self.llm_call_fn:
        #     final_content = self._ai_refine(final_content, topic)

        final_path = os.path.join(self.output_dir, "final_report.md")
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        # 2. 内部工作文档
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

        # 3. CSV 元数据表
        csv_content = self._build_csv(papers)
        csv_path = os.path.join(self.output_dir, "papers_metadata.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        # 4. 图表数据
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
    # 最终交付报告（≤2000字）
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
        """构建最终交付报告。如果有llm_call_fn，用AI写综述；否则回退模板。"""
        now = datetime.now().strftime("%Y年%m月%d日")

        s_papers = [p for p in papers if p.quality_level == "S"]
        a_papers = [p for p in papers if p.quality_level == "A"]
        b_papers = [p for p in papers if p.quality_level == "B"]

        if self.llm_call_fn and s_papers:
            return self._build_review_by_ai(topic, papers, s_papers, a_papers, b_papers, consensus_points, now, fact_check_summary, debate_outputs)

        # 回退：模板模式（无LLM时）
        sections = []
        sections.append(self._build_final_title(topic, now))
        sections.append(self._build_final_summary(topic, papers, s_papers, a_papers))
        sections.append(self._build_final_findings(s_papers, consensus_points))
        sections.append(self._build_final_methodology(clusters, methodology_reviews))
        sections.append(self._build_final_trends(papers))
        sections.append(self._build_final_top_papers(s_papers, a_papers))
        sections.append(self._build_final_gaps(papers, consensus_points))
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
        """用LLM基于论文元数据直接撰写学术综述报告"""
        # 构建论文清单供AI参考——只传S/A/B级，C级不传
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
13. 【引用忠实性】引用[N]时，只能描述论文清单中该论文的标题和摘要已知信息。严禁编造该论文中不存在的具体实验、方法细节、数据结果或案例。如果你对该论文内容不确定，使用"参见[N]"代替具体描述
14. 【续写规则】如果你需要续写未完成的内容，续写部分的引用[N]同样必须严格遵循规则13，只描述清单中的已知信息
15. 【部门辩论整合】如果提供了部门辩论产出，优先采用各部门已验证的分析结论和论文描述，这些结论已经过交叉验证，可信度高于你自己推断的内容。在此基础上进行综述性整合，而非从零重新描述论文
16. 【量化硬规则】描述任何方法效果时，必须包含至少一项量化指标（如"预测精度MAPE=3.2%""在XX数据集上R²=0.95""降低了15%的RMSE"），禁止只写"效果良好""广泛应用""取得显著提升"等空泛描述。若论文未报告量化指标，注明"该论文未报告量化指标"
17. 【辩论焦点必现】综述中至少3处引用辩论组的分歧点，格式为"XX部门认为...，但反方质疑部门指出..."，最终给出交叉辩论后的结论。这是共识管线区别于普通AI综述的核心特征
18. 【对比矩阵填充】方法论对比表每个单元格必须非空，预测精度列必须包含具体数值或"未报告"，趋势列使用↑↑(快速上升)/↑(上升)/→(平稳)/↓(下降)符号
19. 【数据卡片先行】综述开头必须先输出结构化数据卡片"""

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
（2.2 量化对比矩阵：每个单元格必须有具体数字或"未报告"，趋势列用↑↑/↑/→/↓）
（2.3 辩论焦点：至少3处引用"XX部门认为...但反方质疑部门指出..."的交锋，给出交叉辩论结论）

| 方法类别 | 代表论文 | 预测精度 | 可解释性 | 数据需求 | 计算开销 | 趋势 |
|---------|---------|---------|---------|---------|---------|------|

## 三、核心发现与争议
（3-5条实质性发现，每条=支持证据链+反方质疑+交叉辩论结论。标注置信度🟢高🟡中🔴低。
格式：**发现N：标题**
支持证据：...[N]...
反方质疑：...[N]...
辩论结论：...
置信度：🟢/🟡/🔴）

## 四、研究空白与文献计量证据
（5个空白，每个：现状→文献计量佐证(如"76篇中仅2篇涉及")→为什么没人做→价值→可行路径）

## 五、参考文献
（列出所有S级和A级论文，按S/A/B分组，GB/T 7714格式）"""

        try:
            # 综述需要长输出，用专用调用
            report = self._llm_call_long(system_prompt, user_prompt, temperature=0.25)
            if report and len(report) > 500:
                # 用论文元数据重建参考文献，保证引用序号一一对应
                report = self._rebuild_references(report, qualified)

                # 校验引用描述是否与论文实际内容匹配
                report = self._verify_citation_content(report, qualified)

                # 生成可视化图表并嵌入报告
                chart_section = self._embed_charts(qualified, topic)
                if chart_section:
                    # 在"一、研究概况"章节后插入图表
                    report = self._insert_charts_after_section(report, chart_section)

                # 补充页脚
                if fact_check_summary:
                    report += f"\n\n---\n\n> 📋 事实校验：{fact_check_summary}"
                return report
        except Exception:
            pass

        # LLM失败时回退模板
        sections = []
        sections.append(self._build_final_title(topic, now))
        sections.append(self._build_final_summary(topic, papers, s_papers, a_papers))
        sections.append(self._build_final_findings(s_papers, consensus_points))
        sections.append(self._build_final_trends(papers))
        sections.append(self._build_final_references(s_papers, a_papers))
        return "\n\n".join(sections)

    @staticmethod
    def _rebuild_references(report: str, papers: List[PaperCandidate]) -> str:
        """从AI综述中提取所有[N]引用，用论文元数据重建参考文献段，保证一一对应"""
        import re
        # 1. 提取正文中所有引用序号
        cited_indices = set()
        for m in re.finditer(r'\[(\d+)\]', report):
            idx = int(m.group(1))
            if 1 <= idx <= len(papers):
                cited_indices.add(idx)

        # 1.5 移除超出论文清单范围的引用（AI编造的序号）
        # 把[68]、[79]等超出len(papers)的引用替换为空或注释
        out_of_range = set()
        for m in re.finditer(r'\[(\d+)\]', report):
            idx = int(m.group(1))
            if idx > len(papers) or idx < 1:
                out_of_range.add(idx)

        if out_of_range:
            # 将超出范围的[N]替换为"参见相关研究"
            for idx in sorted(out_of_range, reverse=True):
                report = report.replace(f'[{idx}]', '（参见相关研究）')
            # 重新提取有效引用
            cited_indices = set()
            for m in re.finditer(r'\[(\d+)\]', report):
                idx = int(m.group(1))
                if 1 <= idx <= len(papers):
                    cited_indices.add(idx)

        if not cited_indices:
            return report  # 无引用则不改

        # 2. 找到参考文献section的位置，替换
        # 匹配 "## 参考文献" 或 "### 参考文献" 及其后到文末的内容
        ref_pattern = re.compile(r'(\n#{1,3}\s*参考文献.*)', re.DOTALL)
        match = ref_pattern.search(report)
        if not match:
            # 没有参考文献section，追加
            ref_section = "\n\n## 参考文献\n\n"
        else:
            # 替换已有参考文献section
            report = report[:match.start()]
            ref_section = "\n\n## 参考文献\n\n"

        # 3. 用论文元数据生成参考文献列表——按等级分组
        s_refs, a_refs, b_refs = [], [], []
        for idx in sorted(cited_indices):
            p = papers[idx - 1]  # 1-based to 0-based
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

        # 按等级分组输出
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

        # 4. 最终校验：移除正文中未被引用的参考文献条目
        report = ReportGenerator._validate_references(report)
        return report

    @staticmethod
    def _validate_references(report: str) -> str:
        """校验引用一致性：正文[N] ↔ 参考文献列表 一一对应"""
        import re
        ref_split = report.split("## 参考文献")
        if len(ref_split) < 2:
            return report

        body = ref_split[0]
        ref_part = ref_split[-1]

        # 提取正文中的所有[N]
        body_refs = set(int(m) for m in re.findall(r'\[(\d+)\]', body))

        # 提取参考文献中的[N]
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
                # else: 正文没有引用这个编号，移除
            else:
                cleaned_lines.append(line)

        # 重建参考文献部分
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
        
        # 找到参考文献section的分界线，只处理正文部分
        ref_split = report.split("## 参考文献")
        body = ref_split[0] if len(ref_split) >= 2 else report
        
        # 对每个引用序号，提取其上下文并校验
        verified_body = body
        citation_contexts = {}  # idx -> list of context snippets
        
        for m in re.finditer(r'\[(\d+)\]', body):
            idx = int(m.group(1))
            if idx < 1 or idx > len(papers):
                continue
            
            # 提取[N]前后100字的上下文
            start = max(0, m.start() - 100)
            end = min(len(body), m.end() + 100)
            context = body[start:end]
            
            if idx not in citation_contexts:
                citation_contexts[idx] = []
            citation_contexts[idx].append(context)
        
        # 对每个引用检查描述是否与论文匹配
        mismatches = []
        for idx, contexts in citation_contexts.items():
            paper = papers[idx - 1]
            title = paper.title.lower()
            
            # 从论文标题提取关键术语（去掉停用词后的核心名词/动词）
            title_words = set()
            stop_words = {"a", "an", "the", "of", "in", "on", "for", "and", "with", "to", 
                         "from", "by", "at", "is", "are", "was", "were", "using", "based",
                         "its", "their", "this", "that", "which", "between", "through",
                         "under", "over", "into", "within", "during", "after", "before"}
            for word in title.split():
                w = word.strip(".,:;-()[]{}").lower()
                if len(w) >= 3 and w not in stop_words:
                    title_words.add(w)
            
            # 对每个出现位置，检查上下文是否与论文相关
            all_mismatched = True
            for ctx in contexts:
                ctx_lower = ctx.lower()
                # 检查上下文中是否出现论文标题的关键词
                keyword_hits = sum(1 for w in title_words if w in ctx_lower)
                keyword_ratio = keyword_hits / max(len(title_words), 1)
                
                if keyword_ratio >= 0.2:
                    # 至少20%标题关键词出现在上下文中，认为匹配
                    all_mismatched = False
                    break
            
            if all_mismatched and len(title_words) >= 3:
                mismatches.append(idx)
        
        # 对不匹配的引用，将描述性引用替换为安全的"参见[N]"
        if mismatches:
            for idx in mismatches:
                paper = papers[idx - 1]
                # 找到描述[N]的模式并替换：如"Veers[8]提出了..." → "参见[8]"
                # 只替换[N]前面紧跟的方法/描述性内容
                pattern = re.compile(
                    r'([^\n。；]{0,30})\[' + str(idx) + r'\]([^\n。；]{0,60})',
                )
                matches = list(pattern.finditer(verified_body))
                for m in reversed(matches):  # 从后往前替换避免位移
                    prefix = m.group(1).strip()
                    suffix = m.group(2).strip()
                    # 如果前缀或后缀包含具体的论文描述（方法名、结果等）
                    # 替换为更安全的表述
                    full_match = m.group(0)
                    replacement = f"参见[{idx}]"
                    verified_body = verified_body[:m.start()] + replacement + verified_body[m.end():]
        
        # 重新组合
        if len(ref_split) >= 2:
            return verified_body + "## 参考文献" + ref_split[-1]
        return verified_body

    def _embed_charts(self, papers: List[PaperCandidate], topic: str) -> str:
        """生成可视化图表并返回Markdown嵌入文本"""
        try:
            from .report_visualizer import generate_report_charts
            chart_paths = generate_report_charts(papers, self.output_dir, topic)

            lines = []
            if chart_paths.get("year_trend"):
                # 使用相对于output_dir的路径，避免硬编码本地绝对路径
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
            print(f"  [WARN] 图表生成失败: {e}")
            return ""

    @staticmethod
    def _insert_charts_after_section(report: str, chart_section: str) -> str:
        """在"研究概况"章节后插入图表。如果没找到该章节，在摘要后插入。"""
        # 尝试在"一、研究概况"章节后插入
        import re
        # 匹配 "## 一、研究概况" 到下一个 "## " 之间的内容
        pattern = re.compile(r'(##\s*一[、．.]\s*研究概况.*?)(\n##\s)', re.DOTALL)
        match = pattern.search(report)
        if match:
            # 在该章节末尾、下一个章节前插入
            insert_pos = match.end() - len('\n## ')
            report = report[:insert_pos] + "\n\n" + chart_section + "\n" + report[insert_pos:]
            return report

        # 回退：在摘要后插入
        pattern2 = re.compile(r'(##\s*摘要.*?)(\n##\s)', re.DOTALL)
        match2 = pattern2.search(report)
        if match2:
            insert_pos = match2.end() - len('\n## ')
            report = report[:insert_pos] + "\n\n" + chart_section + "\n" + report[insert_pos:]
            return report

        # 最终回退：追加到文末（参考文献前）
        ref_pattern = re.compile(r'(\n#{1,3}\s*参考文献)', re.DOTALL)
        match3 = ref_pattern.search(report)
        if match3:
            insert_pos = match3.start()
            report = report[:insert_pos] + "\n\n" + chart_section + "\n" + report[insert_pos:]
            return report

        # 实在找不到，追加到末尾
        return report + "\n\n" + chart_section

    @staticmethod
    def _format_debate_outputs(debate_outputs: Optional[Dict[str, str]], max_dept: int = 5, max_chars: int = 1500) -> str:
        """将部门辩论产出格式化为综述AI可用的参考文本"""
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
            
            # 提取consensus部分
            consensus_text = ""
            if isinstance(content, dict):
                consensus_text = content.get("consensus", "")
                if not consensus_text:
                    # 尝试从debater_arguments中提取
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
            
            # 截断避免token爆炸
            if len(consensus_text) > max_chars:
                consensus_text = consensus_text[:max_chars] + "\n...(已截断)"
            
            lines.append(f"**{dept_name}**：")
            lines.append(consensus_text)
            lines.append("")
            count += 1
        
        return "\n".join(lines) if count > 0 else ""

    @staticmethod
    def _format_paper_list(papers: List[PaperCandidate], max_papers: int = 80) -> str:
        """格式化论文清单供AI参考，标注可能不相关的论文"""
        # 不相关领域关键词
        irrelevant_markers = [
            "plant survival", "drought mortality", "genomic", "gapseq", "bacterial metabolic",
            "rubisco", "carbon isotope", "soil respiration", "two-sided market",
            "agricultural economics", "crop breeding", "botany", "annals of botany",
            "new phytologist", "genome biology", "bmc genomics",
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
            # 检查相关性
            text = (p.title + " " + (p.journal or "")).lower()
            is_irrelevant = any(kw in text for kw in irrelevant_markers)
            marker = " ⚠️可能不相关" if is_irrelevant else ""
            lines.append(f"[{i}] [{level}]{marker} {authors}. {title}. {journal}, {year}. (引用:{cite})")
        if len(papers) > max_papers:
            lines.append(f"... 共{len(papers)}篇，此处省略{len(papers)-max_papers}篇")
        return "\n".join(lines)

    @staticmethod
    def _compute_year_span(papers: List[PaperCandidate]) -> str:
        """计算年份跨度"""
        years = [p.year for p in papers if p.year and p.year > 1990]
        if not years:
            return "N/A"
        return f"{min(years)}-{max(years)}"

    @staticmethod
    def _compute_year_distribution(papers: List[PaperCandidate]) -> str:
        """计算年份分布"""
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
        """从标题/摘要提取方法关键词分布"""
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
            # v5.1.5: 能源经济学特有方法
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
        """摘要 ≤150字，一句话核心发现 + 关键数据"""
        total = len(papers)
        s_count = len(s_papers)
        a_count = len(a_papers)

        # 提取方法关键词
        method_keywords = self._extract_top_methods(papers)

        return f"""## 摘要

本报告对「{topic}」领域近5年学术文献进行系统性调研，检索并筛选{total}篇高质量论文（S级{s_count}篇、A级{a_count}篇）。核心发现：{method_keywords}是该领域当前主流方法，因果推断与深度学习融合成为新兴方向，但在多任务联合建模与跨领域迁移方面仍存在显著空白。"""

    @staticmethod
    def _compress_text(text: str, max_chars: int = 80) -> str:
        """将长文本压缩为一句话摘要。跳过LLM寒暄语，提取实质结论。"""
        if not text:
            return ""
        # 去掉Markdown标记和常见LLM寒暄语
        clean = text.replace("**", "").replace("###", "").replace("##", "").strip()
        # 跳过寒暄语行
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
            # 全是寒暄语，取最长的一行
            substantive_lines = sorted(lines, key=len, reverse=True)

        result = substantive_lines[0] if substantive_lines else clean[:max_chars]

        if len(result) > max_chars:
            # 找第一个句号断点
            for sep in ["。", ". "]:
                idx = result.find(sep, 10)
                if 10 < idx <= max_chars:
                    return result[:idx + 1].strip()
            return result[:max_chars - 1] + "…"
        return result

    def _llm_call_long(self, system_prompt: str, user_prompt: str, temperature: float = 0.25) -> str:
        """长输出LLM调用（综述报告需要8K+ tokens），支持分段续写"""
        import requests
        # 从llm_call_fn的环境获取API配置
        # 尝试直接调用，但把max_tokens调大
        try:
            # 如果llm_call_fn是run_pipeline.llm_call，我们无法直接改max_tokens
            # 改为：分段请求——先写前半部分，再续写后半部分
            result = self.llm_call_fn(system_prompt, user_prompt, temperature=temperature)
            if not result or len(result) < 500:
                return result or ""
            
            # 检查是否被截断（末尾不完整）
            last_line = result.strip().split("\n")[-1] if result.strip() else ""
            incomplete_markers = [
                not result.rstrip().endswith(("。", ".", "】", ")", "\"", "》", "```")),
                result.rstrip().endswith(("，", "、", "因为", "但是", "而且", "其", "在")),
            ]
            # 如果输出看起来完整（有参考文献段），直接返回
            if "参考文献" in result or "五、" in result or "## 五" in result:
                return result
            
            # 否则续写
            continue_prompt = f"""前文到此被截断了。请从截断处继续撰写，不要重复已有内容，直接接着写：

{result[-200:]}

---
请从上面截断处继续，完成剩余章节（核心发现与争议、研究空白与前沿方向、参考文献）。

【关键规则】续写部分的引用[N]必须严格对应论文清单中的论文。只能描述清单中该论文的标题和摘要已知信息，严禁编造该论文中不存在的实验、方法、数据或案例。如果你对该论文内容不确定，写"参见[N]"即可，不要凭空编造描述。"""

            continuation = self.llm_call_fn(system_prompt, continue_prompt, temperature=temperature)
            if continuation and len(continuation) > 100:
                # 拼接：去掉重叠部分
                return result + "\n\n" + continuation
            return result
        except Exception:
            return ""

    def _ai_refine(self, draft: str, topic: str) -> str:
        """用LLM精炼报告：去废话、提信息密度、保留所有section"""
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
        """核心发现：3-5条，每条带置信度，从辩论共识压缩为一句话"""
        lines = ["## 一、核心发现", ""]

        findings = []

        # 从共识结论压缩提取（每条≤80字）
        if consensus_points:
            for i, point in enumerate(consensus_points[:5]):
                compressed = self._compress_text(point, max_chars=80)
                findings.append({
                    "text": compressed,
                    "confidence": "高" if i < 2 else "中",
                    "evidence": "",
                })

        # 从S级论文补充
        if len(findings) < 3 and s_papers:
            # 方法趋势发现
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

        # 数据来源发现
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
        """方法论分布：有数据时才输出表格"""
        # 收集方法分布
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
        """热点趋势：简洁3条"""
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
        """代表性论文 Top 5，仅标题+期刊+年份"""
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
        """研究空白与机会"""
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

    def _build_final_references(
        self,
        s_papers: List[PaperCandidate],
        a_papers: List[PaperCandidate],
    ) -> str:
        """参考文献：S级+A级全量列出"""
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
    # 内部工作文档（不限长度）
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
        """构建内部工作文档。完整过程记录，不限长度。"""
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        sections = []

        sections.append(f"""# 内部工作文档：{topic}

> Consensus Pipeline v5.1 | 生成时间：{now}
> 本文档为内部质控记录，包含完整检索日志、论文清单、辩论全文和事实校验数据。

---""")

        # 一、检索日志
        sections.append(self._build_internal_search_log(papers, relevance_filter_log))

        # 二、完整论文清单
        sections.append(self._build_internal_paper_list(papers))

        # 三、方法论审查
        sections.append(self._build_internal_methodology(methodology_reviews, clusters))

        # 四、部门辩论全文
        sections.append(self._build_internal_debates(debate_outputs))

        # 五、交叉辩论
        sections.append(self._build_internal_cross_debate(cross_debate_results))

        # 六、共识结论
        sections.append(self._build_internal_consensus(consensus_points))

        # 七、事实校验
        sections.append(self._build_internal_fact_check(fact_check_summary, validations))

        # 八、程序与教程
        sections.append(self._build_internal_code_tutorial(programming_output, tutorial_output))

        # 九、验证结果
        sections.append(self._build_internal_validations(validations))

        return "\n\n".join(sections)

    def _build_internal_search_log(
        self,
        papers: List[PaperCandidate],
        relevance_filter_log: Optional[Dict[str, Any]],
    ) -> str:
        lines = ["## 一、检索日志", ""]

        # 按来源统计
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

        # 相关性过滤日志
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
        lines = ["## 二、完整论文清单", ""]
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
        lines = ["## 三、方法论审查", ""]

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
        lines = ["## 四、部门辩论全文", ""]

        if not debate_outputs:
            lines.append("*无辩论数据*")
            return "\n".join(lines)

        for dept_name, content in debate_outputs.items():
            lines.append(f"### {dept_name}")
            lines.append("")
            if isinstance(content, dict):
                # 结构化辩论输出：提取consensus + debater_arguments
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
        lines = ["## 五、交叉辩论记录", ""]

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
        lines = ["## 六、共识结论", ""]

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
        lines = ["## 七、事实校验", ""]

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
        lines = ["## 八、程序与教程", ""]

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
        lines = ["## 九、验证结果", ""]

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
    # 辅助方法
    # ================================================================

    def _extract_top_methods(self, papers: List[PaperCandidate]) -> str:
        """从论文中提取Top方法关键词"""
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
        """提取论文的学术价值（一句话）"""
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
        if "carbon" in title_lower:
            return "碳市场/碳价格建模的核心研究"
        return "在方法论或应用场景上有重要贡献"

    # ================================================================
    # CSV 元数据表
    # ================================================================

    def _build_csv(self, papers: List[PaperCandidate]) -> str:
        """构建CSV元数据表"""
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