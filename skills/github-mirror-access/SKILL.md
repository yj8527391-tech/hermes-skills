---
name: github-mirror-access
description: 国内被墙环境下访问和发布 GitHub 的完整套路——镜像站探测、GitHub API 直连拿数据、ghfast.top 下载 zip、git 协议走镜像、第三方仓库/插件安全审查，以及推送自己的仓库（git-over-HTTPS 被掐时走 SSH over 443）和把技能/代码开源上架。当用户说"看看 GitHub 上有什么"、"下载/克隆 GitHub 项目"、"装 GitHub 插件"、"把东西上架/传到 GitHub"且直连不通时使用。
version: 1.0.0
author: Hermes Agent (Alice)
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [github, mirror, gfw, proxy, download, security-review]
---

# GitHub 国内镜像访问（GFW 环境）

2026-08-16 实测。核心结论：**网页 github.com 被墙，但 `api.github.com` 直连通常通**——数据层走 API，文件层走镜像代理。

## 第一步：探测

```powershell
# 测连通性（注意用 curl.exe，PowerShell 里 curl 是 Invoke-WebRequest 别名）
curl.exe -s -o NUL -w "%{http_code}" -L --connect-timeout 8 --max-time 15 <url>
```

**关键认知：curl.exe 与 git 的代理行为不同**——本机 git 全局配置了 `http.proxy=127.0.0.1:7897`（Clash Verge），Clash 没跑时 git 所有请求死（报错特征 "Failed to connect ... via 127.0.0.1"）；curl.exe 不走该代理，能直连国内镜像。所以探测用 curl，git 操作要单独处理（见下）。

## 镜像可用性清单（2026-08 实测）

| 镜像 | 网页 | zip 下载 | git 协议 | 备注 |
|---|---|---|---|---|
| `ghfast.top` | ✗(Invalid input) | ✅ | ✅ | 首选 |
| `gh-proxy.com` | ✗(CF 403) | ✅ | ✅ | |
| `ghproxy.net` | ✗ | ✅ | ✅ | |
| `gitclone.com` | ✅ | - | ✗(502) | git 服务不可用 |
| `gitcode.com` | ✅(JS渲染抓不到) | - | - | CSDN 的，需浏览器 |

已失效：kkgithub.com、ghproxy.com、mirror.ghproxy.com、hub.gitmirror.com、github.moeyy.xyz、github.abskoop.xyz（2026-08 全部 000）。镜像会死，每次先探测。

## 拿数据（GitHub API 直连）

- **Trending 替代**（网页 trending 被墙）：`https://api.github.com/search/repositories?q=created:>YYYY-MM-DD+stars:>100&sort=stars&order=desc&per_page=30` —— 拿最近一个月爆款项目
- 仓库元数据：`/repos/owner/repo`（stars、pushed_at、license、archived、size）
- README：`/repos/owner/repo/readme` → JSON 的 `content` 字段是 **base64**，需解码
- 请求头加 `-H "Accept: application/vnd.github+json" -H "User-Agent: hermes-agent"`（无 UA 会被拒）
- 未认证限速 60 次/小时；偶发 5xx 重试 3 秒即可
- **限额用尽的兜底：`raw.githubusercontent.com` 不占 API 限额**——`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/README.md`，同样可直读 `docs/*.md`、`package.json`、`server/*.js` 等任意文件；比 API base64 解码更省事，是 60/h 用尽后的主力通道（2026-09 实测）
- **license 字段为空 ≠ 无 license**：可能 LICENSE 藏在子目录（玄枢案例），以 README 声明为准

## 下载文件（zip）

```
https://ghfast.top/https://github.com/owner/repo/archive/refs/heads/main.zip
```
默认分支可能是 `master`，先看 API 返回的 `default_branch`。实测 663KB ~ 7.9MB 都能秒下。

## git 协议走镜像（clone / 装 git 依赖 / dsh 插件场景）

镜像支持 git smart HTTP：`git ls-remote https://ghfast.top/https://github.com/owner/repo.git HEAD`。

**GIT_CONFIG_GLOBAL 环境变量注入对 pnpm/node 子进程无效**（实测报 missing config value），必须临时改全局 `~\.gitconfig`：

1. 备份：`Copy-Item ~\.gitconfig ~\.gitconfig.bak`
2. 写入：
```ini
[http]
	proxy =
	postBuffer = 524288000
[https]
	proxy =
[url "https://ghfast.top/https://github.com/"]
	insteadOf = https://github.com/
```
3. 执行安装 → 4. 还原（含删 .bak）。装完必须还原，否则 insteadOf 会让 push 全部指向镜像。

**codeload.github.com 的 tarball 下载走 node fetch，不吃 gitconfig**（pnpm 装 git 依赖第二步必踩）→ 大包直接手动安装：下载 zip 解压 → 拷到目标 node_modules → package.json 用 `file:` 依赖注册 → `pnpm install`（本地零网络）。dsh 插件手动挂载细节见 `deepseek-harness-notes` 技能。

## 第三方仓库/插件安全审查（装之前必做）

