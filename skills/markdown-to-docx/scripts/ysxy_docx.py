#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
某院校《学术论文写作》课程作业 docx 生成器
版式复刻主人自己的课业稿（源：用户 文献综述-2.docx，2026-11 逐段扒参数）：
  页面 A4，四边全 2.0cm
  正文 宋体小四 12pt，两端对齐，首行缩进 24pt，固定行距 24pt
  一/二/三级标题 黑体小四 加粗，左对齐，段前段后 0，固定行距 24pt
  摘要/关键词 黑体五号 10.5pt，固定行距 16pt
  封面 校名 26pt 粗 / 学年学期与课程名 22pt / 题名行 12pt / 信息行加粗
  参考文献 悬挂缩进 left 24pt first -24pt
  2 节：封面+目录（无页码）/ 正文（页脚 PAGE 域，从 1 起）

用法：python ysxy_docx.py input.md output.docx

markdown 约定：
  :::cover ... :::     封面区，逐行输出
  # 题目               论文题目（22pt 粗居中）
  > 作者               作者行
  ABS:摘要：...        摘要段（黑体五号）
  KEY:关键词：...      关键词段
  ## 一、xxx           一级标题 Heading 1
  ### （一）xxx        二级标题 Heading 2
  #### 1.xxx           三级标题 Heading 3
  [1] xxx              参考文献条目（悬挂缩进）
  其他非空行            正文段落

注意：md 里的二级标题常是裸行（没写 ### 前缀），转档前先批量补前缀，
      否则会被当正文渲染成宋体非加粗。批量补法：
      len(s)<=30 and '。' not in s and '，' not in s 的独立行即候选标题，
      按 ^（[一二三四五六七八九十]+） 加 ### 、^[一二三四五六七八九十]+、 加 ## ，
      并跳过 :::cover 块内的封面行。

目录是 TOC 域，生成后必须用 Word COM 跑一次 Fields.Update() +
TablesOfContents(1).Update() 才有页码，否则只剩占位提示。
"""
import re
import sys

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

EN_FONT = 'Times New Roman'


def set_run_font(run, cn='宋体', en='宋体', size=None, bold=None):
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    run.font.name = en
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:ascii'), en)
    rFonts.set(qn('w:hAnsi'), en)
    rFonts.set(qn('w:eastAsia'), cn)


def setup_page(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(1.0)
    section.footer_distance = Cm(1.0)


def setup_styles(doc):
    normal = doc.styles['Normal']
    normal.font.name = EN_FONT
    normal.font.size = Pt(12)
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn('w:ascii'), EN_FONT)
    rFonts.set(qn('w:hAnsi'), EN_FONT)
    rFonts.set(qn('w:eastAsia'), '宋体')
    pf = normal.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.first_line_indent = Pt(24)
    pf.line_spacing = Pt(24)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)

    for nm in ('Heading 1', 'Heading 2', 'Heading 3'):
        st = doc.styles[nm]
        st.font.name = '宋体'
        st.font.size = Pt(12)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0, 0, 0)
        rPr = st.element.get_or_add_rPr()
        rFonts = rPr.get_or_add_rFonts()
        rFonts.set(qn('w:ascii'), '宋体')
        rFonts.set(qn('w:hAnsi'), '宋体')
        rFonts.set(qn('w:eastAsia'), '黑体')
        pf = st.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.left_indent = Pt(0)
        pf.first_line_indent = Pt(0)
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.line_spacing = Pt(24)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.keep_with_next = True


def cover_line(doc, text, size=12, bold=False, spacing_after=0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf.first_line_indent = Pt(0)
    pf.line_spacing = 1.5
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.space_after = Pt(spacing_after)
    if text:
        r = p.add_run(text)
        set_run_font(r, cn='宋体', en='宋体', size=size, bold=bold)
    return p


def body_para(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    set_run_font(r, cn='宋体', en='宋体')
    return p


def heading(doc, text, level):
    p = doc.add_paragraph(style='Heading %d' % level)
    r = p.add_run(text)
    set_run_font(r, cn='黑体', en='宋体', size=12, bold=True)
    return p


def small_black(doc, text):
    """摘要 / 关键词：黑体五号，固定行距 16pt"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.first_line_indent = Pt(24)
    pf.line_spacing = Pt(16)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    set_run_font(r, cn='黑体', en='黑体', size=10.5)
    return p


def ref_para(doc, text):
    """参考文献条目：悬挂缩进 24pt"""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Pt(24)
    pf.first_line_indent = Pt(-24)
    pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    set_run_font(r, cn='宋体', en='Times New Roman', size=10.5)
    return p


def add_toc(doc):
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Pt(0)
    run = p.add_run()
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'separate')
    t = OxmlElement('w:t')
    t.text = '（在 Word 中右键此处选择“更新域”生成目录）'
    fld3 = OxmlElement('w:fldChar')
    fld3.set(qn('w:fldCharType'), 'end')
    for el in (fld1, instr, fld2, t, fld3):
        run._r.append(el)
    set_run_font(run, cn='宋体', en='宋体', size=12)


