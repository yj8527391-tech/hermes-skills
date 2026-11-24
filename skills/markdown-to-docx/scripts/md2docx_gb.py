# -*- coding: utf-8 -*-
"""md -> 国标格式 docx：封面 + 目录(TOC域) + 正文(页码从1重排)。
国标版式：A4 / 页边距上2.5下2.5左3右3cm / 标题黑体 / 正文宋体小四12pt / 1.4倍行距 / 首行缩进2字符 / 无斜体无灰字。
用法：python md2docx_gb.py <输入.md> <输出.docx>
md 结构约定：# 封面主标题 / > 封面副标题 / ## 各节标题(进目录 Heading1) / 其余非空行=正文段落
验证：len(doc.sections)==3；正文 footer XML 有 1 个 PAGE，封面/目录 footer 无 PAGE；document.xml 有 1 个 TOC；settings.xml 有 updateFields。
"""
import re
import sys
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SONG = '宋体'
HEI = '黑体'
THEME_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")


def force_font(run, font, size=None, bold=False, color_black=True):
    run.font.name = font
    if size is not None:
        run.font.size = Pt(size)
    run.bold = bold
    if color_black:
        run.font.color.rgb = RGBColor(0, 0, 0)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    for a in THEME_ATTRS:
        attr = qn('w:' + a)
        if rFonts.get(attr) is not None:
            del rFonts.attrib[attr]
    for a in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
        rFonts.set(qn('w:' + a), font)


def setup_page(section):
    section.page_height = Cm(29.7)
    section.page_width = Cm(21.0)
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(3.0)


def clear_footer(section):
    section.footer.is_linked_to_previous = False
    for p in section.footer.paragraphs:
        p.text = ''


def add_field(paragraph, instr_text, placeholder=''):
    run = paragraph.add_run()
    begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = instr_text
    sep = OxmlElement('w:fldChar'); sep.set(qn('w:fldCharType'), 'separate')
    res = OxmlElement('w:t'); res.text = placeholder
    end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
    for el in (begin, instr, sep, res, end):
        run._element.append(el)
    return run


def restart_page_numbering(section, start=1):
    sectPr = section._sectPr
    pgNumType = OxmlElement('w:pgNumType'); pgNumType.set(qn('w:start'), str(start))
    sectPr.insert_element_before(pgNumType, 'w:cols', 'w:docGrid')


def enable_update_fields(doc):
    settings = doc.settings.element
    el = OxmlElement('w:updateFields'); el.set(qn('w:val'), 'true')
    settings.append(el)


def set_first_line_indent(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    ind = pPr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind'); pPr.append(ind)
    ind.set(qn('w:firstLineChars'), '200')


def add_body_paragraph(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.4
    set_first_line_indent(p)
    r = p.add_run(text)
    force_font(r, SONG, 12)


def add_heading1(doc, text):
    p = doc.add_paragraph(style='Heading 1')
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.4
    r = p.add_run(text)
    force_font(r, HEI, 15, bold=True)
    return p


def parse_md(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    title = None
    subtitle_parts = []
    headings = []
    cur_head = None
    cur_body = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith('# ') and title is None:
            title = s[2:].strip()
            continue
        if s.startswith('>'):
            subtitle_parts.append(s.lstrip('> ').strip())
            continue
        if s.startswith('## '):
            if cur_head is not None:
                headings.append((cur_head, cur_body))
            cur_head = s[3:].strip()
            cur_body = []
            continue
        if s.startswith('#'):
            continue
        if cur_head is not None:
            cur_body.append(s)
    if cur_head is not None:
        headings.append((cur_head, cur_body))
    return title, subtitle_parts, headings


def build(md_path, docx_path):
    title, subtitle_parts, headings = parse_md(md_path)
    doc = Document()

    # 第 1 节：封面
    cover = doc.sections[0]
    setup_page(cover)
    clear_footer(cover)
    for _ in range(6):
        doc.add_paragraph()
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title); force_font(r, HEI, 22, bold=True)
    if subtitle_parts:
        p2 = doc.add_paragraph(); p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(' '.join(subtitle_parts)); force_font(r2, SONG, 12)
    for _ in range(8):
        doc.add_paragraph()
    p3 = doc.add_paragraph(); p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run('2026年10月'); force_font(r3, SONG, 12)

    # 第 2 节：目录
    toc_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    setup_page(toc_sec)
    clear_footer(toc_sec)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('目  录'); force_font(r, HEI, 16, bold=True)
    tp = doc.add_paragraph()
    add_field(tp, 'TOC \\o "1-1" \\h \\z \\u', placeholder='（在 Word 中右键 → 更新域）')
    force_font(tp.runs[0], SONG, 12)

    # 第 3 节：正文
    body_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    setup_page(body_sec)
    restart_page_numbering(body_sec, 1)
    body_sec.footer.is_linked_to_previous = False
    fp = body_sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run('— '); force_font(r, SONG, 10.5)
    fld = add_field(fp, 'PAGE', placeholder='1')
    force_font(fld, SONG, 10.5)
    r = fp.add_run(' —'); force_font(r, SONG, 10.5)

    for head_text, body in headings:
        add_heading1(doc, head_text)
        for para in body:
            add_body_paragraph(doc, para)

    enable_update_fields(doc)
    doc.save(docx_path)
    print('saved:', docx_path)


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
