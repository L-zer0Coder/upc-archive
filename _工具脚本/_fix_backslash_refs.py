# -*- coding: utf-8 -*-
"""_fix_backslash_refs.py — 反引号内的反斜杠 md 路径（仓库根相对）→ 规范相对链接。
纯字符串扫描；目标以仓库根解析，不存在则保持原样并记录。"""
import os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BS = chr(92)
BT = chr(96)

total = skip = 0
for d in ["07_题目解读", "05_论文赏析", "10_论文精读", "11_论文模板与工具"]:
    for f in glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True):
        base = os.path.dirname(f)
        lines = open(f, encoding="utf-8").read().split("\n")
        changed = False
        for li, line in enumerate(lines):
            if BS not in line or ".md" not in line:
                continue
            out, i = [], 0
            while True:
                a = line.find(BT, i)
                if a < 0:
                    out.append(line[i:])
                    break
                b = line.find(BT, a + 1)
                if b < 0:
                    out.append(line[i:])
                    break
                span = line[a + 1:b]
                if span.endswith(".md") and BS in span and len(span) < 120:
                    rel = span.replace(BS, "/")
                    target = os.path.normpath(os.path.join(ROOT, rel))
                    if os.path.exists(target):
                        out.append(line[i:a])          # 开引号前的文本
                        out.append("[" + rel + "](" + rel + ")")
                        i = b + 1                       # 跳过闭合反引号
                        total += 1
                        changed = True
                        continue
                    skip += 1
                    print("SKIP:", os.path.basename(f), "|", repr(span))
                    out.append(line[i:b + 1])
                    i = b + 1
                    continue
                out.append(line[i:b + 1])
                i = b + 1
            lines[li] = "".join(out)
        if changed:
            open(f, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("converted:", total, "| skipped:", skip)
