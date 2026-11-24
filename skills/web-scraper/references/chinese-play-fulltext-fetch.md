# 中文剧本全文获取：本地 .doc 转换 + 中华典藏网抓取（实测 2026-08-31《北京人》）

场景：知识库里只有旧格式 `.doc` 剧本（或 PDF 扫描版），需要完整文字版。流程：本地 .doc 转文字 → **验证是否全剧完整**（旧文档常残缺！）→ 残缺则从中华典藏网抓全文 → 清洗水印/导航 → 与本地版关键词比对验证质量。

## 1. 旧 .doc → txt（win32com 两步，Windows 实测）

无需 pandoc/antiword，机器装了 Office 就能跑：

```python
import win32com.client as win32
word = win32.DispatchEx('Word.Application')
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(src, ReadOnly=True)
doc.SaveAs2(docx_tmp, FileFormat=16)  # 16 = wdFormatXMLDocument
doc.Close(False)
word.Quit()

from docx import Document
d = Document(docx_tmp)
lines = [p.text.strip() for p in d.paragraphs if p.text.strip()]
open(txt, 'w', encoding='utf-8').write('\n'.join(lines))
```

注意：写 `.py` 文件再运行，别用 `python -c` 内联（PowerShell 二次解析坑，见 web-scraper 陷阱4）。

## 2. ⚠️ 转完必须验证全剧完整（关键教训）

《北京人》.doc 转出来发现**只有第一幕**（分5小节），二、三幕缺失——旧文档可能是节选/残缺版。验证法：
- 搜 `第[一二三]幕` 标记 + 结尾 `幕徐落|闭幕`
- 多幕剧确认有 `第二幕`/`第三幕` 分界，单幕结尾出现"闭幕"即可能残缺
- 对照已知剧情核对名场面台词（如《北京人》应有"吞了鸦片烟"、"忍不下去"）

## 3. 中华典藏网（diancangwang.cn）抓全文

戏曲/剧本/诗词全集站点，目录页 `https://www.diancangwang.cn/shicixiqu/<id>/` 列出全部分幕链接（实测《北京人》三幕齐全）。页面无反爬，纯 requests + BS4 即可。

### 编码探测（必做，页面 charset=utf-8 但直接 r.text 会乱码）

```python
def fetch(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0'}, timeout=30)
    for enc in ('utf-8', 'gb18030', 'gbk'):
        try:
            return r.content.decode(enc)
        except Exception:
            continue
    return r.text
```

### 正文容器选择

```python
def extract_body(html):
    soup = BeautifulSoup(html, 'lxml')
    for sel in ('div#content', 'div.content', 'article', '.article-content', '.showtxt', '#chaptercontent'):
        el = soup.select_one(sel)
        if el:
            return el.get_text('\n', strip=True)
    # 兜底：文本最长的 div
    return max((d.get_text('\n', strip=True) for d in soup.find_all('div')), key=len)
```

### 清洗两坑（实测）

1. **站点水印穿插行间**：形如 `DFT中华典藏网` / `PZo中华典藏网`（随机 1-4 位字母数字前缀 + 站名），散落在正文每段末尾：
   ```python
   text = re.sub(r'[A-Za-z0-9]{1,4}中华典藏网', '', text)
   text = text.replace('中华典藏网', '')
   ```
2. **导航残留被换行拆开**：`首页 > 诗词戏曲 > 北京人 > 第二幕` 在 get_text 后可能变成多行（`首页\n>\n诗词戏曲\n...`），单行 replace 匹配不到。用容忍换行的正则：
   ```python
   text = re.sub(r'首页\s*\n?\s*>\s*\n?\s*诗词戏曲\s*\n?\s*>\s*\n?\s*北京人\s*\n?\s*>\s*\n?\s*(第[一二三]幕|北京人|曹禺)\s*\n?', '', text)
   text = re.sub(r'\n{3,}', '\n\n', text)
   ```

## 4. 质量验证（必做，防垃圾源）

用本地已有版（doc 转出的第一幕）若干**独特台词**与新抓版比对，全部命中才可信。实测《北京人》第一幕 5 句（"它叫'孤独'"、"你这两只巧手"、"要杀就杀，要打就打"、"成为他永远的奴隶"、"哀静"）全部命中 → 判定同源可信。

## 5. 落库动作

- 完整版存 `11_剧本库\<剧名>_<作者>_完整三幕.txt`（UTF-8），删掉残缺单幕版和中间 docx
- 更新 `_剧本库总览.md`（已提取文字版表格 + 待办划掉）
- 更新记忆（文字版清单 + 来源）
