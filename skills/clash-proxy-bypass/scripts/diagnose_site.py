# -*- coding: utf-8 -*-
"""
网站「打不开」快速诊断：直连 vs 代理 vs 代理健康，四行输出一键判定。
用法:  python diagnose_site.py [URL]     默认 https://map.dishisanceng.com/
依赖:  clash_proxy.py（hermes-home/scripts/）——自动复用常驻 Verge 或临时拉起内核，
       用完只杀自己拉起的进程，绝不动 Clash Verge 常驻。找不到则降级为裸测。

判定矩阵:
  直连200 + 代理超时   -> 站反代理/限境外IP，裸连即可，千万别开代理
  直连200 + 代理200    -> 站活着且代理也能开；用户打不开 = 浏览器代理残留/缓存，切直连或清DNS
  直连超时 + 代理204   -> 被墙，走代理抓
  直连超时 + 代理也超时 -> 站挂了或线路问题（看代理健康行区分是代理坏还是站坏）
"""
import sys
import re
import urllib.request

PROXY = "http://127.0.0.1:7897"


def fetch(url, proxy=None, timeout=12):
    handlers = [urllib.request.ProxyHandler({"http": proxy, "https": proxy})] if proxy else []
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    try:
        with opener.open(req, timeout=timeout) as r:
            head = r.read(8192).decode("utf-8", errors="ignore")
            m = re.search(r"<title>(.*?)</title>", head)
            return f"HTTP {r.status}", (m.group(1).strip() if m else "")
    except Exception as e:
        return f"{type(e).__name__}", str(e)[:90]


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://map.dishisanceng.com/"
    try:
        sys.path.insert(0, r"E:\Hermes Agent CN Desktop\data\hermes-home\scripts")
        import clash_proxy as cp
        cp.start_temporary()
    except Exception as e:
        print(f"⚠️ clash_proxy 不可用（降级裸测）: {str(e)[:80]}")
    d, dt = fetch(url)
    print(f"直连:        {d}  {dt}")
    p, pt = fetch(url, PROXY)
    print(f"代理:        {p}  {pt}")
    h, _ = fetch("https://www.google.com/generate_204", PROXY, timeout=10)
    print(f"代理健康:    {h}  (Google 204)")
    try:
        cp.stop_temporary()
    except Exception:
        pass


if __name__ == "__main__":
    main()
