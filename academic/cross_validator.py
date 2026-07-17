"""
Cross-Validation + Topic Clustering — Consensus Pipeline v4.0

Performs cross-validation on search results and 9-dimension topic clustering.
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict

from .search_engine import PaperCandidate


# ============ 9-Dimension Clustering ============

CLUSTERING_DIMENSIONS = [
    "research_area",      # Research area
    "methodology",        # Methodology
    "data_type",          # Data type
    "geographic_scope",   # Geographic scope
    "temporal_focus",     # Temporal focus
    "research_design",    # Research design
    "core_finding",       # Core finding
    "policy_implication", # Policy implication
    "tech_approach",      # Technical approach
]


@dataclass
class ClusterResult:
    """Clustering result"""
    dimension: str = ""
    clusters: Dict[str, List[str]] = field(default_factory=dict)  # cluster_name -> [paper_titles]
    distribution: Dict[str, int] = field(default_factory=dict)    # cluster_name -> count

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "clusters": self.clusters,
            "distribution": self.distribution,
        }


@dataclass
class ValidationResult:
    """Cross-validation result"""
    paper_title: str = ""
    doi: str = ""
    cross_source_count: int = 0      # Number of sources that found this paper
    consistency_score: float = 0.0   # Multi-source consistency score
    sources: List[str] = field(default_factory=list)
    notes: str = ""


class CrossValidator:
    """
    Cross-Validation + Topic Clustering

    1. Cross-validation: check if the same paper appears across multiple search sources
    2. Topic clustering: classify papers along 9 dimensions
    """

    def __init__(self, llm_call_fn=None):
        self.llm_call_fn = llm_call_fn

    def validate(self, papers: List[PaperCandidate]) -> List[ValidationResult]:
        """
        Cross-validation: the more sources a paper appears in, the higher its credibility.

        Args:
            papers: Candidate paper list (deduplicated but with source info preserved)

        Returns:
            List of validation results
        """
        results = []

        # Group by DOI or title
        doi_groups = defaultdict(list)
        title_groups = defaultdict(list)

        for paper in papers:
            if paper.doi:
                doi_groups[paper.doi].append(paper)
            title_key = paper.title.lower()[:50].strip()
            title_groups[title_key].append(paper)

        # Calculate cross-validation score for each unique paper
        seen = set()
        for paper in papers:
            key = paper.doi or paper.title.lower()[:50].strip()
            if key in seen:
                continue
            seen.add(key)

            # Find all source records for the same paper
            if paper.doi:
                group = doi_groups.get(paper.doi, [paper])
            else:
                title_key = paper.title.lower()[:50].strip()
                group = title_groups.get(title_key, [paper])

            sources = set()
            for p in group:
                if "+" in p.source:
                    for s in p.source.split("+"):
                        sources.add(s)
                else:
                    sources.add(p.source)

            cross_count = len(sources)
            consistency = min(1.0, cross_count / 3.0)  # Found in all 3 sources = 1.0

            results.append(ValidationResult(
                paper_title=paper.title,
                doi=paper.doi,
                cross_source_count=cross_count,
                consistency_score=consistency,
                sources=list(sources),
                notes=f"Found in {cross_count} sources" if cross_count > 1 else "Found in only 1 source",
            ))

        return results

    def cluster(
        self,
        papers: List[PaperCandidate],
        dimensions: Optional[List[str]] = None,
    ) -> List[ClusterResult]:
        """
        9-dimension topic clustering.

        Args:
            papers: Candidate paper list
            dimensions: Dimensions to use, defaults to all 9

        Returns:
            List of clustering results
        """
        dimensions = dimensions or CLUSTERING_DIMENSIONS
        results = []

        if self.llm_call_fn:
            results = self._cluster_with_llm(papers, dimensions)
        else:
            results = self._cluster_rule_based(papers, dimensions)

        return results

    def _cluster_rule_based(
        self,
        papers: List[PaperCandidate],
        dimensions: List[str],
    ) -> List[ClusterResult]:
        """Rule-based clustering (keyword matching)"""
        results = []

        for dim in dimensions:
            clusters = defaultdict(list)

            for paper in papers:
                category = self._categorize_by_dimension(dim, paper)
                clusters[category].append(paper.title[:50])

            distribution = {k: len(v) for k, v in clusters.items()}
            results.append(ClusterResult(
                dimension=dim,
                clusters=dict(clusters),
                distribution=distribution,
            ))

        return results

    def _categorize_by_dimension(self, dimension: str, paper: PaperCandidate) -> str:
        """Categorize a paper by the given dimension"""
        text = f"{paper.title} {paper.abstract}".lower()

        category_map = {
            "research_area": {
                "Carbon Pricing/Market": ["carbon price", "carbon market", "emission trading", "碳价", "碳市场"],
                "Energy Efficiency": ["energy efficiency", "能源效率", "节能"],
                "Renewable Energy": ["renewable", "solar", "wind", "可再生", "光伏", "风电"],
                "Energy Policy": ["energy policy", "能源政策", "政策评估"],
                "Other": [],
            },
            "methodology": {
                "Econometrics": ["econometric", "panel", "regression", "iv", "did", "计量", "面板", "回归"],
                "Machine Learning": ["machine learning", "deep learning", "neural", "lstm", "机器学习", "深度学习"],
                "Hybrid Methods": ["hybrid", "ensemble", "混合", "组合"],
                "Optimization": ["optimization", "linear programming", "优化", "规划"],
                "Other": [],
            },
            "data_type": {
                "Panel Data": ["panel data", "面板数据"],
                "Time Series": ["time series", "时间序列", "序列"],
                "Cross-Section": ["cross-section", "截面"],
                "Text Data": ["text", "nlp", "文本", "自然语言"],
                "Other": [],
            },
            "geographic_scope": {
                "China": ["china", "chinese", "中国"],
                "Global": ["global", "worldwide", "全球"],
                "Europe": ["europe", "eu", "欧洲"],
                "United States": ["united states", "usa", "美国"],
                "Other": [],
            },
        }

        if dimension in category_map:
            for category, keywords in category_map.items():
                if category == "Other":
                    continue
                if any(kw in text for kw in keywords):
                    return category
            return "Other"

        # Dimensions without rules default to "Uncategorized"
        return "Uncategorized"

    def _cluster_with_llm(
        self,
        papers: List[PaperCandidate],
        dimensions: List[str],
    ) -> List[ClusterResult]:
        """LLM-based clustering"""
        paper_list = [{"title": p.title, "journal": p.journal, "year": p.year} for p in papers]

        system_prompt = f"""You are an academic paper classification expert. Cluster the following papers across {len(dimensions)} dimensions.

Dimension list: {json.dumps(dimensions, ensure_ascii=False)}

Output JSON-formatted clustering results:
[
  {{
    "dimension": "dimension_name",
    "clusters": {{
      "category1": ["paper_title1", "paper_title2"],
      "category2": ["paper_title3"]
    }}
  }}
]"""

        user_msg = f"Paper list:\n{json.dumps(paper_list, ensure_ascii=False, indent=2)}"
        response = self.llm_call_fn(system_prompt, user_msg)

        try:
            parsed = json.loads(response)
            results = []
            for item in parsed:
                clusters = item.get("clusters", {})
                distribution = {k: len(v) for k, v in clusters.items()}
                results.append(ClusterResult(
                    dimension=item.get("dimension", ""),
                    clusters=clusters,
                    distribution=distribution,
                ))
            return results
        except json.JSONDecodeError:
            # Fallback to rule-based clustering
            return self._cluster_rule_based(papers, dimensions)
