"""
DOCX导出器 — Consensus Pipeline v5.1.5

将Markdown综述报告转换为专业排版的Word文档(.docx)。
替代fpdf2方案，解决中文字体/emoji/表格排版问题。

依赖: python-docx
"""
import os
import re
from typing import Optional, List

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn


# ── 样式常量 ──
FONT_CN = "微软雅黑"        # 主字体（WPS默认有）
FONT_CN_FALLBACK = "等线"   # 备选
FONT_EN = "Calibri"         # 英文字体
FONT_MONO = "Consolas"      # 代码字体
COLOR_HEADING = RGBColor(0x1A, 0x1A, 0x2E)   # 深蓝黑
COLOR_BODY = RGBColor(0x33, 0x33, 0x33)       # 正文深灰
COLOR_S = RGBColor(0xC0, 0x39, 0x2B)          # S级-红
COLOR_A = RGBColor(0xE6, 0x7E, 0x22)          # A级-橙
COLOR_B = RGBColor(0x27, 0xAE, 0x60)          # B级-绿
COLOR_LINK = RGBColor(0x29, 0x80, 0xB9)       # 链接蓝


def _set_run_font(run, font_cn=FONT_CN, font_en=FONT_EN, size=Pt(10.5),
                  bold=False, italic=False, color=None):
    """设置run的字体属性"""
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font_en
    # 中文字体
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_cn)
    if color:
        run.font.color.rgb = color


def _add_heading(doc, text, level=1):
    """添加标题"""
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        _set_run_font(run, font_cn=FONT_CN, size=Pt(16 - level * 2),
                      bold=True, color=COLOR_HEADING)
    return p


def _add_body(doc, text, bold=False, color=None, alignment=None):
    """添加正文段落"""
    p = doc.add_paragraph()
    if alignment:
        p.alignment = alignment
    # 解析行内格式: **bold** 和 [N]引用
    _parse_inline(p, text, bold=bold, color=color)
    return p


def _parse_inline(paragraph, text, bold=False, italic=False, color=None):
    """解析行内markdown格式，添加runs"""
    # 分割: **bold** 和普通文本
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            inner = part[2:-2]
            run = paragraph.add_run(inner)
            _set_run_font(run, bold=True, italic=italic, color=color)
        else:
            # 处理 [N] 引用
            ref_parts = re.split(r'(\[\d+\])', part)
            for rp in ref_parts:
                run = paragraph.add_run(rp)
                if re.match(r'\[\d+\]', rp):
                    _set_run_font(run, bold=True, color=COLOR_LINK, size=Pt(10.5))
                else:
                    _set_run_font(run, bold=bold, italic=italic, color=color)


def _add_table(doc, headers, rows):
    """添加表格"""
    if not headers or not rows:
        return
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # 表头
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(h.strip())
        _set_run_font(run, bold=True, size=Pt(9.5), color=RGBColor(0xFF, 0xFF, 0xFF))

    # 数据行
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            if c_idx < len(headers):
                cell = table.rows[r_idx + 1].cells[c_idx]
                cell.text = ''
                p = cell.paragraphs[0]
                run = p.add_run(str(val).strip())
                _set_run_font(run, size=Pt(9))

    doc.add_paragraph()  # 表后空行


def _add_image(doc, image_path, width=Inches(5.5)):
    """添加图片"""
    if os.path.exists(image_path):
        try:
            doc.add_picture(image_path, width=width)
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception:
            p = doc.add_paragraph(f'[图表: {os.path.basename(image_path)}]')
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                _set_run_font(run, italic=True, color=RGBColor(0x99, 0x99, 0x99))


