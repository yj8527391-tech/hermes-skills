# -*- coding: utf-8 -*-
"""md -> 单节国标格式 docx（学生作业 / 实践调研报告 / 实习报告：无封面、无目录）

用法: python gb_report_docx.py 输入.md 输出.docx

md 约定：
  # 主标题              -> 黑体三号居中
  ## ——副标题            -> 宋体小四居中
  学院：…               -> 信息行（宋体小四居中）
  附件3                 -> 抬头行（左对齐）
  ## 一、xxx             -> 一级标题（黑体四号）
  ### （一）xxx          -> 二级标题（宋体小四加粗，首行缩进）
  | a | b |             -> 三线表（表题自动加在上方）
  其余非空行            -> 正文（宋体小四 / 1.5倍行距 / 段前后0 / 首行缩进2字符）
  --- 空行              -> 丢弃

国标版式：A4，上下2.5cm 左右3cm，页脚居中「— 1 —」。
2026-11 实测：主人交作业的默认格式（不要蓝字、段间不空行、首行缩进2字符）。
"""
import re
import sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SONG, HEI = '宋体', '黑体'
THEME_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")


def force_font(run, font, size, bold=False):
    """强制中文字体+字号+纯黑，并清掉 theme 属性（否则 Word 会套主题变成蓝色等线体）"""
    run.font.name = font
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = False
    run.font.color.rgb = RGBColor(0, 0, 0)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    for a in THEME_ATTRS:
        attr = qn('w:' + a)
        if rFonts.get(attr) is not None:
            del rFonts.attrib[attr]
    for a in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        rFonts.set(qn('w:' + a), font)


def setup(doc):
    s = doc.sections[0]
    s.page_height, s.page_width = Cm(29.7), Cm(21.0)
    s.top_margin = s.bottom_margin = Cm(2.5)
    s.left_margin = s.right_margin = Cm(3.0)
    st = doc.styles['Normal']
    st.font.name = SONG
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), SONG)
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.space_after = Pt(0)


def first_line_indent(p, chars=200):
    pPr = p._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind')
        pPr.append(ind)
    ind.set(qn('w:firstLineChars'), str(chars))
    ind.set(qn('w:firstLine'), '0')


def para(doc, text, size=12, bold=False, font=SONG, align=None,
         indent=True, before=0, after=0, spacing=1.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = spacing
    if align is not None:
        p.alignment = align
    if indent:
        first_line_indent(p)
    r = p.add_run(text)
    force_font(r, font, size, bold)
    return p


def add_page_number(doc):
    fp = doc.sections[0].footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = fp.add_run('— ')
    force_font(r1, SONG, 10.5)
    run = fp.add_run()
    force_font(run, SONG, 10.5)
    begin = OxmlElement('w:fldChar')
    begin.set(qn('w:fldCharType'), 'begin')
    run._element.append(begin)
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = 'PAGE'
    run._element.append(instr)
    sep = OxmlElement('w:fldChar')
    sep.set(qn('w:fldCharType'), 'separate')
    run._element.append(sep)
    t = OxmlElement('w:t')
    t.text = '1'
    run._element.append(t)
    end = OxmlElement('w:fldChar')
    end.set(qn('w:fldCharType'), 'end')
    run._element.append(end)
    r2 = fp.add_run(' —')
    force_font(r2, SONG, 10.5)


def three_line(table):
    """国标三线表：上下粗线 + 表头下细线，去竖线与内横线"""
    tbl = table._tbl
    borders = OxmlElement('w:tblBorders')
    for edge, sz, val in (('top', 12, 'single'), ('bottom', 12, 'single'),
                          ('left', 0, 'none'), ('right', 0, 'none'),
                          ('insideH', 0, 'none'), ('insideV', 0, 'none')):
        el = OxmlElement('w:' + edge)
        el.set(qn('w:val'), val)
        el.set(qn('w:sz'), str(sz))
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), '000000')
        borders.append(el)
    tbl.tblPr.append(borders)
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        b = OxmlElement('w:tcBorders')
        e = OxmlElement('w:bottom')
        e.set(qn('w:val'), 'single')
        e.set(qn('w:sz'), '8')
        e.set(qn('w:space'), '0')
        e.set(qn('w:color'), '000000')
        b.append(e)
        tcPr.append(b)


def add_table(doc, rows, caption=None):
    if caption:
        para(doc, caption, size=10.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
             indent=False, before=6, after=3, spacing=1.0)
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    for i, row in enumerate(rows):
        for j, text in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ''
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(text))
            force_font(r, SONG, 10.5, bold=(i == 0))
    three_line(t)


def build(md_path, docx_path):
    lines = open(md_path, encoding='utf-8').read().splitlines()
    doc = Document()
    setup(doc)
    add_page_number(doc)

    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s or s == '---':
            i += 1
            continue

        if s.startswith('|'):
            block = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                block.append(lines[i].strip())
                i += 1
            rows = []
            for line in block:
                if re.fullmatch(r'\|[\s\-:|]+\|', line):
                    continue
                rows.append([c.strip() for c in line.strip('|').split('|')])
            cap = '表1  ' + rows[0][0] + '分布' if rows else None
            add_table(doc, rows, cap)
            continue

        if s.startswith('# ') and not s.startswith('## '):
            para(doc, s[2:].strip(), 16, True, HEI, WD_ALIGN_PARAGRAPH.CENTER, False, 0, 6)
        elif s.startswith('## ——') or s.startswith('## --'):
            para(doc, s[3:].strip(), 12, False, SONG, WD_ALIGN_PARAGRAPH.CENTER, False, 0, 10)
        elif s.startswith('学院：') or s.startswith('附件'):
            para(doc, s, 12, False, SONG, None, False, 0, 10)
        elif s.startswith('## '):
            para(doc, s[3:].strip(), 14, True, HEI, None, False, 12, 6)
        elif s.startswith('### '):
            para(doc, s[4:].strip(), 12, True, SONG, None, True, 6, 3)
        else:
            para(doc, s, 12, False, SONG, None, True, 0, 0)
        i += 1

    doc.save(docx_path)
    print('saved:', docx_path)


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
