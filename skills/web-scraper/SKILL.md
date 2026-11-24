---
name: web-scraper
description: "Web scraping for Chinese and global sites — extract comments, reviews, articles, and structured data. Combines a turnkey CLI tool (web_scraper.py) with in-depth knowledge of Chinese-site anti-bot patterns, embedded JSON extraction, AJAX API discovery, proxy rotation, and agent-browser fallback. Use when the user asks to scrape, crawl, collect, or extract data from any website."
version: 1.3.0
author: Alice
metadata:
  hermes:
    tags: [web-scraping, proxy, crawler, chinese-sites, data-extraction, beautifulsoup]
    category: productivity
    related_skills: [agent-browser, ocr-and-documents]
platforms: [windows, linux, macos]
read_when:
  - User wants to scrape comments/reviews/articles from a website
  - User wants to collect data from listings, tables, or API endpoints
  - User needs to extract structured data from Chinese websites
  - User encounters anti-bot protections or JS-rendered content
---

# 🌐 Web Scraper — 中文网站评论/数据抓取

**两条腿走路：** 下方是即开即用的 CLI 命令行工具；后面是完整的中文站反爬知识库 + Python 代码片段。遇到简单页面用 CLI 一把梭，遇到反爬强的站翻知识库。

> 📖 **完整参考指南**: `~/.hermes/references/chinese-web-scraping-guide.md`（51KB，含 9 章节完整代码）
> 📚 **中文电子书获取（微信读书：匿名搜索 API + soldout 在架探测 + 加密 ID 提取 + DOM 分页翻页抓全文；QQ阅读/鸠摩/海外书站/读秀实测坑；豆瓣页做完整性基准）**: `references/chinese-ebook-sources.md`
> 📖 **中文剧本全文获取（旧 .doc→txt 转换 + 中华典藏网 diancangwang.cn 抓全文 + 水印/导航清洗 + 质量验证；实测《北京人》补全）**: `references/chinese-play-fulltext-fetch.md`；即用脚本 `scripts/diancangwang_fetch.py <目录URL> <输出.txt> [--verify 本地剧本]`（自动找分幕链接+清洗+可选台词比对）
> 🔎 **中文搜索矩阵（360搜索/Bing拆词坑/搜狗微信）**: `references/chinese-search-alternatives.md`；**360 搜索脚本**: `scripts/so360_search.py`；**小红书 AI 内容政策官方源清单（2026-08 核实）**: `references/xiaohongshu-ai-policy-sources.md`
> **可用库**: requests, httpx, beautifulsoup4, lxml (Python 3.12, Windows 11)；**playwright 可用**（`chromium.launch(channel='msedge', headless=True)` 直接用系统 Edge，无需下载 Chromium — 2026-09 实测批量渲染云厂商价格页全成功）
> **不可用**: selenium, scrapy, parsel
> **批量渲染脚本**: `scripts/render_pages_text.py`（喂一批 JS 渲染页 URL，输出每页 innerText.txt + 价格正则命中，见下方 5c 小节）
> **脚本位置**: `$HERMES_HOME/scripts/web_scraper.py`

---

## 🚀 快速上手（CLI 工具）

```bash
# 1️⃣ 提取评论数据
python web_scraper.py "https://example.com/reviews" \
  -c ".review-item" --author ".author" --content ".text" -f json

# 2️⃣ 智能自动检测页面结构
python web_scraper.py "https://example.com" --smart

# 3️⃣ 翻页采集（自动翻 3 页）
python web_scraper.py "https://example.com/list" \
  -c ".item" --paginate --max-pages 3 -f csv

# 4️⃣ 提取 CSS 选择器内容
python web_scraper.py "https://example.com" -s "article" -m text

# 5️⃣ 调用 JSON API
python web_scraper.py --api "https://api.example.com/data" \
  -H "Authorization: Bearer xxx" -o data.json
```

---

## 🛠️ CLI 工具参考

**脚本:** `~/.hermes/scripts/web_scraper.py`

```bash
python web_scraper.py <url> [选项]
```

### 提取模式

| 参数 | 说明 | 示例 |
|------|------|------|
| `-s <css>` | CSS 选择器 | `-s "div.comment"` |
| `-m <mode>` | 模式: text/html/attr/all/table/json | `-m all` |
| `-a <attr>` | 提取属性（attr 模式） | `-a src` |
| `--single` | 只取第一个匹配 | |
| `-f <fmt>` | 输出格式: json/jsonl/csv/markdown | `-f csv` |
| `-o <file>` | 保存到文件 | `-o data.json` |

### 评论/列表采集模式

```bash
python web_scraper.py <url> \
  -c ".container" \          # 容器选择器
  --author ".author" \       # 作者
  --content ".text" \        # 内容
  -d ".date" \               # 日期
  -r ".rating" \             # 评分
  --avatar "img.avatar" \    # 头像
  --link "a[href]"           # 链接
```

