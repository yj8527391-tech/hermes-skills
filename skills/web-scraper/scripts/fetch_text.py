# -*- coding: utf-8 -*-
"""抓取网页正文文本 — 中文调研工作流的第二步（search → fetch → 交叉验证）

用法:
    python fetch_text.py <url> [outfile]

- 自动按 Content-Type charset 解码（多数中文站 utf-8/gbk）
- 剥离 script/style/标签，p/div/li/br 转行，输出 标题 + 清洗后正文
- 实测可抓: 搜狐(sohu.com)、网易号(163.com)、PHP中文网、卢松松博客、淘客导航等
- 实测被挡(需 agent-browser 或换源): post.smzdm.com、school.xiaohongshu.com(JS渲染)
- 抓下来后务必人工核对关键数字，与搜索摘要交叉验证再引用
"""
import sys, re, urllib.request, html as htmllib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.so.com/",
    })
    r = urllib.request.urlopen(req, timeout=30)
    data = r.read()
    enc = "utf-8"
    m = re.search(r"charset=([\w-]+)", r.headers.get("Content-Type", ""))
    if m:
        enc = m.group(1)
    return data.decode(enc, "ignore")

def extract_text(html):
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    tm = re.search(r"<title>(.*?)</title>", html, re.S)
    title = htmllib.unescape(tm.group(1)).strip() if tm else ""
    body = re.sub(r"<(br|/p|/div|/li|/h[1-6])[^>]*>", "\n", html)
    body = re.sub(r"<[^>]+>", " ", body)
    body = htmllib.unescape(body)
    body = re.sub(r"[ \t\u00a0]+", " ", body)
    body = re.sub(r"\n\s*\n+", "\n", body)
    return title, body

if __name__ == "__main__":
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        html = fetch(url)
        title, body = extract_text(html)
        text = "URL: %s\nTITLE: %s\n\n%s" % (url, title, body)
        if out:
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            print("saved ->", out, "len:", len(body))
        else:
            print(text[:6000])
    except Exception as e:
        print("ERROR", url, e)
