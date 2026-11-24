# 小红书 (Xiaohongshu) 爬取实战记录

小红书是国内反爬最严格的平台之一。以下是从实战中积累的可用技术和不可行路径。

## 反爬壁垒等级

| 层级 | 防御 | 难度 |
|:---|:---|---:|
| 🔴 L1 | JS 动态渲染内容 | 中 |
| 🔴 L2 | `__INITIAL_STATE__` 含 `undefined` 非标准 JSON | 低 |
| 🔴 L3 | 搜索 feeds 不在 SSR 中（必须调 API） | 中 |
| 🚫 L4 | API 请求需 `x-s`/`x-t` HMAC 签名 | 高 |
| 🚫 L5 | Cookie 需 `a1` + `web_session` 有效会话 | 高 |
| 🚫 L6 | WAF/反爬检测（封 IP/弹验证码） | 高 |

## 🔍 从 SSR HTML 提取数据

小红书 SSR 了页面框架和部分状态，**但搜索/笔记列表是通过后续 API 请求加载的**。

### 提取 `__INITIAL_STATE__`

```python
import re, json

m = re.search(r'window\.__INITIAL_STATE__=(.*?)</script>', html, re.DOTALL)
raw = m.group(1).strip()
```

### ⚠️ 关键陷阱：`undefined` 非标准 JSON

小红书 SSR 输出的 JSON 包含 JS 关键字 `undefined`（如 `"pwaAddDesktopPrompt":undefined`），标准 `json.loads()` 会报错。

**修复方法：** 在解析前替换

```python
raw = raw.replace(':undefined', ':null')
raw = re.sub(r'\bundefined\b', 'null', raw)
if raw.endswith(';'):
    raw = raw[:-1]

data = json.loads(raw)
```

### `__INITIAL_STATE__` 结构

成功解析后，顶层 keys 约 26 个：

```python
['global', 'user', 'board', 'UserFileStore', 'login', 'feed', 'layout',
 'aiAbExp', 'search', 'conversation', 'traceSourceStore', 'AiSugDataForChat',
 'activity', 'sportSearchOnebox', 'worldCup26', 'note', 'nioStore',
 'liveAbExp', 'redAbExp', 'chatData', 'groupData', 'redBadge', 'red',
 'liveList', 'notification']
```

### 搜索数据：**空的**

`search.feeds` 在 SSR 中始终为 `[]`。搜索结果是客户端通过以下 API 获取的：

```
POST https://edith.xiaohongshu.com/api/sns/web/v1/search/notes
```

该 API 需要：
- `x-s` / `x-t` 请求头（前端 JS 生成 HMAC 签名）
- Cookie: `a1` + `web_session`（登录态或匿名会话）
- `x-b3-traceid` 追踪 ID

**无有效签名时直接返回 `{"code":-101,"msg":"无登录信息，或登录信息为空"}`**，无法通过简单的 requests 调用绕过。

### 笔记详情页

`note.noteDetailMap` 同样为 `{}`。笔记内容也是通过 Ajax 加载的：
```
GET https://edith.xiaohongshu.com/api/sns/web/v1/feed
```

同样需要签名。

## ✅ 可行的替代方案

### 1️⃣ agent-browser（需先安装 agent-browser CLI + 浏览器）

```bash
# 0. 安装 agent-browser
npm install -g agent-browser

# 1a. 如果有 Chrome：下载浏览器
agent-browser install

# 1b. 如果没 Chrome，用系统自带的 Edge（Win11 自带）
# Edge 是 Chromium 内核，兼容 agent-browser
agent-browser open "https://www.xiaohongshu.com/search_result?keyword=考研" \
  --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 2. 等 JS 渲染完成
agent-browser wait --load networkidle

# 3. 查看页面快照（确认内容是否可见）
agent-browser snapshot

# 4. 获取渲染后的 HTML 或 __INITIAL_STATE__
agent-browser eval "document.documentElement.outerHTML"
agent-browser close
```