### 翻页 & 网络选项

| 参数 | 默认 | 说明 |
|------|------|------|
| `--paginate` | off | 启用自动翻页 |
| `--next <sel>` | `li.next a` | 下一页链接选择器 |
| `--max-pages N` | 5 | 最大翻页数 |
| `--delay N` | 1.0s | 请求间隔 |
| `--timeout N` | 30s | 超时 |
| `--retries N` | 3 | 重试次数 |
| `--cache` | off | 缓存 HTML（1 小时有效） |
| `--no-rotate-ua` | on | 禁用 UA 轮换 |
| `-H "Key: Val"` | — | 自定义请求头 |
| `--cookie "k=v"` | — | 自定义 Cookie |

### API 模式

```bash
python web_scraper.py --api <url> \
  --method POST \
  --param "page=1" \
  -H "Content-Type: application/json" \
  -o api_result.json
```

### 智能模式

```bash
# 自动检测：标题、正文、评论、链接、JSON-LD、OG元数据
python web_scraper.py <url> --smart
```

### 输出格式

| 格式 | 命令 | 用途 |
|------|------|------|
| JSON | `-f json` | 数据分析 |
| JSONL | `-f jsonl` | 流式/大数据 |
| CSV | `-f csv` | Excel/表格 |
| Markdown | `-f markdown` | 可读报告 |

> 💡 **实测验证:** CLI 工具已在 quotes.toscrape.com 通过测试——基础提取 10 条✅、评论结构化提取✅、翻页 2 页 20 条✅

---

## 📦 依赖安装

```bash
pip install requests beautifulsoup4 lxml
```

安装后即可使用 CLI 工具和下方所有 Python 代码片段。

---

## 🌏 Network Constraints

- Most foreign image hosts/sites are blocked: Tenor, Imgur, i.ibb.co, GitHub raw, httpbin.org
- Chinese sites (Baidu, CNKI, zhihu, chntheatre) work but have:
  - Heavy JS-based dynamic loading (content not in HTML)
  - WAF/anti-bot protections (422 errors, CAPTCHAs)
  - Need user-agent headers, sometimes cookies
  - Rate limiting - add delays between requests

## 🔄 Proxy Rotation

Script at `~/.hermes/scripts/proxy_rotator.py`:
```python
from proxy_rotator import ProxyRotator
rotator = ProxyRotator()
resp = rotator.request(url)  # auto-retry with different IP
```

---

## 🎯 Core Extraction Strategies (优先级从高到低)

### 1️⃣ 提取内嵌 JSON（首选）
许多中文站把数据嵌入 `<script>` 标签的 JS 变量中——这是最高效的方式。

**常见变量名**: `__INITIAL_STATE__` (知乎/B站), `__NEXT_DATA__` (Next.js), `__NUXT__` (Nuxt.js)

```python
import re, json

def extract_embedded_data(html):
    for pattern in [
        r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});',
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        r'window\.__NUXT__\s*=\s*(\{.*?\});',
    ]:
        m = re.search(pattern, html, re.DOTALL)
        if m:
            try: return json.loads(m.group(1))
            except: pass
    return {}
```

### 2️⃣ 发现并调用 AJAX API
前端用 fetch/axios 异步加载评论时，查找 API 端点直接调用。

```python
# 从 HTML 中发现 API 路径
api_urls = re.findall(r'["\'](/api/[^"\']*)["\']', html)
# 或 data-api 属性
data_apis = re.findall(r'data-api=["\']([^"\']+)["\']', html)
```

### 3️⃣ 直接解析 HTML（使用 BS4 + lxml）
```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, 'lxml')
# 常见中文网站类名模式
comments = []
for item in soup.select('.comment-item, .reply-item, [class*="comment"]'):
    content = item.select_one('.content, .text, .comment-content, [class*="content"]')
    author = item.select_one('.author, .username, .user-name, [class*="name"]')
    if content:
        comments.append({
            'content': content.get_text(strip=True),
            'author': author.get_text(strip=True) if author else '',
        })
```

### 4️⃣ agent-browser 回退（JS 渲染内容）

```python
import subprocess
def get_rendered_html(url):
    subprocess.run(['agent-browser', 'open', url], timeout=30)
    subprocess.run(['agent-browser', 'wait', '--load', 'networkidle'], timeout=15)
    r = subprocess.run(['agent-browser', 'eval', 'document.documentElement.outerHTML'],
                       capture_output=True, text=True, timeout=10)
    subprocess.run(['agent-browser', 'close'], timeout=5)
    return r.stdout
```

