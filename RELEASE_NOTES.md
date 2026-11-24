# v1.0.0 — 17 个中文 Hermes 技能

首个公开版。全部为简体中文撰写，写法是「先给结论、再给操作、最后列踩过的坑」，不是英文文档的翻译腔。

## 收录

**命理排盘**

- `xiaoliuren-analysis` 小六壬占卜：农历月日时三数起课，六宫掌诀，末尾附锐评
- `bazi-analysis` 八字人生报告：真太阳时校正、五行能量、大运流年 -5~+5 评分、喜用神定位、健康预警。城市库覆盖 469 城

**内容与数据**

- `xiaohongshu-scraper` 小红书爬取：Playwright 调本机浏览器登录，抓 JS 渲染内容，导出 Excel
- `web-scraper` 通用网页抓取：中文站与海外站的评论区、评分、结构化提取
- `chinese-ocr-txt-cleaning` OCR 文本清洗：去水印噪声、修断行、还原段落
- `pixel-art-web` 像素风网页：字符串点阵 + CSS grid，做角色、看板、小动画

**文档生产**

- `markdown-to-docx` md 转 Word：实测参数、原位改稿、表格模板填写、避坑清单
- `docx-inplace-revision` 原位改稿：保格式替换，防编号双层与语义撞车
- `docx-template-filling` 模板填写：往机构模板填内容，转 PDF 目检
- `pdf-generation` 程序化 PDF：fpdf2 中文字体、表格排版、页眉页脚、生成后验证
- `academic-citation-format` GB/T 7714：著录格式、引用序号、正文与文献表对账

**国内环境**

- `github-mirror-access` GitHub 镜像访问：镜像探测、API 直连、SSH over 443 推送、开源上架流程
- `clash-proxy-bypass` Clash 代理复用：端口探测与回落
- `blocked-page-recovery` 拦页恢复：403 / 429 / paywall / WAF 的降级路线
- `cnki-wanfang-bibliography` 万方查题录：知网打不开时补页码、核真伪
- `feishu-file-send` 飞书发文件：开放 API 上传发送
- `company-due-diligence` 企业背调：招聘会批量背调，三轮筛选、分层打分、薪资比价

## 安装

把 `skills/<名字>/` 整个复制到你的 skills 目录：

```
<HERMES_HOME>/skills/    # 桌面版
~/.hermes/skills/        # 命令行版
```

依赖按需装：

```bash
pip install pytz ephem python-docx fpdf2 pymupdf
pip install playwright && playwright install msedge
```

## 说明

- 命理类技能属于传统文化娱乐，不构成医疗、投资、婚恋或职业建议
- 爬取类技能走本机已登录浏览器，只读你本来就能看到的内容，请自控频率并遵守目标站点条款

## 踩坑记录（本版最有价值的部分）

- WPS 打开文档时 `python-docx` 报 `PermissionError`：不要 kill 进程，会丢未保存内容
- Word 表格末尾自动补空段落，会把正文顶出空白页：需要在 `sectPr` 前插 1 磅零间距段落
- Word COM 一个实例只能开一个文档，第二个 `Open` 报 `unknown.Open`，必须分进程
- GitHub 的 SSH 443 端口在 `ssh.github.com`，不是 `github.com:443`，用错会「指纹对上但连接被掐」
