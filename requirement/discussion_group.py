"""
需求讨论组模块 — Consensus Pipeline v4.0

基于结构化需求组建讨论组，从不同角度审视需求，
找出遗漏/矛盾/补充点，输出讨论纪要。
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .structurer import StructuredRequirement


@dataclass
class DiscussionOpinion:
    """单个角色的观点"""
    role: str
    opinion: str
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DiscussionResult:
    """讨论组结果"""
    opinions: List[DiscussionOpinion] = field(default_factory=list)
    consensus_points: List[str] = field(default_factory=list)      # 达成一致的点
    disagreements: List[Dict[str, str]] = field(default_factory=list)  # 分歧点
    supplements: List[str] = field(default_factory=list)           # 补充建议
    refined_requirement: Dict[str, Any] = field(default_factory=dict)  # 修正后的需求

    def to_dict(self) -> dict:
        import dataclasses
        def _convert(obj):
            if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
                return dataclasses.asdict(obj)
            return obj
        return {
            "opinions": [_convert(o) for o in self.opinions],
            "consensus_points": self.consensus_points,
            "disagreements": self.disagreements,
            "supplements": self.supplements,
            "refined_requirement": self.refined_requirement,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ============ 角色Prompt模板 ============

ROLE_PROMPTS = {
    "方法论审查": """你是方法论审查专家。审视以下需求的方法路径是否合理：
1. 调研路径是否覆盖了关键环节？有没有遗漏？
2. 方法选择是否和目标匹配？有没有更好的替代方案？
3. 从方法论角度，这个需求的核心假设是什么？假设是否合理？

请给出你的观点、担忧和建议。""",

    "反方视角": """你是反方视角专家。假设这个需求的方向可能有问题：
1. 最可能的失败原因是什么？
2. 哪些假设可能是错的？
3. 有没有更值得探索的替代方向？

请给出你的观点、担忧和建议。""",

    "落地可行性": """你是落地可行性专家。评估以下需求的可执行性：
1. 给定现有工具和数据源，能实现吗？
2. 最大的瓶颈在哪里？
3. 哪些目标需要降级或调整？

请给出你的观点、担忧和建议。""",

    "文献覆盖度审查": """你是文献覆盖度审查专家。评估检索策略的完备性：
1. 是否有遗漏的重要检索源？
2. 关键词策略是否能覆盖核心文献？
3. 时间范围和语种限制是否合理？

请给出你的观点、担忧和建议。""",

    "统计方法质疑": """你是统计方法质疑专家。从方法论严格性角度审视：
1. 提到的方法是否适合解决目标问题？
2. 有没有内生性、选择性偏差等常见问题？
3. 需要什么样的稳健性检验？

请给出你的观点、担忧和建议。""",

    "引用链完整性": """你是引用链完整性审查专家：
1. 核心文献的引用网络是否被覆盖？
2. 是否有可能遗漏了奠基性论文？
3. 从引用结构看，有没有隐藏的研究脉络？

请给出你的观点、担忧和建议。""",

    "受众分析": """你是受众分析专家：
1. 目标受众的核心需求是什么？
2. 当前方案是否满足受众期望？
3. 有没有受众视角的盲点？

请给出你的观点、担忧和建议。""",

    "平台适配": """你是平台适配专家：
1. 不同平台的技术约束是什么？
2. 当前方案是否适配目标平台？
3. 需要做哪些适配调整？

请给出你的观点、担忧和建议。""",

    "视觉风格一致性": """你是视觉风格一致性专家：
1. 各视觉要素的风格是否统一？
2. 有没有风格冲突的风险？
3. 如何确保最终产出的视觉一致性？

