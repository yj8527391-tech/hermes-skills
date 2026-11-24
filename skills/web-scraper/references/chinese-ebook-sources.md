# 中文电子书获取：微信读书抓取 + 各书源实测（2026-08）

考研/学术书电子版获取的实测路径（场景：《戏剧本体论》谭霈生、目标院校考研必读剧本批量入库）。核心结论：**微信读书是正版全文首选源——匿名搜索 API 可用，全文抓取只需使用者扫码/微信授权登录一次，正文是 canvas 渲染，必须走"canvas 截图 + RapidOCR"方案（接口法已全灭，DOM 分页法只能拿到章名/UI 文字）**。

> ⚠️ **2026-08-18 重大修正**：早期结论"DOM 分页翻页法可行"是**错的**——`.readerChapterContent_container` 的 innerText 只有章名（如"第一场 艾尔西诺 城堡前的露台"），翻页后 DOM 文本不变，页面正文画在 2 个 `canvas`（约 393×590）里。第一版批量脚本按 DOM 抓出的 29 本全是 200-800 字的详情页/章名空壳。**正文唯一可行提取路径 = canvas 元素截图 + RapidOCR 识别**（实测《哈姆雷特》正文识别流畅准确）。翻页按钮是有效的（canvas 内容在变），"DOM 文本不变"是提取对象错了，不是翻页失败。

## 1. 微信读书匿名搜索（已验证，无需登录）

- `GET https://weread.qq.com/web/search/global?keyword=<URL编码>&maxIdx=0&fragmentSize=20`
- 无鉴权直接返回 JSON：`books[]`，每项含 `bookInfo.title / author / bookId / finished / soldout / deepLink`
- ⚠️ 同名接口 `web/search/books` 返回 HTML 页（书名-全部作品在线阅读-微信读书），不是 JSON
- ⚠️ `web/bookInfo?bookId=` 匿名 404（需登录态）；书籍详情用豆瓣页（见 §4）
- **搜索匹配是文本相似不是精确书目**：搜"雷雨"第一名是奥斯特洛夫斯基《大雷雨》不是曹禺《雷雨》——必须核对 `bookInfo.author`，批量脚本用书名+作者/指定 bookId 精确匹配

## 2. 在架状态探测（soldout）——先探测再决定抓不抓

- `bookInfo.soldout`：**0 = 在架可读，1 = 已下架**（阅读页显示"本书已下架，内容不再支持阅读"）
- 2026-08 实测下架大户：谭霈生《戏剧本体论》《论戏剧性》、曹禺四部曲（雷雨/日出/原野/北京人）、贝克特《等待戈多》、尤涅斯库《秃头歌女》《犀牛》、高乃依《熙德》、拉辛《费德尔》、奥尼尔《毛猿》——现代/当代版权方收回的经典常见 soldout=1
- **下架书登录也没用**，先批量探测（一次循环 50+ 本，间隔 0.8s）筛出在架清单再抓

## 3. 全文抓取：canvas 截图 + RapidOCR（接口法全灭、DOM 法拿不到正文）

### 3.1 登录（一次性，cookies 落盘复用）
1. Playwright + Edge（`channel='msedge'`，headless=True 也行）：打开 **https://weread.qq.com/ 首页**，点右上角"登录"按钮（`text=登录`）→ 弹窗出二维码
   - ⚠️ **不要从书籍页触发登录**：网页 URL（`/web/bookDetail/<id>`、`/web/reader/<id>`）用**加密书 ID**（25 位含字母，如 `f7732410811e7ed6eg017d6f`），数字 bookId 拼 URL 必 404（2026-08-18 实测踩坑）
   - **使用者偏好（2026-08 明确）**：涉及微信登录先查电脑微信是否运行（`Get-Process | Where-Object {$_.ProcessName -match 'Weixin'}`）；已登录 → 网页登录点"允许外部应用"授权免扫码；未登录先让使用者登微信
