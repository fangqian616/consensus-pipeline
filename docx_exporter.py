"""
DOCX Exporter — Consensus Pipeline v5.1.5

Converts Markdown survey reports to professionally formatted Word documents (.docx).
Replaces the fpdf2 approach, resolving CJK font / emoji / table layout issues.

Dependency: python-docx
"""
import os
import re
from typing import Optional, List

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


# ── Style Constants ──
FONT_CN = "Microsoft YaHei"        # Primary font (available by default in WPS)
FONT_CN_FALLBACK = "DengXian"   # Fallback
FONT_EN = "Calibri"         # English font
FONT_MONO = "Consolas"      # Code font
COLOR_HEADING = RGBColor(0x1A, 0x1A, 0x2E)   # Dark blue-black
COLOR_BODY = RGBColor(0x33, 0x33, 0x33)       # Body dark gray
COLOR_S = RGBColor(0xC0, 0x39, 0x2B)          # S-tier red
COLOR_A = RGBColor(0xE6, 0x7E, 0x22)          # A-tier orange
COLOR_B = RGBColor(0x27, 0xAE, 0x60)          # B-tier green
COLOR_LINK = RGBColor(0x29, 0x80, 0xB9)       # Link blue


def _set_run_font(run, font_cn=FONT_CN, font_en=FONT_EN, size=Pt(10.5),
                  bold=False, italic=False, color=None):
    """Set run font properties"""
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font_en
    # CJK font
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_cn)
    if color:
        run.font.color.rgb = color


def _add_heading(doc, text, level=1):
    """Add a heading"""
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        _set_run_font(run, font_cn=FONT_CN, size=Pt(16 - level * 2),
                      bold=True, color=COLOR_HEADING)
    return p


def _add_body(doc, text, bold=False, color=None, alignment=None):
    """Add a body paragraph"""
    p = doc.add_paragraph()
    if alignment:
        p.alignment = alignment
    # Parse inline format: **bold** and [N] references
    _parse_inline(p, text, bold=bold, color=color)
    return p


def _parse_inline(paragraph, text, bold=False, italic=False, color=None):
    """Parse inline Markdown format, add runs"""
    # Split: **bold** and plain text
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            inner = part[2:-2]
            run = paragraph.add_run(inner)
            _set_run_font(run, bold=True, italic=italic, color=color)
        else:
            # Handle [N] references
            ref_parts = re.split(r'(\[\d+\])', part)
            for rp in ref_parts:
                run = paragraph.add_run(rp)
                if re.match(r'\[\d+\]', rp):
                    _set_run_font(run, bold=True, color=COLOR_LINK, size=Pt(10.5))
                else:
                    _set_run_font(run, bold=bold, italic=italic, color=color)


def _add_table(doc, headers, rows):
    """Add a table"""
    if not headers or not rows:
        return
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Table header
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(h.strip())
        _set_run_font(run, bold=True, size=Pt(9.5), color=RGBColor(0xFF, 0xFF, 0xFF))

    # Data rows
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            if c_idx < len(headers):
                cell = table.rows[r_idx + 1].cells[c_idx]
                cell.text = ''
                p = cell.paragraphs[0]
                run = p.add_run(str(val).strip())
                _set_run_font(run, size=Pt(9))

    doc.add_paragraph()  # Blank line after table


def _add_image(doc, image_path, width=Inches(5.5)):
    """Add an image"""
    if os.path.exists(image_path):
        try:
            doc.add_picture(image_path, width=width)
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception:
            p = doc.add_paragraph(f'[Chart: {os.path.basename(image_path)}]')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                _set_run_font(run, italic=True, color=RGBColor(0x99, 0x99, 0x99))


