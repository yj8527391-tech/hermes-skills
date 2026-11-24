# -*- coding: utf-8 -*-
"""
GB/T 7714 顺序编码制正文引用规范化：合并连续序号 + 全部设为上标。

依据：
  第 9.2.1.1 条  顺序编码制按正文引用先后连续编码，序号置于方括号中（标准示例用上标形式）
  第 9.2.1.2 条  同一处引用多篇文献，各序号在同一方括号内列出，用“，”分隔；
                 连续序号起讫间用短横线连接 → [9-12] 而非 [9][10][11][12]

只处理正文，参考文献条目本身（[1] 作者. 题名[J]. ...）保持原样不上标。
判据：段落以 [n] 开头 且（含 [J]/[M]/[D]/[N] 等类型标识 或 长度 > 60）→ 判为文献条目，跳过。

用法:
    python normalize_refs.py 论文.docx [更多.docx ...]
    python normalize_refs.py --check 论文.docx
"""
import sys, re, copy
import docx
from docx.oxml.ns import qn
from docx.text.run import Run

CITE = re.compile(r'\[[\d,\-]+\]')
CITE_RUN = re.compile(r'(?:\[\d+\]){2,}')
TYPEMARK = re.compile(r'\[(J|M|D|N|R|C|S|P|EB|DB|CP|A|Z|G)(/OL)?\]')


def is_ref_entry(text):
    t = text.strip()
    if not re.match(r'^\[\d+\]', t):
        return False
    return bool(TYPEMARK.search(t)) or len(t) > 60


def merge_cites(text):
    """[7][8][10] -> [7-8,10]"""
    def repl(m):
        nums = sorted(set(int(x) for x in re.findall(r'\[(\d+)\]', m.group(0))))
        out, i = [], 0
        while i < len(nums):
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            out.append('%d-%d' % (nums[i], nums[j]) if j - i >= 1 else str(nums[i]))
            i = j + 1
        return '[' + ','.join(out) + ']'
    return CITE_RUN.sub(repl, text)


def superscript_in_paragraph(p):
    n = 0
    for run in list(p.runs):
        txt = run.text
        if not txt or not CITE.search(txt) or run.font.superscript:
            continue
        parts = CITE.split(txt)
        marks = CITE.findall(txt)
        if not marks:
            continue
        seq = []
        for i, part in enumerate(parts):
            if part:
                seq.append((part, False))
            if i < len(marks):
                seq.append((marks[i], True))
        r_el = run._element
        parent = r_el.getparent()
        pos = parent.index(r_el)
        parent.remove(r_el)
        for k, (t2, sup) in enumerate(seq):
            new_r = copy.deepcopy(r_el)
            for t in new_r.findall(qn('w:t')):
                new_r.remove(t)
            t = new_r.makeelement(qn('w:t'), {})
            t.text = t2
            t.set(qn('xml:space'), 'preserve')
            new_r.append(t)
            parent.insert(pos + k, new_r)
            if sup:
                Run(new_r, p).font.superscript = True
                n += 1
    return n


def all_paragraphs(d):
    """含表格单元格；合并单元格会重复返回同一 XML 节点，按 id 去重。"""
    paras, seen = [], set()
    paras.extend(d.paragraphs)
    for tb in d.tables:
        for row in tb.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    if id(p._p) not in seen:
                        seen.add(id(p._p))
                        paras.append(p)
    return paras


def process(path):
    d = docx.Document(path)
    merged = sups = refs = 0
    for p in all_paragraphs(d):
        if is_ref_entry(p.text):
            refs += 1
            continue
        for run in p.runs:
            if CITE_RUN.search(run.text):
                run.text = merge_cites(run.text)
                merged += 1
        sups += superscript_in_paragraph(p)
    d.save(path)
    name = path.replace('\\', '/').split('/')[-1]
    print('%s  合并 %d 处 · 上标 %d 处 · 跳过文献条目 %d 段' % (name, merged, sups, refs))


def check(path):
    d = docx.Document(path)
    body_marks = body_sup = ref_entries = 0
    unmatched = []
    for p in all_paragraphs(d):
        if is_ref_entry(p.text):
            ref_entries += 1
            continue
        for run in p.runs:
            ms = CITE.findall(run.text)
            if ms:
                body_marks += len(ms)
                if run.font.superscript:
                    body_sup += len(ms)
                else:
                    unmatched.append(run.text[:30])
    name = path.replace('\\', '/').split('/')[-1]
    print('%s  文献 %d 条 · 正文引用 %d 处 · 已上标 %d 处' % (name, ref_entries, body_marks, body_sup))
    if unmatched:
        print('  未上标:', unmatched[:5])
    if body_marks == 0:
        print('  [!] 正文零引用：文献清单全挂着，评审必挑，回去补引用位置')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    if args[0] == '--check':
        for f in args[1:]:
            check(f)
    else:
        for f in args:
            process(f)
