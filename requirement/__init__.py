"""
Requirement Research Module — Consensus Pipeline v0.7.0

Conversational requirement gathering → Structuring → Discussion group → Config recommendation → Fact checking
"""

from .interviewer import RequirementInterviewer, RequirementDocument
from .structurer import RequirementStructurer, StructuredRequirement
from .discussion_group import DiscussionGroup, DiscussionResult
from .config_recommender import ConfigRecommender
from .fact_checker import FactChecker, FactCheckReport, FactCheckResult
