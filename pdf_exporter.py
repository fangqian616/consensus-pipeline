"""
PDF Exporter — Consensus Pipeline v4.3

Converts Markdown content to PDF, supporting mixed Chinese-English text.
Supports: academic reports, program department output, tutorial department output, fact-check reports.
"""
import os
import re
import tempfile
from typing import Optional, List, Dict, Any

from fpdf import FPDF


# Font paths — prefer project-local fonts/ dir, fallback to system fonts
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_FONT_CANDIDATES = [
    os.path.join(_THIS_DIR, "fonts", "LXGWWenKai-Regular.ttf"),
    os.path.join(_THIS_DIR, "v4-run", "fonts", "LXGWWenKai-Regular.ttf"),
    "CJK_FONT_PATH_PLACEHOLDER",  # Chinese path — system-specific, do not translate
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
    """Character-level safe truncation, avoiding UTF-8 multi-byte boundary issues."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


class PipelinePDF(FPDF):
    """PDF generator with CJK font support"""

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
    Convert Markdown content to PDF.

    Args:
        markdown_content: Markdown-format content
        output_path: PDF output path
        title: PDF title

    Returns:
        PDF file path
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
        # Code block handling
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                _render_code_block(pdf, code_buffer)
                code_buffer = []
                in_code_block = False
            else:
                # Start code block
                if in_table:
                    _render_table(pdf, table_rows)
                    table_rows = []
                    in_table = False
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        # Table handling
        if "|" in line and line.strip().startswith("|"):
            # Skip separator row
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

        # Empty line
        if not line.strip():
            pdf.ln(3)
            continue

        # Headings
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
        # Blockquote
        elif line.strip().startswith(">"):
            pdf.set_font("zh", "", 10)
            pdf.set_text_color(100, 100, 100)
            quote_text = line.strip().lstrip(">").strip()
            pdf.set_x(20)
            _write_line(pdf, quote_text, max_width=170)
            pdf.ln(2)
        # List items
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
        # Horizontal rule
        elif line.strip() == "---":
            pdf.ln(3)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        # Normal paragraph
        else:
            pdf.set_font("zh", "", 10)
            pdf.set_text_color(30, 30, 30)
            _write_line(pdf, line.strip())
            pdf.ln(2)

    # Handle unclosed tables or code blocks
    if in_table and table_rows:
        _render_table(pdf, table_rows)
    if in_code_block and code_buffer:
        _render_code_block(pdf, code_buffer)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    pdf.output(output_path)
    return output_path


def _write_line(pdf: PipelinePDF, text: str, max_width: int = 190):
    """Write a line of text with auto-wrap handling"""
    # Strip bold/italic/code markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)

    if not text:
        return

    try:
        pdf.multi_cell(max_width, 6, text)
    except Exception:
        # Fallback: safe truncation
        pdf.multi_cell(max_width, 6, safe_truncate(text, 200))


def _render_code_block(pdf: PipelinePDF, lines: List[str]):
    """Render a code block"""
    pdf.ln(2)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("zh", "", 8)
    pdf.set_text_color(50, 50, 50)

    code_text = "\n".join(lines)
    # Limit code block length (safe truncation)
    if len(code_text) > 3000:
        code_text = safe_truncate(code_text, 3000) + "\n... (truncated)"

    for code_line in code_text.split("\n"):
        pdf.set_x(15)
        pdf.cell(180, 5, safe_truncate(code_line, 120), fill=True)
        pdf.ln()

    pdf.ln(3)
    pdf.set_text_color(30, 30, 30)


def _render_table(pdf: PipelinePDF, rows: List[List[str]]):
    """Render a table"""
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
    Generate an academic research PDF report.

    Args:
        topic: Research topic
        papers: List of candidate papers
        clusters: Clustering results
        validations: Validation results
        charts: Chart configurations
        consensus_points: Consensus conclusions
        fact_check_summary: Fact-check summary
        output_dir: Output directory

    Returns:
        PDF file path
    """
    # First generate Markdown via report_generator
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

    # Read Markdown and convert to PDF
    md_path = result["markdown"]
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    safe_topic = topic.replace("/", "_").replace("\\", "_").replace(" ", "_")[:50]
    pdf_path = os.path.join(output_dir, f"{safe_topic}_academic_report.pdf")
    return markdown_to_pdf(md_content, pdf_path, title=f"Academic Research — {topic}")


def generate_department_pdf(
    department_name: str,
    debate_output: str,
    output_dir: str = "./output",
) -> str:
    """
    Convert department debate output to PDF.

    Args:
        department_name: Department name (e.g. "Program" / "Tutorial")
        debate_output: Debate output content (Markdown format)
        output_dir: Output directory

    Returns:
        PDF file path
    """
    os.makedirs(output_dir, exist_ok=True)

    # Wrap into a complete report
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d")
    full_md = f"# {department_name} Debate Output Report\n\n> Consensus Pipeline v4.3 | Generated: {now}\n\n---\n\n{debate_output}"
    safe_name = department_name.replace("/", "_").replace("\\", "_")
    pdf_path = os.path.join(output_dir, f"{safe_name}_debate_report.pdf")
    return markdown_to_pdf(full_md, pdf_path, title=f"{department_name} Debate Output")
