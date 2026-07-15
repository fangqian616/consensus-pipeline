"""
学术调研专属模块 — Consensus Pipeline v4.3

三线并行检索 + 期刊质量过滤（本地+easyScholar API）+ 交叉验证 + 主题聚类 + 可视化 + 报告生成
"""

from .journal_registry import JOURNAL_QUALITY_REGISTRY
from .search_engine import AcademicSearchEngine, PaperCandidate, classify_journal, safe_truncate
from .cross_validator import CrossValidator, ClusterResult, ValidationResult
from .visualizer import AcademicVisualizer, ChartConfig
from .report_generator import ReportGenerator
from .journal_classifier import classify_journal_enhanced, batch_classify_journals, query_easyscholar
