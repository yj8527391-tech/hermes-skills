# 成熟「Agent 像素办公室」项目架构知识库

面向：给 AI agent 做像素风状态看板 / 办公室（角色走动、坐工位、与家具交互）。
本文件是**调研摘要**（2026-09），不是逐行镜像——要细节回原仓库看。

## 0. 怎么在国内拉到这些源码

github.com 网页常被墙，但 **api.github.com 稳定可达**（网页搜索后端不稳时更可靠）：

```bash
# 搜同类项目
curl -s "https://api.github.com/search/repositories?q=openclaw+office+pixel&sort=stars"

# 列目录
curl -s "https://api.github.com/repos/<owner>/<repo>/contents/<path>" \
  | python -c "import json,sys;d=json.load(sys.stdin);[print(x['type'],x['size'],x['name']) for x in d]"

# 取文件内容（base64 解出）
curl -s "https://api.github.com/repos/<owner>/<repo>/contents/<file>" \
  | python -c "import json,sys,base64;d=json.load(sys.stdin);print(base64.b64decode(d['content']).decode('utf-8','replace'))"
```

备选镜像：`https://ghfast.top/https://github.com/...`。

## 1. 项目清单（2026-09 实测）

| 仓库 | ★ | 技术栈 | 对我们的价值 |
|:--|--:|:--|:--|
| `ringhyacinth/Star-Office-UI` | 7481 | Phaser + Flask | **最成熟的动画范式**：spritesheet 逐帧 |
| `xmanrui/OpenClaw-bot-review` | 2014 | Next.js + 单张 Canvas 2D（零第三方库） | **Pixel Office 模块**：座位/交互点自动推导、浮点 zY |
| `shengyu-meng/ClawLibrary`（龙虾图书馆） | 455 | TypeScript + Vite | **数据驱动**：rooms/walkgraph/图层/工作输出协议 |
| `ruiqili2/agent-monitor` / `thx0701/openclaw-virtual-office` / `SweetSophia/openclaw-pixel-agents` | 24–55 | 各异 | 备选参考 |

> 美术素材注意版权：Star-Office-UI 代码 MIT，但**素材标注 non-commercial learning only**，别直接搬。

## 2. Star-Office-UI：逐帧 spritesheet（动画正解）

`frontend/game.js`：

```js
this.load.spritesheet('star_idle', '...', { frameWidth: 128, frameHeight: 128 });
this.anims.create({ key:'star_idle',
  frames: this.anims.generateFrameNumbers('star_idle', { start:0, end:29 }),  // idle 30 帧
  frameRate: 12, repeat: -1 });
this.anims.create({ key:'star_researching', frames: (... end:95), frameRate:12, repeat:-1 }); // working 96 帧
```

- 帧都是 128×128，横向排成一张图，`frameRate:12`
- 配套工具 `gif_to_spritesheet.py`：**GIF → 单行精灵表**，缩到 `target_height=64`（`NEAREST`）
- 另有 `repack_star_working.py` / `webp_to_spritesheet.py` → 素材是 **webp**（体积小）

**结论**：想要「星露谷级」动画就得走 spritesheet；AI 单张生成难保证帧间一致，所以**退路是「多方向静态图 + CSS 分层动画」**（见 SKILL.md 对应小节）。

### 若以后要自己做走路帧（图集规格，直接照抄）

```
一个角色 = 112×96 一张图
  = 7 帧 × 16px 宽 × 3 行（行 = down / up / right）
  行内帧序：walk1, walk2, walk3, type1, type2, read1, read2
左向不单独出图：用 transform: scaleX(-1) 镜像
```

## 3. ClawLibrary：数据驱动的场景协议

`src/data/map.logic.json`（v6 schema）——**逻辑与视觉分离**：

```json
{
  "meta": { "baseResolution": { "width": 1920, "height": 1080 } },
  "renderLayers": [
    {"id":"floor","depth":1}, {"id":"back_walls","depth":8},
    {"id":"mid_props","depth":20}, {"id":"actor","depth":30},
    {"id":"fg_occluder","depth":50}, {"id":"fx_overlay","depth":70}
  ],
  "rooms": [
    {"id":"document","label":"Document",
     "bounds":[430,650,370,250],                      // x, y, w, h
     "labelAnchor":{"x":666,"y":664}},
    {"id":"memory","label":"Memory","bounds":[50,95,500,430], ...},
    {"id":"mcp", ...}, {"id":"images", ...}, {"id":"log", ...}
  ]
}
```

要点：**`actor:30` 夹在 `mid_props:20` 与 `fg_occluder:50` 之间** → 角色天然会被前景遮挡物盖住；
每个房间有自己的 `bounds` 与 `labelAnchor`（贴房间名用）。

`src/data/work-output.protocol.json` —— 工作状态语义（**气泡/输出分类的现成模板**）：

