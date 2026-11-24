# 角色动画实录：多方向精灵 / 走动转身 / 分层动画（2026-09-21）

主人原话：「人物可以自由的活动」「每个人物都需要有三视图，他们转身那些都要有」
「要有动作…他的手会动，头也会动，做成像星露谷物语那样的」。

---

## 一、成熟项目调研（先抄架构，再动手）

主人明确说：「参考优秀的 OpenClaw 代码，不然这样纯原创太难了」。
网页搜索后端不稳，**用 GitHub API 直搜**最可靠：

```bash
curl -s "https://api.github.com/search/repositories?q=openclaw+office+pixel&sort=stars&order=desc&per_page=4"
```

实测同类项目：

| 项目 | ★ | 备注 |
|:--|:--|:--|
| `ringhyacinth/Star-Office-UI` | 7481 | 最成熟；MIT 代码，**美术素材仅限非商业学习** |
| `ruiqili2/agent-monitor` | 55 | 像素办公室 |
| `thx0701/openclaw-virtual-office` | 48 | 虚拟办公室看板 |
| `SweetSophia/openclaw-pixel-agents` | 24 | 像素 agent 办公室 |

### Star-Office-UI 的技术要点（扒 `frontend/game.js`）

栈：**Flask 状态服务 + Phaser 游戏引擎**；角色动画走 **spritesheet 逐帧**：

```js
this.load.spritesheet('star_idle', '/static/star-idle-spritesheet.png',
                      { frameWidth: 128, frameHeight: 128 });
this.anims.create({ key:'star_idle',
  frames: this.anims.generateFrameNumbers('star_idle', { start:0, end:29 }),  // 30 帧
  frameRate: 12, repeat: -1 });
this.anims.create({ key:'star_researching',
  frames: this.anims.generateFrameNumbers('star_researching', { start:0, end:95 }),  // 96 帧
  frameRate: 12, repeat: -1 });
```

- **idle 30 帧 / working 96 帧，12fps，`repeat:-1`** —— 「星露谷式」的技术本质就是多帧精灵表 + 定频播放
- 素材目录约定：`cats-spritesheet.webp`、`desk-v3.webp`、家具也是 spritesheet（`sofa_busy` 48 帧）
- 仓库根有 **`gif_to_spritesheet.py`**：GIF → **单行** spritesheet，`target_height` 默认 **64**，
  `Image.Resampling.NEAREST` 缩放（保像素硬边）；**`webp_to_spritesheet.py`、`repack_star_working.py`、`resize_map.py`** 同理
- 布局用 `LAYOUT.areas` 定义区域坐标，角色在区域间 `tween` 移动

> 结论：要「真·逐帧」就得**每角色 8–30 帧**的素材。AI 单张生成难保证帧间一致，所以本会话走的是
> 「4 方向静态图 + CSS 过渡 + 分层动画」的降级路线；若日后要升级，把 GIF/帧序列过一遍
> `gif_to_spritesheet.py` 的写法即可。

### ClawLibrary（龙虾图书馆，455★）—— 主人点名的参考

主人 2026-09 直接给了链接：`github.com/shengyu-meng/ClawLibrary`（TypeScript + Vite）。
它的 `src/data/` 是「逻辑与美术分离」的范例，四个 JSON 各管一件事：

| 文件 | 管什么 | 可借用的点 |
|:--|:--|:--|
| `map.logic.json` | 房间布局 / 锚点 / **步行图** / 工作区 | `renderLayers` 深度分层、`rooms[].bounds` + `labelAnchor` |
| `asset.manifest.json` | 资产逻辑定义 | 资产与房间的映射 |
| `scene-art.manifest.json` | 角色与场景美术绑定 | 换美术不改逻辑 |
| `work-output.protocol.json` | **工作状态 → 输出语义** | 气泡/文案的「状态词表」 |

`map.logic.json` 的图层深度（这是「角色被家具遮挡」的正解）：

