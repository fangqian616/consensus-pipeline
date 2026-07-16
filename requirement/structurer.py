"""
Requirement Structuring Module — Consensus Pipeline v4.0

Further structures the requirement document output by the interviewer,
providing standardized input for discussion groups and config recommendation modules.
"""
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .interviewer import RequirementDocument


@dataclass
class StructuredRequirement:
    """Structured requirement — output of structurer"""
    # Basic info
    topic: str = ""
    domain: str = ""
    domain_code: str = ""  # academic_research / animation / general

    # Core requirements
    objectives: List[str] = field(default_factory=list)
    key_questions: List[str] = field(default_factory=list)

    # Constraints
    constraints: Dict[str, Any] = field(default_factory=dict)

    # Deliverables
    deliverable_type: str = ""
    quality_criteria: str = ""

    # Discussion group config suggestions
    suggested_roles: List[Dict[str, str]] = field(default_factory=list)
    """[
        {"role": "Methodology Review", "reason": "..."},
        {"role": "Literature Coverage Review", "reason": "Academic research needs..."},
    ]"""

    # Department config direction hints
    department_hints: List[Dict[str, str]] = field(default_factory=list)
    """[
        {"type": "retrieval", "description": "Multi-source literature retrieval"},
        {"type": "validation", "description": "Data validation and cross-checking"},
    ]"""

    # Metadata
    source_doc: Optional[Dict[str, Any]] = None
    domain_specific: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ============ Domain → Role Mapping ============

DOMAIN_ROLE_MAP = {
    "academic_research": {
        "fixed_roles": [
            {"role": "Methodology Review", "reason": "Evaluate the soundness of research paths and method choices"},
            {"role": "Devil's Advocate", "reason": "Challenge assumptions, point out potential blind spots"},
            {"role": "Feasibility Assessment", "reason": "Assess whether search tools and data sources can support the objectives"},
        ],
        "domain_roles": [
            {"role": "Literature Coverage Review", "reason": "Ensure no key sources are missed in retrieval"},
            {"role": "Statistical Method Scrutiny", "reason": "Question the applicability and robustness of methods"},
            {"role": "Citation Chain Integrity", "reason": "Check whether key references are missing"},
        ],
    },
    "animation": {
        "fixed_roles": [
            {"role": "Methodology Review", "reason": "Evaluate the soundness of creative methodology and workflow"},
            {"role": "Devil's Advocate", "reason": "Challenge visual and narrative choices"},
            {"role": "Feasibility Assessment", "reason": "Assess technical implementation difficulty"},
        ],
        "domain_roles": [
            {"role": "Audience Analysis", "reason": "Review content from the target audience perspective"},
            {"role": "Platform Adaptation", "reason": "Check adaptability across different platforms"},
            {"role": "Visual Style Consistency", "reason": "Ensure visual style consistency"},
        ],
    },
    "general": {
        "fixed_roles": [
            {"role": "Methodology Review", "reason": "Evaluate path soundness"},
            {"role": "Devil's Advocate", "reason": "Challenge assumptions and direction"},
            {"role": "Feasibility Assessment", "reason": "Assess executability"},
        ],
        "domain_roles": [],
    },
}

# ============ Domain → Department Direction Mapping ============

DOMAIN_DEPARTMENT_HINTS = {
    "academic_research": [
        {"type": "retrieval", "description": "Multi-source literature retrieval (arXiv/SS/OA)"},
        {"type": "metadata", "description": "DOI precise metadata extraction"},
        {"type": "citation_network", "description": "Citation network analysis"},
        {"type": "methodology_review", "description": "Methodological rigor assessment"},
        {"type": "data_validation", "description": "Cross-validation and data consistency"},
        {"type": "counter_evidence", "description": "Counter-evidence search"},
        {"type": "topic_clustering", "description": "9-dimension topic clustering"},
        {"type": "visualization", "description": "Trend/distribution/breakthrough charts"},
        {"type": "report_integration", "description": "PDF/Markdown report integration"},
    ],
    "animation": [
        {"type": "screenwriter", "description": "Script / Narrative"},
        {"type": "spatial", "description": "Spatial Layout"},
        {"type": "storyboard", "description": "Storyboard Design"},
        {"type": "dp", "description": "Cinematography"},
        {"type": "lighting", "description": "Lighting Design"},
        {"type": "vfx", "description": "Visual Effects"},
        {"type": "sound", "description": "Sound Design"},
        {"type": "editing", "description": "Editing Rhythm"},
    ],
}


