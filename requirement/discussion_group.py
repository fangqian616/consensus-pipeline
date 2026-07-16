"""
Requirement Discussion Group Module — Consensus Pipeline v4.0

Forms discussion groups based on structured requirements, examining requirements from different angles,
identifying omissions/contradictions/supplements, and outputting discussion minutes.
"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .structurer import StructuredRequirement


@dataclass
class DiscussionOpinion:
    """Single role viewpoint"""
    role: str
    opinion: str
    concerns: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class DiscussionResult:
    """Discussion group result"""
    opinions: List[DiscussionOpinion] = field(default_factory=list)
    consensus_points: List[str] = field(default_factory=list)      # Consensus points
    disagreements: List[Dict[str, str]] = field(default_factory=list)  # Disagreement points
    supplements: List[str] = field(default_factory=list)           # Supplementary suggestions
    refined_requirement: Dict[str, Any] = field(default_factory=dict)  # Refined requirement

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


# ============ Role Prompt Templates ============

ROLE_PROMPTS = {
    "Methodology Review": """You are a methodology review expert. Examine whether the methodological path in the following requirement is sound:
1. Does the research path cover key stages? Any omissions?
2. Does the method choice match the objectives? Are there better alternatives?
3. From a methodological perspective, what are the core assumptions? Are they reasonable?

Please provide your views, concerns, and recommendations.""",

    "Devil's Advocate": """You are a devil's advocate expert. Assume this requirement's direction may be flawed:
1. What is the most likely reason for failure?
2. Which assumptions might be wrong?
3. Are there more worthwhile alternative directions?

Please provide your views, concerns, and recommendations.""",

    "Feasibility Assessment": """You are a feasibility assessment expert. Evaluate the executability of the following requirement:
1. Given current tools and data sources, is it achievable?
2. Where is the biggest bottleneck?
3. Which objectives need to be downgraded or adjusted?

Please provide your views, concerns, and recommendations.""",

    "Literature Coverage Review": """You are a literature coverage review expert. Evaluate the completeness of the search strategy:
1. Are there important search sources missing?
2. Can the keyword strategy cover core literature?
3. Are the time range and language restrictions reasonable?

Please provide your views, concerns, and recommendations.""",

    "Statistical Method Scrutiny": """You are a statistical method scrutiny expert. Examine from a methodological rigor perspective:
1. Are the mentioned methods suitable for solving the target problem?
2. Are there common issues like endogeneity, selection bias?
3. What kind of robustness checks are needed?

Please provide your views, concerns, and recommendations.""",

    "Citation Chain Integrity": """You are a citation chain integrity review expert:
1. Is the citation network of core literature covered?
2. Could foundational papers be missing?
3. From the citation structure, are there hidden research threads?

Please provide your views, concerns, and recommendations.""",

    "Audience Analysis": """You are an audience analysis expert:
1. What are the core needs of the target audience?
2. Does the current plan meet audience expectations?
3. Are there blind spots from the audience perspective?

Please provide your views, concerns, and recommendations.""",

    "Platform Adaptation": """You are a platform adaptation expert:
1. What are the technical constraints of different platforms?
2. Does the current plan fit the target platform?
3. What adaptation adjustments are needed?

Please provide your views, concerns, and recommendations.""",

    "Visual Style Consistency": """You are a visual style consistency expert:
1. Is the style of visual elements unified?
2. Are there risks of style conflicts?
3. How to ensure visual consistency in the final output?

