"""
Report Visualization — Consensus Pipeline v5.1.3

Generate 3 core charts (matplotlib PNG) for embedding in final reports:
  1. Year-over-year publication trend bar chart
  2. Methodology distribution pie chart
  3. Journal grade distribution bar chart
"""
import os
from typing import List, Dict, Any, Optional
from collections import Counter

from .search_engine import PaperCandidate


# CJK font configuration
_FONT_CONFIGURED = False

def _setup_chinese_font():
    """Configure matplotlib CJK font for proper Chinese rendering"""
    global _FONT_CONFIGURED
    if _FONT_CONFIGURED:
        return
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties

        # Prefer Noto Serif CJK SC
        font_path = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
        if os.path.exists(font_path):
            plt.rcParams['font.family'] = ['Noto Serif CJK SC', 'serif']
            plt.rcParams['axes.unicode_minus'] = False
        else:
            # Fallback: try system CJK fonts
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
    except Exception:
        pass
    _FONT_CONFIGURED = True


def generate_report_charts(
    papers: List[PaperCandidate],
    output_dir: str,
    topic: str = "",
) -> Dict[str, str]:
    """
    Generate 3 report charts, returning {chart_name: PNG_path}.

    Args:
        papers: Paper list (already graded)
        output_dir: Output directory
        topic: Research topic (used in titles)

    Returns:
        {"year_trend": "path", "method_dist": "path", "grade_dist": "path"}
    """
    _setup_chinese_font()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    results = {}

    # Chart 1: Year-over-year publication trend
    try:
        path1 = _plot_year_trend(papers, charts_dir, topic)
        results["year_trend"] = path1
    except Exception as e:
        print(f"  [WARN] 年度趋势图生成失败 / Year trend chart failed: {e}")

    # Chart 2: Methodology distribution
    try:
        path2 = _plot_method_distribution(papers, charts_dir, topic)
        results["method_dist"] = path2
    except Exception as e:
        print(f"  [WARN] 方法分布图生成失败 / Method distribution chart failed: {e}")

    # Chart 3: Journal grade distribution
    try:
        path3 = _plot_grade_distribution(papers, charts_dir, topic)
        results["grade_dist"] = path3
    except Exception as e:
        print(f"  [WARN] 等级分布图生成失败 / Grade distribution chart failed: {e}")

    plt.close('all')
    return results


