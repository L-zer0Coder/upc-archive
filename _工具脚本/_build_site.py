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

DOC_DIRS = ["05_论文赏析", "07_题目解读", "08_物理模型综述", "02_题目汇总",
             "10_论文精读", "11_论文模板与工具"]
DIR_LABEL = {
    "05_论文赏析": "论文赏析", "07_题目解读": "题目深度解读", "08_物理模型综述": "物理模型综述",
    "02_题目汇总": "题目与官方信息", "10_论文精读": "论文精读教程",
    "11_论文模板与工具": "论文模板与工具", "README.md": "档案库说明",
}
GM_RE = re.compile(r"(\d{4})-GM-([AB])-([0-9A-Za-z]+)", re.I)  # \w 会吞掉「_精读」后缀，故只取字母数字

# 本地自托管的前端依赖（构建前由 _fetch_vendor.py 下载；不再依赖境外 CDN）
VENDOR = os.path.join(SITE, "vendor")
KATEX_CSS = os.path.join(VENDOR, "katex", "katex.min.css")
KATEX_JS = os.path.join(VENDOR, "katex", "katex.min.js")
KATEX_AUTORENDER = os.path.join(VENDOR, "katex", "contrib", "auto-render.min.js")
MERMAID_JS = os.path.join(VENDOR, "mermaid", "mermaid.min.js")

# ---------------- 第 17 届赛事时钟 ----------------
# 北京时间 2026-11-07 09:00 开赛，48 小时；用绝对 UTC 偏移写死，不受访问者时区影响
EVENT_START_MS = 1794013200000   # 2026-11-07T09:00:00+08:00
EVENT_END_MS = EVENT_START_MS + 48 * 3600 * 1000
# 阶段表取自 11_论文模板与工具/48小时作战手册.md 的 T0–T9（小时区间按主序列排，去掉并行重叠）
PHASES = [
    [0, 2, "T0", "读题与选题", "两题各 15 分钟独立读，按“离主场模型更近”选题"],
    [2, 4, "T1", "去模糊化 + 敲定路线图", "把 significant / safely 翻译成可计算判据；里程碑①一页纸作战图"],
    [4, 8, "T2", "基准方案（必须解析）", "先算闭式对照情形，给主模型一个锚数字"],
    [8, 14, "T3", "主模型推导", "从守恒律写主方程，每个假设配一句量级自辩"],
    [14, 20, "T3·T4", "主模型收口 + 数值起跑", "第 14 小时中点检查：主方程没落地就立刻降级模型"],
    [20, 26, "T4", "数值实现", "先跑通一条轨迹，再谈参数扫描"],
    [26, 30, "T5", "修正项与扩展", "按量级表裁决“必须建模 / 可忽略 / 有余力”"],
    [30, 38, "T6", "验证三件套", "收敛性 + 极限情形 + 灵敏度 —— 金银牌的分水岭"],
    [38, 41, "T7", "图表精修", "每张图过 checklist：编号 / 被正文点名 / 单位 / 结论进图题"],
    [41, 46, "T8", "写作与整合", "摘要最后写，但必须带数值结论"],
    [46, 48, "T9", "交叉互查 + 提前交卷", "提前 2 小时交，官网截止不等人"],
]

def posix(p):
    return p.replace("\\", "/")

def rel_root(path_abs):
    return posix(os.path.relpath(path_abs, ROOT))

def site_rel(path_abs):
    """URL for a target as seen from the site entry page (repo-root index.html)."""
    return quote(posix(os.path.relpath(path_abs, ROOT)))

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

DOC_TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ · UPC 全档案库</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%239C3F2E'/%3E%3Ctext x='50' y='70' font-size='58' font-weight='700' text-anchor='middle' fill='%23FDFCF8' font-family='Georgia,serif'%3EU%3C/text%3E%3C/svg%3E">
<meta name="description" content="__DESC__">
<meta property="og:type" content="article">
<meta property="og:site_name" content="UPC 全档案库">
<meta property="og:title" content="__TITLE__ · UPC 全档案库">
<meta property="og:description" content="__DESC__">
<meta property="og:image" content="https://l-zer0coder.github.io/upc-archive/og-image.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="__CSS_KATEX__">
<script defer src="__JS_KATEX__"></script>
<script defer src="__JS_AUTORENDER__"></script>
__MERMAID_TAG__
<style>
:root{
 --paper:#F7F4ED;--sheet:#FDFCF8;--ink:#2A251E;--mut:#6E6557;--dim:#786E60;
 --line:#E7E0D1;--line2:#D9D0BD;
 --acc:#9C3F2E;--acc-d:#7E3225;--acc-soft:rgba(156,63,46,.07);
 --serif:Georgia,"Times New Roman","Source Han Serif SC","Noto Serif SC","Songti SC","STSong","SimSun",serif;
 --sans:"Segoe UI","PingFang SC","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
 --mono:ui-monospace,"Cascadia Code",Consolas,monospace}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:74px}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:2}
