# 小红书 (Xiaohongshu / RED) 反爬案例研究

> 案例目标：搜索「目标院校戏剧管理考研」并提取笔记评论
> 结论：**小红书网页版是全链路登录墙 + 签名API + WAF 的典型代表**

## 反爬等级评估

| 维度 | 等级 | 说明 |
|:---|:---:|:---|
| JS 渲染 | 🔴 最高 | 100% 内容靠异步 JS 加载 |
| 登录墙 | 🔴 强制 | 搜索页显示「登录后查看搜索结果」 |
| API 签名 | 🔴 HMAC | 需要 `x-s`/`x-t` 签名，前端 JS 动态生成 |
| Cookie 校验 | 🔴 必须 | 无 Cookie 返回 code=-101「无登录信息」 |
| WAF | 🟡 中等 | 返回 200 但内容被登录页替换 |
| 搜索引擎索引 | 🟡 低 | 笔记链接不被 Bing/Google 索引 |

## 尝试过的技术路径

### 1️⃣ Direct HTTP Request
```python
# 结果：拿到 HTML 空壳
r = requests.get('https://www.xiaohongshu.com/search_result?keyword=...')
# __INITIAL_STATE__ 存在但 feeds: [] 为空
```
**结论:** 搜索结果的初始数据不在 HTML 里，需后续 API 加载。

### 2️⃣ 提取内嵌 JSON (__INITIAL_STATE__)
```python
# 成功提取但值含 JS 特有语法
m = re.search(r'window\.__INITIAL_STATE__=(.*?)</script>', html, re.DOTALL)
raw = m.group(1).strip()
# ⚠️ JSON 里有 :undefined → 需替换为 :null
raw = raw.replace(':undefined', ':null')
raw = re.sub(r'\bundefined\b', 'null', raw)
```
**发现:** `:undefined` 是合法的 JS 但不合法 JSON，这是常见提取障碍。

### 3️⃣ 调用 edith API (搜索接口)
```bash
POST https://edith.xiaohongshu.com/api/sns/web/v1/search/notes
Content-Type: application/json
Body: {"keyword":"目标院校戏剧管理考研","page":1,"page_size":20}
→ Response: {"code": -101, "msg": "无登录信息，或登录信息为空"}
```
**结论:** 无 Cookie 无法调用搜索 API。

### 4️⃣ agent-browser + Edge 无头浏览器
```bash
agent-browser open <url> --executable-path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
```
**结果:** 成功加载页面，SnapShot 显示「登录后查看搜索结果」+ 登录表单。
**注意:** XHS 页面非常重量级（700KB+ HTML，大量 JS/图片），容易超时。建议 `--timeout 30000` 以上。

### 5️⃣ JSON 循环引用陷阱
```javascript
// eval JSON.stringify(window.__INITIAL_STATE__) 会失败！
// → TypeError: Converting circular structure to JSON
```
**解决:** 不要全量 stringify，分段提取特定属性：
```javascript
JSON.stringify(window.__INITIAL_STATE__.search)         // 搜索状态
JSON.stringify(window.__INITIAL_STATE__.note)            // 笔记状态
JSON.stringify(window.__INITIAL_STATE__.feed)            // 推荐流
```

## 可行的突破路径

### 路径 A: 登录后使用 agent-browser
1. 在真实浏览器中登录小红书
2. 导出 Cookie: `agent-browser state save xhs_auth.json`
3. 后续会话加载状态: `agent-browser state load xhs_auth.json`
4. 再打开搜索页即可看到内容

### 路径 B: 从分享短链入手
小红书笔记可通过 xhslink.com 短链分享，这些链接可能不强制登录。
但搜索引擎不索引这些链接，需要从其他渠道获取（微信、QQ 等）。

### 路径 C: 搜狗微信搜索替代
微信公众号「目标院校考研大家庭」「艺研目标院校考研」等经常发布相关内容，
搜狗微信搜索可以抓取标题和摘要，是有效的替代数据源。

## ✅ 实战验证：完整登录 + 数据提取流程（2026-07-23）

> **目标:** 搜索「目标院校戏剧管理考研」，提取 27 条小红书笔记
> **结果:** ✅ 成功！登录 + 搜索 + DOM 提取 + Excel 导出

### 前置环境
- Windows 11 + Edge 浏览器（系统自带）
- `pip install playwright` 
- `pip install openpyxl`（Excel 导出用）

### 完整登录流程

