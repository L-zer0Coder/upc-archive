# -*- coding: utf-8 -*-
"""
_aggregate_cards.py — 模式卡片提炼管线最后一步：聚合成技能原料
把 _知识提炼/卡片/*.json 按物理域与主题聚合为四个知识库文件（upc-coach 技能的 references）：

  _知识提炼/汇总/模型与套路.md     modeling 技能原料：分域模型清单 + 获奖密码频次 + 陷阱清单
  _知识提炼/汇总/写作动作.md       writing 技能原料：写作动作频次 + 金句范例索引
  _知识提炼/汇总/图表做法.md       figures 技能原料：图表类型频次与画法要点
  _知识提炼/汇总/复用与审查.md     review 技能原料：可复用套路 + 终检补充项
"""
import os, re, json, glob
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
CARD_DIR = P("_知识提炼", "卡片")
OUT_DIR = P("_知识提炼", "汇总")


def load_cards():
    cards = []
    for f in sorted(glob.glob(os.path.join(CARD_DIR, "*.json"))):
        try:
            cards.append(json.load(open(f, encoding="utf-8")))
        except Exception as e:
            print("BAD JSON:", os.path.basename(f), e)
    return cards


def bullets(items, limit=None, prefix="- "):
    out = []
    for x in (items or [])[:limit]:
        x = re.sub(r"\s+", " ", str(x)).strip()
        if x:
            out.append(f"{prefix}{x}")
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cards = load_cards()
    n = len(cards)
    if not n:
        raise SystemExit("no cards found")

    # ---------- 分域索引 ----------
    by_domain = defaultdict(list)
    for c in cards:
        for d in c.get("domains", []) or ["未分类"]:
            by_domain[d].append(c)

    # ---------- 频次统计 ----------
    secret_counter = Counter()
    pitfall_counter = Counter()
    writing_counter = Counter()
    figure_counter = Counter()
    numeric_counter = Counter()
    for c in cards:
        for s in c.get("gold_secret", []):
            secret_counter[re.sub(r"\s+", " ", s).strip()] += 1
        for s in c.get("pitfalls", []):
            pitfall_counter[re.sub(r"\s+", " ", s).strip()] += 1
        for s in c.get("writing_moves", []):
            writing_counter[re.sub(r"\s+", " ", s).strip()] += 1
        for f in c.get("figures", []):
            if isinstance(f, dict) and f.get("type"):
                figure_counter[re.sub(r"\s+", " ", f["type"]).strip()] += 1
        for s in c.get("numerics", []):
            numeric_counter[re.sub(r"\s+", " ", s).strip()] += 1

    def top(counter, k=14):
        return [(t, n) for t, n in counter.most_common(k)]

    # ---------- 1) 模型与套路 ----------
    L = ["# 模型与套路知识库（聚合自 73 张模式卡片）", "",
         f"> 来源：`_知识提炼/卡片/` 共 {n} 张卡片；每条后面括号是论文编号。此文件由 `_aggregate_cards.py` 生成。", ""]
    L.append("## 一、获奖密码总览（按跨论文出现频次排序，Top 18）\n")
    L.append("> 各卡片措辞独立，频次按精确文本匹配统计，只作参考；语义聚类靠人读。≥3 次的几乎肯定是跨队伍的共性。\n")
    for t, k in top(secret_counter, 18):
        L.append(f"- {'**' if k >= 3 else ''}{t}{'**' if k >= 3 else ''}（{k} 篇）")
    L.append("\n## 二、陷阱总览（按出现频次排序，Top 15）\n")
    for t, k in top(pitfall_counter, 15):
        L.append(f"- {t}（{k} 篇）")
    L.append("\n## 三、分域模型清单\n")
    for dom in sorted(by_domain):
        cs = by_domain[dom]
        L.append(f"### {dom}（{len(cs)} 篇）\n")
        for c in sorted(cs, key=lambda x: (x["year"], x["problem"], str(x["team"]))):
            pid = f"{c['year']}-{c['problem']}-{c['team']}"
            L.append(f"#### {pid} {c.get('title_zh','')}\n")
            L.append(f"**核心思路**：{c.get('core_idea','')}\n")
            for m in c.get("models", []) or []:
                name = m.get("name", "")
                eq = m.get("key_eq", "")
                why = m.get("why", "")
                asm = "；".join(m.get("assumptions", []) or [])
                line = f"- **{name}**"
                if eq:
                    line += f"：{eq}"
                if why:
                    line += f"（{why}）"
                L.append(line)
                if asm:
                    L.append(f"  - 假设：{asm}")
            if c.get("numerics"):
                L.append("- 数值：" + "；".join(c["numerics"]))
            L.append("")
    with open(os.path.join(OUT_DIR, "模型与套路.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # ---------- 2) 写作动作 ----------
    L = ["# 写作动作知识库（聚合自 73 张模式卡片）", "",
         f"> 写作动作 = 金牌论文里可直接模仿的表述行为。按出现频次排序；编号索引到论文。", "",
         "## 一、高频写作动作（按跨论文出现频次排序，Top 25）\n"]
    for t, k in top(writing_counter, 25):
        L.append(f"- {t}（{k} 篇）")
    L.append("\n## 二、全部写作动作（按论文）\n")
    for c in sorted(cards, key=lambda x: (x["year"], x["problem"], str(x["team"]))):
        mv = c.get("writing_moves", [])
        if not mv:
            continue
        L.append(f"- **{c['year']}-{c['problem']}-{c['team']}**（{c.get('title_zh','')}）："
                 + "；".join(re.sub(r"\s+", " ", m) for m in mv))
    L.append("\n## 三、反面清单（落选论文高发，来自句库）\n")
    L.append("- 自夸词（accurate/great）→ 改精度声明")
    L.append("- “Obviously/It can easily be shown” → 补一步推导或引用式号")
    L.append("- 摘要无数字 → 必须给区间/阈值/百分比")
    L.append("- 图无编号引用 → 每图 “Figure N” 且被正文点名")
    with open(os.path.join(OUT_DIR, "写作动作.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # ---------- 3) 图表做法 ----------
    L = ["# 图表做法知识库（聚合自 73 张模式卡片）", "", "## 一、高频图型（按出现频次排序，Top 20）\n"]
    for t, k in top(figure_counter, 20):
        L.append(f"- **{t}**（{k} 篇）")
    L.append("\n## 二、图型与画法要点（全部）\n")
    for c in sorted(cards, key=lambda x: (x["year"], x["problem"], str(x["team"]))):
        fs = c.get("figures", []) or []
        if not fs:
            continue
        pid = f"{c['year']}-{c['problem']}-{c['team']}"
        L.append(f"### {pid} {c.get('title_zh','')}\n")
        for f_ in fs:
            if isinstance(f_, dict):
                t = f_.get("type", "")
                note = f_.get("note", "")
                if t:
                    L.append(f"- **{t}**{'：' + note if note else ''}")
        L.append("")
    with open(os.path.join(OUT_DIR, "图表做法.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # ---------- 4) 复用与审查 ----------
    L = ["# 复用套路与审查补充（聚合自 73 张模式卡片）", "",
         "## 一、可复用套路（按论文，供审查时对照“这步做了吗”）\n"]
    for c in sorted(cards, key=lambda x: (x["year"], x["problem"], str(x["team"]))):
        ru = c.get("reusable", [])
        if not ru:
            continue
        L.append(f"- **{c['year']}-{c['problem']}-{c['team']}**："
                 + "；".join(re.sub(r"\s+", " ", m) for m in ru))
    L.append("\n## 二、数值方法使用频次（数值审查时的对照面）\n")
    for t, k in top(numeric_counter, 16):
        L.append(f"- {t}（{k} 篇）")
    L.append("\n## 三、审查优先级（从获奖密码频次反推）\n")
    L.append("1. 判据是否全部操作化且有自辩（出现频率最高的密码族）")
    L.append("2. 是否有解析基准并回扣（基准先于模型）")
    L.append("3. 验证三件套是否完整（收敛/极限/灵敏度）")
    L.append("4. 量级表是否逐项封存了“可忽略”项")
    L.append("5. 负结论/适用域是否诚实给出")
    with open(os.path.join(OUT_DIR, "复用与审查.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"cards: {n} | domains: { {d: len(v) for d, v in sorted(by_domain.items())} }")
    for fn in ["模型与套路.md", "写作动作.md", "图表做法.md", "复用与审查.md"]:
        p = os.path.join(OUT_DIR, fn)
        print(f"  {fn}: {os.path.getsize(p)//1024} KB")


if __name__ == "__main__":
    main()
