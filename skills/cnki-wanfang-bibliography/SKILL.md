---
name: cnki-wanfang-bibliography
description: Use when 补参考文献页码或查题录真伪。走万方替代知网。
---

# 知网/万方 题录与页码核查

补参考文献起止页码、核实某篇中文论文是否真实存在、确认期刊是不是北大核心/CSSCI —— 全部靠这套流程。

## 关键结论（2026-11 实测）

| 站点 | 状态 | 能给什么 |
|---|---|---|
| kns.cnki.net 主站 | ❌ blockPuzzle 滑块验证 | 自动滑 6 次全失败，别硬刚 |
| navi.cnki.net 期刊导航 | ❌ 同样验证 | — |
| search.cnki.com.cn 知网空间 | ⚠️ 不验证但结果不稳 | 题录 JSON（无页码） |
| **s.wanfangdata.com.cn 万方** | ✅ **主力** | **页码 + 刊名年期 + 核心等级 + ISSN** |
| 百度学术 | ❌ 点选汉字验证 | — |
| ncpssd.org 国家哲社文献中心 | ❌ WAF 403 | — |
| 高校学报官网（如 journal.sdu.edu.cn） | ✅ 直接下 PDF | PDF 首页印着"2023年第4期第37-46页" |

**先用万方，万方没有再用学报官网，别在知网主站浪费时间。**

## 万方批量抓题录（主路径）

脚本：`~\thesis27\tools\wanfang_batch.py`

```python
pg.goto('https://s.wanfangdata.com.cn/paper?q=' + urllib.parse.quote(题名))
time.sleep(6)
pg.get_by_text(题名[:12], exact=False).first.click()   # 点标题，开新 tab
t = ctx.pages[-1]; t.bring_to_front(); time.sleep(2)
dt = t.inner_text('body')
```

详情页正文长这样，正则直接抠：

```
页数：
15 (178-192)
戏剧艺术
北大核心CSSCIAMI
ISSN：0257-943X
年,卷(期)：2023(4)
```

```python
页码 = re.search(r'页\s*数[：:]?\s*\n?\s*\d+\s*[\(（]\s*([0-9\-–—]+)\s*[\)）]', dt).group(1)
刊名 = re.search(r'首页\s*>\s*期刊导航\s*>\s*([^>]{2,25}?)\s*>', dt).group(1)
```

核心等级直接读文本里有没有 `北大核心` `CSSCI` `AMI` `CSCD`。

### 坑

- **必须 `headless=False`**。headless 模式下万方结果区渲染不出来，`query_selector_all('a')` 返回空，但 headless=False 就有 73 个 a。
- 标题链接**不是 `<a>`**（SPA 路由），别找 href，直接 `get_by_text(标题).click()`。
- 点标题会开新 tab，用 `ctx.pages[-1]` 取，用完 `close()`。
- 搜索词用**短标题**（前 12 字），带空格的多词搜索会被当 AND 处理而返回 0 条。
- 搜不到时（报纸文章、部分期刊）万方 paper 库本就不收录，转学报官网或知网报纸库。

## 知网空间 API（拿 fileName，无页码）

```python
requests.post('https://search.cnki.com.cn/api/search/listresult',
    data={'searchType':'MulityTermsSearch','ArticleType':'0','Content':关键词,
          'Theme':'','Title':'','KeyWd':'','Author':'','Originate':'','Summary':''},
    headers={'Referer':'https://search.cnki.com.cn/Search/Result',
             'Origin':'https://search.cnki.com.cn'})
# → json['articleList'] 每项: title/author/originate/year/period/fileName/dbType
```

`fileName`（如 `XJYX202304016`）是知网篇名号，但**详情页 `www.cnki.com.cn/Article/CJFDTotal-xxx.htm` 已废弃，全 404**。只别指望它拿页码。接口本身也常超时，重试或换万方。

## 学报官网下 PDF 读页码

```
目录页 → 点文章标题 → 文章页找 a[href*=".pdf"] → curl 下载 → pymupdf 读第 1 页
```

PDF 首页通常印着 `山东大学学报（哲学社会科学版）\n2023年第4期第37-46页`，一次拿到页码 + DOI + 摘要。

## 期刊等级的两个补充

- 万方标的 `CSSCI` 可能**含扩展版**（如《文化艺术研究》，实为 CSSCI 扩展版）。要严格区分正刊/扩展版得查当年 CSSCI 目录。
- 万方标 `AMI` 不等于核心，AMI 是社科院评价，别跟北大核心混。

## 交付前必做

页码写回 `文献综述_*.md` 和 `tools/build_kaiti.py` 两处（开题的参考文献在 py 里），然后重跑生成器 + Word COM 更新目录域，再读 docx 文本确认改到了。**页码一律有据可查才写，查不到就留空并告知用户去哪补，绝不编。**
