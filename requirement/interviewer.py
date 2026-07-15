"""
需求调研 AI — Consensus Pipeline v4.0

产品经理式访谈，把模糊想法变成结构化需求。
独立模块，输出结构化需求文档，作为后续所有流程的输入。
"""
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class RequirementDocument:
    """结构化需求文档 — interviewer 的输出，后续所有模块的输入"""
    topic: str = ""
    domain: str = ""
    objectives: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    key_questions: List[str] = field(default_factory=list)
    deliverable_type: str = ""
    quality_criteria: str = ""
    # 元信息
    interview_history: List[Dict[str, str]] = field(default_factory=list)
    domain_specific: Dict[str, Any] = field(default_factory=dict)  # 领域特化字段

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "RequirementDocument":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ============ 领域调研模板 ============

DOMAIN_INTERVIEW_TEMPLATES = {
    "academic_research": {
        "domain_name": "学术调研",
        "required_dimensions": [
            "研究主题与核心问题",
            "学科领域与交叉范围",
            "时间范围（近3年/5年/10年）",
            "方法论偏好（计量/ML/混合）",
            "论文质量标准（CSSCI/SCI分区）",
            "预期交付物（组会汇报/综述论文/研究计划）",
        ],
        "follow_up_questions": [
            "你关注的是现象描述还是因果机制？",
            "需要覆盖哪些检索源？arXiv/Semantic Scholar/OpenAlex？",
            "是否需要引用网络分析？",
            "最终受众是谁？导师/同门/评审？",
        ],
        "domain_specific_fields": {
            "search_sources": ["arxiv", "semantic_scholar", "openalex"],
            "quality_level": "CSSCI及以上",
            "time_range": "近5年",
        },
    },
    "animation": {
        "domain_name": "动画创作",
        "required_dimensions": [
            "创作目标（短片/分镜/视频Prompt）",
            "视觉风格与参考",
            "叙事结构（线性/非线性/实验）",
            "技术约束（3D/2D/混合）",
            "目标平台与受众",
        ],
        "follow_up_questions": [
            "有没有参考作品或视觉风格？",
            "时长预期是多少？",
            "需要音效和配乐吗？",
        ],
        "domain_specific_fields": {
            "visual_style": "",
            "duration": "",
            "platform": "",
        },
    },
    "general": {
        "domain_name": "通用",
        "required_dimensions": [
            "核心目标",
            "领域范围",
            "约束条件",
            "预期交付",
            "质量标准",
        ],
        "follow_up_questions": [],
        "domain_specific_fields": {},
    },
}


