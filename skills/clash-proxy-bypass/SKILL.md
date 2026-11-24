---
name: clash-proxy-bypass
description: 在 Windows 上被墙（GFW）时用使用者的 Clash 代理访问海外网站。优先复用已在运行的 Clash Verge（7897 端口，零开销），未运行时临时拉起 verge-mihomo 内核加载订阅、切真实专线节点、用完自动杀进程。触发词：被墙, 翻墙, 代理, Clash, 打不开, 超时, wikipedia/github/google 访问失败, clash_proxy.py。
version: 1.0.0
author: Hermes Agent (Alice)
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [proxy, clash, gfw, network, windows]
---

# Clash 代理绕过 GFW

访问海外网站（Wikipedia/GitHub/Google 等）被墙或超时时的标准解决方案。
核心原则（使用者明确要求）：**用完即关、不常驻，绝不影响电脑正常用网**。

## 现成工具

`E:\Hermes Agent CN Desktop\data\hermes-home\scripts\clash_proxy.py`（已实测通过）：

```powershell
python clash_proxy.py check            # 检查 7897 是否可用
python clash_proxy.py fetch <URL>      # 通过代理抓 URL（自动复用/拉起，用完自动关）
python clash_proxy.py stop             # 停止自己拉起的临时内核
```

网站「打不开」一键诊断（本技能自带 `scripts/diagnose_site.py`，判定矩阵见大坑 13）：

```powershell
python <skill_dir>/scripts/diagnose_site.py https://example.com   # 直连/代理/代理健康 四行判定
```

## 关键环境事实（不要配错）

| 项 | 值 |
|----|----|
| 实际代理端口 | **7897**（Clash Verge 新版默认；配置文件里写的 mixed-port 可能还是 7890，以 netstat 实测为准） |
| 常驻进程 | clash-verge.exe + verge-mihomo.exe（用户在跑时直接复用，零开销） |
| 内核路径 | `C:\Program Files\Clash Verge\verge-mihomo.exe` |
| 订阅配置 | `~\AppData\Roaming\io.github.clash-verge-rev.clash-verge-rev\profiles\ROIgCd08d8Bj.yaml` |
| 控制 API | 临时拉起时用 `127.0.0.1:19090`（避开 Verge 常驻的 9090） |

## 策略（两层）

1. **Clash 已在运行**（`Test-NetConnection 127.0.0.1 -Port 7897` 通）→ 直接用 `http://127.0.0.1:7897`，**不开不关**任何进程。
2. **未运行** → 临时拉起内核：
   - 复制订阅配置为临时文件，改 `mixed-port: 7897`、`external-controller: '127.0.0.1:19090'`、**`mode: global`**（不改原文件）
   - `verge-mihomo.exe -f 临时配置 -d <verge目录>` 启动（Python subprocess + CREATE_NO_WINDOW，勿用 PowerShell Start-Process）
   - 等端口就绪后，**通过 REST API 把 GLOBAL 组切到真实专线节点**（默认指向 DIRECT 会直连失败）
   - 用完 `taskkill /PID <pid> /F` 杀进程 + 删临时配置

## 大坑（实测踩过）

