---
name: pixel-art-web
description: Use when 做像素风网页/角色/看板。字符串点阵+CSS grid。
version: 1.0.0
author: Alice
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [pixel-art, css, sprite, retro, web, animation]
    category: creative
---

# 网页像素画（字符点阵 + CSS Grid）

## 何时使用

- 使用者要「像素风」的网页 / 看板 / 角色 / 办公室 / 小游戏画面
- 要快速出可交互的像素画面，但不想引入图片素材或游戏引擎
- 原型阶段要先看到效果再细化

## 核心手法：字符串点阵 + 调色板

一个字符 = 一种颜色，`.` = 透明。改画面就是改字符串，不用编辑器不用素材：

```js
const PALETTE = {'A':'#ff9f43','B':'#ffe0bd','D':'#222','.':null};
const ALICE = [
  "..AAAA..",
  ".ABBBBA.",
  ".ABDBDA.",
  "..BBBB..",
];
```

渲染进 CSS Grid（每格固定像素），**别用 1px 格**（会糊）：

```js
el.style.gridTemplateColumns = `repeat(${cols}, 4px)`;
el.style.gridTemplateRows    = `repeat(${rows}, 4px)`;
el.innerHTML = art.flat().map(ch =>
  `<i style="background:${PALETTE[ch] || 'transparent'}"></i>`).join('');
```

- 容器加 `image-rendering: pixelated`，缩放时保持硬边
- 角色/精灵用绝对定位叠在场景层（`position:absolute; left/bottom`）
- 场景地砖用 `repeating-linear-gradient` 拼，比贴图省事

## 动画：CSS 就够，别上 canvas

- 呼吸：`@keyframes breathe { 50% { transform: translateY(-2px) } }`
- 打字抖动：左右 ±1px 的高频 keyframes
- 多帧/走动：**换下一帧的点阵数据**即可，等价于手写精灵表
- 状态切换：JS 换 class，动画交给 CSS（别用 JS 每帧改 DOM）

## 交付前一定先截图给使用者看

使用者看不了本地文件 → 一律截图发过去。**没有 Chrome 也能截**，用 Edge 无头（零依赖）：

```
"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --no-sandbox \
  --hide-scrollbars --virtual-time-budget=9000 \
  --screenshot="E:/out.png" --window-size=1010,920 "file:///E:/page.html"
```

⚠️ **必须是 `--headless=new`**（2026-09 实测）：旧的裸 `--headless` 会**静默产出 0 字节文件**——
命令 `exit 0`、不报错，只有 `stat -c%s` 才发现是空的。旧写法在本机是**失效**的，别从旧笔记里抄回去。
**截完必查文件大小**（`ls -la` / `stat`），不要只看 exit code。

**关键参数 `--virtual-time-budget=N`（毫秒）**：页面里有 JS 或 `fetch` 轮询时，普通截图会抓到
渲染前的空壳；这个参数会先让页面跑 N 毫秒再截。取 `file://` 本地页和 `http://127.0.0.1:端口/` 都一样适用。
（只靠 `sleep 2-3 秒再取文件` 不可靠——截图进程早退了。）

再发飞书：`python <本技能目录>/scripts/feishu_send_media.py E:/out.png`
（需先设 `FEISHU_CHAT_ID=oc_xxx`，否则脚本拒绝执行；发图走 `/im/v1/images`，
与发文件不是同一个接口 —— 更多飞书 API 细节见 `feishu-file-send` 技能）

「截图 → 发图 → 收反馈 → 改点阵」这个循环，比让使用者自己开文件快得多。

**使用者想要「实时的」而不是截图时**：把 Flask 从 `127.0.0.1` 改成 `host="0.0.0.0"` 即可局域网访问
（`ipconfig` 取 WLAN 的 `10.x` / `192.168.x` 地址），改完本机自测 `curl http://<局域网IP>:<端口>/api/health`
必须返回 `{"ok":true}`。
但**别急着承诺「手机能看了」**，中间有两道常见的坎：① 公用／校园网（实测 `YNART-WIFI`）常开 **AP 隔离**，
同一 WiFi 的设备之间也互访不了；② Windows 防火墙可能对 `python.exe` 有**阻止入站**规则，改它需要管理员权限。
两道坎任一存在，就**直接退回截图发使用者**——这是不依赖网络环境、100% 可交付的路径。

## 照参考图重绘（使用者发图后要像素化）

使用者常会丢一张角色参考图说「照这个做像素画」。流程：

1. **先用视觉模型读图**（自己模型不支持图像时，直接调 Kimi：`kimi-k2.7-code` 支持 image_in，
   把图 base64 塞进 `content` 的 `image_url` 块）。
2. 让 VLM 只吐**可复现的硬信息**（这是关键提示词设计）：
   > 角色是什么／主要配色（尽量给 hex，如 粉发#F5A9C7、紫瞳#A88BDB）／
   > 服装配饰／头身比（如 2头身）／显著特征（耳朵尾巴蝴蝶结呆毛）／整体风格。分点，每点≤30字。
3. 把 hex 直接写进 `PALETTE`，头身比决定点阵高度（1.5头身≈12×14，2头身≈16×20），特征项做成 1-2 个像素特征块。

⚠️ **多角色配色表必须字母唯一**：同一 PALETTE 里两个角色用同一字母表不同颜色，后者会覆盖前者
（实测：dsh 的眼睛用了企鹅白的 `W`，结果眼睛变白）。要么每角色字母不重叠，要么每角色独立 palette。