class RequirementInterviewer:
    """
    需求调研 AI

    职责：产品经理式访谈，通过多轮对话深挖用户需求，
    输出结构化需求文档。

    使用方式：
        interviewer = RequirementInterviewer()
        # 第一步：从用户的一句话初始化
        result = interviewer.start("我想调研机器学习在能源经济学中的应用")
        # result 包含：领域识别 + 首轮追问

        # 后续：逐轮对话
        result = interviewer.chat("我关注碳价预测，方法论偏ML")
        # result 包含：追问或完成判断

        # 完成：获取结构化需求文档
        doc = interviewer.get_requirement_document()
    """

    def __init__(
        self,
        llm_call_fn=None,
        domain_hint: Optional[str] = None,
        max_rounds: int = 8,
    ):
        """
        Args:
            llm_call_fn: LLM调用函数，签名为 fn(system_prompt, user_message) -> str
                         如果为None，使用内置规则引擎（不依赖外部LLM）
            domain_hint: 领域提示，如 "academic_research", "animation"
            max_rounds: 最大对话轮数
        """
        self.llm_call_fn = llm_call_fn
        self.max_rounds = max_rounds
        self.history: List[Dict[str, str]] = []
        self.doc = RequirementDocument()
        self._domain_template = None
        self._detected_domain = domain_hint
        self._current_round = 0
        self._is_complete = False
        self._asked_questions: List[str] = []

    def start(self, user_input: str) -> Dict[str, Any]:
        """
        开始需求调研，从用户的一句话初始化。

        Returns:
            {
                "domain": "识别的领域",
                "question": "首轮追问",
                "round": 1,
                "is_complete": False,
            }
        """
        self.doc.topic = user_input
        self.history.append({"role": "user", "content": user_input})

        # 领域识别
        if self._detected_domain is None:
            self._detected_domain = self._detect_domain(user_input)

        self._domain_template = DOMAIN_INTERVIEW_TEMPLATES.get(
            self._detected_domain, DOMAIN_INTERVIEW_TEMPLATES["general"]
        )
        self.doc.domain = self._domain_template["domain_name"]

        # 初始化领域特化字段
        if self._domain_template.get("domain_specific_fields"):
            self.doc.domain_specific = dict(self._domain_template["domain_specific_fields"])

        # 生成首轮追问
        question = self._generate_next_question()
        self.history.append({"role": "assistant", "content": question})
        self._current_round = 1

        return {
            "domain": self._detected_domain,
            "domain_name": self._domain_template["domain_name"],
            "question": question,
            "round": 1,
            "is_complete": False,
        }

    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        用户回复后，生成下一轮追问或判断完成。

        Returns:
            {
                "question": "下一轮追问（如果未完成）",
                "round": 当前轮次,
                "is_complete": 是否完成,
                "requirement_doc": RequirementDocument（如果完成）,
            }
        """
        self.history.append({"role": "user", "content": user_message})
        self._current_round += 1

        # 从用户回复中提取信息，更新需求文档
        self._extract_info(user_message)

        # 判断是否完成
        is_complete = self._check_completion()

        if is_complete:
            self._is_complete = True
            self.doc.interview_history = self.history
            return {
                "question": None,
                "round": self._current_round,
                "is_complete": True,
                "requirement_doc": self.doc,
            }

        # 生成下一轮追问
        question = self._generate_next_question()
        self.history.append({"role": "assistant", "content": question})

        return {
            "question": question,
            "round": self._current_round,
            "is_complete": False,
        }

    def get_requirement_document(self) -> RequirementDocument:
        """获取当前需求文档（无论是否完成）"""
        self.doc.interview_history = self.history
        return self.doc

    def force_complete(self) -> RequirementDocument:
        """强制完成，用已有信息生成需求文档"""
        self._is_complete = True
        self.doc.interview_history = self.history
        return self.doc

    # ============ 内部方法 ============

    def _detect_domain(self, text: str) -> str:
        """从用户输入识别领域"""
        text_lower = text.lower()
        academic_keywords = [
            "调研", "研究", "论文", "学术", "文献", "期刊",
            "综述", "检索", "引用", "cssci", "sci", "ssci",
            "arxiv", "方法", "实证", "计量",
        ]
        animation_keywords = [
            "动画", "分镜", "视频", "镜头", "特效", "3d", "2d",
            "渲染", "角色", "场景", "prompt", "剪辑",
        ]

        academic_score = sum(1 for kw in academic_keywords if kw in text_lower)
        animation_score = sum(1 for kw in animation_keywords if kw in text_lower)

        if academic_score > animation_score:
            return "academic_research"
        elif animation_score > academic_score:
            return "animation"
        else:
            return "general"

    def _generate_next_question(self) -> str:
        """生成下一轮追问"""
        if self.llm_call_fn:
            return self._generate_question_with_llm()
        return self._generate_question_rule_based()

    def _generate_question_rule_based(self) -> str:
        """基于规则的追问生成（不依赖外部LLM）"""
        template = self._domain_template
        required = template.get("required_dimensions", [])
        follow_ups = template.get("follow_up_questions", [])

        # 找出还没问到的维度
        unasked = []
        for dim in required:
            dim_key = dim.split("（")[0].split("(")[0].strip()
            if dim_key not in self._asked_questions:
                unasked.append(dim)

        if unasked:
            next_q = unasked[0]
            self._asked_questions.append(next_q.split("（")[0].split("(")[0].strip())
            return f"请告诉我：{next_q}？"

        # 必要维度问完了，用follow_up深挖
        if follow_ups and self._current_round < self.max_rounds:
            idx = min(self._current_round - len(required), len(follow_ups) - 1)
            idx = max(0, idx)
            return follow_ups[idx]

        return "还有其他补充吗？如果没有，我们可以开始生成配置了。"

    def _generate_question_with_llm(self) -> str:
        """使用LLM生成追问"""
        system_prompt = f"""你是Consensus Pipeline的需求调研AI，正在进行{self._domain_template['domain_name']}领域的需求调研。

