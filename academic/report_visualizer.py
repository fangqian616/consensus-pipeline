"""
报告可视化 — Consensus Pipeline v5.1.3

生成3张核心图表（matplotlib PNG），嵌入最终报告：
  1. 年度发文量趋势柱状图
  2. 方法论占比饼图
  3. 期刊等级分布图
"""
import os
from typing import List, Dict, Any, Optional
from collections import Counter

from .search_engine import PaperCandidate


# 中文字体配置
_FONT_CONFIGURED = False

def _setup_chinese_font():
    """配置matplotlib中文字体"""
    global _FONT_CONFIGURED
    if _FONT_CONFIGURED:
        return
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties

        # 优先使用 Noto Serif CJK SC
        font_path = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
        if os.path.exists(font_path):
            plt.rcParams['font.family'] = ['Noto Serif CJK SC', 'serif']
            plt.rcParams['axes.unicode_minus'] = False
        else:
            # 回退：尝试系统自带的中文字体
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
    生成3张报告图表，返回 {图表名: PNG路径}。

    Args:
        papers: 论文列表（已分级）
        output_dir: 输出目录
        topic: 研究主题（用于标题）

    Returns:
        {"year_trend": "路径", "method_dist": "路径", "grade_dist": "路径"}
    """
    _setup_chinese_font()
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    results = {}

    # 图1：年度发文量趋势柱状图
    try:
        path1 = _plot_year_trend(papers, charts_dir, topic)
        results["year_trend"] = path1
    except Exception as e:
        print(f"  [WARN] 年度趋势图生成失败: {e}")

    # 图2：方法论占比饼图
    try:
        path2 = _plot_method_distribution(papers, charts_dir, topic)
        results["method_dist"] = path2
    except Exception as e:
        print(f"  [WARN] 方法分布图生成失败: {e}")

    # 图3：期刊等级分布图
    try:
        path3 = _plot_grade_distribution(papers, charts_dir, topic)
        results["grade_dist"] = path3
    except Exception as e:
        print(f"  [WARN] 等级分布图生成失败: {e}")

    plt.close('all')
    return results


def _plot_year_trend(papers: List[PaperCandidate], charts_dir: str, topic: str) -> str:
    """年度发文量趋势柱状图"""
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

    # 在柱子上方标注数量
    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.2,
                    str(count), ha='center', va='bottom', fontsize=8)

    ax.set_xlabel('年份', fontsize=11)
    ax.set_ylabel('论文数量', fontsize=11)
    title = f'研究趋势：{topic}' if topic else '年度发文量趋势'
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], rotation=45, fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # 标注关键转折点
    if len(years) > 3:
        peak_year = max(year_counts, key=year_counts.get)
        ax.annotate(f'峰值: {peak_year}年\n{year_counts[peak_year]}篇',
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
    """方法论占比饼图"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    # 方法关键词映射（互斥分类：每篇论文只归入第一个匹配的类别）
    # v5.1.5: 扩展到18类，与report_generator._compute_method_distribution对齐
    method_keywords = {
        "LSTM/GRU": ["lstm", "gru", "rnn", "recurrent"],
        "Transformer": ["transformer", "attention", "bert", "gpt"],
        "CNN": ["cnn", "convolutional", "convnet"],
        "XGBoost/GBDT": ["xgboost", "gbdt", "gradient boosting", "lightgbm", "catboost"],
        "GNN/图网络": ["gnn", "graph neural", "graph convolution"],
        "因果推断": ["causal", "did", "difference-in-diff", "instrumental", "causal inference"],
        "强化学习": ["reinforcement", "rl ", "deep q", "policy gradient"],
        "贝叶斯方法": ["bayesian", "mcmc", "variational inference"],
        "集成学习": ["ensemble", "stacking", "bagging", "random forest"],
        "优化算法": ["optimization", "pso", "genetic algorithm", "evolutionary"],
        "NLP/文本": ["nlp", "text mining", "sentiment", "word2vec", "topic model"],
        "联邦学习": ["federated", "federated learning"],
        "分解-集成": ["emd", "ceemdan", "vmd", "wavelet", "decompos", "empirical mode", "eemd"],
        "混合模型": ["hybrid", "combined model", "ensemble deep", "multi-model", "fusion"],
        "物理信息融合": ["physics-informed", "pinns", "physics-guided", "mechanism", "domain knowledge"],
        "迁移学习": ["transfer learn", "domain adapt", "pre-train", "fine-tun"],
        "SVAR/计量": ["svar", "var ", "vecm", "cointegrat", "econometric", "granger"],
        "SVM/SVR": ["svm", "svr", "support vector", "kernel method"],
    }

    # 互斥分类：每篇论文只归入第一个匹配的类别
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
                break  # 每篇论文只归入第一个匹配的类别
        # 未匹配任何类别的论文归入"其他"
        if not matched:
            counts["其他"] = counts.get("其他", 0) + 1

    if not counts:
        return ""

    # 合并小分类（<3%归入其他），互斥分类下total = len(papers)
    total = len(papers)
    merged = {}
    other_extra = 0
    for cat, c in counts.items():
        if cat == "其他":
            other_extra += c
        elif c / total < 0.03 and len(merged) >= 5:
            other_extra += c
        else:
            merged[cat] = c
    if other_extra > 0:
        merged["其他"] = merged.get("其他", 0) + other_extra

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

    title = f'方法论分布：{topic}' if topic else '方法论占比分布'
    ax.set_title(title, fontsize=13, fontweight='bold')

    plt.tight_layout()
    path = os.path.join(charts_dir, "method_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def _plot_grade_distribution(papers: List[PaperCandidate], charts_dir: str, topic: str) -> str:
    """期刊等级分布图"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    grade_counts = Counter()
    for p in papers:
        level = p.quality_level or "未分级"
        grade_counts[level] += 1

    # 按等级排序
    grade_order = ["S", "A", "B", "C", "未分级"]
    grades = [g for g in grade_order if g in grade_counts]
    counts = [grade_counts[g] for g in grades]

    if not grades:
        return ""

    grade_colors = {
        "S": "#E91E63",  # 红色-顶级
        "A": "#FF9800",  # 橙色-优秀
        "B": "#2196F3",  # 蓝色-良好
        "C": "#9E9E9E",  # 灰色-一般
        "未分级": "#BDBDBD",
    }
    colors = [grade_colors.get(g, "#BDBDBD") for g in grades]

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(grades, counts, color=colors, edgecolor='white', linewidth=1, width=0.6)

    # 在柱子上方标注数量和占比
    total = sum(counts)
    for bar, count in zip(bars, counts):
        pct = f"{count / total * 100:.1f}%" if total > 0 else ""
        ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.3,
                f'{count}\n({pct})', ha='center', va='bottom', fontsize=10, fontweight='bold')

    grade_labels = {
        "S": "S级（顶刊）",
        "A": "A级（优秀）",
        "B": "B级（良好）",
        "C": "C级（一般）",
        "未分级": "未分级",
    }
    ax.set_xticklabels([grade_labels.get(g, g) for g in grades], fontsize=10)
    ax.set_ylabel('论文数量', fontsize=11)
    title = f'期刊等级分布：{topic}' if topic else '期刊等级分布'
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    path = os.path.join(charts_dir, "grade_distribution.png")
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path
