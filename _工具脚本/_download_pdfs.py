# -*- coding: utf-8 -*-
"""Download all PDFs (award papers + results) into organized folders."""
import os, re, json, time
import requests

BASE = "http://www.uphysicsc.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
ROOT = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(ROOT, "01_官网原始页面", "pdf_links.json"), encoding="utf-8") as f:
    manifest = json.load(f)

session = requests.Session()
session.headers.update(UA)

PAPER_DIR = os.path.join(ROOT, "03_优秀论文PDF")
RESULTS_DIR = os.path.join(ROOT, "02_官方成绩单")

seen = set()
downloaded, failed = [], []
for year, links in sorted(manifest.items(), key=lambda kv: int(kv[0])):
    for href, label in links:
        if href in seen:
            continue
        seen.add(href)
        fname = href.split("/")[-1].split("?")[0]
        if not fname.lower().endswith(".pdf"):
            continue
        # classify
        m = re.match(r"(\d{4})-GM-([A-Za-z])-(\w+)", fname, re.I)
        if m:
            sub = os.path.join(PAPER_DIR, m.group(1), f"Problem {m.group(2).upper()}")
        elif "Results" in fname or "results" in fname:
            yy = re.match(r"(\d{4})", fname).group(1)
            sub = os.path.join(RESULTS_DIR, yy)
        else:
            sub = os.path.join(PAPER_DIR, year, "其他")
        dest = os.path.join(sub, fname)
        os.makedirs(sub, exist_ok=True)
        if os.path.exists(dest) and os.path.getsize(dest) > 10000:
            downloaded.append(dest)
            continue
        ok = False
        for i in range(3):
            try:
                r = session.get(href, timeout=90)
                r.raise_for_status()
                ct = r.headers.get("content-type", "")
                if len(r.content) < 5000 or ("html" in ct.lower() and b"%PDF" not in r.content[:1024]):
                    raise RuntimeError(f"not a pdf ({ct}, {len(r.content)} bytes)")
                with open(dest, "wb") as f:
                    f.write(r.content)
                downloaded.append(dest)
                ok = True
                break
            except Exception as e:
                last = e
                time.sleep(2 + i * 2)
        if ok:
            print(f"OK  {year}: {fname} ({len(r.content)//1024} KB)")
        else:
            failed.append((href, str(last)))
            print(f"FAIL {year}: {href} -> {last}")

print(f"\nDownloaded {len(downloaded)}, failed {len(failed)}")
with open(os.path.join(ROOT, "01_官网原始页面", "download_failures.json"), "w", encoding="utf-8") as f:
    json.dump(failed, f, ensure_ascii=False, indent=2)