2. 登录判定：cookies 出现 `wr_vid`（≠'0'）+ `wr_skey` → `context.cookies()` 存 JSON 落盘
3. 加密 ID 提取：搜索 API 的 `bookInfo.deepLink` 里 `v=<enc_id>`（正则 `r'v=([0-9a-z]+)'`）——数字 bookId 用于搜索匹配，加密 ID 用于打开 reader 页

### 3.2 canvas 截图 + RapidOCR 抓正文（2026-08-18 实测可行，DOM 法已废弃）
**接口全灭**：`/web/book/chapterInfos`、`/web/book/chapter/content`、`/web/book/chapter/e_N` 用 requests（带 cookies）或浏览器内 fetch 全部 404——新版接口需页面 JS 内部签名/上下文，逆向成本高，**别走接口**。**DOM 法也不行**：正文渲染在 canvas，`.readerChapterContent_container` 只有章名/UI。正确流程：

1. `page.goto('https://weread.qq.com/web/reader/<enc_id>')`，等 7-8s
2. 预处理遮罩：`document.querySelectorAll('.wr_mask').forEach(el => el.style.pointerEvents='none')`（否则普通 click 被拦截）
3. 循环每页：
   - **截图**：`page.locator('canvas').first.screenshot(path=...)`（第一个 canvas 即正文页；viewport 设 1280×900 保证 canvas 完整）
   - **OCR**：`RapidOCR()(img)` → 行文本；**过滤 UI 噪声行**（精确匹配"上一页/下一页/点击添加书签/点击目录/朗读/加入书架"或含这些词且 <25 字——剧本台词里也可能出现"下一页"，按长度+精确匹配过滤）
   - **付费墙检测**：OCR 文本含"开通会员/立即购买/购买本章/付费解锁/会员专享"→ 停（免费书不会触发；会员书只到试读处）
   - **去重**：md5 每页 OCR 文本，连续 10 页无新内容结束（翻页未生效会连续重复）
   - **翻页**：`.renderTarget_pager_button` nth(1) **必须 force=True 点击**，点击后轮询等 canvas 内容变化（400ms×20）；章节末点"下一章"（`text=下一章`）；书末检测 DOM 出现"标记读完"
4. 输出 txt：头部写书名/来源/日期/页数/字数（入库验证用）
5. **单书卡死就换书/换版本**（实测《茶馆》人文社版卡"第一幕"章名页翻不动，其他在架版本正常）；OCR 空页连续出现也换版本
6. **批量模式**：单进程 = 一个 Playwright 浏览器 + **一个 RapidOCR 引擎**（模型只初始化一次）循环抓所有书；**断点续抓**（state json 每本完成即写入，重跑跳过）；每本间隔 2-3s。速度 ≈ 5-8s/页（OCR 2-5s + 翻页等待），28 本剧本（50-200 页/本）约 3-7 小时，后台跑 + notify_on_complete

### 3.3 代码骨架
```python
# 登录轮询（2 分钟超时）
for i in range(90):
    ck = {c['name']: c['value'] for c in await context.cookies()}
    if ck.get('wr_vid') and ck.get('wr_skey') and ck.get('wr_vid') != '0':
        json.dump(await context.cookies(), open('_weread_cookies.json', 'w', encoding='utf-8'))
        break
    await page.wait_for_timeout(2000)

# canvas OCR 核心循环（伪代码）
ocr = RapidOCR()  # 只初始化一次
while stall < 10:
    await page.locator('canvas').first.screenshot(path='_tmp.png')
    result, _ = ocr('_tmp.png')
    text = '\n'.join(filter_ui_lines([l[1] for l in result]))  # 过滤 UI 噪声行
    if detect_paywall(text): break          # 开通会员/立即购买
    if text and md5(text) != prev: 入库; stall = 0
    else: stall += 1
    await page.locator('.renderTarget_pager_button').nth(1).click(force=True)  # 必须 force
    for _ in range(20):                      # 轮询等 canvas 变化
        await page.wait_for_timeout(400)
        if canvas_changed(): break
```

## 4. 各书源实测结论（2026-08 环境）

