---
name: markdown-to-docx
description: 把 md 答案/笔记转成 Word(.docx) 交付主人。主人看不了 .md 文件（2026-09 明确说过"我看不了啊，要word"），凡交付文件（作业/答案/笔记/报告）一律给 .docx 或 .pdf，.md 只作知识库内部存储。含可复用转换脚本 scripts/md2docx.py。触发词：要word、转docx、看不了、md打不开、交作业。
---

# Markdown → Word (.docx) 交付

## 为什么需要
- 主人交付物偏好：**文件要看就用 Word(.docx)**，裸 .md 交付 = 主人打不开，会回头说"我看不了啊，要word"
- 知识库内部（`E:\资料\_知识库\`）用 md 存储没问题；一旦要"交作业/给主人看"，必须转 docx
- 作业文件夹：`E:\资料\作业\`，作业版格式 = 作答 + 教师批改（模拟阅卷：总评+得分/30+扣分点表格+改进建议），范本 `论述题_古典主义悲剧_作业版.md`

## 转换步骤
1. 检查依赖：`python -c "import docx"`（python-docx；本机已装，pandoc 未装）
2. 运行：`python <技能目录>\scripts\md2docx.py <输入.md> <输出.docx>`（或已落盘的 `E:\资料\_scripts\md2docx.py`，同一份）
3. 用 MEDIA: 绝对路径交付 .docx 给主人
4. 读回验证（别只看脚本 exit 0，转档成功≠内容完整）：`python -c "import docx; d=docx.Document('<输出.docx>'); ps=[p.text for p in d.paragraphs if p.text.strip()]; print('段落',len(ps),'字符',sum(len(p) for p in ps))"`，确认标题数/字符数与预期一致再交付

## 脚本能力（md2docx.py）
- 标题 `#`→Heading、`**加粗**`、`> 引用`（左缩进灰斜体）、`-` 无序/`1.` 有序列表、`---` 分隔线、`|` 表格（Table Grid + 表头加粗 + 跳过 `|---|` 分隔行）
- 中文字体：正文宋体（eastAsia），代码 Consolas
- 代码块 ``` ``` 原样保留

## Pitfalls
- 转换脚本放两个位置：技能内 `scripts/`（可移植）+ `E:\资料\_scripts\`（主人工作区顺手），改一处记得同步另一处
- 交付前自查：docx 文件名与 md 同名不同扩展名，放同一目录，方便主人对照
- 多子agent并行产出答案→汇总成单份 md 时，各源引号/标点常不统一（弯引号"" vs 直角引号『』、半角 vs 全角标点），转 docx 前先统一（实踩：把『』统一成""、标题半角问号转全角），否则交付文档标点混乱
- 若主人要改内容再生成：先改 md 再重跑脚本，别让两边漂移出两个版本（主人偏好单一来源）
- Word 里主人可能继续手编（补批注/改答案），改完他给你 docx 时按 docx 为准回灌 md
- **验证参考文献条数别在 join 后的整串文本上用 `^` 锚点**。`''.join(p.text for p in ps)` 把换行抹掉了，`re.findall(r'^\[\d+\]', txt, re.M)` 必然返回 0，会误判成“参考文献整批丢了”。要在段落列表上数：`sum(1 for p in d.paragraphs if re.match(r'^\[\d+\]', p.text))`
- **正文 md 里别留“著录待核”“使用说明”这类元内容**。`gb_report_docx.py` 把 `##` 开头的行一律渲染成一节标题，正式稿里冒出“著录待核事项”很扎眼。转档前切掉存成单独说明文件，正式稿到参考文献为止

## docx → PDF（Windows，无 LibreOffice 时用 Word COM）

主人 Windows 机器装了 Word（`/c/Program Files/Microsoft Office/root/Office16/WINWORD.EXE`）但**没装 LibreOffice**，交付要 PDF 时别走 `soffice`，直接 Word COM 转：

⚠️ **WPS 劫持坑（主人机器装了金山 WPS）**：WPS 会把注册表里 Word 的 CLSID `{000209FF-0000-0000-C000-000000000046}` 的 `LocalServer32` 改写为 `D:\WPS Office\...\wps.exe`。于是 `EnsureDispatch('Word.Application')` / `Dispatch('Word.Application.16')` 启动的是 **WPS 不是微软 Word**，而 WPS 打不开带 TOC 域/updateFields 的文档（报「Kingsoft WPS 文档打开失败」）。诊断：`reg query "HKCR\CLSID\{000209FF-0000-0000-C000-000000000046}\LocalServer32"`。

