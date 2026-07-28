"""
Citation-Grounded Fact Verification — Consensus Pipeline

Verifies factual claims in the final report by:
1. Parsing citation markers ([1], [2], ...) and their reference entries (with DOIs)
2. Fetching cited paper abstracts via CrossRef / academic search
3. Decomposing citation-bearing paragraphs into atomic factual claims
4. Running NLI (Natural Language Inference) against cited paper abstracts

This replaces the naive "extract paragraphs → search → match" approach with
a principled citation-grounded verification pipeline.
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


# ── Content Filters ─────────────────────────────────────────────────────────

_CODE_KEYWORDS_RE = re.compile(
    r'(?:def |class |import |from \w+ import|return |print\(|np\.|pd\.|plt\.|'
    r'torch\.|tf\.|dataframe|\.view\(|\.reshape\(|__init__|self\.|lambda |'
    r'函数|参数|默认值|实例化|调用|字典|列表|变量|模块|对象|方法|属性)',
    re.IGNORECASE,
)

# Patterns indicating code/API descriptions or paper metadata — not verifiable claims
_NON_CLAIM_PATTERNS = [
    # Code / API / data-structure descriptions
    r'字典包含', r'的值通过\s*\w+\(', r'通过\s*\w+\.\w+\(',
    r'标签列名', r'属性列名', r'属性值为', r'数据源是',
    r'构造函数', r'label_names', r'protected_attribute',
    r'BinaryLabelDataset', r'df_\w+', r'data_\w+',
    r'test_dataset', r'pert_dataset', r'results\s*字典',
    r'grad_\w+', r'income_binary', r'sex_binary',
    r'实例\b', r'函数\s*\w+\s*用于', r'参数\s*\w+\s*的?默认值',
    r'实例化\s*\w+\s*对象', r'调用\s*\w+\.\w+', r'值为\s*\w+\.\w+\(',
    r'循环遍历', r'从\s*\w+\s*中筛选', r'使用\s*\w+\.\w+\s*从',
    r'将\s*\w+\s*添加', r'被赋值给', r'接受\s*\w+\s*作为参数',
    r'返回的?第[一二三123]\w*个值', r'\w+\.\w+\(\)',
    r'svdvals', r'bootstrap\s*样本', r'SimpleSCM', r'scm_\w+',
    r'ate_\w+', r'cate\b', r'generate_counterfactual', r'causal_fairness_test',
    r'mean_difference|disparate_impact', r'value_counts|normalize=True',
    r'np\.random\.choice', r'\.iloc\[', r'有放回抽样', r'唯一值',
    r'子集\s*subset', r'梯度张量|奇异值|重塑为|列向量',
    r'len\(\w+\)', r'\.value_counts\(', r'\.mean\(\)',
    # Paper metadata descriptions (author/title/journal/DOI — not content claims)
    r'该论文的作者是', r'论文标题为', r'论文的标题是',
    r'是论文的作者之一', r'论文来源为', r'论文发表于',
    r'arXiv\s*preprint', r'DOI\s*为', r'发表于\s*\d{4}年?',
    r'作者包括', r'第一作者',
    # Report self-references (framework/structure descriptions — not external claims)
    r'报告揭示', r'报告提出', r'本报告', r'报告分析', r'报告指出',
    r'报告总结', r'报告发现', r'报告构建',
    r'个研究空白', r'个子方向', r'层结构', r'知识网络',
    r'通过整合.*[组部]', r'构建了.*框架', r'构建了一套',
    r'三C\b', r'综合范式', r'失效边界声明', r'完整性验证框架',
    r'范式转变', r'研究空白',
    # System methodology / pipeline process descriptions (not external claims)
    r'共识方案', r'辩论.*揭示', r'精查组', r'筛选体系', r'四级质量',
    r'无DOI.*无资格', r'先广后精', r'多源定制检索', r'文献网络',
    r'核心文献池', r'范式跃迁', r'单维效率', r'系统协同',
    # Report self-references (section pointers in body text)
    r'本文第\d*\.?\d*[节章]', r'本[节章]\s', r'本文.*探讨',
    r'本文.*指出', r'本文.*分析', r'本文.*构建',
]

_NON_CLAIM_RE = re.compile('|'.join(_NON_CLAIM_PATTERNS), re.IGNORECASE)


def _is_verifiable_claim(text: str) -> bool:
    """Return True only if text is a verifiable factual claim about research content."""
    # Code keyword density (threshold 2 — catches short code descriptions)
    if len(_CODE_KEYWORDS_RE.findall(text)) >= 2:
        return False
    # Specific non-claim patterns
    if _NON_CLAIM_RE.search(text):
        return False
    return True


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks and inline code from markdown text."""
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    return text


# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class Reference:
    """A single entry from the report's reference/bibliography list."""
    index: int                    # Citation number (1-based)
    raw_text: str                 # Full reference text
    doi: str = ""                 # Extracted DOI
    title: str = ""               # Paper title
    authors: str = ""             # Author string
    year: str = ""                # Publication year
    abstract: str = ""            # Fetched abstract (populated later)


@dataclass
class CitationContext:
    """A paragraph/sentence in the report that contains citation markers."""
    text: str                     # The paragraph text
    cited_indices: List[int]      # Reference indices cited in this paragraph
    section: str = ""             # Section header if detectable


@dataclass
class AtomicClaim:
    """A single decomposed factual claim."""
    text: str                     # The atomic claim
    source_context: str           # Original paragraph it came from
    cited_indices: List[int]      # References that should support this claim


@dataclass
class NLIResult:
    """NLI verification result for one atomic claim against one reference."""
    claim: str
    ref_index: int
    ref_title: str
    ref_doi: str
    label: str = "neutral"        # entail / contradict / neutral
    confidence: float = 0.0
    explanation: str = ""
    evidence: str = "abstract"    # abstract / title (title = weaker evidence)


@dataclass
class ClaimVerification:
    """Aggregated verification for one atomic claim."""
    claim: AtomicClaim
    nli_results: List[NLIResult] = field(default_factory=list)
    status: str = "unverified"    # verified / partially_verified / contradicted / unverified
    confidence: float = 0.0


