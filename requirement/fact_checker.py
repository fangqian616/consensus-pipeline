"""
事实校验模块 — Consensus Pipeline v4.3

共识提取后，调用外部检索工具交叉验证关键结论，
为共识结论锚定具体文献DOI。

v4.3: 修复中文分词失效（单字符滑动窗口兜底）
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class FactCheckResult:
    """单条结论的校验结果"""
    claim: str                                       # 原始结论
    status: str = "unverified"                       # verified / partially_verified / contradicted / unverified
    supporting_dois: List[str] = field(default_factory=list)   # 支持的文献DOI
    contradicting_dois: List[str] = field(default_factory=list) # 反对的文献DOI
    confidence: float = 0.0                          # 置信度 0-1
    notes: str = ""                                  # 校验备注


@dataclass
class FactCheckReport:
    """事实校验报告"""
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
    从文本中提取n-gram，兼容中文和英文。
    
    英文：按空格分词后取n-gram
    中文：按单字符滑动窗口取n-gram
    """
    text = text.lower().strip()
    # 判断是否主要是中文
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    total_chars = sum(1 for c in text if c.strip())
    
    if chinese_chars > total_chars * 0.3:
        # 中文为主：字符级n-gram
        chars = [c for c in text if c.strip()]
        if len(chars) < n:
            return {"".join(chars)} if chars else set()
        return {"".join(chars[i:i+n]) for i in range(len(chars) - n + 1)}
    else:
        # 英文为主：词级n-gram
        words = [w for w in text.split() if len(w) > 2]
        if len(words) < n:
            return set(words)
        return {" ".join(words[i:i+n]) for i in range(len(words) - n + 1)}


class FactChecker:
    """
    事实校验

    位置：Phase 7（共识提取）之后，Phase 8（结构化输出）之前

    职责：
    1. 提取共识结论中的可验证事实
    2. 调用检索工具交叉验证
    3. 为结论锚定具体文献DOI
    4. 标注置信度
    """

    def __init__(self, search_fn=None, llm_call_fn=None):
        """
        Args:
            search_fn: 检索函数，签名为 fn(query, max_results) -> List[Dict]
                       每个Dict至少包含 title, doi, abstract 字段
            llm_call_fn: LLM调用函数
        """
        self.search_fn = search_fn
        self.llm_call_fn = llm_call_fn

    def check(self, consensus_points: List[str]) -> FactCheckReport:
        """
        校验共识结论列表。

        Args:
            consensus_points: 共识提取的结论列表

        Returns:
            FactCheckReport: 校验报告
        """
        results = []

        for point in consensus_points:
            result = self._verify_point(point)
            results.append(result)

        # 计算整体置信度
        if results:
            overall = sum(r.confidence for r in results) / len(results)
        else:
            overall = 0.0

        # 生成摘要
        verified = sum(1 for r in results if r.status == "verified")
        partial = sum(1 for r in results if r.status == "partially_verified")
        contradicted = sum(1 for r in results if r.status == "contradicted")
        unverified = sum(1 for r in results if r.status == "unverified")

        summary = (
            f"共校验{len(results)}条结论："
            f"{verified}条已验证，{partial}条部分验证，"
            f"{contradicted}条有反面证据，{unverified}条未验证。"
            f"整体置信度：{overall:.0%}"
        )

        return FactCheckReport(
            results=results,
            overall_confidence=overall,
            summary=summary,
        )

    def _verify_point(self, point: str) -> FactCheckResult:
        """校验单条结论"""
        result = FactCheckResult(claim=point)

        if self.search_fn:
            # 使用检索工具验证
            try:
                search_results = self.search_fn(point, max_results=5)
                supporting = []
                contradicting = []

                for paper in search_results:
                    doi = paper.get("doi", "")
                    title = paper.get("title", "")
                    abstract = paper.get("abstract", "")

                    # 判断是支持还是反对
                    stance = self._judge_stance(point, title, abstract)
                    if stance == "supporting" and doi:
                        supporting.append(doi)
                    elif stance == "contradicting" and doi:
                        contradicting.append(doi)

                result.supporting_dois = supporting
                result.contradicting_dois = contradicting

                # 确定状态
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
                result.notes = f"检索验证失败：{str(e)}"

        elif self.llm_call_fn:
            # 使用LLM判断
            result = self._verify_with_llm(point)

        else:
            # 无外部工具，标记为未验证
            result.status = "unverified"
            result.notes = "无可用的检索工具或LLM进行验证"

        return result

    def _judge_stance(self, claim: str, title: str, abstract: str) -> str:
        """
        判断论文对结论的态度。
        
        v4.3: 使用n-gram重叠替代空格分词，兼容中英文。
        """
        if not self.llm_call_fn:
            # n-gram关键词匹配（兼容中英文）
            text = f"{title} {abstract}".lower()
            claim_ngrams = _extract_ngrams(claim, n=2)
            
            if not claim_ngrams:
                return "neutral"
            
            overlap = sum(1 for ng in claim_ngrams if ng in text)
            ratio = overlap / len(claim_ngrams)

            if ratio > 0.3:
                return "supporting"
            return "neutral"

        # LLM判断
        system_prompt = """你是学术事实校验助手。判断论文摘要是否支持给定的结论。
只输出一个词：supporting / contradicting / neutral"""

        user_msg = f"结论：{claim}\n\n论文标题：{title}\n摘要：{abstract[:500]}"
        response = self.llm_call_fn(system_prompt, user_msg).strip().lower()

        if "supporting" in response:
            return "supporting"
        elif "contradicting" in response:
            return "contradicting"
        return "neutral"

    def _verify_with_llm(self, point: str) -> FactCheckResult:
        """使用LLM进行校验"""
        result = FactCheckResult(claim=point)

        system_prompt = """你是学术事实校验助手。评估以下结论的可信度：
1. 这个结论在学术文献中是否被广泛支持？
2. 是否有已知的反面证据？
3. 置信度估计（0-1）

请输出JSON：
{"status": "verified/partially_verified/contradicted/unverified", "confidence": 0.8, "notes": "说明"}"""

        response = self.llm_call_fn(system_prompt, point)
        try:
            parsed = json.loads(response)
            result.status = parsed.get("status", "unverified")
            result.confidence = parsed.get("confidence", 0.0)
            result.notes = parsed.get("notes", "")
        except json.JSONDecodeError:
            result.notes = response

        return result