请给出你的观点、担忧和建议。""",
}


class DiscussionGroup:
    """
    需求讨论组

    组建讨论组，各角色独立审视需求，
    找出遗漏/矛盾/补充点，输出讨论纪要。
    """

    def __init__(self, llm_call_fn=None):
        """
        Args:
            llm_call_fn: LLM调用函数，签名为 fn(system_prompt, user_message) -> str
                         如果为None，使用规则引擎生成观点
        """
        self.llm_call_fn = llm_call_fn

    def discuss(
        self,
        requirement: StructuredRequirement,
        extra_roles: Optional[List[Dict[str, str]]] = None,
        rounds: int = 1,
    ) -> DiscussionResult:
        """
        执行讨论。

        Args:
            requirement: 结构化需求
            extra_roles: 额外角色（覆盖默认的领域特化角色）
            rounds: 讨论轮数（目前只支持1轮）

        Returns:
            DiscussionResult: 讨论结果
        """
        # 确定参与角色
        roles = list(requirement.suggested_roles)
        if extra_roles:
            roles.extend(extra_roles)

        # 各角色独立给出观点
        opinions = []
        for role_info in roles:
            role_name = role_info["role"]
            opinion = self._generate_opinion(role_name, requirement)
            opinions.append(opinion)

        # 汇总讨论结果
        result = self._aggregate(opinions, requirement)
        return result

    def _generate_opinion(
        self, role_name: str, requirement: StructuredRequirement
    ) -> DiscussionOpinion:
        """单个角色生成观点"""
        if self.llm_call_fn:
            return self._generate_opinion_with_llm(role_name, requirement)
        return self._generate_opinion_rule_based(role_name, requirement)

    def _generate_opinion_rule_based(
        self, role_name: str, requirement: StructuredRequirement
    ) -> DiscussionOpinion:
        """基于规则的观点生成"""
        prompt = ROLE_PROMPTS.get(role_name, f"你是{role_name}专家，请审视该需求并给出观点。")

        # 基于角色和需求内容生成结构化观点
        concerns = []
        suggestions = []

        if role_name == "方法论审查":
            if not requirement.key_questions:
                concerns.append("需求中缺少明确的核心问题")
                suggestions.append("建议明确2-3个必须回答的核心问题")
            if not requirement.constraints.get("methodology"):
                suggestions.append("建议明确方法论偏好，避免检索结果过于分散")

        elif role_name == "反方视角":
            if len(requirement.objectives) > 5:
                concerns.append("目标过多可能导致调研不聚焦")
                suggestions.append("建议缩减到3个核心目标")
            concerns.append("需要确认是否有预设偏见影响调研方向")

        elif role_name == "落地可行性":
            if not requirement.constraints.get("time_range"):
                concerns.append("未指定时间范围，检索结果可能过多")
                suggestions.append("建议限定近3-5年")
            if requirement.domain_code == "academic_research":
                suggestions.append("学术检索需要API配置，请确保arXiv/SS/OA可用")

        elif role_name == "文献覆盖度审查":
            if requirement.domain_code == "academic_research":
                sources = requirement.domain_specific.get("search_sources", [])
                if len(sources) < 2:
                    concerns.append("检索源单一，可能遗漏重要文献")
                    suggestions.append("建议至少使用3个检索源")

        elif role_name == "统计方法质疑":
            if not requirement.constraints.get("methodology"):
                concerns.append("未指定方法论偏好，难以评估统计适用性")
                suggestions.append("建议区分计量方法和ML方法的使用场景")

        opinion_text = f"作为{role_name}，我审视了该需求。"
        if concerns:
            opinion_text += f" 主要关注：{'；'.join(concerns)}"
        if suggestions:
            opinion_text += f" 建议：{'；'.join(suggestions)}"
        if not concerns and not suggestions:
            opinion_text += " 当前需求方向合理，无重大风险。"

        return DiscussionOpinion(
            role=role_name,
            opinion=opinion_text,
            concerns=concerns,
            suggestions=suggestions,
        )

    def _generate_opinion_with_llm(
        self, role_name: str, requirement: StructuredRequirement
    ) -> DiscussionOpinion:
        """使用LLM生成观点"""
        system_prompt = ROLE_PROMPTS.get(
            role_name,
            f"你是{role_name}专家，请审视该需求并给出观点。"
        )

        user_msg = f"""请审视以下需求文档，给出你的专业观点：

{requirement.to_json()}

请用以下JSON格式输出：
{{"opinion": "你的总体观点", "concerns": ["担忧1", "担忧2"], "suggestions": ["建议1", "建议2"]}}"""

        response = self.llm_call_fn(system_prompt, user_msg)

        try:
            parsed = json.loads(response)
            return DiscussionOpinion(
                role=role_name,
                opinion=parsed.get("opinion", response),
                concerns=parsed.get("concerns", []),
                suggestions=parsed.get("suggestions", []),
            )
        except json.JSONDecodeError:
            return DiscussionOpinion(
                role=role_name,
                opinion=response,
            )

    def _aggregate(
        self,
        opinions: List[DiscussionOpinion],
        requirement: StructuredRequirement,
    ) -> DiscussionResult:
        """汇总各角色观点，提取共识和分歧"""
        consensus_points = []
        disagreements = []
        supplements = []

        # 找出多个角色共同关注的问题 → 共识
        all_concerns = {}
        for op in opinions:
            for c in op.concerns:
                all_concerns[c] = all_concerns.get(c, 0) + 1

        for concern, count in all_concerns.items():
            if count >= 2:
                consensus_points.append(f"多方共识：{concern}")

        # 找出冲突建议 → 分歧
        suggestion_themes = {}
        for op in opinions:
            for s in op.suggestions:
                # 简单提取关键词
                key = s[:20]
                suggestion_themes[key] = suggestion_themes.get(key, [])
                suggestion_themes[key].append(op.role)

        # 补充建议
        for op in opinions:
            for s in op.suggestions:
                supplements.append(f"[{op.role}] {s}")

        # 修正需求
        refined = requirement.to_dict()
        if consensus_points:
            refined["_discussion_notes"] = consensus_points

        return DiscussionResult(
            opinions=opinions,
            consensus_points=consensus_points,
            disagreements=disagreements,
            supplements=supplements,
            refined_requirement=refined,
        )