1. **`fetch` 只打印响应前 500 字**——`clash_proxy.py fetch <URL>` 输出是 `内容前 500 字: <截断>`，拿不到完整页面。要全文：curl 走 7897（`curl.exe -x http://127.0.0.1:7897 -sL <URL> -o out.html`），或 agent-browser 渲染（见 web-scraper 技能）。
2. **`fetch` 用完即杀内核——别"先 fetch 拉起、再自己走 7897"**：fetch 退出时临时内核已 taskkill，紧接着的 urllib/requests 连 127.0.0.1:7897 会 `ConnectionRefusedError [WinError 10061]`。要长会话就自己 Popen 拉起内核并保持进程，或一条命令内用 `curl -x` 抓完。
3. **抓 JS 渲染站（Docusaurus 文档站等）时 fetch/curl 只有 HTML 壳**：正文在 JS 里（如 DeepSeek 官方定价页，curl 拿到 22KB 但正文 0）。正确姿势：agent-browser 打开 → `eval "document.querySelector('main article').innerText"` 取正文；Edge 路径与完整用法见 web-scraper 技能。
4. **`-t 60` 是配置校验模式，不是代理模式**——校验通过 ≠ 能代理。正常启动不要带 `-t`。
5. **GLOBAL 组默认 now=DIRECT**——全局模式也必须先切节点，否则请求走直连直接失败。
6. **订阅里有假节点**：`请立即到官网下载新客户端！`、`更新于 2026/4/19`、`邀请新用户60%返利`、`一元.com`、`yiyuanjichang.com` 都是不可用的广告/占位节点。筛选真实节点：type ∈ {Vless, Vmess, Shadowsocks, Trojan, Hysteria2, Hysteria} 且名称不含上述标记；优先含「专线/香港/日本/新加坡」的。
7. **切到假节点的症状**：`SSL: UNEXPECTED_EOF_WHILE_READING` 或 `WinError 10053`（连接被中止）——不是网络问题，是节点不对，换真实专线。
8. **REST API 切节点**：`PUT /proxies/GLOBAL` body `{"name": "香港 03 | 专线"}` → 204 即成功。
9. **PowerShell 权限坑**：`Start-Process` 拉起内核可能 `WinError 5 拒绝访问`；用 Python `subprocess.Popen(creationflags=CREATE_NO_WINDOW)` 稳定。
10. **临时配置文件**写到 `%TEMP%`，用时间戳命名避免和 Verge 的 config.yaml 冲突；`-d` 工作目录仍指向 Verge 目录（需要 geoip/geosite 数据）。
11. **搜索引擎/社媒对代理爬虫全面反爬（2026-08 实测）**：Google 搜索、Bing、DuckDuckGo HTML 版、Reddit JSON API 全被拦（`SSL: UNEXPECTED_EOF`、403 Blocked、空结果页）——这是站方反爬，不是节点问题，换节点无用。**有效替代：HN Algolia API**（`https://hn.algolia.com/api/v1/search?query=<词>&tags=story&hitsPerPage=8`，JSON 直出标题/分数/评论数/URL，对爬虫友好），调研海外口碑用它最稳。GitHub 搜索 API 未认证限流约 60 次/小时，批量查 star 要 `time.sleep(0.3)` 间隔，403 后等一小时。目录站（glama.ai/mcp/servers 等）HTML 是 JS 渲染，直接抓 `<h3>` 提取比解析 JSON 字段靠谱。
12. **连续抓多个 URL 的正规姿势**：`clash_proxy.py fetch` 用完即杀内核，多 URL 调研要先 `import clash_proxy as cp` → `cp.start_temporary()` 保持进程 → 循环 urllib 走 7897 抓 → 脚本收尾 `cp.stop_temporary()`。别先 fetch 拉起再自己连 7897（内核已杀，ConnectionRefused）。
13. **用户说「网站打不开」≠ 被墙——先测直连，别急着开代理**（2026-08 实测）：诊断顺序 = ① `curl.exe -sS -o NUL -w "%{http_code}" <URL>` 直连；② 直连 200 → 站活着，问题在浏览器代理残留（系统 ProxyEnable=0 但 ProxyServer 残留 127.0.0.1:7897、浏览器插件还挂着 → 请求进黑洞），让用户切直连/关插件，**不开代理**；③ 直连超时 → 拉代理再测，同时用 Google 204 验证代理健康；④ 组合判定：**直连200 + 代理超时 = 站反代理**。实测 map.dishisanceng.com：直连秒开 200，走新加坡专线反而读取超时——部分国内站对境外/代理 IP 不友好，开代理反而打不开，必须裸连。一键跑 `python <skill>/scripts/diagnose_site.py <URL>` 出四行判定（脚本自动复用/拉起/关停内核）。
14. **Test-NetConnection 端口测试不可信**：实测 DNS 正常 + TcpTestSucceeded=False，但 curl 直连 200 秒开。端口可达性一律以 curl/HTTP 实测为准，别拿 Test-NetConnection 下"网站死了"的结论。
15. **Edge headless 渲染验证必须用 Start-Process**：`&` 调用 msedge 会被 Hermes 终端误判为后台运行直接拒绝；用 `Start-Process msedge -ArgumentList @('--headless=new','--disable-gpu','--dump-dom','--virtual-time-budget=8000',URL) -RedirectStandardOutput out.html -Wait -NoNewWindow` 拿渲染后 DOM，检查标题/loading-mask 是否消失来判断页面是否真正加载成功（区分"站挂了"vs"页面 JS 没跑起来"）。
16. **GitHub 分域可达性 + 仓库分析替代方案（2026-08 实测，别盲目开代理）**：被墙环境里 GitHub 域名**不是全挂**——`api.github.com`（REST API）和 `raw.githubusercontent.com`（单文件）**直连可用**；`github.com`（git clone）和 `codeload.github.com`（tarball 大文件）被墙/超时。分析 GitHub 仓库的正确姿势：① `GET api.github.com/repos/{owner}/{repo}` 拿元数据（star/语言/创建时间/大小/license）② `GET .../git/trees/main?recursive=1` 拿完整文件清单（含各文件 size，注意 `truncated` 字段）③ 用 `curl.exe raw.githubusercontent.com/{owner}/{repo}/main/{path}` 循环逐个抓文本文件（小文件直连很稳）④ 本地 read_file 分析，二进制/图片跳过。**git clone 失败先查 `git config --global --list` 里的 http.proxy 残留**——曾配坏代理（如 127.0.0.1:443）会让 git 全挂而 curl 正常；修法 `git config --global --unset http.proxy` 或临时 `git -c http.proxy=... clone`。
17. **专线节点下载大文件也可能 SSL EOF，但 codeload 是"挑节点"不是"全挂"**：默认切的「新加坡 01 | 专线」下载 codeload tarball 必报 `SSL: UNEXPECTED_EOF_WHILE_READING`，但 2026-08 实测 8 个专线节点里 **只有「香港 01 | 专线」「香港 03 | 专线」能通 codeload**（44s 拉完 6MB），日本/新加坡/香港 04/06 全挂。需要 tarball 时：切节点 → 测通 → 下载；快速批量探测哪条节点能通目标 URL 用 `python <skill>/scripts/probe_nodes.py <URL>`（自动遍历候选节点打印结果）。实在不行再退到大坑 16 的 tree API + raw 逐文件方案。
18. **GitHub 仓库分析完整工作流**（元数据→文件树→批量抓取→本地分析的 PowerShell 模板）见 `references/github-repo-analysis.md`。
19. **pnpm/npm 拉 GitHub tarball 不走 git 的代理配置**：`dsh plugin add github:...` 这类 git-hosted 安装内部是 pnpm 直连 codeload 下载 tarball，git 配了 http.proxy 也无效，报 `error (23) The operation was aborted due to timeout` / `GET codeload... error (23) Will retry` 就是没走代理。必须在**同一会话**先 `$env:HTTP_PROXY = "http://127.0.0.1:7897"; $env:HTTPS_PROXY = "http://127.0.0.1:7897"` 再跑，且节点要挑能通 codeload 的（大坑 17）。
   **无 Clash 时的解法（2026-08-16 实测）**：① git 源能走镜像——临时改全局 `~/.gitconfig`（`[http] proxy=` 清空 + `[url "https://ghfast.top/https://github.com/"] insteadOf = https://github.com/`）→ 装完还原；pnpm 子进程吃全局 gitconfig，但 **GIT_CONFIG_GLOBAL 环境变量注入对 pnpm 无效**。② codeload tarball 下载走 node fetch，**连 gitconfig 也不吃** → 大包（>2MB）必超时，改为**手动本地挂载**：zip 解压拷进 `profiles/<p>/node_modules/@scope/pkg/`（robocopy 会漏点/下划线开头文件，如 _selftest.mjs，需补拷）+ package.json dependencies 用 `file:` 引用 + bundles 列表加名 + `pnpm install`（file: 本地依赖零网络 ~1s）。③ ⚠️ 挂载 bundle 时**不要**在 profile 的 cordis.patch.yml 手动 insert——bundle 包自带的 cordis.patch.yml 加载时自动应用，重复 insert 报 `duplicate loader entry id: <id>`（实测玄枢报 `chinese-traditional-wisdom-skill`），dsh web 启动直接退出；profile 层保持 `[]`，还原后重启即恢复。dsh web 启动即退先看后台进程日志抓这个签名。④ 镜像 git 协议（`git -c http.proxy= ls-remote` 实测）: ghfast.top / gh-proxy.com / ghproxy.net ✅，gitclone.com git 服务 502 ❌。