**取正文优先用 innerText 而非 outerHTML**：Docusaurus/文档站（DeepSeek 官方定价页等）正文都在 `main article` 里，`eval "document.querySelector('main article').innerText"` 一次拿全（含表格），比 outerHTML 省 token 且无标签噪音。实测：curl 抓 Docusaurus 站只有 ~22KB HTML 壳（正文 0 字），agent-browser 渲染后 innerText 全量可读（含脚注里的涨价公告）。抓更新日志/新闻列表同理，直接 `document.querySelector('main').innerText` 兜底。

**Windows 上没有 Chrome 怎么办？** 用系统自带的 Edge（Chromium 内核，完全兼容）：
```bash
# 先安装 agent-browser CLI
npm install -g agent-browser

# 用 --executable-path 指向 Edge（headless 模式同样必须带！）
agent-browser open <url> --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless
agent-browser wait --load networkidle
agent-browser eval "document.querySelector('main article').innerText"
agent-browser close
```

> ⚠️ **headless 模式必须带 `--executable-path`**（2026-08-17 实测）：只写 `--headless` 不带路径会报 `Auto-launch failed: Chrome not found`——agent-browser 自己的 cache、系统 Chrome、Puppeteer/Playwright 缓存全找不到，唯一出路是指定 Edge 路径。
> 📋 **不想 eval 时用 snapshot 直接读**：`agent-browser snapshot` 输出的 a11y 树自带全部渲染后文本（表格内容也在里面，每格一条 `cell "值"`），`Select-Object -Skip N -First M` 分页翻看即可，适合抓完整价格表/数据表，不用写 JS 选择器。注意 snapshot 输出量大时先 `Select-Object -First 100` 看结构再翻页。

> Edge 在 `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`（Windows 11 自带）。
> **PowerShell 传参坑**：`agent-browser eval` 的 JS 字符串里含 `@`（如 `@e80` ref）会被 PowerShell 当 splatting 解析——参数整体用双引号包住（`agent-browser click "@e80"`），或改用 CSS 选择器避免 `@`。`eval` 输出长文本时用 `Select-Object -First N` 截取即可。

### 5️⃣ Playwright + Edge 浏览器自动化（高反爬网站专用）

对于小红书这类全链路封锁（JS渲染+签名API+登录墙+WAF）的网站，最简单的请求方案是 Playwright + 系统自带 Edge：

```python
import asyncio, json
from playwright.async_api import async_playwright

async def scrape_xhs():
    p = await async_playwright().start()
    browser = await p.chromium.launch(channel='msedge', headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    
    # 复用已保存的 Cookie（免登录）
    import os
    if os.path.exists('xhs_cookies.json'):
        with open('xhs_cookies.json') as f:
            await context.add_cookies(json.load(f))
    
    # 打开搜索页，等 JS 渲染
    await page.goto('https://www.xiaohongshu.com/search_result?keyword=考研', 
                    timeout=60000, wait_until='domcontentloaded')
    try:
        await page.wait_for_load_state('networkidle', timeout=15000)
    except:
        pass
    await page.wait_for_timeout(5000)
    
    # 从 DOM 提取可见数据（__INITIAL_STATE__ 里的 feeds 是空的！）
    text = await page.evaluate('() => document.body.innerText')
    
    # 提取笔记 ID
    notes = await page.evaluate('''() => {
        const results = [];
        document.querySelectorAll('[data-note-id]').forEach(card => {
            const id = card.getAttribute('data-note-id');
            const title = card.querySelector('.title')?.textContent?.trim() || '';
            if (id && id.length === 24) results.push({id, title});
        });
        return results;
    }''')
    
    await browser.close()
    await p.stop()
```

**登录流程**（首次需手动收验证码）：
1. 打开 `https://www.xiaohongshu.com/login`
2. 点 `span.agree-icon` 勾选同意条款
3. 填写手机号到 `input[placeholder="输入手机号"]`
4. 点 `span.code-button.active` 发送验证码
5. 用户提供短信验证码后填入 `input[placeholder="输入验证码"]`
6. 点 `button.submit` 登录
7. 保存 Cookie 供下次复用

> 详见 `references/xiaohongshu-scraping-case-study.md` 的完整流程和 DOM 结构。
> 小红书**变现/运营信息调研**（无需登录爬虫，公开搜索即可）：`references/xiaohongshu-monetization.md`（官方渠道门槛/抽成、非官方玩法与封号风险、旅游类案例、瓶颈速查）。

### 5b️⃣ 搜狗微信搜索 → 公众号全文抓取（Playwright 点开跳转链接，实测 2026-08-31）

搜狗微信结果页（`weixin.sogou.com/weixin?type=2&query=…`）requests 能拿标题+摘要，但文章链接是 JS 加密跳转（`/link?url=dn9a_…`），requests 解不出真实 mp.weixin.qq.com URL，直接抓文章链接返回反爬页。**用 Playwright + Edge 渲染结果页，直接点结果标题，`expect_page` 捕获新标签，等 `#js_content` 渲染后 innerText 取全文**：

