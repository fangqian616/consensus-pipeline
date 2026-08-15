"""
Academic Research Module — Consensus Pipeline v4.4

Triple-source parallel search + journal quality filtering (local + easyScholar API)
+ cross-validation + 9-dimension clustering + visualization + report generation.
v4.4: Search API upgrade ensuring 20+ papers; preprints in standalone appendix.
"""

from .search_engine import AcademicSearchEngine, PaperCandidate, safe_truncate
from .cross_validator import CrossValidator, ClusterResult, ValidationResult
from .visualizer import AcademicVisualizer, ChartConfig
from .report_generator import ReportGenerator
from .journal_classifier import query_easyscholar
