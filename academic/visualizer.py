"""
学术可视化 — Consensus Pipeline v4.0

生成4张核心图表：研究趋势时间线、方法论分布饼图、关键突破时间轴、引用网络演化图
"""
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .search_engine import PaperCandidate
from .cross_validator import ClusterResult


@dataclass
class ChartConfig:
    """图表配置"""
    chart_type: str = ""       # line / pie / timeline / network
    title: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    file_path: str = ""        # 输出文件路径


class AcademicVisualizer:
    """
    学术可视化

    生成4张核心图表（ChartConfig格式），供报告整合组使用。
    实际渲染在 report_generator.py 中完成。
    """

    def __init__(self, output_dir: str = "./output/charts"):
        self.output_dir = output_dir

    def generate_all(
        self,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
    ) -> List[ChartConfig]:
        """
        生成全部4张图表配置。

        Args:
            papers: 候选论文列表
            clusters: 聚类结果

        Returns:
            4个 ChartConfig 对象
        """
        charts = [
            self._research_trend_timeline(papers),
            self._methodology_distribution(papers, clusters),
            self._key_breakthrough_timeline(papers),
            self._citation_network_evolution(papers),
        ]
        return charts

    def _research_trend_timeline(self, papers: List[PaperCandidate]) -> ChartConfig:
        """图表1：研究趋势时间线（按年份论文数量+引用量）"""
        from collections import Counter

        year_counts = Counter()
        year_citations = Counter()

        for p in papers:
            if p.year > 0:
                year_counts[p.year] += 1
                year_citations[p.year] += p.citation_count

        years = sorted(year_counts.keys())
        data = {
            "years": years,
            "paper_counts": [year_counts[y] for y in years],
            "citation_sums": [year_citations[y] for y in years],
        }

        return ChartConfig(
            chart_type="line",
            title="研究趋势时间线",
            data=data,
            file_path=os.path.join(self.output_dir, "research_trend.json"),
        )

    def _methodology_distribution(
        self, papers: List[PaperCandidate], clusters: List[ClusterResult]
    ) -> ChartConfig:
        """图表2：方法论分布饼图"""
        # 从聚类结果中找methodology维度
        methodology_cluster = None
        for c in clusters:
            if c.dimension == "methodology":
                methodology_cluster = c
                break

        if methodology_cluster:
            data = methodology_cluster.distribution
        else:
            # 回退：从论文标题简单统计
            data = self._estimate_methodology_from_titles(papers)

        return ChartConfig(
            chart_type="pie",
            title="方法论分布",
            data=data,
            file_path=os.path.join(self.output_dir, "methodology_distribution.json"),
        )

    def _key_breakthrough_timeline(self, papers: List[PaperCandidate]) -> ChartConfig:
        """图表3：关键突破时间轴（高被引论文）"""
        # 按引用量排序，取前10
        top_papers = sorted(papers, key=lambda p: p.citation_count, reverse=True)[:10]

        events = []
        for p in top_papers:
            events.append({
                "year": p.year,
                "title": p.title[:80],
                "citations": p.citation_count,
                "journal": p.journal,
                "quality_level": p.quality_level,
            })

        return ChartConfig(
            chart_type="timeline",
            title="关键突破时间轴",
            data={"events": events},
            file_path=os.path.join(self.output_dir, "breakthrough_timeline.json"),
        )

    def _citation_network_evolution(self, papers: List[PaperCandidate]) -> ChartConfig:
        """图表4：引用网络演化（按年份-引用量的气泡图）"""
        nodes = []
        for p in papers:
            if p.year > 0:
                nodes.append({
                    "id": p.doi or p.title[:30],
                    "title": p.title[:60],
                    "year": p.year,
                    "citations": p.citation_count,
                    "journal": p.journal,
                    "quality_level": p.quality_level,
                })

        return ChartConfig(
            chart_type="bubble",
            title="引用网络演化",
            data={"nodes": nodes},
            file_path=os.path.join(self.output_dir, "citation_evolution.json"),
        )

    def _estimate_methodology_from_titles(self, papers: List[PaperCandidate]) -> Dict[str, int]:
        """从论文标题估计方法论分布"""
        categories = {
            "计量经济学": 0,
            "机器学习": 0,
            "混合方法": 0,
            "优化模型": 0,
            "其他": 0,
        }

        for p in papers:
            text = f"{p.title} {p.abstract}".lower()
            if any(kw in text for kw in ["econometric", "panel", "regression", "计量", "面板"]):
                categories["计量经济学"] += 1
            elif any(kw in text for kw in ["machine learning", "neural", "deep", "机器学习"]):
                categories["机器学习"] += 1
            elif any(kw in text for kw in ["hybrid", "ensemble", "混合"]):
                categories["混合方法"] += 1
            elif any(kw in text for kw in ["optimization", "programming", "优化"]):
                categories["优化模型"] += 1
            else:
                categories["其他"] += 1

        return {k: v for k, v in categories.items() if v > 0}