## 设计要点

- 调色板控在 **8-16 色**；色一多就退化成低分辨率插画，不像像素画了
- ⚠️ **密度别抠**（使用者 2026-09 明确纠正：「像素密度提高，现在好丑啊」）：
  - 主角（助手这种门面角色）**≥24×32**；配角 **≥20×24**；格宽 **3px**
  - 12×14 / 16×20 那种只适合一次性草图，**别当成品交付**
  - 「细节丰富」和「保留关键元素」要同时满足：帽兜黄嘴、鲸鱼尾、蝴蝶结、呆毛、道具
    这类**识别性特征必须做成独立像素块**，宁可为它多加两行点阵，也不要为了工整削掉
  - 密度上去了，配套把 `draw()` 的 scale 降下来（4px→3px），否则角色会撑破场景
- 改密度时记得**同步挪站位**：角色变大后 left/bottom 要重排，别叠在桌子上
- 每行字符串**长度必须一致**，不够用 `.` 补满
- 角色辨识度靠三样：**发型 / 配色 / 道具**，不靠细节
- 中文界面配暖色调更讨喜；标题用无衬线 + 字间距

## 常见坑

| 现象 | 解法 |
|:--|:--|
| 画面糊 | 格子 <3px，或漏了 `image-rendering: pixelated` |
| 点阵错位 | 某行字符串长度不齐 |
| 截图空白 / **产出 0 字节文件** | ① 用 **`--headless=new`**（裸 `--headless` 会静默出 0 字节，exit 0 但不报错）；② 加 `--disable-gpu` + **`--virtual-time-budget=9000`**（JS 页必须，否则抓到渲染前空壳）；③ **截完必查文件大小** |
| 角色颜色串了 | 多角色共用 PALETTE 时字母撞车，改用互不重叠的字母 |
| 角色不像 | 减色、加大头部占比、强化一个特征道具 |
| 动画卡 | 改用 CSS transform，别 JS 逐帧改 DOM |
| emoji/字体不统一 | 像素画面里别混 emoji，用点阵字符表统一风格 |
| 使用者嫌「好丑/看不出是什么」 | 密度太低。升到 24×32 / 20×24、格 3px，并把关键特征（帽/尾/结/道具）做成独立像素块 |
| 手改大 HTML 点阵改坏了 | 别手敲；点阵放 .py 里校验等长，再用脚本按标记整块替换 |
| 旧服务杀不掉（`taskkill` 被 hardline blocklist 拦） | 自己起的后台服务一律用 `process(action='kill', session_id=...)` 关，别走 taskkill / `netstat`+kill 那套 |
| `python -c "..."` 里带 Windows 反斜杠路径 | 引号会被吃掉、报 `unterminated string literal`（`SyntaxError`）。**落成 .py 文件再跑**，别硬凑一行 |
| AI 精灵图贴出一块白底 | 生成图是白底不是透明。**从边缘 flood fill** 抠背景再 `getbbox()` 裁边（见「用 AI 生图替代手绘点阵」） |
| 抠完「人物的白色不见了」 | 用了**全局阈值去白** → 连角色身上的白（肚皮/围裙/眼圈）一起抠掉了。改成**从四边向内 flood fill**，只清与边缘连通的白 |
| 同一元素挂了两个动画却只动一个 | 两条 keyframes 都改 `transform` 时**只有一条生效**（同属性后被覆盖）。`typing`(translateX) 与 `workbob`(translateY) 不能并存 → 合并为一条，或每元素只留一个动效 class |
| 光斑/光束「写了却看不见」 | 淡色渐变打在浅木地板上极易被吃掉。不透明度提到 ~.85、`blur` 降到 2px；验收用 VLM 问「地板上有没有光斑」，别靠自己看 |
| 生成的多视图**背面其实是正面** | AI 把正面特征照搬到背面（实测：企鹅白肚长到背上、钢铁侠胸口的反应堆出现在背上）。重做时 prompt **显式否掉正面特征**：`Seen from directly behind: the BACK of the suit is SOLID BLACK — do NOT show any white belly` / `do NOT draw the glowing chest arc reactor — that is only on the FRONT` |
| 角色走到桌上 / 被家具挡 | 背景图的家具位置是 AI 画的、和预估对不上。把活动 `area` 压到**前景地板**（`bottom` 取小值）最保险 |
| 叠加的月亮与背景图自带月亮**变成双月** | 夜里背景图常常已经画了月亮。叠 `.moon-glow` 前先让 VLM 看一眼窗外有没有月亮，有就只做「增亮」不做「新增」 |
| 吸顶灯「像贴图」 | 矩形 + 纯色 = 贴图感。改**圆形** `radial-gradient` + 大范围 `box-shadow` 光晕，位置按 VLM 量出的 % 对齐；白天半透明、夜晚发光 |
| **气泡只给第一个角色显示了** | 把 `setBubble()` 写在了 `const hasCats/codexOn/dshOn` **之前** → TDZ `ReferenceError` 中断整个 `render()`。前面的角色已设置完，所以症状是「只漏了后面几个」，极易误判成 CSS 问题。**状态变量全部算完再统一设气泡**（挪到 render 末尾） |
| **气泡跟着角色一起变淡** | 未运行角色挂在 `.char{opacity:.55}` 上，会**连带子元素的气泡和名字标签**一起半透明。改成**只对 `<img>`**（`.sprite`/`.head-layer`）设 opacity，气泡/标签保持不透明 |
| 气泡不出现且不带报错 | 别用 JS `createElement` 动态造气泡（本会话踩两次）。**直接写进 HTML**，JS 只改 `classList` 和 `textContent` |
| **整页 JS 全失效**（状态栏全是「—」、角色不动、气泡全没、又没有报错） | 别怀疑 CSS / 选择器 / DOM 顺序——**整个 `<script>` 编译失败**了。一处 `SyntaxError` 废掉全脚本，表现却是「什么都没发生」。本会话根因：新增的 rAF 函数名 `tick` 与既有顶层 `let tick=0`（2 秒轮询计数器）**重名** → `SyntaxError: Identifier 'tick' has already been declared`。**新函数名一律加前缀**（`gameLoop`），改完必跑语法自检（见下「改完必跑语法自检」） |
| 屏幕上只覆盖了**一台**显示器 | 背景图里是**两台**显示器，只叠了一个 `.desk-screen` → 另一台还是背景自带的浅蓝。**每台各叠一层**，坐标各自量、各自定位（`#ds1` / `#ds2`），别一个矩形打天下 |
| 「坐下办公」被使用者识破为「**下半身都没有了**」 | 遮挡片硬边齐腰截断 = 一眼假（静态一瞥能骗过，使用者盯着看就露）。背景图没画椅子时**光靠遮挡片做不出可信的「坐」**。方向是**补一把 CSS 像素椅子**（椅背＋坐垫＋椅腿，纯 div/box-shadow），插在「坐着的角色」与「桌沿遮挡片」之间（≈`z-index:3.5`），角色坐垫高度与椅面对齐 |
| 光晕一律做成**正圆** | 使用者 2026-09 明确纠正：「**光源要符合对应的像素图案**，比如月亮的就要符合月亮的形状、灯的就要符合灯的形状」。别一个 `border-radius:50%` 的圆到处套：**先让 VLM 量出该物体在背景图里的实际轮廓与位置**，月晕贴月亮（月牙就做月牙形）、灯光贴灯罩，只做「增亮」不做「新增」（背景图已画了的物体别叠出双份）。白天窗外没太阳时**干脆不要明显光源** |