```json
{"outputCategories":[
  {"id":"document","label":"Document","summary":"Specs, handoff notes, research drafts",
   "sampleContents":["architecture delta","handoff note","delivery checklist"]},
  {"id":"images","label":"Images","summary":"Scene slices, generated art, screenshots", ...},
  {"id":"memory","label":"Memory","summary":"Daily logs, durable notes", ...},
  {"id":"skills", ...}, {"id":"gateway", ...}
]}
```

其他运行机制（README）：`map.logic.json`（房间/锚点/步行图/工作区）、`asset.manifest.json`、
`scene-art.manifest.json`（角色↔美术绑定）、`scripts/openclaw-telemetry.mjs`（状态桥接）、
QA 命令 `npm run qa:movement` / `qa:visual`（还有 `remap.html` 做布局标定）。

## 4. OpenClaw-bot-review：Pixel Office 模块

- **渲染**：单张 Canvas 2D，**零第三方库**，手写 rAF 循环；`MAX_DELTA_TIME_SEC = 0.1` **钳制 dt**（照抄）
- **精灵**：`string[][]` 十六进制色格 → 逐像素 `fillRect` 进**离屏 canvas 缓存**（不是 CSS，也不是 `<img>`）
- **状态机**：唯一外部输入 `isActive` → 推导 `idle / walk / type` 三态。
  WALK→TYPE 到位时把 `dir = seat.facingDir` 并吸附到座位坐标。
- **座位自动推导** `layoutToSeats()`：从**椅子家具**推出座位，朝向优先级 **椅子 orientation > 相邻桌 > DOWN**；
  带 `assigned` 借位登记（防两人抢一座）。
- **交互点自动推导** `getInteractionPoints()`：把可交互家具的**下 / 左 / 右三侧可走格**变成交互点；
  闲逛时 **60% 概率**选一个走过去，到位转身面向家具并停留 **5~15s**；再加「摸鱼 3~6 次回座位休息」的双计数器节奏。
- **家具「通电」**：工作中且面朝桌子时，把家具换成「通电变体」（屏幕亮 / 台灯亮）——很便宜的观感细节，值得抄。
- **排序**：所有 drawable 按**浮点 `zY`** 排序（`drawables.sort((a,b)=>a.zY-b.zY)`）。
  ⚠️ DOM 方案只能用**整数 z 分档**，做不到精确交错；4 角色场景够用，真需要精确交错就把角色+家具画进同一张 canvas。
- **素材**：`public/assets/pixel-office/characters/char_N.png`，一格图集 112×96（见上 §2 规格）。
- 额外可借鉴的看板功能：摸鱼排行榜、Token/响应时间 SVG 统计、GitHub 风格热力图、会话/技能管理、
  告警中心+飞书推送+提示音、Gateway 日志与一键重启、平台连通测试、布局编辑器、i18n/主题/刷新档位。

## 5. 把上面的思路落到「单文件 HTML + DOM」的取舍

| 能力 | Canvas 方案（它们） | DOM 方案（我们） |
|:--|:--|:--|
| 帧动画 | spritesheet 逐帧 | 多方向静态图 + CSS 分层动画（`clip-path` 点头/摆手） |
| 遮挡排序 | 浮点 `zY` 精确排序 | 整数 z 分档（2/3/4/5）+ **桌沿遮挡片** |
| 座位 | 从椅子家具推导 | **写死锚点**（背景图是固定图，不需要网格推导） |
| 交互点 | 家具三侧可走格 | 写死命名点（书架/窗边/门口/闲聊） |
| 走到位 | 插值 + 吸附 | `walkTo()` 线性插值 + `onArrive` 回调切姿态 |

> **瓶颈不是算法，是背景图没有椅子** → 「坐」只能靠「桌沿裁切下半身 + 背面视图 + 打字微动 + 屏幕亮」四件事共同暗示。
> 想更到位就再生成一张 `{k}_sit.png`（侧坐/背坐）。

## 6. 给背景图量几何（写锚点前必做）

把渲染好的截图丢给 VLM，一次问全**可复算的几何**（%）——然后换算成 `SPOTS` / 遮挡片坐标：

> 以场景区为 100%×100%：窗户矩形 / 墙地交界线（注意**可能是斜的**）/ 每张桌的桌面范围 / 显示器位置 /
> 书架范围 / 吸顶灯位置 / 「可站立的平地」左右下边界

本项目实测（`bg_autumn_day.png`，960×460）：

```
窗户      x 125–445, y  98–290
墙地交界  左 y≈380 → 中 y≈360 → 右 y≈350（斜的）
桌1 桌面  x 295–515, y 305–330   （桌腿到 y≈395）
桌1显示器 x 370–430, y 268–312
桌2 桌面  x 520–680, y 305–330
书架      x 675–940, y 145–350
可走前景带 y 385–460 全宽；整个木地板 y 360–460
```

→ 直接推出：`SC = {H:460, BACK:358, FRONT:436}`、桌沿遮挡片 `left:288 top:328 w:404 h:74`。

**加一个调试开关**：按 `G` 切 16px 网格叠层，点击场景打印 `x=/y=/bottom=` 便于把坐标粘进锚点表。