@dataclass
class CitationVerificationReport:
    """Full verification report."""
    claim_verifications: List[ClaimVerification] = field(default_factory=list)
    total_references: int = 0
    resolved_references: int = 0   # How many refs got abstracts
    total_citations: int = 0       # Citation contexts found
    total_claims: int = 0          # Atomic claims decomposed
    verified: int = 0
    partially_verified: int = 0
    contradicted: int = 0
    unverified: int = 0
    # v0.12.8: unverified claims backed ONLY by title-level evidence (no
    # public abstract exists) — reported but excluded from the confidence
    # score denominator ("insufficient evidence", not "failed").
    insufficient_evidence: int = 0
    overall_confidence: float = 0.0
    summary: str = ""
    # v0.12.5: audit trail for cached-abstract integrity checks
    abstract_audit: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        import dataclasses
        return dataclass.asdict(self) if hasattr(dataclass, 'asdict') else dataclasses.asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ── Citation Parser ─────────────────────────────────────────────────────────

class CitationParser:
    """Parse citation markers and reference list from report text."""

    # Common citation patterns: [1], [1,2], [1-3], (Author, 2023), [Author et al., 2023]
    CITE_BRACKET = re.compile(r'\[(\d+(?:\s*[,\-–]\s*\d+)*)\]')
    CITE_PAREN = re.compile(r'\((?:[A-Z][a-z]+(?:\s+et\s+al\.?)?,?\s+\d{4}[a-z]?)\)')

    # Reference list patterns
    REF_NUMBERED = re.compile(r'^\s*\[?(\d+)\]?\s*[.\)]?\s+(.+)', re.MULTILINE)
    REF_DOI = re.compile(r'(?:doi[:\s]*|https?://(?:dx\.)?doi\.org/)(10\.\d{4,}/[^\s,;\]\)]+)', re.IGNORECASE)
    REF_YEAR = re.compile(r'\b(19|20)\d{2}\b')
    REF_TITLE_QUOTED = re.compile(r'[""\'](.*?)[""\']')

    @classmethod
    def extract_references(cls, report_text: str) -> List[Reference]:
        """Extract numbered references from the bibliography section."""
        references = []

        # Find the references/bibliography section
        ref_section = cls._find_reference_section(report_text)
        if not ref_section:
            return references

        # Parse numbered entries
        for m in cls.REF_NUMBERED.finditer(ref_section):
            idx = int(m.group(1))
            text = m.group(2).strip()
            if len(text) < 10:
                continue

            ref = Reference(index=idx, raw_text=text)

            # Extract DOI
            doi_m = cls.REF_DOI.search(text)
            if doi_m:
                ref.doi = doi_m.group(1).rstrip('.')

            # Extract year
            year_m = cls.REF_YEAR.search(text)
            if year_m:
                ref.year = year_m.group(0)

            # Try to extract title (heuristic: text between authors and year/journal)
            ref.title = cls._guess_title(text)

            references.append(ref)

        return references

    @classmethod
    def extract_citation_contexts(cls, report_text: str) -> List[CitationContext]:
        """Find paragraphs containing citation markers."""
        contexts = []
        current_section = ""

        # Split into paragraphs, tracking section headers
        lines = report_text.split('\n')
        paragraph_buf = []

        for line in lines:
            stripped = line.strip()

            # Track section headers
            if stripped.startswith('#'):
                if paragraph_buf:
                    cls._flush_paragraph(paragraph_buf, current_section, contexts)
                    paragraph_buf = []
                current_section = stripped.lstrip('#').strip()
                continue

            if not stripped:
                if paragraph_buf:
                    cls._flush_paragraph(paragraph_buf, current_section, contexts)
                    paragraph_buf = []
                continue

            paragraph_buf.append(stripped)

        if paragraph_buf:
            cls._flush_paragraph(paragraph_buf, current_section, contexts)

        return contexts

    @classmethod
    def _split_sentences(cls, text: str) -> List[str]:
        """Split text into sentences, handling Chinese and English punctuation."""
        parts = re.split(r'(?<=[。；！？.!?])\s*', text)
        return [p.strip() for p in parts if p.strip()]

    @classmethod
    def _flush_paragraph(cls, lines: List[str], section: str, contexts: List[CitationContext]):
        text = ' '.join(lines)
        # Skip code-dense paragraphs — not verifiable factual claims
        if not _is_verifiable_claim(text):
            return
        # Sentence-level extraction: each sentence gets its own citations
        # This prevents claims from inheriting citations of neighboring sentences
        for sent in cls._split_sentences(text):
            sent = sent.strip()
            if len(sent) < 15:
                continue
            if not _is_verifiable_claim(sent):
                continue
            cited = cls._extract_cited_indices(sent)
            if cited:
                contexts.append(CitationContext(
                    text=sent,
                    cited_indices=cited,
                    section=section,
                ))

    @classmethod
    def _extract_cited_indices(cls, text: str) -> List[int]:
        """Extract all reference indices from citation markers like [1], [1,2], [1-3]."""
        indices = set()
        for m in cls.CITE_BRACKET.finditer(text):
            parts = re.split(r'[,\s]+', m.group(1))
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # Handle ranges like 1-3 or 1–3
                range_m = re.match(r'(\d+)\s*[-–]\s*(\d+)', part)
                if range_m:
                    start, end = int(range_m.group(1)), int(range_m.group(2))
                    indices.update(range(start, min(end + 1, start + 20)))  # Cap range
                elif part.isdigit():
                    indices.add(int(part))
        return sorted(indices)

    @classmethod
    def _find_reference_section(cls, text: str) -> str:
        """Find the references/bibliography section of the report."""
        # Common section headers
        patterns = [
            r'(?i)#{1,3}\s*(?:references|bibliography|参考文献|引用文献|文献列表)\s*\n(.*?)(?=\n#{1,3}\s|\Z)',
            r'(?i)\n(?:references|bibliography|参考文献|引用文献|文献列表)\s*\n(.*?)(?=\n#{1,3}\s|\Z)',
        ]
        for pat in patterns:
            m = re.search(pat, text, re.DOTALL)
            if m:
                return m.group(1)

        # Fallback: last 30% of text if it contains many numbered entries
        tail_start = int(len(text) * 0.7)
        tail = text[tail_start:]
        numbered_count = len(re.findall(r'^\s*\[?\d+\]?', tail, re.MULTILINE))
        if numbered_count >= 3:
            return tail

        return ""

    @classmethod
    def _guess_title(cls, ref_text: str) -> str:
        """Heuristic title extraction from a reference entry."""
        # Try quoted title first
        qm = cls.REF_TITLE_QUOTED.search(ref_text)
        if qm:
            return qm.group(1)

        # Heuristic: after authors (before year), before journal name
        # Pattern: Authors. "Title." Journal, Year.
        # or: Authors. Title. Journal (Year)
        parts = re.split(r'\.\s+', ref_text)
        if len(parts) >= 2:
            # Often the second segment is the title
            candidate = parts[1].strip()
            if 10 < len(candidate) < 300:
                return candidate

        # Fallback: first 100 chars
        return ref_text[:100]


