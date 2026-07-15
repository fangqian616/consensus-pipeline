"""
学术检索引擎 — Consensus Pipeline v4.0

三线并行检索（arXiv/Semantic Scholar/OpenAlex）+ 期刊质量过滤
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


# ============ 期刊质量分级 ============

JOURNAL_QUALITY_REGISTRY = {
    # === S级：SCI/SSCI Q1 顶刊 ===
    "Energy Economics": {"level": "S", "if_2026": 13.5, "jcr": "SSCI Q1", "note": "经济学第2/380"},
    "Applied Energy": {"level": "S", "if_2026": 11.0, "jcr": "SCIE Q1", "note": "偏工程"},
    "Nature Energy": {"level": "S", "if_2026": 56.0, "jcr": "SCIE Q1", "note": "综合科学顶刊"},
    "Journal of Environmental Economics and Management": {"level": "S", "if_2026": 6.4, "jcr": "SSCI Q1×3", "note": "环境资源经济学历史顶刊"},
    "JEEM": {"level": "S", "if_2026": 6.4, "jcr": "SSCI Q1×3", "note": "同Journal of Environmental Economics and Management"},
    "Energy Policy": {"level": "S", "if_2026": 9.2, "jcr": "SSCI Q1×4", "note": "四学科全Q1"},

    # === A级 ===
    "中国人口·资源与环境": {"level": "A", "if_2026": 11.481, "jcr": "CSSCI+CSCD", "note": "AMI权威+RCCSE A+"},

    # === B级 ===
    "The Energy Journal": {"level": "B", "if_2026": 2.8, "jcr": "SSCI Q2", "note": "经济学Q2"},
    "Resource and Energy Economics": {"level": "B", "if_2026": 3.1, "jcr": "SSCI Q1/Q3", "note": "经济学Q1但环境Q3"},
    "Utilities Policy": {"level": "B", "if_2026": 4.9, "jcr": "Q1(法学)/Q2-Q3", "note": ""},
    "Energy": {"level": "B", "if_2026": 9.0, "jcr": "SCIE Q1", "note": "偏工程，高发文量"},
}


def classify_journal(journal_name: str) -> Dict[str, Any]:
    """
    对期刊进行质量分级。

    Args:
        journal_name: 期刊名称

    Returns:
        {"level": "S/A/B/C/D", "if": float, "jcr": str, "note": str}
    """
    # 精确匹配
    if journal_name in JOURNAL_QUALITY_REGISTRY:
        return JOURNAL_QUALITY_REGISTRY[journal_name]

    # 模糊匹配（去掉标点和多余空格）
    normalized = journal_name.lower().strip().replace(".", "").replace(",", "")
    for key, val in JOURNAL_QUALITY_REGISTRY.items():
        if normalized == key.lower().strip().replace(".", "").replace(",", ""):
            return val

    # 未知期刊 → 按默认规则分级
    # 如果包含已知的S级期刊名缩写
    for key, val in JOURNAL_QUALITY_REGISTRY.items():
        if key.lower() in journal_name.lower():
            return val

    return {"level": "C", "if_2026": None, "jcr": "未知", "note": "未在注册表中"}


@dataclass
class PaperCandidate:
    """候选论文"""
    title: str = ""
    doi: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    abstract: str = ""
    citation_count: int = 0
    source: str = ""  # arxiv / semantic_scholar / openalex
    quality_level: str = "C"  # S/A/B/C/D
    quality_detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)


class AcademicSearchEngine:
    """
    学术检索引擎

    支持：
    1. 三线并行检索（arXiv/Semantic Scholar/OpenAlex）
    2. 期刊质量过滤（四道筛子）
    3. 去重合并
    """

    def __init__(
        self,
        quality_levels: List[str] = None,
        min_citations: int = 5,
        min_yearly_citations: float = 2.0,
        recent_year_buffer: int = 3,
    ):
        """
        Args:
            quality_levels: 保留的期刊等级，默认 ["S", "A", "B"]
            min_citations: 最低总被引数
            min_yearly_citations: 最低年均被引数
            recent_year_buffer: 近N年论文放宽引用要求
        """
        self.quality_levels = quality_levels or ["S", "A", "B"]
        self.min_citations = min_citations
        self.min_yearly_citations = min_yearly_citations
        self.recent_year_buffer = recent_year_buffer

    def search(
        self,
        query: str,
        max_results_per_source: int = 20,
        sources: Optional[List[str]] = None,
    ) -> List[PaperCandidate]:
        """
        三线并行检索 + 质量过滤。

        Args:
            query: 检索关键词
            max_results_per_source: 每个检索源最大结果数
            sources: 检索源列表，默认全部

        Returns:
            过滤后的候选论文列表
        """
        sources = sources or ["arxiv", "semantic_scholar", "openalex"]

        # 并行检索
        all_results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            for source in sources:
                future = executor.submit(
                    self._search_single_source, source, query, max_results_per_source
                )
                futures[future] = source

            for future in as_completed(futures):
                source = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"检索源 {source} 失败: {e}")

        # 去重（按DOI + 标题相似度）
        deduped = self._deduplicate(all_results)

        # 期刊质量分级
        for paper in deduped:
            detail = classify_journal(paper.journal)
            paper.quality_level = detail["level"]
            paper.quality_detail = detail

        # 四道筛子过滤
        filtered = self._apply_four_sieves(deduped)

        # 按等级排序
        level_order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
        filtered.sort(key=lambda p: (level_order.get(p.quality_level, 5), -p.citation_count))

        return filtered

    def _search_single_source(
        self, source: str, query: str, max_results: int
    ) -> List[PaperCandidate]:
        """单源检索"""
        results = []

        if source == "arxiv":
            results = self._search_arxiv(query, max_results)
        elif source == "semantic_scholar":
            results = self._search_semantic_scholar(query, max_results)
        elif source == "openalex":
            results = self._search_openalex(query, max_results)

        return results

    def _search_arxiv(self, query: str, max_results: int) -> List[PaperCandidate]:
        """arXiv检索"""
        try:
            import urllib.request
            import xml.etree.ElementTree as ET

            url = f"http://export.arxiv.org/api/query?search_query=all:{query}&max_results={max_results}"
            req = urllib.request.Request(url, headers={"User-Agent": "ConsensusPipeline/4.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read()

            root = ET.fromstring(xml_data)
            ns = {"atom": "http://www.w3.org/2005/Atom"}

            results = []
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
                doi_elem = entry.find("atom:arxiv:doi", ns) if entry.find("atom:arxiv:doi", ns) is not None else None
                doi = doi_elem.text if doi_elem is not None else ""
                summary = entry.find("atom:summary", ns).text.strip()[:500]
                published = entry.find("atom:published", ns).text[:4]

                results.append(PaperCandidate(
                    title=title,
                    doi=doi,
                    journal="arXiv",  # arXiv预印本
                    year=int(published) if published.isdigit() else 0,
                    abstract=summary,
                    source="arxiv",
                    quality_level="D",  # 预印本默认D级
                ))

            return results

        except Exception as e:
            print(f"arXiv检索异常: {e}")
            return []

    def _search_semantic_scholar(self, query: str, max_results: int) -> List[PaperCandidate]:
        """Semantic Scholar检索"""
        try:
            import urllib.request

            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&limit={max_results}&fields=title,doi,year,abstract,citationCount,journal,authors"
            req = urllib.request.Request(url, headers={"User-Agent": "ConsensusPipeline/4.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            results = []
            for paper in data.get("data", []):
                journal_info = paper.get("journal") or {}
                journal_name = journal_info.get("name", "") if journal_info else ""

                authors = []
                for a in (paper.get("authors") or []):
                    if a.get("name"):
                        authors.append(a["name"])

                results.append(PaperCandidate(
                    title=paper.get("title", ""),
                    doi=paper.get("doi", "") or "",
                    authors=authors,
                    journal=journal_name,
                    year=paper.get("year") or 0,
                    abstract=(paper.get("abstract") or "")[:500],
                    citation_count=paper.get("citationCount", 0) or 0,
                    source="semantic_scholar",
                ))

            return results

        except Exception as e:
            print(f"Semantic Scholar检索异常: {e}")
            return []

    def _search_openalex(self, query: str, max_results: int) -> List[PaperCandidate]:
        """OpenAlex检索"""
        try:
            import urllib.request

            url = f"https://api.openalex.org/works?search={query}&per_page={max_results}&select=id,doi,title,publication_year,cited_by_count,authorships,primary_location"
            req = urllib.request.Request(url, headers={"User-Agent": "ConsensusPipeline/4.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())

            results = []
            for work in data.get("results", []):
                # 提取期刊名
                loc = work.get("primary_location") or {}
                source_info = loc.get("source") or {}
                journal_name = source_info.get("display_name", "")

                authors = []
                for a in (work.get("authorships") or []):
                    author = a.get("author") or {}
                    if author.get("display_name"):
                        authors.append(author["display_name"])

                doi = work.get("doi", "") or ""
                if doi and doi.startswith("https://doi.org/"):
                    doi = doi.replace("https://doi.org/", "")

                results.append(PaperCandidate(
                    title=work.get("title", ""),
                    doi=doi,
                    authors=authors,
                    journal=journal_name,
                    year=work.get("publication_year") or 0,
                    citation_count=work.get("cited_by_count", 0) or 0,
                    source="openalex",
                ))

            return results

        except Exception as e:
            print(f"OpenAlex检索异常: {e}")
            return []

    def _deduplicate(self, papers: List[PaperCandidate]) -> List[PaperCandidate]:
        """去重：按DOI精确去重 + 标题相似度去重"""
        seen_dois = set()
        seen_titles = set()
        result = []

        for paper in papers:
            # DOI去重
            if paper.doi and paper.doi in seen_dois:
                # 合并信息：保留引用数更高的
                existing = next((p for p in result if p.doi == paper.doi), None)
                if existing and paper.citation_count > existing.citation_count:
                    existing.citation_count = paper.citation_count
                    existing.source = f"{existing.source}+{paper.source}"
                continue

            # 标题去重（简单：取标题前30字符的小写）
            title_key = paper.title.lower()[:30].strip()
            if title_key in seen_titles:
                continue

            if paper.doi:
                seen_dois.add(paper.doi)
            seen_titles.add(title_key)
            result.append(paper)

        return result

    def _apply_four_sieves(self, papers: List[PaperCandidate]) -> List[PaperCandidate]:
        """四道筛子过滤"""
        import datetime
        current_year = datetime.datetime.now().year
        result = []

        for paper in papers:
            # 第一道：来源分级
            if paper.quality_level not in self.quality_levels:
                continue

            # B级只保留1-2篇代表
            if paper.quality_level == "B":
                b_count = sum(1 for p in result if p.quality_level == "B")
                if b_count >= 2:
                    continue

            # 第二道：引用加权
            years_since_pub = current_year - paper.year if paper.year > 0 else 10
            is_recent = years_since_pub <= self.recent_year_buffer

            if not is_recent and paper.citation_count < self.min_citations:
                # S级期刊放行，不管引用数
                if paper.quality_level != "S":
                    continue

            if not is_recent and years_since_pub > 0:
                yearly_avg = paper.citation_count / years_since_pub
                if yearly_avg < self.min_yearly_citations and paper.quality_level not in ["S", "A"]:
                    continue

            # 第三道：作者/机构信号（暂不实现，作为后续扩展点）
            # 第四道：内容初筛（暂不实现，由辩论环节处理）

            result.append(paper)

        return result
