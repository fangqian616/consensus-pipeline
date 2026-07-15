"""
报告生成器 — Consensus Pipeline v4.0

将所有部门的输出整合为最终的组会汇报PDF/Markdown。
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .search_engine import PaperCandidate
from .cross_validator import ClusterResult, ValidationResult
from .visualizer import ChartConfig


class ReportGenerator:
    """
    报告整合组

    将各部门输出整合为：
    - 组会汇报 Markdown
    - 论文元数据表 CSV
    - 图表数据（独立JSON，供可视化使用）
    """

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir

    def generate(
        self,
        topic: str,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
        validations: List[ValidationResult],
        charts: List[ChartConfig],
        consensus_points: Optional[List[str]] = None,
        fact_check_summary: str = "",
    ) -> Dict[str, str]:
        """
        生成完整报告。

        Args:
            topic: 研究主题
            papers: 候选论文列表
            clusters: 聚类结果
            validations: 验证结果
            charts: 图表配置
            consensus_points: 共识结论
            fact_check_summary: 事实校验摘要

        Returns:
            {"markdown": "报告内容", "csv": "元数据CSV", "charts_dir": "图表目录"}
        """
        os.makedirs(self.output_dir, exist_ok=True)

        # 1. 生成 Markdown 报告
        md_content = self._build_markdown(
            topic, papers, clusters, validations, charts,
            consensus_points, fact_check_summary,
        )

        md_path = os.path.join(self.output_dir, "report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 2. 生成 CSV 元数据表
        csv_content = self._build_csv(papers)
        csv_path = os.path.join(self.output_dir, "papers_metadata.csv")
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(csv_content)

        # 3. 保存图表数据
        charts_dir = os.path.join(self.output_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        for chart in charts:
            if chart.data:
                chart_path = os.path.join(charts_dir, os.path.basename(chart.file_path))
                with open(chart_path, "w", encoding="utf-8") as f:
                    json.dump(chart.data, f, ensure_ascii=False, indent=2)

        return {
            "markdown": md_path,
            "csv": csv_path,
            "charts_dir": charts_dir,
        }

    def _build_markdown(
        self,
        topic: str,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
        validations: List[ValidationResult],
        charts: List[ChartConfig],
        consensus_points: Optional[List[str]],
        fact_check_summary: str,
    ) -> str:
        """构建 Markdown 报告"""
        now = datetime.now().strftime("%Y年%m月%d日")

        # 统计
        s_count = sum(1 for p in papers if p.quality_level == "S")
        a_count = sum(1 for p in papers if p.quality_level == "A")
        b_count = sum(1 for p in papers if p.quality_level == "B")

        sections = []

        # 标题页
        sections.append(f"""# {topic}

> 学术动向调研报告 | Consensus Pipeline v4.0
> 生成日期：{now}

---""")

        # 摘要
        sections.append(f"""## 一、摘要

本报告对「{topic}」领域的学术论文动向进行了系统性调研。共检索并筛选 **{len(papers)}** 篇高质量文献（S级{s_count}篇、A级{a_count}篇、B级{b_count}篇），覆盖近5年主要研究进展。

{"**事实校验**：" + fact_check_summary if fact_check_summary else ""}""")

        # 领域概览
        sections.append(f"""## 二、领域概览

### 检索范围
- 检索源：arXiv / Semantic Scholar / OpenAlex
- 期刊质量：CSSCI及以上（S级为主、A级辅助、B级代表性1-2篇）
- 论文总数：{len(papers)}篇

### 质量分布

