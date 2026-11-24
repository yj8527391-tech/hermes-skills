---
name: docx-template-filling
description: Use when 往院系或机构的 docx 模板填内容。原位填写加 PDF 目检。
---

# 往既有 docx 模板里填内容

院系、教务处、单位常直接发一个 .docx 模板（开题报告书、任务书、中期检查表、答辩申请表、评优推荐表），要求填进去交。**不要自建文档替代**：模板里的表格结构、栏目名称、签字栁、字号都是审查项，换了就不认。

## 工作流

1. 摸清结构。读段落与每一张表，记录行列数、每个单元格文本与列宽，合并单元格用 `id(cell._tc)` 去重。
2. 定位写入点。分清“标签单元格”与“内容单元格”。
3. 原位写入，保留标签，只清空内容单元格里的段落。
4. 转 PDF 渲染成图，逐页看。
5. 单独列出留空项交用户确认（姓名、日期、签字栁）。

## 必踩的坑

### 1 标签列和值列

两列表格常是左标签右值。往 `rows[i].cells[0]` 写值并清空段落，等于把“选题来源”这个标签干掉，值被挤进 2cm 的窄列里逐字换行（实测出现过“与演出市/场、观众研/究”这种拆词）。**值必须写 `cells[1]`。**

### 2 表格里的分页控制

`paragraph_format.page_break_before` 和 `keep_together`（w:keepLines）在表格单元格内 Word 不认，设了等于没设。唯一有效的是行属性：

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def forbid_split(cell):
    """整行不跨页，只给短行用"""
    tr = cell._tc.getparent()
    trPr = tr.find(qn("w:trPr"))
    if trPr is None:
        trPr = OxmlElement("w:trPr")
        tr.insert(0, trPr)
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))

def allow_split(cell):
    """允许整行跨页，长内容行必须允许"""
    tr = cell._tc.getparent()
    trPr = tr.find(qn("w:trPr"))
    if trPr is not None:
        el = trPr.find(qn("w:cantSplit"))
        if el is not None:
            trPr.remove(el)
```

**cantSplit 只给短行用。**一整栏内容超过一页时（如参考文献十几条），设了 cantSplit 会让整行挤到下一页且内容被裁切丢失。长行必须先 allow_split。

### 3 中文字体

每个 run 都要设 eastAsia，否则中文回落到默认字体，跟模板其他地方不一致：

```python
r = p.add_run(text)
r.font.name = "宋体"
r._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
```

### 4 最后一页凭空多出空白页

表格是 body 的最后一个块级元素时（后面直接跟 `w:sectPr`），Word 会在表格后自补一个整行高的空段落占位。当页面只剩 1—2 cm 余量时，这个隐藏段落被顶到下一页，生成一张彻底空白的页——`get_text()` 返回 0 字符、`get_drawings()` 返回 0 个对象，看着像 Word 抽风，其实上一页内容是完整收口的。

**压行高救不了。** 实测把末尾两行的 `trHeight` 从 3.7 cm / 3.9 cm 压到 2.6 cm，仍然是 8 页。正确做法是在 `sectPr` 前显式插一个 1 磅、零段前段后、固定行距 1 磅的极小段落，让那个占位只占 0.05 cm，挤得进剩余空间：

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

body = d.element.body
tiny = OxmlElement('w:p')
pPr = OxmlElement('w:pPr')
sp = OxmlElement('w:spacing')
sp.set(qn('w:before'), '0'); sp.set(qn('w:after'), '0')
sp.set(qn('w:line'), '20'); sp.set(qn('w:lineRule'), 'exact')
pPr.append(sp)
rPr = OxmlElement('w:rPr')
for tag in ('w:sz', 'w:szCs'):
    e = OxmlElement(tag); e.set(qn('w:val'), '2'); rPr.append(e)
pPr.append(rPr)
tiny.append(pPr)
sectPr = body.find(qn('w:sectPr'))
if sectPr is not None:
    sectPr.addprevious(tiny)
```

顺带一个认知误区：`d.paragraphs` 只返回 body 的**直接子段落**，表格内的段落不在其中。表格后面直接是 sectPr 时，指望「删掉末尾空段落」那招会找不到任何东西可删，然后对着 8 页发呆。

### 5 Word COM 稳定性与文件占用

`DispatchEx('Word.Application')` 起来后循环 `word.Documents.Open(p)`，第一个处理完再开第二个，会报 `AttributeError: <unknown>.Open`，`word.Documents` 整个失效。这不是环境坏了，是同一次 COM 会话重复 Open 的实例状态问题。

稳的做法：**一个文件一个独立 python 进程**。每次开头先 `taskkill //F //IM WINWORD.EXE` 清残留，用 `win32.Dispatch`（不是 DispatchEx），处理完 `Close(0)` 直接退出。多个文件就写 shell 循环 `for f in a.docx b.docx; do python one.py "$f"; done`，别在一个进程里 for 循环。

另外 `w.Quit()` 偶发抛 COM 异常——此时 `Save()` / `SaveAs2()` 已经执行完了。别看到 traceback 就以为没存上，去看 PDF 的时间戳和页数确认。