20. **中文站调研：先试国内搜索引擎，别急着开代理（2026-08 实测）**：Bing（含 cn.bing.com）对 curl 返回**固定缓存结果**（忽略查询词，搜"小程序备案"竟出小红书/小游戏导航）、百度返回 ~620B 重定向壳——都不可用且与代理无关，国内站直连更快。**正确姿势：360 搜索 `curl -A "<Chrome UA>" "https://www.so.com/s?q=<URL编码词>"` 和搜狗 `https://www.sogou.com/web?query=<词>` 直连可用**，返回完整 HTML 可正则提取结果块（360：`<li class="res-list">`，搜狗：`<div class="vrwrap">`）。注意：so.com 结果链接是 `so.com/link?m=...` JS 跳转壳（curl -L 不跟随），页面里有 `<script>window.location.replace("真实URL")</script>`（另有 `<noscript><meta http-equiv="refresh">` 兜底），解析该行拿真实 URL 再抓正文。抓取解析脚本一律写成 .py 文件再跑——**PowerShell 内联 `python -c` 遇到中文/引号/`\"` 转义必炸**（引号被吞、字符串截断），脚本文件 + `os.environ['TEMP']` 传参最稳。另：微信开放文档（VuePress）是 SSR，正文在 `<div id="app" data-server-rendered="true">` 内可直接正则提取；微信开放社区/支付宝文档纯 JS 渲染（curl 只有标题），改搜 360 快照或转载帖。

