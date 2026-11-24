# -*- coding: utf-8 -*-
"""md 文档 → 中文 PDF 通用模板（fpdf2 + 黑体）
支持解析：# 节标题（# 开头，分节自动换页）/ > 引用块 / --- 分隔 /
md 表格（| a | b |，含 |---|---| 分隔行）/ 普通段落（首行缩进两全角空格）
实测于：论述题答案+教师批改表合成 PDF（Windows 中文环境，fpdf2 2.8.x）
用法：改 SRC/OUT 后直接运行；表格列宽 col_w 按需调整（总和 = 内容宽）。
"""
import re
from fpdf import FPDF

SRC = r'E:\path\to\input.md'
OUT = r'E:\path\to\output.pdf'
FONT = r'C:\Windows\Fonts\simhei.ttf'

LM, RM, TM = 22, 22, 20
CW = 210 - LM - RM  # A4 内容宽 166mm（技能正文默认 186mm 是 12mm 边距版，此处 22mm 边距）

class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('SimHei', '', 9)
            self.set_text_color(150, 150, 150)
            self.cell(0, 8, '页眉标题', align='C')
            self.ln(10)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-16)
        self.set_font('SimHei', '', 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f'- {self.page_no()} -', align='C')

pdf = PDF(format='A4')
pdf.add_font('SimHei', '', FONT)
pdf.set_auto_page_break(True, margin=22)
pdf.set_margins(LM, TM, RM)

def mc(w, h, txt, align='L'):
    """关键：multi_cell 前显式 set_x(LM) —— 居中渲染后 x 不归位，
    下一个 multi_cell 会因可用宽度不足抛 Not enough horizontal space"""
    pdf.set_x(LM)
    pdf.multi_cell(w, h, txt, align=align)
    pdf.set_x(LM)

def draw_table(rows, col_w):
    """rows: 列表，首行为表头；col_w 总和必须 = 内容宽"""
    line_h = 5.5
    for i, row in enumerate(rows):
        heights = []
        for c, w in zip(row, col_w):
            n = pdf.multi_cell(w, line_h, c, border=0, dry_run=True, output='LINES')
            heights.append(len(n) * line_h + 2)
        h = max(heights)
        if pdf.get_y() + h > 272:          # 跨页
            pdf.add_page()
        y0 = pdf.get_y()
        for c, w in zip(row, col_w):
            pdf.set_xy(LM + sum(col_w[:col_w.index(w)]), y0)
            if i == 0:                     # 表头：暖橙
                pdf.set_fill_color(216, 168, 130)
                pdf.set_text_color(60, 30, 10)
            else:                          # 数据行：交替浅色
                pdf.set_fill_color(252, 247, 240) if i % 2 == 0 else pdf.set_fill_color(255, 255, 255)
                pdf.set_text_color(0, 0, 0)
            pdf.set_font('SimHei', '', 10)
            pdf.multi_cell(w, line_h, c, border=1, fill=True, align='L')
        pdf.set_xy(LM, y0 + h)
    pdf.ln(3)

text = open(SRC, encoding='utf-8').read()
sections = re.split(r'^# ', text, flags=re.M)[1:]   # 按 # 分节

for sec_idx, sec in enumerate(sections):
    lines = [l for l in sec.splitlines() if l.strip()]
    sec_title = lines[0].strip()
    rest = lines[1:]
    pdf.add_page()                          # 每一节都从新页开始
    pdf.set_font('SimHei', '', 15)
    mc(0, 9, sec_title, align='C')
    pdf.ln(3)

    i = 0
    while i < len(rest):
        line = rest[i].strip()
        if line == '---':
            i += 1
            continue
        if line.startswith('> '):           # 引用块：灰色小字
            pdf.set_font('SimHei', '', 10.5)
            pdf.set_text_color(90, 90, 90)
            mc(0, 6, line[2:].strip())
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
        elif line.startswith('|'):          # md 表格
            rows = []
            while i < len(rest) and rest[i].strip().startswith('|'):
                cells = [c.strip() for c in rest[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c or '--') for c in cells):
                    rows.append(cells)      # 跳过分隔行 |---|---|
                i += 1
            draw_table(rows, [45, 40, 81])  # 例：三列，按内容调
            continue
        else:                               # 正文段落
            pdf.set_font('SimHei', '', 11.5)
            mc(0, 7, '　　' + re.sub(r'\*\*', '', line))  # 去 md 粗体 + 首行缩进
            pdf.ln(1.5)
        i += 1

pdf.output(OUT)

# 验证：页数 + 字体嵌入（中文在 FlateDecode 压缩流里，搜中文字节 False 属正常）
data = open(OUT, 'rb').read()
print('pages:', len(re.findall(rb'/Type\s*/Page[^s]', data)))
print('SimHei embedded:', b'SimHei' in data)
# 可选：pymupdf 抽查文本（检查关键词用纯文本，别带 md 的 | 符号）
# import pymupdf; d = pymupdf.open(OUT); print('kw:', '关键词' in ''.join(p.get_text() for p in d))
