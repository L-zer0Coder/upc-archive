# -*- coding: utf-8 -*-
"""
_build_site.py — 全站构建器
1) 将 144 个 Markdown 文档渲染为 09_可视化总览/docs/*.html（KaTeX 公式 + mermaid 图表，构建期完成 markdown→HTML）
2) 重新生成 09_可视化总览/index.html（全新 UI + 全库文件导航 + 全文搜索）
3) 生成部署辅助文件：根目录 index.html 跳转页、.nojekyll、.gitignore
4) 构建期全量校验所有相对链接
"""
import os, re, json, glob, shutil, html
import markdown
from urllib.parse import quote, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "09_可视化总览")
DOCS = os.path.join(SITE, "docs")
P = lambda *a: os.path.join(ROOT, *a)

DOC_DIRS = ["05_论文赏析", "07_题目解读", "08_物理模型综述", "02_题目汇总"]
DIR_LABEL = {
    "05_论文赏析": "论文赏析", "07_题目解读": "题目深度解读", "08_物理模型综述": "物理模型综述",
    "02_题目汇总": "题目与官方信息", "README.md": "档案库说明",
}
GM_RE = re.compile(r"(\d{4})-GM-([AB])-(\w+)", re.I)

def posix(p):
    return p.replace("\\", "/")

def rel_root(path_abs):
    return posix(os.path.relpath(path_abs, ROOT))

def site_rel(path_abs):
    """URL for a target as seen from index.html (which lives in SITE dir)."""
    return quote(posix(os.path.relpath(path_abs, SITE)))

# ---------------- collect docs ----------------
doc_mds = [P("README.md")]
for d in DOC_DIRS:
    doc_mds += sorted(glob.glob(P(d, "**", "*.md"), recursive=True))
doc_mds = [m for m in doc_mds if not os.path.basename(m).startswith("_parsed")]

def doc_title(md_path):
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"#\s+(.+)", line)
            if m:
                return m.group(1).strip()
    return os.path.splitext(os.path.basename(md_path))[0]

def doc_html_abs(md_abs):
    """output path for a md file: SITE/docs/<rel>.html"""
    rel = rel_root(md_abs)[:-3] + ".html"
    return os.path.join(DOCS, *rel.split("/"))

def link_from(page_dir_abs, target_abs):
    href = posix(os.path.relpath(target_abs, page_dir_abs))
    return quote(href)

# ---------------- render doc pages ----------------
from markdown.extensions.toc import slugify_unicode   # keep CJK in heading ids (#中文锚点)
MD = markdown.Markdown(extensions=["tables", "fenced_code", "toc", "sane_lists"],
                       output_format="html5",
                       extension_configs={"toc": {"slugify": slugify_unicode}})

DOC_TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ · UPC 全档案库</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='18' fill='%236E7BF2'/%3E%3Ctext x='50' y='68' font-size='56' font-weight='600' text-anchor='middle' fill='white' font-family='Arial'%3EU%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<style>
:root{--bg0:#0A0D12;--bg1:#0D1117;--bg2:#11151D;--bg3:#161B24;--ink:#F0F3F7;--mut:#A9B2C0;--dim:#6B7482;
 --line:rgba(255,255,255,.05);--line2:rgba(255,255,255,.16);--acc:#6E7BF2;--accS:#6E7BF2;--cyan:#6E7BF2;--r:10px;
 --pri:#6E7BF2;--pri-sub:rgba(110,123,242,.14);
 --mono:"JetBrains Mono","Cascadia Code",ui-monospace,Consolas,monospace}
html{scrollbar-color:rgba(255,255,255,.16) transparent}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:74px}
body{margin:0;background:radial-gradient(1000px 460px at 80% -10%,rgba(99,102,241,.12),transparent 60%),var(--bg0);
 color:var(--ink);font-family:"Inter","Segoe UI","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
 line-height:1.9;font-size:15.5px}
#pbar{position:fixed;top:0;left:0;height:2px;width:0;z-index:60;background:var(--pri);transition:width .1s}
.topbar{position:sticky;top:0;z-index:9;backdrop-filter:blur(12px);background:rgba(7,10,18,.82);border-bottom:1px solid var(--line)}
.topbar .in{max-width:1240px;margin:0 auto;display:flex;align-items:center;gap:10px;padding:9px 18px;flex-wrap:wrap}
.topbar a{color:var(--mut);text-decoration:none;font-size:12.5px;border:1px solid var(--line);border-radius:8px;
 padding:3px 12px;transition:.15s;white-space:nowrap}
