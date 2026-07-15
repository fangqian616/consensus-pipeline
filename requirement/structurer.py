"""
需求结构化模块 — Consensus Pipeline v4.0

将 interviewer 输出的需求文档进一步结构化，
为讨论组和配置推荐模块提供标准化输入。
"""
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .interviewer import RequirementDocument


@dataclass
class StructuredRequirement:
    """结构化需求 — structurer 的输出"""
    # 基本信息
    topic: str = ""
    domain: str = ""
    domain_code: str = ""  # academic_research / animation / general

    # 核心需求
    objectives: List[str] = field(default_factory=list)
    key_questions: List[str] = field(default_factory=list)

    # 约束条件
    constraints: Dict[str, Any] = field(default_factory=dict)

    # 交付物
    deliverable_type: str = ""
    quality_criteria: str = ""

    # 讨论组配置建议
    suggested_roles: List[Dict[str, str]] = field(default_factory=list)
    """[
        {"role": "方法论审查", "reason": "..."},
        {"role": "文献覆盖度审查", "reason": "学术调研需要..."},
    ]"""

    # 部门配置方向
    department_hints: List[Dict[str, str]] = field(default_factory=list)
    """[
        {"type": "retrieval", "description": "多源文献检索"},
        {"type": "validation", "description": "数据验证与交叉检验"},
    ]"""

    # 元信息
    source_doc: Optional[Dict[str, Any]] = None
    domain_specific: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


# ============ 领域→角色映射 ============

DOMAIN_ROLE_MAP = {
    "academic_research": {
        "fixed_roles": [
            {"role": "方法论审查", "reason": "评估调研路径和方法选择的合理性"},
            {"role": "反方视角", "reason": "挑战假设，指出可能的盲点"},
            {"role": "落地可行性", "reason": "评估检索工具和数据源是否能支撑目标"},
        ],
        "domain_roles": [
            {"role": "文献覆盖度审查", "reason": "确保检索没有遗漏关键来源"},
            {"role": "统计方法质疑", "reason": "质疑方法的适用性和稳健性"},
            {"role": "引用链完整性", "reason": "检查关键文献是否被遗漏"},
        ],
    },
    "animation": {
        "fixed_roles": [
            {"role": "方法论审查", "reason": "评估创作方法论和流程的合理性"},
            {"role": "反方视角", "reason": "挑战视觉和叙事选择"},
            {"role": "落地可行性", "reason": "评估技术实现难度"},
        ],
        "domain_roles": [
            {"role": "受众分析", "reason": "从目标受众角度审视内容"},
            {"role": "平台适配", "reason": "检查不同平台的适配性"},
            {"role": "视觉风格一致性", "reason": "确保视觉风格的统一"},
        ],
    },
    "general": {
        "fixed_roles": [
            {"role": "方法论审查", "reason": "评估路径合理性"},
            {"role": "反方视角", "reason": "挑战假设和方向"},
            {"role": "落地可行性", "reason": "评估可执行性"},
        ],
        "domain_roles": [],
    },
}

# ============ 领域→部门方向映射 ============

DOMAIN_DEPARTMENT_HINTS = {
    "academic_research": [
        {"type": "retrieval", "description": "多源文献检索（arXiv/SS/OA）"},
        {"type": "metadata", "description": "DOI精确元数据提取"},
        {"type": "citation_network", "description": "引用网络分析"},
        {"type": "methodology_review", "description": "方法论严格性评估"},
        {"type": "data_validation", "description": "交叉验证与数据一致性"},
        {"type": "counter_evidence", "description": "反面证据搜寻"},
        {"type": "topic_clustering", "description": "9维度主题聚类"},
        {"type": "visualization", "description": "趋势/分布/突破图表"},
        {"type": "report_integration", "description": "PDF/Markdown报告整合"},
    ],
    "animation": [
        {"type": "screenwriter", "description": "剧本/叙事"},
        {"type": "spatial", "description": "空间布局"},
        {"type": "storyboard", "description": "分镜设计"},
        {"type": "dp", "description": "摄影指导"},
        {"type": "lighting", "description": "灯光设计"},
        {"type": "vfx", "description": "视觉效果"},
        {"type": "sound", "description": "音效设计"},
        {"type": "editing", "description": "剪辑节奏"},
    ],
}


class RequirementStructurer:
    """
    需求结构化

    将 RequirementDocument 转换为 StructuredRequirement，
    添加讨论组角色建议和部门方向建议。
    """

    def __init__(self, llm_call_fn=None):
        self.llm_call_fn = llm_call_fn

    def structure(self, doc: RequirementDocument) -> StructuredRequirement:
        """
        将需求文档结构化。

        Args:
            doc: interviewer 输出的需求文档

        Returns:
            StructuredRequirement: 结构化需求
        """
        # 领域代码推断
        domain_code = self._infer_domain_code(doc.domain)

        # 获取领域模板
        role_template = DOMAIN_ROLE_MAP.get(domain_code, DOMAIN_ROLE_MAP["general"])
        dept_hints = DOMAIN_DEPARTMENT_HINTS.get(domain_code, [])

        # 组装固定角色 + 领域特化角色
        suggested_roles = list(role_template["fixed_roles"])

        # 根据需求动态选择领域特化角色
        domain_roles = role_template.get("domain_roles", [])
        for role_info in domain_roles:
            # 简单启发式：如果需求文档中提到了相关关键词，就加入该角色
            if self._is_role_relevant(role_info["role"], doc):
                suggested_roles.append(role_info)

        # 如果LLM可用，进一步细化
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
        """从中文名推断领域代码"""
        mapping = {
            "学术调研": "academic_research",
            "动画创作": "animation",
            "通用": "general",
        }
        return mapping.get(domain_name, "general")

    def _is_role_relevant(self, role: str, doc: RequirementDocument) -> bool:
        """判断领域特化角色是否与需求相关"""
        text = f"{doc.topic} {' '.join(doc.objectives)} {' '.join(doc.key_questions)}".lower()

        relevance_map = {
            "文献覆盖度审查": ["检索", "文献", "论文", "调研", "搜索"],
            "统计方法质疑": ["统计", "计量", "回归", "模型", "因果"],
            "引用链完整性": ["引用", "溯源", "doi", "影响"],
            "受众分析": ["受众", "用户", "观看", "播放", "传播"],
            "平台适配": ["平台", "发布", "b站", "抖音", "youtube"],
            "视觉风格一致性": ["风格", "视觉", "美术", "色调", "一致"],
        }

        keywords = relevance_map.get(role, [])
        if not keywords:
            return True  # 没有匹配规则时默认加入

        return any(kw in text for kw in keywords)

    def _refine_roles_with_llm(
        self, doc: RequirementDocument, current_roles: List[Dict]
    ) -> List[Dict]:
        """使用LLM细化角色建议"""
        roles_json = json.dumps(current_roles, ensure_ascii=False)
        system_prompt = f"""你是需求分析专家。根据用户的需求文档，调整讨论组角色建议。
当前角色列表：
{roles_json}

请输出调整后的角色列表JSON，格式：
[{{"role": "角色名", "reason": "理由"}}]
只输出JSON，不要其他文字。"""

        user_msg = f"需求文档：\n{doc.to_json()}"
        response = self.llm_call_fn(system_prompt, user_msg)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return current_roles
