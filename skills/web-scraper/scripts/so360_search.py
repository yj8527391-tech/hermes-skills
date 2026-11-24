# -*- coding: utf-8 -*-
"""
so360_search.py — 360 搜索 (so.com) 中文检索：标题 + 真实URL + 摘要 + 日期，结果存文件。

适用场景（2026-08 实测）：
- Bing 对含"小红书"等词的中文查询必拆词出垃圾（"小"字头词典/小游戏页）
- Baidu 对脚本请求返回验证码/空页（1488 字节）
- 360 对中文官方/新闻/平台内容索引好，搜索页 HTML 无需登录可直接解析

用法:
    python so360_search.py "小红书 AI生成内容 主动标识 公告" [结果数]

真实 URL 两种拿法（都实测有效）：
1. 每条结果 <a data-mdurl="https://真实地址"> 直接取属性；
2. 无 data-mdurl 时，so.com/link?m= 跳转页对普通 requests GET 返回 200 的小页面，
   内含 <script>window.location.replace("https://真实URL")</script>，正则提取即可。

依赖: pip install requests beautifulsoup4
"""
import sys, io, re, time
import requests
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}


def real_url(a):
    """优先 data-mdurl 属性；没有则解析 so.com/link JS 跳转页拿真实 URL。"""
    md = a.get('data-mdurl')
    if md:
        return md
    href = a.get('href', '')
    if 'so.com/link' not in href:
        return href
    try:
        r = requests.get(href, headers=H, timeout=20, allow_redirects=True)
        m = re.search(r'window\.location\.replace\("([^"]+)"\)', r.text)
        if m:
            return m.group(1)
        m2 = re.search(r"URL='([^']+)'", r.text)
        if m2:
            return m2.group(1)
        return r.url
    except Exception:
        return href


def search(q, n=10):
    r = requests.get('https://www.so.com/s', params={'q': q, 'pn': '1'}, headers=H, timeout=30)
    soup = BeautifulSoup(r.text, 'lxml')
    out = []
    for li in soup.select('li.res-list')[:n]:
        a = li.select_one('h3 a')
        if not a:
            continue
        snip_el = li.select_one('.res-desc, .res-desc2, p')
        date_el = li.select_one('.res-date, .fz-mid, .res-info')
        out.append({
            'title': a.get_text(strip=True),
            'url': real_url(a),
            'snippet': snip_el.get_text(strip=True)[:300] if snip_el else '',
            'date': date_el.get_text(strip=True) if date_el else '',
        })
        time.sleep(0.8)  # 风控：请求间隔 ≥0.8s
    return out


if __name__ == '__main__':
    q = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    res = search(q, n)
    print(f'===== 360 QUERY: {q} ({len(res)} results) =====')
    for i, it in enumerate(res, 1):
        print(f'[{i}] {it["title"]}')
        print(f'    DATE: {it["date"]}')
        print(f'    URL: {it["url"]}')
        print(f'    SNIP: {it["snippet"]}')
    fn = 'so360_' + re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '_', q)[:30] + '.txt'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(f'QUERY: {q}\n')
        for i, it in enumerate(res, 1):
            f.write(f'[{i}] {it["title"]}\nDATE: {it["date"]}\nURL: {it["url"]}\nSNIP: {it["snippet"]}\n\n')
    print(f'>>> saved: {fn}')
