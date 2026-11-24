# GitHub 仓库分析工作流（被墙环境下）

2026-08 实测（分析 NanmiCoder/dsh-agent-teams 时踩通）。核心结论：**先试直连分域，别盲目开代理**。

## 分域可达性（2026-08，直连实测）

| 域名 | 用途 | 直连 | 说明 |
|---|---|---|---|
| `api.github.com` | REST API（元数据/文件树/搜索） | ✅ 可用 | 未认证限流 ~60 次/小时 |
| `raw.githubusercontent.com` | 单文件原始内容 | ✅ 可用 | 小文本文件很稳 |
| `github.com` | git clone / trending 网页 | ❌ 被墙/坏代理 | 443 连不上 |
| `codeload.github.com` | tarball 大文件下载 | ❌ 超时 | 代理也常被掐（SSL EOF） |

## 热门/新项目发现（Trending 网页的替代方案，2026-08-16 实测）

`github.com/trending` 直连挂，所有镜像代理要么 403（Cloudflare）要么 JS 空壳 → **用 search API 直连模拟 trending**：

```powershell
# 最近一个月新建爆款（实测 1279 命中，per_page=30 够挑）
curl.exe -s "https://api.github.com/search/repositories?q=created:%3E2026-07-16+stars:%3E100&sort=stars&order=desc&per_page=30" -o trending.json
# 解析 items[]: full_name / stargazers_count / language / description

# 变体：
# 老项目近期活跃:  q=stars:>5000&sort=updated
# 按主题找:        q=topic:xxx&sort=stars
# 限流: 未认证 ~60 次/小时，403 后等一小时（见 SKILL.md 大坑 11）
```

解析 JSON 一律写 .py 脚本文件再跑（PowerShell 内联 `python -c` 遇 f-string 引号/`|`/中文转义必炸，见 SKILL.md 大坑 20）。

## 国内镜像下载通道（2026-08-16 实测清单）

| 通道 | 状态 | 用法 |
|---|---|---|
| `api.github.com` | ✅ 直连 | 元数据/搜索/文件树 |
| `ghfast.top` | ✅ **zip 下载实测成功**（663KB 秒下） | `https://ghfast.top/https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip`（branch 用 default_branch，可能是 master） |
| `gitclone.com` | ✅ clone 加速 | `git clone https://gitclone.com/github.com/{owner}/{repo}` |
| `gh-proxy.com` / `ghproxy.net` | ⚠️ 通但 403 拦网页代理 | 文件下载偶尔可过，网页代理必被 Cloudflare 拦 |
| `gitcode.com`（AtomGit/CSDN） | ⚠️ 通但纯 JS 渲染 | curl 只有 HTML 壳，热门内容爬不到 |
| `kkgithub.com` / `github.moeyy.xyz` / `hub.gitmirror.com` / `github.abskoop.xyz` / `ghproxy.com` / `mirror.ghproxy.com` | ❌ 000 失效 | 别浪费时间 |

经验：ghfast 系镜像代理站**只加速文件/zip 下载，不代理网页 HTML**（返回 "Invalid input." 或 403）。探活命令：`curl.exe -s -o NUL -w "%{http_code}" -L --connect-timeout 8 <URL>`（000=域名挂，403=活着但拦爬虫）。

## 完整流程（不用 git clone、不用下 tarball）

### 1. 仓库元数据
```powershell
curl.exe -s -L -A "Mozilla/5.0" "https://api.github.com/repos/{owner}/{repo}" -o repo.json
# 解析: full_name/description/stargazers_count/forks_count/language/created_at/pushed_at/license.spdx_id/topics
```
注意：API 的 `license` 字段为空 ≠ 没 license，README 可能声称 MIT——以仓库里有没有 LICENSE 文件为准（看文件树）。

### 2. 完整文件清单（含大小）
```powershell
curl.exe -s -L -A "Mozilla/5.0" "https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1" -o tree.json
# $t.tree | Where-Object { $_.type -eq 'blob' } → path + size
# 检查 truncated 字段：True 说明文件太多被截断，需按子目录再查
```
分支不是 main 就换 master（或先拿 `GET /repos/{o}/{r}` 的 default_branch）。

### 3. 批量抓取文本文件（跳过二进制/图片）
```powershell
$dst = "$env:TEMP\repo_src"; New-Item -ItemType Directory -Force -Path $dst | Out-Null
$files = @('package.json','src/index.ts','docs/usage.md', ...)  # 从文件树挑文本类
foreach ($f in $files) {
  $name = $f -replace '/','__'   # 避免路径冲突
  curl.exe -s -L -A "Mozilla/5.0" "https://raw.githubusercontent.com/{owner}/{repo}/main/$f" -o "$dst\$name"
}
# 下载后核对 Length 是否与 tree.json 的 size 一致，防空文件/404 壳
```