**绕过：直接启动 WINWORD.EXE + `GetActiveObject(CLSID)` 连运行中的微软 Word**（不经过被劫持的 ProgID）。且**中文路径会触发 Word COM「找不到您的文件」**，要先复制到纯英文临时路径：

```python
import subprocess, time, os, shutil
import win32com.client
WORD_EXE = r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
CLSID = "{000209FF-0000-0000-C000-000000000046}"

# 1) 中文路径 → 英文临时路径（Word COM 对中文路径编码有问题）
src_cn = r"C:\...\中文名.docx"; dst_cn = r"C:\...\中文名.pdf"
tmp = r"C:\Users\ASUS\AppData\Local\Temp"
src_ascii = os.path.join(tmp, "plan.docx"); dst_ascii = os.path.join(tmp, "plan.pdf")
shutil.copyfile(src_cn, src_ascii)

# 2) 清残留（WPS 会劫持 + 锁文件）
for p in ("winword.exe", "wps.exe", "wpscloudsvr.exe"):
    subprocess.run(["taskkill", "/F", "/IM", p], capture_output=True)
time.sleep(2)

# 3) 直接启动微软 Word + 连运行实例
subprocess.Popen([WORD_EXE, "/automation"])   # /automation 抑制启动对话框
app = None
for i in range(30):
    time.sleep(2)
    try: app = win32com.client.GetActiveObject(CLSID); break
    except Exception: continue
# 4) Open 也可能被启动期 RPC_E_CALL_REJECTED，重试
doc = None
for i in range(15):
    try: doc = app.Documents.Open(src_ascii); break
    except Exception: time.sleep(3)

for toc in doc.TablesOfContents: toc.Update()   # 刷新目录页码
try: doc.Fields.Update()
except Exception: pass
doc.Repaginate()
doc.Save()                                        # 缓存目录结果回 docx
doc.SaveAs(dst_ascii, FileFormat=17)             # 17 = wdFormatPDF
doc.Close(False); app.Quit()
shutil.copyfile(src_ascii, src_cn); shutil.move(dst_ascii, dst_cn)   # 移回中文目录
```

坑：`Quit` 报 `AttributeError` = 残留 WINWORD 锁文件，先 `taskkill` 再跑。竖版证书/截图嵌 docx 按图宽 9cm、横图 14cm，避免竖图超 A4 被截断。

**一个 Python 进程只处理一个文档**（2026-11 实踩）。`w = Dispatch('Word.Application')` 后 `for p in files: w.Documents.Open(p)`，第一个文件正常，循环到第二个时抛 `AttributeError: <unknown>.Open` —— 不是文件坏了，是 COM 连接的 Documents 集合在 `doc.Close()` 后失效。**每个文件单独起一个进程**（或每轮重新 `Dispatch` + `CoInitialize()`）。多个文件要批量转时写 shell 循环，别在一个 python 脚本里 for 循环。`Quit()` 抛 `com_error 远程过程调用失败` 同样是常态，只要 `doc.Save()` 在此之前跑过，内容就是好的 —— 别因退出报错判定失败，去核 PDF 页数。

## docx 生成：封面/目录/页码/国标格式

用户要「封面目录页码做好，格式符合国标」的正式交付（策划案/报告），不是 md 转换，而是 python-docx 从零拼三节结构（封面无页码→目录 TOC 域→正文页脚页码从 1 起）。完整 helper（TOC/PAGE 域、页码重排、updateFields、国标版式、清主题字体）+ Word COM 缓存目录的套路见 `references/cover-toc-page-gb.md`。核心坑：PAGE 域在页脚 XML 不在 document.xml；中文字体要清 theme 属性否则变蓝色等线体；`pgNumType` 必须插 `w:cols` 前否则文档损坏；借 codex 写时用 `E:\npm-global\codex.cmd` 全路径 + git init + 注入 DEEPSEEK_API_KEY。

**现成脚本**：`scripts/md2docx_gb.py` 已把三节结构+国标版式+updateFields 封装好，直接 `python .../scripts/md2docx_gb.py <md> <docx>`（2026-10 实测跑通）。md 约定：`#` 封面主标题 / `>` 封面副标题 / `##` 各节标题（进目录 Heading1）/ 其余非空行=正文段落。验证国标结构：`len(doc.sections)==3`、正文 footer XML 有 1 个 `PAGE`（封面/目录 footer 无）、`document.xml` 有 1 个 `TOC`、`settings.xml` 有 `updateFields`。

### 单节国标报告（学生作业/调研报告，不要封面目录）

**场景**：主人交作业、实践调研报告、实习报告——老师给了模板（如「附件3 学生实践调研报告」），**只交正文，不能加封面和目录**（加了反而多余）。这时别用 `md2docx_gb.py`（它是三节结构），用 `scripts/gb_report_docx.py`：

