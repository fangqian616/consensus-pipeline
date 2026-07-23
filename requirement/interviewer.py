"""
Requirement Research AI — Consensus Pipeline v4.0

Product-manager-style interviews, turning vague ideas into structured requirements.
Standalone module that outputs a structured requirement document as input for all downstream processes.
"""
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


@dataclass
class RequirementDocument:
    """Structured requirement document — output of interviewer, input for all downstream modules"""
    topic: str = ""
    domain: str = ""
    objectives: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    key_questions: List[str] = field(default_factory=list)
    deliverable_type: str = ""
    quality_criteria: str = ""
    # Metadata
    interview_history: List[Dict[str, str]] = field(default_factory=list)
    domain_specific: Dict[str, Any] = field(default_factory=dict)  # Domain-specific fields

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, d: dict) -> "RequirementDocument":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


# ============ Domain Interview Templates ============

DOMAIN_INTERVIEW_TEMPLATES = {
    "academic_research": {
        "domain_name": "Academic Research",
        "domain_name_zh": "学术调研",
        "required_dimensions": [
            "Research topic and core questions",
            "Discipline and interdisciplinary scope",
            "Time range (recent 3/5/10 years)",
            "Methodology preference (econometrics/ML/hybrid)",
            "Paper quality standard (CSSCI/SCI tier)",
            "Expected deliverable (group meeting report/survey paper/research plan)",
        ],
        "required_dimensions_zh": [
            "研究主题和核心问题",
            "学科领域和跨学科范围",
            "时间范围（近3/5/10年）",
            "方法论偏好（计量/机器学习/混合方法）",
            "论文质量标准（CSSCI/SCI级别）",
            "预期成果（组会汇报/综述论文/研究计划）",
        ],
        "follow_up_questions": [
            "Are you focused on phenomenon description or causal mechanisms?",
            "Which search sources to cover? arXiv/Semantic Scholar/OpenAlex?",
            "Do you need citation network analysis?",
            "Who is the final audience? Advisor/peers/reviewers?",
        ],
        "follow_up_questions_zh": [
            "您侧重于现象描述还是因果机制？",
            "需要覆盖哪些检索来源？arXiv/Semantic Scholar/OpenAlex？",
            "是否需要引用网络分析？",
            "最终受众是谁？导师/同行/审稿人？",
        ],
        "domain_specific_fields": {
            "search_sources": ["arxiv", "semantic_scholar", "openalex"],
            "quality_level": "CSSCI and above",
            "time_range": "Recent 5 years",
        },
    },
    "animation": {
        "domain_name": "Animation",
        "domain_name_zh": "动画制作",
        "required_dimensions": [
            "Creative goal (short film/storyboard/video prompt)",
            "Visual style and references",
            "Narrative structure (linear/nonlinear/experimental)",
            "Technical constraints (3D/2D/hybrid)",
            "Target platform and audience",
        ],
        "required_dimensions_zh": [
            "创作目标（短片/分镜/视频提示词）",
            "视觉风格和参考作品",
            "叙事结构（线性/非线性/实验性）",
            "技术约束（3D/2D/混合）",
            "目标平台和受众",
        ],
        "follow_up_questions": [
            "Any reference works or visual styles?",
            "What is the expected duration?",
            "Need sound effects and music?",
        ],
        "follow_up_questions_zh": [
            "有参考作品或视觉风格吗？",
            "预期时长是多少？",
            "需要音效和配乐吗？",
        ],
        "domain_specific_fields": {
            "visual_style": "",
            "duration": "",
            "platform": "",
        },
    },
    "general": {
        "domain_name": "General",
        "domain_name_zh": "通用",
        "required_dimensions": [
            "Core objectives",
            "Domain scope",
            "Constraints",
            "Expected deliverable",
            "Quality criteria",
        ],
        "required_dimensions_zh": [
            "核心目标",
            "领域范围",
            "约束条件",
            "预期成果",
            "质量标准",
        ],
        "follow_up_questions": [],
        "follow_up_questions_zh": [],
        "domain_specific_fields": {},
    },
}


