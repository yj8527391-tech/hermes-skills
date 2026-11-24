# Chinese Search Alternatives for Web Scraping

When scraping Chinese content, standard search engines (Baidu, Google) and social platforms (Zhihu, Xiaohongshu) have aggressive anti-bot measures. This file documents working alternatives.

## The Problem

| Target | Anti-Bot Behavior | Notes |
|--------|-------------------|-------|
| Baidu (web search) | Returns CAPTCHA page (1488 bytes) for non-browser requests | Even with proper User-Agent headers. 实测首 1-2 次查询正常，随后返回与查询无关的重复缓存垃圾结果，再往后才出验证码 —— 多查询研究别依赖它 |
| Zhihu | Returns HTTP 403 for automated requests | No known bypass |
| Xiaohongshu (小红书) | Requires login, heavy JS | Web version restricted |
| CNKI (知网) | JS-dynamic content, requires institutional auth for full text | PDFs may be image-scans |

## Solution: 搜狗微信搜索 (Sogou WeChat Search)

**搜狗微信搜索** indexes WeChat Official Account (微信公众号) articles — a huge corpus of Chinese content including:
- University official announcements
- Exam prep / study abroad /考研辅导 articles  
- Industry analysis
- Personal experience sharing

### How to Use

```python
import requests, re, urllib.parse

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

kw = '目标院校 戏剧管理 考研'
url = f"https://weixin.sogou.com/weixin?type=2&query={urllib.parse.quote(kw)}"
r = requests.get(url, headers=headers, timeout=10)

# Extract titles and summaries from search results
titles = re.findall(r'<h3>.*?<a[^>]*>(.*?)</a>.*?</h3>', r.text, re.I | re.DOTALL)
summaries = re.findall(r'class="txt-info"[^>]*>(.*?)</p>', r.text, re.I | re.DOTALL)

for t, s in zip(titles[:5], summaries[:5]):
    clean_t = re.sub(r'<[^>]+>', '', t).strip()
    clean_s = re.sub(r'<[^>]+>', '', s).strip()
    print(f"{clean_t}\n  {clean_s[:200]}\n")
```

### Advantages
- **Search results are accessible** — titles and abstracts extracted from the search page itself
- **No CAPTCHA** — at least not as aggressive as Baidu's
- **Rich content** — WeChat articles are long-form, detailed, and often contain official information
- **University-specific** — many Chinese universities publish on WeChat Official Accounts

### Limitations
- **Article links trigger anti-bot** — clicking an article link redirects to `weixin.sogou.com/antispider/`. The full article content is NOT accessible via automated request.
- **Search snippets are enough** — titles + 2-line abstracts often contain the signal you need
- **Rate limit** — add delays between searches

### Workaround for Full Article Access
If you need the full article text (not just search snippets):
1. Note the article title and source account name
2. Search manually via WeChat mobile app or web version
3. Some articles may have cached versions on other platforms

## Other Alternatives

| Alternative | Works? | Notes |
|------------|--------|-------|
| 360 搜索 (so.com) | ✅ **Best for Chinese stats/news** | See section below. Snippets carry the data; links are 400 bait |
| Bing (cn.bing.com) | ⚠️ Only for exact known titles | Topical Chinese queries → dictionary-page garbage (see pitfall below) |
| Sogou web search (www.sogou.com) | Sometimes | In testing returned a near-empty anti-bot page; weixin.sogou.com is the useful one |
| Sogou WeChat (weixin.sogou.com) | ✅ WeChat corpus | See section above |
| Direct site crawl | Depends | .edu.cn / .gov.cn often accessible with proper headers |

## 360 搜索 (so.com) — 中文统计/新闻数据调研首选

Tested workflow for "find the actual number" research (tourism stats, market data, policy figures).
**360 indexes and serves Chinese official/news content far better than Bing**, and the search page
HTML is parseable without CAPTCHA.

### How to Use

Ready-made script: `scripts/so360_search.py` (prints TITLE / LINK / SNIPPET per result).

```python
import urllib.parse, urllib.request, re
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0"
q = "云南省2024年接待游客 旅游总收入"
url = "https://www.so.com/s?q=" + urllib.parse.quote(q)
html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30).read().decode("utf-8","ignore")
# 每条结果是一个 <li class="res-list"> 块（列表以 <ul class="result"> 开头）
blocks = re.findall(r'<li class="res-list".*?(?=<li class="res-list"|</ul>)', html, re.DOTALL)
# 块内: 标题在 <h3> > <a href>；摘要通常在 class 含 desc/text-row/res-desc 的 <p> 里
```

### Pitfalls (实测)

1. **真实 URL 优先取 `data-mdurl` 属性** — 每条结果形如
   `<h3 class="res-title"><a data-mdurl="https://真实地址" href="https://www.so.com/link?m=...">`，
   直接取 `data-mdurl` 即可（2026-08 实测有效）。
