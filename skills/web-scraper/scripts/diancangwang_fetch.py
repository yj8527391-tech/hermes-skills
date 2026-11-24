# -*- coding: utf-8 -*-
"""中华典藏网 (diancangwang.cn) 中文剧本全文抓取脚本
用法:
    python diancangwang_fetch.py <目录URL> <输出txt路径> [--verify 本地已知剧本路径]
示例:
    python diancangwang_fetch.py https://www.diancangwang.cn/shicixiqu/6bf3ba026be7/ E:\tmp\北京人.txt
    python diancangwang_fetch.py <toc_url> out.txt --verify local_act1.txt

流程: 抓目录页 -> 找"第X幕"链接 -> 逐幕抓正文 -> 清洗站点水印/导航残留
      -> (可选)与本地已知版本关键台词比对验证 -> 输出 UTF-8 全文
实测 2026-08-31《北京人》: 三幕齐全(第三幕分两景), 无验证码无反爬。
"""
import re
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0'}


def fetch(url):
    """编码探测抓取: 页面 charset=utf-8 但直接 r.text 会乱码, 必须 content.decode"""
    r = requests.get(url, headers=HEADERS, timeout=30)
    for enc in ('utf-8', 'gb18030', 'gbk'):
        try:
            return r.content.decode(enc)
        except Exception:
            continue
    return r.text


def extract_body(html):
    """正文容器选择: 常见容器 -> 兜底取文本最长的 div"""
    soup = BeautifulSoup(html, 'lxml')
    for sel in ('div#content', 'div.content', 'article', '.article-content',
                '.showtxt', '#chaptercontent'):
        el = soup.select_one(sel)
        if el:
            return el.get_text('\n', strip=True)
    return max((d.get_text('\n', strip=True) for d in soup.find_all('div')), key=len)


def clean(text):
    """清洗两坑:
    1. 站点水印穿插行间: 形如 `DFT中华典藏网` / `PZo中华典藏网`(随机1-4位字母数字前缀+站名)
    2. 导航残留被换行拆开: `首页 > 诗词戏曲 > X > 第X幕` 变多行, 单行 replace 匹配不到
    """
    text = re.sub(r'[A-Za-z0-9]{1,4}中华典藏网', '', text)
    text = text.replace('中华典藏网', '')
    text = re.sub(
        r'首页\s*\n?\s*>\s*\n?\s*诗词戏曲\s*\n?\s*>\s*\n?\s*[^>\n]+\s*\n?\s*>\s*\n?\s*(第[一二三]幕|[^>\n]+)\s*\n?',
        '', text)
    text = re.sub(r'上一章\s*返回目录\s*下一章', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def find_act_links(toc_html):
    """目录页找分幕链接: 匹配 第X幕/章/前言/序"""
    soup = BeautifulSoup(toc_html, 'lxml')
    links = []
    for a in soup.find_all('a', href=True):
        t = a.get_text(strip=True)
        if t and re.search(r'幕|章|前言|序', t):
            h = a['href']
            if not h.startswith('http'):
                h = 'https://www.diancangwang.cn' + h if h.startswith('/') else \
                    'https://www.diancangwang.cn/shicixiqu/' + h.lstrip('/')
            links.append((t, h))
    return links


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    toc_url = sys.argv[1]
    out_path = sys.argv[2]
    verify_path = None
    if '--verify' in sys.argv:
        verify_path = sys.argv[sys.argv.index('--verify') + 1]

    print('抓目录页:', toc_url)
    toc_html = fetch(toc_url)
    links = find_act_links(toc_html)
    if not links:
        print('!! 目录页未找到分幕链接, 页面可能改版')
        sys.exit(2)
    print(f'找到 {len(links)} 个分幕链接: {[t for t, _ in links]}')

    parts = []
    for name, url in links:
        body = clean(extract_body(fetch(url)))
        print(f'[{name}] chars={len(body)} head={body[:40]!r}')
        parts.append(f'《{name}》\n{body}')

    full = '\n\n\n'.join(parts)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(full)
    print(f'SAVED: {out_path} total_chars={len(full)}')

    # 可选验证: 与本地已知版关键台词比对 (从本地版里找独特短语)
    if verify_path:
        local = open(verify_path, encoding='utf-8').read()
        checks = ['它叫“孤独”', '你这两只巧手', '要杀就杀，要打就打', '成为他永远的奴隶']
        hit = sum(1 for c in checks if c in full and c in local)
        print(f'关键台词比对: {hit}/{len(checks)} 命中本地版 -> {"可信" if hit >= 3 else "可疑!"}')
        if hit < 3:
            sys.exit(3)


if __name__ == '__main__':
    main()
