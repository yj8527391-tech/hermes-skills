---
name: xiaohongshu-scraper
description: "小red薯爬爬（小红书爬取）：Scrape Xiaohongshu (小红书) search results with Playwright, auto-detecting the user's default browser (Chrome/Edge/Firefox). Handles login-with-SMS flow, saves cookies for reuse, extracts JS-rendered content from DOM, and outputs formatted Excel. Use when the user wants to search or collect data from Xiaohongshu."
version: 1.0.4
author: xhs-scraper
metadata:
  hermes:
    tags: [xiaohongshu, scraper, login, playwright, edge, social-media]
    category: data-science
    related_skills: [web-scraper, agent-browser]
platforms: [windows]
read_when:
  - User wants to search or scrape Xiaohongshu (小红书)
  - User needs data from XHS search results
  - User wants to collect XHS notes/comments for exam prep or research
---

# 📕 小red薯爬爬 — 小红书爬取攻略（Playwright + 默认浏览器 + 短信登录）

## 核心套路

```
① Playwright + 用户默认浏览器（自动检测 Chrome/Edge/Firefox）→ 打开登录页
② 勾选同意条款 → 填手机号 → 点发送验证码
③ 用户收到短信 → 把验证码发给我（**1 分钟内**完成，超时自动跳转检查）
④ 填入验证码 → 点击登录 → 等待 JS 渲染
⑤ 从 DOM 提取笔记标题 + data-note-id → 拼接链接
⑥ 按优先级排序 → 生成带链接/热评/总结的 Excel
```

## 🧑🤝🧑 人工 / 自动 分工表（使用前必读）

| 环节 | 谁来做 | 说明 |
|---|---|---|
| 安装依赖 | 👤 人工（一次性） | `pip install playwright openpyxl`；macOS/Linux 另加 `playwright install chromium` |
| 启动浏览器 | 🤖 自动 | 自动检测默认浏览器（Windows 读注册表 / 其他平台内置 Chromium） |
| 打开登录页 | 🤖 自动 | 加载 `xiaohongshu.com/login` |
| 勾选同意条款 | 🤖 自动 | 点击 `span.agree-icon` |
| 填写手机号 | 🤖 自动 | 填入人工提供的号码（运行时输入或 `XHS_PHONE` 环境变量） |
| 发送验证码 | 🤖 自动 | 点击 `span.code-button.active` |
| **接收短信验证码** | 👤 **人工（关键步骤）** | 用户查收短信，把 6 位验证码告知 Agent / 设 `XHS_CODE`。**限时 1 分钟**，超时自动跳转搜索页检查登录状态；也可直接在浏览器窗口手动填写 |
| 输入验证码 + 登录 | 🤖 自动 | 填入后点击登录按钮 |
| 保存 Cookie | 🤖 自动 | 存到 `~/.xhs_cookies.json`（可用 `XHS_COOKIE_PATH` 改路径），下次免登录 |
| 确认搜索关键词 | 👤 人工 + 🤖 自动 | Agent 先按用户画像给 2-3 个候选，**用户确认后才搜** |
| 打开搜索页 + 等渲染 | 🤖 自动 | 等 JS 渲染约 5 秒 |
| 提取笔记数据 | 🤖 自动 | 从 DOM 提取 `data-note-id` + 标题 |
| 生成结果文件 | 🤖 自动 | 输出 `xhs_results.json` / Excel |
| 收尾清理 | 🤖 自动 + 👤 手动 | 脚本自动关浏览器；进程残留时手动 `taskkill` / `killall` |

### 🤖 Agent 操作指引（引导访问时按此执行）

1. **动手前**：告诉用户「本技能会打开你的浏览器并自动操作，请盯一下屏幕」，并说明哪些环节需要用户参与（收验证码、确认关键词）。
2. **手机号**：运行时询问用户输入，不要假设/硬编码。
3. **验证码环节**：点击发送后**立即停下来等用户**，并明确告知「请在 1 分钟内完成验证码填写与登录」；超时后自动跳转搜索页检查登录状态，未登录则提示用户手动操作或重试。不要反复重试发送。
4. **关键词环节**：根据用户画像（职业/兴趣/目标）给出候选关键词让用户选，用户确认后才执行搜索。
5. **过程透明**：每完成一步打印 ✅ 状态，让用户知道进行到哪；报错时引导用户看浏览器窗口或日志。
6. **爬取要温柔**：请求间隔 ≥3 秒，单次会话不超过 2-3 页，不频繁登录（账号风控会拉黑）。

## 前置条件