## 交付图导出（320×320 规范）

使用者要「形象的像素改成 320×320」时指的是**交付图片尺寸**，不是在页面上把角色显示成 320px：

1. **整数倍缩放**（`NEAREST`，绝不用插值——插值会让像素块发虚）
2. 缩到**高度贴住 320** 后，水平居中贴到 320×320 透明画布（点阵非正方形时留透明边）
3. 顺手拼一张四合一总览图（`1280×320`）发飞书，使用者一眼看全

可直接复用 `scripts/render_pixels_png.py`（内含上述全部逻辑 + 总览图拼接）。

## 点阵数据怎么安全写进大 HTML

页面到 15KB 后**别手改点阵**（行长度靠肉眼数必错）：

- 点阵先落在独立 `.py` 里，用脚本**校验每行等长**（`len(set(map(len, art))) == 1`）再写入
- 写入方式：脚本按注释标记定位（如 `// 助手：` 到 `PAL.T = `）做整块替换，而不是手工 patch
- 好处：改密度/换配色只跑一次脚本，不会漏行、不会把 HTML 改坏

## 让看板与现实同步（真实时间 / 天气）

看板类页面加「环境同步」很讨喜，而且零成本：**open-meteo 免费天气 API（无需 key）** + CSS 主题变量。
（使用者 2026-09 就要了这个：「背景我希望可以和现实同步」）

**后端**：加一个 `/api/environment` 接口

```
https://api.open-meteo.com/v1/forecast?latitude=25.04&longitude=102.71
  &current=temperature_2m,weather_code,is_day,cloud_cover&timezone=Asia/Shanghai
```

- 天气**10 分钟缓存**（别每秒轮询）；前端 60 秒拉一次即可
- 时段自己按小时划：5-7 dawn / 7-17 day / 17-19 dusk / 其余 night

**前端**：不要逐元素改样式，用 **`body[data-phase]` + 后代选择器/CSS 变量**一把切：

- `.scene`、窗户背景按时段给不同渐变，配 `transition: background 2.5s` 平滑过渡（避免突变）
- 太阳/月亮/室内灯用 `opacity` + 时段选择器切换；夜晚与阴雨天自动「开灯」（暖色 radial-gradient）
- 雨/雪做成覆盖层（`repeating-linear-gradient` 做雨丝、`radial-gradient` 做雪点，配 keyframes 位移），按状态切 `opacity`

**WMO weather code 分档**（映射成 晴/云/雨/雪 四态就够，不必细分）：

| 码 | 含义 |
|:--|:--|
| 0 | 晴 |
| 1-3 | 多云 |
| 45,48 | 雾 |
| 51-67, 80-82, 95-99 | 雨 |
| 71-77, 85-86 | 雪 |

**调试开关**：用 `?phase=night&weather=rain` 之类的 URL 参数覆盖真实值 → 不用等天黑就能截图验收，
4 时段 + 雨天一次截齐拼成对比图发使用者。

**验收**：拼多时段对比图让 VLM 复核「黄昏感够不够 / 窗外是否是日落 / HUD 有没有显示时间天气」。
实测常见不足：暖色只停在窗外、室内仍偏冷蓝；标籾在暗底上可读性差——提前加暖色余光/描边。

## 用 AI 生图替代手绘点阵（角色 / 场景）