# ── Open-access PDF abstract extraction (v0.12.5) ───────────────────────────

def _extract_abstract_from_text(text: str) -> str:
    """Cut the abstract section out of first/second-page PDF text."""
    m = re.search(r'(?i)\babstract\b[\s.:—–-]*', text)
    if not m:
        return ""
    rest = text[m.end():]
    end = re.search(
        r'(?i)\n\s*(?:jel[- ]?(?:code|classification)|keywords|key words|'
        r'\d{0,2}\.?\s*introduction\b|i\.\s*introduction)',
        rest,
    )
    abstract = rest[:end.start()] if end else rest[:2500]
    abstract = re.sub(r'\s+', ' ', abstract).strip()
    if 150 <= len(abstract) <= 3000:
        return abstract
    return ""


def _looks_like_citation_info(text: str, title: str) -> bool:
    """True when a fetched 'abstract' is really just bibliographic citation
    info (authors + title + journal + volume/pages), not paper content.

    v0.12.6: OpenAlex carries such stubs as the abstract for old records
    (e.g. JSTOR-era papers). Accepting one poisons NLI evidence AND blocks
    the DOI-exact PDF fallbacks that could have found the real abstract.
    """
    t = re.sub(r"\s+", " ", (text or "")).strip()
    if not t or len(t) > 500:
        return False  # stubs are short; real abstracts run long
    def _norm(x):
        return re.sub(r"[^a-z0-9 ]", "", (x or "").lower())
    nt, ntitle = _norm(t), _norm(title)
    if not ntitle or ntitle[:50] not in nt:
        return False  # a stub echoes the paper's own title verbatim
    markers = ("pp ", "vol ", "no ", "isbn", "issn", "doi", "http",
               "journal", "proceedings", "university press")
    return any(m in nt for m in markers)


def _extract_pdf_link_from_landing(data: bytes, page_url: str) -> str:
    """Dig a direct PDF URL out of an HTML repository landing page.

    v0.12.7: Unpaywall/S2 OA locations are often landing pages (DSpace
    /handle/, institutional repositories) rather than direct PDFs.
    Priority: <meta name="citation_pdf_url"> (Google Scholar standard) ->
    DSpace bitstream link -> any .pdf href. Returns "" when nothing found.
    """
    try:
        import html as _html
        import urllib.parse
        page = data.decode('utf-8', errors='replace')
    except Exception:
        return ""
    link = ""
    m = re.search(r"(?is)<meta[^>]+name=['\"]citation_pdf_url['\"][^>]*content=['\"]([^'\"]+)['\"]", page) or \
        re.search(r"(?is)<meta[^>]+content=['\"]([^'\"]+)['\"][^>]*name=['\"]citation_pdf_url['\"]", page)
    if m:
        link = m.group(1)
    if not link:
        m = re.search(r"(?is)href=['\"]([^'\"]*bitstream[^'\"]*)['\"]", page)
        if m:
            link = m.group(1)
    if not link:
        m = re.search(r"(?is)href=['\"]([^'\"]+\.pdf(?:\?[^'\"]*)?)['\"]", page)
        if m:
            link = m.group(1)
    if not link:
        return ""
    return urllib.parse.urljoin(page_url, _html.unescape(link))


