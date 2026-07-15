"""
需求调研通用模块 — Consensus Pipeline v4.0

对话式需求调研 → 结构化 → 讨论组 → 配置推荐 → 事实校验
"""

from .interviewer import RequirementInterviewer, RequirementDocument
from .structurer import RequirementStructurer, StructuredRequirement
from .discussion_group import DiscussionGroup, DiscussionResult
from .config_recommender import ConfigRecommender
from .fact_checker import FactChecker, FactCheckReport, FactCheckResult
