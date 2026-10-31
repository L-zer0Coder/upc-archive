# -*- coding: utf-8 -*-
"""
_mine_phrases.py — 从 74 篇金牌论文全文（04_论文文本/）统计学术写作短语频次
为《中译英润色库》提供语料实证：一个句式值不值得学，看金牌队伍用得多不多。
输出 markdown 表格（短语 | 总频次 | 出现论文数 | 示例论文）。
"""
import os, re, glob, json
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)

# 精选学术短语（按论文部位分组），全部小写匹配
PHRASES = {
    "定义与判据": [
        "we define", "we call this", "we set", "we take ... to be", "by definition",
        "we interpret ... as", "we consider ... to be",
    ],
    "假设与简化": [
        "we assume", "we approximate", "to simplify", "without loss of generality",
        "we neglect", "is negligible", "to first order", "as a first approximation",
        "we further assume", "for simplicity",
    ],
    "建模与推导": [
        "it can be shown", "which gives", "this yields", "substituting ... into",
        "solving for", "we obtain", "leading to", "follows from", "consistent with",
    ],
    "数值方法": [
        "numerically integrated", "time step", "step size", "runge-kutta", "euler's method",
        "we simulated", "convergence", "grid", "boundary condition", "initial condition",
    ],
    "结果与论证": [
        "we conclude", "we find", "figure ... shows", "as shown in", "shown in table",
        "compared with", "in contrast", "on the other hand", "this suggests", "this indicates",
        "as expected", "sanity check", "agrees with",
    ],
    "误差与局限": [
        "uncertainty", "margin of error", "significant figures", "sensitivity",
        "we acknowledge", "limitation", "we neglect the", "out of the scope",
    ],
    "结论与建议": [
        "we recommend", "we would advise", "future work", "could be extended",
        "in conclusion", "further study",
    ],
}

# 归一化：把 "..."" 占位展开为正则
def phrase_regex(phrase):
    parts = [re.escape(p.strip()) for p in phrase.split("...")]
    return re.compile(r"\s+".join(parts).replace(r"\ ", r"\s+"), re.I)


def main():
    txts = sorted(glob.glob(P("04_论文文本", "*", "*.txt")))
    docs = {}
    for f in txts:
        docs[f] = open(f, encoding="utf-8", errors="replace").read()
    rows = []
    for group, phrases in PHRASES.items():
        for ph in phrases:
            rx = phrase_regex(ph)
            total, papers, example = 0, 0, ""
            for f, text in docs.items():
                hits = len(rx.findall(text))
                if hits:
                    total += hits
                    papers += 1
                    if not example:
                        base = os.path.splitext(os.path.basename(f))[0]
                        example = base
            rows.append((group, ph, total, papers, example))
    rows.sort(key=lambda r: -r[2])
    out = ["| 短语 | 总频次 | 出现论文数（/74） | 首见论文 |", "|---|---|---|---|"]
    for group, ph, total, papers, ex in rows:
        if total:
            out.append(f"| {ph} | {total} | {papers} | {ex} |")
    md = "\n".join(out)
    with open(P("_知识提炼", "汇总", "语料实证_短语频次.md"), "w", encoding="utf-8") as f:
        f.write("# 金牌论文短语频次（语料实证）\n\n"
                "> 由 `_工具脚本/_mine_phrases.py` 统计自 74 篇金牌论文全文（04_论文文本/），可随时重跑更新。\n\n" + md + "\n")
    print(md[:2400])
    print(f"\ntotal phrases with hits: {sum(1 for r in rows if r[2])}/{len(rows)} | corpus: {len(docs)} papers")


if __name__ == "__main__":
    main()