def _plot_year_trend(papers: List[PaperCandidate], charts_dir: str, topic: str) -> str:
    """Year-over-year publication trend bar chart"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    year_counts = Counter()
    for p in papers:
        if p.year and p.year > 1990:
            year_counts[p.year] += 1

    if not year_counts:
        return ""

    years = sorted(year_counts.keys())
    counts = [year_counts[y] for y in years]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ['#2196F3' if c < max(counts) * 0.7 else '#FF5722' for c in counts]

    bars = ax.bar(years, counts, color=colors, edgecolor='white', linewidth=0.5)

    # Annotate bar counts
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.2,
                    str(count), ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('年份 / Year', fontsize=11)
    ax.set_ylabel('论文数量 / Paper Count', fontsize=11)
    title = f'研究趋势 / Research Trend：{topic}' if topic else '年度发文量趋势 / Publication Trend'
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], rotation=45, fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Annotate peak turning point
    if len(years) > 3:
        peak_year = max(year_counts, key=year_counts.get)
        ax.annotate(f'峰值/Peak: {peak_year}\n{year_counts[peak_year]}篇/papers',
                    xy=(peak_year, year_counts[peak_year]),
                    xytext=(peak_year - 2, year_counts[peak_year] + 2),
                    arrowprops=dict(arrowstyle='->', color='#E91E63'),
                    fontsize=9, color='#E91E63', fontweight='bold')

    plt.tight_layout()
    path = os.path.join(charts_dir, "year_trend.png")
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _plot_method_distribution(papers: List[PaperCandidate], charts_dir: str, topic: str) -> str:
    """Methodology distribution pie chart"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # Method keyword mapping (mutually exclusive: each paper assigned to first matching category)
    # v5.1.5: Extended to 18 categories, aligned with report_generator._compute_method_distribution
    method_keywords = {
        "LSTM/GRU": ["lstm", "gru", "rnn", "recurrent"],
        "Transformer": ["transformer", "attention", "bert", "gpt"],
        "CNN": ["cnn", "convolutional", "convnet"],
        "XGBoost/GBDT": ["xgboost", "gbdt", "gradient boosting", "lightgbm", "catboost"],
        "GNN/Graph": ["gnn", "graph neural", "graph convolution"],
        "Causal Inference": ["causal", "did", "difference-in-diff", "instrumental", "causal inference"],
        "Reinforcement Learning": ["reinforcement", "rl ", "deep q", "policy gradient"],
        "Bayesian": ["bayesian", "mcmc", "variational inference"],
        "Ensemble Learning": ["ensemble", "stacking", "bagging", "random forest"],
        "Optimization": ["optimization", "pso", "genetic algorithm", "evolutionary"],
        "NLP/Text": ["nlp", "text mining", "sentiment", "word2vec", "topic model"],
        "Federated Learning": ["federated", "federated learning"],
        "Decomposition-Ensemble": ["emd", "ceemdan", "vmd", "wavelet", "decompos", "empirical mode", "eemd"],
        "Hybrid Model": ["hybrid", "combined model", "ensemble deep", "multi-model", "fusion"],
        "Physics-Informed": ["physics-informed", "pinns", "physics-guided", "mechanism", "domain knowledge"],
        "Transfer Learning": ["transfer learn", "domain adapt", "pre-train", "fine-tun"],
        "SVAR/Econometrics": ["svar", "var ", "vecm", "cointegrat", "econometric", "granger"],
        "SVM/SVR": ["svm", "svr", "support vector", "kernel method"],
    }

    # Mutually exclusive classification: each paper assigned to first matching category only
    counts = {}
    classified = set()
    for i, p in enumerate(papers):
        text = (p.title + " " + (p.abstract or "")).lower()
        matched = False
        for cat, kws in method_keywords.items():
            if any(k in text for k in kws):
                counts[cat] = counts.get(cat, 0) + 1
                classified.add(i)
                matched = True
                break  # Each paper assigned to first matching category only
        # Unmatched papers go to "Other"
        if not matched:
            counts["Other/其他"] = counts.get("Other/其他", 0) + 1

    if not counts:
        return ""

    # Merge small categories (<3% into Other), total = len(papers) under mutually exclusive scheme
    total = len(papers)
    merged = {}
    other_extra = 0
    for cat, c in counts.items():
        if cat == "Other/其他":
            other_extra += c
        elif c / total < 0.03 and len(merged) >= 5:
            other_extra += c
        else:
            merged[cat] = c
    if other_extra > 0:
        merged["Other/其他"] = merged.get("Other/其他", 0) + other_extra

    labels = list(merged.keys())
    sizes = list(merged.values())
    colors = ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0',
              '#00BCD4', '#FF5722', '#607D8B', '#795548', '#3F51B5', '#CDDC39', '#FFC107']

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors[:len(labels)],
        startangle=90,
        pctdistance=0.8,
        textprops={'fontsize': 10},
    )
    for autotext in autotexts:
        autotext.set_fontsize(9)

    title = f'方法论分布 / Methodology Distribution：{topic}' if topic else '方法论占比分布 / Methodology Distribution'
    ax.set_title(title, fontsize=13, fontweight='bold')

    plt.tight_layout()
    path = os.path.join(charts_dir, "method_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _plot_grade_distribution(papers: List[PaperCandidate], charts_dir: str, topic: str) -> str:
    """Journal grade distribution bar chart"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    grade_counts = Counter()
    for p in papers:
        level = p.quality_level or "Ungraded"
        grade_counts[level] += 1

    # Sort by grade order
    grade_order = ["S", "A", "B", "C", "Ungraded"]
    grades = [g for g in grade_order if g in grade_counts]
    counts = [grade_counts[g] for g in grades]

    if not grades:
        return ""

    grade_colors = {
        "S": "#E91E63",  # Red — Top-tier
        "A": "#FF9800",  # Orange — Excellent
        "B": "#2196F3",  # Blue — Good
        "C": "#9E9E9E",  # Gray — Average
        "Ungraded": "#BDBDBD",
    }
    colors = [grade_colors.get(g, "#BDBDBD") for g in grades]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(grades, counts, color=colors, edgecolor='white', linewidth=1, width=0.6)

    # Annotate count and percentage above each bar
    total = sum(counts)
    for bar, count in zip(bars, counts):
        pct = f"{count / total * 100:.1f}%" if total > 0 else ""
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.3,
                f'{count}\n({pct})', ha='center', va='bottom', fontsize=10, fontweight='bold')

    grade_labels = {
        "S": "S (顶刊/Top)",
        "A": "A (优秀/Excellent)",
        "B": "B (良好/Good)",
        "C": "C (一般/Average)",
        "Ungraded": "未分级/Ungraded",
    }
    ax.set_xticklabels([grade_labels.get(g, g) for g in grades], fontsize=10)
    ax.set_ylabel('论文数量 / Paper Count', fontsize=11)
    title = f'期刊等级分布 / Journal Grade Distribution：{topic}' if topic else '期刊等级分布 / Journal Grade Distribution'
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    path = os.path.join(charts_dir, "grade_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path
