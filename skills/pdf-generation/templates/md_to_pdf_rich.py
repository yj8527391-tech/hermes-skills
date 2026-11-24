# -*- coding: utf-8 -*-
"""md → PDF 增强模板（fpdf2 + 黑体）：封面 + 目录 + 多级标题 + 列表 + 正文
适合无表格、靠 #/##/### 标题层级组织的中文长文档（背诵手册/讲义/要点清单）。
用法：改 SRC_LIST / TOC / 封面文案 / OUT 后直接运行。

⚠️ 实测教训（务必读）：
  1. 行内加粗别用 write()——write() 逐段渲染 `**` 在中文下会导致换行文字上下重叠（用户反馈
     "字都叠在一起"）。本模板改用 multi_cell + text.replace('**','') 去符号，行高给足。
  2. 黑体缺 ⑪-⑳ 带圈数字字形（只有 ①-⑩），源 md 里先把 ⑪⑫ 等替换成全角括号（11）（12）。
  3. 生成后必跑重叠校验（脚本末尾自带）：pymupdf get_text('blocks') 两两比对 y/x 区间，
     重叠数应为 0，别只信"生成成功"。
"""
import re
from fpdf import FPDF

FONT = r'C:\Windows\Fonts\simhei.ttf'
LM, RM, TM = 16, 16, 15
CW = 210 - LM - RM  # 178mm

# ===== 改这里：多个 md 源文件（按顺序拼成一个 PDF）=====
SRC_LIST = [
    r'E:\path\to\part1.md',
    r'E:\path\to\part2.md',
]
# ===== 改这里：目录条目（no=第几部分，name=标题，sub=副说明）=====
TOC = [
    ('第一部分', '标题一', '高频名词解释 · 简答论述要点 · 必背人物作品术语'),
    ('第二部分', '标题二', '高频名词解释 · 简答论述要点 · 必背人物作品术语'),
]
# ===== 改这里：封面文案 =====
DOC_TITLE_1 = '某某'            # 主标题第一行
DOC_TITLE_2 = '核心考点背诵手册'  # 主标题第二行
DOC_SUB = '2026 考研 · 全科核心考点'
DOC_META = '覆盖科目：……'
OUT = r'E:\path\to\output.pdf'

ACCENT = (176, 42, 42)   # 深红（标题）
GRAY = (130, 130, 130)
BODY = (25, 25, 25)
DARK = (60, 30, 10)


class PDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('SimHei', '', 8.5)
            self.set_text_color(*GRAY)
            self.cell(0, 7, DOC_TITLE_2, align='C')
            self.ln(9)
            self.set_text_color(*BODY)

    def footer(self):
        self.set_y(-15)
        self.set_font('SimHei', '', 9)
        self.set_text_color(*GRAY)
        self.cell(0, 7, f'- {self.page_no()} -', align='C')
        self.set_text_color(*BODY)


pdf = PDF(format='A4')
pdf.add_font('SimHei', '', FONT)
pdf.set_auto_page_break(True, margin=16)
pdf.set_margins(LM, TM, RM)


def plain(s):
    """去掉 md 加粗符号（放弃行内颜色区分，避免 write() 中文重叠）"""
    return s.replace('**', '').strip()


def body(text, size=10.5, line_h=5.6):
    """正文/列表项：整段 multi_cell，行高给足"""
    pdf.set_font('SimHei', '', size)
    pdf.set_text_color(*BODY)
    pdf.set_x(LM)
    pdf.multi_cell(CW, line_h, text)
    pdf.set_x(LM)
    pdf.ln(0.8)


def h1(text):
    pdf.set_font('SimHei', '', 19)
    pdf.set_text_color(*ACCENT)
    pdf.set_x(LM)
    pdf.multi_cell(CW, 11, text, align='C')
    pdf.set_x(LM)
    pdf.ln(2)
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(LM + 25, y, LM + CW - 25, y)
    pdf.ln(7)


def h2(text):
    pdf.set_font('SimHei', '', 14.5)
    pdf.set_text_color(*ACCENT)
    pdf.set_x(LM)
    pdf.multi_cell(CW, 9, text)
    pdf.set_x(LM)
    pdf.ln(2)


def h3(text):
    pdf.set_font('SimHei', '', 12)
    pdf.set_text_color(*DARK)
    pdf.set_x(LM)
    pdf.multi_cell(CW, 8, '■ ' + text)
    pdf.set_x(LM)
    pdf.ln(1.5)