> ⚠️ 实测结果：agent-browser + Edge 可成功打开小红书页面，但搜索结果显示 **"登录后查看搜索结果"** ——即使是有头浏览器，未登录也无法看到内容。
>
> 💡 `JSON.stringify(window.__INITIAL_STATE__)` 会因循环引用报错。改为提取 `__INITIAL_STATE__.search` 子对象或直接取渲染后的 HTML 再解析。

### 2️⃣ 搜狗微信搜索（推荐，无需浏览器，已验证）

微信公众平台索引了大量公众号文章，其中不少引用了小红书内容。

**实测：搜索"小红书 目标院校戏剧管理考研"返回 10 条结果，无验证码，内容质量高。**

```python
import requests, re, urllib.parse

kw = '小红书 目标院校戏剧管理考研'
url = f'https://weixin.sogou.com/weixin?type=2&query={urllib.parse.quote(kw)}'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0'})

titles = re.findall(r'<h3>.*?<a[^>]*>(.*?)</a>.*?</h3>', r.text, re.I | re.DOTALL)
summaries = re.findall(r'class="txt-info"[^>]*>(.*?)</p>', r.text, re.I | re.DOTALL)
sources = re.findall(r'class="account"[^>]*>(.*?)</span>', r.text)

for t, s in zip(titles[:5], summaries[:5]):
    clean_t = re.sub(r'<[^>]+>', '', t).strip()
    clean_s = re.sub(r'<[^>]+>', '', s).strip()
    print(f'{clean_t}\n  {clean_s[:200]}\n')
```

> ⚠️ 搜狗搜索结果页可正常访问，但**点击文章链接**会触发反爬重定向到反爬页面。

### 3️⃣ 百度/Bing 搜索缓存

```python
bing_url = 'https://www.bing.com/search?q=' + urllib.parse.quote('site:xiaohongshu.com 关键词')
```

但搜索引擎缓存的 XHS 内容有限，只有标题+摘要片段。注：Bing **不索引** XHS 笔记详情页 URL，搜不到具体笔记链接。

### 4️⃣ 小红书开放平台 / 笔记 API

商业合作需申请小红书开放平台 API 权限（企业资质）。个人用户无此途径。

## 🆕 Playwright + Edge 登录方案（本次会话验证）

这是目前已知唯一能访问 XHS 搜索内容的技术路径。

### 前置条件
- Windows 11（自带 Edge 浏览器）
- `pip install playwright`
- 浏览器位置：`channel='msedge'` 自动发现

### 登录流程

```python
import asyncio
from playwright.async_api import async_playwright

async def login_and_scrape():
    p = await async_playwright().start()
    browser = await p.chromium.launch(channel='msedge', headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    # 打开登录页
    await page.goto('https://www.xiaohongshu.com/login', timeout=60000)
    await page.wait_for_timeout(3000)

    # 确认输入框存在
    inputs = await page.query_selector_all('input')
    # inputs[0].placeholder = '输入手机号' (type=text)
    # inputs[1].placeholder = '输入验证码' (type=number)
    await inputs[0].fill('手机号')

    # 点"获取验证码"
    for btn in await page.query_selector_all('button'):
        if '验证码' in await btn.inner_text():
            await btn.click()
            break

    # 等待用户提供验证码...

    # 登录成功后保存 cookies
    cookies = await context.cookies()
    # 用 cookies 做后续 API 调用

    # 提取认证后的搜索数据
    await page.goto('https://www.xiaohongshu.com/search_result?keyword=考研', timeout=30000)
    await page.wait_for_timeout(5000)

    # 安全地序列化 __INITIAL_STATE__（处理循环引用）
    data = await page.evaluate('''() => {
        const state = window.__INITIAL_STATE__;
        if (!state) return null;
        const seen = new WeakSet();
        return JSON.parse(JSON.stringify(state, (key, val) => {
            if (typeof val === 'object' && val !== null) {
                if (seen.has(val)) return '[Circular]';
                seen.add(val);
            }
            return val;
        }));
    }''')

    await browser.close()
    await p.stop()
```

