# -*- coding: utf-8 -*-
"""
_extract_structure.py — 论文透视数据提取（关键词锚点 + 序号连续编号标题 混合版）
1) 结构图谱：命名锚点（Abstract/Introduction/…）+ 序号连续的编号标题共同切分，
   统计各段字符体量占比（无分页符，体量占比≈页配比的近似，页面如实标注）
2) 摘要解剖：抽取 Abstract 段，规则逐句标注功能（定义/两难/方法/数字结论/数字/建议/叙述）
输出 _知识提炼/汇总/结构图谱.json、摘要解剖.json。
"""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
OUT = P("_知识提炼", "汇总")

# 命名锚点：桶名 → 标题行关键词
ANCHORS = [
    ("abstract", r"abstract\b"),
    ("intro", r"introduc|background|problem (statement|description)|motivation"),
    ("model", r"mathematical model|model (construction|development|formulation)|^model\b|formulation|equations? of motion|governing equations?|physical (model|analysis)|theoretical (model|analysis)|force (model|analysis)|assumptions?\b|aerodynamic (model|forces?)|energy (model|balance|analysis)"),
    ("numerics", r"numerical (method|model|approach|solution|simulation|analysis|integration)|simulation|computational (method|model)|euler('s)? method|runge.?kutta|matlab|solution method|method of solution|implementation"),
    ("results", r"results?|sensitivity|validation|verification|error (analysis|estimation)|margin of error|bounds|discussion"),
    ("conclusion", r"conclusions?\b|summary and|final remarks?|recommendations?\b"),
    ("references", r"references\b|bibliography\b"),
    ("appendix", r"appendix|nomenclature|code listing|source code"),
]
NAMES = {"front": "标题页", "abstract": "摘要", "intro": "引言", "model": "建模",
         "numerics": "数值", "results": "结果与验证", "conclusion": "结论",
         "references": "参考文献", "appendix": "附录", "other": "其他"}

HEADLINE = r"^[ \t]*(?:(?:\d{1,2}(?:\.\d+){0,2})[.。\t ]*)?(?:%s)[^.!?]*$"

# 编号标题黑名单：拦公式编号后的句子开头
BLACKLIST = ("that is", "this means", "note that", "hence", "thus", "therefore",
             "we ", "it ", "in ", "for ", "as ", "so ", "if ", "the ", "a ", "an ",
             "of ", "on ", "to ", "at ", "by ", "which", "where ", "since",
             "figure", "table", "such")
KNOWN_SINGLE = {"results", "references", "conclusions", "conclusion", "discussion",
                "model", "introduction", "abstract", "appendix", "nomenclature",
                "simulation", "analysis", "method", "methods", "summary", "validation"}


def numbered_candidates(text):
    """编号标题候选：数字(可含子号) + 换行或空格 + 标题词串"""
    rx = re.compile(r"^[ \t]*(\d{1,2}(?:\.\d{1,2})?)[.。]?(?:[ \t]*\n[ \t]*|[ \t]+)([A-Z][^\n]{3,70})$", re.M)
    out = []
    for m in rx.finditer(text):
        title = m.group(2).strip()
        low = title.lower()
        if any(low.startswith(b) for b in BLACKLIST):
            continue
        if ";" in title or title.endswith(","):
            continue
        if len(title.split()) < 2 and low not in KNOWN_SINGLE:
            continue
        out.append((m.start(), m.group(1), title))
    return out


def bucket_of(title):
    t = title.lower()
    for bucket, kw in ANCHORS:
        if re.search(kw, t, re.I):
            return bucket
    return "other"


def anchor_positions(text):
    """合并：命名锚点 + 序号连续的编号标题（编号标题的桶由标题关键词判定）"""
    pts = []
    for bucket, kw in ANCHORS:
        rx = re.compile(HEADLINE % kw, re.I | re.M)
        for m in rx.finditer(text):
            if len(m.group(0).strip()) < 90:
                pts.append((m.start(), bucket))
    last_top, last_sub = 0, 0
    for pos, num, title in numbered_candidates(text):
        if "." in num:
            top, sub = (int(x) for x in num.split("."))
            if top == last_top and sub == last_sub + 1:
                last_sub = sub
            elif top == last_top + 1:
                last_top, last_sub = top, sub
            else:
                continue
        else:
            top = int(num)
            if top == last_top + 1:
                last_top, last_sub = top, 0
            else:
                continue
        pts.append((pos, "num:" + title))
    pts.sort()
    merged = []
    for pos, b in pts:
        if merged and merged[-1][1] == b:
            continue
        merged.append((pos, b))
    return merged


