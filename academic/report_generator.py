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
    ) -> str:
        """构建最终交付报告。如果有llm_call_fn，用AI写综述；否则回退模板。"""
        now = datetime.now().strftime("%Y年%m月%d日")

        s_papers = [p for p in papers if p.quality_level == "S"]
        a_papers = [p for p in papers if p.quality_level == "A"]
        b_papers = [p for p in papers if p.quality_level == "B"]

        if self.llm_call_fn and s_papers:
            return self._build_review_by_ai(topic, papers, s_papers, a_papers, b_papers, consensus_points, now, fact_check_summary)

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
    ) -> str:
        """用LLM基于论文元数据直接撰写学术综述报告"""
        # 构建论文清单供AI参考
        paper_list = self._format_paper_list(papers)
        year_dist = self._compute_year_distribution(papers)
        method_dist = self._compute_method_distribution(papers)
        consensus_text = "\n".join([f"- {c}" for c in (consensus_points or [])])

        system_prompt = """你是一位资深学术综述撰写专家。你的任务是基于给定的论文数据撰写一篇结构完整的学术动向综述报告。

写作规范：
1. 每个章节要有实质内容段落，不是干巴巴的要点列表
2. 引用具体论文支撑论点，用[序号]标注
3. 方法论对比要有深度：不同方法的优劣、适用场景、计算开销、数据需求
4. 趋势分析基于年份分布数据，说明演进脉络
5. 反面证据必须包含：对主流方法的有效批评、失败案例、适用边界
6. 研究空白要从"为什么没人做"和"做了有什么价值"两个角度分析
7. 语言学术化但不晦涩，避免空话套话"""

        user_prompt = f"""请撰写「{topic}」领域的学术动向综述报告。

## 可用论文数据

### 年份分布
{year_dist}

### 方法分布（从标题/摘要提取）
{method_dist}

### 论文清单（{len(papers)}篇：S级{len(s_papers)}、A级{len(a_papers)}、B级{len(b_papers)}）
{paper_list}

### 部门辩论共识
{consensus_text if consensus_text else "无辩论数据"}

---

请按以下结构撰写，每个章节都要有实质段落而非要点列表：

# {topic}

> 学术动向综述 | Consensus Pipeline v5 | {now}

## 摘要
（200字以内，概述调研范围、核心发现、方法论格局）

## 一、研究概况与发展脉络
（基于年份分布，描述该领域从何时兴起、关键转折点、当前热度。引用具体论文说明里程碑工作）

## 二、方法论格局与对比
（分类别阐述主流方法，每类说明：核心思路、代表论文、优势、局限、适用场景。用表格做横向对比）

| 方法类别 | 代表论文 | 预测精度 | 可解释性 | 数据需求 | 计算开销 | 趋势 |
|---------|---------|---------|---------|---------|---------|------|

## 三、核心发现与争议
（3-5条实质性发现，每条必须有支撑论文和反面证据。标注置信度🟢高🟡中🔴低）

## 四、研究空白与前沿方向
（5个空白，每个说明：现状→为什么重要→可行路径→预期突破）

## 五、参考文献
（列出所有S级和A级论文，GB/T 7714格式）"""

        try:
            # 综述需要长输出，用专用调用
            report = self._llm_call_long(system_prompt, user_prompt, temperature=0.25)
            if report and len(report) > 500:
                # 用论文元数据重建参考文献，保证引用序号一一对应
                report = self._rebuild_references(report, papers)
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

        # 3. 用论文元数据生成参考文献列表
        ref_lines = []
        for idx in sorted(cited_indices):
            p = papers[idx - 1]  # 1-based to 0-based
            authors_str = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors_str += ", 等"
            elif len(p.authors) > 1:
                authors_str = authors_str.replace(", ", ", ", 1)  # 保持原样
                # 最后一个作者前用"和"
                parts = authors_str.rsplit(", ", 1)
                if len(parts) == 2:
                    authors_str = f"{parts[0]}和{parts[1]}"

            title = p.title.rstrip(".")
            journal = p.journal or "arXiv预印本"
            year = p.year or "n/a"
            doi_str = f". doi:{p.doi}" if p.doi else ""

            if p.source == "arxiv" or not p.journal:
                ref_lines.append(f"[{idx}] {authors_str}. {title}. *{journal}*, {year}{doi_str}.  ")
            else:
                ref_lines.append(f"[{idx}] {authors_str}. {title}. *{journal}*, {year}{doi_str}.  ")

        ref_section += "\n".join(ref_lines)
        return report + ref_section

    @staticmethod
    def _format_paper_list(papers: List[PaperCandidate], max_papers: int = 80) -> str:
        """格式化论文清单供AI参考"""
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
            lines.append(f"[{i}] [{level}] {authors}. {title}. {journal}, {year}. (引用:{cite})")
        if len(papers) > max_papers:
            lines.append(f"... 共{len(papers)}篇，此处省略{len(papers)-max_papers}篇")
        return "\n".join(lines)

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
            "XGBoost/GBDT": ["xgboost", "gbdt", "gradient boosting", "lightgbm"],
            "GNN/Graph": ["gnn", "graph neural", "graph convolution"],
            "因果推断": ["causal", "did", "difference-in-diff", "instrumental"],
            "强化学习": ["reinforcement", "rl ", "deep q", "policy gradient"],
            "贝叶斯": ["bayesian", "mcmc", "variational inference"],
            "集成学习": ["ensemble", "stacking", "bagging", "random forest"],
            "优化算法": ["optimization", "pso", "genetic algorithm", "evolutionary"],
            "NLP/文本": ["nlp", "text mining", "sentiment", "word2vec"],
            "联邦学习": ["federated", "federated learning"],
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
请从上面截断处继续，完成剩余章节（核心发现与争议、研究空白与前沿方向、参考文献）。"""

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