```python
items = await page.query_selector_all('ul.news-list > li')
title_el = await item.query_selector('h3 a')
async with context.expect_page(timeout=30000) as new_page_info:
    await title_el.click()
new_page = await new_page_info.value
await new_page.wait_for_load_state('domcontentloaded', timeout=30000)
await new_page.wait_for_timeout(4000)
content = await new_page.evaluate('() => document.querySelector("#js_content, .rich_media_content") ? document.querySelector("#js_content, .rich_media_content").innerText : document.body.innerText')
```

要点与坑：
- 先打印前 10 条标题再按关键词（如 '612'、'真题'、'书单'）定位点击，避免点错
- 部分账号已被屏蔽：正文返回"此账号已被屏蔽, 内容无法查看"（LEN≈70）——换下一条结果
- 图片排版文章正文极短（LEN≈80），只剩标题导航，需换源
- 每点一次间隔 2-3s，防搜狗风控；headless 也要 `channel='msedge'`
- 实测价值：抓到目标院校考研 612戏剧基础 2022/2024 全卷真题、全院科目书单等公众号长文（回忆版资料集）
- 同类坑：知乎专栏（zhuanlan.zhihu.com）requests 和 Playwright 均 40362 风控拒绝，B站专栏有验证码——这类直接放弃，换搜狗微信搜公众号版本

### 5c️⃣ 批量渲染抓取 JS 单页应用 / 云厂商价格页（Playwright + Edge，2026-09 实测）

云厂商（腾讯云/阿里云/华为云/京东云）的活动页、购买页、产品页、定价页**全是客户端渲染**——
curl 拿到的 HTML 里价格 **0 条**（例：`cloud.tencent.com/act/pro/lighthouse` 341KB HTML 全是壳，
渲染后才出「4核4G3M … 109 元/年」）。做法：

1. 用 `scripts/render_pages_text.py`（或抄它的逻辑）一次跑完一批 URL：每页存 `innerText` 纯文本
   + 正则 `\d+元/年|月` 命中预览 + `_summary.json`
2. 渲染要点：`chromium.launch(channel='msedge', headless=True)`（系统 Edge 免下载）+ `locale='zh-CN'`
   + `wait_until='domcontentloaded'` 后 `wait_for_timeout(5000~8000)`
   + `page.mouse.wheel(0, 3000)` 触发懒加载卡片
3. **拿到 txt 再用 Python 正则切「规格 / 时长 / 活动价 / 日常价」**，比在 HTML 上抠 DOM 稳得多；
   注意「活动价：\n109\n元\n日常价：780元」这类换行断裂，`re.sub(r'\s+',' ')` 归一化后再解析
4. **坑：登录后才显示的价格渲染成「询价中」或 ███ 方块占位**（阿里云轻量购买页即如此）。
   这类只能引用活动页口径（如「38元/年起」）并**如实标注"具体套餐价需登录查看"——不要编数字**
5. **坑：页面里的"解决方案/推荐"卡片链接也是 JS 渲染的**，静态 HTML 里搜 `deepseek`/`hermes` 0 命中。
   → 用**厂商站内搜索**：`https://www.aliyun.com/search?q=<关键词>` 渲染后取 `<a href>`，
   就能拿到 `aliyun.com/solution/tech-solution/...` 这类官方方案页 URL

> ⚠️ **搜索引擎选型（2026-09 实测）**：查国内厂商页面时，Bing（`cn.bing.com/search?q=`）对**长中文查询会退化成
> "只认第一个词"的垃圾结果**（换 query 结果不变，全是泛化的品牌页）；DuckDuckGo html 端点
> （`html.duckduckgo.com/html/?q=`）在国内网络**直接超时**。
> **优先顺序：厂商站内搜索 > 360 搜索（`scripts/so360_search.py`）> 搜狗微信**，Bing 只作最后兜底。

### 5d️⃣ 批量查企业工商/舆情（2026-11 实测，124家公司实战）

做批量公司背调时，搜索引擎被限流是首要障碍。实测各源「连续可用请求数」排序：