| 来源 | 结果 |
|---|---|
| 360 搜索"书名 PDF 下载 / 提取码" | 多为广告/百度知道死链；豆瓣小组帖常是淘宝卖资料广告（正文只有 item.taobao.com 链接） |
| 豆瓣读书 subject 页（book.douban.com） | 出版基准：作者/出版社/年份/ISBN/页数，**用于完整性验证**；目录块 `related_info` 经常缺失，别依赖 |
| QQ 阅读 book-detail 页 | 可匿名访问，学术书常显示"因版权原因待上架"→ 不可读 |
| 鸠摩搜书 jiumodiary.com/api/s | API 已死（404 页面未找到），勿再试 |
| Anna's Archive / libgen.is/rs / z-lib 直连 | 国内全被墙；机场节点过期时全 HTTP 000，**先测节点再指望代理**（probe_nodes.py / 切香港 01/03 专线） |
| 读秀/超星文献传递（ucdrs.superlib.net） | 兜底：注册登录后每次约 50 页传邮箱，几百页的书分多次，最后再用 |
| GitHub/gitee 仓库搜书 | api.github.com 直连可用，但考研/专业理论书命中率极低；搜到的是程序员技术书仓库 |
| 付费兜底 | 古籍电子书站（如 xy980.net 有《谭霈生文集》6 卷全 PDF，QQ/微信联系站长）；淘宝/闲鱼搜"书名 电子版"3-10 元秒发 |

## 5. 完整性验证基准（案例）

- 豆瓣《戏剧本体论》：2009 北京大学出版社，284 页，ISBN 9787301158104（另有 2023 中国国际广播出版社新版 68 元，别混淆）
- 抓取后对比：页数/总字数/末章标题（原书末章"后记"）是否齐全；微信读书 finished=1 = 完本标记
- 剧本类：正文几万字即可确认完整（对照目录章节数）

## 6. 附录：目标院校考研必读剧本清单（55 部 + 微信读书在架状态，2026-08 实测）

批量探测用搜索 API 循环（间隔 0.8s），按书名匹配后**必须核对 author**（搜"雷雨"会命中奥斯特洛夫斯基《大雷雨》）。

**✅ 微信读书在架可抓（30 部，soldout=0）**：俄狄浦斯王（索福克勒斯悲剧集2）、美狄亚（欧里庇得斯悲剧集2）、哈姆雷特、麦克白（有纯中文版/中英双语两版，选纯中文）、李尔王、仲夏夜之梦、伪君子（作家榜）、浮士德、阴谋与爱情、钦差大臣、玩偶之家、群鬼、樱桃园（人文经典丛书）、三姐妹、万尼亚舅舅、六个寻找剧作家的角色（诺贝尔奖大系）、四川好人、高加索灰阑记、大胆妈妈和她的孩子们、伽利略传（布莱希特四部同版）、老妇还乡、推销员之死（阿瑟·米勒作品系列）、欲望号街车（译文经典）、天边外、茶馆（在架 20+ 版本，人文社版会卡章名页需换版）、屈原、名优之死、风雪夜归人、天下第一楼

**❌ 微信读书下架/未收录（25 部，需网盘/付费/鉴赏辞典选录）**：曹禺四部曲（雷雨/日出/原野/北京人——全下架）、被缚的普罗米修斯、熙德、费德尔、悭吝人、欧那尼、朱丽小姐、等待戈多、秃头歌女、犀牛、毛猿、上海屋檐下、一只马蜂、五奎桥、陈毅市长、绝对信号；在底层/人民公敌（仅英文版）/于无声处/物理学家/禁闭/关汉卿/在底层等搜索命中同名异书，**必须核 author 或放弃**（如"在底层"命中《我在底层的生活》、"物理学家"命中《宽客人生》、"禁闭"命中《禁闭岛》）

**付费/兜底**：《戏剧本体论》《论戏剧性》（谭霈生）微信读书全下架 → xy980.net《谭霈生文集》6 卷 PDF（卷6=戏剧本体论 187.95MB，QQ 75689990/微信 k77815100 联系站长）或淘宝/闲鱼 3-10 元
