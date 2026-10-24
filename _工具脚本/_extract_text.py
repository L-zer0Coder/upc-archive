# -*- coding: utf-8 -*-
"""Extract text + metadata from every award paper PDF into 04_论文文本/."""
import os, re, json
import pymupdf

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "03_优秀论文PDF")
DST = os.path.join(ROOT, "04_论文文本")

meta = []
for dirpath, _, files in os.walk(SRC):
    for fn in sorted(files):
        if not fn.lower().endswith(".pdf"):
            continue
        src = os.path.join(dirpath, fn)
        rel = os.path.relpath(src, SRC)
        year = rel.split(os.sep)[0]
        try:
            doc = pymupdf.open(src)
            n_pages = len(doc)
            parts = []
            for p in doc:
                parts.append(p.get_text("text"))
            doc.close()
            full = "\n".join(parts)
        except Exception as e:
            print("ERR", fn, e)
            continue
        out_dir = os.path.join(DST, year)
        os.makedirs(out_dir, exist_ok=True)
        txt_path = os.path.join(out_dir, fn.replace(".pdf", ".txt").replace(".PDF", ".txt"))
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full)
        m = re.match(r"(\d{4})-GM-([AB])-(\w+)", fn, re.I)
        # paper title: usually on first page after byline; grab first non-empty line heuristics
        first = [l.strip() for l in full.split("\n") if l.strip()][:8]
        meta.append({"year": year, "file": fn, "problem": m.group(2).upper() if m else "?",
                     "team": m.group(3) if m else "?", "pages": n_pages,
                     "chars": len(full), "first_lines": first[:6]})
        print(f"{rel}: {n_pages}p {len(full)//1000}k chars | {' / '.join(first[:3])[:110]}")

with open(os.path.join(DST, "_meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
print(f"\n{len(meta)} papers extracted")