```bash
python <技能目录>/scripts/gb_report_docx.py 输入.md 输出.docx
```

它直接读 md 生成单节国标正文（A4 / 上下2.5 左右3cm / 页脚居中「— 1 —」），md 约定：`#` 主标题 → `## ——xxx` 副标题 → `学院：…` 信息行 → `## 一、` 一级标题 → `### （一）` 二级标题 → `|` 表格（自动转三线表）→ 其余非空行 = 正文段落，`---` 与空行一律丢弃。

**国标参数（2026-11 主人实测要求，逐条对过）**：

| 项 | 值 |
|---|---|
| 大标题 | 黑体 三号 16pt 居中 |
| 副标题/信息行 | 宋体 小四 12pt 居中 |
| 一级标题「一、」 | 黑体 四号 14pt，段前12pt 段后6pt |
| 二级标题「（一）」 | 宋体 小四 12pt **加粗**，首行缩进2字符 |
| 正文 | 宋体 小四 12pt，行距 1.5 倍，**段前段后 = 0** |
| 首行缩进 | `w:ind @firstLineChars="200"`（用字符单位，不用 24pt 死值） |
| 表格 | **三线表**：上下 1.5pt 单线 + 表头下 0.75pt 单线，无竖线无内横线；表内宋体五号 10.5pt 居中；**表题在表上方**「表1 xxx（N=124）」 |
| 颜色 | 全黑。`md2docx.py` 用 Heading 样式会带出**蓝色标题**，必须改直排 + `run.font.color.rgb = RGBColor(0,0,0)`，并删 `rFonts` 的 4 个 theme 属性 |

**主人原话（2026-11）**：「要符合论文国标格式，不要有蓝色字体，段与段之间不要空行，首段空两格，字体大小也调整」——这四条是默认基线，以后交论文体文档直接按此出，不用等他说。

**验证（交付前必跑）**：解 `word/document.xml` 数一数——`4472C4`/`themeColor` 出现 0 次（无蓝字）、`firstLineChars="200"` 等于正文字段数、`w:before="0"`+`w:after="0"` 覆盖全部正文段、`<w:tbl>` 数对、`from docx import Document; Document(f).paragraphs` 里**空段落数必须为 0**（段间无空行）。

**刷新目录别死磕 Word COM**：Word COM 缓存目录要先 `taskkill` WPS——这是破坏性操作，在桌面会话会被审批拦截、卡住流程（2026-10 实踩）。更省事的替代：国标脚本已写 `updateFields=true`，微软 Word 打开时自动刷新目录页码；交付时告知主人「用 Word 打开自动刷新，WPS 打开则右键目录→更新域」即可，不必非用 Word COM 缓存。

### 某院校《学术论文写作》课程作业格式（复刻主人自己的稿子）

**场景**：主人把一份他自己写的课业 docx 甩过来说「模拟这样的语言逻辑，字体格式也是这样」。这时既不是国标也不是 `gb_report_docx.py` 那套，是**照他那份逐段扒参数**。

**别凭眼睛看**。用 python-docx 逐段打印 `style.name / font.name / font.size / bold / first_line_indent / line_spacing / line_spacing_rule`，再单独打印 `doc.styles['Heading 1']` 的 `rPr/rFonts@eastAsia`。一次就能把整套版式量出来。

实测参数（2026-11，源：`用户 文献综述-2.docx`）：

| 项 | 值 |
|---|---|
| 页面 | A4，**四边全 2.0cm**（不是 gb_report 的上下2.5/左右3） |
| Normal | 西文 Times/Calibri，中文宋体，小四 12pt，两端对齐，首行缩进 24pt，**固定行距 24pt**（EXACTLY，不是 1.5 倍） |
| 一/二/三级标题 | 黑体 12pt 加粗，左对齐，段前段后 0，固定行距 24pt，`rFonts` ascii=宋体 eastAsia=黑体 |
| 摘要/关键词 | **黑体 10.5pt**，固定行距 16pt |
| 封面 | 校名 26pt 粗 / 学年学期与课程名 22pt /（题名）行 12pt / 学生信息行加粗 |
| 参考文献 | 悬挂缩进 `left=24pt first=-24pt` |
| 分节 | 2 节：封面+目录无页码 / 正文页脚 PAGE 域从 1 起 |