| 源 | 耐用度 | 用法 |
|:--|:--|:--|
| **头条搜索** `so.toutiao.com/search?keyword=` | ★★★★★ 连抓 80+ 家未封 | 摘要里就有启信宝/企知道/爱企查的成立日期+注册资本，还带 BOSS/智联岗位与中标记录，最适合「招聘+待遇+舆情」 |
| 神马/夸克 `m.sm.cn/s?q=` | ★★★ 约 30-40 次 | 首屏是水滴信用企业卡片（成立日期/注册资本/地址/经营范围），最适合「工商核验」 |
| 360 `www.so.com/s?q=` | ★★ 约 150 次后封 IP | 桌面版封禁后换 iPhone UA 请求 `m.so.com/s?q=` 还能撑一段（选择器 `div.res-list`，标题 `h3.res-title`，真实 URL 在 `data-pcurl`），彻底封了要等 30-60 分钟 |
| 搜狗 `www.sogou.com/web?query=` | ★★ 约 60 次 | 优点：用**引号把公司全名包起来**查询，首条就是企查查卡片（成立/注册资本/状态/经营范围）；长查询词会退化成垃圾结果 |
| 天眼查 `www.tianyancha.com/search?key=` | ★★ 约 3 次！ | 最脆但数据最好：搜索页与详情页都能直接解析 `script#__NEXT_DATA__`，搜索命中在 `props.pageProps.listRes.data.companyList[]`（含 name/legalPersonName/estiblishTime/regCapital/regStatus/creditCode/businessScope/regLocation），详情页正文含「员工人数 N 人 (2025年)」「自身风险/历史风险/预警提醒/司法案件」计数。3 次后服务端只回 22KB 骨架页，Playwright 渲染出来就是「扫码登录」墙 |

其它踩坑：
- Bing（`cn.bing.com`）对自动化请求会返回**固定缓存页**：换 5 个不同 query 结果一模一样，全部是无关键词的通用结果 → 不可用于中文企业查询。百度直接 1488 字节验证码页。
- `11467.com`（顺企网）、`qcc.com`、`aiqicha.baidu.com` 直接请求会被 403/429 或返回加密 arg1 反爬脚本。
- 本地脚本文件名别叫 `inspect.py`、`json.py`——会遮蔽标准库，导致 bs4 导入报 `module 'inspect' has no attribute 'signature'`。
- 批量跑：单进程 2 线程 + 每家间隔 1-2s 是甜点；一开始 3 查询/家 × 124 家会在第 50 家左右触发全网封禁，改「每家 1-2 个高价值查询 + 分引擎轮换」更稳。

### 6️⃣ 微信读书网页版全文抓取（图书全文 txt 入库）

用户要"找某本书电子版/抓全文"时，微信读书是**正版在架书的最优源**（比网传扫描 PDF 干净）。完整配方见 `references/chinese-ebook-sources.md`，核心要点：

- **登录**：Playwright + Edge（headless），首页点"登录"→ 用户扫码 → 等 `wr_vid`+`wr_skey` cookie 存 json 复用。**用户偏好：先查电脑微信（Weixin 进程）是否已登录，已登录则网页登录点"允许外部应用"授权免扫码**
- **加密 ID 陷阱**：网页 URL（`/web/reader/<enc>`）用 deepLink 里的 `v=` 加密 ID，数字 bookId 拼 URL 必 404；加密 ID 从搜索 API `/web/search/global?keyword=X` 的 `bookInfo.deepLink` 提取（匿名可调）
- **先探测 soldout**：`bookInfo.soldout`（0=在架 1=下架）；下架书（谭霈生《戏剧本体论》、曹禺四部曲、《等待戈多》等）登录也没用，别浪费扫码
- **⚠️ 正文是 canvas 渲染——DOM 提取拿不到正文**：`.readerChapterContent_container` 的 innerText 只有章名/UI 文字（如"第一场…"），翻页后 DOM 文本不变；页面有 2 个 `canvas`（约 393×590），正文画在 canvas 里。**抓正文 = canvas 元素截图 + RapidOCR 识别**（实测质量好，《哈姆雷特》正文识别流畅）。翻页本身有效（canvas 内容在变），别被"DOM 文本不变"误导判成翻页失败
- **别逆向接口**：chapterInfos/chapter/content 等接口 2026-08 实测全 404（页面 JS 内部签名）；翻页按钮 `.renderTarget_pager_button` **必须 force=True 点击**（`.wr_mask` 透明遮罩拦截普通 click），点击后轮询等 canvas 内容变化，OCR 结果过滤 UI 噪声（上一页/下一页/点击添加书签），书末检测"标记读完"，付费墙检测 OCR 文本含"开通会员/立即购买"
- **单书卡死就换书/换版本**（实测《茶馆》人文社版卡章名页，其他在架版本正常）
- 批量抓带断点续抓（state json），每本间隔 3s，后台跑
- 搜索匹配是文本相似非精确书目（搜"雷雨"命中奥斯特洛夫斯基而非曹禺），必须核对 author

---

## 🚧 Anti-Scraping Patterns (Chinese Sites)

