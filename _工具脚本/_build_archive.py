# -*- coding: utf-8 -*-
"""Build 02_题目汇总/<year>.md from crawled page text. v2: robust parsing."""
import os, re, json

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "01_官网原始页面")
DST = os.path.join(ROOT, "02_题目汇总")
os.makedirs(DST, exist_ok=True)

with open(os.path.join(SRC, "pdf_links.json"), encoding="utf-8") as f:
    manifest = json.load(f)

def nav_strip(text, year):
    m = re.search(rf"The {year} University Physics Competition", text)
    text = text[m.start():] if m else text
    # merge "Team" alone on a line with the following "380: names" line
    lines = text.split("\n")
    merged = []
    i = 0
    while i < len(lines):
        if re.fullmatch(r"Team\s*", lines[i]) and i + 1 < len(lines):
            merged.append("Team " + lines[i + 1].strip())
            i += 2
        else:
            merged.append(lines[i])
            i += 1
    return "\n".join(merged)

def cut(text, start_pat, end_pats):
    m = re.search(start_pat, text)
    if not m:
        return None
    s = m.end()
    e = len(text)
    for p in end_pats:
        m2 = re.search(p, text[s:])
        if m2:
            e = min(e, s + m2.start())
    seg = text[s:e].strip()
    return re.sub(r"\n{2,}", "\n", seg)

TEAM_LINE = re.compile(r"Team\s+(\d+)\s*:?\s*(.*)", re.I)
PAPER_LINE = re.compile(r"Gold Medal Winning Paper|UPC_Results", re.I)

def parse_teams(sec):
    out = []
    if not sec:
        return out
    lines = sec.split("\n")
    i = 0
    while i < len(lines):
        m = TEAM_LINE.match(lines[i])
        if m and not PAPER_LINE.search(lines[i]) and "Results" not in lines[i]:
            team, names = m.group(1), m.group(2).strip()
            i += 1
            inst = sponsor = ""
            names_buf = [names] if names else []
            while i < len(lines) and not (TEAM_LINE.match(lines[i]) and not PAPER_LINE.search(lines[i])):
                line = lines[i]
                mi = re.match(r"Institution\s*:?\s*(.*)", line, re.I)
                ms = re.match(r"Faculty\s+Sponsor\s*:?\s*(.*)", line, re.I)
                ma = re.match(r"Team\s+Advisor\s*:?\s*(.*)", line, re.I)
                if mi:
                    inst = mi.group(1).strip()
                elif ms:
                    sponsor = ms.group(1).strip()
                elif ma:
                    sponsor = ma.group(1).strip()
                elif line.strip() and not PAPER_LINE.search(line) and "medal" not in line.lower():
                    names_buf.append(line.strip())
                i += 1
            out.append({"team": team, "names": " ".join(names_buf),
                        "institution": inst, "sponsor": sponsor})
        else:
            i += 1
    return out

results = {}
for year in range(2010, 2027):
    path = os.path.join(SRC, f"{year}_page_text.txt")
    if not os.path.exists(path):
        continue
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = nav_strip(text, year)

    prob_a = cut(text, r"Problem A\b[\s.:—-]*", [r"Problem B\b", r"Results of the"])
    prob_b = cut(text, r"Problem B\b[\s.:—-]*", [r"Results of the", r"Problem C\b"])

    sec_a = cut(text, r"For\s+Problem\s+A\s*,?\s+the[^\n]*\n",
                [r"For\s+problem\s+B", r"For\s+Problem\s+B", r"We are very pleased",
                 r"We extend our sincerest", r"Above,", r"Kelly S\. Cline"])
    sec_b = cut(text, r"For\s+problem\s+B\s*,?\s+the[^\n]*\n",
                [r"We are very pleased", r"Accomplished Competitors", r"Of the \d+ teams",
                 r"We extend our sincerest", r"Above,", r"Kelly S\. Cline"])

    teams_a = parse_teams(sec_a)
    teams_b = parse_teams(sec_b)

    papers_a, papers_b = [], []
    for href, label in manifest.get(str(year), []):
        m = re.search(r"(\d{4})-GM-([AB])-(\w+)\.pdf", href, re.I)
        if m and int(m.group(1)) == year:
            lst = papers_a if m.group(2).upper() == "A" else papers_b
            if href not in lst:
                lst.append(href)

    stats = ""
    m = re.search(r"(In this year.{0,10}s competition[^.]*\.)", text)
    if m:
        stats = m.group(1)
    else:
        m = re.search(r"([\d,]+\s+teams submitted[^.]*\.)", text)
        if m:
            stats = m.group(1)
    medal_line = re.search(r"(Of\s+(the\s+)?[\d,]+\s+teams?[^.]*Accomplished Competitors\.?)", text, re.S)
    if medal_line:
        stats += "\n\n> " + re.sub(r"\s+", " ", medal_line.group(1))

    results[year] = {"prob_a": prob_a, "prob_b": prob_b,
                     "teams_a": teams_a, "teams_b": teams_b,
                     "papers_a": papers_a, "papers_b": papers_b, "stats": stats}

    md = [f"# {year} 年 University Physics Competition（UPC）题目与官方信息", ""]
    md.append(f"## 赛事概况\n\n{stats or '（官网未给出统计；2026 年比赛尚未举行）'}\n")
    md.append(f"## Problem A\n\n{prob_a or '（官网尚未发布）'}\n")
    if prob_b:
        md.append(f"## Problem B\n\n{prob_b}\n")
    for tag, teams, papers in (("A", teams_a, papers_a), ("B", teams_b, papers_b)):
        if teams:
            md.append(f"## Problem {tag} 金牌队伍\n")
            md.append("| 队伍 | 成员 | 学校 | 指导教师 |")
            md.append("|---|---|---|---|")
            for t in teams:
                md.append(f"| {t['team']} | {t['names']} | {t['institution']} | {t['sponsor']} |")
            md.append("")
        if papers:
            md.append(f"## Problem {tag} 官方公开论文（已下载至 03_优秀论文PDF/{year}/）\n")
            for u in papers:
                md.append(f"- {u}")
            md.append("")

    with open(os.path.join(DST, f"{year}_题目与官方信息.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

with open(os.path.join(DST, "_parsed.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

for y, r in results.items():
    print(y, "A:", bool(r["prob_a"]), "B:", bool(r["prob_b"]),
          f"teams A/B: {len(r['teams_a'])}/{len(r['teams_b'])}",
          f"papers A/B: {len(r['papers_a'])}/{len(r['papers_b'])}")