def _add_caption(doc, text):
    """添加图注"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    _set_run_font(run, italic=True, size=Pt(9), color=RGBColor(0x66, 0x66, 0x66))


def _add_code_block(doc, code_text):
    """添加代码块（灰色底纹段落）"""
    for line in code_text.split('\n'):
        p = doc.add_paragraph()
        run = p.add_run(line)
        _set_run_font(run, font_cn=FONT_MONO, font_en=FONT_MONO, size=Pt(8.5),
                      color=RGBColor(0x2C, 0x3E, 0x50))
        # 添加底纹
        shading = run._element.makeelement(qn('w:shd'), {
            qn('w:val'): 'clear',
            qn('w:color'): 'auto',
            qn('w:fill'): 'F5F5F5'
        })
        run._element.rPr.append(shading)


def markdown_to_docx(md_path: str, docx_path: str,
                     title: str = "学术综述报告",
                     charts_dir: str = None) -> str:
    """
    将Markdown报告转换为专业排版的Word文档。

    Args:
        md_path: Markdown文件路径
        docx_path: 输出docx文件路径
        title: 文档标题
        charts_dir: 图表目录（相对于md_path的父目录）

    Returns:
        生成的docx文件路径
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    doc = Document()

    # ── 全局样式 ──
    style = doc.styles['Normal']
    style.font.name = FONT_EN
    style.font.size = Pt(10.5)
    style._element.rPr.rFonts.set(qn('w:eastAsia'), FONT_CN)
    style.paragraph_format.line_spacing = 1.35
    style.paragraph_format.space_after = Pt(4)

    # 页边距
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.8)

    base_dir = os.path.dirname(os.path.abspath(md_path))
    if charts_dir is None:
        charts_dir = os.path.join(base_dir, "charts")

    # ── 逐行解析 ──
    lines = content.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    in_table = False
    table_rows = []

    while i < len(lines):
        line = lines[i]

        # 代码块
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

        # 空行
        if not line.strip():
            if in_table and table_rows:
                _flush_table(doc, table_rows)
                table_rows = []
                in_table = False
            i += 1
            continue

        # 表格行
        if '|' in line and line.strip().startswith('|'):
            cells = [c.strip() for c in line.strip().split('|')[1:-1]]
            # 分隔行跳过
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

        # 标题
        heading_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2).strip()
            # 去掉emoji前的空格
            _add_heading(doc, text, level=min(level, 4))
            i += 1
            continue

        # 引用块
        if line.strip().startswith('>'):
            text = line.strip().lstrip('>').strip()
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            _parse_inline(p, text, italic=True, color=RGBColor(0x55, 0x55, 0x55))
            i += 1
            continue

        # 图片
        img_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
        if img_match:
            alt_text = img_match.group(1)
            img_path = img_match.group(2)
            # 相对路径转绝对
            if not os.path.isabs(img_path):
                img_path = os.path.join(base_dir, img_path)
            _add_image(doc, img_path)
            # 下一行可能是图注（*斜体*）
            i += 1
            if i < len(lines) and lines[i].strip().startswith('*') and lines[i].strip().endswith('*'):
                caption = lines[i].strip().strip('*')
                _add_caption(doc, caption)
                i += 1
            continue

        # 参考文献等级标题（### S级（顶刊）等）
        ref_level_match = re.match(r'###\s+(S级|A级|B级)', line)
        if ref_level_match:
            level_text = ref_level_match.group(1)
            color_map = {'S级': COLOR_S, 'A级': COLOR_A, 'B级': COLOR_B}
            p = doc.add_paragraph()
            run = p.add_run(line.strip().lstrip('#').strip())
            _set_run_font(run, bold=True, size=Pt(12), color=color_map.get(level_text, COLOR_BODY))
            i += 1
            continue

        # 普通段落
        _add_body(doc, line.strip())
        i += 1

    # 刷出剩余表格
    if in_table and table_rows:
        _flush_table(doc, table_rows)

    # ── 页脚 ──
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("— Consensus Pipeline 生成 —")
    _set_run_font(run, italic=True, size=Pt(8), color=RGBColor(0xAA, 0xAA, 0xAA))

    doc.save(docx_path)
    return docx_path


def _flush_table(doc, rows):
    """将累积的表格行写入文档"""
    if not rows:
        return
    headers = rows[0]
    data = rows[1:]
    _add_table(doc, headers, data)


def generate_department_docx(md_path: str, docx_path: str,
                             dept_name: str = "") -> str:
    """
    将部门产出（程序部/教程部）转为docx
    """
    return markdown_to_docx(md_path, docx_path, title=dept_name or "部门产出")