点阵手绘适合快速原型；使用者嫌「不好看」时改走 **AI 生图**（火山方舟 seedream-5.0，调用细节见 `cn-multimodal-apis`），
再把生成图当 `<img>` 精灵用。切换成本极低：

- **页面里 `div` 换 `img` 就行**：`<div class="px breathe" id="px-alice">` →
  `<img class="sprite breathe" id="px-alice" src="assets/xxx.png">`；JS 里那些
  `classList.toggle('typing'/'bob')` **一行都不用改**（动画本来就是 CSS class 驱动的，跟标签无关）。
- `.sprite{display:block; height:80px; width:auto; image-rendering:pixelated;
  filter:drop-shadow(0 3px 0 rgba(0,0,0,.3))}` —— **只定高度、宽度自适应**，写死宽高会拉变形。
- 图片必须放在 Flask 的 `static_folder` 目录下（如 `frontend/assets/`）才被服务；放项目其他目录前端拿不到。
- **AI 图默认是白底、不是透明**，直接贴会顶一块白方块。先过这两步：

  ⚠️ **必须只清「外围背景」，不能全局按阈值去白**（2026-09 实测翻车）：角色身上的白（企鹅白肚、
  白围裙、白眼圈、白项圈）也是 >238 的近白 —— 全局去白会把它们**一起抠成透明**，使用者一眼就看出
  「**人物白色都不见了**」。正解是**从四条边向内 flood fill**，只清与边缘连通的背景白：

  ```python
  from collections import deque
  def strip_outer_bg(im, thresh=236):
      px = im.load(); w, h = im.size
      seen = [[False]*w for _ in range(h)]
      q = deque()
      for x in range(w): q.append((x,0)); q.append((x,h-1))
      for y in range(h): q.append((0,y)); q.append((w-1,y))
      while q:
          x, y = q.popleft()
          if x<0 or y<0 or x>=w or y>=h or seen[y][x]: continue
          seen[y][x] = True
          r,g,b,a = px[x,y]
          if r>thresh and g>thresh and b>thresh:      # 仅背景白
              px[x,y] = (0,0,0,0)
              q.extend([(x+1,y),(x-1,y),(x,y+1),(x,y-1)])
      return im

  strip_outer_bg(im)
  im = im.crop(im.getbbox())   # ② 裁掉四周空边（不裁的话角色在格子里显得很小）
  ```

  **验收**：抠完必须用 VLM 问一句「角色身上的白色部分（肚皮/围裙/眼圈）是否完整保留、背景是否透明」——
  这类缺陷肉眼看缩略图看不出来，使用者却一眼就发现。
- 同一形象**两套素材并存**（手绘点阵 + AI 图）当备选，别急着删旧版。

### 用 AI 背景图替换整块手绘场景（2026-09 实测三坑）

把 CSS 画的房间换成 AI 背景图，**不是加一条 `background-image` 就完事**：

1. **旧时段规则会悄悄盖掉背景图**：先前写的 `body[data-phase="dusk"] .scene{background:linear-gradient(...)}`
   与背景图规则同级、但位置更靠后 → 背景图永不显示。必须**删掉那几条**，时段冷暖改走**独立叠加层**
   `.scene::before{position:absolute;inset:0;z-index:1}` + `body[data-phase=...] .scene::before{...}`。
2. **手绘元素要显式关掉**：`.window,.sun,.moon,.cloud,.floor,.plant,.coffee,.desk,.monitor{display:none}`
   （背景图里已含房间，不关会双层重叠）。
3. **显式排 z-index**，别赌 DOM 顺序：叠加层 1 / 灯 2 / 角色 4 / 雨雪 6 / 气泡 8。角色不加 z-index 会被叠加层盖住。

另：**离线/未运行的精灵别调太淡** —— `opacity:0.3` 在暗背景上几乎看不见，使用者会以为角色没渲染；**用 0.55** 既表意（离岗）又可辨。

## 四季 / GPS：把「现实同步」再做深两层

在「时段 + 天气」之上再加这两层，同样零成本：

**四季**：后端按月份判（3-5 春 / 6-8 夏 / 9-11 秋 / 其余冬）→ 前端 `body[data-season]` 切背景图。
背景让 AI 直接生成四季各一张（`bg_{spring,summer,autumn,winter}.png`）：prompt 里把**不变的室内元素写死**
（`white walls` 白墙 / `light wooden plank floor` 木地板 / 桌 + 显示器 + 绿植），只换窗外景色
（樱花 / 浓绿 / 红叶 / 雪景）。

> ⚠️ **「同一场景只换一个元素」别靠独立文生图**（2026-09 实测）：prompt 把室内写死也没用，四次独立生成的
> 房间**墙色/窗框/显示器款式/整体色温全不同**，VLM 判「像换了个年代不同的房间」，切季节时房间会「跳」。
> 正解是**图生图**：拿第一张当参考图，prompt 用
> `Keep this EXACT same office room: identical walls, floor, furniture layout, desks, chairs, bookshelf,
> plant, lamp, window position and camera angle. Only change the view outside the window to: {view}.`
> —— 这才是 i2i 的强项（保形只改一处），和「风格转换」正相反（那边 i2i 帮倒忙，见 `cn-multimodal-apis`）。

> ⚠️ 宽幅背景的 size 用 **`2560x1440`** —— 正好 3,686,400 像素，卡着 seedream-5.0 的下限，且是 16:9。
> 时段冷/暖色一律用**叠加层**（`::after` 或覆盖层）来做，**别把冷暖画进背景图本身**，否则季节和时段会互相打架。

