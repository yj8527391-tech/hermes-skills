# 原地修订使用者已有的 docx

使用者（本实例：某院校艺术管理专业本科生）拿自己写好的 `xxx.docx` 说“融合一下”“把这份弄出来”。**不要另写一篇，不要用脚本重生成**。他要的是自己那篇被修干净，不是换一篇陌生的。

## 一、先读全，再动手

终端直接 `print` 长文档常被截成一行，靠它判断内容必翻车。先落 txt 再 read_file：

```python
from docx import Document
d = Document(src)
lines = [f"[{i}]({p.style.name}) {p.text.strip()}"
         for i, p in enumerate(d.paragraphs) if p.text.strip()]
open(out_txt, "w", encoding="utf-8").write("\n".join(lines))
```

带段落索引和样式名，后面定位改哪一段全靠它。一万两千字的综述一次能读完——读完才知道毛病在哪，不读就改一定漏。

## 二、改稿骨架

`set_text` 只改第一个 run、删掉其余 run，保住该段字体字号缩进：

```python
def set_text(p, text):
    if not p.runs:
        p.add_run(text); return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
```

按“旧串 → 新串”顺序跑，每段改完重新取 `p.text` 再匹配下一条：

```python
for p in paras:
    t = p.text
    for old, new in FIX:
        if old in t:
            set_text(p, t.replace(old, new))
            t = p.text
```

只对确认真实存在的串设 `assert`。跑完打印“命中 N/M”，没命中的说明原稿与预期不符，回去看原文，**别硬改**。

## 三、Word 自动编号陷阱（最常见的隐形坑）

段落挂了 `w:numPr` 时，python-docx 的 `p.text` **不包含**自动编号的文字，Word 渲染却会加上。用户已经手写了“第一，”你再替换上去，就成了“第一，第一，”。

- 症状：docx 文本检查干净，解 XML 搜“第一，第一”也是 0 次，但转成 PDF 就有。**只有渲染才能暴露。**
- 诊断：遍历 `p._element.pPr.numPr`，打印命中段的文本。
- 修法：删掉冲突段的 `numPr`（保留手写序号）；其他自动编号列表（如参考文献）保持不动。
- 判断依据：同一组序号里如果有几段有 `numPr` 几段没有，统一成手写更稳。

```python
for p in d.paragraphs:
    pPr = p._element.pPr
    if pPr is not None and pPr.numPr is not None and p.text.strip().startswith("第一，"):
        pPr.remove(pPr.numPr)
```

## 四、删节 + 更新目录

删掉混进来的非正文章节（如综述里夹着的“选题构思”）按标题定位，删该段及其后所有段落。删完目录还是旧的，会留着已删章节名和“错误！未定义书签。”——交上去最刺眼的就是这行。

```python
import win32com.client as w
app = w.DispatchEx('Word.Application'); app.Visible = False; app.DisplayAlerts = 0
doc = app.Documents.Open(path)
doc.TablesOfContents(1).Update()
doc.Fields.Update()
doc.Save()
try: doc.Close(0); app.Quit()
except Exception: pass     # Quit 常抛“远程过程调用失败”，文件已存，忽略
```

验证：转 PDF 后搜目录页文本，确认 `'选题构思' not in text and '未定义书签' not in text`。

## 五、参考文献批量补全

用户稿子里的参考文献普遍只有题名、作者空着。补全顺序：

1. 把全部题名整理成一列，交给能批量检索的通道（知网校园网 + UIA 地址栏直达，见 `windows-gui-automation` 技能「路径D」；英文文献用 Kimi 联网）。
2. 一轮能拿回 8—10 条“题名｜作者｜来源｜出版日期”，**作者是最大缺口，先补齐**。
3. **列表页只给出版日期，不给期号和页码**。期号按出版日期推（月刊月份≈期号，半月刊要算），推出来的标“需核”；页码必须进详情页。交付时把推断项逐条讲出来，别假装完整。
4. 原稿参考文献段若是自动编号列表，**逐段换文字**（数量相同）就能保住编号与悬挂缩进，不必重建列表。
5. 英文著录用 Kimi 能补齐出版社与卷期页码。实例纠正过三处：Walmsley 那本书是 Palgrave Macmillan 不是 Springer；Lindelof 在 *International Journal of Cultural Policy* 2015, 21(2): 200-218；Kawashima 是华威大学文化政策研究中心 working paper No.6。
6. **核不到就拿出来问使用者**，不要沉默保留，也不要擅自把作者题名换成看起来像的另一篇。

## 六、否认一条文献也要拿出检索证明

用户稿子里可能引了不存在的条目。换 2—3 组同义检索词交叉确认再下结论：篇名含“买谷子”11 条全是报纸、含“买谷子现象”仅 1 条报纸 → 那篇《买谷子现象研究述评》确实不存在。然后如实报告 + 给可核到的替代文献，让使用者决定。

## 七、校对 vs 润色（必须分开报）

| 类别 | 例子 | 怎么处理 |
|---|---|---|
| 错字／错词 | “吃苦经济”→“谷子经济”、“他基于”→“她基于” | 直接改，校对性质 |
| 编号／标点 | `[[17]`→`[17]`、并列引号补顿号、引号嵌套、逗号错位 | 直接改 |
| 著录补全 | 补作者、卷期、页码 | 直接改 |
| 结构删除 | 删掉混入的非正文章节 | 改并告知 |
| **句子改写** | 口语判断句 → 学术表述 | **单列清单，原句新句都给，让使用者自己决定用不用** |

改写三句以上就必须在交付说明里单独列出来。学校和单位可能明令禁止用 AI 做语言润色，改完不说等于替他踩线。

顺带：改写句子前先看清楚上下文有没有已经说过同一件事——本次就出现过把“迁移到表演艺术场景”又重复了一遍，靠读 PDF 全文才发现。

## 八、交付前自检

- [ ] 转 PDF，逐页看渲染图（docx 文本干净不代表排出来没毛病）
- [ ] 搜 PDF 全文本：无重复编号、无“未定义书签”、无孤字跨页
- [ ] 目录页码与实际一致；参考文献编号从 [1] 连续到最后一条
- [ ] 桌面副本已覆盖——旧版留在桌面是最高频的翻车点
- [ ] 待核清单（推断的期号、缺的页码、存疑文献）逐条写给使用者，不留在自己脑子里