```json
"renderLayers": [
  {"id":"floor","depth":1}, {"id":"back_walls","depth":8}, {"id":"mid_props","depth":20},
  {"id":"actor","depth":30},        // 角色夹在中景道具之上、前景遮挡物之下
  {"id":"fg_occluder","depth":50}, {"id":"fx_overlay","depth":70}
]
"rooms": [ {"id":"document","bounds":[430,650,370,250],"labelAnchor":{"x":666,"y":664}} ]
```

要点：

- **actor 夹在 mid_props(20) 与 fg_occluder(50) 之间** → 角色走到桌后会被桌子挡住，天然透视（不必自己算遮挡）
- 每个房间是 `bounds:[x,y,w,h]` + `labelAnchor`；「工作区」就是角色该去的锚点 → 对应「走到工位坐下」
- `work-output.protocol.json` 把工作类型（document/images/memory/skills/gateway…）映射成人话摘要 → 正是头顶气泡的文案来源
- 它还有 `qa:movement` 这类移动 QA 脚本（走位回归测试），思路可借鉴
- ⚠️ 搜它时网页搜索后端可能挂；**GitHub API 直连更可靠**：
  `curl -s "https://api.github.com/repos/shengyu-meng/ClawLibrary/contents/src/data"`

---

## 二、4 方向视图生产

### prompt 模板（图生图，每方向一张）

```
Show the SAME character as in the reference image, but drawn as: {view}.
The character is {desc}.
Full body, standing straight, centered, plain white background.
Keep the exact same art style, colors, proportions and outfit as the reference.
Clean pixel art, chibi style, no text
```

`{view}` 四种：

| key | view 描述 |
|:--|:--|
| front | `front view, facing the camera directly, symmetrical frontal pose` |
| back  | `back view, seen from behind, showing the back of the character` |
| left  | `left side view, the character facing to the LEFT (profile view)` |
| right | `right side view, the character facing to the RIGHT (profile view)` |

### ⚠️ 背面重做（AI 会把正面特征搬到背面）

VLM 复核 4×4 视图表后判：「第 1、4 行背面必须重做」——企鹅服的白肚皮画到了背上、钢铁侠胸口的方舟反应堆出现在背上。
**重做时把正面特征显式否掉**：

```
Show the BACK view of the SAME character as the reference (a girl in a penguin kigurumi onesie).
Seen from directly behind: the BACK of the penguin suit is SOLID BLACK — do NOT show any white belly
on the back. Show the back of the black hair and the penguin hood from behind, and the yellow penguin feet.
Full body, standing, centered, plain white background, clean pixel art, same style as reference, no text
```
```
Show the BACK view of the SAME character as the reference (an Iron Man style robot with red and gold armor).
Seen from directly behind: show the back armor plates in red and gold.
IMPORTANT: do NOT draw the glowing chest arc reactor — that is only on the FRONT.
The back of the helmet has no eye slits. Full body, standing, centered, plain white background,
clean pixel art, same style as reference, no text
```

### 后处理（16 张统一规格）

```python
# 1) 先等比放到 1920 高 2) 边缘 flood fill 去白底 3) getbbox 裁边 4) 统一缩到 256 高
im = Image.open(p).convert("RGBA")
if im.height != 1920:
    im = im.resize((im.width*1920//im.height, 1920), Image.LANCZOS)
im = strip_outer_bg(im)          # 见 SKILL.md「用 AI 生图替代手绘点阵」的 flood fill 实现
im = im.crop(im.getbbox())
sc = 256 / im.height
im = im.resize((max(1,int(im.width*sc)), 256), Image.LANCZOS)
```

验收：把 4×4 拼成一张表（行=角色，列=前/后/左/右），丢给 VLM 问
「每行 4 个视图是否同一角色的不同角度 / 背面是否真是背面 / 哪些不合格」。

---

## 三、走动 + 转身状态机