def add_page_number_footer(section):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = 'PAGE'
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'end')
    for el in (fld1, instr, fld2):
        run._r.append(el)
    set_run_font(run, cn='宋体', en='Times New Roman', size=10.5)


def restart_numbering(section, start=1):
    sectPr = section._sectPr
    pgNumType = sectPr.find(qn('w:pgNumType'))
    if pgNumType is None:
        pgNumType = OxmlElement('w:pgNumType')
        sectPr.append(pgNumType)
    pgNumType.set(qn('w:start'), str(start))


def parse(md_text):
    lines = md_text.splitlines()
    out = {'cover': [], 'title': None, 'author': None,
           'abs': None, 'key': None, 'blocks': []}
    i, n = 0, len(lines)
    while i < n:
        s = lines[i].strip()
        if s == ':::cover':
            i += 1
            while i < n and lines[i].strip() != ':::':
                if lines[i].strip():
                    out['cover'].append(lines[i].strip())
                i += 1
            i += 1
            continue
        if not s:
            i += 1
            continue
        if s.startswith('# '):
            out['title'] = s[2:].strip()
        elif s.startswith('> '):
            out['author'] = s[2:].strip()
        elif s.startswith('ABS:'):
            out['abs'] = s[4:].strip()
        elif s.startswith('KEY:'):
            out['key'] = s[4:].strip()
        elif s.startswith('#### '):
            out['blocks'].append(('h3', s[5:].strip()))
        elif s.startswith('### '):
            out['blocks'].append(('h2', s[4:].strip()))
        elif s.startswith('## '):
            out['blocks'].append(('h1', s[3:].strip()))
        elif re.match(r'^\[\d+\]', s):
            out['blocks'].append(('ref', s))
        else:
            out['blocks'].append(('p', s))
        i += 1
    return out


def build(md_path, out_path):
    data = parse(open(md_path, encoding='utf-8').read())
    doc = Document()
    setup_styles(doc)
    sec1 = doc.sections[0]
    setup_page(sec1)

    # ---- 封面 ----
    cover = data['cover']
    for _ in range(6):
        cover_line(doc, '', size=12)
    for line in cover:
        if line == '某院校':
            cover_line(doc, line, size=26, bold=True, spacing_after=8)
        elif '学年第' in line or line.startswith('《'):
            cover_line(doc, line, size=22, bold=False, spacing_after=6)
        elif line.startswith('（题名）') or line.startswith('(题名)'):
            cover_line(doc, line, size=12, bold=False, spacing_after=36)
        elif line.startswith('评阅意见'):
            cover_line(doc, line, size=12, bold=True, spacing_after=0)
            for _ in range(3):
                cover_line(doc, '', size=12)
        elif line.startswith('评阅时间'):
            cover_line(doc, line, size=12, bold=True)
        else:
            cover_line(doc, line, size=12, bold=True, spacing_after=8)

    doc.add_page_break()

    # ---- 题目 / 作者 / 摘要 / 关键词 ----
    if data['title']:
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(data['title'])
        set_run_font(r, cn='黑体', en='宋体', size=22, bold=True)

    if data['author']:
        p = doc.add_paragraph()
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        p.paragraph_format.space_after = Pt(10)
        r = p.add_run(data['author'])
        set_run_font(r, cn='宋体', en='宋体', size=12)

    if data['abs']:
        small_black(doc, data['abs'])
        sp = doc.add_paragraph()
        sp.paragraph_format.line_spacing = Pt(6)
    if data['key']:
        small_black(doc, data['key'])

    # ---- 目录 ----
    doc.add_page_break()
    p = doc.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    p.paragraph_format.space_after = Pt(12)
    r = p.add_run('目录')          # 别用 '目　录'，全角空格在 Word 2010 会折成两行
    set_run_font(r, cn='黑体', en='宋体', size=15, bold=True)
    add_toc(doc)

    # ---- 正文新节 ----
    sec2 = doc.add_section(WD_SECTION.NEW_PAGE)
    setup_page(sec2)
    add_page_number_footer(sec2)
    restart_numbering(sec2, 1)
    sec1.footer.is_linked_to_previous = False

    for kind, text in data['blocks']:
        if kind == 'h1':
            heading(doc, text, 1)
        elif kind == 'h2':
            heading(doc, text, 2)
        elif kind == 'h3':
            heading(doc, text, 3)
        elif kind == 'ref':
            ref_para(doc, text)
        else:
            body_para(doc, text)

    # 打开时自动更新域（目录页码）
    settings = doc.settings.element
    uf = OxmlElement('w:updateFields')
    uf.set(qn('w:val'), 'true')
    settings.append(uf)

    doc.save(out_path)
    return out_path


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
    print('saved:', sys.argv[2])