def _fetch_pdf_abstract(pdf_url: str, max_bytes: int = 6_000_000, _depth: int = 0) -> str:
    """Download an open-access PDF and extract its abstract (best-effort).

    Returns "" on any failure — non-PDF response, parse error, no abstract
    marker — so callers simply fall through to the next source.
    v0.12.7: a non-PDF response is treated as a repository landing page and
    dug once for its real PDF link (one level deep, no recursion loop).
    """
    try:
        import io
        import urllib.request
        req = urllib.request.Request(
            pdf_url, headers={'User-Agent': 'Mozilla/5.0 (academic abstract fetch)'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read(max_bytes)
        if data[:5] != b'%PDF-':
            if _depth == 0:
                link = _extract_pdf_link_from_landing(data, pdf_url)
                if link and link != pdf_url:
                    return _fetch_pdf_abstract(link, max_bytes, _depth=1)
            return ""
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        text = ""
        for page in reader.pages[:4]:
            text += (page.extract_text() or "") + "\n"
        return _extract_abstract_from_text(text)
    except Exception:
        return ""


# ── Reference Resolver ───────────────────────────────────────────────────────

class ReferenceResolver:
    """Fetch paper abstracts for references using CrossRef and academic search."""

    def __init__(self, search_fn=None):
        """
        Args:
            search_fn: Optional search function fn(query, max_results) -> List[Dict]
                       Fallback when CrossRef doesn't have the abstract.
        """
        self.search_fn = search_fn

    def resolve(self, references: List[Reference]) -> int:
        """
        Fetch abstracts for all references that have DOIs.

        Returns:
            Number of references successfully resolved with abstracts.
        """
        resolved = 0
        self._pdf_attempts = 0  # v0.12.5: bound expensive PDF fetches per resolve()

        # Step 1: batch fill via OpenAlex (a single request covers up to 25 DOIs;
        # far cheaper than per-ref lookups and has the best abstract coverage)
        need = [r for r in references if not r.abstract and r.doi]
        if need:
            try:
                from academic.search_engine import openalex_batch_abstracts
                got = openalex_batch_abstracts([r.doi for r in need])
                for r in need:
                    text = got.get(r.doi) or got.get(r.doi.lower())
                    # v0.12.6: reject citation-info stubs so the DOI-exact
                    # fallbacks below still get a chance at the real abstract.
                    if text and not _looks_like_citation_info(text, r.title):
                        r.abstract = text
            except Exception as _oa_err:
                # v0.12.8: log why the batch failed (shared-IP 429s etc.) so
                # cloud deployments are diagnosable from the Manage-App logs.
                print(f"  [verify] openalex batch FAIL: {type(_oa_err).__name__}: {str(_oa_err)[:150]}")

        # Step 2: per-ref fallback (Crossref by DOI, then title search, capped)
        # v0.12.8: every resolution logs its source, every failure logs a
        # TITLE-ONLY line — cloud runs (Manage-App terminal) stay diagnosable.
        _title_attempts = 0
        for ref in references:
            if ref.abstract:
                resolved += 1
                continue

            # Try CrossRef first (if DOI available)
            if ref.doi:
                abstract = self._fetch_crossref(ref.doi)
                if abstract and not _looks_like_citation_info(abstract, ref.title):
                    ref.abstract = abstract
                    resolved += 1
                    print(f"  [verify] resolved [{ref.index}] {ref.doi} via crossref ({len(abstract)} ch)")
                    continue

            # v0.12.5/0.12.7: DOI-exact fallbacks — OpenAIRE (aggregated
            # repository/publisher abstracts), Semantic Scholar (abstract or
            # its open-access PDF), then Unpaywall OA PDF. These cover old
            # Elsevier/JSTOR papers OpenAlex/Crossref carry no abstract for.
            if ref.doi:
                abstract = self._fetch_openaire(ref.doi)
                if abstract and not _looks_like_citation_info(abstract, ref.title):
                    ref.abstract = abstract
                    resolved += 1
                    print(f"  [verify] resolved [{ref.index}] {ref.doi} via openaire ({len(abstract)} ch)")
                    continue
                abstract = self._fetch_s2(ref.doi)
                if abstract and not _looks_like_citation_info(abstract, ref.title):
                    ref.abstract = abstract
                    resolved += 1
                    print(f"  [verify] resolved [{ref.index}] {ref.doi} via s2 ({len(abstract)} ch)")
                    continue
                abstract = self._fetch_unpaywall_pdf(ref.doi)
                if abstract:
                    ref.abstract = abstract
                    resolved += 1
                    print(f"  [verify] resolved [{ref.index}] {ref.doi} via unpaywall-pdf ({len(abstract)} ch)")
                    continue

            # Fallback: academic search by title (bounded — slow per call)
            if ref.title and self.search_fn and _title_attempts < 5:
                _title_attempts += 1
                abstract = self._search_by_title(ref.title)
                if abstract:
                    ref.abstract = abstract
                    resolved += 1
                    print(f"  [verify] resolved [{ref.index}] via title-search ({len(abstract)} ch)")

            if not ref.abstract:
                print(f"  [verify] TITLE-ONLY [{ref.index}] doi={ref.doi or 'N/A'} "
                      f"title={(ref.title or '')[:50]}")

        return resolved

    def _fetch_crossref(self, doi: str) -> str:
        """Fetch abstract from CrossRef API."""
        try:
            import urllib.request
            import urllib.error

            url = f"https://api.crossref.org/works/{doi}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'ConsensusPipeline/1.0 (mailto:fang616@users.noreply.github.com)',
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            message = data.get('message', {})
            abstract = message.get('abstract', '')
            if abstract:
                # CrossRef abstracts often have JATS XML tags
                abstract = re.sub(r'<[^>]+>', '', abstract).strip()
                return abstract

            # Some entries have no abstract but have title
            return ""
        except Exception as _cr_err:
            print(f"  [verify] crossref FAIL {doi}: {type(_cr_err).__name__}: {str(_cr_err)[:150]}")
            return ""

    def _fetch_openaire(self, doi: str) -> str:
        """OpenAIRE Search API by DOI: abstract aggregated from repositories
        and publishers. v0.12.7: covers Elsevier / old-JSTOR papers that
        OpenAlex, Crossref and S2 all carry no abstract for — free, keyless,
        and reachable from datacenter IPs where S2 rate-limits us."""
        try:
            import html as _html
            import urllib.parse
            import urllib.request
            q = urllib.parse.quote(doi, safe="()/:.")
            url = f"https://api.openaire.eu/search/publications?doi={q}"
            req = urllib.request.Request(url, headers={"User-Agent": "ConsensusPipeline/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read(2_000_000).decode("utf-8", errors="replace")
            best = ""
            for d in re.findall(r"(?is)<(?:\w+:)?description[^>]*>(.*?)</(?:\w+:)?description>", body):
                d = re.sub(r"<[^>]+>", " ", d)
                d = _html.unescape(d)
                d = re.sub(r"\s+", " ", d).strip()
                d = re.sub(r"^abstract\b[:\s.\-–—]*", "", d, flags=re.I).strip()
                if len(d) > len(best):
                    best = d
            if 150 <= len(best):
                return best[:3000]
            print(f"  [verify] openaire EMPTY {doi} (no usable abstract in response)")
        except Exception as _oa2_err:
            print(f"  [verify] openaire FAIL {doi}: {type(_oa2_err).__name__}: {str(_oa2_err)[:150]}")
        return ""

    def _search_by_title(self, title: str) -> str:
        """Search by title; accept an abstract ONLY from a near-exact title match.

        v0.12.3: the relevance-ranked top-1 is often a *different* paper (older /
        low-cited targets lose ranking), and its abstract was grafted onto this
        reference — misaligned abstracts corrupted every NLI verdict (22% incident).
        Now: scan top-5, require normalized title similarity >= 0.80, else return ""
        (reference falls back to title-level NLI, capped at partially — honest).
        """
        if not self.search_fn:
            return ""
        try:
            results = self.search_fn(title, max_results=5)
        except Exception:
            return ""
        if not results:
            return ""
        import difflib
        def _norm(s):
            return re.sub(r'[^a-z0-9 ]', '', (s or '').lower()).strip()
        want = _norm(title)
        best_abs, best_ratio = "", 0.0
        for r in results:
            if not r.get('abstract'):
                continue
            if _looks_like_citation_info(r['abstract'], r.get('title', '')):
                continue  # v0.12.6: skip citation-info stubs
            ratio = difflib.SequenceMatcher(None, want, _norm(r.get('title', ''))).ratio()
            if ratio > best_ratio:
                best_ratio, best_abs = ratio, r['abstract']
        if best_abs and best_ratio >= 0.80:
            return best_abs
        print(f"  [verify] title-search abstract REJECTED (best match {best_ratio:.2f}): {title[:60]}")
        return ""

    def _fetch_s2(self, doi: str) -> str:
        """Semantic Scholar by DOI: direct abstract, else its open-access PDF.

        v0.12.5: covers old papers OpenAlex/Crossref have no abstract for.
        Best-effort (S2 rate-limits requests without an API key).
        """
        try:
            import os
            import urllib.request
            url = (f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
                   f"?fields=title,abstract,openAccessPdf")
            headers = {'User-Agent': 'ConsensusPipeline/1.0'}
            _s2k = os.environ.get('S2_API_KEY', '')  # v0.12.7: optional key
            if _s2k:
                headers['x-api-key'] = _s2k
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            abstract = (data.get('abstract') or '').strip()
            if abstract:
                return abstract
            pdf_url = (data.get('openAccessPdf') or {}).get('url') or ''
            if pdf_url and self._pdf_attempts < 6:
                self._pdf_attempts += 1
                return _fetch_pdf_abstract(pdf_url)
        except Exception as _s2_err:
            print(f"  [verify] s2 FAIL {doi}: {type(_s2_err).__name__}: {str(_s2_err)[:150]}")
        return ""

    def _fetch_unpaywall_pdf(self, doi: str) -> str:
        """Unpaywall by DOI: find an OA PDF location and extract its abstract."""
        try:
            import urllib.request
            url = f"https://api.unpaywall.org/v2/{doi}?email=fang616@users.noreply.github.com"
            req = urllib.request.Request(url, headers={'User-Agent': 'ConsensusPipeline/1.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            if not data.get('is_oa'):
                return ""
            urls = []
            best = data.get('best_oa_location') or {}
            if best.get('url_for_pdf'):
                urls.append(best['url_for_pdf'])
            for loc in data.get('oa_locations') or []:
                u = loc.get('url_for_pdf')
                if u and u not in urls:
                    urls.append(u)
            # v0.12.7: OA locations without a direct PDF often point at a
            # repository landing page — _fetch_pdf_abstract now digs those
            # for the real PDF link, so offer them as fallback candidates.
            for loc in [best] + list(data.get('oa_locations') or []):
                u = loc.get('url')
                if u and u not in urls:
                    urls.append(u)
            for u in urls[:3]:
                if self._pdf_attempts >= 6:
                    break
                self._pdf_attempts += 1
                abstract = _fetch_pdf_abstract(u)
                if abstract:
                    return abstract
        except Exception as _up_err:
            print(f"  [verify] unpaywall FAIL {doi}: {type(_up_err).__name__}: {str(_up_err)[:150]}")
        return ""


# ── Atomic Fact Decomposer ──────────────────────────────────────────────────

class AtomicFactDecomposer:
    """Decompose citation-bearing paragraphs into atomic factual claims using LLM."""

    DECOMPOSE_PROMPT_ZH = """你是一个学术事实分解助手。将以下段落分解为独立的原子事实论断。

规则：
1. 每个原子论断只包含一个可验证的事实
2. 保留原文的具体数据、方法名、结论
3. 去除主观评价和流程描述
4. 每个论断必须是自包含的（不依赖上下文也能理解）
5. 最多输出5个论断
6. 严格排除：代码/API描述（函数、参数、变量、数据结构操作）、论文元数据（作者、标题、期刊名、DOI、发表年份）、教程/操作步骤、纯历史事件或常识背景陈述（如"20世纪70年代发生了石油危机"这类不含方法、机制、数据、研究发现的时间/事实陈述——但涉及研究方法、模型、机制的论断必须保留）

输出JSON格式：
{"claims": ["论断1", "论断2", ...]}

如果没有可分解的事实论断，输出：{"claims": []}"""

    DECOMPOSE_PROMPT_EN = """You are an academic fact decomposition assistant. Decompose the following paragraph into independent atomic factual claims.

Rules:
1. Each atomic claim contains exactly one verifiable fact
2. Preserve specific data, method names, and conclusions from the original text
3. Remove subjective evaluations and process descriptions
4. Each claim must be self-contained (understandable without context)
5. Output at most 5 claims
6. Strictly exclude: pure historical/common-knowledge statements (time/event facts without methods, mechanisms, data, or research findings — e.g. "an oil crisis occurred in the 1970s"). KEEP claims about research methods, models, or mechanisms.

Output JSON format:
{"claims": ["claim1", "claim2", ...]}

If no decomposable factual claims exist, output: {"claims": []}"""

    def __init__(self, llm_call_fn=None, language: str = "zh"):
        """
        Args:
            llm_call_fn: LLM call function fn(system_prompt, user_prompt) -> str
            language: "zh" or "en"
        """
        self.llm_call_fn = llm_call_fn
        self.language = language

    def decompose(self, contexts: List[CitationContext]) -> List[AtomicClaim]:
        """Decompose citation contexts into atomic claims."""
        if not self.llm_call_fn:
            # Fallback: treat each context as a single claim
            return [
                AtomicClaim(
                    text=ctx.text[:500],
                    source_context=ctx.text,
                    cited_indices=ctx.cited_indices,
                )
                for ctx in contexts
                if _is_verifiable_claim(ctx.text[:500])
            ]

        claims = []
        for ctx in contexts:
            atomic = self._decompose_single(ctx)
            claims.extend(atomic)

        # Filter out code/API descriptions — not verifiable via paper abstracts
        claims = [c for c in claims if _is_verifiable_claim(c.text)]
        return claims

    def _decompose_single(self, ctx: CitationContext) -> List[AtomicClaim]:
        """Decompose a single citation context."""
        system = self.DECOMPOSE_PROMPT_ZH if self.language == "zh" else self.DECOMPOSE_PROMPT_EN

        # Truncate very long contexts
        text = ctx.text[:2000]

        try:
            response = self.llm_call_fn(system, text)
            # Extract JSON from response
            parsed = self._parse_json_response(response)

            return [
                AtomicClaim(
                    text=claim_text,
                    source_context=ctx.text,
                    cited_indices=ctx.cited_indices,
                )
                for claim_text in parsed.get("claims", [])
                if len(claim_text) >= 15  # Minimum claim length
            ]
        except Exception:
            # Fallback: use the whole context as one claim
            return [AtomicClaim(
                text=ctx.text[:500],
                source_context=ctx.text,
                cited_indices=ctx.cited_indices,
            )]

    @staticmethod
    def _parse_json_response(response: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Try to find JSON in the response
        # Handle ```json ... ``` blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))

        # Try direct JSON parse
        # Find the outermost { ... }
        brace_start = response.find('{')
        if brace_start >= 0:
            depth = 0
            for i in range(brace_start, len(response)):
                if response[i] == '{':
                    depth += 1
                elif response[i] == '}':
                    depth -= 1
                    if depth == 0:
                        return json.loads(response[brace_start:i + 1])

        return {"claims": []}


# ── NLI Verifier ─────────────────────────────────────────────────────────────

class NLIVerifier:
    """Verify atomic claims against cited paper abstracts using NLI."""

    NLI_PROMPT_ZH = """你是一个学术事实校验助手。判断文献摘要是否支持给定论断。

论断：{claim}

文献标题：{title}
文献摘要：{abstract}

判断标准：
- entail: 摘要内容明确支持该论断（同一事实/结论）
- contradict: 摘要内容明确反驳该论断
- neutral: 摘要与该论断无关，或无法从摘要判断

输出JSON：
{{"label": "entail/contradict/neutral", "confidence": 0.0-1.0, "explanation": "一句话说明"}}"""

    NLI_PROMPT_EN = """You are an academic fact-checking assistant. Determine whether the paper abstract supports the given claim.

Claim: {claim}

Paper title: {title}
Abstract: {abstract}

Criteria:
- entail: The abstract clearly supports this claim (same fact/conclusion)
- contradict: The abstract clearly refutes this claim
- neutral: The abstract is unrelated to this claim, or cannot be determined from the abstract

Output JSON:
{{"label": "entail/contradict/neutral", "confidence": 0.0-1.0, "explanation": "one-sentence explanation"}}"""

    def __init__(self, llm_call_fn=None, language: str = "zh"):
        self.llm_call_fn = llm_call_fn
        self.language = language

    TITLE_PROMPT_ZH = """你是一个学术事实校验助手。该文献无法获取摘要，只有标题与出处信息。请判断仅凭标题是否能直接支持给定论断。

论断：{claim}

文献标题：{title}
期刊：{journal}（{year}）

判断标准：
- entail: 论断正是该文献标题直接表明的主题/结论（如论断是"存在一项关于X的元分析"而标题即"X: A Meta-Analysis"）
- contradict: 标题与论断明显矛盾
- neutral: 仅凭标题无法判断（多数情况应选此项，宁缺勿滥）

输出JSON：{{"label": "entail/contradict/neutral", "confidence": 0.0-1.0, "explanation": "一句话说明（注明仅标题证据）"}}"""

    TITLE_PROMPT_EN = """You are an academic fact-checking assistant. No abstract is available for this paper — only its title and venue. Judge whether the title alone directly supports the claim.

Claim: {claim}

Paper title: {title}
Journal: {journal} ({year})

Criteria:
- entail: the claim restates exactly what the title declares (e.g. claim "a meta-analysis on X exists" with title "X: A Meta-Analysis")
- contradict: the title clearly contradicts the claim
- neutral: cannot be determined from the title alone (choose this in most cases; when in doubt, be conservative)

Output JSON: {{"label": "entail/contradict/neutral", "confidence": 0.0-1.0, "explanation": "one-sentence explanation (note title-only evidence)"}}"""

    def verify_claim(
        self,
        claim: AtomicClaim,
        references: Dict[int, Reference],
    ) -> ClaimVerification:
        """Verify one atomic claim against its cited references."""
        result = ClaimVerification(claim=claim)

        for ref_idx in claim.cited_indices:
            ref = references.get(ref_idx)
            if not ref:
                continue

            if ref.abstract:
                nli = self._check_nli(claim.text, ref)
            else:
                # No abstract retrievable — fall back to conservative title-level
                # check instead of skipping the reference entirely.
                nli = self._check_nli_title(claim.text, ref)
            nli.ref_index = ref_idx
            result.nli_results.append(nli)

        # Aggregate NLI results
        result.status, result.confidence = self._aggregate(result.nli_results)
        return result

    def _check_nli_title(self, claim_text: str, ref: Reference) -> NLIResult:
        """Conservative title-only NLI for references without abstracts."""
        result = NLIResult(
            claim=claim_text,
            ref_index=ref.index,
            ref_title=ref.title,
            ref_doi=ref.doi,
            evidence="title",
        )

        if not self.llm_call_fn:
            result.label = "neutral"
            result.explanation = "No LLM available for NLI verification"
            return result

        prompt_template = self.TITLE_PROMPT_ZH if self.language == "zh" else self.TITLE_PROMPT_EN
        user_msg = prompt_template.format(
            claim=claim_text,
            title=ref.title,
            journal=ref.raw_text.split(".")[-1].strip() if ref.raw_text else "",
            year=ref.year or "?",
        )

        try:
            response = self.llm_call_fn(
                "You are an academic NLI system. Output only valid JSON.",
                user_msg,
            )
            parsed = AtomicFactDecomposer._parse_json_response(response)

            label = parsed.get("label", "neutral").lower().strip()
            if label not in ("entail", "contradict", "neutral"):
                label = "neutral"

            result.label = label
            result.confidence = float(parsed.get("confidence", 0.5))
            result.explanation = parsed.get("explanation", "")
        except Exception as e:
            result.explanation = f"Title-level check failed: {e}"

        return result

    def _check_nli(self, claim_text: str, ref: Reference) -> NLIResult:
        """Run NLI check for one claim against one reference."""
        result = NLIResult(
            claim=claim_text,
            ref_index=ref.index,
            ref_title=ref.title,
            ref_doi=ref.doi,
        )

        if not self.llm_call_fn:
            result.label = "neutral"
            result.explanation = "No LLM available for NLI verification"
            return result

        prompt_template = self.NLI_PROMPT_ZH if self.language == "zh" else self.NLI_PROMPT_EN
        user_msg = prompt_template.format(
            claim=claim_text,
            title=ref.title,
            abstract=ref.abstract[:800],  # Truncate long abstracts
        )

        try:
            response = self.llm_call_fn(
                "You are an academic NLI system. Output only valid JSON.",
                user_msg,
            )
            parsed = AtomicFactDecomposer._parse_json_response(response)

            label = parsed.get("label", "neutral").lower().strip()
            if label not in ("entail", "contradict", "neutral"):
                label = "neutral"

            result.label = label
            result.confidence = float(parsed.get("confidence", 0.5))
            result.explanation = parsed.get("explanation", "")
        except Exception as e:
            result.explanation = f"NLI check failed: {e}"

        return result

    @staticmethod
    def _aggregate(nli_results: List[NLIResult]) -> Tuple[str, float]:
        """Aggregate NLI results into a final status and confidence.

        Title-only entailment is weaker evidence than abstract entailment:
        it can lift a claim to partially_verified but never to fully verified.
        """
        if not nli_results:
            return "unverified", 0.0

        entails_abs = sum(1 for r in nli_results if r.label == "entail" and r.evidence != "title")
        entails_title = sum(1 for r in nli_results if r.label == "entail" and r.evidence == "title")
        contradicts = sum(1 for r in nli_results if r.label == "contradict")
        total = len(nli_results)

        avg_conf = sum(r.confidence for r in nli_results) / total

        if entails_abs > 0 and contradicts == 0:
            return "verified", min(0.95, avg_conf + 0.1 * (entails_abs + entails_title))
        elif entails_abs > 0 and contradicts > 0:
            return "partially_verified", 0.5
        elif contradicts > 0 and entails_abs == 0:
            return "contradicted", max(0.1, avg_conf - 0.1 * contradicts)
        elif entails_title > 0:
            return "partially_verified", min(0.5, avg_conf)
        else:
            return "unverified", 0.0  # Neutral = no evidence found


def _is_title_only_unverified(cv: "ClaimVerification") -> bool:
    """v0.12.8: True when a claim ended unverified with ONLY title-level
    evidence (no public abstract for every cited reference). Such claims are
    "insufficient evidence" — not wrong, just not confirmable — so the
    confidence score excludes them from its denominator."""
    return (
        cv.status == "unverified"
        and bool(cv.nli_results)
        and all(getattr(n, "evidence", "abstract") == "title" for n in cv.nli_results)
    )


# ── Main Pipeline ────────────────────────────────────────────────────────────

class CitationVerifier:
    """
    Citation-grounded fact verification pipeline.

    Usage:
        verifier = CitationVerifier(
            llm_call_fn=my_llm_fn,
            search_fn=my_search_fn,  # Optional, for abstract fallback
            language="zh",
        )
        report = verifier.verify(final_report_text)
    """

    def __init__(
        self,
        llm_call_fn=None,
        search_fn=None,
        language: str = "zh",
        max_claims: int = 30,
        max_contexts: int = 20,
    ):
        self.language = language
        self.max_claims = max_claims
        self.max_contexts = max_contexts

        self.parser = CitationParser()
        self.resolver = ReferenceResolver(search_fn=search_fn)
        self.decomposer = AtomicFactDecomposer(llm_call_fn=llm_call_fn, language=language)
        self.nli = NLIVerifier(llm_call_fn=llm_call_fn, language=language)

    def _audit_abstracts(self, references: List[Reference]) -> List[Dict[str, Any]]:
        """v0.12.5: check each cached abstract actually belongs to its paper.

        Pre-v0.12.3 title search grafted top-1 abstracts onto the wrong papers,
        and those poisoned abstracts persist in the checkpoint cache — every NLI
        verdict against them is garbage (the recurring low-score incidents).
        One batched LLM call flags mismatches; flagged abstracts are cleared so
        the reference falls back to DOI-exact re-resolution or honest
        title-level evidence. Audit failure is non-fatal (skip silently).
        """
        llm_fn = self.decomposer.llm_call_fn
        if not llm_fn:
            return []
        candidates = [r for r in references if (r.abstract or "").strip()]
        if not candidates:
            return []
        entries = "\n".join(
            f"{i}. TITLE: {(r.title or '')[:150]}\n   ABSTRACT: {(r.abstract or '')[:500]}"
            for i, r in enumerate(candidates, 1)
        )
        if self.language == "zh":
            prompt = (
                "你是学术文献元数据校验员。下面每项给出一篇论文的标题和一段据称属于它的摘要。"
                "判断每段摘要是否真的属于该标题对应的论文（同一研究主题即可，不要求逐字对应；"
                "如果摘要只是引用/出版信息而非论文内容，也判 no）。\n\n"
                "输出JSON：{\"items\": {\"1\": \"yes\", \"2\": \"no\", ...}}\n\n"
                f"论文列表：\n{entries}"
            )
        else:
            prompt = (
                "You are auditing academic paper metadata. For each item, decide whether the "
                "ABSTRACT genuinely belongs to the paper with the given TITLE (same research "
                "topic is enough; answer \"no\" if it is another paper's abstract or mere "
                "citation/publisher metadata).\n\n"
                "Output JSON: {\"items\": {\"1\": \"yes\", \"2\": \"no\", ...}}\n\n"
                f"Items:\n{entries}"
            )
        try:
            parsed = AtomicFactDecomposer._parse_json_response(
                llm_fn("You are an academic metadata auditor. Output only valid JSON.", prompt))
            items = parsed.get("items", {})
            if not isinstance(items, dict):
                return []
            audit = []
            for i, r in enumerate(candidates, 1):
                verdict = str(items.get(str(i), "yes")).strip().lower()
                if verdict.startswith("n"):
                    audit.append({
                        "index": r.index, "title": r.title, "doi": r.doi,
                        "action": "cleared",
                        "reason": "abstract does not match title",
                    })
                    print(f"  [verify] abstract MISMATCH cleared for [{r.index}]: {(r.title or '')[:60]}")
                    r.abstract = ""
            return audit
        except Exception as e:
            print(f"  [verify] abstract audit skipped: {e}")
            return []

    @staticmethod
    def _match_papers_to_text(text: str, ref_dict: Dict[int, Reference]) -> List[int]:
        """Find most relevant paper indices for a text by keyword overlap."""
        text_words = set(re.findall(r'[a-zA-Z]{4,}|[\u4e00-\u9fff]{2,}', text.lower()))

        scored = []
        for idx, ref in ref_dict.items():
            ref_text = (ref.title + " " + ref.abstract).lower()
            ref_words = set(re.findall(r'[a-zA-Z]{4,}|[\u4e00-\u9fff]{2,}', ref_text))
            overlap = len(text_words & ref_words)
            if overlap > 0:
                scored.append((overlap, idx))

        scored.sort(reverse=True)
        # Return top 2 most relevant papers
        return [idx for _, idx in scored[:2]] if scored else []

    def verify(
        self,
        report_text: str,
        papers_data: Optional[List[Dict[str, Any]]] = None,
    ) -> CitationVerificationReport:
        """
        Run the full citation-grounded verification pipeline.

        Args:
            report_text: The final report markdown text
            papers_data: Optional pre-fetched paper data from the pipeline's search phase.
                         Each dict should have: title, doi, abstract, authors, year, journal.
                         When provided, skips reference parsing/resolution and uses these directly.

        Returns:
            CitationVerificationReport with per-claim verification results
        """
        report = CitationVerificationReport()

        # ── Build reference list ──
        if papers_data:
            # Use pre-fetched papers from pipeline search (have abstracts already)
            references = []
            for i, p in enumerate(papers_data, 1):
                ref = Reference(
                    index=i,
                    raw_text=f"{', '.join(p.get('authors', ['Unknown'])[:3])} ({p.get('year', '')}). {p.get('title', '')}. {p.get('journal', '')}",
                    doi=p.get("doi", ""),
                    title=p.get("title", ""),
                    authors=", ".join(p.get("authors", [])[:3]),
                    year=str(p.get("year", "")),
                    abstract=p.get("abstract", ""),
                )
                references.append(ref)
            report.total_references = len(references)
            # v0.12.7: a cached "abstract" that is really citation info (own
            # title echoed + vol/pp markers, short) can slip past the LLM
            # audit since it mentions the right title — scrub it here so
            # resolve() below re-fetches the real abstract.
            for r in references:
                if r.abstract and _looks_like_citation_info(r.abstract, r.title):
                    r.abstract = ""
            # Backfill missing abstracts (Crossref-sourced papers usually lack
            # them) instead of silently verifying against nothing.
            report.resolved_references = self.resolver.resolve(references)
            # v0.12.5: cached abstracts may belong to the WRONG paper (grafted
            # by pre-v0.12.3 title search and then persisted in checkpoints) —
            # audit them, quarantine mismatches, re-resolve via DOI-exact
            # sources, and write the cleaned abstracts back into the caller's
            # cache so the fix persists across re-runs.
            report.abstract_audit = self._audit_abstracts(references)
            if report.abstract_audit:
                self.resolver.resolve(references)
                for _a in report.abstract_audit:
                    _r = next((r for r in references if r.index == _a["index"]), None)
                    if _r is not None and _r.abstract:
                        _a["action"] = "replaced"
                report.resolved_references = sum(1 for r in references if r.abstract)
            for _r, _p in zip(references, papers_data):
                _p["abstract"] = _r.abstract
        else:
            # Parse references from bibliography
            references = self.parser.extract_references(report_text)
            report.total_references = len(references)

            if not references:
                report.summary = "No reference list found in report"
                return report

            # Resolve references (fetch abstracts)
            resolved = self.resolver.resolve(references)
            report.resolved_references = resolved

        # Build lookup dict
        ref_dict = {r.index: r for r in references}

        # ── Extract citation contexts ──
        contexts = self.parser.extract_citation_contexts(report_text)
        report.total_citations = len(contexts)

        if not contexts and not papers_data:
            report.summary = "No citation markers found in report text"
            return report

        # If no citation contexts but we have papers_data, extract all substantive
        # paragraphs as contexts (they may reference papers without [N] markers)
        if not contexts and papers_data:
            for para in report_text.split("\n\n"):
                para = para.strip()
                if len(para) < 60 or para.startswith("#"):
                    continue
                # Skip pure list paragraphs
                if para.count("\n- ") > 3 or para.count("\n* ") > 3:
                    continue
                # Skip code-dense / non-verifiable paragraphs
                if not _is_verifiable_claim(para):
                    continue
                # Match paragraph to most relevant papers by keyword overlap
                # instead of assigning ALL papers (which causes false neutral NLI)
                relevant_indices = self._match_papers_to_text(para, ref_dict)
                if relevant_indices:
                    contexts.append(CitationContext(
                        text=para,
                        cited_indices=relevant_indices,
                        section="",
                    ))
            contexts = contexts[:self.max_contexts]

        # Limit contexts to avoid excessive LLM calls
        contexts = contexts[:self.max_contexts]

        # ── Decompose into atomic claims ──
        claims = self.decomposer.decompose(contexts)
        claims = claims[:self.max_claims]
        report.total_claims = len(claims)

        if not claims:
            report.summary = "No atomic claims decomposed from citation contexts"
            return report

        # ── NLI verification ──
        for claim in claims:
            cv = self.nli.verify_claim(claim, ref_dict)
            report.claim_verifications.append(cv)

        # ── Aggregate ──
        report.verified = sum(1 for cv in report.claim_verifications if cv.status == "verified")
        report.partially_verified = sum(1 for cv in report.claim_verifications if cv.status == "partially_verified")
        report.contradicted = sum(1 for cv in report.claim_verifications if cv.status == "contradicted")
        report.unverified = sum(1 for cv in report.claim_verifications if cv.status == "unverified")
        # v0.12.8: title-only unverified claims are insufficient evidence —
        # they still count in `unverified` and appear per-claim, but are
        # excluded from the confidence denominator.
        report.insufficient_evidence = sum(
            1 for cv in report.claim_verifications if _is_title_only_unverified(cv))

        scored = [cv for cv in report.claim_verifications if not _is_title_only_unverified(cv)]
        if scored:
            weighted = sum(
                1.0 if cv.status == "verified"
                else 0.5 if cv.status == "partially_verified"
                else 0.0
                for cv in scored
            )
            report.overall_confidence = weighted / len(scored)
        else:
            report.overall_confidence = 0.0

        src = "cached papers" if papers_data else "bibliography"
        report.summary = (
            f"Verified {report.total_claims} claims from {report.total_citations} citation contexts "
            f"({report.resolved_references}/{report.total_references} references from {src}): "
            f"{report.verified} verified, {report.partially_verified} partially verified, "
            f"{report.contradicted} contradicted, {report.unverified} unverified. "
        )
        # v0.12.8
        if report.insufficient_evidence:
            report.summary += (
                f"{report.insufficient_evidence} claim(s) had title-level evidence only "
                f"(no public abstract) — counted as insufficient evidence, excluded from scoring. "
            )
        report.summary += f"Overall confidence: {report.overall_confidence:.0%}"
        if report.abstract_audit:
            report.summary += (f" Abstract audit: {len(report.abstract_audit)} mismatched "
                               f"cached abstract(s) quarantined.")

        return report