### Common Defenses
- **Baidu**: Returns CAPTCHA/security verification page (1488 bytes) for non-browser requests. No workaround via simple headers — need real browser session cookies.
- **Zhihu**: Returns HTTP 403 for automated requests. No easy bypass.
- **搜狗微信**: 结果页标题+摘要 requests 可拿；**文章全文走 5b 小节 Playwright 点击法**（旧结论"文章链接不可访问"已过时，2026-08-31 实测可抓全文）。
- **Xiaohongshu**: Web version heavily restricted. SSR has __INITIAL_STATE__ but search feeds are empty — results loaded via signed API. See `references/xiaohongshu-scraping.md` for full patterns and alternatives.
- **WAF gateways**: Many .edu.cn sites use CloudFlare-like WAF (websaas.cn) returning HTTP 422.

### What Works
1. **Search engine snippets**: Even when full article is blocked, search result snippets (title + 2-line abstract) often contain enough signal.
2. **搜狗微信搜索 (Sogou WeChat Search)**: Best alternative when Baidu/Zhihu block — search result page is accessible without CAPTCHA. See `references/chinese-search-alternatives.md` for the full technique.
3. **Paginated URL patterns**: Discover site pagination patterns (e.g. `/p/2.html`, `?page=2`) — the first page's HTML may have the pagination links even if content is JS-loaded.
4. **PDF fallback**: Many `.edu.cn` sites offer PDF versions at `/Uploads/...` paths. Even if the HTML has no text, the PDF link may exist.
5. **Multiple search engines**: 中文调研首选 360 搜索 (so.com) → 搜狗微信搜索 → Bing 兜底。Baidu 首 1-2 次查询后即退化为垃圾结果/验证码，别用于多查询研究。完整工作流：`scripts/so360_search.py`（检索，摘要即证据）→ `scripts/fetch_text.py`（抓文章全文核验）→ 多源交叉验证，详见 `references/chinese-search-alternatives.md`。
6. **Site navigation HTML**: Even JS-heavy sites often include the navigation menu and section IDs in the initial HTML — use those to understand site structure.
7. **360 搜索 (so.com) — 中文统计/新闻/平台政策调研首选**: 搜索结果摘要直接含关键数字与来源，且页面无验证码可解析。真实 URL 优先取 `<a data-mdurl>` 属性；无 `data-mdurl` 时 `so.com/link?m=` 跳转页对 requests 返回 200 并含 `window.location.replace("真实URL")`，正则提取即可（2026-08 实测成功解析出 news.qq.com / m.ithome.com / tech.ifeng.com 等真实链接）。即用脚本 `scripts/so360_search.py`，完整工作流见 `references/chinese-search-alternatives.md`（含 Bing 中文查询拆词坑、数据归属与统计口径双检）。

### What Does NOT Work
- Requests without browser-like headers → blocked
- Too many requests in quick succession → rate-limited or IP-banned
- Direct requests to article links from search engines → anti-bot triggered
- Foreign-hosted image CDNs (Tenor, Imgur) → connection reset in China network

### CNKI / University Sites
- Content often loaded via AJAX tabs (not in initial HTML)
- Use BS4/regex on the admission.html pages, find section IDs like `admission2`
- PDF attachments are at `/Uploads/...` paths
- Full-text papers require institutional VPN/CARSI auth, cannot be scraped
- Some PDFs are scanned images (not text) — need OCR (pytesseract or similar) to extract

### Chntheatre.edu.cn (Central Academy of Drama)
- Main site: `https://example.edu.cn/cn/index`
- Navigation uses `/cn/admission.html` → sections: admission1~6
- Master's page: `/cn/recruit/shuoshi.html` (JS-loaded content)
- Detail pages: `/cn/recruit/shuoshi/detail/{id}.html`
- Pagination: `/cn/recruit/shuoshi/p/{n}.html`
- PDF files: `https://example.edu.cn/Uploads/...`
- Graduate contact: yjsb1@example.edu.cn, +8610 56620342

### When HTML content is empty (JS-rendered)
1. Try direct URL patterns based on site structure
2. Look for PDF versions of the content
3. Extract from Google/Baidu cache
4. Use the page search API if exposed
5. Fall back: tell user the URL and let them open in browser

---

## 📄 Pagination Patterns 分页处理

| 模式 | 示例 | 处理方法 |
|------|------|---------|
| URL 参数 | `?page=2`, `?p=3`, `?start=20` | 循环递增参数 |
| 路径分页 | `/page/2/`, `/p2.html` | 替换路径中的 `{page}` |
| Cursor 分页 | `?cursor=xxx` (API) | 从响应中提取 next_cursor |
| "加载更多" 按钮 | 点击触发 AJAX | 查找并调用 API 端点 |
| 无限滚动 | 滚动触发加载 | 使用 agent-browser 滚动 |

CLI 翻页：
```bash
# 自动找 "下一页" 链接翻页
python web_scraper.py <url> -c ".item" --paginate --max-pages 10

# 自定义下一页选择器
python web_scraper.py <url> -s "a" -m text --paginate --next "li.next a"
```

