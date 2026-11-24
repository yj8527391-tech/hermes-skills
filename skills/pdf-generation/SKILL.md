---
name: pdf-generation
description: 程序化生成 PDF（fpdf2）——覆盖中文字体处理、表格排版、A4 页眉页脚、生成后验证。当用户要"整理成 PDF / 打印版 / 图片版文档"（课表、计划、清单、报告）时使用。脚本在 Windows 中文环境实测通过。
---

# PDF 生成（fpdf2 · 中文优先）

## 触发条件
- 用户要求"整理成 PDF / 打印版文档"（考研课表、计划表、清单、证书、报告）
- 需要程序化排版「表格 + 中文内容」的 A4 文档

## 核心流程
1. 安装：`pip install fpdf2 -q`（本机 2.8.x 实测 OK）
2. **中文字体（Windows 关键）**：用 `C:\Windows\Fonts\simhei.ttf`（黑体，单 TTF 文件，fpdf2 直接支持）
   - ⚠️ 不要用 `msyh.ttc` / `simsun.ttc`：TTC 是字体集合文件，fpdf2 兼容性差；选 .ttf 单字体最稳
   - 黑体无粗斜体变体，标题靠字号区分
3. 注册：`pdf.add_font("SimHei", "", r"C:\Windows\Fonts\simhei.ttf")`
4. 表格列宽总和必须 = 内容宽：A4 宽 210mm - 左右边距 12*2 = **186mm**
5. 生成后必须验证（见下）

## 表格行高计算（关键技巧）
fpdf2 的 multi_cell 要先 dry_run 算出实际行数，才能确定行高再绘制：
```python
cell = pdf.multi_cell(w_mm, 5.5, text, border=0, dry_run=True, output="LINES")
h = len(cell) * 5.5 + 2        # 行高 = 行数 × 行高 + 内边距
```
流程：遍历行内所有单元格取 `max_h` → 若 `pdf.get_y() + max_h > 270` 则 `add_page()` → 逐列 `set_xy(x, y0)` + `multi_cell(..., fill=True)` 绘制 → `set_xy(l_margin, y0 + max_h)`。

## 页眉页脚
覆盖 `FPDF.header()` / `FPDF.footer()`：非首页显示标题 + 页码（`self.page_no()`）；页脚标语。`footer()` 里 `set_y(-16)` 固定底部。

## 验证（每次生成后必做）
```python
import re
data = open(path, 'rb').read()
len(re.findall(rb'/Type\s*/Page[^s]', data))   # 页数
b'SimHei' in data                               # 字体已嵌入
```
⚠️ 中文正文在 FlateDecode 压缩流里，**直接搜中文字节会返回 False——属正常**，别误判为乱码。页数 + 字体名够用了。

