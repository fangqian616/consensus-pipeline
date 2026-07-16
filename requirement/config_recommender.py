"""
Department Configuration Recommendation Module — Consensus Pipeline v4.0

Recommends complete department configuration (PresetConfig format) based on structured requirements + discussion group input,
presented in full for user review.
"""
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .structurer import StructuredRequirement
from .discussion_group import DiscussionResult


# ============ Department Template Library ============

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TEMPLATES_DIR = os.path.join(_BASE_DIR, "templates")


def _load_template(name: str) -> dict:
    """Load department templates from templates/"""
    path = os.path.join(_TEMPLATES_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ============ Academic Research Department Template (embedded default) ============

ACADEMIC_DEPARTMENT_TEMPLATE = {
    "name": "Academic Research",
    "description": "Multi-source academic paper trend research with cross-debate and fact-checking",
    "departments": {
        "literature_search": {
            "zh_name": "文献检索组",
            "en_name": "Literature Search",
            "debaters": {
                "A": {
                    "zh_name": "多源广度派",
                    "en_name": "Broad Retriever",
                    "zh_style": "你专注从多个检索源（arXiv/Semantic Scholar/OpenAlex）广泛收集文献，确保覆盖面。你的首要目标是'不遗漏'，宁可多检索再筛选。你对每个检索源的特点了如指掌，能根据研究问题选择最佳检索策略。",
                    "en_style": "Focus on broad multi-source retrieval to ensure coverage"
                },
                "B": {
                    "zh_name": "精准筛选派",
                    "en_name": "Precision Filter",
                    "zh_style": "你专注对检索结果进行质量分级筛选，按期刊等级（S/A/B）和引用量过滤。你的首要目标是'宁缺毋滥'，只有真正高质量的论文才能进入候选池。你严格执行四道筛子：来源分级→引用加权→作者信号→内容初筛。",
                    "en_style": "Focus on quality filtering with strict journal-level screening"
                }
            }
        },
        "metadata_inspector": {
            "zh_name": "元数据精查组",
            "en_name": "Metadata Inspector",
            "debaters": {
                "A": {
                    "zh_name": "DOI溯源派",
                    "en_name": "DOI Tracer",
                    "zh_style": "你专注通过Crossref DOI获取精确的论文元数据：作者、机构、发表日期、卷期页码、基金信息。你确保每篇论文的身份信息完整可溯源，拒绝来路不明的引用。",
                    "en_style": "Focus on precise DOI-based metadata extraction"
                }
            }
        },
        "citation_network": {
            "zh_name": "引用网络组",
            "en_name": "Citation Network",
            "debaters": {
                "A": {
                    "zh_name": "影响力追踪派",
                    "en_name": "Impact Tracker",
                    "zh_style": "你专注通过OpenCitations分析引用链路，识别领域核心节点和高影响力论文。你能从引用结构中发现隐藏的研究脉络和学术传承关系。",
                    "en_style": "Focus on citation network analysis and core node identification"
                }
            }
        },
        "methodology_review": {
            "zh_name": "方法论审查组",
            "en_name": "Methodology Review",
            "debaters": {
                "A": {
                    "zh_name": "严谨性质疑派",
                    "en_name": "Rigor Skeptic",
                    "zh_style": "你从方法论严格性角度审视每篇论文：研究设计是否合理？模型设定是否有遗漏变量偏误？内生性问题如何处理？稳健性检验是否充分？你的职责是找出方法论上的软肋。",
                    "en_style": "Question methodological rigor and identify weaknesses"
                },
                "B": {
                    "zh_name": "创新性识别派",
                    "en_name": "Innovation Spotter",
                    "zh_style": "你专注识别方法论上的创新和突破：新的模型架构、新的估计策略、新的数据源利用方式。你的职责是发现有方法论贡献的论文，而不仅仅是应用现有方法的论文。",
                    "en_style": "Identify methodological innovations and breakthroughs"
                }
            }
        },
        "data_validation": {
            "zh_name": "数据验证组",
            "en_name": "Data Validation",
            "debaters": {
                "A": {
                    "zh_name": "交叉验证派",
                    "en_name": "Cross Validator",
                    "zh_style": "你专注对论文核心结论进行多源交叉验证：不同数据集是否得到一致结论？不同方法是否指向相同结果？稳健性是否经得起检验？",
                    "en_style": "Cross-validate conclusions across multiple sources"
                }
            }
        },
        "counter_evidence": {
            "zh_name": "反方质疑组",
            "en_name": "Counter Evidence",
            "debaters": {
                "A": {
                    "zh_name": "反例搜寻派",
                    "en_name": "Counterexample Hunter",
                    "zh_style": "你主动搜寻与主流结论相矛盾的证据和论文。你的职责是确保调研不会陷入确认偏误，每一条共识都应该经过反面证据的检验。没有反例的结论是可疑的。",
                    "en_style": "Actively search for contradictory evidence"
                },
                "B": {
                    "zh_name": "边界条件派",
                    "en_name": "Boundary Condition",
                    "zh_style": "你专注识别结论的适用边界：在什么条件下结论成立？在什么条件下可能失效？不同情境下的异质性如何？你的职责是为每条结论标注适用范围。",
                    "en_style": "Identify boundary conditions and applicability limits"
                }
            }
        },
        "topic_clustering": {
            "zh_name": "主题聚类组",
            "en_name": "Topic Clustering",
            "debaters": {
                "A": {
                    "zh_name": "9维度归类派",
                    "en_name": "9D Classifier",
                    "zh_style": "你使用9个维度对论文进行主题归类：研究领域、方法论、数据类型、地理范围、时间特征、研究设计、核心发现、政策含义、技术路线。你的职责是构建完整的主题地图。",
                    "en_style": "Classify papers across 9 dimensions"
                }
            }
        },
        "visualization": {
            "zh_name": "可视化组",
            "en_name": "Visualization",
            "debaters": {
                "A": {
                    "zh_name": "趋势与分布派",
                    "en_name": "Trend & Distribution",
                    "zh_style": "你负责生成4张核心图表：研究趋势时间线、方法论分布饼图、关键突破时间轴、引用网络演化图。图表要清晰、信息密度高、适合组会汇报。",
                    "en_style": "Generate 4 core charts for presentation"
                }
            }
        },
        "report_integration": {
            "zh_name": "报告整合组",
            "en_name": "Report Integration",
            "debaters": {
                "A": {
                    "zh_name": "结构化整合派",
                    "en_name": "Structural Integrator",
                    "zh_style": "你负责将所有部门的输出整合为最终的组会汇报PDF。报告结构：摘要→领域概览→方法论综述→核心发现→争议与前沿→研究建议→参考文献。12页，约9000字，20篇参考文献，4张图表。",
                    "en_style": "Integrate all outputs into structured report"
                }
            }
        },
        "programming": {
            "zh_name": "程序部",
            "en_name": "Programming",
            "debaters": {
                "A": {
                    "zh_name": "技术选型师",
                    "en_name": "Tech Stack Analyst",
                    "zh_style": "你专注分析该学术领域主流使用什么模型、框架和工具链。核心工作：(1) 梳理最主流技术栈——GitHub Stars/Downloads、近6个月commit频率；(2) 对比不同方案的适用场景、成熟度；(3) 给出明确选型建议和理由。只做选型，不写代码。输出格式：候选方案一行，含名称、版本、适用场景、成熟度评级(★~★★★★★)、推荐理由。",
                    "en_style": "Analyze mainstream tech stacks with adoption metrics, give clear selection recommendations."
                },
                "B": {
                    "zh_name": "代码架构师",
                    "en_name": "Code Architect",
                    "zh_style": "你专注将选型结果转化为可运行代码。核心工作：(1) 设计模块结构和调用关系；(2) 写出完整可运行代码，含import、配置、核心逻辑、异常处理；(3) 标注关键参数含义和调优方向。代码必须：能直接复制运行、有类型注解、有中文注释。输出格式：先画架构图，再输出完整代码块。",
                    "en_style": "Turn tech selection into runnable code with architecture diagrams and error handling."
                },
                "C": {
                    "zh_name": "调试优化师",
                    "en_name": "Debug & Optimize Specialist",
                    "zh_style": "你专注审查代码可运行性和性能边界。核心工作：(1) 预判出错条件和修复方案；(2) 分析性能瓶颈和优化方向；(3) 给出部署注意事项（环境依赖、版本兼容、GPU需求）。输出格式：风险点→严重等级(🔴高/🟡中/🟢低)→原因→修复方案。",
                    "en_style": "Diagnose code risks and performance bottlenecks with severity ratings."
                }
            }
        },
        "tutorial": {
            "zh_name": "教程部",
            "en_name": "Tutorial",
            "debaters": {
                "A": {
                    "zh_name": "零基础引导师",
                    "en_name": "Beginner Guide",
                    "zh_style": "专为零基础读者写教程。核心原则：(1) 每步假设读者零基础，解释专业术语；(2) 用「做什么→为什么→预期结果」三段式；(3) 预判新手卡点，提前排错。教程必须：从安装开始、每步有代码示例、提供最小demo。输出格式：编号步骤，每步含操作→原因→预期输出→常见报错。",
                    "en_style": "Write for absolute beginners with What→Why→Expected Result format."
                },
                "B": {
                    "zh_name": "进阶实战师",
                    "en_name": "Advanced Practitioner",
                    "zh_style": "专为有基础、想快速上手的读者写实战指南。核心原则：(1) 跳过基础，直奔实际用法；(2) 标注生产环境的坑——什么配置踩雷、什么参数别改、什么版本有bug；(3) 给出可直接复用的代码模板。输出格式：场景→代码→效果→避坑→替代方案。",
                    "en_style": "Write for practitioners. Focus on real-world usage and reusable templates."
                },
                "C": {
                    "zh_name": "最佳实践师",
                    "en_name": "Best Practices Curator",
                    "zh_style": "专注提炼行业标准和工作流规范。核心工作：(1) 梳理行业最佳实践——大厂怎么做、论文推荐什么pipeline；(2) 标注反模式——看似合理但有害的做法；(3) 给出可落地规范清单。输出格式：分类清单，每条含规范→原因→违反后果→参考来源。",
                    "en_style": "Curate industry best practices and anti-patterns with audit-ready checklists."
                }
            }
        }
    },
    "dept_order": [
        "literature_search", "metadata_inspector", "citation_network",
        "methodology_review", "data_validation", "counter_evidence",
        "topic_clustering", "visualization", "report_integration",
        "programming",
        "tutorial",
    ],
    "p2_cross_debates": [
        {"side_a": "methodology_review", "side_b": "counter_evidence", "zh_topic": "方法论的稳健性 vs 反面证据的冲击力", "en_topic": "Methodological robustness vs counter-evidence impact"},
        {"side_a": "literature_search", "side_b": "data_validation", "zh_topic": "覆盖广度 vs 验证深度", "en_topic": "Coverage breadth vs validation depth"},
        {"side_a": "topic_clustering", "side_b": "visualization", "zh_topic": "分类逻辑 vs 可视化呈现", "en_topic": "Classification logic vs visualization presentation"},
    ],
    "p5_cross_debates": [
        {"side_a": "methodology_review", "side_b": "counter_evidence", "zh_topic": "最终共识校验：方法论风险 vs 反面证据", "en_topic": "Final consensus check"},
    ],
    "proofread_departments": ["report_integration"],
    "debate_rounds": 3,
    "negative_prompts": "",
}


class ConfigRecommender:
    """
    Department Configuration Recommendation

    Recommends complete department configuration based on structured requirements + discussion group input.
    Output format is fully compatible with existing PresetConfig.
    """

    def __init__(self, llm_call_fn=None):
        self.llm_call_fn = llm_call_fn

    def recommend(
        self,
        requirement: StructuredRequirement,
        discussion: DiscussionResult,
    ) -> Dict[str, Any]:
        """
        Recommend department configuration.

        Args:
            requirement: Structured requirement
            discussion: Discussion group result

        Returns:
            dict: PresetConfig-format configuration, presented in full for user review
        """
        domain_code = requirement.domain_code

        # Select base template
        if domain_code == "academic_research":
            base_config = self._deep_copy_config(ACADEMIC_DEPARTMENT_TEMPLATE)
        else:
            # Try loading from template file
            base_config = _load_template(f"{domain_code}_departments")
            if not base_config:
                # Fallback to Router-generated configuration
                base_config = self._generate_default_config(requirement)

        # Adjust based on discussion group input
        config = self._adjust_with_discussion(base_config, requirement, discussion)

        # Inject requirement info into configuration description
        config["name"] = f"{requirement.topic} - {config.get('name', 'Custom Configuration')}"
        config["description"] = self._build_description(requirement, discussion)

        return config

    def _deep_copy_config(self, config: dict) -> dict:
        """Deep-copy configuration"""
        return json.loads(json.dumps(config))

    def _adjust_with_discussion(
        self,
        base_config: dict,
        requirement: StructuredRequirement,
        discussion: DiscussionResult,
    ) -> dict:
        """Adjust configuration based on discussion group input"""
        config = self._deep_copy_config(base_config)

        # If LLM is available, refine further
        if self.llm_call_fn:
            config = self._adjust_with_llm(config, requirement, discussion)

        return config

    def _adjust_with_llm(
        self,
        config: dict,
        requirement: StructuredRequirement,
        discussion: DiscussionResult,
    ) -> dict:
        """Adjust configuration using LLM"""
        system_prompt = """You are a configuration optimization expert. Adjust the department configuration based on the requirement document and discussion group input.
Keep the PresetConfig format unchanged; only adjust content and parameters.
Output the complete adjusted configuration JSON, no other text."""

        user_msg = f"""Requirement document:
{requirement.to_json()}

Discussion group input:
{discussion.to_json()}

Current configuration:
{json.dumps(config, ensure_ascii=False)}

Please adjust the configuration to better match the requirement, focusing on supplementary suggestions from the discussion group."""

        response = self.llm_call_fn(system_prompt, user_msg)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return config

    def _generate_default_config(self, requirement: StructuredRequirement) -> dict:
        """Generate default configuration (when no matching template exists)"""
        depts = {}
        dept_order = []

        for hint in requirement.department_hints:
            key = hint["type"]
            depts[key] = {
                "zh_name": hint["description"],
                "en_name": hint["type"].replace("_", " ").title(),
                "debaters": {
                    "A": {
                        "zh_name": f"{hint['description']} Expert A",
                        "en_name": f"Expert A",
                        "zh_style": f"You are a {hint['description']} expert, reviewing and analyzing from a professional perspective.",
                        "en_style": f"Expert in {hint['description']}"
                    }
                }
            }
            dept_order.append(key)

        return {
            "name": "Custom Configuration",
            "description": requirement.topic,
            "departments": depts,
            "dept_order": dept_order,
            "p2_cross_debates": [],
            "p5_cross_debates": [],
            "proofread_departments": [dept_order[-1]] if dept_order else [],
            "debate_rounds": 2,
            "negative_prompts": "",
        }

    def _build_description(
        self,
        requirement: StructuredRequirement,
        discussion: DiscussionResult,
    ) -> str:
        """Build configuration description"""
        parts = [f"Topic: {requirement.topic}"]
        if requirement.objectives:
            parts.append(f"Objectives: {'； '.join(requirement.objectives[:3])}")
        if requirement.deliverable_type:
            parts.append(f"Deliverable: {requirement.deliverable_type}")
        if discussion.supplements:
            parts.append(f"Discussion supplements: {'; '.join(discussion.supplements[:3])}")
        return " | ".join(parts)