def _add_caption(doc, text):
    """Add a figure caption"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    _set_run_font(run, italic=True, size=Pt(9), color=RGBColor(0x66, 0x66, 0x66))


def _add_code_block(doc, code_text):
    """Add a code block (gray-shaded paragraph)"""
    for line in code_text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        _set_run_font(run, font_cn=FONT_MONO, font_en=FONT_MONO, size=Pt(8.5),
                      color=RGBColor(0x2C, 0x3E, 0x50))
        # Add background shading
        shading = run._element.makeelement(qn('w:shd'), {
            qn('w:val'): 'clear',
            qn('w:color'): 'auto',
            qn('w:fill'): 'F5F5F5'
        })
        run._element.rPr.append(shading)


def markdown_to_docx(md_path: str, docx_path: str,
                     title: str = "Academic Survey Report",
                     charts_dir: str = None) -> str:
    """
    Convert a Markdown report to a professionally formatted Word document.

    Args:
        md_path: Markdown file path
        docx_path: Output docx file path
        title: Document title
        charts_dir: Charts directory (relative to md_path parent)

    Returns:
        Generated docx file path
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = Document()

    # ── Global Styles ──
    style = doc.styles['Normal']
    style.font.name = FONT_EN
    style.font.size = Pt(10.5)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_CN)
    style.paragraph_format.line_spacing = 1.35
    style.paragraph_format.space_after = Pt(4)

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.8)

    base_dir = os.path.dirname(os.path.abspath(md_path))
    if charts_dir is None:
        charts_dir = os.path.join(base_dir, "charts")

    # ── Line-by-line Parsing ──
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]

        # Code block
        if line.strip().startswith('```'):
            if in_code_block:
                _add_code_block(doc, '\n'.join(code_lines))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Empty line
        if not line.strip():
            if in_table and table_rows:
                _flush_table(doc, table_rows)
                table_rows = []
                in_table = False
            i += 1
            continue

        # Table row
        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
            # Skip separator row
            if all(set(c) <= set('-: ') for c in cells):
                i += 1
                continue
            in_table = True
            table_rows.append(cells)
            i += 1
            continue
        elif in_table and table_rows:
            _flush_table(doc, table_rows)
            table_rows = []
            in_table = False

        # Heading
        heading_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            # Remove space before emoji
            _add_heading(doc, text, level=min(level, 4))
            i += 1
            continue

        # Blockquote
        if line.strip().startswith('>'):
            text = line.strip().lstrip('>').strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            _parse_inline(p, text, italic=True, color=RGBColor(0x55, 0x55, 0x55))
            i += 1
            continue

        # Image
        img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
        if img_match:
            alt_text = img_match.group(1)
            img_path = img_match.group(2)
            # Convert relative path to absolute
            if not os.path.isabs(img_path):
                img_path = os.path.join(base_dir, img_path)
            _add_image(doc, img_path)
            # Next line may be a caption (*italic*)
            i += 1
            if i < len(lines) and lines[i].strip().startswith('*') and lines[i].strip().endswith('*'):
                caption = lines[i].strip().strip('*')
                _add_caption(doc, caption)
                i += 1
            continue

        # Reference tier heading (### S-tier (top journal) etc.)
        ref_level_match = re.match(r'###\s+(S级|A级|B级)', line)  # Matches Chinese tier labels in generated reports
        if ref_level_match:
            level_text = ref_level_match.group(1)
            color_map = {'S级': COLOR_S, 'A级': COLOR_A, 'B级': COLOR_B}  # Chinese tier labels — must match generated report headers
            p = doc.add_paragraph()
            run = p.add_run(line.strip().lstrip('#').strip())
            _set_run_font(run, bold=True, size=Pt(12), color=color_map.get(level_text, COLOR_BODY))
            i += 1
            continue

        # Normal paragraph
        _add_body(doc, line.strip())
        i += 1

    # Flush remaining table rows
    if in_table and table_rows:
        _flush_table(doc, table_rows)

    # ── Footer ──
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("— Generated by Consensus Pipeline —")
    _set_run_font(run, italic=True, size=Pt(8), color=RGBColor(0xAA, 0xAA, 0xAA))

    doc.save(docx_path)
    return docx_path


def _flush_table(doc, rows):
    """Flush accumulated table rows into document"""
    if not rows:
        return
    headers = rows[0]
    data = rows[1:]
    _add_table(doc, headers, data)


def generate_department_docx(md_path: str, docx_path: str,
                             dept_name: str = "") -> str:
    """
    Convert department output (Program / Tutorial) to docx
    """
    return markdown_to_docx(md_path, docx_path, title=dept_name or "Department Output")