class RequirementInterviewer:
    """
    Requirement Research AI

    Role: Product-manager-style interviews, digging into user needs through multi-round dialogue,
    outputting a structured requirement document.

    Usage:
        interviewer = RequirementInterviewer()
        # Step 1: Initialize from a single user sentence
        result = interviewer.start("I want to research ML applications in energy economics")
        # result contains: domain identification + first follow-up question

        # Subsequent: round-by-round dialogue
        result = interviewer.chat("I focus on carbon price forecasting, methodology偏向ML")  # Example with Chinese term
        # result contains: follow-up question or completion judgment

        # Complete: get structured requirement document
        doc = interviewer.get_requirement_document()
    """

    def __init__(
        self,
        llm_call_fn=None,
        domain_hint: Optional[str] = None,
        max_rounds: int = 8,
        language: str = "en",
    ):
        """
        Args:
            llm_call_fn: LLM call function with signature fn(system_prompt, user_message) -> str
                         If None, uses built-in rule engine (no external LLM dependency)
            domain_hint: Domain hint, e.g. "academic_research", "animation"
            max_rounds: Maximum dialogue rounds
            language: "zh" for Chinese, "en" for English
        """
        self.llm_call_fn = llm_call_fn
        self.max_rounds = max_rounds
        self.language = language
        self.history: List[Dict[str, str]] = []
        self.doc = RequirementDocument()
        self._domain_template = None
        self._detected_domain = domain_hint
        self._current_round = 0
        self._is_complete = False
        self._asked_questions: List[str] = []

    def start(self, user_input: str) -> Dict[str, Any]:
        """
        Start requirement research, initializing from a single user sentence.

        Returns:
            {
                "domain": "Identified domain",
                "question": "First follow-up question",
                "round": 1,
                "is_complete": False,
            }
        """
        self.doc.topic = user_input
        self.history.append({"role": "user", "content": user_input})

        # Domain identification
        if self._detected_domain is None:
            self._detected_domain = self._detect_domain(user_input)

        self._domain_template = DOMAIN_INTERVIEW_TEMPLATES.get(
            self._detected_domain, DOMAIN_INTERVIEW_TEMPLATES["general"]
        )
        if self.language == "zh":
            self.doc.domain = self._domain_template.get("domain_name_zh", self._domain_template["domain_name"])
        else:
            self.doc.domain = self._domain_template["domain_name"]

        # Initialize domain-specific fields
        if self._domain_template.get("domain_specific_fields"):
            self.doc.domain_specific = dict(self._domain_template["domain_specific_fields"])

        # Generate first follow-up question
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
        After user replies, generate the next follow-up question or determine completion.

        Returns:
            {
                "question": "Next follow-up question (if not complete)",
                "round": Current round number,
                "is_complete": Whether complete,
                "requirement_doc": RequirementDocument (if complete),
            }
        """
        self.history.append({"role": "user", "content": user_message})
        self._current_round += 1

        # Extract info from user reply, update requirement doc
        self._extract_info(user_message)

        # Check if complete
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

        # Generate next follow-up question
        question = self._generate_next_question()
        self.history.append({"role": "assistant", "content": question})

        return {
            "question": question,
            "round": self._current_round,
            "is_complete": False,
        }

    def get_requirement_document(self) -> RequirementDocument:
        """Get the current requirement document (whether complete or not)"""
        self.doc.interview_history = self.history
        return self.doc

    def force_complete(self) -> RequirementDocument:
        """Force completion, generating requirement document from available information"""
        self._is_complete = True
        self.doc.interview_history = self.history
        return self.doc

    # ============ Internal Methods ============

    def _detect_domain(self, text: str) -> str:
        """Identify domain from user input (v4.3: 'method' requires co-occurrence with academic keywords)"""
        text_lower = text.lower()
        # Strong academic signal keywords (sufficient alone to classify as academic)
        academic_strong = [
            "调研", "研究", "论文", "学术", "文献", "期刊",  # Chinese academic keywords
            "综述", "检索", "引用", "cssci", "sci", "ssci",
            "arxiv", "实证", "计量",
            # v0.7.6: academic discipline keywords
            "经济学", "金融学", "管理学", "社会学", "心理学", "物理学",
            "计算机科学", "生物学", "化学", "数学", "统计学", "工程学",
            "能源经济", "环境经济", "公共管理", "政治学", "法学",
            "economics", "finance", "sociology", "psychology", "physics",
            "biology", "chemistry", "philosophy", "history",
        ]
        # Weak academic signals (only score when co-occurring with strong signals)
        academic_weak = ["方法", "模型", "数据", "经济", "分析"]
        
        academic_score = sum(1 for kw in academic_strong if kw in text_lower)
        # Weak signals only score when strong signals are present
        if academic_score > 0:
            academic_score += sum(1 for kw in academic_weak if kw in text_lower)
        
        animation_keywords = [
            "动画", "分镜", "视频", "镜头", "特效", "3d", "2d",
            "渲染", "角色", "场景", "prompt", "剪辑",
        ]
        animation_score = sum(1 for kw in animation_keywords if kw in text_lower)

        if academic_score > animation_score:
            return "academic_research"
        elif animation_score > academic_score:
            return "animation"
        else:
            return "general"

    def _generate_next_question(self) -> str:
        """Generate the next follow-up question"""
        if self.llm_call_fn:
            return self._generate_question_with_llm()
        return self._generate_question_rule_based()

    def _generate_question_rule_based(self) -> str:
        """Rule-based question generation (no external LLM dependency)"""
        template = self._domain_template
        if self.language == "zh":
            required = template.get("required_dimensions_zh", template.get("required_dimensions", []))
            follow_ups = template.get("follow_up_questions_zh", template.get("follow_up_questions", []))
        else:
            required = template.get("required_dimensions", [])
            follow_ups = template.get("follow_up_questions", [])

        # Find dimensions not yet asked about
        unasked = []
        for dim in required:
            dim_key = dim.split("（")[0].split("(")[0].strip()
            if dim_key not in self._asked_questions:
                unasked.append(dim)

        if unasked:
            next_q = unasked[0]
            self._asked_questions.append(next_q.split("（")[0].split("(")[0].strip())
            if self.language == "zh":
                return f"请告诉我：{next_q}？"
            return f"Please tell me: {next_q}?"

        # Required dimensions covered; use follow_ups for deeper probing
        if follow_ups and self._current_round < self.max_rounds:
            idx = min(self._current_round - len(required), len(follow_ups) - 1)
            idx = max(0, idx)
            return follow_ups[idx]

        if self.language == "zh":
            return "还有什么要补充的吗？如果没有，我们可以开始生成配置了。"
        return "Anything else to add? If not, we can start generating the configuration."

    def _generate_question_with_llm(self) -> str:
        """Generate follow-up question using LLM"""
        system_prompt = f"""You are the Consensus Pipeline requirement research AI, conducting requirement research in the {self._domain_template['domain_name']} domain.