```python
import asyncio
from playwright.async_api import async_playwright

PHONE = '159xxxxxxxx'  # 小红书绑定的手机号

async def login():
    p = await async_playwright().start()
    browser = await p.chromium.launch(channel='msedge', headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    
    # 1️⃣ 打开登录页
    await page.goto('https://www.xiaohongshu.com/login', wait_until='domcontentloaded')
    await page.wait_for_timeout(2000)
    
    # 2️⃣ 勾选同意条款（关键！）
    agree = await page.query_selector('span.agree-icon')
    await agree.click()
    
    # 3️⃣ 填入手机号
    phone_input = await page.query_selector('input[placeholder="输入手机号"]')
    await phone_input.fill(PHONE)
    
    # 4️⃣ 点击「获取验证码」（注意选择器！）
    code_btn = await page.query_selector('span.code-button.active')
    await code_btn.click()
    # ✅ 此时用户手机收到短信验证码
    
    # 5️⃣ 填入验证码 + 登录（用户提供验证码后）
    code_input = await page.query_selector('input[placeholder="输入验证码"]')
    await code_input.fill('收到的验证码')
    login_btn = await page.query_selector('button.submit')
    await login_btn.click()
    
    # 6️⃣ 保存 Cookie（免下次登录）
    cookies = await context.cookies()
    with open('xhs_cookies.json', 'w') as f:
        json.dump(cookies, f)
    
    await browser.close()
    await p.stop()
```

### ⚠️ 关键结构解析

从 DOM 中提取的登录页结构：

```html
<!-- 同意条款（不是 checkbox，是自定义图标） -->
<span class="agree-icon">
  <div class="icon-wrapper"><!----></div>
</span>

<!-- 手机号输入 -->
<label class="phone">
  <span class="country-code">+86</span>
  <input placeholder="输入手机号" type="text" name="xhs-pc-web-phone">
</label>

<!-- 验证码输入 + 获取按钮 -->
<label class="auth-code">
  <input type="number" placeholder="输入验证码" autocomplete="false">
  <span class="code-button active">获取验证码</span>   <!-- ← 点击这个！ -->
</label>

<!-- 登录按钮 -->
<button class="submit"> 登录 </button>
```

> 💡 **验证码按钮的精确选择器**: `span.code-button.active` 或 `label.auth-code span`

### 提取搜索数据（登录后）

**核心发现：登录后的搜索数据在 DOM 中，不在 `__INITIAL_STATE__` 里。**

即使登录成功，`__INITIAL_STATE__.search.feeds` 仍然是 `[]`。搜索结果是客户端通过另一个 API 获取后渲染到 DOM 的。

```python
# 方式 A：从 DOM 提取可见文字（已验证，拿到 27 条）
text = await page.evaluate('() => document.body.innerText')
lines = [l.strip() for l in text.split('\n') if l.strip()]
# 过滤出相关关键词
notes = [l for l in lines if any(kw in l for kw in ['目标院校','考研','上岸','戏剧管理'])]

# 方式 B：从 data-note-id 属性提取笔记 ID + 构建链接（已验证）
note_data = await page.evaluate('''() => {
    const results = [];
    const cards = document.querySelectorAll('[data-note-id]');
    cards.forEach(card => {
        const id = card.getAttribute('data-note-id');
        if (id && id.length === 24) {
            const title = card.querySelector('.title')?.textContent?.trim() || '';
            results.push({ id, title });
        }
    });
    return results;
}''')
# 构建链接: https://www.xiaohongshu.com/explore/{id}
```

### JSON 循环引用处理

```javascript
// 直接 JSON.stringify(window.__INITIAL_STATE__) → TypeError!
// 正确做法：分段提取
JSON.stringify(window.__INITIAL_STATE__.search)  // 搜索状态
JSON.stringify(window.__INITIAL_STATE__.user)     // 用户登录态

// 或用 WeakSet 去重
const seen = new WeakSet();
JSON.stringify(window.__INITIAL_STATE__, (key, val) => {
    if (typeof val === 'object' && val !== null) {
        if (seen.has(val)) return '[Circular]';
        seen.add(val);
    }
    return val;
});
```

### 复用 Cookie（免重新登录）

```python
# 下次会话
if os.path.exists('xhs_cookies.json'):
    with open('xhs_cookies.json') as f:
        cookies = json.load(f)
    await context.add_cookies(cookies)
# 直接打开搜索页即可
await page.goto('https://www.xiaohongshu.com/search_result?keyword=目标院校戏剧管理考研')
```

### 防封号建议
- ⏱ 请求间隔 ≥ 3秒（模拟人操作）
- 📄 单次最多爬 2-3 页
- 🔄 不频繁登录登出
- 🚫 不要短时间多次搜索相同关键词
- 🍪 尽量复用 Cookie，减少登录频次

## 其他中文站反爬对比

| 网站 | 反爬等级 | 可爬程度 | 推荐方法 |
|:---|:---:|:---:|:---|
| 豆瓣 | 🟢 低 | 直接 HTML 解析 | `web_scraper.py` |
| 知乎 | 🟡 中 | 需 Cookie | 登录后 API |
| B站 | 🟡 中 | JS 加载但 API 可调 | agent-browser / API |
| 百度 | 🔴 高 | CAPTCHA 墙 | 搜狗微信替代 |
| 小红书 | 🔴🔴 极高 | 全链路封锁 | 登录 + agent-browser |
