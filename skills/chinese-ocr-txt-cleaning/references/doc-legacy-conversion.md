# 旧版 .doc 剧本/资料转文字（win32com 配方）

知识库待办常见：60必读文件夹里有旧格式 .doc（如《北京人》剧本.doc）。python-docx 只支持 .docx，旧 .doc 需先经 Word COM 转换。实测 2026-08-31（Windows + 已装 Word 环境，win32com 可用）。

## 三步配方

```python
# 1) doc → docx（Word COM）
import win32com.client as win32
word = win32.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(src, ReadOnly=True)
doc.SaveAs2(docx_tmp, FileFormat=16)  # wdFormatXMLDocument
doc.Close(False)
word.Quit()

# 2) docx → txt（python-docx，跳过空段）
from docx import Document
doc = Document(docx_tmp)
lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
open(out, 'w', encoding='utf-8').write('\n'.join(lines))
```

实测《北京人》：243KB doc → docx 110KB → txt 4.2万字/1000行。PowerShell 里可用 `python -c "..."` 直接跑（注意引号转义，用单引号包 Python 代码）。

## 关键坑：转换成功 ≠ 剧本完整

- 转出后**必须**验证完整性：`search_files` 搜「第X幕」统计幕数。
- 实测《北京人》.doc 只有**第一幕**（分5小节），第二、三幕缺失——doc 本身是残缺版。
- 残缺版本入库要标注 ⚠️（写进 `_剧本库总览.md` 的文字版清单和待办区），别当全文精读。
- 同理：.doc 也可能是辅导资料而非剧本原文（提取后按内容归入对应科目，不一定是 11_剧本库）。

## 参考流程
- 转换后脚本产物：docx 可留可删（txt 已是最终态）；知识库惯例 txt 存 `11_剧本库\原名_作者.txt`
- 与 `ocr-and-documents` 互补：本配方管 Word 旧格式，那个管 PDF/扫描件
