"""
种子论文导入模块 (Seed Paper Importer)

扫描 seed_papers/ 文件夹中的 PDF 文件，提取元数据（标题/作者/摘要/DOI/年份/期刊），
与自动搜索的论文库合并，辩论时优先引用用户指定的种子论文。

v1 权重系统（2026-08-16，spec: seed_paper_weight_spec.md）:
- 三档权重: normal（普通参考）/ core（核心文献，默认）/ anchor（立场锚定，本期降级 core）
- manifest.json: default_weight + 单篇覆盖；无 manifest 默认 core
- scan_folder() 自动注入 weight + seed_profile
- merge_with_search_results() 按档位分支去重

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

# 合法权重档位（spec §0）
VALID_WEIGHTS = ("normal", "core", "anchor")


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
                - weight: "normal" | "core"（anchor 本期降级 core）
                - seed_profile: manifest 中的完整意图 profile（无 manifest 时为 {}）
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

        # === 权重系统：manifest 注入（spec §3.1）===
        self._inject_weights(papers)
        return papers

    def _load_manifest(self) -> dict:
        """读取 seed_papers/manifest.json；不存在或解析失败返回 {}"""
        mpath = self.seed_folder / "manifest.json"
        if not mpath.exists():
            return {}
        try:
            with open(mpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                logger.warning("manifest.json 顶层不是对象，按默认处理")
                return {}
            return data
        except Exception as e:
            logger.warning(f"manifest.json 读取失败，按默认处理: {e}")
            return {}

    def _inject_weights(self, papers: list[dict]) -> None:
        """
        按 manifest 给每篇论文注入 weight + seed_profile。

        解析优先级: paper.weight → default_weight → "core"（spec §2）
        anchor 本期降级 core（spec §0 决策8），标记 _anchor_downgraded。
        manifest 中列出但文件不存在的条目: 忽略 + warning。
        """
        manifest = self._load_manifest()
        default_w = manifest.get("default_weight") or "core"
        if default_w not in VALID_WEIGHTS:
            logger.warning(f"manifest default_weight 非法值 '{default_w}'，回退 core")
            default_w = "core"

        profiles = {}
        for p in manifest.get("papers", []):
            if isinstance(p, dict) and p.get("file"):
                profiles[p["file"]] = p

        seen = set()
        for paper in papers:
            fname = paper.get("file_name", "")
            seen.add(fname)
            prof = profiles.get(fname, {})
            w = prof.get("weight") or default_w
            if w not in VALID_WEIGHTS:
                logger.warning(f"{fname}: 非法 weight '{w}'，回退 core")
                w = "core"
            if w == "anchor":
                # spec §0 决策8：anchor 本期未实现，降级 core
                paper["_anchor_downgraded"] = True
                logger.info(f"[seed] anchor 档本期未实现，降级 core: {fname}")
                w = "core"
            paper["weight"] = w
            paper["seed_profile"] = prof

        # manifest 列出但文件夹里不存在的 PDF
        for fname in profiles:
            if fname not in seen:
                logger.warning(f"[seed] manifest 列出但未找到文件: {fname}")

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
        合并种子论文与搜索结果，按档位分支去重（spec §3.2）。

        normal 档（普通参考）:
        - DOI/hash 撞 → 跳过种子版
        - 不撞 → append 末尾

        core 档（核心文献）:
        - DOI 撞 → 保留搜索版元数据，但继承种子身份（source/weight/seed_profile）
        - 不撞 → insert 到最前
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
            weight = paper.get("weight", "core")

            if weight == "normal":
                # 普通参考：维持原去重逻辑，append 末尾
                if doi and doi in search_dois:
                    logger.info(f"种子论文[normal] DOI 重复，跳过: {paper.get('title', '')[:50]}")
                    continue
                if content_hash and content_hash in search_hashes:
                    logger.info(f"种子论文[normal] 内容重复，跳过: {paper.get('title', '')[:50]}")
                    continue
                merged.append(paper)
                added_count += 1

            else:
                # 核心文献：DOI 撞 → 搜索版继承种子身份
                if doi and doi in search_dois:
                    for sp in merged:
                        if (sp.get("doi") or "").lower() == doi:
                            sp["source"] = "user_seed"
                            sp["weight"] = "core"
                            sp["seed_profile"] = paper.get("seed_profile", {})
                            break
                    logger.info(f"种子论文[core] DOI 撞搜索，元数据合并+继承身份: {doi}")
                    continue
                # 不撞 → 插到最前
                merged.insert(0, paper)
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
        策略：取前几行非空文本中最长的一行作为标题候选，
        排除封面噪声（学号/单位代码/作者/指导等中文封面 + 英文元数据关键词）。
        """
        lines = text.split("\n")
        candidates = []
        noise_kw = [
            # 英文元数据关键词
            "abstract", "introduction", "keywords", "received", "accepted",
            "published", "doi:", "http", "vol.", "no.", "journal", "proceedings",
            "copyright", "©",
            # 中文学位论文封面噪声
            "单位代码", "论文作者", "指导教师", "学科专业", "研究方向",
            "提交论文", "答辩", "学位授予", "硕士学位", "博士学位",
            "中 国", "重庆", "southwest", "master", "thesis", "author name",
            "supervisor", "june", "student", "college", "姓名",
        ]
        # 正则噪声：学号行（学+任意空白+号）、连续长数字（学号/编号）
        noise_re = re.compile(r'学\s*号|\d{8,}')
        for line in lines[:30]:  # 封面页可能较多行，扩展到前30行
            line = line.strip()
            if len(line) > 10 and len(line) < 300:  # 中文标题可能较短，下限降到10
                if not any(kw in line.lower() for kw in noise_kw) and not noise_re.search(line):
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
        list[dict]: 论文元数据列表（含 weight + seed_profile）
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


def write_manifest(seed_folder: str, data: dict) -> str:
    """
    写入 seed_papers/manifest.json（UI 访谈模块使用）。

    Args:
        seed_folder: 种子论文文件夹路径
        data: manifest 数据（自动补 version/updated_at）

    Returns:
        str: 写入的文件路径
    """
    from datetime import datetime, timezone, timedelta
    folder = Path(seed_folder)
    folder.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data.setdefault("version", 1)
    data["updated_at"] = datetime.now(
        timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    mpath = folder / "manifest.json"
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"manifest.json 已写入: {mpath}")
    return str(mpath)


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    papers = import_seed_papers("seed_papers")
    print(f"\n导入 {len(papers)} 篇种子论文:")
    for p in papers:
        print(f"  - [{p.get('weight', '?')}] {p['title'][:60]} ({p['year']}) DOI={p.get('doi', 'N/A')}")