```js
/* area = [x0, x1, bottom0, bottom1] —— 限制在办公室地板上活动 */
const CHAR_CFG = {
  alice:{cid:'char-alice', iid:'px-alice', hid:'hd-alice', area:[56, 300, 8, 58]},
  doro: {cid:'char-cat',   iid:'px-cat',   hid:'hd-cat',   area:[306,470, 6, 44]},
  codex:{cid:'char-codex', iid:'px-codex', hid:'hd-codex', area:[500,690, 8, 58]},
  dsh:  {cid:'char-dsh',   iid:'px-dsh',   hid:'hd-dsh',   area:[700,884, 6, 44]},
};
const chState = {};
for (const k in CHAR_CFG) {
  const el = document.getElementById(CHAR_CFG[k].cid);
  chState[k] = { x:+el.style.left||100, y:+el.style.bottom||40,
                 dir:'front', busy:false, waitT: Math.random()*5, moveT:0 };
}
function setCharView(k, dir) {
  const s = chState[k];
  if (s.dir === dir) return;
  s.dir = dir;
  const src = `assets/views/${k}_${dir}.png`;
  const img = document.getElementById(CHAR_CFG[k].iid); if (img) img.src = src;
  const hd  = document.getElementById(CHAR_CFG[k].hid); if (hd)  hd.src  = src;  // ← 头层必须同步
}
let _lastT = performance.now();
function stepChars() {
  const now = performance.now(), dt = Math.min(0.5, (now-_lastT)/1000); _lastT = now;
  for (const k in CHAR_CFG) {
    const c = CHAR_CFG[k], s = chState[k], el = document.getElementById(c.cid);
    if (!el) continue;
    if (s.busy) {
      s.moveT -= dt;
      if (s.moveT <= 0) { s.busy = false; setCharView(k,'front'); s.waitT = 1.5+Math.random()*5; }
    } else {
      s.waitT -= dt;
      if (s.waitT <= 0) {
        const a = c.area;
        const tx = a[0]+Math.random()*(a[1]-a[0]);
        const ty = a[2]+Math.random()*(a[3]-a[2]);
        const dx = tx - s.x;
        if (Math.abs(dx) > 10) setCharView(k, dx<0 ? 'left' : 'right');
        s.moveT = Math.min(2.6, 0.6 + Math.abs(dx)/120 + Math.abs(ty-s.y)/120);
        el.style.transition = `left ${s.moveT}s linear, bottom ${s.moveT}s linear`;
        el.style.left = tx+'px'; el.style.bottom = ty+'px';
        s.x = tx; s.y = ty; s.busy = true;
      }
    }
  }
}
setInterval(stepChars, 130);
```

要点：

- **`moveT` 按距离算**，不然近距离也慢吞吞
- 走动用的是 `transition`，所以**不要**再给同一元素挂 `pace` 这类原地来回的 keyframe（会打架）
- 走到一半切朝向只需换图，**不需要** `transform: scaleX(-1)` 镜像（左右各出了一张图）
- **活动区压前景地板**：首版把 `area` 定在中景，VLM 判「doro 卡在桌子下面、像被夹在桌腿之间」。
  背景图的家具是 AI 画的，跟你脑子里的布局对不上——`bottom` 取 6~58 这种小值最安全

---

## 四、分层动画（点头 / 摆手 / 呼吸）

单张静态图也能让部位动起来：**同图叠一层 + `clip-path` 切出部位 + 各自 transform**。

```css
/* 头部层：只留上部，绕脖子转 */
.head-layer{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;
  image-rendering:pixelated;clip-path:inset(0 0 65% 0);
  transform-origin:50% 35%; animation:nod 3.8s ease-in-out infinite}
@keyframes nod{0%,100%{transform:rotate(-2.6deg) translateY(0)}
               50%   {transform:rotate(2.6deg)  translateY(-1px)}}

/* 手臂：绕肩轴微摆 */
.arm-sway{animation:armsway 2.4s ease-in-out infinite;transform-origin:50% 78%}
@keyframes armsway{0%,100%{transform:rotate(-1.8deg)}50%{transform:rotate(1.8deg)}}
```

