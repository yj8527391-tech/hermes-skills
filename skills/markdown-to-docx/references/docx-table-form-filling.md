# 填写别人给的下发 docx 表格模板

场景：学校/单位下发一份固定格式的表格模板（开题报告书、审批表、申请书、登记表），要求在表格单元格里填内容。这与从零拼 docx 完全不同，坑全在表格结构上。2026-11 填某院校开题报告书实测。

## 第一步：先勘察结构，别动手写

```python
from docx import Document
d = Document(tpl)
s = d.sections[0]
print("页面 %.1f x %.1f 边距 L%.1f R%.1f T%.1f B%.1f" % (
    s.page_width.cm, s.page_height.cm,
    s.left_margin.cm, s.right_margin.cm, s.top_margin.cm, s.bottom_margin.cm))

for ti, tb in enumerate(d.tables):
    print(f"===== 表{ti} rows={len(tb.rows)} cols={len(tb.columns)}")
    for ri, row in enumerate(tb.rows):
        for ci, c in enumerate(row.cells):
            print(f"[{ri},{ci}] {c.text[:200]!r} width={c.width.cm if c.width else None}")
    print("列宽:", [col.width.cm if col.width else None for col in tb.columns])
```

要看三样：哪一格是标签、哪一格是值、每列多宽。合并单元格的表格里同一个 `_tc` 会被 `row.cells` 重复返回，打印时多个下标指向同一段文本，属正常。

## 坑一：清空错格子会毁掉栏目名

两列表格里 `cells[0]` 是栏目名（“选题来源”“研究方向”），`cells[1]` 才是填值处。

**实测事故**：`fill(tb.rows[0].cells[0], [("学生自拟","p")])` 先清空再写入，结果栏目名“选题来源”被抹掉，值落到 2.36cm 窄列里被拆成“与演出市 / 场、观众研 / 究”。转 PDF 目检才发现。

口径：

- 标签加值型的两列行 → 只填 `cells[1]`，`cells[0]` 一个字节都别动。
- 整栏合并成一格的长文本栏（“一、选题依据”那类）→ 用 `cells[0]`，此时它同时是 `cells[1]`。
- 判定看列宽：窄列 2—4cm 是标签列，宽列 12cm 以上是值列。

## 坑二：单元格内的分页控制只认 cantSplit

想让某栏从新页开始时，三种常规做法全部失效：

| 做法 | 结果 |
|---|---|
| 段落 `page_break_before = True` | Word 在表格单元格内直接忽略 |
| 段落 `keep_together = True`（w:keepLines） | 单元格内不生效，段落照样拆 |
| `add_page_break()` | 插出多余空行，破坏表格 |
| **`w:trPr/w:cantSplit`** | **有效**，整行被推到下一页 |

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def forbid_split(cell):
    tr = cell._tc.getparent()
    trPr = tr.find(qn("w:trPr"))
    if trPr is None:
        trPr = OxmlElement("w:trPr"); tr.insert(0, trPr)
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))

def allow_split(cell):
    tr = cell._tc.getparent()
    trPr = tr.find(qn("w:trPr"))
    if trPr is not None:
        el = trPr.find(qn("w:cantSplit"))
        if el is not None:
            trPr.remove(el)
```

**只给短行加。** 长内容行（参考文献十几条、正文两三页）一旦禁止拆行，整行会被挤到下一页甚至超出页高丢内容。下发模板常默认给所有行加了 `cantSplit`，填长栏前必须先 `allow_split`。

实践口径：正文长栏全部 `allow_split`，短栏（进度安排七八行、签名栏）`forbid_split`。

## 坑三：孤字跨页

允许拆行后会出现一句话最后一个字被挤到下一页开头（“撰写并提交开题报 / 告。”）。处理优先级：给那一短栏 `forbid_split` 让整栏换页。**别为一个字去调行距或字号**，调完全局排版跟着变，可能引发新的溢出。

## 填内容骨架

```python
def fill(cell, blocks, indent=True, line=22):
    """blocks: [(文本, 类型)]，类型 h=栏目标题 bold=子标签 p=正文 sched=短行不拆页"""
    for p in list(cell.paragraphs):
        p._element.getparent().remove(p._element)
    allow_split(cell)
    for i, (text, kind) in enumerate(blocks):
        p = cell.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0); pf.space_after = Pt(0)
        pf.line_spacing = Pt(line)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        r.font.name = "宋体"; r.font.size = Pt(12)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        if kind == "h":
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r.font.name = "黑体"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
            r.bold = True; pf.space_before = Pt(4)
        elif kind == "bold":
            r.bold = True; pf.first_line_indent = Pt(0)
        else:
            if indent: pf.first_line_indent = Pt(24)   # 2 字符
```

中文字体必须同时设 `r.font.name` 和 `w:eastAsia`，只设前者 Word 里不生效。

## 交付前必做

1. 转 PDF（Word COM，见 SKILL.md 的转换段）。
2. 用文本层扫每页首行，比看图像更快抓跨页问题：

```python
import pymupdf
d = pymupdf.open("_out.pdf")
for i in range(d.page_count):
    print("p%d:" % (i+1), d[i].get_text()[:36].replace("\n", "|"))
```

首行只有一两个字 = 孤字跨页。

3. 渲染 PNG 目检三件事：栏目名还在不在、有无拆字、签字栏是否留空。
4. 页数与内容量对得上（开题报告七栏填满通常 5—7 页）。

## 已合成的成品案例

| 模板 | 结构 | 产出 |
|---|---|---|
| 某院校本科学生毕业论文开题报告书 | 封面七项（题目/院系/专业/姓名/学号/指导教师/填写时间）+ 正文七栏（选题来源、研究方向、一、选题依据、二、主要内容重点难点、三、研究方法、四、进度安排、五、参考文献，六、七留给老师签字） | `E:\hermes_memes\thesis27\tools\gen_kaiti.py` + `kaiti.docx`，6 页 3709 字 |

生成脚本的写法：把各栏内容写成 Python 常量列表（元素带类型标记），封面和正文分开填，便于反复修改重跑。内容改一句就重跑一次，别手改 docx，否则下次重跑会覆盖。
