"""
学术调研专属模块 — Consensus Pipeline v4.0

三线并行检索 + 期刊质量过滤 + 交叉验证 + 主题聚类 + 可视化 + 报告生成
"""

from .search_engine import AcademicSearchEngine
from .cross_validator import CrossValidator
from .visualizer import AcademicVisualizer
from .report_generator import ReportGenerator

__all__ = [
    "AcademicSearchEngine",
    "CrossValidator",
    "AcademicVisualizer",
    "ReportGenerator",
]
