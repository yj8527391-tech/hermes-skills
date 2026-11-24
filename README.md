# hermes-skills

一组给 [Hermes Agent](https://hermes-agent.nousresearch.com/docs) 用的中文技能（skills）合集。

每个技能就是一个目录，里面是 `SKILL.md` 加可选的 `scripts/`、`references/`、`assets/`。Hermes 读 `SKILL.md` 的 frontmatter 决定什么时候触发，所以复制进目录就能用，不需要额外注册。

## 收录

| 技能 | 目录 | 做什么 | 依赖 |
|---|---|---|---|
| 小六壬占卜（诸葛马前课） | `skills/xiaoliuren-analysis` | 按农历月日时三数起课，推六宫掌诀，用大白话解读事业财运感情，末尾附锐评 | `pytz` `ephem` |
| 人生报告 · 八字命理深度解读 | `skills/bazi-analysis` | 真太阳时校正排盘、五行能量条形图、大运流年 -5~+5 评分走势、喜用神定位、健康预警 | `pytz` `ephem` |
| 小red薯爬爬（小红书爬取） | `skills/xiaohongshu-scraper` | Playwright 调本机浏览器登录，抓搜索结果，提取 JS 渲染内容，导出 Excel | `playwright` |
| 企业背调 | `skills/company-due-diligence` | 招聘会批量背调公司：三轮筛选、分层打分、薪资比价、走场路线 | 无 |
| Markdown 转 Word | `skills/markdown-to-docx` | md 转 docx 的实测参数，含原位改稿、表格模板填写、避坑清单 | `python-docx` |
| OCR 文本清洗 | `skills/chinese-ocr-txt-cleaning` | 清洗扫描件 / 阅读器 OCR 出来的脏文本，去水印噪声、修断行、还原段落 | 无 |
| 像素风网页 | `skills/pixel-art-web` | 用字符串点阵加 CSS grid 做像素角色、看板、小动画 | 无 |
| 飞书发文件 | `skills/feishu-file-send` | 走飞书开放 API 上传并发送文件到群或私聊 | 飞书自建应用 |
| GitHub 镜像访问 | `skills/github-mirror-access` | 国内被墙时访问与推送 GitHub：镜像探测、API 直连、SSH over 443、开源上架 | `git` `ssh` |
| Clash 代理复用 | `skills/clash-proxy-bypass` | Windows 上复用本机 Clash 代理抓海外站点，含端口探测与回落 | Clash |
| 拦页恢复 | `skills/blocked-page-recovery` | 遇到 403/429/paywall/WAF 时的降级抓取路线 | 无 |
| GB/T 7714 引用 | `skills/academic-citation-format` | 参考文献著录格式、引用序号、正文与文献表对账 | 无 |
| docx 原位改稿 | `skills/docx-inplace-revision` | 在现成 Word 上原位替换保格式，防编号双层与语义撞车 | `python-docx` |
| docx 模板填写 | `skills/docx-template-filling` | 往机构模板里原位填内容，填完转 PDF 目检 | `python-docx` `pymupdf` |
| 程序化 PDF | `skills/pdf-generation` | fpdf2 生成 PDF：中文字体、表格排版、A4 页眉页脚、生成后验证 | `fpdf2` |
| 万方查题录 | `skills/cnki-wanfang-bibliography` | 知网打不开时走万方补参考文献页码、核题录真伪 | 无 |
| 网页抓取 | `skills/web-scraper` | 中文站与海外站的通用抓取：评论区、评分、结构化提取 | `playwright` |



## 安装

把技能目录整个复制进你的 skills 目录，二选一：

```
# 桌面版
<HERMES_HOME>/skills/xiaoliuren-analysis/
# 命令行版
~/.hermes/skills/xiaoliuren-analysis/
```

装依赖：

```bash
pip install pytz ephem
pip install playwright && playwright install msedge
```

## 两点说明

**排盘类**：城市库覆盖 469 个城市。真太阳时校正和节气定位依赖 `ephem`，缺了会退回近似算法，精度会掉。

**爬取类**：走本机已登录的浏览器（Edge / Chrome），只读取你本来就能看到的内容。请自己控制频率、遵守目标站点的服务条款，账号风险自行承担。

## 免责

占卜与命理内容属于传统文化娱乐，不构成任何医疗、投资、婚恋或职业建议。信不信都行，别拿它替代专业意见。

## License

MIT
