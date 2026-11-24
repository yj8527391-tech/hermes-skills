# -*- coding: utf-8 -*-
"""批量企业背调全量表生成器（复制后改三个路径即可）

输入：
  r1_all.csv  表头 id,name,est_year,reg_capital,status,business,fit_post,
              fit_level,risk_score,verdict,reason,evidence
  tiers.tsv   两列：id<TAB>梯队（如 "A007\tA档·必去"），可缺省
输出：
  背调总表.xlsx  —— Sheet1 全量筛选表，Sheet2 统计
"""
import csv
import os
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.join(BASE, "r1_all.csv")
TIERS = os.path.join(BASE, "tiers.tsv")
OUT = os.path.join(BASE, "背调总表.xlsx")

HEAD = ["编号", "公司名称", "成立年份", "注册资本", "经营状态", "业务实质",
        "对口岗位方向", "对口度", "风险分(0-10)", "第一轮结论", "梯队",
        "判定依据", "证据来源"]
COLOR = {"淘汰": "FCE4E4", "观察": "FFF6DC", "通过": "E4F3E6"}
WIDTH = [8, 34, 9, 14, 8, 30, 24, 7, 9, 9, 12, 46, 34]

rows = list(csv.DictReader(open(R1, encoding="utf-8-sig")))
tiers = {}
if os.path.exists(TIERS):
    for line in open(TIERS, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 2 and p[1]:
            tiers[p[0]] = p[1]

wb = Workbook()
ws = wb.active
ws.title = "全量筛查"
ws.append(HEAD)

thin = Side(style="thin", color="D9D9D9")
for c in ws[1]:
    c.fill = PatternFill("solid", fgColor="1F3B57")
    c.font = Font(color="FFFFFF", bold=True, size=10)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

for r in rows:
    ws.append([
        r["id"], r["name"], r.get("est_year", ""), r.get("reg_capital", ""),
        r.get("status", ""), r.get("business", ""), r.get("fit_post", ""),
        r.get("fit_level", ""), int(r.get("risk_score") or 0),
        r.get("verdict", ""), tiers.get(r["id"], ""),
        r.get("reason", ""), (r.get("evidence", "") or "")[:120],
    ])
    fill = PatternFill("solid", fgColor=COLOR.get(r.get("verdict"), "FFFFFF"))
    for c in ws[ws.max_row]:
        c.fill = fill
        c.font = Font(size=9)
        c.alignment = Alignment(vertical="center", wrap_text=True)
        c.border = Border(left=thin, right=thin, top=thin, bottom=thin)

for i, w in enumerate(WIDTH, 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "C2"
ws.auto_filter.ref = f"A1:M{ws.max_row}"

ws2 = wb.create_sheet("统计")
ws2.append(["第一轮结论", "家数"])
for k, v in Counter(r.get("verdict", "") for r in rows).most_common():
    ws2.append([k, v])
ws2.append([])
ws2.append(["梯队", "家数"])
for k, v in Counter(tiers.get(r["id"], "未分级") for r in rows).most_common():
    ws2.append([k, v])
ws2.append([])
ws2.append(["说明", "风险分≥6淘汰；4-5观察；≤3通过。数据来自公开网络检索，仅供参考"])

wb.save(OUT)
print("saved", OUT, "rows", len(rows))