class RequirementStructurer:
    """
    Requirement Structuring

    Converts RequirementDocument to StructuredRequirement,
    adding discussion group role suggestions and department direction hints.
    """

    def __init__(self, llm_call_fn=None):
        self.llm_call_fn = llm_call_fn

    def structure(self, doc: RequirementDocument) -> StructuredRequirement:
        """
        Structure a requirement document.

        Args:
            doc: Requirement document output by interviewer

        Returns:
            StructuredRequirement: Structured requirement
        """
        # Infer domain code
        domain_code = self._infer_domain_code(doc.domain)

        # Get domain template
        role_template = DOMAIN_ROLE_MAP.get(domain_code, DOMAIN_ROLE_MAP["general"])
        dept_hints = DOMAIN_DEPARTMENT_HINTS.get(domain_code, [])

        # Assemble fixed roles + domain-specific roles
        suggested_roles = list(role_template["fixed_roles"])

        # Dynamically select domain-specific roles based on requirements
        domain_roles = role_template.get("domain_roles", [])
        for role_info in domain_roles:
            # Simple heuristic: add role if requirement doc mentions related keywords
            if self._is_role_relevant(role_info["role"], doc):
                suggested_roles.append(role_info)

        # If LLM is available, refine further
        if self.llm_call_fn:
            suggested_roles = self._refine_roles_with_llm(doc, suggested_roles)

        structured = StructuredRequirement(
            topic=doc.topic,
            domain=doc.domain,
            domain_code=domain_code,
            objectives=doc.objectives,
            key_questions=doc.key_questions,
            constraints=doc.constraints,
            deliverable_type=doc.deliverable_type,
            quality_criteria=doc.quality_criteria,
            suggested_roles=suggested_roles,
            department_hints=dept_hints,
            source_doc=doc.to_dict(),
            domain_specific=doc.domain_specific,
        )

        return structured

    def _infer_domain_code(self, domain_name: str) -> str:
        """Infer domain code from domain name"""
        mapping = {
            "学术调研": "academic_research",  # Chinese domain name from interviewer output
            "动画创作": "animation",  # Chinese domain name from interviewer output
            "通用": "general",  # Chinese domain name from interviewer output
        }
        return mapping.get(domain_name, "general")

    def _is_role_relevant(self, role: str, doc: RequirementDocument) -> bool:
        """Determine whether a domain-specific role is relevant to the requirement"""
        text = f"{doc.topic} {' '.join(doc.objectives)} {' '.join(doc.key_questions)}".lower()

        relevance_map = {
            "Literature Coverage Review": ["检索", "文献", "论文", "调研", "搜索"],
            "Statistical Method Scrutiny": ["统计", "计量", "回归", "模型", "因果"],
            "Citation Chain Integrity": ["引用", "溯源", "doi", "影响"],
            "Audience Analysis": ["受众", "用户", "观看", "播放", "传播"],
            "Platform Adaptation": ["平台", "发布", "b站", "抖音", "youtube"],
            "Visual Style Consistency": ["风格", "视觉", "美术", "色调", "一致"],
        }

        keywords = relevance_map.get(role, [])
        if not keywords:
            return True  # Default to including when no matching rules exist

        return any(kw in text for kw in keywords)

    def _refine_roles_with_llm(
        self, doc: RequirementDocument, current_roles: List[Dict]
    ) -> List[Dict]:
        """Refine role suggestions using LLM"""
        roles_json = json.dumps(current_roles, ensure_ascii=False)
        system_prompt = f"""You are a requirements analysis expert. Adjust the discussion group role suggestions based on the user's requirement document.
Current role list:
{roles_json}

Output the adjusted role list as JSON, format:
[{{"role": "Role name", "reason": "Reason"}}]
Output only JSON, no other text."""

        user_msg = f"Requirement document:\n{doc.to_json()}"
        response = self.llm_call_fn(system_prompt, user_msg)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return current_roles