21. **GitHub 热门/新项目发现——Trending 网页被墙的替代方案（2026-08-16 实测）**：`github.com/trending` 直连挂（000），镜像代理全 403（Cloudflare "Invalid input"/Access Denied）或 JS 空壳，但 **`api.github.com` 直连可用**，用搜索接口模拟 trending：`curl.exe -s "https://api.github.com/search/repositories?q=created:%3E2026-07-16+stars:%3E100&sort=stars&order=desc&per_page=30"` 拿最近一个月新建爆款（实测 1279 命中，前 30 够挑）；变体 `q=stars:>5000&sort=updated` 看老项目近期活跃。**国内下载通道实测**：ghfast.top 能下 zip（`https://ghfast.top/https://github.com/{o}/{r}/archive/refs/heads/{branch}.zip`，663KB 实测秒下，branch 用 default_branch）、gitclone.com 能 clone（`git clone https://gitclone.com/github.com/{o}/{r}`）；gh-proxy.com/ghproxy.net 通但只拦网页、文件下载偶尔可过；**已失效勿试**：kkgithub.com、github.moeyy.xyz、hub.gitmirror.com、github.abskoop.xyz、ghproxy.com、mirror.ghproxy.com（全 000）；gitcode.com 通但纯 JS 渲染 curl 只有壳。镜像代理站**只加速文件/zip，不代理网页**。完整清单与模板见 `references/github-repo-analysis.md`。

## 验证命令

```powershell
# 复用模式验证（Clash 开着时）
Invoke-WebRequest -Uri "https://www.google.com/generate_204" -Proxy "http://127.0.0.1:7897" -UseBasicParsing -TimeoutSec 15
# 期望 204
```

## 注意事项

- 代理只用于**被墙网站的抓取**，不要给所有流量开代理（用完即关）
- 用户的订阅是机场（一元机场），节点会过期/变动；假节点检测标记需定期更新
- 不要修改用户的订阅原文件、不要动 Verge 常驻进程的配置
