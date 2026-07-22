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
    overall_confidence: float = 0.0
    summary: str = ""

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
    def _flush_paragraph(cls, lines: List[str], section: str, contexts: List[CitationContext]):
        text = ' '.join(lines)
        # Skip code-dense paragraphs — not verifiable factual claims
        if not _is_verifiable_claim(text):
            return
        cited = cls._extract_cited_indices(text)
        if cited:
            contexts.append(CitationContext(
                text=text,
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
        for ref in references:
            if ref.abstract:
                resolved += 1
                continue

            # Try CrossRef first (if DOI available)
            if ref.doi:
                abstract = self._fetch_crossref(ref.doi)
                if abstract:
                    ref.abstract = abstract
                    resolved += 1
                    continue

            # Fallback: academic search by title
            if ref.title and self.search_fn:
                abstract = self._search_by_title(ref.title)
                if abstract:
                    ref.abstract = abstract
                    resolved += 1

        return resolved

    def _fetch_crossref(self, doi: str) -> str:
        """Fetch abstract from CrossRef API."""
        try:
            import urllib.request
            import urllib.error

            url = f"https://api.crossref.org/works/{doi}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'ConsensusPipeline/1.0 (mailto:research@example.com)',
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
        except Exception:
            return ""

    def _search_by_title(self, title: str) -> str:
        """Search for paper by title and return first result's abstract."""
        if not self.search_fn:
            return ""
        try:
            results = self.search_fn(title, max_results=1)
            if results:
                return results[0].get('abstract', '')
        except Exception:
            pass
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
6. 严格排除：代码/API描述（函数、参数、变量、数据结构操作）、论文元数据（作者、标题、期刊名、DOI、发表年份）、教程/操作步骤

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
            # Fallback: treat each context paragraph as a single claim
            return [
                AtomicClaim(
                    text=ctx.text[:500],
                    source_context=ctx.text,
                    cited_indices=ctx.cited_indices,
                )
                for ctx in contexts
                if not _is_verifiable_claim(ctx.text[:500])
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

    def verify_claim(
        self,
        claim: AtomicClaim,
        references: Dict[int, Reference],
    ) -> ClaimVerification:
        """Verify one atomic claim against its cited references."""
        result = ClaimVerification(claim=claim)

        for ref_idx in claim.cited_indices:
            ref = references.get(ref_idx)
            if not ref or not ref.abstract:
                continue

            nli = self._check_nli(claim.text, ref)
            nli.ref_index = ref_idx
            result.nli_results.append(nli)

        # Aggregate NLI results
        result.status, result.confidence = self._aggregate(result.nli_results)
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
        """Aggregate NLI results into a final status and confidence."""
        if not nli_results:
            return "unverified", 0.0

        entails = sum(1 for r in nli_results if r.label == "entail")
        contradicts = sum(1 for r in nli_results if r.label == "contradict")
        total = len(nli_results)

        avg_conf = sum(r.confidence for r in nli_results) / total

        if entails > 0 and contradicts == 0:
            return "verified", min(0.95, avg_conf + 0.1 * entails)
        elif entails > 0 and contradicts > 0:
            return "partially_verified", 0.5
        elif contradicts > 0 and entails == 0:
            return "contradicted", max(0.1, avg_conf - 0.1 * contradicts)
        else:
            return "unverified", avg_conf * 0.3  # Low confidence for neutral


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
            report.resolved_references = sum(1 for r in references if r.abstract)
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
            all_indices = list(ref_dict.keys())
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
                contexts.append(CitationContext(
                    text=para,
                    cited_indices=all_indices,  # Verify against all papers
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

        if report.claim_verifications:
            report.overall_confidence = sum(
                cv.confidence for cv in report.claim_verifications
            ) / len(report.claim_verifications)

        src = "cached papers" if papers_data else "bibliography"
        report.summary = (
            f"Verified {report.total_claims} claims from {report.total_citations} citation contexts "
            f"({report.resolved_references}/{report.total_references} references from {src}): "
            f"{report.verified} verified, {report.partially_verified} partially verified, "
            f"{report.contradicted} contradicted, {report.unverified} unverified. "
            f"Overall confidence: {report.overall_confidence:.0%}"
        )

        return report