**报 `PermissionError: [Errno 13]` 时先认清是谁锁着文件。** 本机文档默认关联 WPS，`taskkill //F //IM WINWORD.EXE` 杀多少遍都没用——占用者根本没有 WINWORD 进程。先查：

```bash
tasklist 2>/dev/null | grep -iE "winword|wps" || echo "无 Office/金山进程"
```

看到 `wps.exe` 就别杀（用户可能正开着文档看，杀掉丢编辑）。**换个文件名生成，先把能用的文件交出去**：

```bash
python build_kaiti.py 模板.docx "E:/桌面/xxx_v2.docx"
```

然后在回复里说清楚「原件被 WPS 锁住，先存成 v2，你关掉后我再换回原名」。别死磕覆盖，也别只回一句「保存失败」——把文件先落地，用户当天就要交，卡在这一步最亏。

### 6 源文件里混进别的章节

生成脚本读的是中间稿（.md / .txt），中间稿可能被上一次会话的编辑污染——实测综述 md 末尾躺着整段开题报告的「研究意义 / 创新点 / 与专业联系」。生成脚本老实照抄，docx 变成两份文档拼接，只多两页，**单看页数完全正常**。

所以对页数不够，必须抽末页文本核对：

```python
import pymupdf
d = pymupdf.open(pdf)
for i in range(d.page_count - 3, d.page_count):
    print(i + 1, d[i].get_text().strip()[:200])
```

正文该收在哪里（参考文献最后一条、致谢、签字栏）心里要有数，末页冒出认不出的章节标题就是污染。回源 md 里按标题切掉，被切的内容另存一份备查，再重新生成。

## 换选题：整栏重建，不要逐段手写格式

模板里躺着上一版选题的完整内容，这次要整篇换掉（旧题开题报告 → 新题开题报告）。别用 `add_paragraph` 加 `Pt(12)`、加粗、缩进这些参数手工复刻——十几个段落写下来必错一处。**从原单元格里抽三类模板段落，`deepcopy` 后只换文字，格式必然与模板一致。**

```python
from copy import deepcopy
from docx.oxml.ns import qn

def retitle(tpl_p, text):
    """复制模板段落，只换文字，保住 pPr 与第一个 run 的 rPr"""
    p = deepcopy(tpl_p)
    runs = p.findall(qn('w:r'))
    if not runs:
        return p
    first = runs[0]
    for r in runs[1:]:
        p.remove(r)
    ts = first.findall(qn('w:t'))
    for t in ts[1:]:
        first.remove(t)
    if ts:
        ts[0].text = text
        ts[0].set(qn('xml:space'), 'preserve')
    return p

def clear_cell(cell):
    for p in cell._tc.findall(qn('w:p')):
        cell._tc.remove(p)

def fill_cell(cell, blocks, tpl):        # blocks: [(kind, text), ...]
    clear_cell(cell)
    for kind, text in blocks:
        cell._tc.append(retitle(tpl[kind], text))
    if cell._tc.find(qn('w:p')) is None:   # Word 要求单元格至少一个段落
        cell._tc.append(deepcopy(tpl['b']))
```

模板段落按文本特征自动分三类，不用手工指定：`以「一、」开头` → 栏目标题（黑体加粗）、`以「：」结尾且长度 ≤8` → 加粗子标签（「选题目的：」）、其余非空段 → 正文。抽完 `assert` 三类都拿到，缺哪一类就说明模板结构跟预想不同，回去重新摸。

封面上的长题目另说：**超出行宽它会按字断，「黑神话悟空」被拆成「黑神话悟」+「空」**，视觉模型会一眼指出来。手动在语义完整处断行，`run.text` 里写 `chr(10)`，python-docx 自动转成 `<w:br/>`：

```python
TITLE_COVER = '从玩家到观众：' + chr(10) + '游戏IP音乐会受众拓展——以黑神话悟空巡演为例'
```

断点选冒号后最稳——破折号不能落在行首，专有名词不能拆开。

## 目检闭环（不可省）

docx → Word COM 转 PDF → pymupdf 渲 PNG（dpi≈100）→ 看图。

以下几类问题机器查不出来，只有看图才露：

- 中文引号被写成 ASCII 双引号。编辑器里几乎看不出区别，渲染出来一眼能认出
- 孤字行。一个字的 widow 出现在次页开头（“……开题报” / “告。”），用 cantSplit 修
- 断字拆词。窄列强制换行把“市场”拆成“市/场”
- 内容被裁切。cantSplit 误用在长行上的后果
- 下划线合并成一条长线、页码错乱、签字栁位置漂移

看图时视觉模型会提一堆与本国公文无关的建议（比如让表格“取消跨页断行”），**要自己判断**：单栏长表格必须允许跨页，否则丢内容。

## 交付前清单

- [ ] 每一栏都有字，没有空栏（签字栁除外）
- [ ] 签字栁、指导教师、日期等留空项单独列给用户
- [ ] 引号是中文“”不是 ASCII
- [ ] 页码连续，无空白页（空白页的成因与修法见坑 4）
- [ ] 抽过末页文本，没有串入别的章节（见坑 6）
- [ ] PDF 页数符合预期（开题报告一般 5—6 页，正文 3000 字以上）
- [ ] 文件同时放工作目录与桌面，用 MEDIA: 发给用户