---

## 🛡️ Anti-Scraping Countermeasures

### User-Agent 轮换
使用 Chrome/Edge/微信浏览器 UA 轮换，每次请求更换：
```python
import random
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/131.0.0.0',
    'Mozilla/5.0 (Linux; Android 14) MicroMessenger/8.0.50',  # 微信浏览器
]
```

CLI 工具默认已启用 UA 轮换：
```bash
# 禁用（如需要固定 UA）
python web_scraper.py <url> -s "h1" --no-rotate-ua
```

### 请求延迟
- 知乎/B站/豆瓣: 1-2s
- 百度/微博: 3-5s (严格)
- 普通站: 0.5-1.5s
- 使用随机抖动: ±0.5s
- 错误时指数退避: delay × 2^attempt

CLI 调整延迟：
```bash
python web_scraper.py <url> -s "h1" --delay 2.5
```

### Cookie 管理
- 使用 `requests.Session()` 自动管理 cookies
- 部分站（知乎、B站）需要 Cookie 才能访问
- 从浏览器导出 Cookie 后导入到会话

CLI 传 Cookie：
```bash
python web_scraper.py <url> --cookie "sessionid=abc123" --cookie "token=xyz"
```

### 代理支持
- 环境变量 `HTTP_PROXY`/`HTTPS_PROXY`
- 配置文件 `~/.hermes/scripts/proxies.txt` (每行一个 proxy)
- 或使用 `proxy_rotator.py` 自动轮换

---

## 🔍 CSS Selector vs XPath 指导

| 场景 | 推荐 | 原因 |
|------|------|------|
| 按类名/属性选择 | CSS | `soup.select('.comment .content')` |
| 按文本内容匹配 | XPath (lxml) | `//div[contains(text(),'评论')]` |
| 按位置选择 | XPath | `(//div[@class='comment'])[3]` |
| 简单结构化提取 | CSS | 可读性更好 |
| 处理哈希类名 | CSS 属性匹配 | `[class*="comment"]`, `[class^="_"]` |

---

## ⚠️ Error Handling

```python
def safe_request(url, session, retries=3):
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=30)
            if resp.status_code == 429:
                time.sleep(5 * (2 ** attempt))  # 指数退避
                continue
            if resp.status_code in (403, 503):
                raise AntiBotError(f"Anti-bot at {url}")
            resp.raise_for_status()
            # 检查是否返回了 CAPTCHA 页面
            if len(resp.text) < 2000 and '验证' in resp.text:
                raise AntiBotError(f"CAPTCHA at {url}")
            return resp
        except (requests.Timeout, requests.ConnectionError) as e:
            if attempt == retries - 1: raise
            time.sleep(2 ** attempt)
```

CLI 工具已内置重试：
```bash
python web_scraper.py <url> --retries 5 --timeout 60
```

---

## 🏷️ 常见中文站评论选择器参考

| 网站 | 评论容器 | 内容选择器 |
|------|---------|-----------|
| 豆瓣电影 | `.comment-item` | `.comment-content` |
| 知乎 | `.AnswerItem` | `.RichText` |
| B站 | `.reply-item` | `.reply-content` |
| 淘宝 | `.review-item` | `.review-content` |
| 微博 | `.comment-wrap` | `.comment-text` |
| 大众点评 | `.comment-item` | `.desc` |
| 贴吧 | `.post_item` | `.post_content` |

> ⚠️ 类名因网站改版会变化。许多现代中文站使用 CSS Modules (哈希类名如 `_3tC4x`)，此时应使用属性选择器 `[class*="comment"]` 或按 DOM 结构定位。

### CLI 实战：豆瓣电影评论
```bash
python web_scraper.py "https://movie.douban.com/subject/xxx/comments" \
  -c ".comment-item" \
  --author ".comment-info a" \
  --content ".comment-content" \
  -d ".comment-time" \
  -r ".rating" \
  --paginate --max-pages 3 \
  -f csv -o douban_comments.csv
```

### CLI 实战：B站评论
```bash
python web_scraper.py "https://www.bilibili.com/video/BVxxx" \
  -c ".reply-item" \
  --author ".user-name" \
  --content ".reply-content" \
  -d ".reply-time" \
  --paginate --max-pages 2 \
  -f json -o bilibili_replies.json
```

---

## ⚠️ 关键陷阱

### 陷阱 1：JS `undefined` → JSON 解析失败

许多中国网站（小红书、知乎等）的 SSR JSON 中包含 JS 特有的 `undefined` 关键字，标准 `json.loads()` 会报错。

**修复方法：** 解析前替换
```python
raw = raw.replace(':undefined', ':null')
raw = re.sub(r'\\bundefined\\b', 'null', raw)
if raw.endswith(';'):
    raw = raw[:-1]
data = json.loads(raw)
```

