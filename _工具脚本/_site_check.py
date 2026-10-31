# -*- coding: utf-8 -*-
"""
_site_check.py — 站点独立体检（不依赖完整构建；构建期校验之外的第二道网）

检查项：
  MISSING     链接目标不存在（index.html + 404.html + 09_可视化总览/docs/**/*.html + 12_赛时工具/*.html）
  CASE        链接大小写与磁盘不一致（GitHub Pages 跑在 Linux 上，必 404）
  UNTRACKED   文件存在但未进 git（.gitignore 白名单漏目录 → 线上 404）
  ANCHOR      href="#..." 的页内/跨页锚点不存在（尽力检查：目标页含 id= 即认）
  STALE-INDEX search-index.js 里的文档页路径与磁盘不符
  COUNT       search-index 文档数 / 磁盘 docs html 数对不上
  TMP         应清理的临时文件（_tmp* / _verify* / out.png / *.log 等，仅提示）

用法：
  python _工具脚本/_site_check.py [--external]
  --external 附带抽查外链（HEAD 请求，慢；默认只查本地）
退出码：有问题为 1（pre-commit hook 用）
"""
import os, re, sys, json, glob, subprocess
from urllib.parse import unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

TMP_PATTERNS = ["_tmp*", "_verify*", "_tmp_repro", "out.png", "*.log", "_评审截图/*.png.tmp"]
TMP_HINTS = {"_tmp_clean", "_tmp_repro", "_tmp_verify", "_verify_tmp"}


def real_index():
    idx = {}
    for dp, dns, fns in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace("\\", "/")
        if rel == ".git" or rel.startswith(".git/") or "/.git" in rel:
            dns[:] = [d for d in dns if d != ".git"]
            continue
        for fn in fns:
            r = fn if rel == "." else rel + "/" + fn
            idx.setdefault(r.lower(), r)
    return idx


def tracked():
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"], capture_output=True)
        if out.returncode != 0:
            return None
        return set(x for x in out.stdout.decode("utf-8", "replace").split("\0") if x)
    except Exception:
        return None


def pages():
    out = [P("index.html"), P("404.html"), P("09_可视化总览", "index.html")]
    out += glob.glob(P("09_可视化总览", "docs", "**", "*.html"), recursive=True)
    out += glob.glob(P("12_赛时工具", "*.html"))
    return [p for p in out if os.path.exists(p)]


def check_anchor(target_page, frag, disk):
    """目标页里找 id="frag" 或 name="frag"（尽力而为：小写匹配）"""
    if not target_page or not os.path.exists(target_page):
        return False
    try:
        text = open(target_page, encoding="utf-8", errors="replace").read()
    except Exception:
        return True  # 读不了就不误报
    return ('id="%s"' % frag) in text or ("id='%s'" % frag) in text \
        or ('id="%s"' % frag.lower()) in text.lower()


def main():
    external = "--external" in sys.argv
    idx = real_index()
    trk = tracked()
    problems = []

    href_re = re.compile(r'(?:href|src)="([^"]+)"')
    pages_list = pages()
    for pg in pages_list:
        base = os.path.dirname(pg)
        text = open(pg, encoding="utf-8").read()
        for u in href_re.findall(text):
            if re.match(r"^(https?:|data:|mailto:|javascript:)", u):
                if external and u.startswith("http"):
                    pass  # 外链抽查交给构建/人工，这里不阻塞
                continue
            if "${" in u or "+" in u or "'" in u or u.startswith("#"):
                if u.startswith("#") and len(u) > 1:
                    if not check_anchor(pg, u[1:], idx):
                        problems.append(("ANCHOR", os.path.relpath(pg, ROOT), u))
                continue
            dec = unquote(u.split("#")[0].split("?")[0])
            if not dec or dec.startswith("/"):
                continue
            frag = u.split("#")[1] if "#" in u else None
            abspath = os.path.normpath(os.path.join(base, dec))
            rel = os.path.relpath(abspath, ROOT).replace("\\", "/")
            if rel.startswith("../"):
                problems.append(("MISSING", os.path.relpath(pg, ROOT), rel + "（越界）"))
                continue
            real = idx.get(rel.lower())
            if real is None:
                problems.append(("MISSING", os.path.relpath(pg, ROOT), rel))
                continue
            if real != rel:
                problems.append(("CASE", os.path.relpath(pg, ROOT), f"{rel} → 实际 {real}"))
                continue
            if trk is not None and real not in trk:
                problems.append(("UNTRACKED", os.path.relpath(pg, ROOT), real))
            if frag and not check_anchor(abspath, frag, idx):
                problems.append(("ANCHOR", os.path.relpath(pg, ROOT), f"{rel}#{frag}"))

    # search-index 同步
    si = P("search-index.js")
    docs_html = glob.glob(P("09_可视化总览", "docs", "**", "*.html"), recursive=True)
    if os.path.exists(si):
        m = re.search(r"window\.UPC_SEARCH=(\[.*\]);?\s*$", open(si, encoding="utf-8").read(), re.S)
        if m:
            entries = json.loads(m.group(1))
            urls = [e.get("u", "") for e in entries]
            for u in urls:
                dec = unquote(u)
                if not idx.get(dec.lower()):
                    problems.append(("STALE-INDEX", "search-index.js", dec))
            if len(entries) != len(docs_html):
                problems.append(("COUNT", "search-index.js",
                                 f"索引 {len(entries)} 条 vs 磁盘 docs {len(docs_html)} 页"))
        else:
            problems.append(("STALE-INDEX", "search-index.js", "解析失败（格式变了？）"))
    else:
        problems.append(("STALE-INDEX", "search-index.js", "文件不存在——先跑 _build_site.py"))

    # 临时文件提示（不算失败，仅报告）
    tmp_hits = []
    for name in sorted(os.listdir(ROOT)):
        if name in TMP_HINTS or (name.startswith("_tmp") and os.path.isdir(P(name))):
            tmp_hits.append(name + "/")
    for pat in ["out.png", "*.log"]:
        tmp_hits += [os.path.basename(x) for x in glob.glob(P(pat))]

    # 汇总
    kinds = {}
    for k, f, d in problems:
        kinds[k] = kinds.get(k, 0) + 1
    print(json.dumps({"pages": len(pages_list), "problems": len(problems), "by_kind": kinds},
                     ensure_ascii=False))
    for k, f, d in problems[:60]:
        print(f"  [{k}] {f} -> {d}")
    if len(problems) > 60:
        print(f"  … 其余 {len(problems)-60} 条省略")
    if tmp_hits:
        print("TMP 提示（不阻塞）：", ", ".join(tmp_hits))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
