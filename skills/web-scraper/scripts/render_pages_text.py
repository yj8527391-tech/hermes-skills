#!/usr/bin/env python3
"""批量渲染 JS 单页应用 / 云厂商价格页，导出每页 innerText + 价格正则命中。

用法:
    python render_pages_text.py out_dir https://a.com https://b.com
    python render_pages_text.py out_dir --file urls.txt
    python render_pages_text.py out_dir --file urls.txt --wait 8000 --scroll 3000 --headed

输出:
    out_dir/<slug>.txt      每页渲染后的 innerText
    out_dir/_summary.json   {slug: {url, len, price_hits[], error?}}
    控制台同时打印价格命中预览

要点 (2026-09 实测):
- 用系统自带 Edge (channel='msedge')，无需下载 Chromium；Windows/Linux/macOS 有 Edge 即可
- domcontentloaded + wait_for_timeout 拿客户端渲染结果（价格页往往要 5-8s）
- mouse.wheel 滚动触发懒加载/IntersectionObserver 卡片
- 厂商活动页/购买页/定价页静态 HTML 里价格是 0 条，必须渲染
- 登录后才显示的价格会渲染成「询价中」/方块占位 —— 这类拿不到就别编数字
"""
import argparse
import asyncio
import json
import pathlib
import re
import sys

from playwright.async_api import async_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
PRICE = re.compile(r".{0,50}?\d+(?:\.\d+)?\s*元\s*/?\s*(?:月|年|1个月|1年).{0,50}")


def slug(url: str) -> str:
    s = re.sub(r"^https?://", "", url)
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", s)
    return (s[:80] or "page").strip("_")


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("urls", nargs="*")
    ap.add_argument("--file", help="每行一个 URL 的文件（# 开头忽略）")
    ap.add_argument("--wait", type=int, default=6000, help="渲染后等待毫秒，默认 6000")
    ap.add_argument("--scroll", type=int, default=3000, help="滚动像素，0=不滚")
    ap.add_argument("--headed", action="store_true", help="显示浏览器窗口（调试用）")
    ap.add_argument("--channel", default="msedge", help="浏览器 channel，默认 msedge")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.file:
        urls += [ln.strip() for ln in pathlib.Path(args.file).read_text(encoding="utf-8").splitlines()
                 if ln.strip() and not ln.startswith("#")]
    if not urls:
        sys.exit("no urls given (positional or --file)")

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel=args.channel,
            headless=not args.headed,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(locale="zh-CN",
                                        viewport={"width": 1600, "height": 1200},
                                        user_agent=UA)
        page = await ctx.new_page()
        for url in urls:
            name = slug(url)
            try:
                await page.goto(url, timeout=50000, wait_until="domcontentloaded")
                await page.wait_for_timeout(args.wait)
                if args.scroll:
                    try:
                        await page.mouse.wheel(0, args.scroll)
                        await page.wait_for_timeout(2500)
                    except Exception:
                        pass
                txt = await page.evaluate("document.body.innerText") or ""
                txt = re.sub(r"\n{3,}", "\n", txt)
                (out / f"{name}.txt").write_text(txt, encoding="utf-8")
                hits = [" ".join(h.split()) for h in PRICE.findall(txt)]
                summary[name] = {"url": url, "len": len(txt), "price_hits": hits[:20]}
                print(f"[OK] {name} len={len(txt)} price_hits={len(hits)}", flush=True)
                for h in hits[:10]:
                    print("   $ " + h, flush=True)
            except Exception as e:  # noqa: BLE001 - 逐站容错，不中断整批
                summary[name] = {"url": url, "error": str(e)[:200]}
                print(f"[ERR] {name} {str(e)[:160]}", flush=True)
        await browser.close()

    (out / "_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {len(summary)} page(s) -> {out}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
