"""
种子论文导入模块 (Seed Paper Importer)

扫描 seed_papers/ 文件夹中的 PDF 文件，提取元数据（标题/作者/摘要/DOI/年份/期刊），
与自动搜索的论文库合并，辩论时优先引用用户指定的种子论文。

依赖: pip install PyMuPDF requests
"""

import os
import re
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF
import requests

logger = logging.getLogger(__name__)

# DOI 正则：匹配 10.xxxx/... 格式
DOI_PATTERN = re.compile(
    r'\b(10\.\d{4,9}/[^\s,;"\'\]}{)]+)',
    re.IGNORECASE
)

CROSSREF_API = "https://api.crossref.org/works/{doi}"


class SeedPaperImporter:
    """种子论文导入器：扫描文件夹 → 解析PDF → 提取元数据 → 合并去重"""

    def __init__(self, seed_folder: str = "seed_papers"):
        self.seed_folder = Path(seed_folder)

    def scan_folder(self) -> list[dict]:
        """
        扫描 seed_papers/ 文件夹，解析所有 PDF 文件。

        Returns:
            list[dict]: 论文元数据列表，每项包含:
                - title, authors, abstract, doi, year, journal
                - source: "user_seed"
                - grade: "B" (无 DOI) 或按期刊分级
                - full_text_excerpt: 前3页文本摘录
        """
        if not self.seed_folder.exists():
            logger.info(f"种子论文文件夹不存在: {self.seed_folder}，跳过")
            return []

        pdf_files = sorted(self.seed_folder.glob("*.pdf"))
        if not pdf_files:
            logger.info("种子论文文件夹为空，跳过")
            return []

        logger.info(f"发现 {len(pdf_files)} 篇种子论文")
        papers = []
        for pdf_path in pdf_files:
            try:
                paper = self.parse_pdf(pdf_path)
                if paper:
                    papers.append(paper)
                    logger.info(f"  ✅ {paper.get('title', '未知标题')[:60]}")
                else:
                    logger.warning(f"  ❌ 解析失败: {pdf_path.name}")
            except Exception as e:
                logger.error(f"  ❌ {pdf_path.name}: {e}")

        return papers

    def parse_pdf(self, pdf_path: Path) -> Optional[dict]:
        """
        解析单篇 PDF，提取元数据。

        流程:
        1. PyMuPDF 取前3页文本
        2. 正则找 DOI
        3. 有 DOI → Crossref API 拿元数据
        4. 无 DOI → 从首页文本提取 title/authors
        """
        doc = fitz.open(str(pdf_path))
        if doc.page_count == 0:
            doc.close()
            return None

        # 取前3页文本
        max_pages = min(3, doc.page_count)
        text_pages = []
        for i in range(max_pages):
            text_pages.append(doc[i].get_text())
        full_excerpt = "\n".join(text_pages)[:3000]  # 限制3000字符
        doc.close()

        # 提取 DOI
        doi = self._extract_doi(full_excerpt)

        if doi:
            # 有 DOI → Crossref API
            metadata = self._query_crossref(doi)
            if metadata:
                return {
                    "title": metadata.get("title", ""),
                    "authors": metadata.get("authors", []),
                    "abstract": metadata.get("abstract", ""),
                    "doi": doi,
                    "year": metadata.get("year", ""),
                    "journal": metadata.get("journal", ""),
                    "source": "user_seed",
                    "grade": "B",  # 种子论文默认B级
                    "full_text_excerpt": full_excerpt,
                    "file_name": pdf_path.name,
                    "content_hash": self._hash_content(full_excerpt),
                }

        # 无 DOI 或 Crossref 失败 → 从文本提取
        title = self._extract_title(full_excerpt)
        authors = self._extract_authors(full_excerpt)
        year = self._extract_year(full_excerpt)

        return {
            "title": title or pdf_path.stem,
            "authors": authors,
            "abstract": "",  # 无法可靠提取
            "doi": doi or "",
            "year": year,
            "journal": "",
            "source": "user_seed",
            "grade": "B",
            "full_text_excerpt": full_excerpt,
            "file_name": pdf_path.name,
            "content_hash": self._hash_content(full_excerpt),
        }

    def merge_with_search_results(
        self,
        seed_papers: list[dict],
        search_papers: list[dict],
    ) -> list[dict]:
        """
        合并种子论文与搜索结果，按 DOI 去重。

        去重策略:
        - 有 DOI 且重复 → 保留搜索版（有完整期刊分级/引用数）
        - 无 DOI → 按 content_hash 去重
        - 种子论文标记 source='user_seed'，辩论时优先引用
        """
        if not seed_papers:
            return search_papers

        # 收集搜索论文的 DOI 集合
        search_dois = {p.get("doi", "").lower() for p in search_papers if p.get("doi")}
        search_hashes = {p.get("content_hash", "") for p in search_papers if p.get("content_hash")}

        merged = list(search_papers)  # 保留全部搜索论文
        added_count = 0

        for paper in seed_papers:
            doi = paper.get("doi", "").lower()
            content_hash = paper.get("content_hash", "")

            # DOI 去重
            if doi and doi in search_dois:
                logger.info(f"种子论文 DOI 重复，跳过: {paper.get('title', '')[:50]}")
                continue

            # content_hash 去重
            if content_hash and content_hash in search_hashes:
                logger.info(f"种子论文内容重复，跳过: {paper.get('title', '')[:50]}")
                continue

            merged.append(paper)
            added_count += 1

        logger.info(f"种子论文合并完成: {added_count} 篇新增, 总计 {len(merged)} 篇")
        return merged

    # ---- 内部方法 ----

    def _extract_doi(self, text: str) -> Optional[str]:
        """从文本中提取第一个有效 DOI"""
        match = DOI_PATTERN.search(text)
        if match:
            doi = match.group(1).rstrip(".")
            return doi
        return None

    def _query_crossref(self, doi: str) -> Optional[dict]:
        """通过 Crossref API 查询论文元数据"""
        try:
            url = CROSSREF_API.format(doi=doi)
            resp = requests.get(url, timeout=10, headers={
                "User-Agent": "ConsensusPipeline/1.0 (mailto:consensus-pipeline@example.com)"
            })
            if resp.status_code != 200:
                logger.warning(f"Crossref 查询失败 [{resp.status_code}]: {doi}")
                return None

            data = resp.json().get("message", {})

            # 提取标题
            title_list = data.get("title", [])
            title = title_list[0] if title_list else ""

            # 提取作者
            authors = []
            for author in data.get("author", []):
                name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                if name:
                    authors.append(name)

            # 提取年份
            issued = data.get("issued", {}).get("date-parts", [[]])
            year = str(issued[0][0]) if issued and issued[0] else ""

            # 提取期刊
            journal_list = data.get("container-title", [])
            journal = journal_list[0] if journal_list else ""

            # 提取摘要（Crossref 不一定有）
            abstract = data.get("abstract", "")
            # Crossref 摘要可能带 JATS XML 标签，简单清理
            abstract = re.sub(r'<[^>]+>', '', abstract)

            return {
                "title": title,
                "authors": authors,
                "abstract": abstract,
                "year": year,
                "journal": journal,
            }

        except Exception as e:
            logger.warning(f"Crossref 查询异常: {doi} - {e}")
            return None

    def _extract_title(self, text: str) -> str:
        """
        从首页文本提取标题（启发式）。
        策略：取前几行非空文本中最长的一行作为标题候选。
        """
        lines = text.split("\n")
        candidates = []
        for line in lines[:20]:  # 只看前20行
            line = line.strip()
            if len(line) > 15 and len(line) < 300:  # 合理的标题长度
                # 排除常见非标题行
                if not any(kw in line.lower() for kw in [
                    "abstract", "introduction", "keywords", "received",
                    "accepted", "published", "doi:", "http", "vol.", "no.",
                    "journal", "proceedings", "copyright", "©"
                ]):
                    candidates.append(line)

        if candidates:
            # 取最长的作为标题（标题通常是最长的前几行之一）
            return max(candidates, key=len)
        return ""

    def _extract_authors(self, text: str) -> list[str]:
        """
        从首页文本提取作者（启发式）。
        策略：找包含逗号分隔的人名的行。
        """
        lines = text.split("\n")
        for line in lines[:15]:
            line = line.strip()
            # 作者行特征：包含多个逗号分隔的名字，可能有 "and"
            if "," in line and len(line) < 500:
                # 简单检查是否像人名（包含多个大写开头的词）
                words = re.findall(r'[A-Z][a-z]+', line)
                if len(words) >= 2:
                    # 按逗号/and 分割
                    parts = re.split(r',\s*|\s+and\s+', line)
                    authors = [p.strip().rstrip("0123456789,*†‡§¶") for p in parts]
                    authors = [a for a in authors if len(a) > 2 and len(a) < 60]
                    if authors:
                        return authors[:10]  # 最多10个作者
        return []

    def _extract_year(self, text: str) -> str:
        """从文本提取年份"""
        # 找 20xx 格式的年份
        matches = re.findall(r'\b(20[0-2]\d)\b', text[:2000])
        if matches:
            # 取最近的年份
            return max(matches)
        return ""

    def _hash_content(self, text: str) -> str:
        """对文本内容做 hash，用于无 DOI 时的去重"""
        # 取前500字符做 hash，避免全文 hash 开销
        return hashlib.md5(text[:500].encode()).hexdigest()


# ---- 便捷函数 ----

def import_seed_papers(folder: str = "seed_papers") -> list[dict]:
    """
    一键导入种子论文。

    Args:
        folder: 种子论文文件夹路径

    Returns:
        list[dict]: 论文元数据列表
    """
    importer = SeedPaperImporter(folder)
    return importer.scan_folder()


def merge_papers(seed_folder: str = "seed_papers", search_papers: list = None) -> list[dict]:
    """
    导入种子论文并与搜索结果合并。

    Args:
        seed_folder: 种子论文文件夹路径
        search_papers: 自动搜索的论文列表

    Returns:
        list[dict]: 合并后的论文列表
    """
    if search_papers is None:
        search_papers = []

    seed_papers = import_seed_papers(seed_folder)
    importer = SeedPaperImporter(seed_folder)
    return importer.merge_with_search_results(seed_papers, search_papers)


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    papers = import_seed_papers("seed_papers")
    print(f"\n导入 {len(papers)} 篇种子论文:")
    for p in papers:
        print(f"  - {p['title'][:60]} ({p['year']}) DOI={p.get('doi', 'N/A')}")