### 注意事项
- `headless=False` 必须保持，XHS 会检测 headless 模式
- 登录后 Cookie 可持久化到文件（下次 `context.add_cookies()` 直接复用）
- **登录成功后，搜索数据在 DOM 中，不在 `__INITIAL_STATE__.search.feeds` 里**（feeds 始终为 `[]`）——通过 `document.body.innerText` 或 DOM 树提取可见文本
- `JSON.stringify()` 直接调 `__INITIAL_STATE__` 会因循环引用抛 `TypeError`，需要用 WeakSet 去重
- 登录页 title: `小红书 - 你的生活兴趣社区`
- **防封号建议**：不要短时间内多次搜索；搜索间隔至少 5 秒；单次采集不超过 2 页

## 浏览器安装位置：避开 C 盘

`agent-browser install` 默认把 Chromium 下载到 `C:\Users\<user>\.agent-browser\browsers`。

如需改到其他盘：

```bash
# 方案 1：Playwright 方式（验证可用）
$env:PLAYWRIGHT_BROWSERS_PATH = "E:\.agent-browser\browsers"
python -m playwright install chromium

# 方案 2：用系统 Edge 代替，完全不需额外下载
agent-browser open <url> --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```

## 实测结论

| 方法 | 结果 | 说明 |
|:---|:---:|:---|
| requests + BS4 | ❌ | 内容 JS 渲染，HTML 无数据 |
| `__INITIAL_STATE__` 解析 | ⚠️ | 有框架数据，但搜索 feeds 为空 |
| 直接调 API | ❌ 403 | 需要 HMAC 签名，无法绕过 |
| agent-browser + Edge (`--executable-path`) | ⚠️ | 页面可打开，但搜索需登录，不支持 headless 自动安装 |
| agent-browser + Chrome (`install`) | ❓ | 需先 `install` 下载 Chromium，可能被 headless 检测 |
| Playwright + Edge 登录 | ✅ **已验证** | 成功打开登录页，看到手机号+验证码输入框 |
| **搜狗微信搜索** | ✅ **已验证** | 搜到 10+ 条相关内容，无验证码 |
| 搜索引擎缓存 | ✅ 有限 | 标题+摘要片段，Bing 不索引 XHS 笔记链接 |
| 开放平台 API | ❌ | 需企业资质 |

## 经验教训

- XHS 搜索页的 SSR 虽然有 700KB+ HTML，但**数据承载量为零**——它是单页应用的空壳。
- 但 SSR 的 HTML 中确实嵌入了 24 个笔记 ID（`noteIds`）——这些 ID 可能是预加载的推荐内容，但实际数据仍需要 API 获取。
- 判断一个站能不能爬：看 `__INITIAL_STATE__` 或 `__NEXT_DATA__` 里是否包含实际数据列表。XHS 的 SSR 状态里 `search.feeds: []` 就是信号。
- JSON 中的 `undefined` 关键字是 XHS 特有的——其他用 Next.js 的站不会有这个问题。
- 搜狗微信搜索是中文内容爬取的"后门"：反爬远弱于百度/知乎/XHS，索引内容丰富。
- **Windows 上没装 Chrome 时**：用 Edge 代替，通过 `--executable-path` 指定路径。Edge 是 Chromium 内核，agent-browser 兼容。
- **浏览器下载位置**：`PLAYWRIGHT_BROWSERS_PATH` 环境变量可重定向浏览器安装路径到 E 盘或其他非 C 盘。
- **agent-browser 不兼容 headless 自动安装**：NPM 安装 CLI 后仍需手动 `agent-browser install` 下载浏览器，该操作在无 Chrome 的 Windows 上会失败。用 Playwright + Edge 可完全绕过这个问题。