HTML 就是同 src 叠两张：

```html
<div class="char" id="char-alice" style="left:120px;bottom:40px">
  <div class="tag" id="tag-alice">助手</div>
  <img class="sprite arm-sway" id="px-alice" src="assets/views/alice_front.png" alt="助手">
  <img class="head-layer" id="hd-alice" src="assets/views/alice_front.png" alt="">
</div>
```

坑：

- `clip-path: inset(top right bottom left)` 的 **bottom %** 决定「从底部裁掉多少」，即哪一截能独立动；
  头部一般裁掉 60~70%
- `transform-origin` 一定要挪到**关节**（颈部 35%、肩部 78%），否则是整块平移不是点头
- **一个元素只挂一个 transform 动画**（两条 keyframes 同改 `transform` 时只有一条生效）
- 走动切图时 `head-layer` 的 `src` 必须跟着换，否则「身子转过去了头没转」
- 分层动画是**程序化替代方案**，静态截图完全看不出——交付时必须提醒主人开浏览器

---

## 五、屏幕内容投射（背景图里的黑框）

主人：「背景上为什么会有三个黑框，将内容投射到设计好的电脑上」——那是背景图自带的显示器。

1. 让 VLM 量出显示器的 % 位置（实测某张秋景：左 37.4% / 上 57.2% / 宽 6.4% / 高 8.2%，另一台 55.2% / 57.4% / 5.4% / 7.2%）
2. 叠一层假屏幕：

```css
.desk-screen{position:absolute;z-index:2;pointer-events:none;border-radius:1px;
  background:#07180d;
  background-image:repeating-linear-gradient(0deg,rgba(74,222,128,.9) 0 1px,transparent 1px 4px);
  box-shadow:0 0 6px rgba(74,222,128,.45);opacity:.9;
  animation:crtscan 2.2s linear infinite}
@keyframes crtscan{from{background-position:0 0}to{background-position:0 12px}}
.desk-screen.off{background:#0b0b12;background-image:none;box-shadow:none;opacity:.55;animation:none}
#ds1{left:37.5%;top:57.3%;width:6.2%;height:8%}
#ds2{left:55.3%;top:57.5%;width:5.2%;height:7%}
```

3. 「未运行」的角色把对应屏幕加 `.off` 熄屏

> ⚠️ 背景图是 **4 季 × 昼夜 12 张**，显示器位置每张略有出入 → 用主图对齐，或每张单独量。
> ⚠️ 同批还叠了 `.moon-glow`（夜晚增亮）——VLM 复核时发现**画面里出现两个月亮**（一个是我叠的、
> 一个是背景图自带的）。叠之前先问 VLM「窗外有没有月亮」。

---

## 六、角色气泡（状态语义：颜文字 / 乱码）

主人 2026-09：「气泡要从该角色的头上指示出去」「工作的时候可以将头上的气泡变为相应的颜文字，
或者是一堆乱码，开心的时候或完成项目可以有开心的颜文字，遇到比较困难处理的问题的时候也可以冒出一堆乱码」。

**结构**：气泡写在角色容器内（`.char` 里），随走动/转身自动跟随，不用算屏幕坐标。

```html
<div class="char" id="char-alice">
  <div class="tag" id="tag-alice">助手</div>
  <div class="cbubble" id="bub-alice"></div>
  <img class="sprite arm-sway" id="px-alice" src="...">
  <img class="head-layer" id="hd-alice" src="...">
</div>
```

```css
.cbubble{position:absolute;bottom:100%;left:50%;transform:translateX(-50%);margin-bottom:24px;
  background:#fff;color:#222;font-size:11px;padding:3px 8px;border:2px solid #2b2b3d;
  border-radius:10px;white-space:nowrap;z-index:9;display:none}
.cbubble::after{content:"";position:absolute;bottom:-8px;left:50%;transform:translateX(-50%);
  border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid #2b2b3d}
.cbubble.show{display:block;animation:bubpop .35s ease-out}
```