#pbar{position:fixed;top:0;left:0;height:2px;width:0;z-index:60;background:var(--acc);transition:width .1s}
.topbar{position:sticky;top:0;z-index:9;background:rgba(253,252,248,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.topbar .in{max-width:1200px;margin:0 auto;display:flex;align-items:center;gap:8px;padding:9px 22px;min-width:0}
.topbar a{color:var(--mut);text-decoration:none;font-size:12.5px;white-space:nowrap}
.topbar a:hover{color:var(--acc)}
.topbar .tag{border:1px solid var(--line2);border-radius:3px;padding:2px 10px}
.topbar .tag:hover{border-color:var(--acc)}
.topbar .ck{cursor:pointer;font-family:inherit;background:var(--sheet);color:var(--mut);font-size:12.5px;white-space:nowrap}
.topbar .ck:hover{border-color:var(--acc);color:var(--acc)}
.topbar .ck.done{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.topbar .ck.done:hover{background:var(--acc-d);color:#FDFCF8}
.brand{display:flex;align-items:center;gap:9px;color:var(--ink);font-weight:600;font-size:13.5px;margin-right:4px}
.brand:hover{color:var(--ink)}
.brand .seal{width:24px;height:24px;border-radius:5px;background:var(--acc);color:#FDFCF8;display:flex;align-items:center;justify-content:center;font-family:var(--serif);font-size:13px;font-weight:700}
.crumb{color:var(--dim);font-size:12px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}
/* 赛事时钟徽章：赛前显示 D-天数，赛中显示已用时长 */
.topbar .clock{margin-left:12px;flex-shrink:0;font-family:var(--mono);font-size:11px;line-height:1.9;
 letter-spacing:.02em;padding:1px 8px;border:1px solid rgba(156,63,46,.28);border-radius:3px;
 color:var(--acc);background:var(--acc-soft);white-space:nowrap;font-variant-numeric:tabular-nums}
.topbar .clock:hover{border-color:var(--acc);color:var(--acc-d);background:rgba(156,63,46,.12)}
.topbar .clock[data-s="live"]{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.topbar .clock[data-s="post"]{color:var(--dim);border-color:var(--line2);background:transparent}
.layout{display:flex;justify-content:center;gap:46px;max-width:1200px;margin:0 auto;padding:34px 22px 90px;align-items:flex-start}
.content{flex:0 1 780px;min-width:0}
.sheet{background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:44px 52px 54px}
.sheet h1{font-family:var(--serif);font-size:27px;line-height:1.55;margin:.15em 0 .8em;font-weight:700}
.sheet h2{font-family:var(--serif);font-size:21px;line-height:1.6;margin:1.9em 0 .6em;scroll-margin-top:74px;font-weight:700;padding-bottom:.3em;border-bottom:1px solid var(--line)}
.sheet h3{font-family:var(--serif);font-size:17.5px;margin:1.5em 0 .4em;scroll-margin-top:74px;font-weight:700}
.sheet h4{font-size:15.5px;margin:1.2em 0 .4em;font-weight:600}
.sheet p{margin:.85em 0}
.sheet a{color:var(--acc)}
.sheet a:hover{color:var(--acc-d);text-decoration:underline;text-underline-offset:3px}
.sheet ul,.sheet ol{padding-left:1.6em;margin:.7em 0}
.sheet li{margin:.3em 0}
.sheet li::marker{color:var(--dim)}
code{background:#F2EDE2;border:1px solid var(--line);border-radius:3px;padding:.5px 6px;font-size:.86em;font-family:var(--mono)}
pre{background:#F9F6EF;border:1px solid var(--line);border-radius:4px;padding:14px 17px;overflow:auto;line-height:1.75;font-size:13.5px}
pre code{border:none;background:none;padding:0}
blockquote{margin:1.1em 0;padding:2px 0 2px 18px;border-left:2px solid var(--acc);color:var(--mut)}
blockquote p{margin:.5em 0}
table{border-collapse:collapse;width:100%;margin:1em 0;font-size:13.8px;display:block;overflow-x:auto;line-height:1.8}
th,td{border-bottom:1px solid var(--line);padding:8px 12px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:12px;letter-spacing:.05em;border-bottom:1px solid var(--line2);background:var(--sheet);white-space:nowrap}
td:first-child,th:first-child{white-space:nowrap}
tbody tr:nth-child(2n) td{background:#F8F5EE}
hr{border:none;border-top:1px solid var(--line);margin:2.2em 0}
.sheet img{max-width:100%;border:1px solid var(--line);border-radius:3px}
.mermaid{background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:12px;margin:1em 0;display:flex;justify-content:center}
.mermaid svg{max-width:100%;height:auto}
.katex-display{overflow-x:auto;padding:6px 0}.katex{font-size:1.03em}
footer{text-align:center;color:var(--dim);font-size:12px;padding:28px 20px}
#top{position:fixed;right:26px;bottom:26px;z-index:30;background:var(--sheet);border:1px solid var(--line2);color:var(--mut);
 border-radius:50%;width:40px;height:40px;font-size:16px;cursor:pointer;opacity:0;pointer-events:none;transition:.2s}
#top.on{opacity:1;pointer-events:auto}
#top:hover{color:var(--acc);border-color:var(--acc)}
aside.toc{position:sticky;top:74px;width:214px;flex-shrink:0;max-height:calc(100vh - 100px);overflow-y:auto;padding:4px 0}
aside.toc .tt{font-weight:600;font-size:11px;color:var(--dim);letter-spacing:.12em;padding:0 0 8px 14px}
aside.toc ul{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}
aside.toc li a{display:block;padding:4px 12px;margin-left:-1px;color:var(--mut);text-decoration:none;border-left:2px solid transparent;line-height:1.75;font-size:12.5px}
aside.toc li.l3 a{padding-left:26px;font-size:12px}
aside.toc li a:hover{color:var(--ink)}
aside.toc li a.on{color:var(--acc);border-left-color:var(--acc)}
aside.toc::-webkit-scrollbar{width:5px}
aside.toc::-webkit-scrollbar-thumb{background:var(--line2);border-radius:4px}
@media(max-width:1100px){aside.toc{display:none}.sheet{padding:26px 20px 34px}}
/* ---- 窄屏：顶栏折行，避免整页横向溢出 ---- */
@media(max-width:760px){
 .topbar .in{flex-wrap:wrap;row-gap:6px;padding:8px 16px;gap:6px}
 .topbar .brand{margin-right:2px}
 .crumb{display:none}
 .layout{padding:18px 14px 64px}
 .sheet{padding:22px 18px 28px}
 .sheet h1{font-size:22px}
 body{font-size:15px;line-height:1.95}
 .sheet h2{font-size:19px}
 .realted-wrap{padding:0 4px}
}
/* ---- 打印：48h 手册/checklist 可直接出纸质版 ---- */
@media print{
 .topbar,#pbar,#top,aside.toc,footer,.ck,.tcard .btns,.realted-wrap{display:none!important}
 body{background:#fff;font-size:11pt;line-height:1.7}
 .layout{display:block;padding:0;max-width:none}
 .content{flex:none;max-width:none}
 .sheet{border:none;background:#fff;padding:0;border-radius:0}
 .sheet h1,.sheet h2,.sheet h3{page-break-after:avoid}
 .sheet table,.sheet pre,.sheet .mermaid{page-break-inside:avoid}
 a{color:#000;text-decoration:none}
}
/* ---- 同题对比块 ---- */
.realted-wrap{margin-top:26px}
.realted{background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:16px 20px}
.realted .tt{font-size:11px;letter-spacing:.12em;color:var(--dim);margin-bottom:10px}
.realted ul{list-style:none;margin:0;padding:0;display:block}
.realted li{display:flex;align-items:baseline;gap:10px;padding:6px 0;border-bottom:1px solid var(--line);font-size:13px;line-height:1.7}
.realted li:last-child{border-bottom:none}
.realted li.self{color:var(--acc);font-weight:600}
.realted .t{font-family:var(--mono);font-size:11.5px;color:var(--dim);flex-shrink:0;min-width:46px}
.realted .n{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
</style>
</head>
<body>
<div id="pbar"></div>
<div class="topbar"><div class="in">
  <a class="brand" href="__HOME__"><span class="seal">U</span>UPC 全档案库</a>
  <a href="__HOME__#guide">使用指南</a>
  <button id="ck" class="tag ck" type="button" hidden></button>
  __PAPERTAG__
  <a class="tag" href="__RAWMD__">Markdown</a>
  <span class="crumb">__CRUMB__ · __TITLE__</span>
  <a class="clock" id="clock" href="__HOME__#race" hidden aria-label="第 17 届 UPC 赛程"></a>
</div></div>
<div class="layout">
  <div class="content"><div class="sheet">
__BODY__
</div>
__RELATED__
</div>
__TOC__
</div>
<footer>UPC 2010–2025 全档案库 · 内容仅供学习交流 · 论文版权归原队伍与 UPC 官方（uphysicsc.com）</footer>
<div style="max-width:824px;margin:26px auto;padding:0 20px"><div id="giscus-thread" hidden></div></div>
<button id="top" aria-label="回到顶部">↑</button>
<script>
/* ---------- 打卡：浏览自动标记 + 手动打卡（localStorage） ---------- */
var PKEY="__PKEY__",PKIND="__PKIND__",CKS="upcProgress.v1";
function ckLoad(){try{return JSON.parse(localStorage.getItem(CKS)||"{}")}catch(e){return{}}}
function ckSave(s){try{localStorage.setItem(CKS,JSON.stringify(s))}catch(e){}}
function ckPush(s,st){(s.log=s.log||[]).unshift({k:PKEY,t:PKIND,s:st,ts:Date.now()});if(s.log.length>80)s.log.length=80;}
function ckSet(state){
  var s=ckLoad();
  var bag=PKIND==="paper"?(s.p=s.p||{}):(s.i=s.i||{});
  var it=bag[PKEY]||{},now=Date.now();
  if(state==="v"){if(!it.v){it.v=now;ckPush(s,"v");}}
  else if(state==="t"){if(it.d){delete it.d;ckPush(s,"u");}else{it.d=now;ckPush(s,"d");}}
  bag[PKEY]=it;ckSave(s);ckUI();
}
function ckUI(){
  var b=document.getElementById('ck');if(!b||!PKEY)return;
  var s=ckLoad(),it=(PKIND==="paper"?(s.p||{}):(s.i||{}))[PKEY]||{};
  var done=!!it.d;
  b.textContent=done?"已打卡 ✓":"打卡 · 标记已吃透";
  b.classList.toggle('done',done);
}
document.addEventListener("DOMContentLoaded", function(){
  if(PKEY){
    var b=document.getElementById('ck');b.hidden=false;
    b.addEventListener('click',function(){ckSet("t")});
    ckUI();
    setTimeout(function(){ckSet("v")},3000);  // 停留 3 秒 = 浏览过（自动标记）
  }
  if (window.renderMathInElement) renderMathInElement(document.querySelector(".sheet"), {
    delimiters:[{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}],
    ignoredTags:["script","style","textarea","pre","code"]});
  if (window.mermaid){
    mermaid.initialize({startOnLoad:false,theme:"neutral",securityLevel:"loose"});
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
/* ---------- 赛事时钟徽章：赛前 D-天数，赛中已用时长，点回首页赛程 ---------- */
(function(){
  var S=__EV_START__,E=__EV_END__,el=document.getElementById('clock');
  if(!el)return;
  function p2(n){return n<10?'0'+n:''+n;}
  function upd(){
    var t=Date.now();
    if(t<S){var ms=S-t,dd=Math.floor(ms/864e5);
      if(dd>=1){el.textContent='赛前 D-'+dd;el.dataset.s='pre';}
      else{var hh=Math.floor(ms/36e5),mm=Math.floor(ms%36e5/6e4);
        el.textContent='赛前 '+p2(hh)+':'+p2(mm);el.dataset.s='pre';}}
    else if(t<E){var u=Math.floor((t-S)/1000);
      el.textContent='赛中 '+p2(Math.floor(u/3600))+':'+p2(Math.floor(u%3600/60));el.dataset.s='live';}
    else{el.textContent='第 17 届已结束';el.dataset.s='post';}
    el.hidden=false;
  }
  upd();setInterval(upd,30000);
})();
/* ---------- giscus 讨论区（可选，零默认请求）：填好仓库配置后重建即启用 ---------- */
var GISCUS={repo:"",repoId:"",category:"",categoryId:""};
if(GISCUS.repo){
  var gbox=document.getElementById('giscus-thread');
  if(gbox){
    gbox.hidden=false;
    var gs=document.createElement('script');
    gs.src='https://giscus.app/client.js';
    gs.setAttribute('data-repo',GISCUS.repo);gs.setAttribute('data-repo-id',GISCUS.repoId);
    gs.setAttribute('data-category',GISCUS.category);gs.setAttribute('data-category-id',GISCUS.categoryId);
    gs.setAttribute('data-mapping','pathname');gs.setAttribute('data-strict','0');
    gs.setAttribute('data-reactions-enabled','1');gs.setAttribute('data-emit-metadata','0');
    gs.setAttribute('data-theme','light');gs.setAttribute('data-lang','zh-CN');
    gs.setAttribute('crossorigin','anonymous');gs.async=true;
    gbox.appendChild(gs);
  }
}
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
        home = link_from(page_dir, P("index.html"))
        raw = link_from(page_dir, md_abs)
        # 摘要：给 meta description / OG 用（也写进搜索索引）
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
        desc = html.escape(plain[:118] + ("…" if len(plain) > 118 else ""), quote=True)
        # per-paper pages (赏析/精读) get cross-links: PDF 原件 + 姊妹篇
        m = GM_RE.search(rel)
        papertag = ""
        if m:
            base = m.group(0)
            yr, prob = m.group(1), m.group(2).upper()
            pdf = P("03_优秀论文PDF", yr, f"Problem {prob}", base + ".pdf")
            if os.path.exists(pdf):
                papertag += f'<a class="tag" href="{link_from(page_dir, pdf)}">论文 PDF</a>'
            if rel.startswith("05_论文赏析"):
                jd = P("10_论文精读", yr, base + "_精读.md")
                if os.path.exists(jd):
                    papertag += f'<a class="tag" href="{link_from(page_dir, doc_html_abs(jd))}">手把手精读</a>'
            elif rel.startswith("10_论文精读"):
                ana = P("05_论文赏析", yr, base + ".md")
                if os.path.exists(ana):
                    papertag += f'<a class="tag" href="{link_from(page_dir, doc_html_abs(ana))}">本篇赏析</a>'
        # 打卡键：论文页 = PDF 文件名（611 归并到 611a）；题目解读页 = 年-题
        pkey, pkind = "", ""
        if m:
            pkey, pkind = re.sub(r"-611$", "-611a", m.group(0)), "paper"
        elif rel.startswith("07_题目解读"):
            mi = re.match(r"(\d{4})_题([AB])_", os.path.basename(rel))
            if mi:
                pkey, pkind = f"{mi.group(1)}-{mi.group(2).upper()}", "interp"

        # 同年同题的其他金牌论文：UPC 学习里最核心的动作就是横向对比同题解法
        related = ""
        if m and pkind == "paper":
            yr, prob = m.group(1), m.group(2).upper()
            siblings = papers_by.get((int(yr), prob), [])
            if len(siblings) > 1:
                rows = []
                for x in siblings:
                    b2 = os.path.splitext(x["file"])[0]
                    key2 = "2013-GM-B-611a" if b2 == "2013-GM-B-611" else b2
                    ana2 = P("05_论文赏析", yr, key2 + ".md")
                    jd2 = P("10_论文精读", yr, key2 + "_精读.md")
                    if rel.startswith("10_论文精读"):
                        tgt2 = jd2 if os.path.exists(jd2) else ana2
                    else:
                        tgt2 = ana2 if os.path.exists(ana2) else jd2
                    t2 = doc_title(ana2) if os.path.exists(ana2) else key2
                    t2 = re.sub(r"（.*?）$", "", t2).strip()
                    is_self = key2 == re.sub(r"-611$", "-611a", m.group(0))
                    if is_self:
                        rows.append(f'<li class="self"><span class="t">#{x["team"]}</span>'
                                    f'<span class="n">{html.escape(t2)}</span><span>本篇</span></li>')
                    else:
                        rows.append(f'<li><span class="t">#{x["team"]}</span>'
                                    f'<a class="n" href="{link_from(page_dir, doc_html_abs(tgt2) if tgt2.endswith(".md") else tgt2)}"'
                                    f' title="{html.escape(t2)}">{html.escape(t2)}</a>'
                                    f'<span class="t" style="text-align:right">{x["pages"]} 页</span></li>')
                related = ('<div class="realted-wrap"><div class="realted">'
                           f'<div class="tt">{yr} 题{prob} · 同年同题金牌论文（{len(siblings)} 篇）</div>'
                           '<ul>' + "".join(rows) + '</ul></div></div>')

        # Mermaid 只在该页真的含流程图时才引入（省掉 115 个页面各 3MB 的无谓下载）
        has_mermaid = 'class="language-mermaid"' in body
        mermaid_tag = (f'<script src="{link_from(page_dir, MERMAID_JS)}"></script>'
                       if has_mermaid and os.path.exists(MERMAID_JS) else "")

        page_html = (DOC_TPL.replace("__TITLE__", title).replace("__CRUMB__", crumb)
                     .replace("__HOME__", home).replace("__RAWMD__", raw)
                     .replace("__PAPERTAG__", papertag).replace("__BODY__", body)
                     .replace("__PKEY__", pkey).replace("__PKIND__", pkind)
                     .replace("__DESC__", desc).replace("__RELATED__", related)
                     .replace("__CSS_KATEX__", link_from(page_dir, KATEX_CSS))
                     .replace("__JS_KATEX__", link_from(page_dir, KATEX_JS))
                     .replace("__JS_AUTORENDER__", link_from(page_dir, KATEX_AUTORENDER))
                     .replace("__EV_START__", str(EVENT_START_MS))
                     .replace("__EV_END__", str(EVENT_END_MS))
                     .replace("__MERMAID_TAG__", mermaid_tag)
                     .replace("__TOC__", toc_html(MD)))
        os.makedirs(page_dir, exist_ok=True)
        with open(html_abs, "w", encoding="utf-8") as f:
            f.write(page_html)
        built.append((md_abs, html_abs, title, plain[:600]))
    return built

# ---------------- shared data for index ----------------
with open(P("04_论文文本", "_meta.json"), encoding="utf-8") as f:
    papers = json.load(f)
# 元数据里早期抓的是大写 .PDF，磁盘上已统一改小写；这里同步，避免生成大写的死链
for _p in papers:
    _p["file"] = re.sub(r"\.PDF$", ".pdf", _p["file"], flags=re.I)
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
 "astro":("航天与轨道","#3A5A8C"), "fluid":("流体与空气动力","#2F7D6B"), "mech":("刚体与多体","#9A6232"),
 "heat":("热学与能量","#B0543B"), "bio":("生物与标度律","#647C35"), "em":("电磁与辐射","#6E5599"),
 "acou":("声学与信号","#A84A76"),
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

# 文档页渲染依赖 papers_by（用于「同年同题其他论文」对比块），故延后到这里执行
built_docs = render_docs()

def paper_entry(p):
    base = os.path.splitext(p["file"])[0]
    pdf = P("03_优秀论文PDF", p["year"], f"Problem {p['problem']}", p["file"])
    txt = P("04_论文文本", p["year"], base + ".txt")
    ana_md = P("05_论文赏析", p["year"], base + ".md")
    if base == "2013-GM-B-611":  # duplicate of 611a → analysis & deep-read live under 611a
        ana_md = P("05_论文赏析", "2013", "2013-GM-B-611a.md")
    ana_html = doc_html_abs(ana_md)
    png1 = P("06_论文页面图", p["year"], base + "_p1.png")
    pngf = P("06_论文页面图", p["year"], base + "_fig.png")
    title = " / ".join(p["first_lines"][:3])[:120]
    if base == "2013-GM-B-611":
        title = "（与 611a 同文异版）" + title
    jd_base = "2013-GM-B-611a" if base == "2013-GM-B-611" else base
    jd_md = P("10_论文精读", p["year"], jd_base + "_精读.md")
    return {"file": p["file"], "team": p["team"], "pages": p["pages"], "title": title,
            "pdf": site_rel(pdf), "txt": site_rel(txt),
            "ana": site_rel(ana_html), "png1": site_rel(png1),
            "pngf": site_rel(pngf),
            "jd": site_rel(doc_html_abs(jd_md)) if os.path.exists(jd_md) else None}

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
lib.append({"name": "10_论文精读", "desc": "73 篇金牌论文逐篇手把手精读（逐节导读/图表深析/公式推导/建模决策链）",
            "items": [{"n": doc_title(f), "u": site_rel(doc_html_abs(f))}
                      for f in sorted(glob.glob(P("10_论文精读", "**", "*.md"), recursive=True))]})
lib.append({"name": "11_论文模板与工具", "desc": "LaTeX 模板 / 图表配方库 / 写作句库 / 建模决策树 / 48h 手册 / 终检清单 / 完整历程（文档页）",
            "items": [{"n": doc_title(f), "u": site_rel(doc_html_abs(f))}
                      for f in sorted(glob.glob(P("11_论文模板与工具", "**", "*.md"), recursive=True))
                      ] + [{"n": "LaTeX模板/" + os.path.basename(f), "u": site_rel(f)}
                           for f in sorted(glob.glob(P("11_论文模板与工具", "LaTeX模板", "*.tex")))]
                      + [{"n": "图表配方库/matplotlib_recipes.py（图表配方库源码）", "u": site_rel(P("11_论文模板与工具", "图表配方库", "matplotlib_recipes.py"))}]})
lib.append({"name": "_工具脚本", "desc": "抓取 / 建库 / 建站全流程 Python 脚本（构建时用，无需在线浏览）",
            "items": [{"n": os.path.basename(f), "u": site_rel(f)}
                      for f in sorted(glob.glob(P("_工具脚本", "*.py")))]})
lib.append({"name": "12_赛时工具", "desc": "赛时交互工具：48 小时作战室 / 提示词工坊 / 模型闪卡 / 选题助手 / 数值实验台",
            "items": [{"n": "48小时作战室", "u": "12_赛时工具/warroom.html"},
                      {"n": "AI 提示词工坊", "u": "12_赛时工具/prompts.html"},
                      {"n": "物理模型闪卡", "u": "12_赛时工具/flashcards.html"},
                      {"n": "选题助手", "u": "12_赛时工具/selector.html"},
                      {"n": "数值实验台", "u": "12_赛时工具/lab.html"}]})

# search index over all doc pages（含正文片段：标题搜不到关键词时靠它兜底）
search_docs = []
for md_abs, html_abs, title, snip in built_docs:
    rel = rel_root(md_abs)
    search_docs.append({"t": title, "u": site_rel(html_abs),
                        "d": DIR_LABEL.get(rel, rel.split("/")[0]), "c": snip})

SEARCH_INDEX = json.dumps({"docs": search_docs}, ensure_ascii=False)
# 全文索引单独成文件，首页不背这 ~300KB；首次输入搜索时按需加载
with open(os.path.join(ROOT, "search-index.js"), "w", encoding="utf-8") as f:
    f.write("window.UPC_SEARCH=" + json.dumps(search_docs, ensure_ascii=False) + ";")
DATA_JS = json.dumps({"years": years_data,
                      "domains": {k: {"name": v[0], "color": v[1]} for k, v in DOMAINS.items()},
                      "lib": lib}, ensure_ascii=False)

# 模板工坊数据：LaTeX模板/ 下全部 .tex（名称、链接、大小）+ 完整历程文档页链接
TEX_JS = json.dumps([{"n": os.path.basename(f), "u": site_rel(f),
                      "kb": round(os.path.getsize(f) / 1024, 1)}
                     for f in sorted(glob.glob(P("11_论文模板与工具", "LaTeX模板", "*.tex")))],
                    ensure_ascii=False)
JOURNEY_URL = site_rel(doc_html_abs(P("11_论文模板与工具", "一篇金牌论文的完整历程.md")))

# ---------------- SVG diagrams ----------------
import math
W,H = 960, 310
tl = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img">']
tl.append('<defs><filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
tl.append(f'<line x1="40" y1="205" x2="{W-30}" y2="205" stroke="#D9D0BD" stroke-width="1"/>')
tl.append('<text x="30" y="133" font-size="11" fill="#9A9080" text-anchor="end">A 题</text>')
tl.append('<text x="30" y="175" font-size="11" fill="#9A9080" text-anchor="end">B 题</text>')
for i,y in enumerate(YEARS):
    x = 60 + i*((W-100)/15)
    if i % 2 == 0:
        tl.append(f'<text x="{x}" y="228" font-size="11" fill="#9A9080" text-anchor="middle">{y}</text>')
    for prob in "AB":
        cn,en,dom = CN[(y,prob)]
        col = DOMAINS[dom][1]
        cy = 205 - (76 if prob=="A" else 34)
        tl.append(f'<circle cx="{x}" cy="{cy}" r="7" fill="{col}"><title>{y} 题{prob}: {cn}</title></circle>')
lx = 40
for k,(name,col) in DOMAINS.items():
    tl.append(f'<circle cx="{lx}" cy="268" r="6" fill="{col}"/>')
    tl.append(f'<text x="{lx+13}" y="272" font-size="12" fill="#6E6557">{name}</text>')
    lx += 26 + len(name)*13
tl.append('</svg>')
TIMELINE_SVG = "".join(tl)

W2,H2 = 960, 260
bc = [f'<svg viewBox="0 0 {W2} {H2}" xmlns="http://www.w3.org/2000/svg">']
bc.append(f'<text x="40" y="26" font-size="13" fill="#6E6557">每年官方公开金牌论文数（共 {len(papers)} 篇；2024 官方未公开）</text>')
maxn = max(len(v) for v in papers_by.values())
for i,y in enumerate(YEARS):
    n = len(papers_by.get((y,'A'),[])) + len(papers_by.get((y,'B'),[]))
    x = 60 + i*((W2-100)/15)
    bh = n/maxn*150 if n else 0
    if n:
        bc.append(f'<rect x="{x-15}" y="{206-bh}" width="30" height="{bh}" rx="2" fill="#9C3F2E" fill-opacity="0.85"/>')
        wt = ' font-weight="600"' if n == maxn else ''
        bc.append(f'<text x="{x}" y="{206-bh-7}" font-size="11.5" fill="#2A251E" text-anchor="middle"{wt}>{n}</text>')
    else:
        bc.append(f'<line x1="{x-9}" y1="204" x2="{x+9}" y2="204" stroke="#9A9080" stroke-width="1.5"/>')
        bc.append(f'<text x="{x}" y="193" font-size="10.5" fill="#9A9080" text-anchor="middle">无</text>')
    bc.append(f'<text x="{x}" y="224" font-size="11" fill="#9A9080" text-anchor="middle">{y}</text>')
bc.append('</svg>')
BARS_SVG = "".join(bc)

W3,H3 = 960, 430
mm = [f'<svg viewBox="0 0 {W3} {H3}" xmlns="http://www.w3.org/2000/svg">']
center = W3/2; hub = 92
mm.append(f'<circle cx="{center}" cy="210" r="{hub}" fill="#FBF9F3" stroke="#D9D0BD" stroke-width="1.5"/>')
mm.append(f'<text x="{center}" y="203" font-size="16" fill="#2A251E" text-anchor="middle" font-weight="700" letter-spacing=".5">UPC</text>')
mm.append(f'<text x="{center}" y="224" font-size="12.5" fill="#9A9080" text-anchor="middle">物理模型库</text>')
dom_files = sorted(glob.glob(P("08_物理模型综述", "0*.md")))   # 00 总览 / 01–07 七个物理域 / 08 方法论
# 八个节点 = 七个物理域 + 方法论；按域名顺序映射到 01–07，而不是直接按下标（旧版在此处整体错位一格）
dom_nodes = [(DOMAINS[k][0], DOMAINS[k][1], dom_files[i + 1])
             for i, k in enumerate(DOMAINS) if i + 1 < len(dom_files)]
if len(dom_files) > 8:
    dom_nodes.append(("方法论与数值算法", "#7A7161", dom_files[8]))
for idx, (name, col, src_md) in enumerate(dom_nodes):
    ang = -math.pi / 2 + idx * (2 * math.pi / len(dom_nodes))
    cx = center + 330 * math.cos(ang); cy = 210 + 150 * math.sin(ang)
    mm.append(f'<line x1="{center+hub*math.cos(ang)}" y1="{210+hub*math.sin(ang)}" x2="{cx}" y2="{cy}" stroke="{col}" stroke-width="1.5" opacity="0.45"/>')
    mm.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="{col}" fill-opacity="0.12" stroke="{col}" stroke-width="1.5"/>')
    parts = name.split("与") if "与" in name else [name[:4], name[4:]]
    mm.append(f'<text x="{cx}" y="{cy-3}" font-size="12.5" fill="{col}" text-anchor="middle" font-weight="600">{parts[0]}</text>')
    mm.append(f'<text x="{cx}" y="{cy+13}" font-size="12.5" fill="{col}" text-anchor="middle" font-weight="600">{parts[1] if len(parts)>1 else ""}</text>')
    mm.append(f'<a href="{site_rel(doc_html_abs(src_md))}"><circle cx="{cx}" cy="{cy}" r="52" fill="transparent"><title>{name} → 综述</title></circle></a>')
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
import _build_tools

# 赛时工具页（作战室等），赛事时间与阶段表与全站同源
_build_tools.render_tools({"root": ROOT, "ev_start": EVENT_START_MS,
                           "ev_end": EVENT_END_MS, "phases": PHASES})

render_index({"timeline": TIMELINE_SVG, "bars": BARS_SVG, "model": MODEL_SVG,
              "rules": RULES_HTML, "data": DATA_JS, "ndocs": len(search_docs),
              "site": SITE, "root": ROOT,
              "model_url": site_rel(doc_html_abs(P("08_物理模型综述", "00_总览.md"))),
              "manual_url": site_rel(doc_html_abs(P("11_论文模板与工具", "48小时作战手册.md"))),
              "ev_start": EVENT_START_MS, "ev_end": EVENT_END_MS,
              "phases": json.dumps(PHASES, ensure_ascii=False),
              "tex": TEX_JS, "journey": JOURNEY_URL})
write_deploy_helpers(ROOT, SITE)

# 运行时注入的 URL 也要校验（静态扫描看不到 DATA blob 里的字段）
_extra = []
for _y in years_data:
    for _p in _y["probs"]:
        _extra.append((ROOT, _p["interp"], f"题目解读 {_y['year']}-{_p['prob']}"))
        _extra.append((ROOT, _p["summary"], f"题目汇总 {_y['year']}-{_p['prob']}"))
        for _pp in _p["papers"]:
            for _k in ("pdf", "txt", "ana", "png1", "pngf", "jd"):
                if _pp.get(_k):
                    _extra.append((ROOT, _pp[_k], f"论文 {_pp['file']}.{_k}"))
for _g in lib:
    for _it in _g["items"]:
        _extra.append((ROOT, _it["u"], f"全库 {_g['name']}/{_it['n']}"))
for _t in json.loads(TEX_JS):
    _extra.append((ROOT, _t["u"], f"模板 {_t['n']}"))
# 赛时工具页自身的相对链接也纳入校验（跳过 JS 运行时拼接的 URL：含引号/加号的都是模板串）
_href_re = re.compile(r'(?:href|src)="([^"]+)"')
for _tp in sorted(glob.glob(P("12_赛时工具", "*.html"))):
    _tbase = os.path.dirname(_tp)
    _ttext = open(_tp, encoding="utf-8").read()
    for _u in _href_re.findall(_ttext):
        if re.match(r"^(https?:|data:|#|mailto:|javascript:)", _u) or "${" in _u:
            continue
        if "'" in _u or '"' in _u or "+" in _u:
            continue
        _extra.append((_tbase, _u, f"工具页 {os.path.basename(_tp)}"))
for _s in search_docs:
    _extra.append((ROOT, _s["u"], f"搜索索引 {_s['t']}"))

validate(ROOT, SITE, _extra)

print(f"docs built: {len(built_docs)} | papers: {len(papers)} | all done")