| 等级 | 数量 | 说明 |
|------|------|------|
| S级 | {s_count} | SCI/SSCI Q1顶刊，主力来源 |
| A级 | {a_count} | 高质量辅助来源 |
| B级 | {b_count} | 代表性文献 |""")

        # 方法论综述（从聚类结果中提取）
        methodology_section = self._build_methodology_section(clusters, papers)
        sections.append(methodology_section)

        # 核心发现
        findings_section = self._build_findings_section(papers, consensus_points)
        sections.append(findings_section)

        # 争议与前沿
        debate_section = self._build_debate_section(papers, consensus_points)
        sections.append(debate_section)

        # 研究建议
        suggestions = self._build_suggestions_section(papers, clusters)
        sections.append(suggestions)

        # 参考文献
        ref_section = self._build_references_section(papers)
        sections.append(ref_section)

        return "\n\n".join(sections)

    def _build_methodology_section(
        self, clusters: List[ClusterResult], papers: List[PaperCandidate]
    ) -> str:
        """构建方法论综述"""
        lines = ["## 三、方法论综述", ""]

        # 找methodology聚类
        meth_cluster = None
        for c in clusters:
            if c.dimension == "methodology":
                meth_cluster = c
                break

        if meth_cluster and meth_cluster.distribution:
            lines.append("### 方法论分布")
            lines.append("")
            lines.append("| 方法类别 | 论文数量 | 占比 |")
            lines.append("|---------|---------|------|")
            total = sum(meth_cluster.distribution.values())
            for cat, count in sorted(meth_cluster.distribution.items(), key=lambda x: -x[1]):
                pct = f"{count/total*100:.1f}%" if total > 0 else "0%"
                lines.append(f"| {cat} | {count} | {pct} |")
            lines.append("")

        # 高被引论文方法论
        top_papers = sorted(papers, key=lambda p: p.citation_count, reverse=True)[:5]
        if top_papers:
            lines.append("### 高被引论文方法论特征")
            lines.append("")
            for p in top_papers:
                lines.append(f"- **{p.title[:80]}** ({p.journal}, {p.year}, 被引{p.citation_count}次)")
            lines.append("")

        return "\n".join(lines)

    def _build_findings_section(
        self, papers: List[PaperCandidate], consensus_points: Optional[List[str]]
    ) -> str:
        """构建核心发现"""
        lines = ["## 四、核心发现", ""]

        if consensus_points:
            lines.append("### 共识性结论")
            lines.append("")
            for i, point in enumerate(consensus_points, 1):
                lines.append(f"{i}. {point}")
            lines.append("")

        # S级论文的关键发现
        s_papers = [p for p in papers if p.quality_level == "S"]
        if s_papers:
            lines.append("### S级论文重点")
            lines.append("")
            for p in s_papers[:10]:
                lines.append(f"- **{p.title[:80]}**")
                if p.abstract:
                    lines.append(f"  > {p.abstract[:200]}...")
                lines.append(f"  *{p.journal}* ({p.year}), 被引{p.citation_count}次")
                lines.append("")

        return "\n".join(lines)

    def _build_debate_section(
        self, papers: List[PaperCandidate], consensus_points: Optional[List[str]]
    ) -> str:
        """构建争议与前沿"""
        lines = ["## 五、争议与前沿", ""]

        # B级和A级论文常含有争议性观点
        ab_papers = [p for p in papers if p.quality_level in ["A", "B"]]
        if ab_papers:
            lines.append("### 补充视角")
            lines.append("")
            for p in ab_papers[:5]:
                lines.append(f"- **{p.title[:80]}** (*{p.journal}*, {p.year})")
            lines.append("")

        lines.append("### 待解决的开放问题")
        lines.append("")
        lines.append("（此部分需要基于辩论环节的分歧点填充）")
        lines.append("")

        return "\n".join(lines)

    def _build_suggestions_section(
        self, papers: List[PaperCandidate], clusters: List[ClusterResult]
    ) -> str:
        """构建研究建议"""
        lines = ["## 六、研究建议", ""]

        lines.append("### 基于文献趋势的建议")
        lines.append("")

        # 从趋势中提取建议
        if papers:
            recent = [p for p in papers if p.year >= 2024]
            lines.append(f"1. 近2年有 **{len(recent)}** 篇高质量论文发表，表明该领域活跃度高")
            lines.append("2. 建议关注方法论交叉融合趋势（计量+ML混合方法）")
            lines.append("3. 重点关注S级期刊的最新特刊和征稿方向")
        lines.append("")

        return "\n".join(lines)

    def _build_references_section(self, papers: List[PaperCandidate]) -> str:
        """构建参考文献"""
        lines = ["## 七、参考文献", ""]

        # 按等级+引用量排序
        level_order = {"S": 0, "A": 1, "B": 2}
        sorted_papers = sorted(
            papers,
            key=lambda p: (level_order.get(p.quality_level, 5), -p.citation_count),
        )

        for i, p in enumerate(sorted_papers, 1):
            authors_str = ", ".join(p.authors[:3])
            if len(p.authors) > 3:
                authors_str += " et al."
            doi_str = f" DOI: {p.doi}" if p.doi else ""
            lines.append(f"[{i}] {authors_str}. {p.title}. *{p.journal}*, {p.year}.{doi_str}")

        return "\n".join(lines)

    def _build_csv(self, papers: List[PaperCandidate]) -> str:
        """构建CSV元数据表"""
        lines = ["title,doi,authors,journal,year,citation_count,quality_level,source"]

        for p in papers:
            authors_str = "; ".join(p.authors[:5]).replace(",", " ")
            title_clean = p.title.replace(",", " ").replace('"', "'")
            doi = p.doi or "N/A"
            journal_clean = p.journal.replace(",", " ")
            lines.append(
                f'"{title_clean}","{doi}","{authors_str}","{journal_clean}",'
                f'{p.year},{p.citation_count},{p.quality_level},{p.source}'
            )

        return "\n".join(lines)