**GPS**（让坐标跟着使用者走，而不是写死城市）：

```js
navigator.geolocation.getCurrentPosition(p => {
  gps = {lat: p.coords.latitude.toFixed(4), lon: p.coords.longitude.toFixed(4)};
  pollEnv();   // 定位成功立刻带坐标重查一次
}, () => {}, {timeout: 8000, maximumAge: 600000});
// 请求时：fetch('/api/environment' + (gps ? `?gps=1&lat=${gps.lat}&lon=${gps.lon}` : ''))
```

- 后端天气缓存**按坐标做 key**（`(round(lat,2), round(lon,2))`），别用单一全局缓存（换城市会串数据）
- 定位只在**安全上下文**可用：`http://localhost` / `127.0.0.1` 可以，但 **headless 截图一律拿不到** → 必然回落默认城市，
  这是正常的，别以为代码写错了
- 授权失败/超时都要 **fallback 到默认坐标**，UI 上注明当前是「GPS 定位」还是默认城市

## 让人物「站得住」：物理校准 + 动作 + 光影

使用者 2026-09 的一串要求：「要考虑 3D 物理特性」「电脑和书架的比例要和人物比例差不多」「人物要会动啊，要有动效」
「窗边那些地方人物爬不上去的、违反现实物理的就改一下」「外面的阳光也要做到实时动效」「头顶的灯在晚上要打开」。

### 1) 先量几何，再定 px（别凭感觉调）

把渲染好的截图丢给 VLM，一次问全**可复算的几何**：

> 以场景区为 100%×100%：(a) 墙地交界线的垂直位置 %（地板顶沿）(b) 桌面离地占场景高 % (c) 书架高度 %
> (d) 吸顶灯位置（水平%、垂直%）(e) 窗户矩形（左/上/宽/高%）(f) 每个角色现高占场景高% 及位置
> (g)「可站立的平地」范围（左右下边界）

拿到就能算：

- **角色高度按真实比例反推**：`人/桌 ≈ 1.7m/0.75m ≈ 2.27`。
  ⚠️ **两种量法会差一倍，别只信一种**（2026-09 实测打架）：
  - ① 按 VLM 给的「桌高占场景 %」反推 → 场景 460px、桌高 7–8% → 人 ≈ **72–84px**
  - ② 按背景图里桌子的**实际像素高**换算（实测值：桌 0.75m = 74px）→ 人应 ≈ **168px**，即当时用的 84px 只有应有尺寸的一半

  两者对不上，是因为 ① 量的是**桌面以上的可见部分**，② 量的是**含桌腿的整体高度**。
  **最终以 VLM 复核为准**：改完高度后问一句「角色是否坐在桌后、肩在桌沿之上、髋被桌沿遮住」——
  这是「坐」成立与否的硬标准（桌上遮挡片只能吃掉看不见的部分：精灵太矮会**整个被桌沿片吃掉**，太高则**完全盖不住**）。
  **最终结论（使用者 2026-09 拍板 B）**：取 **105px**（≈美术隐含比例的 **62%**）——
  Q 版头大，拉到 168px 会显得"头巨大"；122px 在 460px 高的场景里又挤。**60–65% 是使用者认可的甜点区**。
  量法口径：❶用「含桌腿的整体高」（实测 桌 0.75m = 74px）反推真实比例→人 168px；
  ❷取该值的 **62%** 做 Q 版修正 → **105px**。改完仍以 VLM 复核「能否坐在桌后」定稿。
  VLM 反复判「角色太小、像摆件」时，多半就是踩了 ② 没对齐。
- **可站立区**＝墙地交界线到下沿（实测 y 276→451px ⇒ `bottom: 0~184px`），脚必须落在里面。
- ⚠️ **站前景地板最保险**：背景图桌椅在中景，把角色 `bottom` 压到 **20~90px 前景区**，绝不会「站到桌上」——
  VLM 对「站在桌面上 / 悬空 / 嵌墙」一律判违反物理。
- 加**脚下投影**补接地：
  `.char::after{content:"";position:absolute;bottom:-3px;left:50%;transform:translateX(-50%);
  width:68%;height:8px;background:rgba(0,0,0,.2);border-radius:50%;z-index:-1}`

### 2) 动效：按状态给不同 keyframes

四种实测够用：工作中 `workbob`（上下浮动）/ 待机 `sway`（以脚为轴微摆，`transform-origin:50% 100%`）/
有活干 `pace`（来回踱步）/ 闲着 `hop`（蹦跳）。JS 只 `classList.toggle`，动画交给 CSS。
（记住上面的互斥坑：一个元素只挂一个 transform 动画。）

### 3) 光影「按真实世界驱动」，不是装饰

- **阳光光斑**：单独一层 `.sunbeam`，用**当前真实时间**算太阳位置再定位，长 `transition` 让它缓慢移动：

```js
const t = Math.min(1, Math.max(0, (h - 6) / 13));   // 6:00 日出(东) → 19:00 日落(西)
b.style.left   = (5  + t*36) + '%';   b.style.top    = (28 + t*20) + '%';
b.style.width  = (46 - t*16) + '%';   b.style.height = (42 - t*12) + '%';
b.style.transform = `skewX(${-28 + t*56}deg)`;   // 角度随时间变，才像在动
```

