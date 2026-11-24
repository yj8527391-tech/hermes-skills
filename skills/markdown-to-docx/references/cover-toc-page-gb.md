# 生成带封面/目录/页码/国标格式的 docx（python-docx + lxml 域 + Word COM 缓存目录）

场景：用户要「封面目录页码做好，格式符合国标」的正式 Word 交付（策划案/报告/申报书）。不是 md→docx 转换，而是用 python-docx 从零拼一份结构完整的 docx。2026-10 实测跑通（借 codex 写出骨架 + 本人复核）。

## 三节结构（封面/目录/正文）

```python
from docx.enum.section import WD_SECTION
# 第 1 节：封面（无页脚无页码）
cover = doc.sections[0]; setup_page(cover); clear_footer(cover)
# 第 2 节：目录（无页码，TOC 域）
toc_sec = doc.add_section(WD_SECTION.NEW_PAGE); setup_page(toc_sec); clear_footer(toc_sec)
# 第 3 节：正文（页脚页码，从 1 重排）
body_sec = doc.add_section(WD_SECTION.NEW_PAGE); setup_page(body_sec); restart_page_numbering(body_sec, 1); clear_footer(body_sec)
```

## 关键 lxml 域（python-docx 没内置，要拼 XML）

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_field(paragraph, instr_text, placeholder="", font=SONG, size=10.5):
    run = styled_run(paragraph.add_run(), font, size)
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText"); instr.set(qn("xml:space"), "preserve"); instr.text = instr_text
    sep = OxmlElement("w:fldChar"); sep.set(qn("w:fldCharType"), "separate")
    res = OxmlElement("w:t"); res.text = placeholder
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    for el in (begin, instr, sep, res, end): run._element.append(el)
```

- **目录域**：`add_field(p, 'TOC \o "1-1" \h \z \u', placeholder="（在 Word 中右键→更新域）")` —— `\o "1-1"` 只收一级标题
- **页码域**（页脚）：`add_field(footer_p, 'PAGE', placeholder='1')`，前后拼 `— ` 和 ` —` 即国标式「— 1 —」

## 页码重排 + 自动刷新域

```python
def restart_page_numbering(section, start=1):
    sectPr = section._sectPr
    pgNumType = OxmlElement("w:pgNumType"); pgNumType.set(qn("w:start"), str(start))
    sectPr.insert_element_before(pgNumType, "w:cols", "w:docGrid")  # ⚠ 必须插到 cols/docGrid 前，否则 Word 报文档损坏

def enable_update_fields(doc):
    settings = doc.settings.element
    el = OxmlElement("w:updateFields"); el.set(qn("w:val"), "true")
    settings.insert_element_before(el, "w:hdrShapeDefaults", "w:footnotePr", ...)  # 打开文档自动刷新目录页码
```

## 国标版式

- A4，页边距 上 2.5 / 下 2.5 / 左 3 / 右 3 cm（`setup_page`）
- 标题黑体加粗（H1 15pt / H2 13pt），正文宋体小四 12pt，1.4 倍行距
- 首行缩进 2 字符：`w:firstLineChars="200"`（比 `w:firstLine` 绝对磅值更准，Word 中文排版）
- **无斜体、无灰字**（用户偏好）：每个 run 强制 `italic=False` + `color.rgb=RGBColor(0,0,0)`

## 中文字体必须写死 + 清主题属性（否则 Word 渲染成蓝色等线体）

```python
THEME_ATTRS = ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme")
def force_font(rPr_owner, font):
    rPr = rPr_owner.get_or_add_rPr(); rFonts = rPr.get_or_add_rFonts()
    for a in THEME_ATTRS:
        if rFonts.get(qn("w:" + a)) is not None: del rFonts.attrib[qn("w:" + a)]
    for a in ("ascii", "hAnsi", "eastAsia", "cs"): rFonts.set(qn("w:" + a), font)
```

主题属性优先级 > w:val，不删掉的话黑体/宋体写死了也白写。

## Word COM 缓存目录（让 TOC 在任何阅读器直接显示真实页码）

TOC 域刚生成时是空的（显示占位文字），WPS 预览/macOS 快速查看不显示真实条目。用 Word COM 刷新并另存即可把结果缓存进文件。⚠️ 装了 WPS 的机器上 `EnsureDispatch('Word.Application')` 会启动 WPS 而失败——改用 SKILL.md「docx → PDF」的「直接启动 WINWORD.EXE + GetActiveObject(CLSID) + 英文临时路径」绕过法（同一个 Word COM，同样要清 WPS 残留、中文路径复制到英文临时路径）。

```python
import win32com.client
word = win32com.client.gencache.EnsureDispatch('Word.Application')
word.Visible = False; word.DisplayAlerts = 0
doc = word.Documents.Open(os.path.abspath('x.docx'))
for toc in doc.TablesOfContents: toc.Update()   # 刷新目录
doc.Fields.Update()                              # 刷新页码等
word.Visible = False
# 用 Word COM 另存（不 SaveAs 同路径可能不写回）；实测 doc.Save() 即可
... doc.Save(); doc.Close(False); word.Quit()
```

## 验证坑

- **PAGE 域不在 document.xml 里，在页脚里**：`doc.element.xml.count('PAGE')` 恒为 0。要 `zipfile` 打开 docx 查 `word/footer*.xml` 里的 `PAGE`，或直接看各 section 的 footer。封面/目录的 footer 应该无 PAGE，正文 footer 有 1 个。
- 检查域/节：`doc.element.xml.count('TOC')`（目录域，正文里 1 个）、`len(doc.sections)`（=3）、`settings.xml` 里 `updateFields`、`word/media/` 里的图片数。
- Word 里若有残留 WINWORD.EXE 锁文件，`taskkill //F //IM WINWORD.EXE` 再跑。

## 借 codex 写这套脚本

用户说「相应的程序可以用 codex 或 harness 完成」时，把 docx 生成脚本交给 codex：
- codex 需要 git 仓库（`git init` 目标目录）+ `DEEPSEEK_API_KEY` env 注入（从 Hermes `.env` 读）
- 命令行要 `E:\npm-global\codex.cmd` 全路径（裸 `codex` 在 subprocess 里 WinError 2 找不到）
- 任务写进 .txt 文件，Python subprocess 列表传参（绕开 shell 转义），`--sandbox danger-full-access`
- codex 自报结果必须复核：读回 docx 文字 + 查 footer/TOC/域，别信「成功」字样
