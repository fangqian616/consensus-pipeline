"""
Academic Research Module — Consensus Pipeline v4.4

Triple-source parallel search + journal quality filtering (local + easyScholar API)
+ cross-validation + 9-dimension clustering + visualization + report generation.
v4.4: Search API upgrade ensuring 20+ papers; preprints in standalone appendix.
"""

from .journal_registry import JOURNAL_QUALITY_REGISTRY
from .search_engine import AcademicSearchEngine, PaperCandidate, classify_journal, safe_truncate
from .cross_validator import CrossValidator, ClusterResult, ValidationResult
from .visualizer import AcademicVisualizer, ChartConfig
from .report_generator import ReportGenerator
from .journal_classifier import classify_journal_enhanced, batch_classify_journals, query_easyscholar
