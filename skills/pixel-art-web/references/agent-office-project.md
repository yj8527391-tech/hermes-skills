# 像素办公室项目设定（主人专属）

> 主人 2026-09 定的方向：把 Hermes agent 的运行状态可视化成**像素风办公室**，自研，不走现成 OpenClaw 生态方案。

## 角色 roster（2026-09 主人发参考图重定，别自作主张改）

主人发来三张参考图指定形象，已按图提取配色/比例后重绘：

| 形象 | 对应 | 参考图特征 → 点阵设计 |
|:--|:--|:--|
| **企鹅连体帽服少女** | **助手**（主 agent，自己） | 黑发#1f1f2e、蓝眼#7ec0ee、企鹅服深灰+白肚#f7f7f7+黄嘴/脚#f4c430；2头身 → 点阵 **24×32** |
| **doro 粉发团子猫** | 子 agent（delegate_task） | 粉发#f5a9c7、紫瞳#a88bdb、灰蝴蝶结、:3 嘴；1.5头身团子 → 点阵 **20×24** |
| **钢铁侠（Iron Man）** | codex | 主人 2026-09 补了参考图：红#CC3333+金#E6B800+黑轮廓#111111、黑色眼带+白点眼、胸口方舟反应堆 → 点阵 **20×20** |
| **蓝发鲸鱼兽耳女仆** | dsh（DeepSeek Harness，蓝鲸配 DeepSeek 的鲸鱼 logo） | 蓝发#4a9eff、呆毛、女仆头箍、白围裙#eef5ff、藏蓝裙#22376b、鲸鱼尾；→ 点阵 **20×24** |

> ⚠️ 主人 2026-09 纠正过：「像素密度提高，现在好丑啊」→ 所有角色已从初版 12×14/16×20 **升级到上表尺寸**（格宽 3px）。别再回退。

> 参考图获取路径：主人发到微信/飞书的图会缓存到 `hermes-home/cache/images/img_*.jpg`，
> 或从飞书 API 拉（见 feishu-file-send 技能的「读取消息/下载图片」段）。缓存文件名是 hash，
> **不能假设与聊天里的图片顺序或编号一一对应**，按内容（VLM 描述）判断哪张是哪个角色。

## 项目路径与进度

- 目录：`E:\pixel-office\`（英文名，避免中文路径在脚本里的编码坑）
- `prototype/characters.html` —— 四角色静态原型（点阵+呼吸/打字动画+木地板/办公桌/显示器场景）
- `backend/app.py` —— **Flask 状态推断服务**（端口 8899，`/api/status`、`/api/health`）
- `frontend/index.html` —— 像素办公室主页面（HUD 状态栏 + 场景 + 四角色 + 2 秒轮询 + 状态卡片）
- 已验证：后端能实时吐出主 agent 状态（`working · receiving stream response · 消息789条 · 工具310次`）
- 交付方式：改完截图（`--virtual-time-budget=9000`）→ 发飞书

## 数据源（做「谁在干活」用，已实测）

| 来源 | 用途 |
|:--|:--|
| `hermes-home/state.db`（SQLite，`mode=ro` 打开） | 主数据源：会话/消息/工具调用 |
| `http://127.0.0.1:9120/api/status` | 全局健康（gateway_state、平台连接、active_sessions），匿名可用 |
| `cache/delegation/live/<id>/task-N.log` | 子 agent 实时 transcript（细粒度进度） |

关键字段与判定：

- **`sessions.last_activity_description`** = 现成的「现在在干什么」人话串（实测值：`starting API call #1`、
  `tool completed: terminal (32.2s)`、`context compression completed`、
  `delegate_task: subagent waiting for non-streaming API response (iteration 28/250)`）。
- **`session_turn_leases.expires_at > now`** = 正在生成（活跃租约），TTL≈300s；这是最硬的「RUNNING」信号。
- **`async_delegations.state='running'`** = 有子 agent 在场（→ doro 出现在办公室）。
- `sessions.source` 取值：`desktop` / `feishu` / `weixin` / `tui` / **`subagent`**；判主会话要 `source != 'subagent'`。

⚠️ **语义坑**：`last_activity_at` **不是**滚动时间戳——活动持续期间不推进，只在活动*改变*时更新。
所以 `now - last_activity_at` ≈ 当前这一步已跑多久，**不能当「空闲多久」**。判空闲要结合租约与描述变化。

## 候选方案与取舍（2026-09 调研结论，别重复调研）