def alloc_of(text, pts):
    alloc = {}
    for i, (a, b) in enumerate(pts):
        end = pts[i + 1][0] if i + 1 < len(pts) else len(text)
        b2 = bucket_of(b[4:]) if b.startswith("num:") else b
        alloc[b2] = alloc.get(b2, 0) + (end - a)
    tot = sum(alloc.values()) or 1
    return {k: round(v * 100.0 / tot, 1) for k, v in alloc.items()}


SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"A-Z0-9(])")
RULES = [
    ("num结论", re.compile(r"\d", re.I), re.compile(r"conclu|therefore|thus|hence|result|yield|find|margin|window|allow", re.I)),
    ("定义", re.compile(r"\b(define[sd]?|denote[sd]?|set)\b|defined as|call(ed)? (this|it)", re.I), None),
    ("两难", re.compile(r"on the other hand|trade.?off|whereas|too (large|small|weak|strong|high|low)|if .{3,60}(then|,)", re.I), None),
    ("方法", re.compile(r"\bwe (use|used|apply|applied|model|modeled|modeling|simulat(e|ed)|simulating|integrat(e|ed)|solv(e|ed)|deriv(e|ed)|develop(ed)?|employ(ed)?|construct(ed)?|present)\b|numerically|euler|runge", re.I), None),
    ("建议", re.compile(r"\b(recommend|advise|suggest)", re.I), None),
]


def classify(sent):
    for name, need, and_rx in RULES:
        if and_rx is not None:
            if need.search(sent) and and_rx.search(sent):
                return name
            continue
        if need.search(sent):
            return name
    if re.search(r"\d", sent):
        return "数字"
    return "叙述"


def main():
    with open(P("04_论文文本", "_meta.json"), encoding="utf-8") as f:
        papers = json.load(f)
    struct, abstracts = [], []
    for p in papers:
        base = os.path.splitext(p["file"])[0]
        if base == "2013-GM-B-611":
            base = "2013-GM-B-611a"
        fp = P("04_论文文本", str(p["year"]), base + ".txt")
        if not os.path.exists(fp):
            continue
        text = open(fp, encoding="utf-8", errors="replace").read()
        pts = anchor_positions(text)
        alloc = alloc_of(text, pts)
        struct.append({"id": base, "year": int(p["year"]), "problem": p["problem"],
                       "team": p["team"], "pages": p["pages"],
                       "n_sections": len(pts), "alloc": alloc})
        # 摘要：Abstract 行 → 首个「编号标题/keywords/nomenclature」前瞻（独立于锚点系统）
        am = re.search(r"^\s*abstract\b[^\n]*$((?:.|\n)*?)(?=^\s*(?:\d{1,2}[.。\t ]+[A-Z]|\d{1,2}\s*$|keywords|nomenclature|acknowledg)|\Z)",
                       text, re.I | re.M)
        if am and len(am.group(1)) > 120:
            body = re.sub(r"\s+", " ", am.group(1)).strip()
            sents = [x.strip() for x in SENT_SPLIT.split(body) if len(x.strip()) > 15]
            abstracts.append({"id": base, "year": int(p["year"]), "problem": p["problem"],
                              "team": p["team"], "n": len(sents),
                              "sents": [{"t": x[:260], "f": classify(x)} for x in sents]})
    struct.sort(key=lambda x: (x["year"], x["problem"], x["team"]))
    abstracts.sort(key=lambda x: (x["year"], x["problem"], x["team"]))
    with open(os.path.join(OUT, "结构图谱.json"), "w", encoding="utf-8") as f:
        json.dump({"papers": struct, "names": NAMES}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "摘要解剖.json"), "w", encoding="utf-8") as f:
        json.dump({"papers": abstracts, "names": NAMES}, f, ensure_ascii=False, indent=1)
    print(f"struct: {len(struct)} | abstracts: {len(abstracts)} "
          f"({sum(a['n'] for a in abstracts)} sentences)")


if __name__ == "__main__":
    main()