### 4. 本地分析
`read_file` 逐个读。重点文件优先级：package.json（依赖/脚本/入口）→ 入口 index.ts → 核心实现（最大源文件）→ docs/usage.md（工作原理）。

### 5. 拉 README（评估第一手材料，2026-08-16 实测）

```powershell
curl.exe -s -H "Accept: application/vnd.github+json" -H "User-Agent: hermes-agent" "https://api.github.com/repos/{owner}/{repo}/readme" -o readme.json
# 解析: content 字段是 base64 —— python: base64.b64decode(json.load(open(f))['content']).decode('utf-8')
```

坑：API 偶发 5xx（body 是 169B 的 `{"message": "No server is currently available..."}`）——**不是仓库不存在**，sleep 3s 重试一次即可；404 与 5xx 都是小 JSON，先读 `message` 字段再判断。

### 6. 第三方插件/仓库安全审查流程（2026-08-16 实测玄枢/dsh-market/hermes-dsh-collab）

下载 → 解压 → 双路扫描 → 逐条甄别 → 结合元数据出结论：

1. **下 zip 解压**：ghfast.top 下 `archive/refs/heads/{default_branch}.zip` → `Expand-Archive`
2. **危险模式扫描**（search_files 内容搜索，path 指向解压目录，output_mode=content）：
   - 外传通道：`fetch\(['"]https?://|https?\.request|axios|XMLHttpRequest|WebSocket`
   - 命令执行：`child_process|\.exec\(|\.spawn\(|eval\(|new Function`
   - 敏感数据：`\.ssh|\.env|api[_-]?key|token|secret|password|credential`
3. **逐条甄别匹配（关键！匹配≠有罪）**：
   - JS 正则 `.exec(` ≠ shell exec；`fetch('/相对路径')` 是加载本地资源 ≠ 外传；e2e 测试里的 `BASE_URL=127.0.0.1`、test 文件里的 spawn 不算运行时行为
   - 本次玄枢 7.9MB 实测：5 处匹配全无害（本地 JSON fetch + 正则 exec），生产代码零外传零命令执行 → 审查通过；README 声称"离线优先、无远程服务端"与代码一致
4. **元数据交叉验证**：stars/forks（社区验证）、pushed_at（活跃度）、created_at（1 天前=太新，风险高）、根目录有无 LICENSE 文件（API license 字段空≠没 license，README 可能声明 MIT，以文件树为准）、README 声明是否与代码一致
5. **结论分级**：纯文档技能包（只有 SKILL.md+references，无执行代码）→ 风险极低直接装；有可执行代码但扫描干净 → 可装但小范围试用；1★/刚建/无 LICENSE → 标注风险，让用户决策
6. **装第三方插件永远提示安全警告**：插件权限与用户本人相同（能读文件/用凭据/访问网络），工具审批管不到插件自己的代码

## 失败路径记录（别重复踩）

1. **git clone 挂**：`Failed to connect to github.com port 443 via 127.0.0.1` —— 不是节点问题，是 git 全局残留坏代理 `http.proxy=127.0.0.1:443`。诊断：`git config --global --list`。修：`git config --global --unset http.proxy`。
2. **codeload tarball 直连超时**（120s 卡死）→ 放弃。
3. **走 Clash 代理下 tarball**：拉起内核切「新加坡 01 | 专线」后 `SSL: UNEXPECTED_EOF_WHILE_READING` —— 专线节点下载大文件也被掐。→ 回到方案：tree API + raw 逐文件（全程直连，0 代理开销）。
4. **GitHub contents API 逐个查文件会 404 且慢**（路径含特殊字符要编码）——不要用它，用 raw + tree 组合。
5. **gh-proxy.com / ghproxy.net 代理网页必 403**：Cloudflare WAF 拦（"Access Denied" 页带 Ray ID）——网页内容别走它们，只有文件下载偶尔可过。
6. **gitcode.com 是 JS 渲染壳**：curl 拿到的是 `<div id="app"></div>` + bundle JS，热门/探索内容爬不到（要数据用 api.github.com，要页面用 agent-browser 渲染）。

## 分析报告套路（使用者偏好）

- 状态图标表格对比：维度/情况/评价
- 先亮硬数据（star/语言/时间/大小），再讲代码质量证据（错误处理/状态机/锁/安全），再吐槽（README 与仓库不符、缺 LICENSE、rc 依赖不稳定）
- 结尾给"对你有什么用" + 行动建议（收藏观望 vs 装来试玩）