| 项目 | 值 | 结论 |
|:--|:--|:--|
| Claw3D | 2.2k★ MIT 活跃 | **唯一原生支持 Hermes**（内置 WebSocket adapter，`npm run hermes-adapter`），但要 Hermes 起 HTTP API（文档写 `:8642`，而 Hermes `serve` 是 `:9119` JSON-RPC → 端口/协议不匹配，需适配） |
| my-virtual-office | 326★ AGPL | 也支持 Hermes（走 Hermes API Server + SSE），需 Docker（本机未装） |
| **Star-Office-UI** | **7.4k★**，代码 MIT / 美术素材 non-commercial only | 像素风看板，6 状态→3 区域映射、服务端 auto-idle TTL 300s。**主人 2026-09 明确认可参考它**（「可以参考优秀的 OpenClaw 代码，不然这样纯原创太难了」）。技术栈：**Flask + Phaser**；角色动画走 **spritesheet**（`frontend/cats-spritesheet.webp` + `game.js` 播放），配 `gif_to_spritesheet.py`（GIF→单行精灵表，目标高 64px，NEAREST 缩放）。**素材不能直接用**（授权限制 + 形象不符），但**精灵表工作流值得照搬** |
| OpenClawfice | 74★ 停更 | 读 session transcript 尾部（64KB→40 行）推断状态，思路可抄；强依赖 OpenClaw |
| ~~ali-musafir/openclaw-office~~ | — | **仓库不存在（404）**，别再用 |

## 增强层

- ✅ **环境同步已落地（2026-09-21）**：`/api/environment` 接口（真实时间时段 + open-meteo 天气/温度），
  前端用 `body[data-phase]` 切时段色调、窗外日月云、雨雪覆盖层、夜晚自动开灯；支持 `?phase=` / `?weather=` URL 预览参数。
  手法见 pixel-art-web 主文档「让看板与现实同步」。坐标默认昆明（25.04, 102.71）。
- ✅ **角色美术改走火山方舟 AI 图**：主人 2026-09 定「用我发给你的图去投喂」→ seedream-5.0 图生图（1920×1920）→ 缩 320×320。
  产物：`E:\pixel-office\assets\ark_*_320.png`、`characters4_final.png`；脚本：`backend/ark_i2i.py`、`ark_restyle.py`、`shrink_ark.py`、`gen_sheet4.py`；
  原图在 `refs\ark_*_pixel.png`。手绘点阵版（`alice_320.png` 等）仍保留作备选。调用细节与「多角色统一画风」坑见 `cn-multimodal-apis` 技能。
  像素化 320×320 交付用 `scripts/render_pixels_png.py`。
- ✅ **前端精灵已换成 AI 图（2026-09-21）**：`frontend/index.html` 里四角色的 `div.px` 点阵 → `<img class="sprite">`，
  加载 `frontend/assets/ark_*_v2_t.png`（白底已抠透明 + 裁边；⚠️ 必须用 `backend/trim_sprites2.py`
  的 **flood fill 版**——早期 `trim_sprites.py` 的全局阈值去白会把角色**身上的白**（企鹅白肚 / 白围裙 /
  白項圈 / 白眼圈）一起抠成透明，主人 2026-09 直接反馈「**人物白色都不见了**」）；
  动画仍走原 class（`breathe`/`typing`/`bob`/`patrol`），JS 未改。图必须放 `frontend/assets/` 才被 Flask 服务。
- 🔄 **四季背景（2026-09-21）**：`backend/gen_bg.py` 生成 `backgrounds/bg_{spring,summer,autumn,winter}.png`
  （seedream-5.0，`2560x1440`，白墙 + 木地板 + 窗外按季节变），已接入 `body[data-season]` 切背景
  （图拷到 `frontend/assets/bg_*.png`）。
  ⚠️ **首版踩坑**：四张独立文生图 → 房间布局/墙色/显示器款式各不相同，VLM 判「四季像换了个房间」。
  改用 `backend/gen_bg_v2.py`（**以 spring 为参考图做图生图**，prompt「keep this EXACT same office room… only
  change the window view」）生成 `bg_{season}_v2.png` —— 结论：**同一场景出变体必须走 i2i，不能靠文生图**。
  ⚠️ **背景图接入三坑**：① 旧 `body[data-phase] .scene{background:linear-gradient}` 会盖掉背景图，必须删、
  时段色改走 `.scene::before` 叠加层；② 旧手绘元素 `.window/.floor/.desk/.monitor/.plant/.coffee` 要
  `display:none`；③ 显式 z-index（叠加层1/灯2/角色4/雨雪6/气泡8）。离线角色 opacity 从 0.3 提到 **0.55**
  （太淡主人会以为没渲染）。
  后端已加 `season_of()`（按月份）并支持 `?lat=&lon=&gps=1` 覆盖坐标（天气缓存已改为按坐标做 key）；
  前端已加 `navigator.geolocation` 取真实坐标（失败回落昆明）。
- 🔄 **角色多视图 + 自由走动（2026-09-21 主人新要求，进行中）**：主人要求「人物可以自由的活动」+
  「每个人物都需要有三视图，他们转身那些都要有」。方案：seedream-5.0 **逐张图生图**生成每角色
  4 方向（front/back/left/right）→ 前端按朝向切图 + 位置移动 + 转身。脚本 `backend/gen_views.py`
  （4 角色×4 方向=16 张，输出 `views/<char>_<view>.png`，用角色 320 原图做参考图保形）。
  ⚠️ **视频路线已排除**：火山方舟 seedance 视频模型（lite-t2v / lite-i2v / pro）在该账号
  **全部未开通或不存在**（`ModelNotOpen` + `InvalidEndpointOrModel.NotFound`）——无法用「视频→抽帧」做动画。
