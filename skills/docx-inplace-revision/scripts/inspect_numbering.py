"""列出 docx 中所有带自动编号（numPr）的段落，诊断“第一，第一，”这类双层编号。

用法：python inspect_numbering.py 文件.docx
"""
import sys

from docx import Document


def main(path):
    d = Document(path)
    hits = 0
    for i, p in enumerate(d.paragraphs):
        pPr = p._element.pPr
        if pPr is None or pPr.numPr is None:
            continue
        num = pPr.numPr
        num_id = num.numId.val if num.numId is not None else None
        ilvl = num.ilvl.val if num.ilvl is not None else None
        text = p.text.strip()
        print(f"[{i:3d}] numId={num_id} ilvl={ilvl} | {text[:70]}")
        hits += 1

    total = len(d.paragraphs)
    print(f"\n共 {hits} 段带自动编号 / 全文 {total} 段")
    if hits:
        print("提示：这些段落若字面已有「第一，」「[1]」之类编号，导出 PDF 会渲染成两层。")


def clear_numbering(path, prefixes, out=None):
    """删掉文本以指定前缀开头段落的自动编号，保留字面编号。

    clear_numbering('a.docx', ('第一，', '第二，'), 'b.docx')
    """
    d = Document(path)
    removed = 0
    for p in d.paragraphs:
        if not p.text.strip().startswith(prefixes):
            continue
        pPr = p._element.pPr
        if pPr is not None and pPr.numPr is not None:
            pPr.remove(pPr.numPr)
            removed += 1
    d.save(out or path)
    print(f"已清除 {removed} 段自动编号 -> {out or path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])