## 此用户偏好（已在会话验证）
- 输出路径：`~\`（用户数据目录；软件/文件一律不装 C 盘）
- 交付方式：`MEDIA:<绝对路径>` 发送 + 报告页数/字体验证结果
- 视觉风格：暖色调（红/橙表头 + 交替行浅色底）、标题大字号 + 副标题行
- 生成脚本保留在 ~\，用户改需求时复用脚本微调重新生成，不重写
- 用户改课表/计划时：给出修订版完整表格 + 分阶段调整 + "劳逸结合红线"，再问是否出 PDF

## Pitfalls
- fpdf2 2.5.2+ 的 `ln=True` 弃用警告（改用 `new_x/new_y`）：无害，可忽略
- **PDF 内正文避免 emoji**（✅⚠️💪☀️）：黑体缺字形会出豆腐块/乱码，用纯文字或简单符号
- 列宽和必须精确等于 186mm，否则表格错位
- multi_cell 的 dry_run=True 必须配合 output="LINES" 才能拿行数
- 生成脚本放 E 盘再运行，避免 Python -c 内联长脚本被终端标记拦截
- **multi_cell 居中后 x 不归位（实测报错）**：`multi_cell(0, h, text, align='C')` 渲染结束后 x 停在文本起始处（居中偏移位置），下一个 `multi_cell(0, ...)` 从中间开始、可用宽度不足，抛 `FPDFException: Not enough horizontal space to render a single character`。修复：封装 `def mc(w,h,txt,align='L'): pdf.set_x(LM); pdf.multi_cell(w,h,txt,align=align); pdf.set_x(LM)`，**所有 multi_cell/cell 前显式 set_x(l_margin)**（header() 内同样处理）
- **第一页必须显式 add_page()**：multi_cell 前未开页抛 `No page open, you need to call add_page() first`——分节循环生成时第 1 节也要 add_page，别只给后续节加
- **md 表格 → PDF 表格**：`strip('|').split('|')` 解析单元格；`re.fullmatch(r':?-{2,}:?', c)` 跳过分隔行（`|---|---|`）；表头深色底 + 数据行交替浅色底；行高 dry_run 算法见模板；跨页判断 `get_y() + max_h > 272` 时 add_page。完整解析脚本见 `templates/md_to_pdf.py`（标题/引用块/正文/md表格 → PDF）
- **验证表格渲染别带 md 符号**：pymupdf `get_text()` 检查关键词时用纯文本（如 `'具体位置'`），带管道符的 `'| 具体位置'` 永远 False——不是渲染失败，别误判（实测虚惊一场）
- **黑体缺 ⑪⑫ 带圈数字字形**：simhei.ttf 支持 ①-⑩（U+2460-2469），但 ⑪-⑳（U+246A 起）缺字形，渲染时 stderr 报 `missing the following glyphs`、出豆腐块（实测"剧本分析十二步"的 ⑪⑫）。生成前把 ⑪⑫ 等替换成全角括号（11）（12）或普通数字。检测：跑生成脚本看 stderr 有没有 `missing ... glyphs` 警告，有就逐个改。
- **行内加粗/关键词高亮用 write() + 显式行高（实测可靠，0 重叠）**：黑体无粗体变体，「加粗」靠「深红 + 稍大字号」区分最醒目（`set_font('SimHei','',size+1)` + `set_text_color(ACCENT)`）。旧坑"字都叠在一起"的根因是 **`write()` 没给显式 `h`**——默认按 simhei 字体 ascent/descent 算行高会过小。修复：`fpdf.write(h, seg)` 里 `h` 显式给足（≥字号 1.6 倍：10.5pt→5.6mm、11pt→7mm、12pt→7.5mm），逐段切换颜色/字号渲染（普通段 BODY 色 + size，关键词段 ACCENT 红 + size+1），最后 `ln(h+0.6)`。注意 write() 自动换行后 x 回到左 margin（无悬挂缩进），缩进列表项的长文本换行后对齐左边距。生成后必跑重叠校验：pymupdf `get_text('blocks')` 两两比对 y/x 区间是否同时重叠，重叠数应为 0。完整实现见本会话 `E:\资料\_知识库\_md_to_pdf_bold.py`（多级标题 #/##/###/#### + 列表缩进 + 行内 **加粗**，实测 0 重叠）
- **PDF 被占用 PermissionError（[Errno 13]）**：用户正开着旧 PDF 时 `pdf.output(OUT)` 报权限错误。修复：`pdf.output(OUT + '.tmp')` → `os.replace(tmp, OUT)` 尝试覆盖；失败则交付 tmp（或复制到用户工作区/别处干净名），提示用户关闭旧文件后再统一覆盖，别默认生成 v2 后缀

## 支持文件
- `templates/fpdf_chinese_table.py` — 可复制修改的完整模板（含中文表格类 + dry_run 行高算法）
- `templates/md_to_pdf.py` — md 文档 → PDF 通用模板（# 分节/引用块/md表格/正文段落，含 mc() set_x 封装与表格跨页），实测于论述题答案+教师批改表合成 PDF
- `templates/md_to_pdf_rich.py` — md → PDF 增强模板（封面+目录+`#/##/###` 多级标题+`-`列表+行内`**加粗**`），实测于考研背诵手册（7 科名词/简答/术语清单合成 10 页 PDF）。适合无表格、靠标题层级和加粗组织的中文长文档