- 🔄 **v3 背景（显示器比例 + 夜景）**：主人反馈「电脑还是太大了」+「窗外的景色还是白天」→
  `backend/gen_bg_v3.py` 重出 8 张（4 季 × 白天/夜晚），白天版 prompt 加 `TWO SMALL compact computer
  monitors … about the size of a desk book`；夜晚版 prompt 写 `AT NIGHT … ceiling lamp GLOWING warm
  yellow … the rest of the room is dim and dark blue`。「人物動效」不是原地拟揺，要的是**自主移动**。
- 待办：Kimi API 生成旁白/气泡文案。⚠️ Kimi 是推理模型，`max_tokens` 给 500+，否则 token 全被 thinking 吃掉、`content` 返回空
- 待办：一键启动 bat / 开机自启
- 待办：场景细化（茶水间、猫爬架、显示器滚动代码）

- ✅ **走动系统 2.0 已上线（2026-09-21）**：放弃 `area` 矩形 + CSS `transition`，改为
  **SPOTS 命名锚点**（`seat_a1/a2/b1/b2` + `ix_shelf/ix_window/ix_door/ix_chat`）+ **三态状态机**（idle/walk/sit）
  + **透视缩放**（工位层 0.78，地板层 0.86~1.0）+ **`requestAnimationFrame` 主循环**（`dt` 钳制 0.1s）
  + **桌沿遮挡片 `.desk-front`**（把背景图桌沿原样再画一遍盖下半身）。
  z-index 阶梓：坐着角色 2 < 桌面屏幕 3 < 桌沿遮挡 4 < 前景角色 5 < 雨雪 6 < 气泡 12。
  ⚠️ 主循环函数名必须是 `gameLoop`（原名 `tick` 与顶层 `let tick=0` 重名 → 整页 `<script>` 编译失败）。
  手法见主文档「走动系统 2.0」。
- ✅ **子agent 数量可视化已上线（2026-09-21）**：主人「dora 的数量和子agent的数量要对应，可以变成几个更小的
  dora 在桌子上」→ 后端 `/api/status` 的 `cats` 字段（`async_delegations` 里 `state='running'` +
  `sessions.source='subagent'` 近 60s 活跃）+ 前端 `renderMiniCats()` 元素池渲染 → 桌上出现
  `cats.length` 只 **46px 小 doro**（封顶 6 只），各自头顶小气泡显示负责的 task 摘要（截 9 字）、
  跳动相位错开。容器 `#mini-cats` 写在 HTML 里。代码模板见主文档。
- 🔄 **角色尺寸定稿 105px（2026-09-21 主人拍板 B）**：从 84px → 122px → 最终 **105px**
  （≈美术隐含比例 168px 的 62%，Q 版甜点区）。子角色相应：doro 92 / codex 100 / dsh 100。
  ⚠️ 两种量法差一倍（VLM 估「桌高占场景%」反推 ≈72–84px；按背景图桌子实测像素 0.75m=74px 反推 ≈168px），
  以后者为准再乘 Q 版系数。
- 🔄 **待办：CSS 像素椅子（主人 2026-09-21 最新反馈）**：主人原话「人物坐到椅子上办公的样子，他下半身
  都没有了」。根因：背景图（AI 生成的）**没有椅子**，之前的「坐」全靠 `.desk-front` 遮挡片把下半身盖掉，
  硬边齐腰截断 → 静态一瞥能骗过、盯住看就露。方向：用纯 CSS 补一把像素椅子（椅背+坐垫+腿），
  插在「坐着的角色」(z=2) 与「遮挡片」(z=4) 之间（≈z=3.5），四个工位各一把。
- 🔄 **主人 2026-09-21 一次性提的 6 条反馈**（做完划掉）：① 光源形状要贴像素图案（月晕贴月、灯光贴灯，
  不要一律正圆；白天窗外无太阳就**不要明显光源**）；② 坐椅子下半身消失；③ 画布遮挡有问题；
  ④ 绿色屏幕没对上台显示器（背景图有**两台**）；⑤ 工作时屏幕上要出现画面；⑥ dora 数量对应子agent（✅ 已做）。

## 自己踩过的坑

| 坑 | 解法 |
|:--|:--|
| 进程检测假阳性（codex/dsh 永远显示工作中） | 查询命令的命令行里就含 `codex|dsh` 字样 → 搜到自身。必须排除查询进程行（含 `Get-CimInstance`/`CommandLine`）并改用精确正则（`codex\.cmd`、`npm-global[\\/]dsh`） |
| 读进程列表 UnicodeDecodeError | `subprocess.run(..., text=True, encoding='utf-8', errors='replace')` — PowerShell 输出是 GBK，不带 errors 会崩线程 |
| state.db 被 Hermes 占用 | 一律用 `sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=3)` 只读打开 |
