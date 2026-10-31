# -*- coding: utf-8 -*-
"""
_extract_knowledge.py — 模式卡片提炼管线第一步：章节抽取
从 73 篇赏析中抽「论文速览 / 获奖密码 / 可借鉴清单」，从 73 篇精读中抽
「一分钟看懂全文骨架 / 建模决策链 / 可复用模板」，按论文合并为一份精简
原料摘要（_知识提炼/原料/<base>.md），供后续 LLM 提炼模式卡片使用。
"""
import os, re, json, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
OUT = P("_知识提炼", "原料")

# 赏析/精读中值得进卡片的章节（按关键词模糊匹配标题，兼容各年份编号差异）
ANA_KEYS = [("速览", "论文速览"), ("获奖密码", "获奖密码"), ("可借鉴", "可借鉴清单")]
JD_KEYS = [("一分钟看懂", "全文骨架"), ("决策链", "建模决策链"), ("可复用", "可复用模板")]

HEAD_RE = re.compile(r"^(#{2,3})\s+(.+)$", re.M)


def split_sections(text):
    """返回 [(标题, 级别, 内容)]，内容不含标题行"""
    marks = [(m.start(), m.end(), len(m.group(1)), m.group(2).strip())
             for m in HEAD_RE.finditer(text)]
    out = []
    for i, (s, e, lvl, title) in enumerate(marks):
        nxt = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        # 只取本级或更高级标题之前的内容（即本节的完整内容）
        j = i + 1
        while j < len(marks) and marks[j][2] > lvl:
            j += 1
        end = marks[j][0] if j < len(marks) else len(text)
        out.append((title, lvl, text[e:end].strip()))
    return out


def grab(text, keys):
    outs = []
    for kw, label in keys:
        for title, lvl, body in split_sections(text):
            if kw in title and body:
                outs.append(f"### {label}\n\n{body}\n")
                break
    return "\n".join(outs)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(P("04_论文文本", "_meta.json"), encoding="utf-8") as f:
        papers = json.load(f)
    cards = []
    for p in papers:
        base = os.path.splitext(p["file"])[0]
        if base == "2013-GM-B-611":  # 同文异版 → 以 611a 为准
            base = "2013-GM-B-611a"
        yr = p["year"]
        ana = P("05_论文赏析", str(yr), base + ".md")
        jd = P("10_论文精读", str(yr), base + "_精读.md")
        parts = [f"# {base}（{yr} 题{p['problem']} · 队伍 {p['team']} · {p['pages']} 页）\n"]
        if os.path.exists(ana):
            parts.append("## 来自赏析\n\n" + grab(open(ana, encoding="utf-8").read(), ANA_KEYS))
        else:
            parts.append("## 来自赏析\n\n（缺失）\n")
        if os.path.exists(jd):
            parts.append("## 来自精读\n\n" + grab(open(jd, encoding="utf-8").read(), JD_KEYS))
        else:
            parts.append("## 来自精读\n\n（缺失）\n")
        digest = "\n".join(parts)
        # 压掉三个以上连续空行，控制体积
        digest = re.sub(r"\n{3,}", "\n\n", digest)
        with open(os.path.join(OUT, base + ".md"), "w", encoding="utf-8") as f:
            f.write(digest)
        cards.append({"base": base, "year": yr, "problem": p["problem"],
                      "team": p["team"], "pages": p["pages"],
                      "digest_kb": round(len(digest.encode("utf-8")) / 1024, 1),
                      "has_ana": os.path.exists(ana), "has_jd": os.path.exists(jd)})
    cards.sort(key=lambda c: (c["year"], c["problem"], c["team"]))
    with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(cards, f, ensure_ascii=False, indent=1)
    total_kb = sum(c["digest_kb"] for c in cards)
    print(f"digests: {len(cards)} | total {total_kb:.0f} KB | "
          f"avg {total_kb/len(cards):.1f} KB | "
          f"missing ana={sum(1 for c in cards if not c['has_ana'])} jd={sum(1 for c in cards if not c['has_jd'])}")


if __name__ == "__main__":
    main()