Please provide your views, concerns, and recommendations.""",
}


class DiscussionGroup:
    """
    Requirement Discussion Group

    Forms a discussion group where each role independently examines the requirement,
    identifying omissions/contradictions/supplements, and outputting discussion minutes.
    """

    def __init__(self, llm_call_fn=None):
        """
        Args:
            llm_call_fn: LLM call function with signature fn(system_prompt, user_message) -> str
                         If None, uses rule engine to generate viewpoints
        """
        self.llm_call_fn = llm_call_fn

    def discuss(
        self,
        requirement: StructuredRequirement,
        extra_roles: Optional[List[Dict[str, str]]] = None,
        rounds: int = 1,
    ) -> DiscussionResult:
        """
        Execute the discussion.

        Args:
            requirement: Structured requirement
            extra_roles: Extra roles (override default domain-specific roles)
            rounds: Discussion rounds (currently only 1 round supported)

        Returns:
            DiscussionResult: Discussion result
        """
        # Determine participating roles
        roles = list(requirement.suggested_roles)
        if extra_roles:
            roles.extend(extra_roles)

        # Each role independently gives viewpoint
        opinions = []
        for role_info in roles:
            role_name = role_info["role"]
            opinion = self._generate_opinion(role_name, requirement)
            opinions.append(opinion)

        # Summarize discussion results
        result = self._aggregate(opinions, requirement)
        return result

    def _generate_opinion(
        self, role_name: str, requirement: StructuredRequirement
    ) -> DiscussionOpinion:
        """Generate viewpoint for a single role"""
        if self.llm_call_fn:
            return self._generate_opinion_with_llm(role_name, requirement)
        return self._generate_opinion_rule_based(role_name, requirement)

    def _generate_opinion_rule_based(
        self, role_name: str, requirement: StructuredRequirement
    ) -> DiscussionOpinion:
        """Rule-based viewpoint generation"""
        prompt = ROLE_PROMPTS.get(role_name, f"You are a {role_name} expert. Please review this requirement and provide your viewpoint.")

        # Generate structured viewpoint based on role and requirement content
        concerns = []
        suggestions = []

        if role_name == "Methodology Review":
            if not requirement.key_questions:
                concerns.append("Missing clear core questions in the requirement")
                suggestions.append("Recommend clarifying 2-3 core questions that must be answered")
            if not requirement.constraints.get("methodology"):
                suggestions.append("Recommend clarifying methodology preference to avoid scattered search results")

        elif role_name == "Devil's Advocate":
            if len(requirement.objectives) > 5:
                concerns.append("Too many objectives may lead to unfocused research")
                suggestions.append("Recommend reducing to 3 core objectives")
            concerns.append("Need to confirm whether pre-existing bias affects research direction")

        elif role_name == "Feasibility Assessment":
            if not requirement.constraints.get("time_range"):
                concerns.append("No time range specified; search results may be excessive")
                suggestions.append("Recommend limiting to the recent 3-5 years")
            if requirement.domain_code == "academic_research":
                suggestions.append("Academic search requires API configuration; ensure arXiv/SS/OA are available")

        elif role_name == "Literature Coverage Review":
            if requirement.domain_code == "academic_research":
                sources = requirement.domain_specific.get("search_sources", [])
                if len(sources) < 2:
                    concerns.append("Single search source may miss important literature")
                    suggestions.append("Recommend using at least 3 search sources")

        elif role_name == "Statistical Method Scrutiny":
            if not requirement.constraints.get("methodology"):
                concerns.append("No methodology preference specified; difficult to assess statistical applicability")
                suggestions.append("Recommend distinguishing usage scenarios for econometric vs ML methods")

        opinion_text = f"As {role_name}, I have reviewed this requirement."
        if concerns:
            opinion_text += f" Key concerns: {'; '.join(concerns)}"
        if suggestions:
            opinion_text += f" Suggestions: {'; '.join(suggestions)}"
        if not concerns and not suggestions:
            opinion_text += " Current requirement direction is sound, no major risks."

        return DiscussionOpinion(
            role=role_name,
            opinion=opinion_text,
            concerns=concerns,
            suggestions=suggestions,
        )

    def _generate_opinion_with_llm(
        self, role_name: str, requirement: StructuredRequirement
    ) -> DiscussionOpinion:
        """Generate viewpoint using LLM"""
        system_prompt = ROLE_PROMPTS.get(
            role_name,
            f"You are a {role_name} expert. Please review this requirement and provide your viewpoint."
        )

        user_msg = f"""Please review the following requirement document and provide your professional viewpoint:

{requirement.to_json()}

Output in the following JSON format:
{{"opinion": "Your overall viewpoint", "concerns": ["Concern 1", "Concern 2"], "suggestions": ["Suggestion 1", "Suggestion 2"]}}"""

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
        """Summarize role viewpoints, extract consensus and disagreements"""
        consensus_points = []
        disagreements = []
        supplements = []

        # Find concerns shared by multiple roles → consensus
        all_concerns = {}
        for op in opinions:
            for c in op.concerns:
                all_concerns[c] = all_concerns.get(c, 0) + 1

        for concern, count in all_concerns.items():
            if count >= 2:
                consensus_points.append(f"Multi-party consensus: {concern}")

        # Find conflicting suggestions → disagreements
        suggestion_themes = {}
        for op in opinions:
            for s in op.suggestions:
                # Simple keyword extraction
                key = s[:20]
                suggestion_themes[key] = suggestion_themes.get(key, [])
                suggestion_themes[key].append(op.role)

        # Supplementary suggestions
        for op in opinions:
            for s in op.suggestions:
                supplements.append(f"[{op.role}] {s}")

        # Refine requirement
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