def quote(text):
    pdf.set_font('SimHei', '', 9.5)
    pdf.set_text_color(*GRAY)
    pdf.set_x(LM)
    pdf.multi_cell(CW, 5.5, text)
    pdf.set_x(LM)
    pdf.ln(1.5)


def render_md(md_text, part_no):
    lines = md_text.splitlines()
    i = 0
    first_h1 = False
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s == '---':
            i += 1
            continue
        if s.startswith('# '):  # 部分标题（新页）
            pdf.add_page()
            title = s[2:].strip()
            if not first_h1:
                title = f'第{part_no}部分 · {title}'
                first_h1 = True
            h1(title)
        elif s.startswith('## '):
            h2(s[3:].strip())
        elif s.startswith('### '):
            h3(s[4:].strip())
        elif s.startswith('> '):
            quote(s[2:].strip())
        elif s.startswith('- ') or s.startswith('* '):
            body('· ' + plain(s[2:].strip()))
        else:
            body(plain(s))
        i += 1


# ===== 封面 =====
pdf.add_page()
pdf.ln(46)
pdf.set_font('SimHei', '', 28); pdf.set_text_color(*ACCENT)
pdf.set_x(LM); pdf.multi_cell(CW, 15, DOC_TITLE_1, align='C'); pdf.set_x(LM)
pdf.multi_cell(CW, 15, DOC_TITLE_2, align='C'); pdf.set_x(LM)
pdf.ln(10)
pdf.set_font('SimHei', '', 13); pdf.set_text_color(*GRAY)
pdf.set_x(LM); pdf.multi_cell(CW, 8, DOC_SUB, align='C'); pdf.set_x(LM)
pdf.ln(30)
pdf.set_font('SimHei', '', 11); pdf.set_text_color(70, 70, 70)
pdf.set_x(LM); pdf.multi_cell(CW, 8, DOC_META, align='C'); pdf.set_x(LM)
pdf.ln(4)
pdf.set_x(LM); pdf.multi_cell(CW, 8, '整理日期：YYYY-MM-DD', align='C'); pdf.set_x(LM)

# ===== 目录 =====
pdf.add_page()
pdf.set_font('SimHei', '', 18); pdf.set_text_color(*ACCENT)
pdf.set_x(LM); pdf.multi_cell(CW, 11, '目  录', align='C'); pdf.set_x(LM); pdf.ln(8)
for no, name, sub in TOC:
    pdf.set_font('SimHei', '', 13); pdf.set_text_color(*ACCENT)
    pdf.set_x(LM); pdf.cell(CW, 9, f'{no}  {name}'); pdf.ln(10)
    pdf.set_font('SimHei', '', 10); pdf.set_text_color(*GRAY)
    pdf.set_x(LM); pdf.cell(CW, 7, f'　　{sub}'); pdf.ln(14)

# ===== 正文 =====
for idx, src in enumerate(SRC_LIST, 1):
    render_md(open(src, encoding='utf-8').read(), idx)

# 输出（若目标被占用会 PermissionError，见 SKILL.md 的 tmp+os.replace 兜底）
pdf.output(OUT)

# ===== 验证 =====
data = open(OUT, 'rb').read()
print('pages:', len(re.findall(rb'/Type\s*/Page[^s]', data)))
print('SimHei embedded:', b'SimHei' in data)

import pymupdf
d = pymupdf.open(OUT)
txt = ''.join(p.get_text() for p in d)
for kw in ['关键词1', '关键词2']:   # 改成你的关键词
    print(f'  kw[{kw}]:', kw in txt)

# 重叠校验（应为 0，别只信"生成成功"）
overlap = 0
for pno in range(d.page_count):
    blocks = d[pno].get_text('blocks')
    for a in range(len(blocks)):
        for b in range(a + 1, len(blocks)):
            ya0, ya1 = blocks[a][1], blocks[a][3]
            yb0, yb1 = blocks[b][1], blocks[b][3]
            xa0, xa1 = blocks[a][0], blocks[a][2]
            xb0, xb1 = blocks[b][0], blocks[b][2]
            if ya0 < yb1 and yb0 < ya1 and xa0 < xb1 and xb0 < xa1:
                overlap += 1
print('重叠文本块数:', overlap, '（应为 0）')
