# -*- coding: utf-8 -*-
"""简易 md -> docx 转换:处理标题/粗体/列表/表格/引用块。专为知识库答案文件设计。
用法: python md2docx.py <输入.md> <输出.docx>
依赖: pip install python-docx
"""
import re
import sys
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_runs_with_bold(paragraph, text):
    """把 **bold** 和 `code` 转成带格式的 runs"""
    parts = re.split(r'(\*\*.+?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
        else:
            sub = re.split(r'(`[^`]+`)', part)
            for s in sub:
                if s.startswith('`') and s.endswith('`'):
                    r = paragraph.add_run(s[1:-1])
                    r.font.name = 'Consolas'
                else:
                    paragraph.add_run(s)

def md_to_docx(md_path, docx_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()

    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    try:
        style.element.rPr.rFonts.set(__import__('docx').oxml.ns.qn('w:eastAsia'), '宋体')
    except Exception:
        pass

    i = 0
    in_code = False
    in_table = False
    table_rows = []
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith('```'):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            p = doc.add_paragraph()
            r = p.add_run(line)
            r.font.name = 'Consolas'
            i += 1
            continue
        if line.startswith('|') and line.endswith('|'):
            cells = [c.strip() for c in line.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                i += 1
                continue
            table_rows.append(cells)
            i += 1
            continue
        elif table_rows:
            ncols = max(len(r) for r in table_rows)
            table = doc.add_table(rows=len(table_rows), cols=ncols)
            table.style = 'Table Grid'
            for ri, row in enumerate(table_rows):
                for ci in range(ncols):
                    cell = row[ci] if ci < len(row) else ''
                    cell = re.sub(r'\*\*(.+?)\*\*', r'\1', cell)
                    table.cell(ri, ci).text = cell
            for ci in range(ncols):
                for run in table.rows[0].cells[ci].paragraphs[0].runs:
                    run.bold = True
            table_rows = []
            i += 1
            continue

        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(2))
            p = doc.add_heading('', level=level)
            p.add_run(text)
            i += 1
            continue
        if line.startswith('>'):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            text = line.lstrip('> ').strip()
            add_runs_with_bold(p, text)
            for run in p.runs:
                run.font.color.rgb = RGBColor(0x59, 0x59, 0x59)
                run.italic = True
            i += 1
            continue
        m = re.match(r'^\s*[-*]\s+(.*)', line)
        if m:
            p = doc.add_paragraph(style='List Bullet')
            add_runs_with_bold(p, m.group(1))
            i += 1
            continue
        m = re.match(r'^\s*(\d+)\.\s+(.*)', line)
        if m:
            p = doc.add_paragraph(style='List Number')
            add_runs_with_bold(p, m.group(2))
            i += 1
            continue
        if re.match(r'^\s*(---|\*\*\*)\s*$', line):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run('─' * 20)
            r.font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        p = doc.add_paragraph()
        add_runs_with_bold(p, line)
        i += 1

    if table_rows:
        ncols = max(len(r) for r in table_rows)
        table = doc.add_table(rows=len(table_rows), cols=ncols)
        table.style = 'Table Grid'
        for ri, row in enumerate(table_rows):
            for ci in range(ncols):
                cell = row[ci] if ci < len(row) else ''
                cell = re.sub(r'\*\*(.+?)\*\*', r'\1', cell)
                table.cell(ri, ci).text = cell

    doc.save(docx_path)
    print('saved:', docx_path)

if __name__ == '__main__':
    md_to_docx(sys.argv[1], sys.argv[2])
