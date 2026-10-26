# -*- coding: utf-8 -*-
"""_fetch_vendor.py — 把 KaTeX / Mermaid 拉到本地 09_可视化总览/vendor/

为什么自托管：这两个库原先都从 cdn.jsdelivr.net 加载，国内网络经常拿不到，
一旦失败就是全站公式变源码、流程图变文本。下载一次进仓库，从此零外网依赖。

用法：python _工具脚本/_fetch_vendor.py [--force]
源站默认 unpkg，可用 VENDOR_MIRROR 环境变量换成 npmmirror 等。
"""
import os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "09_可视化总览", "vendor")
MIRROR = os.environ.get("VENDOR_MIRROR", "https://unpkg.com")

KATEX_V = "0.16.11"
MERMAID_V = "10.9.1"
FILES = [
    (f"{MIRROR}/katex@{KATEX_V}/dist/katex.min.css", "katex/katex.min.css"),
    (f"{MIRROR}/katex@{KATEX_V}/dist/katex.min.js", "katex/katex.min.js"),
    (f"{MIRROR}/katex@{KATEX_V}/dist/contrib/auto-render.min.js", "katex/contrib/auto-render.min.js"),
    (f"{MIRROR}/mermaid@{MERMAID_V}/dist/mermaid.min.js", "mermaid/mermaid.min.js"),
]
UA = {"User-Agent": "Mozilla/5.0 upc-archive-builder"}


def get(url, dst, force=False):
    if os.path.exists(dst) and not force:
        print("  skip", os.path.relpath(dst, ROOT), f"({os.path.getsize(dst)//1024} KB)")
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(dst, "wb") as f:
        f.write(r.read())
    print("  ok  ", os.path.relpath(dst, ROOT), f"({os.path.getsize(dst)//1024} KB)")


def main():
    force = "--force" in sys.argv
    print(f"vendor mirror: {MIRROR}")
    for url, rel in FILES:
        get(url, os.path.join(VENDOR, *rel.split("/")), force)
    # katex.min.css 里引用的字体一并抓下来（缺字体公式会退化成替换字形）
    css = os.path.join(VENDOR, "katex", "katex.min.css")
    fonts = sorted(set(re.findall(r"fonts/(KaTeX_[A-Za-z0-9_-]+\.woff2)", open(css, encoding="utf-8").read())))
    print(f"fonts referenced: {len(fonts)}")
    for fn in fonts:
        get(f"{MIRROR}/katex@{KATEX_V}/dist/fonts/{fn}",
            os.path.join(VENDOR, "katex", "fonts", fn), force)
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(VENDOR) for f in fs)
    print(f"vendor total: {total/1048576:.2f} MB")


if __name__ == "__main__":
    main()
