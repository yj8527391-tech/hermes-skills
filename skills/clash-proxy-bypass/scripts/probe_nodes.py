#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
探测哪条 Clash 专线节点能通目标 URL（2026-08 实测：codeload.github.com 只有香港 01/03 专线能通）。
用法:
  python probe_nodes.py <URL> [--node "香港 01 | 专线" ...]
  python probe_nodes.py https://codeload.github.com/<owner>/<repo>/tar.gz/<sha>

前置: Clash 临时内核已拉起（clash_proxy.start_temporary()），控制 API 在 127.0.0.1:19090，
代理端口 7897。脚本会依次切节点 → 带 Range 头请求 URL（codeload 会忽略 Range 返回全文，
正好验证大文件传输稳定性）→ 打印每个节点的结果。
"""
import json
import sys
import time
import urllib.request

CTRL = "http://127.0.0.1:19090"
PROXY = "http://127.0.0.1:7897"

DEFAULT_NODES = [
    "香港 01 | 专线",
    "香港 03 | 专线",
    "香港 04 | 专线 | 20倍流量",
    "香港 06 | 专线 | 20倍流量",
    "日本 01 | 专线",
    "日本 02 | 专线 | 20倍流量",
    "新加坡 01 | 专线",
    "新加坡 02 | 专线 | 20倍流量",
]


def switch(name: str) -> None:
    req = urllib.request.Request(
        CTRL + "/proxies/GLOBAL",
        data=json.dumps({"name": name}).encode(),
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=8) as r:
        assert r.status == 204, r.status


def test(url: str) -> str:
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-65535"}
    )
    try:
        t0 = time.time()
        with opener.open(req, timeout=25) as r:
            body = r.read()
            return f"OK {r.status} bytes={len(body)} {time.time()-t0:.1f}s"
    except Exception as e:
        return f"FAIL {type(e).__name__}: {str(e)[:80]}"


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    url = args[0]
    nodes = DEFAULT_NODES
    # --node "名称" 可多次指定自定义节点列表
    if "--node" in sys.argv:
        i = sys.argv.index("--node")
        nodes = sys.argv[i + 1:]

    for name in nodes:
        try:
            switch(name)
            time.sleep(1.5)
            print(f"{name}: {test(url)}", flush=True)
        except Exception as e:
            print(f"{name}: SWITCH-FAIL {e}", flush=True)


if __name__ == "__main__":
    main()