Your task is to help users transform vague ideas into structured requirements through follow-up questions. Probe like an advisor, not a form-filler.

Currently gathered information:
{self.doc.to_json()}

Dimensions still needed:
{json.dumps(self._domain_template.get('required_dimensions', []), ensure_ascii=False)}

Suggested follow-up directions:
{json.dumps(self._domain_template.get('follow_up_questions', []), ensure_ascii=False)}

Generate a brief follow-up question (1-2 sentences), focusing on the dimension most needing clarification. Do not repeat already known information."""

        user_msg = f"Current dialogue history:\n" + "\n".join(
            f"{'User' if h['role']=='user' else 'AI'}: {h['content']}"
            for h in self.history[-4:]
        )

        response = self.llm_call_fn(system_prompt, user_msg)
        return response

    def _extract_info(self, user_message: str):
        """Extract information from user reply, update requirement document"""
        if self.llm_call_fn:
            self._extract_info_with_llm(user_message)
        else:
            self._extract_info_rule_based(user_message)

    def _extract_info_rule_based(self, user_message: str):
        """Rule-based info extraction (v4.3: regex parsing for time/method/tier, no longer storing entire text as objective)"""
        import re
        msg = user_message.strip()
        extracted_something = False

        # Time range extraction
        time_match = re.search(r'近(\d+)\s*年|(\d{4})\s*[-–—]\s*(\d{4})\s*年', msg)
        if time_match:
            if time_match.group(1):
                self.doc.constraints["time_range"] = f"Recent {time_match.group(1)} years"
            elif time_match.group(2):
                self.doc.constraints["time_range"] = f"{time_match.group(2)}-{time_match.group(3)}"
            extracted_something = True

        # Method extraction
        method_keywords = ["机器学习", "深度学习", "强化学习", "计量", "面板数据",  # Chinese method keywords for matching
                           "ML", "神经网络", "因果推断", "混合方法", "定性", "定量"]
        methods = [kw for kw in method_keywords if kw in msg]
        if methods:
            self.doc.constraints["methodology"] = ", ".join(methods)
            extracted_something = True

        # Quality level extraction
        level_match = re.search(r'(CSSCI|SCI|SSCI|Q1|Q2|核心|CSCD)', msg, re.IGNORECASE)
        if level_match:
            self.doc.constraints["quality_level"] = level_match.group(1).upper()
            extracted_something = True

        # Deliverable extraction
        deliverable_match = re.search(r'(PDF|汇报|综述|论文|报告|组会|答辩)', msg)
        if deliverable_match:
            self.doc.deliverable_type = deliverable_match.group(1)
            extracted_something = True

        # If first round and no structured fields extracted, store as objective
        if self._current_round == 1 and not self.doc.objectives:
            self.doc.objectives.append(msg)
            extracted_something = True
        
        # Fallback: if no field matched, store as key_question
        if not extracted_something:
            if not self.doc.key_questions:
                self.doc.key_questions.append(msg)
            else:
                self.doc.objectives.append(msg)

    def _extract_info_with_llm(self, user_message: str):
        """Extract information using LLM"""
        system_prompt = f"""You are an information extraction assistant. Extract key information from the user's reply and update the requirement document.

Current requirement document:
{self.doc.to_json()}

Output the updated complete requirement document JSON. Output only JSON, no other text."""

        response = self.llm_call_fn(system_prompt, user_message)
        try:
            updated = json.loads(response)
            for key, value in updated.items():
                if key in RequirementDocument.__dataclass_fields__:
                    setattr(self.doc, key, value)
        except json.JSONDecodeError:
            pass  # LLM output format incorrect, keep as-is

    def _check_completion(self) -> bool:
        """Determine whether the research interview is complete"""
        # Reached maximum rounds
        if self._current_round >= self.max_rounds:
            return True

        # All required dimensions collected
        template = self._domain_template
        required = template.get("required_dimensions", [])

        filled_count = 0
        for dim in required:
            dim_key = dim.split("（")[0].split("(")[0].strip()
            if dim_key in self._asked_questions:
                filled_count += 1

        # At least 80% of required dimensions answered + has objectives + has deliverable
        completion_ratio = filled_count / max(len(required), 1)
        has_objectives = len(self.doc.objectives) > 0
        has_deliverable = bool(self.doc.deliverable_type)

        if completion_ratio >= 0.8 and has_objectives and has_deliverable:
            return True

        return False