- **吸顶灯**：AI 背景图里的灯是**画死的**，晚上不会亮 → 照背景图里灯的位置**另贴一个** `.ceiling-lamp`
  （用 % 对齐 `left/top/width/height`），夜晚换 `background` + `box-shadow` 发光，再叠一层
  `.scene::after` 的 radial-gradient 当房间级光晕。
- **夜晚只开灯还不够**：窗外「白天感」还在。夜晚叠加层要压到 `rgba(16,20,60,.68) → rgba(6,9,32,.80)` 才像晚上。

### 4) 验收清单（拼多时段图后让 VLM 逐条答）

光斑有没有 / 角色是否都站在地板上 / 比例与家具协不协调 / 有没有站桌上·悬空·嵌墙 /
夜晚灯是否亮、阳光是否已关。

> 静态截图**看不到动画**：交付时明确告诉使用者「动效要打开 `http://127.0.0.1:端口` 才看得到」，别指望截图能证明。

## 多方向精灵 + 走动转身 + 分层动画（星露谷式的廉价版）

使用者 2026-09 追加：「人物可以自由的活动」「每个人物都需要有三视图，他们转身那些都要有」「要有动作…手会动，头也会动，做成像星露谷物语那样」。
**逐帧 spritesheet 才是最正解**（成熟项目做法见下），但「多方向静态图 + CSS 过渡 + 分层动画」能拿到八成效果、成本低一个量级。

> 使用者另一条工作方式（2026-09）：「参考优秀的 OpenClaw 代码，不然这样纯原创太难了」——**纯原创卡住时先去 GitHub 抄架构**，别硬扛。
> 搜法：`curl "https://api.github.com/search/repositories?q=openclaw+office+pixel&sort=stars"`（网页搜索后端不稳时 API 直连更可靠）。
> 同类项目实测：`ringhyacinth/Star-Office-UI`（7481★，最成熟）、`ruiqili2/agent-monitor`、`thx0701/openclaw-virtual-office`、`SweetSophia/openclaw-pixel-agents`。

### 1) 4 方向视图怎么出

每角色出 4 张 `{char}_{front,back,left,right}.png`，**统一走图生图**、拿该角色的原图当参考：

```
Show the SAME character as in the reference image, but drawn as: {view}.
The character is {desc}. Full body, standing straight, centered, plain white background.
Keep the exact same art style, colors, proportions and outfit. Clean pixel art, chibi style, no text.
```

`{view}` 取 `front view, facing the camera directly` / `back view, seen from behind` /
`left side view, facing to the LEFT (profile view)` / `right side view, facing to the RIGHT (profile view)`。

- 出完统一处理：`strip_outer_bg`（边缘 flood fill）→ `getbbox()` 裁边 → **缩到同一高度**（如 256px）——前端按固定高度显示才能对齐
- ⚠️ **背面最容易翻车**（见「常见坑」表），要单独重做那几张
- 4 角色 × 4 方向 = 16 张，约 8 分钟 → 后台跑 + 完成通知

### 2) 走动 + 转身

- 每角色配 `area=[x0,x1,bottom0,bottom1]` 活动区，**压在场景前景地板**（见上节「可站立区」）
- 状态机：`waitT` 到点 → 随机选目标点 → 按 `dx` 正负切 `left`/`right` 图 → 走位 → 到达切回 `front`
- 位移用 CSS：`el.style.transition = `left ${moveT}s linear, bottom ${moveT}s linear``（`moveT` 按距离算）；
  `setInterval(step, 130)` 驱动。**别用 JS 每帧改坐标**——交给 `transition` 省性能、天然缓动
- 切图时 `sprite` 和 `head-layer` **必须同步换 `src`**（否则头是旧的朝向）

### 3) 分层动画（「头会动、手会动」）

静态单图也能做出部位动画——**同一张图叠层 + `clip-path` 切分 + 各自 transform**：

```html
<div class="char" id="char-alice">
  <img class="sprite arm-sway" id="px-alice" src="assets/views/alice_front.png">
  <img class="head-layer" id="hd-alice" src="assets/views/alice_front.png">  <!-- 同一张图，再叠一层 -->
</div>
```
```css
.head-layer{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;
  clip-path:inset(0 0 65% 0);        /* bottom 百分比 = 从底部裁掉多少 → 决定哪一截能独立动 */
  transform-origin:50% 35%;          /* 轴心落在脖子处 */
  animation:nod 3.8s ease-in-out infinite}
@keyframes nod{0%,100%{transform:rotate(-2.6deg)}50%{transform:rotate(2.6deg)}}
.arm-sway{animation:armsway 2.4s ease-in-out infinite;transform-origin:50% 78%}  /* 绕肩轴摆手 */
```

- `clip-path: inset(top right bottom left)`：裁出「头部层」再单独旋转 = 点头；同样的手法裁腰/手臂就成摆手
- 每层**只挂一个 transform 动画**（老坑：同元素两套 keyframes 改同一属性，只有一条生效）
- 多角色共用一套 keyframe，靠 `animation-delay` 错开相位，别每个角色各写一份

### 4) 把内容「投射」到背景图的显示器上

背景图里的显示器是黑框（使用者：「背景上为什么会有三个黑框…将内容投射到设计好的电脑上」）：

- 先让 VLM 量出**每台显示器的 % 位置与尺寸**（左/上/宽/高）
- 叠 `.desk-screen`：深色底 + `repeating-linear-gradient` 绿色代码线 + 扫描线 keyframes + `box-shadow` 发光；
  未运行的角色加 `.off` 熄屏
