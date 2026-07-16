"""
交叉验证+主题聚类 — Consensus Pipeline v4.0

对检索结果进行交叉验证和9维度主题聚类。
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from collections import Counter, defaultdict

from .search_engine import PaperCandidate


# ============ 9维度聚类 ============

CLUSTERING_DIMENSIONS = [
    "research_area",      # 研究领域
    "methodology",        # 方法论
    "data_type",          # 数据类型
    "geographic_scope",   # 地理范围
    "temporal_focus",     # 时间特征
    "research_design",    # 研究设计
    "core_finding",       # 核心发现
    "policy_implication", # 政策含义
    "tech_approach",      # 技术路线
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
    """交叉验证结果"""
    paper_title: str = ""
    doi: str = ""
    cross_source_count: int = 0      # 被几个检索源找到
    consistency_score: float = 0.0   # 多源一致性分数
    sources: List[str] = field(default_factory=list)
    notes: str = ""


class CrossValidator:
    """
    交叉验证 + 主题聚类

    1. 交叉验证：检查同一论文在多个检索源中出现的情况
    2. 主题聚类：按9维度对论文进行分类
    """

    def __init__(self, llm_call_fn=None):
        self.llm_call_fn = llm_call_fn

    def validate(self, papers: List[PaperCandidate]) -> List[ValidationResult]:
        """
        交叉验证：多源出现次数越多，可信度越高。

        Args:
            papers: 候选论文列表（已去重但记录了来源）

        Returns:
            验证结果列表
        """
        results = []

        # 按DOI或标题分组
        doi_groups = defaultdict(list)
        title_groups = defaultdict(list)

        for paper in papers:
            if paper.doi:
                doi_groups[paper.doi].append(paper)
            title_key = paper.title.lower()[:50].strip()
            title_groups[title_key].append(paper)

        # 对每个唯一论文计算交叉验证分数
        seen = set()
        for paper in papers:
            key = paper.doi or paper.title.lower()[:50].strip()
            if key in seen:
                continue
            seen.add(key)

            # 找到同一论文的所有来源记录
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
            consistency = min(1.0, cross_count / 3.0)  # 3个源全找到 = 1.0

            results.append(ValidationResult(
                paper_title=paper.title,
                doi=paper.doi,
                cross_source_count=cross_count,
                consistency_score=consistency,
                sources=list(sources),
                notes=f"在{cross_count}个检索源中被发现" if cross_count > 1 else "仅在1个检索源中发现",
            ))

        return results

    def cluster(
        self,
        papers: List[PaperCandidate],
        dimensions: Optional[List[str]] = None,
    ) -> List[ClusterResult]:
        """
        9维度主题聚类。

        Args:
            papers: 候选论文列表
            dimensions: 使用的维度列表，默认全部9维度

        Returns:
            聚类结果列表
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
        """基于规则的聚类（关键词匹配）"""
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
        """按维度归类论文"""
        text = f"{paper.title} {paper.abstract}".lower()

        category_map = {
            "research_area": {
                "碳价/碳市场": ["carbon price", "carbon market", "emission trading", "碳价", "碳市场"],
                "能源效率": ["energy efficiency", "能源效率", "节能"],
                "可再生能源": ["renewable", "solar", "wind", "可再生", "光伏", "风电"],
                "能源政策": ["energy policy", "能源政策", "政策评估"],
                "其他": [],
            },
            "methodology": {
                "计量经济学": ["econometric", "panel", "regression", "iv", "did", "计量", "面板", "回归"],
                "机器学习": ["machine learning", "deep learning", "neural", "lstm", "机器学习", "深度学习"],
                "混合方法": ["hybrid", "ensemble", "混合", "组合"],
                "优化模型": ["optimization", "linear programming", "优化", "规划"],
                "其他": [],
            },
            "data_type": {
                "面板数据": ["panel data", "面板数据"],
                "时间序列": ["time series", "时间序列", "序列"],
                "截面数据": ["cross-section", "截面"],
                "文本数据": ["text", "nlp", "文本", "自然语言"],
                "其他": [],
            },
            "geographic_scope": {
                "中国": ["china", "chinese", "中国"],
                "全球": ["global", "worldwide", "全球"],
                "欧洲": ["europe", "eu", "欧洲"],
                "美国": ["united states", "usa", "美国"],
                "其他": [],
            },
        }

        if dimension in category_map:
            for category, keywords in category_map[dimension].items():
                if category == "其他":
                    continue
                if any(kw in text for kw in keywords):
                    return category
            return "其他"

        # 没有规则的维度，返回"未分类"
        return "未分类"

    def _cluster_with_llm(
        self,
        papers: List[PaperCandidate],
        dimensions: List[str],
    ) -> List[ClusterResult]:
        """使用LLM进行聚类"""
        paper_list = [{"title": p.title, "journal": p.journal, "year": p.year} for p in papers]

        system_prompt = f"""你是学术论文分类专家。对以下论文按{len(dimensions)}个维度进行聚类。

维度列表：{json.dumps(dimensions, ensure_ascii=False)}

请输出JSON格式的聚类结果：
[
  {{
    "dimension": "维度名",
    "clusters": {{
      "类别1": ["论文标题1", "论文标题2"],
      "类别2": ["论文标题3"]
    }}
  }}
]"""

        user_msg = f"论文列表：\n{json.dumps(paper_list, ensure_ascii=False, indent=2)}"
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
            # 回退到规则聚类
            return self._cluster_rule_based(papers, dimensions)
