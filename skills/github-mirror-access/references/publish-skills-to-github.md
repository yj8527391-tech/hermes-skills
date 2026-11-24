# 把自己的技能/代码发布到 GitHub

2026-11-24 首次跑通（8 个中文 Hermes 技能上架本地仓库，等使用者挂 SSH key 后推）。被墙环境的传输层问题见主 SKILL.md「推送到 GitHub」。

## 一、先挑：什么能发，什么永远别发

拿 `skills_list` 或扫 `HERMES_HOME/skills/**/SKILL.md` 列出全部技能，分三档：

| 档 | 判断标准 | 处理 |
|---|---|---|
| ✅ 优先发 | **已在虾评等平台公开过**的技能（小六壬、八字人生报告、小红书爬取） | 零新增暴露风险，直接搬 |
| 🟡 清洗后可发 | 方法论类、通用工具类：企业背调、md 转 Word、OCR 清洗、像素风网页、飞书发文件 | 跑清洗脚本 + 人工复核 |
| ⛔ 永久不发 | 个人档案类：考研整套（目标院校/真题/书单）、院校论文排版、简历生成、受众研究、命理个人排盘 | 等于公开姓名/学校/志愿/生日 |

**版权红线**：Hermes 自带的几十个技能（`docx` `pdf` `xlsx` `mlops/*` 等）不是自己的作品，搬到个人仓库属侵权，一个都别碰。

## 二、隐私清洗（脚本化，别手工改）

`scripts/build_public_repo.py` 是实测跑过的版本：遍历技能目录 → 按替换表改写文本 → 再全量复查。替换表（按本机实测命中率排序）：

```python
REPS = [
    (r'用户_简历[^\s`\'"]*\.docx', 'resume.docx'),
    (r'用户', '用户'),
    (r'某院校', '某院校'),
    (r'院校', '院校'),
    (r'目标院校', '目标院校'),
    (r'资料', '资料'),
    (r'助手|助手', '助手'),
    (r'C:\\\\Users\\\\ASUS', '~'),
    (r'<手机号>', '<手机号>'),
    (r'<qq号>@qq\.com|<gmail>', '<邮箱>'),
    (r'wxid_[0-9a-z]+', '<wxid>'),
]
BLACK = re.compile(r'用户|目标院校|考研|助手|<手机号>|wxid_[0-9a-z]|USERS\\\\ASUS')
```

要点：
- **替换完必须再扫一遍 BLACK 并打印残留文件名**，别信一次性 replace
- 只处理文本扩展名（`.md .py .json .txt .html .css .js .yaml .yml`），二进制跳过
- 目录级排除：`__pycache__`、`*.pyc`；**文件级排除院校专用脚本**（如 `ysxy_docx.py` 里熔了本院通知模板/学时编号规则，清洗也没意义）
- 清洗会打断路径语义时手动补：`E:/资料/_scripts/md2docx.py` → `<脚本目录>/md2docx.py`（别让它变成 `E:/资料/_scripts/...` 这种怪路径）
- 残留的「考研」若只出现在**通用选题示例**里（如小红书爬虫的「考研经验分享」实测案例），属可接受，保留

## 三、仓库结构（实测够用的最小集）

```
<repo>/
├── README.md        中文：一句话定位 + 技能表格（目录/做什么/依赖）+ 安装 + 免责 + License
├── LICENSE          MIT
├── .gitignore       __pycache__/ *.pyc .DS_Store .vscode/ .idea/ *.log
├── push.sh          SSH over 443 一键推（用法 bash push.sh <用户名> [仓库名]）
└── skills/
    └── <skill-name>/  SKILL.md + scripts/ + references/
```

- README 的技能表用**目录相对路径**（`skills/xxx`），别用本机绝对路径
- 首次 commit 用中性身份，别用真名：`git config user.name "skill-keeper"` + `git config user.email "skill-keeper@users.noreply.github.com"`（公开仓库的 commit author 人人可见）
- 提交信息写清「新增 X / 修复 Y」，别一条 `update` 糊到底

## 四、交付话术

给使用者报三样：**仓库路径 + 已清洗项（表格列出来）+ 他只需要做的两三步（带链接、带公钥原文）**。中途失败别报「已完成」——`Permission denied (publickey)` 说明还差他挂 key，如实说。
