# -*- coding: utf-8 -*-
"""一次配好仓库元数据 + 建 Release。用法：python apply_meta.py <PAT>"""
import json, sys, io, urllib.request, urllib.error

if len(sys.argv) < 2:
    print('用法: python apply_meta.py <github_pat>')
    sys.exit(1)

TOKEN = sys.argv[1].strip()
REPO = 'yj8527391-tech/hermes-skills'
API = 'https://api.github.com'

DESC = ('一组中文 Hermes Agent 技能：小六壬、八字命理、小红书爬取、企业背调、'
        'md 转 Word、OCR 清洗、像素风网页、飞书发文件等 17 个')

TOPICS = ['hermes', 'ai-agent', 'skills', 'chinese', 'bazi', 'playwright',
          'python-docx', 'fpdf2', 'web-scraping', 'prompt-engineering']

BODY = io.open(r'E:\hermes_memes\hermes-skills\RELEASE_NOTES.md', encoding='utf-8').read()


def call(method, path, payload=None):
    url = API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + TOKEN)
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('User-Agent', 'hermes-skills')
    if data:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


print('1) 写 description')
print('  ', call('PATCH', f'/repos/{REPO}', {'description': DESC})[0])

print('2) 写 topics')
print('  ', call('PUT', f'/repos/{REPO}/topics', {'names': TOPICS})[0])

print('3) 建 Release v1.0.0')
st, body = call('POST', f'/repos/{REPO}/releases', {
    'tag_name': 'v1.0.0',
    'name': 'v1.0.0 — 17 个中文 Hermes 技能',
    'body': BODY,
    'draft': False,
    'prerelease': False,
})
print('  ', st)
if st in (200, 201) and isinstance(body, dict):
    print('  Release:', body.get('html_url'))
else:
    print('  ', body)

print('\n4) 回读校验')
st, repo = call('GET', f'/repos/{REPO}')
if isinstance(repo, dict):
    print('  description:', repo.get('description'))
    print('  topics:', ', '.join(repo.get('topics', [])))
    print('  html_url:', repo.get('html_url'))