**现成脚本**：`scripts/ysxy_docx.py`（2026-11 实测跑通，封面+目录+正文+参考文献共 12 页）。md 约定：`:::cover … :::` 封面区逐行 / `# 题目` / `> 作者` / `ABS:摘要：…` / `KEY:关键词：…` / `## 一、` / `### （一）` / `#### 1.` / `[1] ` 开头=参考文献悬挂缩进 / 其余非空行=正文。

四个实踩坑：

1. **md 里的二级标题常是裸行**。`（一）研究背景` 前面没写 `### `，脚本就当正文渲染，出来是宋体非加粗、混进段落里。转档前批量扫：`len(s)<=30 and '。' not in s and '，' not in s` 的独立行即候选标题，`^（[一二三四五六七八九十]+）` 补 `### `、`^[一二三四五六七八九十]+、` 补 `## `。**必须跳过 `:::cover` 块内的封面行**，`学院：`/`学号：` 同样满足短行条件，误补前缀会把封面搞坏。另注意「选题构思」下面手打的「一、二、三」要与正文「一、引言」区分层级，补成 `###` 而不是 `##`。
2. **`目　录` 用全角空格会在 Word 2010 里折成两行**「目」「录」。直接写 `目录`。
3. **封面内容会全挤在页面上部**，下方留白过半、头重脚轻。开头补 6 个空段落（1.5 倍行距）再放校名；`评阅意见：` 后补 3 个空行给主人手写。
4. **`app.Quit()` 抛 `com_error 远程过程调用失败` 不等于失败**。`doc.Save()` 与 `ExportAsFixedFormat()` 都在它之前跑完了，docx 和 PDF 都是好的。判断依据是文件存在、页数对不对，不是退出码。

**验证顺序**：生成 → Word COM `Fields.Update()` + `TablesOfContents(1).Update()`（目录这才真有页码，否则只剩占位提示）→ `ExportAsFixedFormat(pdf, 17)` → `pymupdf` 渲 110dpi 抽查封面与正文首页。查四样：首行缩进、行距均匀、标题加粗、页脚有页码。

目录里「选题构思」下的「一、选题来源与初衷」与正文「一、引言」编号并列，是主人**原稿本来就这样**，别自作主张改编号体系。

**「模拟这样的语言逻辑」包含两层，别只做版式。** 扒完字体行距，还要逐段读原稿提炼行文套路：每节首句先下一句总起判断、中间用「有学者……指出」「该研究进一步指出」引述、段末跟一句自己的评价或推论、破折号作补充说明、长段落不分点、术语少用英文、摘要用「随着……正在成为……本文系统梳理了……研究发现……基于此，本文提出……」的固定句式。照这个骨架写新内容，读起来才像本人。只对版式不对文体，交上去一眼就看得出换了人写。

## 填写下发模板（表格）

另一种常见活的：学校/单位给一份固定格式的表格 docx（开题报告书、审批表、申请书），要求在表格单元格里填。**不是从零生成**，别套上面的 md2docx 脚本。完整方法、代码骨架与三个实测坑见 `references/docx-table-form-filling.md`。

三条先记住：

1. **别清空错格子**。两列表格里 `cells[0]` 是栏目名，`cells[1]` 才是值。清零会把“选题来源”这类标签抹掉，值落进窄列被拆字。先打印每行每列文本与列宽认格子。
2. **单元格内的分页只认 `w:trPr/w:cantSplit`**。`page_break_before` 与 `keep_together` 在表格里全部失效。且只给短行加，长内容行必须允许拆，否则整行溢出丢内容。
3. **交付前扫每页首行文本**抓孤字跨页（`d[i].get_text()[:36]`），比看图像快得多。

产出后交付时说清楚哪些格子故意留空（签字栏）、哪几个字段需要主人自己确认（指导教师、选题来源口径）。

## 原地修订主人已有的 docx（不重生成）

主人拿自己写的稿子说“改一下”“弄出来”时，**别用脚本重生成**——他会认不出自己的格式。在原 docx 上改文字，保留章节、字体、缩进。三条实测坑：

1. **Word 自动编号在 `p.text` 里看不见**。段落挂了 `w:numPr` 时，python-docx 只返回文字，Word 渲染却会自动加“第一、”。你手写一个序号就成了“第一，第一，”，docx 文本检查完全正常、转成 PDF 才露。改稿后扫 `p._element.pPr.numPr`，删掉与手写序号冲突的。
2. **删掉整节后必须更新 TOC 域**，否则目录留着已删章节名 + 一行“错误！未定义书签。”。`doc.TablesOfContents(1).Update()` 之后还要 `doc.Fields.Update()`，否则目录更新了但别的域没更。
3. **参考文献段落数量不变时，逐段换文字就能保住自动编号与悬挂缩进**；数量一变就得重建列表。

