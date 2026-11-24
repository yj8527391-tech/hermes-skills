# -*- coding: utf-8 -*-
"""
点阵像素画 → 交付 PNG（整数倍缩放 + 居中透明底 + 总览图拼接）

用法:
    python render_pixels_png.py spec.json [out_dir]

spec.json 结构:
{
  "canvas": 320,
  "bg": "#fafafc",            # 总览图底色；单个 sprite 用透明底
  "chars": [
    {"name": "alice",
     "palette": {"K":"#1f1f2e", "B":"#fce4d6", ".":null},
     "art": ["..KK..", ".KBBK.", "..KK.."]},
    {"name": "doro", "palette": {...}, "art": [...]}
  ]
}

要点（都是踩过坑换来的）:
  - 必须整数倍缩放（Image.NEAREST）；插值会让像素块发虚
  - 缩到高度贴住 canvas 后水平居中贴在 canvas×canvas 透明画布上
  - 每个角色用**独立 palette**，别共用字母表（同字母不同色会互相覆盖）
  - art 每行长度必须一致；本脚本会先校验并报错
"""
import json
import os
import sys

from PIL import Image


def _hex_rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def check_art(art):
    """校验点阵：非空 + 每行等长"""
    if not art:
        raise ValueError("art 为空")
    lens = {len(r) for r in art}
    if len(lens) != 1:
        bad = [(i, len(r)) for i, r in enumerate(art) if len(r) != len(art[0])]
        raise ValueError(f"点阵每行长度不一致，行(索引,长度)={bad}")


def render_sprite(art, palette, canvas=320, transparent=True):
    """点阵 → canvas×canvas PNG（整数倍缩放 + 居中）"""
    check_art(art)
    rows, cols = len(art), len(art[0])
    scale = max(1, canvas // rows)          # 以高度贴边为准
    w, h = cols * scale, rows * scale

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y, row in enumerate(art):
        for x, ch in enumerate(row):
            col = palette.get(ch)
            if not col or col in ("transparent", "none"):
                continue
            r, g, b = _hex_rgb(col)
            for dy in range(scale):
                for dx in range(scale):
                    px[x * scale + dx, y * scale + dy] = (r, g, b, 255)

    bg = (0, 0, 0, 0) if transparent else (255, 255, 255, 255)
    big = Image.new("RGBA", (canvas, canvas), bg)
    big.paste(img, ((canvas - w) // 2, (canvas - h) // 2), img if transparent else None)
    return big, (w, h, scale)


def make_sheet(images, out_path, bg="#fafafc"):
    """把若干 canvas×canvas 图横向拼成总览图"""
    if not images:
        return None
    cw = images[0].width
    ch = images[0].height
    sheet = Image.new("RGB", (cw * len(images), ch), _hex_rgb(bg))
    for i, im in enumerate(images):
        sheet.paste(im, (i * cw, 0), im)
    sheet.save(out_path)
    return sheet


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(sys.argv[1]))
    os.makedirs(out_dir, exist_ok=True)

    canvas = int(spec.get("canvas", 320))
    made = []
    for c in spec.get("chars", []):
        name = c["name"]
        img, (w, h, scale) = render_sprite(c["art"], c.get("palette", {}), canvas)
        p = os.path.join(out_dir, f"{name}_{canvas}.png")
        img.save(p)
        made.append(img)
        print(f"{name}: {scale}x → {w}x{h} 居中到 {canvas}x{canvas} → {p}")

    if made:
        sp = os.path.join(out_dir, f"characters_{canvas}_sheet.png")
        make_sheet(made, sp, spec.get("bg", "#fafafc"))
        print("总览图:", sp, f"({canvas * len(made)}x{canvas})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
