# -*- coding: utf-8 -*-
"""_term_sweep.py — 术语存量回扫：按《11_论文模板与工具/术语速查表.md》的
首选译名/常见异译对照，扫描 05/07/08/10/11 语料的出现频次，产出报告
_工具脚本/术语回扫报告.md；并对纯音译差异的等义词对做安全替换（--apply）。

替换原则（宁窄勿宽）：只替换「纯音译差异、语义完全等义」的三组
（蒙地卡罗→蒙特卡洛 / 傅立叶→傅里叶 / 史蒂芬-玻尔兹曼→斯特藩-玻尔兹曼）；
其余异译（如"大气制动"在特定语境下成立）只在报告中列出，替换决策留给人。
"""
import os, sys, re, io, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ["05_论文赏析", "07_题目解读", "08_物理模型综述", "10_论文精读", "11_论文模板与工具"]
APPLY_PAIRS = [("蒙地卡罗", "蒙特卡洛"), ("傅立叶", "傅里叶"), ("史蒂芬-玻尔兹曼", "斯特藩-玻尔兹曼")]

def term_pairs():
    """从术语速查表解析（首选, [异译...]）——只取有异译的行"""
    txt = open(os.path.join(ROOT, "11_论文模板与工具", "术语速查表.md"), encoding="utf-8").read()
    pairs = []
    for ln in txt.split("\n"):
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", ln)
        if not m or m.group(1).strip() in ("英文", "---"):
            continue
        alt = m.group(3).strip()
        if alt in ("—", ""):
            continue
        alts = [a.strip() for a in re.split(r"[、,，/]", alt) if a.strip()]
        pairs.append((m.group(2).strip(), alts))
    return pairs

def corpus():
    out = []
    for d in SCAN_DIRS:
        for f in glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True):
            if os.path.basename(f) == "术语速查表.md":
                continue   # 排除术语表自身（异译列会造成自引用计数）
            out.append(f)
    return out

def main(apply=False):
    pairs = term_pairs()
    files = corpus()
    rows = []
    replaced = {}
    for pref, alts in pairs:
        c_pref = sum(open(f, encoding="utf-8", errors="replace").read().count(pref) for f in files)
        for a in alts:
            c_alt = sum(open(f, encoding="utf-8", errors="replace").read().count(a) for f in files)
            if c_alt == 0 and c_pref == 0:
                continue
            rows.append((pref, a, c_pref, c_alt))
            if apply and a in [p[0] for p in APPLY_PAIRS]:
                tgt = dict(APPLY_PAIRS)[a]
                for f in files:
                    t = open(f, encoding="utf-8", errors="replace").read()
                    if a in t:
                        n = t.count(a)
                        open(f, "w", encoding="utf-8", newline="\n").write(t.replace(a, tgt))
                        replaced[a] = replaced.get(a, 0) + n
    rep = ["# 术语存量回扫报告（2026-11-01）", "",
           "扫描范围：05/07/08/10/11 五个语料目录的全部 md；口径：字符串出现次数（含合理语境，非全部需要替换）。", "",
           "| 首选译名 | 异译 | 首选出现 | 异译出现 | 处理 |", "|---|---|---|---|---|"]
    for pref, a, cp, ca in sorted(rows, key=lambda r: -r[3]):
        act = "已替换（纯音译等义）" if (apply and ca > 0 and a in dict(APPLY_PAIRS)) else ("报告留观（语境相关）" if ca else "—")
        rep.append(f"| {pref} | {a} | {cp} | {ca} | {act} |")
    if apply and replaced:
        rep.append("")
        rep.append("## 本轮已替换")
        rep += [f"- {k} → {dict(APPLY_PAIRS)[k]}：{v} 处" for k, v in replaced.items()]
    rep.append("")
    rep.append("替换原则：仅纯音译等义三组自动替换；其余异译（如「大气制动」）在具体语境下可能成立，替换决策人工逐处判断。")
    out = os.path.join(ROOT, "_工具脚本", "术语回扫报告.md")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(rep))
    print("report:", out, "| pairs:", len(rows), "| replaced:", replaced if apply else "(dry-run)")

if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
