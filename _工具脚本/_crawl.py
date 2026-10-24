# -*- coding: utf-8 -*-
"""Crawl uphysicsc.com: year pages, problem texts, gold/silver medal paper PDFs."""
import os, re, html, json, time
import requests

BASE = "http://www.uphysicsc.com"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(ROOT, "01_官网原始页面")
PDF_DIR = os.path.join(ROOT, "03_优秀论文PDF")
YEARS = list(range(2010, 2027))

session = requests.Session()
session.headers.update(UA)

def get(url, binary=False, tries=3):
    last = None
    for i in range(tries):
        try:
            r = session.get(url, timeout=60)
            r.raise_for_status()
            return r.content if binary else r.text
        except Exception as e:
            last = e
            time.sleep(2 + i * 2)
    print(f"  !! FAILED {url}: {last}")
    return None

def clean_text(t):
    t = re.sub(r'(?is)<(script|style).*?</\1>', ' ', t)
    t = re.sub(r'(?is)<br\s*/?>', '\n', t)
    t = re.sub(r'(?is)</(p|div|td|tr|h\d|li)>', '\n', t)
    t = re.sub(r'(?s)<[^>]+>', ' ', t)
    t = html.unescape(t)
    t = t.replace('\xa0', ' ')
    t = re.sub(r'[ \t]+', ' ', t)
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    return '\n'.join(lines)

def fix_url(u):
    u = html.unescape(u.strip().strip('"'))
    if u.lower().startswith('http://https://') or u.lower().startswith('http://http://'):
        u = u[7:]
    if u.startswith('//'):
        u = 'http:' + u
    if u.startswith('/'):
        u = BASE + u
    if not u.lower().startswith('http'):
        u = BASE + '/' + u
    return u

manifest = {}
for y in YEARS:
    page_name = f"{y}contest.html"
    print(f"== {y} ==")
    text = get(f"{BASE}/{page_name}")
    if text is None:
        continue
    os.makedirs(SITE_DIR, exist_ok=True)
    with open(os.path.join(SITE_DIR, page_name), "w", encoding="utf-8") as f:
        f.write(text)

    plain = clean_text(text)
    with open(os.path.join(SITE_DIR, f"{y}_page_text.txt"), "w", encoding="utf-8") as f:
        f.write(plain)

    # extract all pdf links (papers, results, problems)
    links = re.findall(r'<a[^>]*?href\s*=\s*["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.I | re.S)
    pdfs = []
    for href, label in links:
        href2 = fix_url(href)
        label2 = clean_text(label)
        if re.search(r'\.pdf(\?.*)?$', href2, re.I) or re.search(r'\.pdf', label2, re.I):
            pdfs.append((href2, label2))
    manifest[y] = pdfs
    print(f"  page ok, {len(pdfs)} pdf links")

with open(os.path.join(SITE_DIR, "pdf_links.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print("done")