1. **元数据体检**：stars/forks、创建时间（<3 天要警惕）、pushed_at（僵尸仓库）、license、archived
2. **代码扫描**（search_files content 模式）：
   - 网络外传：`fetch\(|https?\.request|axios|XMLHttpRequest|WebSocket|child_process|\.exec\(|\.spawn\(|eval\(|new Function`
   - 敏感读取：`\.ssh|\.env|api[_-]?key|token|secret|password|credential`
   - 注意区分：正则 `\.exec\(`（无害）vs `child_process`（危险）；测试文件里的 spawn 无害；本地 `fetch('/xxx.json')` 相对路径无害
3. 结论分级：纯文档技能包（零执行）= 低风险；有引擎/可执行代码但扫描干净 = 中风险可装；任何外传 = 不装
4. 装插件=跑第三方代码，权限等同本人——不熟的先在无密钥环境试

## 推送到 GitHub（要写权限，2026-11-24 实测）

访问别人的仓库能靠镜像，**推送自己的仓库不行**——镜像站不代理 push，只能走真实通道。

### 诊断三步（别跳过）

```bash
curl.exe -s -o /dev/null -w "api -> %{http_code}\n" https://api.github.com/rate_limit      # 数据层
curl.exe -s -o /dev/null -w "web -> %{http_code}\n" https://github.com                    # 网页层
timeout 20 ssh -p 443 -o StrictHostKeyChecking=no -o BatchMode=yes -T git@ssh.github.com   # 传输层
```

实测结果的含义：
- `api -> 200` 但 `git ls-remote https://github.com/...` 报 **`fatal: expected flush after ref listing`** → 典型的 git-over-HTTPS 被掐。**别怀疑自己写错命令**，也别在 `http.version=HTTP/1.1`、`postBuffer` 上来回试（实测全无效）
- `ssh -p 443 ... Permission denied (publickey)` = **通路正常，只差密钥**。这是成功信号，不是失败
- 结论：GFW 环境下 **push 走 SSH over 443**（`ssh.github.com:443`），不走 HTTPS

### 密钥与本机配置

```bash
ssh-keygen -t ed25519 -N "" -C "<用途>" -f ~/.ssh/id_ed25519_github -q
cat ~/.ssh/id_ed25519_github.pub   # 这串交给使用者贴到 https://github.com/settings/keys
```

- 本机 git 全局常有 `http.proxy=127.0.0.1:7897`（Clash），Clash 没起时所有 git 请求死。**用仓库级覆盖** `git config --local http.proxy ""`、`--local https.proxy ""`，别动全局配置
- push 时显式指定：`GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_github -p 443 -o StrictHostKeyChecking=no" git push -u origin main`，并 `git config --local core.sshCommand "ssh -i ~/.ssh/id_ed25519_github -p 443"`
- ⚠️ **判断「有没有存过 GitHub 凭证」不要用 `git credential fill`**——无凭证时它会挂起等 GUI 弹窗（实测 180s 超时、看起来像网络卡死）。改看 `~/.ssh` 有没有 key、`~/.config/gh` 存不存在
- 网页自动化不再试：桌面预览窗口加载 github.com 会超时（被墙），建仓和挂 key 必须使用者点两下。给他**预填链接**省事：`https://github.com/new?name=<repo>`，并提醒**别勾** README / license / .gitignore（与本地已有提交冲突）

### 「你来操纵就行」的边界

使用者这句话的授权范围是**执行本地一切操作**（建目录、清洗、commit、写好 push 脚本），不包含**替他注册账号或替他授权**。正确姿势：把能做的全做完 → 停在需要人类账号的那一步 → 给他三条带链接的动作 + 一句「做完说一声我立刻推」。别反复催，也别声称已完成。

### 发布自己的代码/技能到 GitHub

挑选、隐私清洗、仓库结构、README 模板、push.sh 全套见 `references/publish-skills-to-github.md`。

## 陷阱

- **robocopy 漏复制点/下划线开头文件**（如 `_selftest.mjs`）→ 拷完核对源目录顶层文件，漏的单独补拷
- 网页代理抓 HTML 会返回 "Invalid input." 或 CF 403 页——镜像只代理文件/git，不代理页面；页面数据走 API
- PowerShell 传复杂 python -c 会转义爆炸 → 写脚本文件跑；python subprocess 调 `.cmd` 需完整路径（如 `E:\npm-global\dsh.cmd`），`.cmd` 不经 PATH 解析
- API 搜索 `q=` 参数里的 `:` 要 URL 编码（`%3E`）
- **二手来源里的仓库名先核存在性再采用**：搜索结果/文章/榜单里的项目可能早已删除或根本不存在（2026-09 实测：一个被多处提到的 `ali-musafir/openclaw-office` 用 API 一查是 404）。落地前先 `curl -s https://api.github.com/repos/<owner>/<repo>` 核一遍，404 就别写进交付
- **子agent 派出去查 GitHub 时，把上面这些约束写进它的 context**：否则它会重踩（网页不通、API 限额、写文件到 `/tmp` 在 Windows 不映射）
- **超长的内联 grep 正则一行会被 terminal 硬拦**（报 `BLOCKED (hardline): command parser limit`，提示已存到 `cache/blocked-scripts/`）。别重试同样的一行——写成 `.sh` 文件再 `bash 文件.sh`，顺便好复用
- `netstat -ano | grep LISTENING` 确认代理端口是否真在监听，比 `tasklist` 找进程可靠（本机 7897 无监听 = Clash 没跑，但 git 全局配置还指着它）