- ⚠️ 背景图有「4 季 × 昼夜」多张，显示器位置**各图略有差异** → 按主用那张对齐，或每张单独量一遍

> 完整代码（走动状态机 / 分层动画 / 屏幕投射 / 背面重做 prompt 原文 / Phaser spritesheet 调研）见
> `references/character-animation.md`。

### 5) 角色气泡（从头顶指出 + 状态语义）

使用者 2026-09：「气泡要从该角色的头上指示出去」「工作的时候…可以将头上的气泡变为相应的颜文字，或者是一堆乱码，
开心的时候或完成项目可以有开心的颜文字，遇到比较困难处理的问题的时候也可以冒出一堆乱码」。

**气泡挂在角色容器内部**（不是屏幕绝对坐标），走动/转身时自动跟随：

```css
.cbubble{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:24px;
  background:#fff;border:2px solid #2b2b3d;border-radius:10px;z-index:9;display:none;
  white-space:nowrap;box-shadow:2px 3px 0 rgba(0,0,0,.3)}
.cbubble::after{content:"";position:absolute;bottom:-8px;left:50%;transform:translateX(-50%);
  border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid #2b2b3d}
.cbubble.show{display:block;animation:bubpop .35s ease-out}
/* 按状态分流样式：终端风 / 开心 / 思考 */
.cbubble.mono {background:#0d1a12;color:#4ade80;font-family:Consolas,monospace}
.cbubble.mono::after{border-top-color:#1d3a26}
.cbubble.happy{background:#fffbe8;border-color:#e0a030}
```

```html
<div class="char" id="char-alice">
  <div class="tag">助手</div>
  <div class="cbubble" id="bub-alice"></div>   <!-- 写进 HTML，别 JS createElement -->
  <img class="sprite" ...><img class="head-layer" ...>
</div>
```

**文案池按状态分**，`setBubble(key, mode)` 每 ~3 秒随机换一条（延续角色可爱性格）：

| 状态 | 样式 | 实测文案 |
|:--|:--|:--|
| tool 运行中 | mono 终端风 | `>_<`、`while(true){}`、`[████░░░░] 45%`、`$ hermes run`、`▓▒░处理中░▒▓`、`[ERROR] #@$%` |
| working | happy 颜文字 | `(๑•̀ㅂ•́)و✧`、`٩(ˊᗜˋ*)و`、`✧◝(⁰▿⁰)◜✧`、`思考中…` |
| idle | 卖萌摸鱼 | `(｡･ω･｡)`、`摸摸鱼…`、`☕ 咖啡时间`、`(∪.∪ )..zzz` |

其他角色各给自己的池：doro `🐾 跑腿中!` / codex `[BUILD] ▓▒░` / dsh `◈ 处理中`。
**用正则给文案自动选样式**（含 `[`/`$`/`▓`/`while` → mono；含颜文字符号 → happy；其余 think），不用人工标 class。

> 两个专属坑见「常见坑」表：**TDZ 中断 render**（只漏后面几个角色）、**父级 opacity 连带变淡**。

## 走动系统 2.0：命名锚点 + 分层 z + 遮挡片（`rect area` 的进阶版）

角色一多、要「**走到工位坐下工作**」「**被家具挡住**」时，`area` 矩形 + CSS `transition` 就不够用了
（它做不到分层遮挡，也没法表达「到位后换姿态」）。换成**命名锚点 + 角色自驱插值**：

- **SPOTS 锚点表**：一切行为 = 走到某个命名点 + 到位后的姿态。座位 `seat_*`（`layer:'desk'`、`arrive:'back'`、`pose:'sit'`）
  与交互点 `ix_shelf/ix_window/ix_door/ix_chat`（`layer:'floor'`、`pose:'use'`、`stay:[秒,秒]`）各一份。
  比 `area` 好在：意图可读（`goSeat('alice')`）、新行为（去书架拿书）只是加一个锚点。
- **z-index 阶梯**（照写，别赌 DOM 顺序）：`2` 坐着的角色 < `3` 桌面屏幕 < `4` **桌沿遮挡片** < `5` 前景走动角色 < `6` 雨雪 < `12` 气泡。
- **桌沿遮挡片 `.desk-front`**：背景图没画椅子，「坐」靠**把背景图的桌沿那一条原样再画一遍盖住下半身**——
  同一张背景图 + `background-position` 负偏移切片即可，**不需要新素材**；但季节/昼夜背景换了它也要跟着换，
  夜里再叠一层与场景同参数的压暗，否则切片比周围亮。
- **透视缩放**：`place(k,x,y,layer)` 按纵深算 `--s`；`.char{transform:translateY(var(--sit)) scale(var(--s));transition:none}`。
  工位层用固定比例（≈`0.78`，对齐桌深），地板层 `0.86 + 0.14*(y-BACK)/(FRONT-BACK)`。
- **主循环换 `requestAnimationFrame` + `dt` 钳制**（`dt = Math.min(0.1, ...)`）：切标签页 30s 回来不会瞬移。
  位移自己做线性插值（`walkT/walkDur`），**别再挂 CSS `transition:left/bottom`**（会和 `transform` 缩放互相干扰）。
- **状态联动只在布尔变化时触发**：`setWorking(k,on){ if(on===c.working) return; ... }`——
  否则 2 秒一次的轮询会反复重发「去坐下」，角色永远在起立/坐下的路上。