.topbar a:hover{border-color:var(--line2);color:var(--ink)}
.crumb{color:var(--dim);font-size:12px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}
.layout{display:flex;justify-content:center;gap:40px;max-width:1160px;margin:0 auto;padding:32px 24px 96px;align-items:flex-start}
.content{flex:0 1 760px;min-width:0}
.card{background:var(--bg2);border:1px solid var(--line);border-radius:14px;padding:40px 48px;box-shadow:0 24px 60px rgba(0,0,0,.22)}
h1{font-size:26px;line-height:1.4;margin:.2em 0 .6em;font-weight:600;letter-spacing:0;color:#F0F3F7;text-wrap:balance}
h2{font-size:20px;padding-left:12px;margin-top:1.9em;scroll-margin-top:60px;font-weight:600;letter-spacing:0;position:relative}
h2::before{content:"";position:absolute;left:0;top:.3em;bottom:.3em;width:3px;border-radius:2px;background:var(--pri)}
h3{font-size:16px;color:#cdd8ec;scroll-margin-top:60px;font-weight:500}
a{color:var(--acc)} a:hover{text-decoration:underline}
code{background:var(--bg3);border:1px solid var(--line);border-radius:6px;padding:1px 6px;font-size:.88em;
 font-family:var(--mono)}
pre{background:var(--bg1);border:1px solid var(--line);border-radius:10px;padding:14px 16px;overflow:auto}
pre code{border:none;background:none;padding:0}
blockquote{margin:1.2em 0;padding:4px 0 4px 16px;border-left:2px solid var(--line2);background:none;color:var(--mut);border-radius:0}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:13.5px;display:block;overflow-x:auto}
th,td{border:1px solid transparent;border-bottom:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
th{background:none;color:var(--dim);white-space:nowrap;font-size:11px;letter-spacing:.04em;border-bottom:1px solid var(--line2)}
td:first-child,th:first-child{white-space:nowrap}
tbody tr:nth-child(2n) td{background:rgba(255,255,255,.015)}
hr{border:none;border-top:1px solid var(--line);margin:2em 0}
img{max-width:100%}
.mermaid{background:var(--bg1);border:1px solid var(--line);border-radius:10px;padding:10px;margin:1em 0;display:flex;justify-content:center}
.mermaid svg{max-width:100%;height:auto}
.katex-display{overflow-x:auto;padding:6px 0}.katex{font-size:1.02em}
footer{text-align:center;color:var(--dim);font-size:12px;padding:26px}
#top{position:fixed;right:26px;bottom:26px;z-index:30;background:var(--bg3);border:1px solid var(--line2);color:var(--ink);
 border:none;border-radius:12px;width:42px;height:42px;font-size:17px;cursor:pointer;opacity:0;pointer-events:none;transition:.25s}
#top.on{opacity:1;pointer-events:auto}
#top:hover{background:var(--accS)}
aside.toc{position:sticky;top:60px;width:220px;flex-shrink:0;max-height:calc(100vh - 84px);overflow-y:auto;
 background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:16px 8px 16px 0;font-size:13px}
aside.toc .tt{font-weight:600;font-size:11px;color:var(--dim);letter-spacing:.1em;padding:0 16px 10px}
aside.toc ul{list-style:none;margin:0;padding:0}
aside.toc li a{display:block;line-height:30px;color:var(--dim);text-decoration:none;border-left:2px solid transparent;
 padding:0 14px;white-space:normal;transition:.15s;font-size:12.5px}
aside.toc li.l3 a{padding-left:28px;font-size:12px}
aside.toc li a:hover{color:var(--ink)}
aside.toc li a.on{color:var(--t1,var(--ink));border-left-color:var(--pri);background:none;font-weight:500}
aside.toc::-webkit-scrollbar{width:5px}aside.toc::-webkit-scrollbar-thumb{background:#232d44;border-radius:4px}
@media(max-width:1100px){aside.toc{display:none}.card{padding:22px 18px}}
</style>
</head>
<body>
<div id="pbar"></div>
<div class="topbar"><div class="in">
  <a href="__HOME__" style="font-weight:500">← 总览首页</a>
  __PAPERTAG__
  <a href="__RAWMD__">Markdown</a>
  <span class="crumb" style="flex:1">__CRUMB__ · __TITLE__</span>
</div></div>
<div class="layout">
  <div class="content"><div class="card">
__BODY__
</div></div>
__TOC__
</div>
<footer>UPC 2010–2025 全档案库 · 内容仅供学习交流 · 论文版权归原队伍与 UPC 官方（uphysicsc.com）</footer>
<button id="top" aria-label="回到顶部">↑</button>
<script>
document.addEventListener("DOMContentLoaded", function(){
  if (window.renderMathInElement) renderMathInElement(document.querySelector(".card"), {
    delimiters:[{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}],
    ignoredTags:["script","style","textarea","pre","code"]});
  if (window.mermaid){
    mermaid.initialize({startOnLoad:false,theme:"dark",securityLevel:"loose"});
    document.querySelectorAll('pre code.language-mermaid').forEach(function(el){
      var d=document.createElement('div');d.className='mermaid';d.textContent=el.textContent;
      el.parentElement.replaceWith(d);});
    mermaid.run({querySelector:'.mermaid'});
  }
  // back-to-top (window.scrollTo explicitly — inline scrollTo gets shadowed)
  document.getElementById('top').addEventListener('click',function(){
    try{window.scrollTo({top:0,behavior:'smooth'});}catch(e){window.scrollTo(0,0);}
    setTimeout(function(){document.documentElement.scrollTop=0;},450);
  });
  // reading progress
  var pb=document.getElementById('pbar');
  addEventListener('scroll',function(){
    var h=document.documentElement;
    pb.style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100||0)+'%';
    document.getElementById('top').classList.toggle('on',scrollY>600);
  },{passive:true});
  // toc scroll-spy + click-highlight
  var links=[].slice.call(document.querySelectorAll('aside.toc a'));
  if(links.length){
    var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a;});
    links.forEach(function(a){a.addEventListener('click',function(){
      links.forEach(function(x){x.classList.remove('on');});a.classList.add('on');
    });});
    var heads=Object.keys(map).map(function(id){return document.getElementById(id);}).filter(Boolean);
    var spy=new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){
        links.forEach(function(a){a.classList.remove('on');});
        map[e.target.id]&&map[e.target.id].classList.add('on');
      }});
    },{rootMargin:'-5% 0px -65% 0px'});
    heads.forEach(function(h){spy.observe(h);});
    // keep last heading lit when scrolled to page bottom
    addEventListener('scroll',function(){
      if(innerHeight+scrollY>=document.documentElement.scrollHeight-40){
        links.forEach(function(a){a.classList.remove('on');});
        links[links.length-1]&&links[links.length-1].classList.add('on');
      }
    },{passive:true});
  }
});
</script>
</body>
</html>"""

def toc_html(md_obj):
    """render nested <ul> from python-markdown toc tokens (h2/h3 only)"""
    def walk(tokens, out, depth):
        for t in tokens:
            if t["level"] == 1 and t["children"]:
                walk(t["children"], out, depth)   # skip the h1 itself
                continue
            if t["level"] in (2, 3):
                out.append(f'<li class="l{t["level"]}"><a href="#{t["id"]}">{t["name"]}</a></li>')
            if t.get("children"):
                walk(t["children"], out, depth + 1)
    out = []
    walk(md_obj.toc_tokens, out, 0)
    if not out:
        return ""
    return ('<aside class="toc"><div class="tt">本页目录</div><ul>'
            + "".join(out) + "</ul></aside>")

MATH_RE = re.compile(r"\$\$.*?(?:\$\$|\n\n)|\$[^$\n]+?\$", re.S)
TOK = "MATHPH{:06d}ENDPH"

def render_docs():
    os.makedirs(DOCS, exist_ok=True)
    built = []   # (md_abs, html_abs, title)
    for md_abs in doc_mds:
        rel = rel_root(md_abs)
        html_abs = doc_html_abs(md_abs)
        page_dir = os.path.dirname(html_abs)
        text = open(md_abs, encoding="utf-8").read()

        # 1) stash math spans so markdown can't mangle them (false "[x](y)" links, _emphasis_)
        spans = []
        def stash(m):
            spans.append(m.group(0))
            return TOK.format(len(spans) - 1)
        text = MATH_RE.sub(stash, text)

        # 2) rewrite relative links; non-file targets (e.g. plain-text "[η](t)") are
        #    bracket-escaped so markdown keeps them literal instead of linkifying
        def sub(m):
            label, tgt = m.group(1), m.group(2).strip()
            if re.match(r"^(https?:|data:|#|mailto:)", tgt):
                return m.group(0)
            abs_t = os.path.normpath(os.path.join(os.path.dirname(md_abs), unquote(tgt)))
            if os.path.exists(abs_t):
                if abs_t.lower().endswith(".md"):
                    abs_t = doc_html_abs(abs_t)
                return f"]({label})({link_from(page_dir, abs_t)})"
            return "\\[" + label + "\\](" + tgt + ")"
        text = re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", sub, text)

        MD.reset()
        body = MD.convert(text)
        # 3) restore math spans (HTML-escaped so KaTeX auto-render sees clean text)
        for i, s in enumerate(spans):
            body = body.replace(TOK.format(i), html.escape(s))
        title = doc_title(md_abs)
        crumb = DIR_LABEL.get(rel, rel.rsplit("/", 1)[0] if "/" in rel else rel)
        home = link_from(page_dir, os.path.join(SITE, "index.html"))
        raw = link_from(page_dir, md_abs)
        # paper pdf shortcut for analysis pages
        m = GM_RE.search(rel)
        papertag = ""
        if m and rel.startswith("05_论文赏析"):
            pdf = P("03_优秀论文PDF", m.group(1), f"Problem {m.group(2).upper()}", m.group(0) + ".pdf")
            if os.path.exists(pdf):
                papertag = f'<a href="{link_from(page_dir, pdf)}">论文 PDF</a>'
        page_html = (DOC_TPL.replace("__TITLE__", title).replace("__CRUMB__", crumb)
                     .replace("__HOME__", home).replace("__RAWMD__", raw)
                     .replace("__PAPERTAG__", papertag).replace("__BODY__", body)
                     .replace("__TOC__", toc_html(MD)))
        os.makedirs(page_dir, exist_ok=True)
        with open(html_abs, "w", encoding="utf-8") as f:
            f.write(page_html)
        built.append((md_abs, html_abs, title))
    return built

built_docs = render_docs()

# ---------------- shared data for index ----------------
with open(P("04_论文文本", "_meta.json"), encoding="utf-8") as f:
    papers = json.load(f)
with open(P("02_题目汇总", "_parsed.json"), encoding="utf-8") as f:
    parsed = {int(k): v for k, v in json.load(f).items()}

CN = {
 (2010,'A'):("海王星飞船气动制动","Aerobraking a Space Probe at Neptune","astro"),
 (2010,'B'):("中世纪投石机动力学","Trebuchet: The Dynamics of a Medieval Siege Engine","mech"),
 (2011,'A'):("太空塔发射成本","Space Tower Launch Costs","astro"),
 (2011,'B'):("三分球投篮物理","The Physics of a Three Point Shot","fluid"),
 (2012,'A'):("超级地球上的火山活动","Volcanism on Super-Earths","heat"),
 (2012,'B'):("乒乓球尺寸","Table Tennis Ball Sizes","mech"),
 (2013,'A'):("木星卫星引力辅助减速入轨","Gravitationally Assisted Jupiter Orbital Entry","astro"),
 (2013,'B'):("超重力环境下的生物结构","Biological Structures in Hypergravity Environment","bio"),
 (2014,'A'):("环双星行星","Circumbinary Planets","astro"),
 (2014,'B'):("喷泉高度优化","An Optimized Fountain Model","fluid"),
 (2015,'A'):("改造火星：定向撞击","Terraforming Mars","heat"),
 (2015,'B'):("绕树高尔夫球","Golfing Around a Tree","fluid"),
 (2016,'A'):("核废料太空处置","Reactor Waste Disposal","astro"),
 (2016,'B'):("恐龙 vs 哺乳动物体型上限","Dinosaurs versus Mammals","bio"),
 (2017,'A'):("太阳帆飞往火星","Solar Sailing to Mars","astro"),
 (2017,'B'):("离子推进器排气磁场导向","Magnetic Fields to Direct Ion Thruster Exhaust","em"),
 (2018,'A'):("激光光帆纳米飞行器飞掠比邻星","Light Sail Nanocraft to Alpha Centauri","astro"),
 (2018,'B'):("堆肥堆尺寸","Compost Pile Sizes","heat"),
 (2019,'A'):("火星旅行辐射防护","Protecting Travellers to Mars","em"),
 (2019,'B'):("过山车设计","Design a Roller Coaster","mech"),
 (2020,'A'):("离子推进器低推力转移去土星","Ion Thrusters to Saturn","astro"),
 (2020,'B'):("四旋翼无人机抗风稳定性","Quadcopter Stability in Wind","fluid"),
 (2021,'A'):("火星大气演化（0.2 bar）","Evolution of Martian Atmosphere","heat"),
 (2021,'B'):("小行星撞击沿海城市","Asteroid Impact on a Coastal City","fluid"),
 (2022,'A'):("偏转小行星","Deflecting an Asteroid","astro"),
 (2022,'B'):("点球最优策略","The Best Strategy for Penalty Kicks","fluid"),
 (2023,'A'):("近太空跳伞最高安全高度","Maximum Safe Altitude for Space Jumps","fluid"),
 (2023,'B'):("三人蹦床","Trampoline Jumping","mech"),
 (2024,'A'):("空间站空气逃逸时间","Space Station Air Evacuation Time","fluid"),
 (2024,'B'):("火星 150 kW 电源最小质量设计","Mars Electrical Power","em"),
 (2025,'A'):("电声沙桑托琴的声学保真","Acoustic Preservation of the Electric Sasando","acou"),
 (2025,'B'):("19 世纪火炮弹道与无计算器射表","Artillery","fluid"),
}
DOMAINS = {
 "astro":("航天与轨道","#7E9BE0"), "fluid":("流体与空气动力","#5CB3A8"), "mech":("刚体与多体","#D29A55"),
 "heat":("热学与能量","#DB7A74"), "bio":("生物与标度律","#8CBA6E"), "em":("电磁与辐射","#A48BD9"),
 "acou":("声学与信号","#D77FAD"),
}
YEARS = list(range(2010, 2026))

INTERP = {
 (2010,'A'):"2010_题A_海王星气动制动.md",(2010,'B'):"2010_题B_投石机动力学.md",
 (2011,'A'):"2011_题A_太空塔发射成本.md",(2011,'B'):"2011_题B_三分球投篮.md",
 (2012,'A'):"2012_题A_超级地球火山.md",(2012,'B'):"2012_题B_乒乓球尺寸.md",
 (2013,'A'):"2013_题A_木星引力辅助入轨.md",(2013,'B'):"2013_题B_超重力生物结构.md",
 (2014,'A'):"2014_题A_环双星行星.md",(2014,'B'):"2014_题B_喷泉优化.md",
 (2015,'A'):"2015_题A_改造火星定向撞击.md",(2015,'B'):"2015_题B_绕树高尔夫.md",
 (2016,'A'):"2016_题A_核废料太空处置.md",(2016,'B'):"2016_题B_恐龙哺乳动物体型上限.md",
 (2017,'A'):"2017_题A_太阳帆去火星.md",(2017,'B'):"2017_题B_离子推进器磁导向.md",
 (2018,'A'):"2018_题A_光帆纳米飞行器.md",(2018,'B'):"2018_题B_堆肥堆尺寸.md",
 (2019,'A'):"2019_题A_火星辐射防护.md",(2019,'B'):"2019_题B_过山车设计.md",
 (2020,'A'):"2020_题A_离子推进器去土星.md",(2020,'B'):"2020_题B_四旋翼抗风.md",
 (2021,'A'):"2021_题A_火星大气演化.md",(2021,'B'):"2021_题B_小行星撞击沿海城市.md",
 (2022,'A'):"2022_题A_偏转小行星.md",(2022,'B'):"2022_题B_点球最优策略.md",
 (2023,'A'):"2023_题A_太空跳伞安全高度.md",(2023,'B'):"2023_题B_三人蹦床.md",
 (2024,'A'):"2024_题A_空间站空气逃逸.md",(2024,'B'):"2024_题B_火星电源最小质量.md",
 (2025,'A'):"2025_题A_电声沙桑托琴.md",(2025,'B'):"2025_题B_火炮弹道射表.md",
}

papers_by = {}
for p in papers:
    papers_by.setdefault((int(p["year"]), p["problem"]), []).append(p)
for k in papers_by:
    papers_by[k].sort(key=lambda x: x["file"])

def paper_entry(p):
    base = os.path.splitext(p["file"])[0]
    pdf = P("03_优秀论文PDF", p["year"], f"Problem {p['problem']}", p["file"])
    txt = P("04_论文文本", p["year"], base + ".txt")
    ana_md = P("05_论文赏析", p["year"], base + ".md")
    if base == "2013-GM-B-611":  # duplicate of 611a → analysis lives under 611a
        ana_md = P("05_论文赏析", "2013", "2013-GM-B-611a.md")
    ana_html = doc_html_abs(ana_md)
    png1 = P("06_论文页面图", p["year"], base + "_p1.png")
    pngf = P("06_论文页面图", p["year"], base + "_fig.png")
    title = " / ".join(p["first_lines"][:3])[:120]
    if base == "2013-GM-B-611":
        title = "（与 611a 同文异版）" + title
    return {"file": p["file"], "team": p["team"], "pages": p["pages"], "title": title,
            "pdf": site_rel(pdf), "txt": site_rel(txt),
            "ana": site_rel(ana_html), "png1": site_rel(png1),
            "pngf": site_rel(pngf)}

years_data = []
for y in YEARS:
    p_ = parsed.get(y, {})
    entry = {"year": y, "stats": (p_.get("stats") or "").strip(), "probs": []}
    for prob in "AB":
        cn, en, dom = CN[(y, prob)]
        head_src = (p_.get("prob_a") if prob == "A" else p_.get("prob_b")) or ""
        entry["probs"].append({
            "prob": prob, "cn": cn, "en": en, "dom": dom, "head": head_src[:320],
            "teams": p_.get(f"teams_{prob.lower()}", []),
            "papers": [paper_entry(x) for x in papers_by.get((y, prob), [])],
            "interp": site_rel(doc_html_abs(P("07_题目解读", INTERP[(y, prob)]))),
            "summary": site_rel(doc_html_abs(P("02_题目汇总", f"{y}_题目与官方信息.md"))),
        })
    years_data.append(entry)

# library sections (every file in the archive)
def sub_files(sub, exts):
    out = []
    for f in sorted(glob.glob(P(sub, "**", "*"), recursive=True)):
        if os.path.isfile(f) and os.path.splitext(f)[1].lower() in exts:
            out.append(f)
    return out

lib = []
lib.append({"name": "01_官网原始页面", "desc": "抓取自 uphysicsc.com 的 17 个年份页 HTML 原件与提取文本",
            "items": [{"n": os.path.basename(f), "u": site_rel(f)}
                      for f in sub_files("01_官网原始页面", {".html", ".txt", ".json"})]})
lib.append({"name": "02_官方成绩单", "desc": "各年官方成绩公告 PDF（全部金银铜牌名单）",
            "items": [{"n": os.path.basename(f), "u": site_rel(f)}
                      for f in sub_files("02_官方成绩单", {".pdf"})]})
lib.append({"name": "02_题目汇总", "desc": "每年题目原文 + 金牌队伍 + 论文清单（文档页）",
            "items": [{"n": doc_title(f), "u": site_rel(doc_html_abs(f))}
                      for f in sorted(glob.glob(P("02_题目汇总", "*.md")))]})
lib.append({"name": "03_优秀论文PDF", "desc": "74 篇金牌论文原件（见下方论文库搜索直达）", "items": []})
lib.append({"name": "04_论文文本", "desc": "论文全文提取文本，便于检索",
            "items": [{"n": os.path.basename(f), "u": site_rel(f)}
                      for f in sub_files("04_论文文本", {".txt", ".json"})]})
lib.append({"name": "05_论文赏析", "desc": "73 篇论文逐篇赏析 + 12 份批次对比表（文档页）",
            "items": [{"n": doc_title(f), "u": site_rel(doc_html_abs(f))}
                      for f in sorted(glob.glob(P("05_论文赏析", "**", "*.md"), recursive=True))
                      if not os.path.basename(f).startswith("_parsed")]})
lib.append({"name": "06_论文页面图", "desc": "148 张论文标题页/图表页渲染图（见论文库“图页”按钮）", "items": []})
lib.append({"name": "07_题目解读", "desc": "32 道题目深度解读（文档页）",
            "items": [{"n": doc_title(f), "u": site_rel(doc_html_abs(f))}
                      for f in sorted(glob.glob(P("07_题目解读", "*.md")))]})
lib.append({"name": "08_物理模型综述", "desc": "八大专题综述 + 总览（文档页）",
            "items": [{"n": doc_title(f), "u": site_rel(doc_html_abs(f))}
                      for f in sorted(glob.glob(P("08_物理模型综述", "*.md")))]})
lib.append({"name": "_工具脚本", "desc": "抓取 / 建库 / 建站全流程 Python 脚本（构建时用，无需在线浏览）",
            "items": [{"n": os.path.basename(f), "u": site_rel(f)}
                      for f in sorted(glob.glob(P("_工具脚本", "*.py")))]})

# search index over all doc pages
search_docs = []
for md_abs, html_abs, title in built_docs:
    rel = rel_root(md_abs)
    search_docs.append({"t": title, "u": site_rel(html_abs), "d": DIR_LABEL.get(rel, rel.split("/")[0])})

SEARCH_INDEX = json.dumps({"docs": search_docs}, ensure_ascii=False)
DATA_JS = json.dumps({"years": years_data, "domains": {k: {"name": v[0], "color": v[1]} for k, v in DOMAINS.items()},
                      "lib": lib, "search": search_docs}, ensure_ascii=False)

# ---------------- SVG diagrams ----------------
import math
W,H = 960, 310
tl = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img">']
tl.append('<defs><filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
tl.append(f'<line x1="40" y1="205" x2="{W-30}" y2="205" stroke="rgba(255,255,255,.12)" stroke-width="1"/>')
tl.append('<text x="30" y="133" font-size="11" fill="#6B7482" text-anchor="end">A 题</text>')
tl.append('<text x="30" y="175" font-size="11" fill="#6B7482" text-anchor="end">B 题</text>')
for i,y in enumerate(YEARS):
    x = 60 + i*((W-100)/15)
    if i % 2 == 0:
        tl.append(f'<text x="{x}" y="228" font-size="11" fill="#6B7482" text-anchor="middle">{y}</text>')
    for prob in "AB":
        cn,en,dom = CN[(y,prob)]
        col = DOMAINS[dom][1]
        cy = 205 - (76 if prob=="A" else 34)
        tl.append(f'<circle cx="{x}" cy="{cy}" r="7" fill="{col}"><title>{y} 题{prob}: {cn}</title></circle>')
lx = 40
for k,(name,col) in DOMAINS.items():
    tl.append(f'<circle cx="{lx}" cy="268" r="6" fill="{col}"/>')
    tl.append(f'<text x="{lx+13}" y="272" font-size="12" fill="#A9B2C0">{name}</text>')
    lx += 26 + len(name)*13
tl.append('</svg>')
TIMELINE_SVG = "".join(tl)

W2,H2 = 960, 260
bc = [f'<svg viewBox="0 0 {W2} {H2}" xmlns="http://www.w3.org/2000/svg">']
bc.append(f'<text x="40" y="26" font-size="13" fill="#A9B2C0">每年官方公开金牌论文数（共 {len(papers)} 篇；2024 官方未公开）</text>')
maxn = max(len(v) for v in papers_by.values())
for i,y in enumerate(YEARS):
    n = len(papers_by.get((y,'A'),[])) + len(papers_by.get((y,'B'),[]))
    x = 60 + i*((W2-100)/15)
    bh = n/maxn*150 if n else 0
    if n:
        bc.append(f'<rect x="{x-15}" y="{206-bh}" width="30" height="{bh}" rx="3" fill="#6E7BF2"/>')
        wt = ' font-weight="600"' if n == maxn else ''
        bc.append(f'<text x="{x}" y="{206-bh-7}" font-size="11.5" fill="#F0F3F7" text-anchor="middle"{wt}>{n}</text>')
    else:
        bc.append(f'<line x1="{x-9}" y1="204" x2="{x+9}" y2="204" stroke="#6B7482" stroke-width="1.5"/>')
        bc.append(f'<text x="{x}" y="193" font-size="10.5" fill="#6B7482" text-anchor="middle">无</text>')
    bc.append(f'<text x="{x}" y="224" font-size="11" fill="#6B7482" text-anchor="middle">{y}</text>')
bc.append('</svg>')
BARS_SVG = "".join(bc)

W3,H3 = 960, 430
mm = [f'<svg viewBox="0 0 {W3} {H3}" xmlns="http://www.w3.org/2000/svg">']
center = W3/2; hub = 92
mm.append(f'<circle cx="{center}" cy="210" r="{hub}" fill="#0d1526" stroke="rgba(151,167,197,.3)" stroke-width="1.5"/>')
mm.append(f'<text x="{center}" y="203" font-size="16" fill="#e9eef7" text-anchor="middle" font-weight="700" letter-spacing=".5">UPC</text>')
mm.append(f'<text x="{center}" y="224" font-size="12.5" fill="#68748e" text-anchor="middle">物理模型库</text>')
dom_files = sorted(glob.glob(P("08_物理模型综述","0*.md")))
dom_links = [quote(posix(os.path.relpath(doc_html_abs(f), SITE))) for f in dom_files]
for idx,(k,(name,col)) in enumerate(DOMAINS.items()):
    ang = -math.pi/2 + idx*(2*math.pi/8)
    cx = center + 330*math.cos(ang); cy = 210 + 150*math.sin(ang)
    mm.append(f'<line x1="{center+hub*math.cos(ang)}" y1="{210+hub*math.sin(ang)}" x2="{cx}" y2="{cy}" stroke="{col}" stroke-width="1.5" opacity="0.35"/>')
    mm.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="{col}" fill-opacity="0.14" stroke="{col}" stroke-width="1.5"/>')
    parts = name.split("与") if "与" in name else [name[:4], name[4:]]
    mm.append(f'<text x="{cx}" y="{cy-3}" font-size="12.5" fill="{col}" text-anchor="middle" font-weight="600">{parts[0]}</text>')
    mm.append(f'<text x="{cx}" y="{cy+13}" font-size="12.5" fill="{col}" text-anchor="middle" font-weight="600">{parts[1] if len(parts)>1 else ""}</text>')
    mm.append(f'<a href="{dom_links[idx]}"><circle cx="{cx}" cy="{cy}" r="52" fill="transparent"><title>{name} → 综述</title></circle></a>')
mm.append('</svg>')
MODEL_SVG = "".join(mm)

RULES = [
 ("统一货币","把不可比的方案变成可比标量：Δv、能量、剂量、裕度、起飞质量。"),
 ("端点锚定再外推","先用已知情形校准（水星/地球、MAVEN、Baumgartner 实测、FIBA 数据），再外推到题设区域。"),
 ("模糊词操作化","damage→末速度、successful→命中窗口、safe→概率阈值；先立判据再动手。"),
 ("模型分层递进","理想（真空/点质量）→ 关键修正（阻力/大气/转动）→ 扩展（风/海拔/失效），每层给量级论证。"),
 ("验证三件套","收敛性（步长减半）、极限情形（退化为解析解）、灵敏度（参数扫描）。"),
 ("负结果显式报告","论据扎实的反直觉结论（放弃气动制动、太空塔不经济）恰是高分项。"),
 ("降维交付","交付“可用的东西”：射表、列线图、修正公式、心算口诀、设计准则。"),
]
RULES_HTML = "".join(
    f'<div class="rule"><div class="rule-n">{i+1}</div><div><div class="rule-t">{t}</div><div class="rule-d">{d}</div></div></div>'
    for i,(t,d) in enumerate(RULES))

# ---------------- index.html ----------------

# ---------------- build index + deploy helpers + validate ----------------
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _build_site_tail import render_index, write_deploy_helpers, validate

render_index({"timeline": TIMELINE_SVG, "bars": BARS_SVG, "model": MODEL_SVG,
              "rules": RULES_HTML, "data": DATA_JS, "ndocs": len(search_docs), "site": SITE})
write_deploy_helpers(ROOT, SITE)
validate(ROOT, SITE)

# runtime-data validation: every URL the index JS injects must resolve from SITE dir
# (static validate() can't see these because they live inside the DATA blob)
from urllib.parse import unquote as _unq
_rt_bad = []
def _rt(u):
    if u and not os.path.exists(os.path.normpath(os.path.join(SITE, _unq(u)))):
        _rt_bad.append(u)
for _y in years_data:
    for _p in _y["probs"]:
        _rt(_p["interp"]); _rt(_p["summary"])
        for _pp in _p["papers"]:
            for _k in ("pdf", "txt", "ana", "png1", "pngf"):
                _rt(_pp[_k])
for _g in lib:
    for _it in _g["items"]:
        _rt(_it["u"])
for _s in search_docs:
    _rt(_s["u"])
if _rt_bad:
    print(f"RUNTIME-DATA VALIDATION FAILED: {len(_rt_bad)} broken urls")
    for u in _rt_bad[:30]:
        print("  ", u)
    raise SystemExit(1)
print(f"runtime-data validation ok: {sum(len(p['papers']) for y in years_data for p in y['probs'])} papers "
      f"+ {len(lib)} lib groups + {len(search_docs)} search docs")

print(f"docs built: {len(built_docs)} | papers: {len(papers)} | all done")
