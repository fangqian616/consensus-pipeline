"""
Fact-Checking Module — Consensus Pipeline v4.3

After consensus extraction, calls external search tools to cross-validate key conclusions,
anchoring consensus conclusions to specific literature DOIs.
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FactCheckResult:
    """Verification result for a single conclusion"""
    claim: str                                       # Original claim
    status: str = "unverified"                       # verified / partially_verified / contradicted / unverified
    supporting_dois: List[str] = field(default_factory=list)   # Supporting literature DOIs
    contradicting_dois: List[str] = field(default_factory=list) # Contradicting literature DOIs
    confidence: float = 0.0                          # Confidence 0-1
    notes: str = ""                                  # Verification notes


@dataclass
class FactCheckReport:
    """Fact-check report"""
    results: List[FactCheckResult] = field(default_factory=list)
    overall_confidence: float = 0.0
    summary: str = ""

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def _extract_ngrams(text: str, n: int = 2) -> set:
    """
    Extract n-grams from text, supporting both Chinese and English.
    
    English: word-level n-grams after space tokenization
    Chinese: character-level n-grams via sliding window
    """
    text = text.lower().strip()
    # Determine if text is primarily Chinese
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = sum(1 for c in text if c.strip())
    
    if chinese_chars > total_chars * 0.3:
        # Chinese-dominant: character-level n-grams
        chars = [c for c in text if c.strip()]
        if len(chars) < n:
            return {"".join(chars)} if chars else set()
        return {"".join(chars[i:i+n]) for i in range(len(chars) - n + 1)}
    else:
        # English-dominant: word-level n-grams
        words = [w for w in text.split() if len(w) > 2]
        if len(words) < n:
            return set(words)
        return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


class FactChecker:
    """
    Fact-Checking

    Position: after Phase 7 (Consensus Extraction), before Phase 8 (Structured Output)

    Responsibilities:
    1. Extract verifiable facts from consensus conclusions
    2. Call search tools for cross-validation
    3. Anchor conclusions to specific literature DOIs
    4. Label confidence levels
    """

    def __init__(self, search_fn=None, llm_call_fn=None):
        """
        Args:
            search_fn: Search function with signature fn(query, max_results) -> List[Dict]
                       Each Dict must contain at least title, doi, abstract fields
            llm_call_fn: LLM call function
        """
        self.search_fn = search_fn
        self.llm_call_fn = llm_call_fn

    def check(self, consensus_points: List[str]) -> FactCheckReport:
        """
        Verify a list of consensus conclusions.

        Args:
            consensus_points: List of conclusions from consensus extraction

        Returns:
            FactCheckReport: Verification report
        """
        results = []

        for point in consensus_points:
            result = self._verify_point(point)
            results.append(result)

        # Calculate overall confidence
        if results:
            overall = sum(r.confidence for r in results) / len(results)
        else:
            overall = 0.0

        # Generate summary
        verified = sum(1 for r in results if r.status == "verified")
        partial = sum(1 for r in results if r.status == "partially_verified")
        contradicted = sum(1 for r in results if r.status == "contradicted")
        unverified = sum(1 for r in results if r.status == "unverified")

        summary = (
            f"Verified {len(results)} conclusions: "
            f"{verified} verified, {partial} partially verified, "
            f"{contradicted} with counter-evidence, {unverified} unverified. "
            f"Overall confidence: {overall:.0%}"
        )

        return FactCheckReport(
            results=results,
            overall_confidence=overall,
            summary=summary,
        )

    def _verify_point(self, point: str) -> FactCheckResult:
        """Verify a single conclusion"""
        result = FactCheckResult(claim=point)

        if self.search_fn:
            # Verify using search tool
            try:
                search_results = self.search_fn(point, max_results=5)
                supporting = []
                contradicting = []

                for paper in search_results:
                    doi = paper.get("doi", "")
                    title = paper.get("title", "")
                    abstract = paper.get("abstract", "")

                    # Determine supporting or contradicting stance
                    stance = self._judge_stance(point, title, abstract)
                    if stance == "supporting" and doi:
                        supporting.append(doi)
                    elif stance == "contradicting" and doi:
                        contradicting.append(doi)

                result.supporting_dois = supporting
                result.contradicting_dois = contradicting

                # Determine status
                if supporting and not contradicting:
                    result.status = "verified"
                    result.confidence = min(0.9, 0.5 + 0.1 * len(supporting))
                elif supporting and contradicting:
                    result.status = "partially_verified"
                    result.confidence = 0.5
                elif contradicting and not supporting:
                    result.status = "contradicted"
                    result.confidence = 0.2
                else:
                    result.status = "unverified"

            except Exception as e:
                result.notes = f"Search verification failed: {str(e)}"

        elif self.llm_call_fn:
            # Verify using LLM
            result = self._verify_with_llm(point)

        else:
            # No external tools available, mark as unverified
            result.status = "unverified"
            result.notes = "No search tool or LLM available for verification"

        return result

    def _judge_stance(self, claim: str, title: str, abstract: str) -> str:
        """
        Determine the paper's stance toward a conclusion.
        
        v4.3: Uses n-gram overlap instead of space tokenization, compatible with both CJK and English.
        """
        if not self.llm_call_fn:
            # n-gram keyword matching (CJK/English compatible)
            text = f"{title} {abstract}".lower()
            claim_ngrams = _extract_ngrams(claim, n=2)
            
            if not claim_ngrams:
                return "neutral"
            
            overlap = sum(1 for ng in claim_ngrams if ng in text)
            ratio = overlap / len(claim_ngrams)

            if ratio > 0.3:
                return "supporting"
            return "neutral"

        # LLM judgment
        system_prompt = """You are an academic fact-checking assistant. Determine whether the paper abstract supports the given conclusion.
Output only one word: supporting / contradicting / neutral"""

        user_msg = f"Conclusion: {claim}\n\nPaper title: {title}\nAbstract: {abstract[:500]}"
        response = self.llm_call_fn(system_prompt, user_msg).strip().lower()

        if "supporting" in response:
            return "supporting"
        elif "contradicting" in response:
            return "contradicting"
        return "neutral"

    def _verify_with_llm(self, point: str) -> FactCheckResult:
        """Verify using LLM"""
        result = FactCheckResult(claim=point)

        system_prompt = """You are an academic fact-checking assistant. Evaluate the credibility of the following conclusion:
1. Is this conclusion widely supported in academic literature?
2. Are there known counter-evidence?
3. Confidence estimate (0-1)

Output JSON:
{"status": "verified/partially_verified/contradicted/unverified", "confidence": 0.8, "notes": "explanation"}"""

        response = self.llm_call_fn(system_prompt, point)
        try:
            parsed = json.loads(response)
            result.status = parsed.get("status", "unverified")
            result.confidence = parsed.get("confidence", 0.0)
            result.notes = parsed.get("notes", "")
        except json.JSONDecodeError:
            result.notes = response

        return result