你的任务是通过追问，帮助用户把模糊想法变成结构化需求。像导师一样追问，不是简单填表。

当前已获取的信息：
{self.doc.to_json()}

还需要了解的维度：
{json.dumps(self._domain_template.get('required_dimensions', []), ensure_ascii=False)}

追问建议方向：
{json.dumps(self._domain_template.get('follow_up_questions', []), ensure_ascii=False)}

请生成一个简短的追问（1-2句话），聚焦最需要澄清的维度。不要重复已经了解的信息。"""

        user_msg = f"当前对话历史：\n" + "\n".join(
            f"{'用户' if h['role']=='user' else 'AI'}：{h['content']}"
            for h in self.history[-4:]
        )

        response = self.llm_call_fn(system_prompt, user_msg)
        return response

    def _extract_info(self, user_message: str):
        """从用户回复中提取信息，更新需求文档"""
        if self.llm_call_fn:
            self._extract_info_with_llm(user_message)
        else:
            self._extract_info_rule_based(user_message)

    def _extract_info_rule_based(self, user_message: str):
        """基于规则的信息提取"""
        msg = user_message.strip()

        # 尝试匹配当前追问的维度，补充到对应字段
        if self._current_round == 1 and not self.doc.objectives:
            self.doc.objectives.append(msg)
        elif any(kw in msg for kw in ["年", "时间", "近期", "最近"]):
            self.doc.constraints["time_range"] = msg
        elif any(kw in msg for kw in ["方法", "计量", "ML", "机器学习", "深度学习"]):
            self.doc.constraints["methodology"] = msg
        elif any(kw in msg for kw in ["CSSCI", "SCI", "SSCI", "Q1", "质量", "等级"]):
            self.doc.constraints["quality_level"] = msg
        elif any(kw in msg for kw in ["PDF", "汇报", "综述", "论文", "报告", "交付"]):
            self.doc.deliverable_type = msg
        elif not self.doc.key_questions:
            self.doc.key_questions.append(msg)
        else:
            self.doc.objectives.append(msg)

    def _extract_info_with_llm(self, user_message: str):
        """使用LLM的信息提取"""
        system_prompt = f"""你是信息提取助手。从用户的回复中提取关键信息，更新需求文档。

当前需求文档：
{self.doc.to_json()}

请输出更新后的完整需求文档JSON，只输出JSON，不要其他文字。"""

        response = self.llm_call_fn(system_prompt, user_message)
        try:
            updated = json.loads(response)
            for key, value in updated.items():
                if key in RequirementDocument.__dataclass_fields__:
                    setattr(self.doc, key, value)
        except json.JSONDecodeError:
            pass  # LLM输出格式不对，保持原样

    def _check_completion(self) -> bool:
        """判断调研是否完成"""
        # 达到最大轮数
        if self._current_round >= self.max_rounds:
            return True

        # 必要维度都已收集
        template = self._domain_template
        required = template.get("required_dimensions", [])

        filled_count = 0
        for dim in required:
            dim_key = dim.split("（")[0].split("(")[0].strip()
            if dim_key in self._asked_questions:
                filled_count += 1

        # 至少回答了80%的必要维度 + 有目标 + 有交付物
        completion_ratio = filled_count / max(len(required), 1)
        has_objectives = len(self.doc.objectives) > 0
        has_deliverable = bool(self.doc.deliverable_type)

        if completion_ratio >= 0.8 and has_objectives and has_deliverable:
            return True

        return False