```powershell
# Windows
pip install playwright openpyxl
$env:PLAYWRIGHT_BROWSERS_PATH = "E:\.agent-browser\browsers"  # 不占 C 盘
```
```bash
# macOS / Linux
pip install playwright openpyxl
playwright install chromium   # 非 Windows 平台用 Playwright 内置 Chromium
export PLAYWRIGHT_BROWSERS_PATH="$HOME/.cache/ms-playwright"  # 可选
```

浏览器：**自动检测用户默认浏览器**——Windows 读注册表 UserChoice（Chrome / Edge / Firefox 均可）；macOS/Linux 用 Playwright 内置 Chromium（最稳）。都可用 `XHS_BROWSER=chrome|edge|firefox` 环境变量强制指定。

---

## 🚀 完整流程

### Step 1: 输入手机号 + 打开登录页 + 勾条款 + 发验证码

```python
import asyncio
from playwright.async_api import async_playwright

PHONE = input('📱 请输入手机号: ').strip()  # ← 运行时会提示输入

async def login_step1():
    p = await async_playwright().start()
    browser = await launch_browser(p)  # 自动检测默认浏览器，失败回退 Edge
    page = await browser.new_page(viewport={'width': 1280, 'height': 800})
    
    await page.goto('https://www.xiaohongshu.com/login', timeout=60000, wait_until='domcontentloaded')
    await page.wait_for_timeout(2000)
    
    # 勾选同意
    agree = await page.query_selector('span.agree-icon')
    if agree: await agree.click()
    
    await page.wait_for_timeout(300)
    
    # 填手机号
    phone_input = await page.query_selector('input[placeholder="输入手机号"]')
    if phone_input:
        await phone_input.click()
        await phone_input.fill(PHONE)
    
    await page.wait_for_timeout(500)
    
    # 点获取验证码
    code_btn = await page.query_selector('span.code-button.active')
    if code_btn:
        await code_btn.click()
        print('✅ 验证码已发送！请查收手机短信')
    
    return browser, page  # 保持浏览器打开
```

**关键选择器：**
- 同意条款：`span.agree-icon`（自定义样式，非 checkbox）
- 手机号输入：`input[placeholder="输入手机号"]`
- 验证码按钮：`span.code-button.active`
- 验证码输入：`input[placeholder="输入验证码"]`
- 登录按钮：`button.submit`

### Step 2: 填入验证码 + 登录

```python
async def login_step2(page, code):
    code_input = await page.query_selector('input[placeholder="输入验证码"]')
    if code_input:
        await code_input.fill(code)
    
    await page.wait_for_timeout(800)
    
    login_btn = await page.query_selector('button.submit')
    if login_btn:
        await login_btn.click()
        print('✅ 已点击登录')
    
    await page.wait_for_timeout(5000)  # 等登录完成
```

### Step 3: 保存 Cookie（下次免登录）

```python
async def save_cookies(context):
    cookies = await context.cookies()
    cookie_path = os.environ.get('XHS_COOKIE_PATH', os.path.expanduser('~/.xhs_cookies.json'))
    with open(cookie_path, 'w') as f:
        json.dump(cookies, f, ensure_ascii=False)
    print(f'✅ Cookie 已保存: {cookie_path}')
```

### Step 4: 加载 Cookie + 搜索

```python
async def search_with_cookies(context, keyword=''):  # 无默认词，由用户画像/输入决定
    page = await context.new_page()
    await page.goto(f'https://www.xiaohongshu.com/search_result?keyword={keyword}', 
                   timeout=60000, wait_until='domcontentloaded')
    
    # 等 JS 渲染完
    try:
        await page.wait_for_load_state('networkidle', timeout=15000)
    except:
        pass
    await page.wait_for_timeout(5000)  # 关键等待！
    
    # 从 DOM 提取笔记数据
    notes = await page.evaluate('''() => {
        const results = [];
        const seen = new Set();
        const cards = document.querySelectorAll('[data-note-id]');
        cards.forEach(card => {
            const noteId = card.getAttribute('data-note-id');
            if (!noteId || noteId.length !== 24 || seen.has(noteId)) return;
            seen.add(noteId);
            const title = (card.querySelector('.title, [class*="title"], h3, h4') || card).textContent?.trim() || '';
            results.push({ id: noteId, title: title.substring(0, 100) });
        });
        return results;
    }''')
    
    return notes
```

### Step 5: 生成 Excel（含总结 + 热评 + 链接）

```python
from openpyxl import Workbook
from openpyxl.styles import PatternFill

def export_excel(notes, path='xhs_results.xlsx'):
    wb = Workbook(); ws = wb.active; ws.title = '笔记数据'
    ws.append(['序号', '标题', '链接'])
    for i, n in enumerate(notes, 1):
        ws.append([i, n['title'], f'https://www.xiaohongshu.com/explore/{n["id"]}'])
    wb.save(path)
    print(f'✅ Excel 已生成: {path}')
```

