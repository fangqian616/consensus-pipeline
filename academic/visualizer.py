"""
Academic Visualization — Consensus Pipeline v4.0

Generates 4 core charts: research trend timeline, methodology distribution pie chart,
key breakthrough timeline, citation network evolution chart
"""
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .search_engine import PaperCandidate
from .cross_validator import ClusterResult


@dataclass
class ChartConfig:
    """Chart configuration"""
    chart_type: str = ""       # line / pie / timeline / network
    title: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    file_path: str = ""        # output file path


class AcademicVisualizer:
    """
    Academic Visualization

    Generates 4 core charts (ChartConfig format) for use by the report integration team.
    Actual rendering is done in report_generator.py.
    """

    def __init__(self, output_dir: str = "./output/charts"):
        self.output_dir = output_dir

    def generate_all(
        self,
        papers: List[PaperCandidate],
        clusters: List[ClusterResult],
    ) -> List[ChartConfig]:
        """
        Generate all 4 chart configurations.

        Args:
            papers: List of candidate papers
            clusters: Clustering results

        Returns:
            4 ChartConfig objects
        """
        charts = [
            self._research_trend_timeline(papers),
            self._methodology_distribution(papers, clusters),
            self._key_breakthrough_timeline(papers),
            self._citation_network_evolution(papers),
        ]
        return charts

    def _research_trend_timeline(self, papers: List[PaperCandidate]) -> ChartConfig:
        """Chart 1: Research Trend Timeline (paper count + citations by year)"""
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
            title="Research Trend Timeline",
            data=data,
            file_path=os.path.join(self.output_dir, "research_trend.json"),
        )

    def _methodology_distribution(
        self, papers: List[PaperCandidate], clusters: List[ClusterResult]
    ) -> ChartConfig:
        """Chart 2: Methodology Distribution Pie Chart"""
        # Find methodology dimension from clustering results
        methodology_cluster = None
        for c in clusters:
            if c.dimension == "methodology":
                methodology_cluster = c
                break

        if methodology_cluster:
            data = methodology_cluster.distribution
        else:
            # Fallback: simple statistics from paper titles
            data = self._estimate_methodology_from_titles(papers)

        return ChartConfig(
            chart_type="pie",
            title="Methodology Distribution",
            data=data,
            file_path=os.path.join(self.output_dir, "methodology_distribution.json"),
        )

    def _key_breakthrough_timeline(self, papers: List[PaperCandidate]) -> ChartConfig:
        """Chart 3: Key Breakthrough Timeline (highly-cited papers)"""
        # Sort by citation count, take top 10
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
            title="Key Breakthrough Timeline",
            data={"events": events},
            file_path=os.path.join(self.output_dir, "breakthrough_timeline.json"),
        )

    def _citation_network_evolution(self, papers: List[PaperCandidate]) -> ChartConfig:
        """Chart 4: Citation Network Evolution (year-citation bubble chart)"""
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
            title="Citation Network Evolution",
            data={"nodes": nodes},
            file_path=os.path.join(self.output_dir, "citation_evolution.json"),
        )

    def _estimate_methodology_from_titles(self, papers: List[PaperCandidate]) -> Dict[str, int]:
        """Estimate methodology distribution from paper titles"""
        categories = {
            "Econometrics": 0,
            "Machine Learning": 0,
            "Hybrid Methods": 0,
            "Optimization": 0,
            "Other": 0,
        }

        for p in papers:
            text = f"{p.title} {p.abstract}".lower()
            if any(kw in text for kw in ["econometric", "panel", "regression", "计量", "面板"]):  # "计量"/"面板" = Chinese terms for econometric/panel
                categories["Econometrics"] += 1
            elif any(kw in text for kw in ["machine learning", "neural", "deep", "Machine Learning"]):
                categories["Machine Learning"] += 1
            elif any(kw in text for kw in ["hybrid", "ensemble", "混合"]):  # "混合" = Chinese for hybrid
                categories["Hybrid Methods"] += 1
            elif any(kw in text for kw in ["optimization", "programming", "优化"]):  # "优化" = Chinese for optimization
                categories["Optimization"] += 1
            else:
                categories["Other"] += 1

        return {k: v for k, v in categories.items() if v > 0}
