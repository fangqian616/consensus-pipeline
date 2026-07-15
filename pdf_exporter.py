"""
PDF导出器 — Consensus Pipeline v4.3

将Markdown内容转换为PDF，支持中英文混排。
支持：学术报告、程序部产出、教程部产出、事实校验报告。

v4.3: 字体路径改用__file__相对定位，修复多字节字符截断问题
"""
import os
import re
import tempfile
from typing import Optional, List, Dict, Any

from fpdf import FPDF


# 字体路径 — 优先项目内fonts目录，备选系统字体
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_FONT_CANDIDATES = [
    os.path.join(_THIS_DIR, "fonts", "LXGWWenKai-Regular.ttf"),
    os.path.join(_THIS_DIR, "v4-run", "fonts", "LXGWWenKai-Regular.ttf"),
    "CJK_FONT_PATH_PLACEHOLDER",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]

_FONT_BOLD_CANDIDATES = [
    os.path.join(_THIS_DIR, "fonts", "LXGWWenKai-Bold.ttf"),
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
]


def _find_font(candidates: List[str]) -> Optional[str]:
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def safe_truncate(text: str, max_chars: int = 200) -> str:
    """字符级安全截断，避免UTF-8多字节字符边界问题。"""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


class PipelinePDF(FPDF):
    """支持中文的PDF生成器"""

    def __init__(self, title: str = "Consensus Pipeline Report", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._title = title
        self._setup_fonts()
        self.set_auto_page_break(auto=True, margin=20)

    def _setup_fonts(self):
        font_regular = _find_font(_FONT_CANDIDATES)
        font_bold = _find_font(_FONT_BOLD_CANDIDATES)

        if font_regular:
            self.add_font("zh", "", font_regular, uni=True)
        else:
            self.add_font("zh", "", "Helvetica", uni=True)

        if font_bold:
            self.add_font("zh", "B", font_bold, uni=True)
        else:
            self.add_font("zh", "B", "Helvetica", uni=True)

    def header(self):
        self.set_font("zh", "B", 9)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, self._title, align="R")
        self.ln(3)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("zh", "", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def markdown_to_pdf(
    markdown_content: str,
    output_path: str,
    title: str = "Consensus Pipeline Report",
) -> str:
    """
    将Markdown内容转换为PDF。

    Args:
        markdown_content: Markdown格式内容
        output_path: PDF输出路径
        title: PDF标题

    Returns:
        PDF文件路径
    """
    pdf = PipelinePDF(title=title)
    pdf.alias_nb_pages()
    pdf.add_page()

    lines = markdown_content.split("\n")
    in_code_block = False
    code_buffer = []
    in_table = False
    table_rows = []

    for line in lines:
        # 代码块处理
        if line.strip().startswith("```"):
            if in_code_block:
                # 结束代码块
                _render_code_block(pdf, code_buffer)
                code_buffer = []
                in_code_block = False
            else:
                # 开始代码块
                if in_table:
                    _render_table(pdf, table_rows)
                    table_rows = []
                    in_table = False
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # 表格处理
        if "|" in line and line.strip().startswith("|"):
            # 分隔行跳过
            if re.match(r'^\|[\s\-:|]+\|$', line.strip()):
                continue
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            table_rows.append(cells)
            in_table = True
            continue
        elif in_table:
            _render_table(pdf, table_rows)
            table_rows = []
            in_table = False

        # 空行
        if not line.strip():
            pdf.ln(3)
            continue

        # 标题
        if line.startswith("# "):
            pdf.set_font("zh", "B", 18)
            pdf.set_text_color(30, 30, 30)
            _write_line(pdf, line[2:].strip())
            pdf.ln(6)
        elif line.startswith("## "):
            pdf.set_font("zh", "B", 14)
            pdf.set_text_color(40, 40, 40)
            _write_line(pdf, line[3:].strip())
            pdf.ln(5)
        elif line.startswith("### "):
            pdf.set_font("zh", "B", 12)
            pdf.set_text_color(50, 50, 50)
            _write_line(pdf, line[4:].strip())
            pdf.ln(4)
        elif line.startswith("#### "):
            pdf.set_font("zh", "B", 11)
            pdf.set_text_color(60, 60, 60)
            _write_line(pdf, line[5:].strip())
            pdf.ln(3)
        # 引用块
        elif line.strip().startswith(">"):
            pdf.set_font("zh", "", 10)
            pdf.set_text_color(100, 100, 100)
            quote_text = line.strip().lstrip(">").strip()
            pdf.set_x(20)
            _write_line(pdf, quote_text, max_width=170)
            pdf.ln(2)
        # 列表项
        elif re.match(r'^(\d+)\.\s', line.strip()):
            pdf.set_font("zh", "", 10)
            pdf.set_text_color(30, 30, 30)
            list_text = re.sub(r'^(\d+)\.\s', r'\1. ', line.strip())
            pdf.set_x(15)
            _write_line(pdf, list_text, max_width=180)
            pdf.ln(1)
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            pdf.set_font("zh", "", 10)
            pdf.set_text_color(30, 30, 30)
            bullet_text = line.strip()[2:].strip()
            pdf.set_x(15)
            pdf.cell(5, 6, chr(8226))  # bullet
            pdf.set_x(20)
            _write_line(pdf, bullet_text, max_width=175)
            pdf.ln(1)
        # 水平线
        elif line.strip() == "---":
            pdf.ln(3)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        # 普通段落
        else:
            pdf.set_font("zh", "", 10)
            pdf.set_text_color(30, 30, 30)
            _write_line(pdf, line.strip())
            pdf.ln(2)

    # 处理未闭合的表格或代码块
    if in_table and table_rows:
        _render_table(pdf, table_rows)
    if in_code_block and code_buffer:
        _render_code_block(pdf, code_buffer)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    pdf.output(output_path)
    return output_path


def _write_line(pdf: PipelinePDF, text: str, max_width: int = 190):
    """写入一行文本，处理自动换行"""
    # 简单处理粗体标记
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)

    if not text:
        return

    try:
        pdf.multi_cell(max_width, 6, text)
    except Exception:
        # 降级处理：安全截断
        pdf.multi_cell(max_width, 6, safe_truncate(text, 200))