## ⚠️ 关键坑点

| 坑 | 解决 |
|:---|:---|
| **CSS选择器复杂** | `.agree-icon` 不是 checkbox，是自定义 span；`span.code-button.active` 需精准定位 |
| **验证码每次不同** | 无法自动化！必须用户手动收短信并告知 |
| **JS 渲染延迟** | 登录后搜索页数据不在 HTML 里！必须 `wait_for_timeout(5000)` 等客户端渲染 |
| **feeds 永远是空** | `__INITIAL_STATE__.search.feeds` 不会自动填充，数据在 DOM 里 |
| **JSON 循环引用** | 无法 `JSON.stringify(window.__INITIAL_STATE__)`，须逐级提取或从 HTML 正则提取 |
| **Cookie 有时效** | 保存后短期内可用，但过几天或登出后失效，需重新登录 |
| **反爬全家桶** | JS渲染 + 签名API + 登录墙 + WAF + DOM加密，是最高难度级别 |
| **浏览器进程残留** | Windows 跑完 `taskkill /f /im msedge.exe`（或 chrome.exe/firefox.exe）；macOS 用 `killall "Google Chrome"` 等 |

## ✅ 分享前安全检查清单

每次分享/发布 skill 前，逐项检查：

- [ ] 🔒 **手机号** → 用 `input()` 替代硬编码
- [ ] 🔒 **本地路径** → 用 `os.path.expanduser()` 替代 `C:\Users\xxx`
- [ ] 🔒 **用户名/真名** → 替换为占位符
- [ ] 🔒 **API Key / Token** → 从环境变量或文件读取
- [ ] 🏷️ **赛博水印** → 脚本头部加作者/版本/链接水印
- [ ] 📂 **Temp 文件** → 检查 `AppData\Local\Temp` 下的调试脚本

### 赛博水印模板

```python
'''
==============================================================
  技能名称 — 功能说明
  📅 创建: 2026-XX-XX | 🏷️ 版本: 1.0.0
  ✍️ 作者: 你的名字 (虾评 @你的ID)
  🔗 发布: https://xiaping.coze.com/skill/{skill_id}
  ⚠️ 本脚本仅供个人学习使用, 未经授权禁止商用转载
==============================================================
'''
```

这套 Playwright + 默认浏览器 + Cookie 复用 的套路可以爬小红书 **任何页面**：

| 类型 | URL 格式 | 提取方式 |
|:---|---|:---|
| 🔍 **搜索笔记** | `/search_result?keyword=xxx` | `[data-note-id]` → 标题+ID+链接 |
| 📄 **单篇笔记详情** | `/explore/{note_id}` | `noteDetailMap` 或 DOM 提取正文+图片+标签 |
| 💬 **笔记评论** | `/explore/{note_id}` | 滚动加载后提取 `.comment-item` 或相关容器 |
| 👤 **用户主页** | `/user/profile/{user_id}` | 用户信息+笔记列表 |
| 🏠 **首页推荐** | `/explore` | 推荐 feed 流 |
| 🏷️ **话题/标签页** | `/page/{tag}` | 标签下笔记列表 |

### 爬取单篇笔记详情示例

```python
async def get_note_detail(page, note_id):
    await page.goto(f'https://www.xiaohongshu.com/explore/{note_id}', timeout=30000)
    await page.wait_for_timeout(5000)
    
    # 提取笔记信息
    info = await page.evaluate('''() => {
        const text = document.body.innerText;
        // 找标题、正文、标签等
        return { text: text.substring(0, 2000) };
    }''')
    return info
```

### 爬取笔记评论示例

```python
async def get_note_comments(page, note_id):
    await page.goto(f'https://www.xiaohongshu.com/explore/{note_id}', timeout=30000)
    await page.wait_for_timeout(5000)
    # 滚动触发评论加载
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await page.wait_for_timeout(3000)
    
    comments = await page.evaluate('''() => {
        const items = document.querySelectorAll('[class*="comment"], [class*="reply"]');
        return Array.from(items).slice(0, 50).map(el => el.textContent?.trim()).filter(Boolean);
    }')
    return comments
```

### 切换搜索筛选条件

```python
# 在搜索页面点击筛选标签
await page.click('text=图文')     # 只看图文笔记
await page.click('text=视频')     # 只看视频
await page.click('text=用户')     # 搜用户
await page.click('text=综合')     # 综合排序
await page.click('text=参考书目') # 特定子标签（搜索词相关）
```

### 翻页采集

```python
# 滚动加载更多
for page_num in range(3):
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await page.wait_for_timeout(2000)
    # 提取当前页数据...
```