2. **`so.com/link?m=` 跳转页可二次解析（另一实测路径）** — 若块里没有 `data-mdurl`，
   对跳转链接发普通 GET（带浏览器 UA）会返回 200 的小页面（约 200–300 字节），内含
   `<script>window.location.replace("https://真实URL")</script>`，正则提取即可拿到真实地址
   （2026-08 实测成功解析出 news.qq.com / m.ithome.com / tech.ifeng.com 等站链接）。
   个别情况下仍会 400/空页，此时退回用摘要。
3. **摘要即证据** — 360 摘要常直接含数字和来源（如"2025年1月18日 - 云南省人民政府门户网站: 2024年
   云南实现旅游总花费1.14万亿元"）。引用时用「标题 + 媒体/域名 + 日期 + 摘要数字」即可，标注"经搜索摘要核实"。
4. **查询词要带数字/机构名** — "云南省2024年接待游客 旅游总收入 亿" 这类带具体词元的查询效果好；
   纯话题词容易返回泛泛结果。
5. **请求间隔 ≥1s，每查询取 6–10 条** — 快速连发会被风控。
6. **搜索页 URL 里的 `src=related_middle_*` 块是广告/相关推荐，跳过**（标题为"XX官网"的广告块）。

### Bing 的坑 (cn.bing.com)

- 对中文话题性查询，Bing 会把查询词拆词后返回词典/百科页（搜"去年全省实现旅游花费1.27万亿元"
  返回的全是"去年"的词典释义）。**别用它做中文话题检索。**
- URL 必须带 `&mkt=zh-CN`（否则连页面标题都解析不对）；即使带上，多词长中文查询仍会拆词成
  垃圾结果（实测"小红书 蒲公英 商单 门槛 佣金 抽成"返回的全是"小"字头词典/小游戏页）。
- 若不得已要解析 Bing 结果：`<li class="b_algo">` 块内嵌了子 `<li>`（样式表注入），
  `.*?</li>` 正则会截断——必须按 `'<li class="b_algo"'` 分割再取块。
- 主要用途：已知精确标题/法规全名时搜直达 URL（Bing 结果给真实链接而非跳转）。
  **规范性文档名不会被拆词**：搜"人工智能生成合成内容标识办法""互联网信息服务深度合成管理规定"等
  法规全名，能直接命中 cac.gov.cn / gov.cn / openstd.samr.gov.cn 官方全文（2026-08 实测，
  含 GB 强制国标页）。中文平台政策调研用此法拿国家法规一手原文，再切 360 查平台落地细则。

### 数据归属与口径双检（重要！）

引用中文统计数据前必须做两道核查，本技能实际踩过坑：

1. **归属核查** — 搜索结果标题里的"我省/全市"可能指任何省份。案例：标题"2024年接待游客4.51亿人次
   旅游花费3452亿元我省文旅产业实现量质双升"看似云南，实为**甘肃**（同文案甘肃报道批量出现）。
   引用前用第二个查询（数字+候选地名）交叉验证数字属于哪个实体。
2. **统计口径核查** — 官方旅游/经济数据常有新旧口径并存（人次 vs 人数、含/不含一日游）。
   案例：云南 2024 游客量同时存在"7 亿人次"（文旅部门新口径）与"11.32 亿人次（前11月）"（旧口径）。
   报告里两个都列并标注口径，优先采用政府/文旅部门口径。

## Strategy for Chinese Content Research

1. **First pass**: 搜狗微信搜索 for WeChat articles (best signal/noise ratio)
2. **Second pass**: Direct site crawl with proper headers + delays
3. **PDF fallback**: Look for PDF attachments at predictable URL patterns
4. **Snippet synthesis**: Multiple search result snippets > one blocked full article
5. **User-assisted**: When all automated methods fail, give the user specific search terms to try manually
6. **平台政策/法规调研套路**（"某平台对 X 的规定 / 限流 / 真实案例"类问题）：
   - 国家法规全文 → Bing 精确法规名（见上，不拆词）；平台规则/公告 → 360 搜「平台名 + 关键词」。
   - 平台官方协议页（如小红书 /protocols/*）是 SPA 纯客户端渲染，原始 HTML 无正文
     （实测 745KB HTML 中"人工智能/标识/公约"等词 0 次命中）——直接放弃抓取，改用权威媒体
     （澎湃/解放日报/IT之家/海报新闻等）对官方账号公告的转述取证。
   - 报告结论分级标注可信度：官方原文/官方账号公告 > 权威媒体转述 > 自媒体推测/软文，逐条给来源+日期。
   - 已核实的官方源清单示例：`references/xiaohongshu-ai-policy-sources.md`（小红书 AI 内容政策，2026-08）。