> 参考实现与真实数据结构（ClawLibrary 的 `map.logic.json` rooms/walkgraph、座位从椅子自动推导、
> 交互点从家具三侧推导、图集规格）见 `references/agent-office-architecture.md`。
>
> ⚠️ **别把参考项目的「声明能力」当成「它真在用」**（2026-09 实测）：ClawLibrary 的 `occluders`
> 只在 `debugVisualsVisible=true` 时可见、`roomSlices` 是**空数组** —— 「角色被家具挡住」在它的默认
> 美术里**根本没发生**，那是预留能力而非运行分支。抷架构前先用 `grep` 确认一个能力**真的被调用**
> （看开关默认值、看配置数组是否为空），别看到字段名就以为它在跑。
>
> ⚠️ **背景图里没有椅子时，「坐」只能靠遮挡片做**，而且精灵高度与桌沿位置必须匹配：
> 太矮会被桌沿片**整个吃掉**（人消失），太高则**盖不住**（变成站在桌上）。所以「调精灵高度」
> 和「切遮挡片位置」是同一件事，不是两个独立参数。

## 把「子agent」角色做成真实数量（桌上小 doro）

使用者 2026-09：「**dora 的数量和子agent的数量要对应**，可以变成几个更小的 dora 在桌子上」。
看板里的「子agent」不能永远是一个固定角色——数量要跟着真实并发数走。

**数据源在后端拼，别在前端猜**：从 Hermes `state.db` 读两处合成 `cats` 数组——
① `async_delegations` 里 `state='running'` 的（真正的 `delegate_task` 子agent）；
② `sessions` 里 `source='subagent' AND ended_at IS NULL` 且 60 秒内有活动的（兜底，防漏）。
每项带 `{id, state, goal, elapsed}`，`goal` 取 `task_json.goal` 截 50 字。挂进 `/api/status` 的 `cats` 字段。

**前端用「元素池」渲染**（按需增删子节点，别每次清空重建——会闪）：

```js
const MINI_SPOTS = [[316,322],[376,322],[436,322],  [566,322],[626,322],[686,322]];
function renderMiniCats(cats){
  const layer = document.getElementById('mini-cats');   // 容器直接写进 HTML
  if (!layer) return;
  const want = Math.min(cats.length, MINI_SPOTS.length);
  while (layer.children.length > want) layer.removeChild(layer.lastChild);
  while (layer.children.length < want) {
    const d = document.createElement('div');
    d.className = 'cat-mini';
    d.innerHTML = '<span class="mini-bub"></span><img src="assets/views/doro_front.png">';
    layer.appendChild(d);
  }
  for (let i = 0; i < layer.children.length; i++){
    const el = layer.children[i], sp = MINI_SPOTS[i];
    el.style.left = (sp[0]-23)+'px'; el.style.bottom = (SC.H-sp[1])+'px';
    el.querySelector('.mini-bub').textContent =
      (cats[i].goal||'').replace(/\s+/g,' ').trim().slice(0,9);
    el.style.animationDelay = (i*0.23).toFixed(2)+'s';   // 错开跳动相位
  }
}
```

- 小 doro **~46px**（大角色 105px 的 44%），趴在桌面高度，`z-index` 与屏幕同层（3）
- 每只带一个小气泡显示它负责的 task 摘要；**文字截到 9 字**（实测 14 字会拖成长条），
  先 `replace(/\s+/g,' ')` 再去空白（`goal` 里可能混换行/多空格）
- 每只**错开 `animation-delay`**，否则一排小 doro 整齐同步跳，很假
- 池子渲染放在 `render()` **末尾**（所有状态变量算完之后），躲开 TDZ 老坑
- 场地不够时**封顶**（`Math.min(cats.length, MINI_SPOTS.length)`），别让子agent 一多就铺满屏

## 改完必跑语法自检（单文件 HTML）

```bash
python - <<'EOF'
import re
html = open(r"E:\path\index.html", encoding='utf-8').read()
m = re.search(r'<script>(.*)</script>', html, re.S)
open(r"E:\path\_check.js", "w", encoding='utf-8').write(m.group(1))
EOF
node --check "E:/path/_check.js"     # 无输出 = 通过
```

单文件页 JS 几千行时，**一处 `SyntaxError` 让整页死掉**，而截图只呈现为「什么都没发生」——
极易误判成 CSS / 数据 / 后端问题（本会话为此白查了两轮）。改完（尤其新加函数/变量）跑一次，10 秒省一小时。

## 相关文件

- `references/agent-office-architecture.md` — 成熟像素办公室项目的架构知识库（ClawLibrary 的 rooms/walkgraph/图层与工作输出协议；OpenClaw-bot-review 的 Canvas 引擎、座位自动推导、zY 排序、图集规格；国内拉 GitHub 源码的 curl 姿势）
- `references/agent-office-project.md` — 使用者的「像素办公室」项目设定（角色 roster（含参考图配色）、数据源字段、候选方案、已踩坑、进度）
- `references/character-animation.md` — 角色动画实录：4 方向视图生产（含背面翻车重做 prompt）、走动+转身状态机、分层动画（clip-path 点头/摆手）、屏幕内容投射、Star-Office-UI 等成熟项目调研
- `scripts/feishu_send_media.py` — 把截好的图/文件发到飞书（图片/文件自动分流，需 `FEISHU_CHAT_ID`）
- `scripts/render_pixels_png.py` — 点阵 → 320×320 PNG（整数倍缩放 + 居中透明底 + 四合一总览图）
