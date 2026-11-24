# -*- coding: utf-8 -*-
"""fpdf2 中文表格 PDF 模板（Windows 实测通过）— 复制修改即可。
用法: pip install fpdf2 -q ; python 本文件.py
关键: 列宽总和 = 内容宽 (A4: 210 - 12*2 = 186mm)；正文避免 emoji（黑体缺字形）。
"""
import os
import re
from fpdf import FPDF

FONT = r"C:\Windows\Fonts\simhei.ttf"   # 黑体单TTF，fpdf2最稳（不要用 .ttc 集合）
OUT = r"~\output.pdf"     # 用户数据目录（不装C盘）

C_HEAD = (196, 43, 28)     # 表头深红
C_ALT = (255, 245, 238)    # 交替行浅橙
C_TEXT = (60, 45, 40)      # 正文深棕
C_SUB = (120, 90, 70)      # 副标题


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("SimHei", "", 9)
        self.set_text_color(*C_SUB)
        self.cell(0, 8, "标题", align="L")
        self.cell(0, 8, f"第 {self.page_no()} 页", align="R")
        self.ln(4)

    def footer(self):
        self.set_y(-16)
        self.set_font("SimHei", "", 8)
        self.set_text_color(*C_SUB)
        self.cell(0, 8, "页脚标语", align="C")

    def table(self, headers, rows, widths, aligns=None):
        """widths 总和必须 == 186 (A4)。用 dry_run 算行高避免文字溢出。"""
        assert abs(sum(widths) - 186) < 2, f"列宽总和 {sum(widths)} != 186"
        aligns = aligns or ["C"] * len(headers)
        self.set_font("SimHei", "", 10)
        self.set_fill_color(*C_HEAD)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(widths[i], 8, h, border=1, align="C", fill=True)
        self.ln()
        self.set_font("SimHei", "", 9)
        self.set_text_color(*C_TEXT)
        for r_idx, row in enumerate(rows):
            # 1) dry_run 算最大行高
            max_h = 0
            for i, val in enumerate(row):
                cell = self.multi_cell(widths[i], 5.5, str(val), border=0,
                                       dry_run=True, output="LINES")
                max_h = max(max_h, len(cell) * 5.5 + 2)
            if self.get_y() + max_h > 270:
                self.add_page()
            y0 = self.get_y()
            self.set_fill_color(*(C_ALT if r_idx % 2 else (255, 255, 255)))
            for i, val in enumerate(row):
                self.set_xy(self.l_margin + sum(widths[:i]), y0)
                self.multi_cell(widths[i], 5.5, str(val), border=1,
                                align=aligns[i], fill=True)
            self.set_xy(self.l_margin, y0 + max_h)
        self.ln(3)


if __name__ == "__main__":
    pdf = PDF(format="A4")
    pdf.set_margins(12, 12, 12)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("SimHei", "", FONT)
    pdf.add_page()
    pdf.table(["列1", "列2", "列3"], [["a", "b", "c"]], [60, 60, 66])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pdf.output(OUT)
    # 验证：页数 + 字体嵌入（中文正文在压缩流里，直接搜中文字节为 False 属正常）
    data = open(OUT, "rb").read()
    print("OK:", OUT, "| 页数:", len(re.findall(rb'/Type\s*/Page[^s]', data)),
          "| SimHei嵌入:", b'SimHei' in data)
