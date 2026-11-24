#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把选定的技能清洗后复制进公开仓库。

用法：改 SKILLS / DST / EXCLUDE_FILES 后直接 python build_public_repo.py
跑完看最后「残留检查」，必须为 0（或人工确认可接受）。
"""
import os, re, shutil, io

SRC = r'E:\Hermes Agent CN Desktop\data\hermes-home\skills'
DST = r'~\hermes-skills\skills'

WAIT = [
    # r'research\company-due-diligence',
    # r'productivity\markdown-to-docx',
]

EXCLUDE_FILES = set()  # 相对 DST 的路径，如 'productivity\\markdown-to-docx\\scripts\\ysxy_docx.py'

REPS = [
    (r'用户_简历[^\s`\'"]*\.docx', 'resume.docx'),
    (r'用户', '用户'),
    (r'某院校', '某院校'),
    (r'院校', '院校'),
    (r'目标院校', '目标院校'),
    (r'资料', '资料'),
    (r'助手', '助手'),
    (r'助手', '助手'),
    (r'C:\\\\Users\\\\ASUS', '~'),
    (r'~', '~'),
    (r'<手机号>', '<手机号>'),
    (r'<qq号>@qq\.com', '<邮箱>'),
    (r'<github-user>@gmail\.com', '<邮箱>'),
    (r'wxid_[0-9a-z]+', '<wxid>'),
]

TEXT_EXT = {'.md', '.py', '.json', '.txt', '.html', '.css', '.js', '.yaml', '.yml'}
BLACK = re.compile(r'用户|目标院校|考研|助手|助手|<手机号>|wxid_[0-9a-z]|USERS\\\\ASUS|<qq号>|<github-user>')


def convert(path):
    txt = io.open(path, encoding='utf-8', errors='ignore').read()
    new = txt
    for pat, rep in REPS:
        new = re.sub(pat, rep, new)
    if new != txt:
        io.open(path, 'w', encoding='utf-8').write(new)


for rel in WAIT:
    s, d = os.path.join(SRC, rel), os.path.join(DST, os.path.basename(rel))
    if os.path.exists(d):
        shutil.rmtree(d)
    shutil.copytree(s, d, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for dp, dn, fn in os.walk(d):
        for f in fn:
            fp = os.path.join(dp, f)
            if os.path.relpath(fp, DST) in EXCLUDE_FILES:
                os.remove(fp)
                print('EXCLUDED', os.path.relpath(fp, DST))
                continue
            if os.path.splitext(f)[1].lower() in TEXT_EXT:
                convert(fp)
    print('COPIED', rel)

print()
bad = 0
for dp, dn, fn in os.walk(DST):
    for f in fn:
        fp = os.path.join(dp, f)
        try:
            hits = BLACK.findall(io.open(fp, encoding='utf-8', errors='ignore').read())
        except Exception:
            continue
        if hits:
            bad += 1
            print('  残留', os.path.relpath(fp, DST), set(hits))
print('残留文件数:', bad, '(必须为 0 或人工确认可接受)')