### 陷阱 2：`JSON.stringify()` 循环引用（Playwright 提取失败）

通过 Playwright 提取 `__INITIAL_STATE__` 时：
```javascript
// ❌ 会报错：Converting circular structure to JSON
await page.evaluate('() => JSON.stringify(window.__INITIAL_STATE__)')
```

Vuex/Redux 状态树包含循环引用（`dep` → `sub` → `computed` 环），无法直接序列化。

**修复方法：** 用 HTML 正则提取代替 JS evaluate
```python
# ✅ 从渲染后的 HTML 正则提取（文本，无循环引用）
html = await page.content()
m = re.search(r'window\.__INITIAL_STATE__=(.*?)</script>', html, re.DOTALL)
raw = m.group(1).replace(':undefined', ':null')
data = json.loads(raw)
```

### 陷阱 3：SSR 数据 vs CSR 数据——不在同一个地方

对于重度客户端渲染的网站（小红书等），`__INITIAL_STATE__` 在**服务端渲染的 HTML** 和**客户端执行后**的行为不同：

| 阶段 | `__INITIAL_STATE__` | DOM |
|:---|:---|:---|
| 初始 HTML（SSR） | 有 shell 配置，但 `feeds: []` 空 | 登录墙/骨架屏 |
| JS 渲染后（CSR） | **仍为空** — 数据不在 JSON 里！ | 实际内容渲染到 DOM |

**关键结论：** 对于 CSR 重站点，**不要依赖 `__INITIAL_STATE__`** 中的数据字段。改为：
1. 用 Playwright 等 JS 到渲染
2. 从 DOM 提取：`page.evaluate('() => document.body.innerText')` 或特定 DOM 选择器
3. 小红书特定技巧：从 `[data-note-id]` 属性提取笔记数据（24位 hex ID）

```python
# ✅ 正确方式：从渲染后的 DOM 提取
notes = await page.evaluate('''() => {
    const results = [];
    document.querySelectorAll('[data-note-id]').forEach(card => {
        const id = card.getAttribute('data-note-id');
        const title = (card.querySelector('.title, [class*="title"]') || card).textContent?.trim() || '';
        if (id && id.length === 24) results.push({id, title});
    });
    return results;
}''')
```

### 陷阱 4：Windows PowerShell 下不要用 `python -c "..."` 内联跑含引号/正则的代码

PowerShell 5.1 会对 `-c` 后的内容做引号/括号/`<`/`>` 的二次解析，内联 Python 一旦带正则或字典字面量几乎必挂
（报 ParserError / MissingTypename / 字符串缺少终止符）。**先 write_file 写成 .py 脚本文件再运行**，
这是本环境的标准姿势——也便于复用和调试。示例见 `scripts/so360_search.py`。

## 🧘 Ethical Scraping — 安全第一，不被封号

- **间隔控制**：请求间隔 3-5 秒（高风险站 5-10 秒），模拟人类操作节奏
- **量级控制**：单次最多爬 2-3 页，不要批量刷数据
- **行为模拟**：随机等待、滚动行为、不并发请求、不频繁登录登出
- **尊重边界**：不爬登录墙后内容、遵守 robots.txt、不撞反爬 CAPTCHA
- **账号安全**：爬取已登录网站时尤其小心——频率过高会导致账号被风控
- ⚠️ 小红书特别提醒：搜索页面需登录且内容通过 JS 异步加载。爬取后需等待 `networkidle` 再提取。不要在短时间内多次搜索，容易被封号
- CNKI full-text requires institutional access (VPN/CARSI)

---

## 🔄 Quick Reference: `detect` → `scrape` workflow

```python
# 1. 探测页面结构
$ python -c "
import re, json, requests
r = requests.get('URL', headers={'User-Agent':'...'})
apis = re.findall(r'[\"\'](/api/[^\"\']*)[\"\']', r.text)
print('APIs found:', apis[:5])
print('Has __INITIAL_STATE__:', '__INITIAL_STATE__' in r.text)
"

# 2. 用 CLI 快速提取
$ python web_scraper.py <url> -c ".comment-item" --author ".author" -f json
```

## 📋 Verification Checklist

- [ ] CLI 工具可运行: `python web_scraper.py --help`
- [ ] 基础提取测试: `python web_scraper.py https://example.com -s "h1" -m text`
- [ ] 评论模式测试通过（至少一个真实网站）
- [ ] 翻页功能跨 2 页测试通过
- [ ] 输出 JSON 可解析
- [ ] 已安装依赖: `pip install requests beautifulsoup4 lxml`
- [ ] 中文站反爬策略已了解（内嵌 JSON > AJAX API > BS4 > agent-browser）