**文案池 + 自动选样式**（省掉人工标 class）：

```js
const EMOTE = {
  alice: {
    tool:    ['>_<','[运行中]','while(true){}','[████░░░░] 45%','$ hermes run','▓▒░处理中░▒▓','[ERROR] #@$%'],
    working: ['(๑•̀ㅂ•́)و✧','٩(ˊᗜˋ*)و','思考中…','✧◝(⁰▿⁰)◜✧','hmm...'],
    idle:    ['(｡･ω･｡)','摸摸鱼…','☕ 咖啡时间','(∪.∪ )..zzz'],
  },
  doro:  { busy: ['🐾 跑腿中!','(ↀωↀ)✧','喵呜~'], idle: ['(=_=)','趴一下…','zzZ'] },
  codex: { busy: ['[BUILD] ▓▒░','编译中...','✔ 测试通过'], idle: ['(— _ —)','待命中','[off]'] },
  dsh:   { busy: ['(๑>ᴗ<๑)','数据流…','◈ 处理中'], idle: ['(・_・)','静默','[sleep]'] },
};
function setBubble(k, mode) {
  const b = document.getElementById('bub-' + k);
  if (!b) return;
  if (!mode) { b.classList.remove('show'); s.mode=''; return; }
  if (s.mode === mode && performance.now() - s.t < 3200) return;   // ~3s 才换一条，别闪太快
  const pool = EMOTE[k][mode] || ['…'];
  const txt = pool[Math.floor(Math.random() * pool.length)];
  const cls = /^\[|^\$|^▓|^while|ERROR/i.test(txt) ? 'mono'
            : /✧|٩|๑|🐾|✔|♪|◈/.test(txt) ? 'happy' : 'think';
  b.className = 'cbubble ' + cls + ' show';
  b.textContent = txt;
}
```

**挂载点：`render()` 的末尾**（所有状态变量算完之后）。

```js
setBubble('alice', working ? (a.kind==='tool' ? 'tool' : 'working')
                           : (aStat==='idle'||aStat==='away' ? 'idle' : null));
setBubble('doro',  hasCats ? 'busy' : 'idle');
setBubble('codex', codexOn ? 'busy' : 'idle');
setBubble('dsh',   dshOn ? 'busy' : 'idle');
```

### ⚠️ 两个专属坑（都实际踩过）

1. **TDZ 中断 render**：首版把气泡调用放在 `const hasCats` / `codexOn` / `dshOn` **之前**。
   `const` 有暂时性死区 → `ReferenceError: Cannot access 'hasCats' before initialization` →
   **整个 `render()` 从这行起中断**。症状极具迷惑性：**助手的气泡正常显示**（她那行已执行完），
   后面 3 个角色全没气泡 —— 看起来像 CSS / 元素缺失问题。→ **状态变量全部算完再统一设气泡**。
2. **父级 opacity 连带变淡**：未运行角色原本用 `.char{opacity:.55}`，气泡和名字标签**一起半透明**，
   VLM 复核直接判定「codex/dsh 头顶没有气泡」。→ 改成只对 `<img>` 设 opacity：
   ```js
   const op = codexOn ? 1 : 0.62;
   document.getElementById('px-codex').style.opacity = op;
   document.getElementById('hd-codex').style.opacity = op;
   ```

> 另外：**别用 JS `createElement` 动态造气泡**（本会话试了两次都不显示）。写进 HTML，JS 只管 `classList` / `textContent`。

## 七、待办 / 未解决

- 分层动画只是降级方案；**真·逐帧**需按 Star-Office-UI 的 spritesheet 路线出帧序列
- VLM 复核的常见遗留判词：doro 偶尔被桌腿挡、dsh 的侧面是坐姿、脚下阴影偏淡、显示器仍偏小
- 静态截图的验收局限：走动/转身/昼夜切换一律**必须开浏览器**，交付话术要写清楚
