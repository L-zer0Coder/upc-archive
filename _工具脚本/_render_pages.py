# -*- coding: utf-8 -*-
"""Render title page + densest-figure page of each paper to PNG for typography analysis."""
import os, re, json
import pymupdf

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "03_优秀论文PDF")
DST = os.path.join(ROOT, "06_论文页面图")

info = []
for dirpath, _, files in os.walk(SRC):
    for fn in sorted(files):
        if not fn.lower().endswith(".pdf"):
            continue
        src = os.path.join(dirpath, fn)
        rel = os.path.relpath(src, SRC)
        year = rel.split(os.sep)[0]
        base = os.path.splitext(fn)[0]
        out_dir = os.path.join(DST, year)
        os.makedirs(out_dir, exist_ok=True)
        try:
            doc = pymupdf.open(src)
            n = len(doc)
            # count images per page
            counts = [len(p.get_images(full=True)) for p in doc]
            p1 = 0
            pbest = max(range(n), key=lambda i: counts[i]) if any(counts) else min(2, n - 1)
            if pbest == p1 and n > 2:
                pbest = 2
            targets = {p1: "p1", pbest: "fig"}
            for pi, tag in targets.items():
                pix = doc[pi].get_pixmap(dpi=110)
                out = os.path.join(out_dir, f"{base}_{tag}.png")
                pix.save(out)
            doc.close()
            info.append({"year": year, "file": fn, "pages": n,
                         "img_per_page": counts, "title_png": f"06_论文页面图/{year}/{base}_p1.png",
                         "fig_png": f"06_论文页面图/{year}/{base}_fig.png"})
            print(f"{rel}: rendered p1 + p{pbest} (imgs {counts[:8]}{'...' if n>8 else ''})")
        except Exception as e:
            print("ERR", fn, e)

with open(os.path.join(DST, "_pages.json"), "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=1)
print(f"\n{len(info)} papers rendered")
