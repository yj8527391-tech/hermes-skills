# 交叉引用域的实现细节

配套 SKILL.md 第六节。这里放完整 XML、python-docx 代码和验证步骤。

## 一、判定一份 docx 用没用交叉引用

解包看 `word/document.xml`，搜 `w:instrText` 里有没有 `REF`：

```python
import re, zipfile
x = zipfile.ZipFile(path).read('word/document.xml').decode('utf-8')
instr = re.findall(r'<w:instrText[^>]*>([^<]*)</w:instrText>', x)
for s in instr:
    if s.strip().startswith('REF'):
        print(repr(s))
```

典型的输出是 `' REF _Ref21842 \r \h '`。同时应该能在 `document.xml` 里找到同名的 `bookmarkStart`，并在 `numbering.xml` 里找到 `lvlText="[%1]"`。三样齐了才是真正的交叉引用，只有 `REF` 没书签的是断链接。

## 二、自动编号的定义

参考文献段落的 `pPr` 里 `numPr` 指向 `numId`，`numId` 指向 `abstractNumId`，`abstractNum` 里才有格式：

```xml
<w:abstractNum w:abstractNumId="900">
  <w:multiLevelType w:val="singleLevel"/>
  <w:lvl w:ilvl="0">
    <w:start w:val="1"/>
    <w:numFmt w:val="decimal"/>
    <w:lvlText w:val="[%1]"/>
    <w:lvlJc w:val="left"/>
    <w:pPr>
      <w:tabs><w:tab w:val="left" w:pos="420"/></w:tabs>
      <w:ind w:left="425" w:hanging="425"/>
    </w:pPr>
    <w:rPr><w:rFonts w:hint="default"/></w:rPr>
  </w:lvl>
</w:abstractNum>
<w:num w:numId="900"><w:abstractNumId w:val="900"/></w:num>
```

Schema 要求所有 `abstractNum` 排在所有 `num` 之前，新建时用 `first_num.addprevious(an)`，不能直接 append。

## 三、文档没有 numbering 部件时怎么造

手打编号的文档根本没有 `numbering.xml`。`doc.part.numbering_part` 抛 `KeyError`，`NumberingPart.new()` 抛 `NotImplementedError`，两条路都堵。手工造：

```python
from docx.oxml import parse_xml
from docx.opc.part import XmlPart
from docx.opc.packuri import PackURI
from docx.opc.constants import RELATIONSHIP_TYPE as RT

el = parse_xml(
    '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>')
part = XmlPart(PackURI('/word/numbering.xml'),
               'application/vnd.openxmlformats-officedocument.numbering+xml',
               el, doc.part.package)
doc.part.relate_to(part, RT.NUMBERING)
```

之后 `part.element` 就是可编辑的 numbering 根节点。

## 四、域的五个 run

```xml
<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:fldChar w:fldCharType="begin"/></w:r>
<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:instrText xml:space="preserve"> REF _Ref21842 \r \h </w:instrText></w:r>
<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:fldChar w:fldCharType="separate"/></w:r>
<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:t>[1]</w:t></w:r>
<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:fldChar w:fldCharType="end"/></w:r>
```

`separate` 之后的 `w:t` 叫“域结果”，Word 打开会重新算，所以初值写不写准无所谓，但不写会显示空白，最好按编号写个大概。

用 python-docx 构造时，`rPr` 直接从原文字的 run 复制一份（保留宋体、字号），再补 `vertAlign`，不要凭空造字体。

## 五、幂等性：已经在域里的 run 必须跳过

否则对已处理过的文档重跑，会把域结果套上新域，文档直接坏掉：

```python
in_field = set(); depth = 0
for child in p._p:
    if child.tag != qn('w:r'):
        continue
    fc = child.find(qn('w:fldChar'))
    ftype = fc.get(qn('w:fldCharType')) if fc is not None else None
    if ftype == 'begin':
        depth += 1; in_field.add(child)
    elif ftype == 'end':
        in_field.add(child); depth = max(0, depth - 1)
    elif ftype == 'separate':
        in_field.add(child)
    elif depth > 0:
        in_field.add(child)
```

处理循环里加一句 `if run._element in in_field: continue`。

## 六、验证脚本

删一条文献 → 更新域 → 转 PDF 读文字，看编号有没有重排：

```python
import pythoncom, win32com.client as win32, pymupdf, re
pythoncom.CoInitialize()
w = win32.Dispatch('Word.Application')
w.Visible = False; w.DisplayAlerts = 0
d = w.Documents.Open(r'C:\path\test.docx')
d.Fields.Update(); d.Repaginate()
print('页', d.ComputeStatistics(2), '字', d.ComputeStatistics(0), '域', d.Fields.Count)
d.SaveAs2(r'C:\path\test.pdf', FileFormat=17)
d.Close(0)
try: w.Quit()
except Exception: pass

txt = ''.join(pg.get_text() for pg in pymupdf.open(r'C:\path\test.pdf'))
print('双括号异常:', '有' if ('[[' in txt or ']]' in txt) else '无')
for line in txt.split('\n'):
    if re.search(r'\[\d+\]', line) and len(line) > 15:
        print(' >', line[:100])
```

三项判据：域数应等于正文引用处数（区间拆开后会多一些）、页面无 `[[`、每处引用显示为干净的上标方括号。

## 七、现成脚本

`~\thesis27\tools\` 下：

- `superscript_refs.py` —— 只做上标，带 `--check` 模式回检
- `xref_refs.py` —— 上标加交叉引用全套，幂等，支持多文件参数

调用顺序固定：md 生成 docx → 上标 → 交叉引用 → Word 更新域 → 转 PDF 目检。

## 八、坑汇总

| 现象 | 原因 | 处置 |
|---|---|---|
| 15 条文献只识别出 3 条 | 用 `id(p._p)` 去重，lxml 代理 id 复用 | 改用元素本身当 set key |
| 页面上出现 `[5][6]5-6` | `re.split` 正则带捕获组，内容被当正文插回 | split 用无捕获正则，findall 用带捕获 |
| 显示 `[5]-[6]` | 用 `\n` 想做区间，但 `\n` 同样带方括号 | 接受独立域，或定稿手合并 |
| 显示 `[[5]]` | 手写方括号又叠了域自带括号 | 域自带括号时不要再写 |
| 重复跑后文档坏 | 未跳过已在域内的 run | 加 fldChar 深度判定 |
| 参考文献编号不重排 | 段落没用 `numPr`，编号是文字 | 剥掉手打 `[n]` 再挂 numPr |
| `doc.part.numbering_part` KeyError | 文档本来没有编号部件 | 用 XmlPart 手工造并 relate_to |