以下脚本保存在本地 `Temp` 目录，核心文件：

| 脚本 | 功能 |
|:---|---|
| `login_xhs_v5.py` | 完整登录 + 搜索 + 提取数据 |
| `search_xhs_with_cookie.py` | 用 Cookie 直接搜，无需重新登录 |
| `final_excel_v2.py` | 数据整理 → 精美 Excel（含总结+热评+吐槽） |

## 🎯 优先级判断逻辑

```python
def get_priority(title):
    high = ['经验','上岸','400+','经验帖','速成','一战','400天','专业第一','备考','140+','双非']
    mid  = ['Q&A','答疑','考学硕','专硕','考研情况','选择专业','真题','没有实践']
    for k in high:
        if k in title: return (1, '⭐⭐⭐ 重点')
    for k in mid:
        if k in title: return (2, '⭐⭐ 参考')
    return (3, '⭐ 一般')
```

## 📊 Excel 模板结构

```
Sheet 1
├─ 📊 内容总结（分类统计 + 整体评价）
├─ 📋 数据表（27条笔记，按优先级排序）
│  ├─ 🔴 ⭐⭐⭐ 重点（经验帖/上岸喜报）红底
│  ├─ 🟠 ⭐⭐ 参考（Q&A/考研科普）橙底
│  └─ ⚪ ⭐ 一般（信息类）灰底
├─ 🔗 笔记链接（https://www.xiaohongshu.com/explore/{note_id}）
├─ 🏆 重点推荐 Top 5
├─ 🔥 热评精选（从评论数据提取，无评论时标注"暂无热评"）
└─ 💬 爬虫君的吐槽（爬取心路历程）
```

## 🔗 小红书笔记 URL 格式

```
https://www.xiaohongshu.com/explore/{24位hex_id}
```

通过 DOM 的 `data-note-id` 属性提取 ID，然后拼接完整链接。

## 🎯 智能关键词建议（读取使用者画像）

> 运行前先读取**使用者的用户画像**（身份/职业/近期目标/兴趣，如记忆中的个人资料），从画像推导 2-3 个候选关键词让用户确认，而不是让用户从零想：

```python
# 示例：画像 = 考研党 → 建议 ["考研经验", "上岸经验", "目标院校+专业"]
# 示例：画像 = 电商运营 → 建议 ["竞品名", "品类+选品", "爆款"]
keyword = os.environ.get('XHS_KEYWORD', '').strip() or input('🔍 请输入搜索关键词: ').strip()
```

## 📝 实战案例：考研经验分享（2026-07 实测）

| 指标 | 数据 |
|:---|---|
| 关键词 | 考研经验分享 |
| 获取笔记 | 27 条 |
| 含链接 | 20/27 条 |
| ⭐⭐⭐ 重点 | 10 条（经验帖/上岸喜报） |
| ⭐⭐ 参考 | 4 条（Q&A/考研科普） |
| ⭐ 一般 | 13 条 |
| 总耗时 | 约 15 分钟（含短信等待） |

---

## ⚠️ 免责声明（使用即视为同意）

1. **用途限制**：本技能仅供**个人学习、学术研究、内容分析**等合法用途，禁止用于商业牟利、数据转售、隐私窃取、恶意攻击或任何违反法律法规的行为。
2. **遵守平台规则**：使用者须遵守目标平台（小红书）的《用户协议》、robots 协议及隐私政策，以及适用法律（包括但不限于《中华人民共和国民法典》《个人信息保护法》《数据安全法》）。
3. **克制采集**：请保持低频率采集（建议请求间隔 ≥3 秒、单次会话 ≤3 页、不频繁登录），避免对平台服务造成异常负担；因高频请求触发风控导致的账号封禁、IP 限制等后果由使用者自行承担。
4. **数据责任**：采集所得数据（尤其是涉及个人信息的内容）应妥善保管、按需删除，**不得公开传播、转售或用于非法目的**；因数据滥用产生的法律责任由使用者承担。
5. **风险自担**：使用者因违规操作（绕过风控、滥用采集数据、违反平台条款）引发的账号封禁、法律纠纷、经济损失等，与技能作者及发布平台无关。
6. **内容免责**：技能作者对第三方网站（小红书）的内容、可用性、数据准确性及访问限制不承担任何责任；平台页面结构变化可能导致技能失效。
7. **无担保声明**：本技能按「现状」提供，不附带任何明示或默示担保。**不同意上述条款者，请勿使用本技能。**

> 📌 合规小贴士：如用于毕业论文、行业报告等正式场景，建议优先使用平台官方开放接口/数据分析产品，并注意对采集内容做匿名化处理。