def _render_code_block(pdf: PipelinePDF, lines: List[str]):
    """渲染代码块"""
    pdf.ln(2)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("zh", "", 8)
    pdf.set_text_color(50, 50, 50)

    code_text = "\n".join(lines)
    # 限制代码块长度（安全截断）
    if len(code_text) > 3000:
        code_text = safe_truncate(code_text, 3000) + "\n... (truncated)"

    for code_line in code_text.split("\n"):
        pdf.set_x(15)
        pdf.cell(180, 5, safe_truncate(code_line, 120), fill=True)
        pdf.ln()

    pdf.ln(3)
    pdf.set_text_color(30, 30, 30)


def _render_table(pdf: PipelinePDF, rows: List[List[str]]):
    """渲染表格"""
    if not rows:
        return

    pdf.ln(2)
    num_cols = len(rows[0]) if rows else 1
    col_width = min(180 / max(num_cols, 1), 60)

    for i, row in enumerate(rows):
        if i == 0:
            pdf.set_font("zh", "B", 9)
            pdf.set_fill_color(230, 230, 230)
        else:
            pdf.set_font("zh", "", 9)
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(30, 30, 30)
        max_h = 6
        for j, cell in enumerate(row[:num_cols]):
            cell_text = safe_truncate(str(cell), 50)
            pdf.cell(col_width, max_h, cell_text, border=1, fill=True)
        pdf.ln()

    pdf.ln(3)


def generate_academic_pdf(
    topic: str,
    papers: list,
    clusters: list,
    validations: list,
    charts: list,
    consensus_points: Optional[list] = None,
    fact_check_summary: str = "",
    output_dir: str = "./output",
) -> str:
    """
    生成学术调研PDF报告。

    Args:
        topic: 研究主题
        papers: 候选论文列表
        clusters: 聚类结果
        validations: 验证结果
        charts: 图表配置
        consensus_points: 共识结论
        fact_check_summary: 事实校验摘要
        output_dir: 输出目录

    Returns:
        PDF文件路径
    """
    # 先用report_generator生成Markdown
    from academic.report_generator import ReportGenerator
    gen = ReportGenerator(output_dir=output_dir)
    result = gen.generate(
        topic=topic,
        papers=papers,
        clusters=clusters,
        validations=validations,
        charts=charts,
        consensus_points=consensus_points,
        fact_check_summary=fact_check_summary,
    )

    # 读取Markdown转PDF
    md_path = result["markdown"]
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    safe_topic = topic.replace("/", "_").replace("\\", "_").replace(" ", "_")[:50]
    pdf_path = os.path.join(output_dir, f"{safe_topic}_academic_report.pdf")
    return markdown_to_pdf(md_content, pdf_path, title=f"学术调研 — {topic}")


def generate_department_pdf(
    department_name: str,
    debate_output: str,
    output_dir: str = "./output",
) -> str:
    """
    将部门辩论输出转为PDF。

    Args:
        department_name: 部门名称（如"程序部"/"教程部"）
        debate_output: 辩论输出内容（Markdown格式）
        output_dir: 输出目录

    Returns:
        PDF文件路径
    """
    os.makedirs(output_dir, exist_ok=True)

    # 包装成完整报告
    from datetime import datetime
    now = datetime.now().strftime("%Y年%m月%d日")
    full_md = f"# {department_name} 辩论产出报告\n\n> Consensus Pipeline v4.3 | 生成日期：{now}\n\n---\n\n{debate_output}"
    safe_name = department_name.replace("/", "_").replace("\\", "_")
    pdf_path = os.path.join(output_dir, f"{safe_name}_debate_report.pdf")
    return markdown_to_pdf(full_md, pdf_path, title=f"{department_name} 辩论产出")
