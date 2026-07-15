"""
期刊质量分级注册表 — Consensus Pipeline v4.3

独立的期刊注册表模块，避免 journal_classifier ↔ search_engine 循环导入。

数据来源：
- 能源经济学领域：人工校验（2026-07-15）
- 其他领域：通过 easyScholar API 动态查询

等级说明：
- S：SCI/SSCI Q1 顶刊（IF≥5 或中科院1区）
- A：Q1 或中科院2区
- B：CSSCI/CSCD/Q2（B级上限2篇代表）
- C：有等级数据但不够高
- D：无等级数据或预警期刊
"""

JOURNAL_QUALITY_REGISTRY = {
    # === S级：SCI/SSCI Q1 顶刊 ===
    "Energy Economics": {"level": "S", "if_2026": 13.5, "jcr": "SSCI Q1", "note": "经济学第2/380"},
    "Applied Energy": {"level": "S", "if_2026": 11.0, "jcr": "SCIE Q1", "note": "偏工程"},
    "Nature Energy": {"level": "S", "if_2026": 56.0, "jcr": "SCIE Q1", "note": "综合科学顶刊"},
    "Journal of Environmental Economics and Management": {"level": "S", "if_2026": 6.4, "jcr": "SSCI Q1×3", "note": "环境资源经济学历史顶刊"},
    "JEEM": {"level": "S", "if_2026": 6.4, "jcr": "SSCI Q1×3", "note": "同Journal of Environmental Economics and Management"},
    "Energy Policy": {"level": "S", "if_2026": 9.2, "jcr": "SSCI Q1×4", "note": "四学科全Q1"},

    # === A级 ===
    "中国人口·资源与环境": {"level": "A", "if_2026": 11.481, "jcr": "CSSCI+CSCD", "note": "AMI权威+RCCSE A+"},

    # === B级 ===
    "The Energy Journal": {"level": "B", "if_2026": 2.8, "jcr": "SSCI Q2", "note": "经济学Q2"},
    "Resource and Energy Economics": {"level": "B", "if_2026": 3.1, "jcr": "SSCI Q1/Q3", "note": "经济学Q1但环境Q3"},
    "Utilities Policy": {"level": "B", "if_2026": 4.9, "jcr": "Q1(法学)/Q2-Q3", "note": ""},
    "Energy": {"level": "B", "if_2026": 9.0, "jcr": "SCIE Q1", "note": "偏工程，高发文量"},
}