改文字用 `p.runs[0].text = new` 再删掉其余 run，能保住该段字体字号。**区分校对与润色**：错字、编号、标点、著录缺失直接改；把口语改写成学术句属于语言润色（学校／单位可能明令禁止用 AI 做），改完必须单列清单告知主人原句与新句，让他自己决定用不用。

完整流程、脚本骨架与交付自检见 `references/docx-inplace-revision.md`。

## 学术文档：正文上标引注（方括号在右上角）

论文、文献综述要求“方括号标在右上角”。md 里的 `[1]` 直接转出来是与正文同字号的基线字，不合格。在段落生成函数里按正则拆 run，只给编号那段设 superscript：

```python
def para(doc, text, ..., sup=False):
    p = doc.add_paragraph()
    ...
    if sup and re.search(r'\[\d+\]', text):
        for part in re.split(r'(\[\d+\])', text):
            if not part:
                continue
            r = p.add_run(part)
            set_font(r, font, size, bold)
            if re.fullmatch(r'\[\d+\]', part):
                r.font.superscript = True
    else:
        r = p.add_run(text)
        set_font(r, font, size, bold)
```

只对**正文段落**开 `sup=True`。参考文献列表里的 `[1]` 必须保持正常基线，那里是条目标号不是引注，一起上标就错了。

**验证上标别用眼睛，更别用 vision**。把 PDF 渲成 110 DPI 的图交给 vision 检查，它会很肯定地说“编号不是右上角上标，与正文同字号位于基线”——而 docx 里其实已经设好，是缩略图分辨率看不出来。正确做法是遍历 runs 数：

```python
from docx import Document
d = Document('x.docx')
print(sum(1 for p in d.paragraphs for r in p.runs if r.font.superscript))
```

数字要等于正文标引数（参考文献行没设上标，不计入）。同理，任何字号、颜色、行距的细微差异都别指望 vision 验证，读 XML 或 python-docx 属性。

**长文档生成后必扫四样**（中文长文尤其容易漏）：

1. **繁体字混入**。生成时偶发错出「藝術机构」「觀眾」「這個」，md 里扫一遍最快：`grep -n "藝\|術\|觀眾\|個\|這\|還" file.md`，应当为空。拖到 PDF 交付才被发现就要重跑一遍全流程
2. **引注编号连续**。`sorted(set(re.findall(r'\[\d+\]', body)), key=lambda x: int(x.strip('[]')))` 应为 1 到 N 元缺
3. **引注最大编号 = 参考文献条数**。两者不等就是漏引或漏列，交上去必被挑
4. **源 md 有没有混进别份文档的内容**。2026-11 事故：综述 md 末尾混了一整段开题报告的「选题构思/研究意义与创新点/与专业联系」，生成的 docx 一路带着，页数多了两页才发现。只数参考文献条数完全查不出来。转完抽 PDF 全文查污染关键词计数：

```python
all_t = ''.join(p.get_text() for p in pymupdf.open(pdf))
for k in ['研究意义与价值', '创新点', '与专业的联系']:
    print(k, all_t.count(k))   # 全为 0 才交付
```

发现后别直接删——先把那段切出来另存（如 `_note/选题构思素材.md`），它可能是另一份文档的正文，删了就没了。

另：引注编号要按正文**首次出现**顺序排，不是按中外文分组。中文文献夹在英文中间是正常的，别为了好看重排，重排就得上正文一起改。

## 表题位置：两种规范，接活前先问是哪一类

- **国标报告、调研报告**（本技能 `gb_report_docx.py`）：表题在**表格上方**，“表1 xxx”居中。
- **某院校本科论文、综述**：表序与表题置于**表格下方**居中，楷体五号。这与常见国标相反，是学校规范化要求写定的。

别默认套国标。做法：在 md 里就按目标位置把表题行放好（表格前或后），脚本按行序渲染即可，不必做位置识别。判定表题行用 `re.match(r'^表\s*\d', s)`，楷体五号、段前 3 段后 8。

三线表手写实现（自建综述脚本时照抄）：`tblPr` 插 `tblBorders` 六边全 `none`，再给表头行 `tcBorders` 设 top `sz=12` 加 bottom `sz=6`，末行 bottom `sz=12`。sz 单位是 1/8 pt。表内宋体五号居中，表头加粗。

## 关联
- 输出 PDF 走 `pdf-generation` 技能（fpdf2 程序化生成）；docx 转 PDF 走上面的 Word COM；docx 生成走本技能
- 目标院校知识库总入口 `zhongxi-kaoyan`（该技能为手动编写，curator 不可改，需更新时告知主人手动）
