# -*- coding: utf-8 -*-
"""_build_tools.py — 赛时工具页构建器（由 _build_site.py 调用）

生成 12_赛时工具/ 下的交互式工具页。数据在构建期从库内 md 解析注入，
保持「md 是唯一数据源」：改了 手册/checklist/句库 重建即可同步。

  warroom.html   48 小时作战室：思路时间线 / 交互手册 / 交互终检 / 写作句库 / 思路导图 / 速查
（提示词工坊、闪卡、选题助手、实验台由后续 render_* 函数追加）
"""
import os, re, json, glob
import markdown
from urllib.parse import quote, unquote

ROOT_OF = lambda ctx: ctx["root"]
P = lambda ctx, *a: os.path.join(ctx["root"], *a)
TOOLS_DIR = "12_赛时工具"

_md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"], output_format="html5")


def md_fragment(text):
    return _md.reset().convert(text)


def doc_url(ctx, md_rel):
    """md 相对路径（posix）→ 从 12_赛时工具/ 页面出发的文档页 URL"""
    rel = md_rel[:-3] + ".html"
    return quote("../09_可视化总览/docs/" + rel)


def read(ctx, *a):
    with open(P(ctx, *a), encoding="utf-8") as f:
        return f.read()


# ---------------- 解析：提交前终检 checklist ----------------
def parse_checklist(text):
    secs, cur, notes = [], None, []
    cur_note = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            if cur is not None and not cur["items"]:
                notes.append(f"## {cur['t']}\n\n" + "\n".join(cur_note or []))
            cur = {"t": m.group(1).strip(), "items": []}
            cur_note = []
            secs.append(cur)
            continue
        m = re.match(r"^- \[ \]\s+(.+)$", line)
        if m and cur is not None:
            cur["items"].append(m.group(1).strip())
        elif cur is not None:
            cur_note.append(line)
    if cur is not None and not cur["items"]:
        notes.append(f"## {cur['t']}\n\n" + "\n".join(cur_note or []))
    checked = [s for s in secs if s["items"]]
    note_html = md_fragment("\n\n".join(notes)).strip() if notes else ""
    return checked, note_html


# ---------------- 解析：写作句库 ----------------
def parse_sentbank(text):
    secs = []
    for chunk in re.split(r"^##\s+", text, flags=re.M)[1:]:
        lines = chunk.splitlines()
        title = lines[0].strip()
        rows, notes = [], []
        in_table = False
        for ln in lines[1:]:
            s = ln.strip()
            if s.startswith("|"):
                cells = [c.strip() for c in s.strip("|").split("|")]
                if len(cells) < 2 or set(cells[0]) <= set(":- "):
                    in_table = True
                    continue
                rows.append({"t": cells[0],
                             "src": cells[1] if len(cells) >= 3 else "",
                             "scene": cells[-1]})
            else:
                in_table = False
                m = re.match(r"^(?:[-*]|\d+[.、])\s*(.+)$", s)
                if m and not s.startswith(">"):
                    notes.append(re.sub(r"^[❌✅]\s*", "", m.group(1)).strip())
                elif s.startswith(">") and len(s) > 2:
                    notes.append(s.lstrip("> ").strip())
        secs.append({"t": title, "rows": rows, "notes": notes})
    return secs


# ---------------- 公共页面骨架 ----------------
PAGE_HEAD = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__ · UPC 全档案库</title>
<meta name="description" content="__DESC__">
<meta property="og:type" content="website">
<meta property="og:site_name" content="UPC 全档案库">
<meta property="og:title" content="__TITLE__ · UPC 全档案库">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%239C3F2E'/%3E%3Ctext x='50' y='70' font-size='58' font-weight='700' text-anchor='middle' fill='%23FDFCF8' font-family='Georgia,serif'%3EU%3C/text%3E%3C/svg%3E">
__EXTRA_HEAD__
<style>
:root{
 --paper:#F7F4ED;--sheet:#FDFCF8;--ink:#2A251E;--mut:#6E6557;--dim:#786E60;
 --line:#E7E0D1;--line2:#D9D0BD;
 --acc:#9C3F2E;--acc-d:#7E3225;--acc-soft:rgba(156,63,46,.07);
 --serif:Georgia,"Times New Roman","Source Han Serif SC","Noto Serif SC","Songti SC","STSong","SimSun",serif;
 --sans:"Segoe UI","PingFang SC","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
 --mono:ui-monospace,"Cascadia Code",Consolas,monospace}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.85}
a{color:var(--acc);text-decoration:none}
a:hover{color:var(--acc-d)}
::selection{background:rgba(156,63,46,.16)}
.topbar{position:sticky;top:0;z-index:30;background:rgba(253,252,248,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.topbar .in{max-width:1060px;margin:0 auto;display:flex;align-items:center;gap:8px;padding:9px 22px}
.topbar a{color:var(--mut);text-decoration:none;font-size:12.5px;white-space:nowrap}
.topbar a:hover{color:var(--acc)}
.brand{display:flex;align-items:center;gap:9px;color:var(--ink);font-weight:600;font-size:13.5px;margin-right:4px}
.brand:hover{color:var(--ink)}
.brand .seal{width:24px;height:24px;border-radius:5px;background:var(--acc);color:#FDFCF8;display:flex;align-items:center;justify-content:center;font-family:var(--serif);font-size:13px;font-weight:700}
.crumb{color:var(--dim);font-size:12px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:right}
.clock{font-family:var(--mono);font-size:11px;line-height:1.9;letter-spacing:.02em;padding:1px 8px;
 border:1px solid rgba(156,63,46,.28);border-radius:3px;color:var(--acc);background:var(--acc-soft);
 white-space:nowrap;font-variant-numeric:tabular-nums}
.clock[data-s="live"]{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.clock[data-s="post"]{color:var(--dim);border-color:var(--line2);background:transparent}
.wrap{max-width:1060px;margin:0 auto;padding:22px 22px 80px}
h1.pt{font-family:var(--serif);font-size:25px;margin:.2em 0 .3em;font-weight:700}
p.pt-lead{color:var(--mut);font-size:13.5px;margin:0 0 18px;max-width:760px}
.tabs{position:sticky;top:51px;z-index:20;display:flex;gap:2px;overflow-x:auto;background:rgba(247,244,237,.96);
 padding:6px 0;border-bottom:1px solid var(--line);scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs a{padding:7px 15px;font-size:13.5px;color:var(--mut);border-radius:3px;white-space:nowrap;cursor:pointer}
.tabs a:hover{color:var(--ink)}
.tabs a.on{background:var(--acc);color:#FDFCF8}
.pane{display:none;padding-top:18px}
.pane.on{display:block}
.btn{display:inline-flex;align-items:center;height:32px;padding:0 14px;border:1px solid var(--line2);border-radius:3px;
 font-size:12.5px;color:var(--ink);background:var(--sheet);cursor:pointer;font-family:inherit;transition:.15s}
.btn:hover{border-color:var(--acc);color:var(--acc)}
.btn.solid{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.btn.solid:hover{background:var(--acc-d);color:#FDFCF8}
.btn.danger:hover{border-color:#B23A22;color:#B23A22}
.card{background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:16px 20px}
.notebox{border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:0 3px 3px 0;background:var(--sheet);
 padding:12px 16px;color:var(--mut);font-size:13px;line-height:1.9}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:8px 12px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:11.5px;letter-spacing:.05em;border-bottom:1px solid var(--line2);background:var(--sheet)}
tbody tr:nth-child(2n) td{background:#F8F5EC}
footer{text-align:center;color:var(--dim);font-size:12px;padding:26px 20px}
.mermaid{background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:12px;margin:1em 0;display:flex;justify-content:center}
.mermaid svg{max-width:100%;height:auto}
input[type=text],input[type=search],textarea{font-family:inherit;color:var(--ink)}
@media print{
 .topbar,.tabs,.btn,#pbar{display:none!important}
 body{background:#fff;font-size:11pt}
 .wrap{max-width:none;padding:0}
 .card{border:none;padding:0}
 .pane{display:block!important;page-break-inside:auto}
}
</style>
</head>
<body>
<div class="topbar"><div class="in">
  <a class="brand" href="__HOME__"><span class="seal">U</span>UPC 全档案库</a>
  <span class="crumb">__CRUMB__</span>
  <span class="clock" id="clock" aria-label="第 17 届 UPC 赛程"></span>
</div></div>
<div class="wrap">
<h1 class="pt">__TITLE__</h1>
<p class="pt-lead">__LEAD__</p>
__BODY__
</div>
<footer>UPC 2010–2025 全档案库 · 第 17 届 2026-11-07 09:00 – 11-09 09:00（北京时间）· 数据只存本浏览器，记得导出备份</footer>
<script>
var EV_START=__EV_START__,EV_END=__EV_END__;
function p2(n){return n<10?'0'+n:''+n;}
(function(){
  var el=document.getElementById('clock');
  function upd(){var t=Date.now();
    if(t<EV_START){var ms=EV_START-t,dd=Math.floor(ms/864e5);
      if(dd>=1){el.textContent='赛前 D-'+dd;el.dataset.s='pre';}
      else{el.textContent='赛前 '+p2(Math.floor(ms/36e5))+':'+p2(Math.floor(ms%36e5/6e4));el.dataset.s='pre';}}
    else if(t<EV_END){var u=Math.floor((t-EV_START)/1000);
      el.textContent='赛中 '+p2(Math.floor(u/3600))+':'+p2(Math.floor(u%3600/60));el.dataset.s='live';}
    else{el.textContent='第 17 届已结束';el.dataset.s='post';}}
  upd();setInterval(upd,30000);
})();
function escHtml(s){return String(s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function copyText(t,btn){
  function ok(){if(btn){var o=btn.textContent;btn.textContent='已复制 ✓';setTimeout(function(){btn.textContent=o;},1600);}}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,function(){fallback();});}
  else fallback();
  function fallback(){var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();
    try{document.execCommand('copy');ok();}catch(e){}ta.remove();}
}
function download(name,text,mime){
  var blob=new Blob([text],{type:mime||'text/plain;charset=utf-8'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(function(){URL.revokeObjectURL(a.href);},4000);
}
function phaseAt(ts){
  if(ts<EV_START)return null;
  var hr=(ts-EV_START)/36e5,cur=PHASES[0];
  for(var i=0;i<PHASES.length;i++){if(hr>=PHASES[i][0]&&hr<PHASES[i][1]){cur=PHASES[i];break;}}
  return cur;
}
function tLabel(ts){
  if(ts<EV_START)return '备赛';
  var s=Math.floor((ts-EV_START)/1000);
  return 'T+'+p2(Math.floor(s/3600))+':'+p2(Math.floor(s%3600/60));
}
__SCRIPT__
</script>
</body>
</html>"""


def page(ctx, title, crumb, desc, lead, body, script, extra_head=""):
    tpl = PAGE_HEAD
    home = "../index.html"
    return (tpl.replace("__TITLE__", title).replace("__CRUMB__", crumb)
              .replace("__DESC__", desc).replace("__LEAD__", lead)
              .replace("__BODY__", body).replace("__SCRIPT__", script)
              .replace("__HOME__", home).replace("__EXTRA_HEAD__", extra_head)
              .replace("__EV_START__", str(ctx["ev_start"]))
              .replace("__EV_END__", str(ctx["ev_end"])))


def write_out(ctx, name, html):
    d = P(ctx, TOOLS_DIR)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("  tool:", TOOLS_DIR + "/" + name, f"({len(html.encode('utf-8'))//1024} KB)")


# ================================================================
# 48 小时作战室
# ================================================================
def render_warroom(ctx):
    manual_md = read(ctx, "11_论文模板与工具", "48小时作战手册.md")
    manual_html = md_fragment(manual_md)
    # 手册里的 mermaid 甘特替换为构建期原生 SVG：mermaid 在 display:none 面板里测量出 0 宽度，运行时渲染不可靠
    gantt_tasks = parse_gantt(manual_md)
    if gantt_tasks:
        manual_html = re.sub(
            r'<pre><code class="language-mermaid">.*?</code></pre>',
            lambda _m: '<div class="mermaid">' + gantt_svg(gantt_tasks) + "</div>",
            manual_html, count=1, flags=re.S)
    ck_secs, ck_note = parse_checklist(read(ctx, "11_论文模板与工具", "提交前终检checklist.md"))
    sent = parse_sentbank(read(ctx, "11_论文模板与工具", "写作句库.md"))
    polish = parse_polish(read(ctx, "11_论文模板与工具", "中译英润色库.md"))

    links = {
        "decision_tree": doc_url(ctx, "11_论文模板与工具/建模决策树.md"),
        "manual": doc_url(ctx, "11_论文模板与工具/48小时作战手册.md"),
        "sentbank": doc_url(ctx, "11_论文模板与工具/写作句库.md"),
        "polish": doc_url(ctx, "11_论文模板与工具/中译英润色库.md"),
        "rules": doc_url(ctx, "02_题目汇总/比赛规则_ContestRules.md"),
        "recipes": quote("../11_论文模板与工具/图表配方库/matplotlib_recipes.py"),
        "method": doc_url(ctx, "08_物理模型综述/08_方法论与数值算法总论.md"),
        "home_years": "../index.html#years",
        "home_models": "../index.html#models",
        "home_templates": "../index.html#templates",
        "home_papers": "../index.html#papers",
    }
    # T0–T9 每阶段该看的库内入口（速查标签页；11 行与 PHASES 一一对应，含 T3·T4 收口行）
    phase_links = [
        ["home_years|年鉴对照历年两题风格", "decision_tree|建模决策树从 Q1 走"],
        ["decision_tree|去模糊化 Q5", "sentbank|句库·模糊词操作化"],
        ["decision_tree|Q2 基准情形", "sentbank|句库·基准与动机"],
        ["home_models|物理模型地图查套路", "sentbank|句库·建模与假设"],
        ["decision_tree|主方程收口检查（第 14 小时）", "method|积分器与步长速查"],
        ["method|方法论与数值算法总论", "recipes|图表配方库源码"],
        ["decision_tree|Q3 量级表", "method|数值算法速查"],
        ["sentbank|句库·数值方法（收敛声明）", "manual|手册 T6 验证三件套"],
        ["recipes|8 类配方对照补图", "decision_tree|验证先于美化"],
        ["sentbank|句库按部位检索", "polish|中译英五步法逐段过"],
        ["manual|危机预案", "rules|提交合规细则（官方规则）"],
    ]

    body = r"""
<nav class="tabs" id="tabs">
  <a data-t="log" class="on">思路时间线</a>
  <a data-t="manual">作战手册</a>
  <a data-t="check">提交终检</a>
  <a data-t="sent">写作句库</a>
  <a data-t="polish">中译英</a>
  <a data-t="map">思路导图</a>
  <a data-t="speed">阶段速查</a>
</nav>

<section class="pane on" id="pane-log">
  <div class="card" id="logclock" style="margin-bottom:14px"></div>
  <div class="card">
    <textarea id="note" rows="3" style="width:100%;border:1px solid var(--line2);border-radius:3px;background:var(--paper);
      padding:10px 12px;font-size:14px;outline:none;resize:vertical" placeholder="随手记：判据、假设、算出的数、分工变化、踩的坑…（Ctrl+Enter 快速记一条）"></textarea>
    <div style="display:flex;gap:8px;margin-top:10px;align-items:center;flex-wrap:wrap">
      <button class="btn solid" id="add" type="button">记一条（自动盖时间戳与阶段）</button>
      <button class="btn" id="logexp" type="button">导出决策日志 .md</button>
      <button class="btn" id="logjson" type="button">导出 JSON</button>
      <button class="btn" id="logimp" type="button">导入 JSON</button>
      <input type="file" id="logfile" accept=".json,application/json" hidden>
      <button class="btn danger" id="logclr" type="button">清空</button>
      <span class="note" id="logcnt" style="color:var(--dim);font-size:12px"></span>
    </div>
  </div>
  <div id="loglist" style="margin-top:14px"></div>
</section>

<section class="pane" id="pane-manual">__MANUAL__</section>

<section class="pane" id="pane-check">
  <div class="card" style="margin-bottom:14px">
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
      <div><b style="font-family:var(--serif);font-size:26px;color:var(--acc)" id="ckpct">0%</b>
      <span style="font-size:12px;color:var(--dim)">总完成度</span></div>
      <div style="flex:1;min-width:220px;height:8px;background:#EFEADC;border-radius:4px;overflow:hidden">
        <i id="ckbar" style="display:block;height:100%;width:0;background:var(--acc);transition:width .3s"></i></div>
      <button class="btn" id="ckreset" type="button">重置勾选</button>
    </div>
  </div>
  <div id="cklist"></div>
  <div class="notebox" style="margin-top:16px">__CKNOTE__</div>
</section>

<section class="pane" id="pane-sent">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px">
    <input id="sq" type="search" placeholder="搜句式 / 场景 / 出处…（如 trade-off、收敛、20%）"
      style="flex:1;min-width:240px;height:34px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);padding:0 12px;font-size:13px;outline:none">
    <span class="note" id="scnt" style="color:var(--dim);font-size:12px"></span>
  </div>
  <div id="slist"></div>
</section>

<section class="pane" id="pane-polish">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px">
    <input id="pq" type="search" placeholder="搜中文直译腔 / 英文表达 / 说明…（如 显著、忽略、prove）"
      style="flex:1;min-width:240px;height:34px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);padding:0 12px;font-size:13px;outline:none">
    <span class="note" id="pcnt" style="color:var(--dim);font-size:12px"></span>
    <a class="btn" href="__LINKS_POLISH__" target="_blank" style="height:34px">文档版 →</a>
  </div>
  <div id="plist2"></div>
</section>

<section class="pane" id="pane-map">
  <div class="card">
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">
      <button class="btn solid" id="mapdraw" type="button">重新渲染</button>
      <button class="btn" id="mapsvg" type="button">导出 SVG</button>
      <button class="btn" id="mappng" type="button">导出 PNG（进论文/笔记）</button>
      <span class="note" style="color:var(--dim);font-size:12px;align-self:center">缩进即层级（每 2 空格一层）</span>
    </div>
    <textarea id="mapsrc" rows="9" style="width:100%;border:1px solid var(--line2);border-radius:3px;background:var(--paper);
      padding:10px 12px;font-size:13.5px;font-family:var(--mono);outline:none;resize:vertical"></textarea>
  </div>
  <div class="card" style="margin-top:14px;overflow:auto"><div id="mapbox"></div></div>
</section>

<section class="pane" id="pane-speed">
  <div id="speedlist"></div>
</section>
"""

    script = r"""
var PHASES=__PHASES__;
var CK=__CHECKLIST__;
var SENT=__SENTBANK__;
var LINKS=__LINKS__;
var PLINKS=__PLINKS__;
var WKEY='upcWarroom.v1', CKKEY='upcWarroom.check.v1';
function wLoad(){try{return JSON.parse(localStorage.getItem(WKEY)||'{}')}catch(e){return{}}}
function wSave(s){try{localStorage.setItem(WKEY,JSON.stringify(s))}catch(e){}}
function cLoad(){try{return JSON.parse(localStorage.getItem(CKKEY)||'{}')}catch(e){return{}}}
function cSave(s){try{localStorage.setItem(CKKEY,JSON.stringify(s))}catch(e){}}

/* ---------- 标签页 ---------- */
var tabs=document.getElementById('tabs');
tabs.addEventListener('click',function(ev){
  var a=ev.target.closest('a');if(!a)return;
  document.querySelectorAll('#tabs a').forEach(function(x){x.classList.remove('on')});
  a.classList.add('on');
  document.querySelectorAll('.pane').forEach(function(p){p.classList.remove('on')});
  document.getElementById('pane-'+a.dataset.t).classList.add('on');
  if(a.dataset.t==='map')drawMap();
});

/* ---------- 思路时间线 ---------- */
var note=document.getElementById('note');
note.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();addNote();}});
document.getElementById('add').addEventListener('click',addNote);
function addNote(){
  var t=note.value.trim();if(!t)return;
  var s=wLoad();(s.notes=s.notes||[]).push({ts:Date.now(),text:t});
  wSave(s);note.value='';renderLog();
}
function fmtNote(t){
  return escHtml(t).replace(/\n/g,'<br>');
}
function renderLog(){
  var s=wLoad(),notes=(s.notes||[]).slice().sort(function(a,b){return a.ts-b.ts});
  document.getElementById('logcnt').textContent=notes.length+' 条记录';
  var box=document.getElementById('loglist');
  if(!notes.length){box.innerHTML='<div class="notebox">开赛后随手记：每条自动盖上官方时钟的时间戳与阶段号（T0–T9），导出后就是现成的「决策日志」素材。</div>';return;}
  var html='';
  notes.forEach(function(n,i){
    var ph=phaseAt(n.ts);
    var tag=ph?ph[2]+' · '+ph[3]:'赛前准备';
    html+='<div class="card" style="margin-bottom:8px;padding:11px 16px">'+
      '<div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">'+
      '<b style="font-family:var(--mono);font-size:12px;color:var(--acc)">'+tLabel(n.ts)+'</b>'+
      '<span style="font-size:11.5px;color:var(--dim)">'+escHtml(tag)+'</span>'+
      '<span style="margin-left:auto;font-size:11px;color:var(--dim);font-family:var(--mono)">'+new Date(n.ts).toLocaleString()+'</span>'+
      '<button class="btn" data-del="'+n.ts+'" type="button" style="height:22px;padding:0 8px;font-size:11px">删</button></div>'+
      '<div style="margin-top:5px;font-size:13.5px">'+fmtNote(n.text)+'</div></div>';
  });
  box.innerHTML=html;
}
document.getElementById('loglist').addEventListener('click',function(ev){
  var b=ev.target.closest('button[data-del]');if(!b)return;
  var ts=+b.dataset.del,s=wLoad();
  s.notes=(s.notes||[]).filter(function(n){return n.ts!==ts});
  wSave(s);renderLog();
});
document.getElementById('logexp').addEventListener('click',function(){
  var s=wLoad(),notes=(s.notes||[]).slice().sort(function(a,b){return a.ts-b.ts});
  if(!notes.length)return;
  var md='# 第 17 届 UPC 决策日志\n\n> 由 UPC 全档案库「48 小时作战室」导出于 '+new Date().toLocaleString()+'\n';
  var cur=null;
  notes.forEach(function(n){
    var ph=phaseAt(n.ts);
    var tag=ph?('T+'+p2(Math.floor((n.ts-EV_START)/36e5))+'h · '+ph[2]+' '+ph[3]):'赛前';
    if(ph&&(!cur||cur[2]!==ph[2])){md+='\n## '+ph[2]+' '+ph[3]+'（第 '+ph[0]+'–'+ph[1]+' 小时）\n';cur=ph;}
    else if(!ph&&cur!==null){md+='\n## 赛前准备\n';cur=null;}
    md+='\n- **'+tLabel(n.ts)+'** '+n.text.replace(/\n/g,'\n  ');
  });
  md+='\n';
  download('upc-决策日志-'+new Date().toISOString().slice(0,10)+'.md',md);
});
document.getElementById('logjson').addEventListener('click',function(){
  download('upc-作战室-'+new Date().toISOString().slice(0,10)+'.json',JSON.stringify(wLoad(),null,1),'application/json');
});
document.getElementById('logimp').addEventListener('click',function(){document.getElementById('logfile').click()});
document.getElementById('logfile').addEventListener('change',function(ev){
  var f=ev.target.files[0];if(!f)return;
  var r=new FileReader();
  r.onload=function(){
    try{
      var inc=JSON.parse(r.result),s=wLoad();
      s.notes=(s.notes||[]).concat(inc.notes||[]);
      var seen={},out=[];
      s.notes.sort(function(a,b){return a.ts-b.ts}).forEach(function(n){
        var k=n.ts+'|'+n.text;if(!seen[k]){seen[k]=1;out.push(n);}});
      s.notes=out;wSave(s);renderLog();ev.target.value='';
    }catch(e){alert('导入失败：不是有效的作战室 JSON');}
  };
  r.readAsText(f);
});
document.getElementById('logclr').addEventListener('click',function(){
  if(!confirm('确定清空全部思路记录？建议先导出备份。'))return;
  var s=wLoad();s.notes=[];wSave(s);renderLog();
});

/* 赛时顶栏大钟 */
function tickLog(){
  var t=Date.now(),el=document.getElementById('logclock');
  if(t<EV_START){
    var ms=EV_START-t;
    el.innerHTML='<b style="font-family:var(--serif);font-size:20px">开赛倒计时 '+Math.floor(ms/864e5)+' 天 '+
      p2(Math.floor(ms%864e5/36e5))+':'+p2(Math.floor(ms%36e5/6e4))+':'+p2(Math.floor(ms%6e4/1e3))+'</b>'+
      '<span style="color:var(--dim);font-size:12.5px">　—　现在记的每一条都会标记为「备赛」，开赛后自动切换为官方阶段标记。</span>';
  }else if(t<EV_END){
    var used=t-EV_START,left=EV_END-t;
    var hr=used/36e5,cur=PHASES[0],nx=null;
    for(var i=0;i<PHASES.length;i++){if(hr>=PHASES[i][0]&&hr<PHASES[i][1]){cur=PHASES[i];break;}}
    for(var j=0;j<PHASES.length;j++){if(PHASES[j][0]>hr){nx=PHASES[j];break;}}
    function hms(ms){var s=Math.max(0,Math.floor(ms/1000));return p2(Math.floor(s/3600))+':'+p2(Math.floor(s%3600/60))+':'+p2(s%60);}
    el.innerHTML='<b style="font-family:var(--mono);font-size:20px">已用 '+hms(used)+'</b>'+
      '　<b style="font-family:var(--mono);font-size:20px;color:var(--acc)">剩余 '+hms(left)+'</b>'+
      '　<span style="font-size:13px">当前 <b style="font-family:var(--serif);font-size:15px">'+cur[2]+' '+cur[3]+'</b>'+
      '（第 '+cur[0]+'–'+cur[1]+' 小时）</span>'+
      (nx?'<span style="color:var(--dim);font-size:12px">　下一阶段：'+nx[2]+' '+nx[3]+'</span>':'');
  }else{
    el.innerHTML='<b style="font-family:var(--serif);font-size:18px">第 17 届已结束</b>'+
      '<span style="color:var(--dim);font-size:12.5px">　导出决策日志，对照历届同域金牌论文复盘。</span>';
  }
}
tickLog();setInterval(tickLog,1000);

/* ---------- 提交终检 ---------- */
function ckKey(si,ii){return 'c'+si+'_'+ii;}
function renderCk(){
  var st=cLoad(),total=0,done=0,html='';
  CK.forEach(function(sec,si){
    var boxes=sec.items.map(function(it,ii){
      total++;
      var k=ckKey(si,ii),on=!!st[k];
      if(on)done++;
      return '<label style="display:flex;gap:9px;align-items:flex-start;padding:6px 0;border-bottom:1px solid var(--line);cursor:pointer;font-size:13.5px;line-height:1.8">'+
        '<input type="checkbox" data-ck="'+k+'" '+(on?'checked':'')+' style="margin-top:7px;accent-color:#9C3F2E;flex-shrink:0">'+
        '<span'+(on?' style="color:var(--dim)"':'')+'>'+escHtml(it)+'</span></label>';
    }).join('');
    var dcnt=sec.items.filter(function(_,ii){return st[ckKey(si,ii)]}).length;
    html+='<div class="card" style="margin-bottom:12px"><div style="display:flex;align-items:baseline;gap:10px">'+
      '<b style="font-family:var(--serif);font-size:15.5px">'+escHtml(sec.t)+'</b>'+
      '<span style="font-size:12px;color:'+(dcnt===sec.items.length?'var(--acc)':'var(--dim)')+';margin-left:auto;font-variant-numeric:tabular-nums">'+dcnt+' / '+sec.items.length+'</span></div>'+boxes+'</div>';
  });
  document.getElementById('cklist').innerHTML=html;
  var pct=total?Math.round(done/total*100):0;
  document.getElementById('ckpct').textContent=pct+'%';
  document.getElementById('ckbar').style.width=pct+'%';
}
document.getElementById('cklist').addEventListener('change',function(ev){
  var c=ev.target.closest('input[data-ck]');if(!c)return;
  var st=cLoad();st[c.dataset.ck]=c.checked;cSave(st);renderCk();
});
document.getElementById('ckreset').addEventListener('click',function(){
  if(!confirm('重置全部勾选？'))return;
  try{localStorage.removeItem(CKKEY)}catch(e){}
  renderCk();
});
renderCk();

/* ---------- 写作句库 ---------- */
function renderSent(){
  var kw=document.getElementById('sq').value.trim().toLowerCase();
  var n=0,html='';
  SENT.forEach(function(sec){
    var rows=sec.rows.filter(function(r){
      if(!kw)return true;
      return (r.t+' '+r.src+' '+r.scene).toLowerCase().indexOf(kw)>=0;});
    var notes=sec.notes.filter(function(x){return !kw||x.toLowerCase().indexOf(kw)>=0;});
    if(kw&&!rows.length&&!notes.length)return;
    n+=rows.length+notes.length;
    html+='<div class="card" style="margin-bottom:12px"><b style="font-family:var(--serif);font-size:15.5px">'+escHtml(sec.t)+'</b>';
    if(rows.length){
      html+='<table style="margin-top:8px"><thead><tr><th style="width:52%">句式</th>'+(sec.rows[0].src?'<th style="width:14%">出处</th>':'')+'<th>场景</th></tr></thead><tbody>'+
        rows.map(function(r){
          return '<tr><td><span style="font-family:var(--mono);font-size:12.5px">'+escHtml(r.t)+'</span> '+
            '<button class="btn" data-cp="'+escHtml(r.t).replace(/"/g,'&quot;')+'" type="button" style="height:20px;padding:0 7px;font-size:10.5px;margin-left:6px">复制</button></td>'+
            (r.src?'<td style="font-family:var(--mono);font-size:11.5px;color:var(--dim)">'+escHtml(r.src)+'</td>':'')+
            '<td style="font-size:12.5px;color:var(--mut)">'+escHtml(r.scene)+'</td></tr>';}).join('')+'</tbody></table>';
    }
    if(notes.length){
      html+='<ul style="margin:8px 0 2px;padding-left:1.4em;font-size:13px;line-height:1.9">'+
        notes.map(function(x){return '<li>'+escHtml(x)+'</li>';}).join('')+'</ul>';
    }
    html+='</div>';
  });
  document.getElementById('slist').innerHTML=html||'<div class="notebox">句库里没有匹配「'+escHtml(kw)+'」的句式</div>';
  document.getElementById('scnt').textContent=n+' 条';
}
document.getElementById('sq').addEventListener('input',renderSent);
document.getElementById('slist').addEventListener('click',function(ev){
  var b=ev.target.closest('button[data-cp]');if(!b)return;
  var tmp=document.createElement('textarea');tmp.innerHTML=b.dataset.cp;copyText(tmp.value,b);
});
renderSent();

/* ---------- 中译英润色库 ---------- */
var POLISH=__POLISH__;
function renderPolish(){
  var kw=document.getElementById('pq').value.trim().toLowerCase();
  var n=0,html='';
  POLISH.forEach(function(sec){
    function hit(s){return !kw||String(s).toLowerCase().indexOf(kw)>=0;}
    var blocks=sec.blocks.map(function(b){
      if(b.kind==='table'){
        var rows=b.rows.filter(function(r){return r.some(hit);});
        if(kw&&!rows.length)return '';
        n+=rows.length;
        return '<table style="margin:8px 0 2px"><thead><tr>'+b.header.map(function(h){return '<th>'+escHtml(h)+'</th>';}).join('')+'</tr></thead><tbody>'+
          rows.map(function(r){return '<tr>'+r.map(function(c,i){
            var cls=i===1?'font-family:var(--mono);font-size:12px':'';
            return '<td style="'+cls+'">'+escHtml(c)+'</td>';}).join('')+'</tr>';}).join('')+'</tbody></table>';
      }
      if(b.kind==='notes'){
        var items=b.items.filter(hit);
        if(kw&&!items.length)return '';
        n+=items.length;
        return '<ul style="margin:8px 0 2px;padding-left:1.4em;font-size:13px;line-height:1.9">'+
          items.map(function(x){return '<li>'+escHtml(x)+'</li>';}).join('')+'</ul>';
      }
      if(!hit(b.text))return '';
      n++;
      return '<p style="margin:6px 0;font-size:13px;color:var(--mut)">'+escHtml(b.text)+'</p>';
    }).join('');
    if(kw&&!blocks)return;
    html+='<div class="card" style="margin-bottom:12px"><b style="font-family:var(--serif);font-size:15.5px">'+escHtml(sec.t)+'</b>'+
      (sec.usage?'<p style="margin:4px 0 2px;font-size:12.5px;color:var(--dim)">'+escHtml(sec.usage)+'</p>':'')+blocks+'</div>';
  });
  document.getElementById('plist2').innerHTML=html||'<div class="notebox">润色库里没有匹配「'+escHtml(kw)+'」的条目</div>';
  document.getElementById('pcnt').textContent=n+' 条';
}
document.getElementById('pq').addEventListener('input',renderPolish);
renderPolish();

/* ---------- 思路导图（无依赖径向 SVG） ---------- */
var MAP_DEFAULT=[
 '# 第 17 届建模作战图（示例骨架）',
 '题目：____（题号）',
 ' 判据：significant → 20%？safely → 概率 < x？',
 ' 基准（Level 0）：真空/无阻力的解析解',
 ' 主模型（Level 1）',
 '  守恒律 → 主方程',
 '  关键假设 × 量级自辩',
 ' 数值（Level 2）',
 '  RK45 + 步长控制',
 '  先跑通一条轨迹',
 ' 验证三件套',
 '  收敛：步长减半',
 '  极限：退化到基准',
 '  灵敏度：±20% 扫描',
 ' 交付：结论进摘要与图题',
].join('\n');
var mapsrc=document.getElementById('mapsrc');
mapsrc.value=localStorage.getItem('upcWarroom.map')||MAP_DEFAULT;
mapsrc.addEventListener('input',function(){
  localStorage.setItem('upcWarroom.map',mapsrc.value);
  clearTimeout(window.__mapT);window.__mapT=setTimeout(drawMap,600);
});
document.getElementById('mapdraw').addEventListener('click',drawMap);

function parseOutline(text){
  var root={t:'',ch:[]},stack=[{lv:-1,node:root}];
  text.split('\n').forEach(function(ln){
    if(!ln.trim()||/^#{1,6}\s*$/.test(ln.trim()))return;
    var t=ln.replace(/^#+\s*/,'').trim();
    if(!t)return;
    var ind=ln.match(/^\s*/)[0].replace(/\t/g,'  ').length;
    var lv=Math.floor(ind/2);
    var node={t:t,ch:[]};
    while(stack.length>1&&stack[stack.length-1].lv>=lv)stack.pop();
    stack[stack.length-1].node.ch.push(node);
    stack.push({lv:lv,node:node});
  });
  return root;
}
function leaves(n){return n.ch.length?n.ch.reduce(function(s,c){return s+leaves(c)},0):1;}
var MAP_COLORS=['#9C3F2E','#3A5A8C','#2F7D6B','#9A6232','#647C35','#6E5599','#A84A76','#7A7161'];
function drawMap(){
  var box=document.getElementById('mapbox');
  var root=parseOutline(mapsrc.value);
  if(!root.ch.length){box.innerHTML='<p style="color:var(--dim);font-size:13px">输入大纲后点「重新渲染」</p>';return;}
  var W=980,H=620,cx=W/2,cy=H/2+8;
  var l1=root.ch,L1=l1.length;
  var totalLeaves=leaves(root);
  var R1=Math.min(225,155+L1*6);
  var svg=['<svg id="mapsvg-el" viewBox="0 0 '+W+' '+H+'" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;min-width:640px">'];
  function tw(t){var w=0;for(var i=0;i<t.length;i++)w+=t.charCodeAt(i)>255?1:0.55;return w;}
  function nodeW(t,fs){return tw(t)*fs+20;}
  function nodeBox(x,y,t,col,fs,bold){
    var w=nodeW(t,fs),h=fs+13;
    return '<rect x="'+(x-w/2)+'" y="'+(y-h/2)+'" width="'+w+'" height="'+h+'" rx="4" fill="'+col+'" fill-opacity="'+(bold?0.92:0.1)+'" stroke="'+col+'" stroke-width="1.2"/>'+
      '<text x="'+x+'" y="'+(y+fs*0.36)+'" font-size="'+fs+'" font-weight="'+(bold?'600':'400')+'" text-anchor="middle" fill="'+(bold?'#FDFCF8':col)+'" font-family="Segoe UI,PingFang SC,sans-serif">'+escHtml(t)+'</text>';
  }
  // 一级角位：按叶数比例分配，再做最小角间距松弛（防同级框重叠）
  var per=2*Math.PI/totalLeaves,acc=-Math.PI/2;
  var spans=l1.map(function(c){return per*leaves(c);});
  var angs=spans.map(function(s){acc+=s;return acc-s/2;});
  for(var it=0;it<80;it++){
    for(var i=0;i<L1;i++){
      var j=(i+1)%L1;if(L1<2)break;
      var need=(nodeW(l1[i].t,13.5)+nodeW(l1[j].t,13.5))/2/R1+0.10;
      var d=angs[j]-angs[i];if(j===0)d+=2*Math.PI;
      if(d<need){var push=(need-d)/2;angs[i]-=push;angs[j]+=push;}
    }
  }
  // 先算坐标（root + 各级节点），再做笛卡尔成对推开（root 固定），最后统一画线
  var nodes=[];   // {t,fs,bold,col,x,y,ring,ringR,parent}
  var rootW=nodeW(root.t,17);
  nodes.push({t:root.t,fs:17,bold:true,col:'#9C3F2E',x:cx,y:cy,w:rootW,ring:0,parent:-1});
  var per=2*Math.PI/totalLeaves,acc=-Math.PI/2;
  var spans=l1.map(function(c){return per*leaves(c);});
  var angs=spans.map(function(s){acc+=s;return acc-s/2;});
  l1.forEach(function(c,i){
    var col=MAP_COLORS[i%MAP_COLORS.length];
    nodes.push({t:c.t,fs:13.5,bold:true,col:col,x:cx+R1*Math.cos(angs[i]),y:cy+R1*Math.sin(angs[i])*0.8,ring:1,ringR:R1,parent:0});
  });
  l1.forEach(function(c,i){
    var col=MAP_COLORS[i%MAP_COLORS.length];
    var pi=i+1, half=spans[i]/2, cc=angs[i]-half, lf=leaves(c);
    c.ch.forEach(function(g,gi){
      var spg=2*half*leaves(g)/lf;
      var ang=cc+spg/2, r=R1+95+(gi%2)*48;
      nodes.push({t:g.t,fs:12,bold:false,col:col,x:cx+r*Math.cos(ang),y:cy+r*Math.sin(ang)*0.8,ring:2,ringR:r,parent:pi});
      cc+=spg;
      g.ch&&g.ch.forEach(function(h2,hi){});   // 3 层以上暂按同级并排
    });
  });
  nodes.forEach(function(n){n.h=n.fs+13;if(n.w===undefined)n.w=nodeW(n.t,n.fs);});
  for(var it=0;it<50;it++){
    for(var i=0;i<nodes.length;i++)for(var j=i+1;j<nodes.length;j++){
      var a=nodes[i],b=nodes[j];
      if(a.ring===0||b.ring===0)continue;
      var ox=Math.min(a.x+a.w/2,b.x+b.w/2)-Math.max(a.x-a.w/2,b.x-b.w/2);
      var oy=Math.min(a.y+a.h/2,b.y+b.h/2)-Math.max(a.y-a.h/2,b.y-b.h/2);
      if(ox>4&&oy>4){
        var dx=(b.x-a.x)||0.01,dy=(b.y-a.y)||0.01,len=Math.sqrt(dx*dx+dy*dy);
        var push=Math.min(ox,oy)/2+1;
        a.x-=dx/len*push;a.y-=dy/len*push;
        b.x+=dx/len*push;b.y+=dy/len*push;
      }
    }
    nodes.forEach(function(n){
      if(!n.ring)return;
      // 轻微拉回轨道，保持环形观感
      var dx=n.x-cx,dy=(n.y-cy)/0.8,len=Math.sqrt(dx*dx+dy*dy)||1;
      var r2=n.ringR+(len-n.ringR)*0.85;
      n.x=cx+dx/len*r2;n.y=cy+dy/len*r2*0.8;
    });
  }
  nodes.forEach(function(n,i){
    if(n.ring===0)return;
    var p=nodes[n.parent];
    svg.push('<line x1="'+p.x+'" y1="'+p.y+'" x2="'+n.x+'" y2="'+n.y+'" stroke="'+n.col+'" stroke-width="'+(n.ring===1?1.6:1.1)+'" opacity="'+(n.ring===1?0.5:0.35)+'"/>');
  });
  nodes.forEach(function(n){
    svg.push('<rect x="'+(n.x-n.w/2)+'" y="'+(n.y-n.h/2)+'" width="'+n.w+'" height="'+n.h+'" rx="4" fill="'+n.col+'" fill-opacity="'+(n.bold?0.92:0.1)+'" stroke="'+n.col+'" stroke-width="1.2"/>'+
      '<text x="'+n.x+'" y="'+(n.y+n.fs*0.36)+'" font-size="'+n.fs+'" font-weight="'+(n.bold?'600':'400')+'" text-anchor="middle" fill="'+(n.bold?'#FDFCF8':n.col)+'" font-family="Segoe UI,PingFang SC,sans-serif">'+escHtml(n.t)+'</text>');
  });
  svg.push('</svg>');
  box.innerHTML=svg.join('');
}
drawMap();
document.getElementById('mapsvg').addEventListener('click',function(){
  var el=document.getElementById('mapsvg-el');if(!el)return;
  download('upc-思路导图.svg','<?xml version="1.0"?>\n'+new XMLSerializer().serializeToString(el),'image/svg+xml');
});
document.getElementById('mappng').addEventListener('click',function(){
  var el=document.getElementById('mapsvg-el');if(!el)return;
  var svgStr=new XMLSerializer().serializeToString(el);
  var img=new Image();
  img.onload=function(){
    var sc=2,cv=document.createElement('canvas');
    cv.width=980*sc;cv.height=620*sc;
    var c=cv.getContext('2d');c.fillStyle='#FDFCF8';c.fillRect(0,0,cv.width,cv.height);
    c.drawImage(img,0,0,cv.width,cv.height);
    cv.toBlob(function(b){
      var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='upc-思路导图.png';
      document.body.appendChild(a);a.click();a.remove();
    });
  };
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svgStr);
});

/* ---------- 阶段速查 ---------- */
function renderSpeed(){
  var t=Date.now(),hr=(t-EV_START)/36e5,curIdx=-1;
  if(t>=EV_START&&t<EV_END){
    for(var i=0;i<PHASES.length;i++){if(hr>=PHASES[i][0]&&hr<PHASES[i][1]){curIdx=i;break;}}
  }
  var html='<div class="notebox" style="margin-bottom:14px">每个阶段：先看「本阶段任务」，再顺手打开「库内入口」。'+
    '完整任务单在 <a href="'+LINKS.manual+'" target="_blank">48 小时作战手册</a>；选题走 <a href="'+LINKS.decision_tree+'" target="_blank">建模决策树</a>。</div>';
  PHASES.forEach(function(ph,i){
    var now=i===curIdx;
    var links=PLINKS[i].map(function(x){
      var kv=x.split('|');return '<a class="btn" style="height:26px;padding:0 10px;font-size:12px" href="'+LINKS[kv[0]]+'" target="_blank">'+kv[1]+' →</a>';
    }).join(' ');
    html+='<div class="card" style="margin-bottom:10px;'+(now?'border-color:var(--acc);border-width:1.5px':'')+'">'+
      '<div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">'+
      (now?'<span style="font-size:10.5px;letter-spacing:.14em;background:var(--acc);color:#FDFCF8;padding:2px 9px;border-radius:2px;font-weight:600">当前阶段</span>':'')+
      '<b style="font-family:var(--mono);font-size:13px;color:var(--acc)">'+ph[2]+'</b>'+
      '<b style="font-family:var(--serif);font-size:15.5px">'+escHtml(ph[3])+'</b>'+
      '<span style="font-size:12px;color:var(--dim)">第 '+ph[0]+'–'+ph[1]+' 小时</span></div>'+
      '<p style="margin:6px 0 10px;font-size:13px;color:var(--mut)">'+escHtml(ph[4])+'</p>'+
      '<div style="display:flex;gap:8px;flex-wrap:wrap">'+links+'</div></div>';
  });
  document.getElementById('speedlist').innerHTML=html;
}
renderSpeed();

renderLog();
"""

    return page(ctx, "48 小时作战室", "实战工具 · 平时开放",
                "UPC 48 小时作战室：思路时间线、交互式作战手册、提交终检清单、写作句库检索、中译英润色、思路导图与阶段速查。",
                "备赛、赛时都可用：句库/中译英/导图/终检现在就能练；开赛后把这一页钉在屏幕上，随手记思路（自动盖阶段戳）、对照手册推进。所有数据只存在本浏览器，可导出备份。",
                body.replace("__MANUAL__", manual_html).replace("__CKNOTE__", ck_note)
                    .replace("__LINKS_POLISH__", links["polish"]),
                script
                .replace("__PHASES__", json.dumps(ctx["phases"], ensure_ascii=False))
                .replace("__CHECKLIST__", json.dumps(ck_secs, ensure_ascii=False))
                .replace("__SENTBANK__", json.dumps(sent, ensure_ascii=False))
                .replace("__POLISH__", json.dumps(polish, ensure_ascii=False))
                .replace("__LINKS__", json.dumps(links, ensure_ascii=False))
                .replace("__PLINKS__", json.dumps(phase_links, ensure_ascii=False)),
                extra_head="")


# ---------------- 解析：48h 手册甘特 → 构建期原生 SVG ----------------
GANTT_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.S)
GANTT_TASK_RE = re.compile(r"^(.+?)\s*:\s*([0-9.]+)\s*,\s*([0-9.]+)\s*$")


def parse_gantt(md_text):
    m = GANTT_BLOCK_RE.search(md_text)
    if not m or "gantt" not in m.group(1):
        return None
    tasks, section = [], "分组"
    for ln in m.group(1).splitlines():
        s = ln.strip()
        if s.startswith("section "):
            section = s[8:].strip()
            continue
        mt = GANTT_TASK_RE.match(s)
        if mt:
            tasks.append((section, mt.group(1).strip(), float(mt.group(2)), float(mt.group(3))))
    return tasks or None


def gantt_svg(tasks):
    """48h 甘特的原生 SVG：左侧任务名 + 0–48h 时间轴，四段配色，悬停显示区间"""
    W, LX, barH, gap = 960, 178, 24, 11
    CW = W - LX - 34
    H = 46 + len(tasks) * (barH + gap) + 8
    colors = {"开局": "#3A5A8C", "建模": "#9C3F2E", "深化": "#2F7D6B", "收官": "#9A6232"}
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">']
    for hh in range(0, 49, 6):
        x = LX + hh / 48 * CW
        out.append(f'<line x1="{x:.1f}" y1="30" x2="{x:.1f}" y2="{H-16}" stroke="#E7E0D1" stroke-width="1"/>')
        out.append(f'<text x="{x:.1f}" y="20" font-size="11" fill="#786E60" text-anchor="middle">{hh}h</text>')
    y = 40
    for sec, name, a, b in tasks:
        col = colors.get(sec, "#7A7161")
        x = LX + a / 48 * CW
        w = max((b - a) / 48 * CW, 4)
        out.append(f'<text x="{LX-10}" y="{y + barH * 0.72:.1f}" font-size="12.5" fill="#2A251E" text-anchor="end">{name}</text>')
        out.append(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{barH}" rx="3" fill="{col}" fill-opacity="0.85">'
                   f'<title>{sec} · 第 {a:g}–{b:g} 小时：{name}</title></rect>')
        if w > 48:
            out.append(f'<text x="{x + w / 2:.1f}" y="{y + barH * 0.68:.1f}" font-size="10.5" fill="#FDFCF8" text-anchor="middle">{a:g}–{b:g}h</text>')
        y += barH + gap
    out.append("</svg>")
    return "".join(out)


# ---------------- 解析：中译英润色库（带表头的表格） ----------------
def parse_polish(text):
    """返回 [{t, usage, blocks:[{kind:'table',header,rows}|{kind:'notes',items}|{kind:'prose',text}]}]"""
    clean = lambda s: s.replace("**", "")
    secs = []
    for chunk in re.split(r"^##\s+", text, flags=re.M)[1:]:
        lines = chunk.splitlines()
        title = clean(lines[0].strip())
        usage = ""
        m = re.search(r"^>\s*(.+)$", chunk, re.M)
        if m:
            usage = clean(m.group(1).strip())
        blocks, cur_table, cur_notes = [], None, []
        table_header = None
        def flush():
            nonlocal cur_table, cur_notes, table_header
            if cur_table:
                blocks.append({"kind": "table", "header": table_header, "rows": cur_table})
                cur_table, table_header = None, None
            if cur_notes:
                blocks.append({"kind": "notes", "items": cur_notes})
                cur_notes = []
        for ln in lines[1:]:
            s = ln.strip()
            if s.startswith(">"):
                continue
            if s.startswith("|"):
                cells = [clean(c.strip()) for c in s.strip("|").split("|")]
                if set(cells[0]) <= set(":- ") or not any(cells):
                    continue
                if cur_table is None and not table_header:
                    table_header = cells   # md 表头行
                    cur_table = []
                else:
                    cur_table.append(cells)
            else:
                if cur_table is not None or table_header is not None:
                    flush()
                m2 = re.match(r"^(?:[-*]|\d+[.、])\s*(.+)$", s)
                if m2:
                    cur_notes.append(clean(re.sub(r"^[❌✅]\s*", "", m2.group(1)).strip()))
                elif s:
                    blocks.append({"kind": "prose", "text": clean(s)})
        flush()
        secs.append({"t": title, "usage": usage, "blocks": blocks})
    return secs


# ================================================================
# AI 提示词工坊
# ================================================================
def parse_prompts(text):
    secs = []
    for chunk in re.split(r"^##\s+", text, flags=re.M)[1:]:
        lines = chunk.splitlines()
        title = lines[0].strip()
        usage = ""
        m = re.search(r"^>\s*(.+)$", chunk, re.M)
        if m:
            usage = m.group(1).strip()
        prompts = []
        for pm in re.finditer(
                r"### 提示词[:：]([^\n]+?)\n+```[a-z]*\n(.*?)```[ \t]*\n+(?:上下文包[:：]([^\n]+))?",
                chunk, re.S | re.M):
            ctxline = (pm.group(3) or "").strip()
            prompts.append({"t": pm.group(1).strip(), "text": pm.group(2).strip(),
                            "ctx": re.sub(r"^(可选|强烈建议附|可选《)\s*", r"", ctxline)})
        secs.append({"t": title, "usage": usage, "prompts": prompts})
    return secs


def render_prompts(ctx):
    text = read(ctx, "11_论文模板与工具", "AI提示词包.md")
    secs = parse_prompts(text)
    body = r"""
<section class="pane on" id="pane-p" style="display:block">
  <div id="plist"></div>
</section>
"""
    script = r"""
var SECS=__SECS__;
function esc(s){return escHtml(s);}
var html='';
SECS.forEach(function(sec){
  html+='<div class="card" style="margin-bottom:16px"><b style="font-family:var(--serif);font-size:17px">'+esc(sec.t)+'</b>'+
    (sec.usage?'<p style="margin:6px 0 4px;font-size:12.5px;color:var(--dim)">'+esc(sec.usage)+'</p>':'');
  sec.prompts.forEach(function(p,i){
    var id='p'+Math.random().toString(36).slice(2,9);
    html+='<div style="border:1px solid var(--line);border-radius:4px;margin-top:10px;overflow:hidden">'+
      '<div style="display:flex;align-items:center;gap:8px;padding:9px 14px;background:#F8F5EC">'+
      '<b style="font-size:13.5px">'+esc(p.t)+'</b>'+
      '<button class="btn solid" data-show="'+id+'" type="button" style="height:24px;padding:0 10px;font-size:11.5px;margin-left:auto">展开</button>'+
      '<button class="btn" data-copy="'+id+'" type="button" style="height:24px;padding:0 10px;font-size:11.5px">复制</button></div>'+
      '<div id="'+id+'" hidden><pre style="margin:0;border:none;border-radius:0;background:var(--sheet);white-space:pre-wrap;font-size:12.8px;line-height:1.9">'+esc(p.text)+'</pre>'+
      (p.ctx?'<div style="padding:8px 14px;border-top:1px dashed var(--line);font-size:12px;color:var(--dim)">📎 上下文包：'+esc(p.ctx)+'</div>':'')+
      '</div></div>';
  });
  html+='</div>';
});
document.getElementById('plist').innerHTML=html;
document.getElementById('plist').addEventListener('click',function(ev){
  var b=ev.target.closest('button');if(!b)return;
  var id=b.dataset.show||b.dataset.copy;
  var box=document.getElementById(id);if(!box)return;
  if(b.dataset.show){
    var open=!box.hidden;
    box.hidden=open;
    b.textContent=open?'展开':'收起';
  }else{
    box.hidden=false;
    b.closest('div').querySelector('[data-show]').textContent='收起';
    copyText(box.querySelector('pre').textContent,b);
  }
});
"""
    return page(ctx, "AI 提示词工坊", "实战工具 · 平时开放",
                "UPC 备赛与赛时 AI 提示词包：选题读题、建模设计、数值验证、论文写作、模拟评审与赛后复盘，内置 74 篇金牌论文的评审标准。",
                "把金牌方法论装进任意 AI 对话框：每条提示词都内置「判据—方程—数值—检验」评审标准与库内上下文包说明。配套文档版见《AI 提示词包》（可直接阅读）。",
                body,
                script.replace("__SECS__", json.dumps(secs, ensure_ascii=False)))


# ================================================================
# 物理模型闪卡
# ================================================================
def parse_model_cards(ctx):
    dom_files = sorted(glob.glob(P(ctx, "08_物理模型综述", "0*.md")))
    cards = []
    for fp in dom_files:
        base = os.path.splitext(os.path.basename(fp))[0]
        dname = re.sub(r"^\d+_", "", base)
        if base == "00_总览":
            continue
        text = open(fp, encoding="utf-8").read()
        url = doc_url(ctx, "08_物理模型综述/" + base + ".md")
        for m in re.finditer(r"^### 2\.\d+\s+(.+?)(?:\s*（([^）]*)）)?\s*$(.*?)(?=^### |\Z)",
                             text, re.S | re.M):
            name = m.group(1).strip()
            years = (m.group(2) or "").strip()
            body = m.group(3)
            def field(kw):
                mm = re.search(r"\*\*" + kw + r"[^*]*\*\*[：:]\s*(.+?)(?=\*\*|\Z)", body, re.S)
                if not mm:
                    return ""
                return re.sub(r"\s+", " ", mm.group(1)).strip()
            scene, eq, pt, err = (field("适用场景"), field("方程"),
                                  field("建模要点"), field("常见错误"))
            if not (scene or eq or pt):
                # 自定义标记/纯段落的小节：取首段兜底，保证卡片可用
                paras = [re.sub(r"\s+", " ", re.sub(r"\*\*", "", p)).strip()
                         for p in body.split("\n\n") if p.strip()]
                if paras:
                    pt = paras[0][:200] + ("…" if len(paras[0]) > 200 else "")
            clean = lambda s: s.replace("**", "")
            cards.append({"d": dname, "n": name, "y": years,
                          "scene": clean(scene), "eq": clean(eq),
                          "pt": clean(pt), "err": clean(err),
                          "u": url})
    return cards


def render_flashcards(ctx):
    cards = parse_model_cards(ctx)
    body = r"""
<section class="pane on" id="pane-fc" style="display:block">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px">
    <select id="fdom" style="height:32px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);font-family:inherit;font-size:12.5px;padding:0 8px;color:var(--mut)"></select>
    <button class="btn" id="fshuffle" type="button">随机打乱</button>
    <div class="segs" id="ffilter" style="display:flex;border:1px solid var(--line2);border-radius:3px;overflow:hidden">
      <a data-v="all" class="on" style="padding:6px 12px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">全部</a>
      <a data-v="todo" style="padding:6px 12px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">未掌握</a>
      <a data-v="done" style="padding:6px 12px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">已掌握</a>
    </div>
    <span class="note" id="fcnt" style="color:var(--dim);font-size:12px"></span>
  </div>
  <div id="fbox"></div>
  <div class="notebox" style="margin-top:14px">点击卡片翻面；「掌握 / 再练」标记存在本浏览器。复习顺序：先未掌握、后已掌握；公式由 KaTeX 渲染。</div>
</section>
"""
    script = r"""
var CARDS=__CARDS__;
var FKEY='upcFlashcards.v1';
function fLoad(){try{return JSON.parse(localStorage.getItem(FKEY)||'{}')}catch(e){return{}}}
function fSave(s){try{localStorage.setItem(FKEY,JSON.stringify(s))}catch(e){}}
var fdom='__ALL__',ffil='all';
var dsel=document.getElementById('fdom');
var doms=[];CARDS.forEach(function(c){if(doms.indexOf(c.d)<0)doms.push(c.d)});
doms.forEach(function(d){var o=document.createElement('option');o.value=d;o.textContent=d;dsel.appendChild(o);});
dsel.addEventListener('change',function(){fdom=dsel.value;render();});
document.getElementById('fshuffle').addEventListener('click',function(){order.sort(function(){return Math.random()-0.5});render();});
document.getElementById('ffilter').addEventListener('click',function(ev){
  var a=ev.target.closest('a');if(!a)return;
  document.querySelectorAll('#ffilter a').forEach(function(x){x.classList.remove('on')});
  a.classList.add('on');ffil=a.dataset.v;render();
});
var order=CARDS.map(function(_,i){return i});
function render(){
  var st=fLoad(),n=0,html='';
  var shown=order.filter(function(i){
    var c=CARDS[i];
    if(fdom!=='__ALL__'&&c.d!==fdom)return false;
    var done=!!st[c.n];
    if(ffil==='todo'&&done)return false;
    if(ffil==='done'&&!done)return false;
    return true;
  });
  shown.forEach(function(i){
    var c=CARDS[i],done=!!st[c.n];n++;
    html+='<div class="card" style="margin-bottom:10px">'+
      '<div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;cursor:pointer" data-flip="'+i+'">'+
      '<b style="font-family:var(--serif);font-size:15px;color:'+(done?'var(--acc)':'var(--ink)')+'">'+escHtml(c.n)+'</b>'+
      (c.y?'<span style="font-family:var(--mono);font-size:11px;color:var(--dim)">'+escHtml(c.y)+'</span>':'')+
      '<span style="margin-left:auto;font-size:11px;color:var(--dim)">'+escHtml(c.d)+' · 点击翻面</span></div>'+
      '<div data-back="'+i+'" hidden style="border-top:1px dashed var(--line);margin-top:8px;padding-top:8px;font-size:13px;line-height:2">'+
      (c.scene?'<p style="margin:2px 0"><b>适用</b>　'+escHtml(c.scene)+'</p>':'')+
      (c.eq?'<p style="margin:2px 0"><b>方程</b>　'+escHtml(c.eq)+'</p>':'')+
      (c.pt?'<p style="margin:2px 0"><b>要点</b>　'+escHtml(c.pt)+'</p>':'')+
      (c.err?'<p style="margin:2px 0;color:#8A3A2A"><b>易错</b>　'+escHtml(c.err)+'</p>':'')+
      '<div style="display:flex;gap:8px;margin-top:8px;align-items:center">'+
      '<button class="btn'+(done?'':' solid')+'" data-mark="'+i+'" type="button">'+(done?'再练':'掌握')+'</button>'+
      '<a class="btn" href="'+c.u+'" target="_blank" style="height:32px">综述原文 →</a></div></div></div>';
  });
  document.getElementById('fbox').innerHTML=html||'<div class="notebox">该筛选下没有卡片。</div>';
  document.getElementById('fcnt').textContent=n+' 张 · 已掌握 '+Object.keys(st).length+' / '+CARDS.length;
  katexRender(document.getElementById('fbox'));
}
function katexRender(el){
  if(window.renderMathInElement)renderMathInElement(el,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});
}
document.getElementById('fbox').addEventListener('click',function(ev){
  var f=ev.target.closest('[data-flip]');
  if(f){var b=document.querySelector('[data-back="'+f.dataset.flip+'"]');
    if(b){b.hidden=!b.hidden;
      if(!b.hidden)katexRender(b);   // 首屏渲染时 KaTeX 可能尚未加载完，展开时补渲染
    }
    return;}
  var m=ev.target.closest('button[data-mark]');
  if(m){var st=fLoad(),c=CARDS[+m.dataset.mark];
    if(st[c.n])delete st[c.n];else st[c.n]=Date.now();
    fSave(st);render();}
});
render();
window.addEventListener('load',function(){render();});   // KaTeX defer 加载完毕后整体补渲染一次
"""
    katex = ('<link rel="stylesheet" href="../09_可视化总览/vendor/katex/katex.min.css">'
             '<script defer src="../09_可视化总览/vendor/katex/katex.min.js"></script>'
             '<script defer src="../09_可视化总览/vendor/katex/contrib/auto-render.min.js"></script>')
    return page(ctx, "物理模型闪卡", "实战工具 · 平时开放",
                "UPC 物理模型闪卡：从八份模型综述提炼的全部核心模型，适用场景/方程/要点/常见错误四面翻卡，赛前刷模型库。",
                "考前把模型库过一遍：翻卡自测「这个场景该上什么模型、方程长什么样、金牌怎么用、常见错误是什么」。标记存在本浏览器。",
                body, script.replace("__CARDS__", json.dumps(cards, ensure_ascii=False)),
                extra_head=katex)


# ================================================================
# 选题助手
# ================================================================
def render_selector(ctx):
    # 题目解读页 URL：按 07_题目解读/<year>_题<p>_*_前缀匹配，避免硬编码文件名
    interp = {}
    for f in glob.glob(P(ctx, "07_题目解读", "*.md")):
        b = os.path.basename(f)
        m = re.match(r"(\d{4})_题([AB])_", b)
        if m:
            interp[(m.group(1), m.group(2))] = doc_url(ctx, "07_题目解读/" + b)
    data = []
    PROBS = [
        (2010,'A',"海王星飞船气动制动",["航天与轨道","流体与空气动力","数值仿真功底"],"建模深度","火箭方程基准＋指数大气＋平方阻力，临界入射角二分夹逼"),
        (2010,'B',"中世纪投石机动力学",["刚体与多体","航天与轨道"],"机制解释","配重-臂-释放角的能量与角动量账本"),
        (2011,'A',"太空塔发射成本",["航天与轨道","工程与设计","数值仿真功底"],"建模深度","全轨迹仿真：共转大气阻力＋重力转向，Δv 折算美元"),
        (2011,'B',"三分球投篮物理",["流体与空气动力","数据处理与统计"],"机制解释","抛体＋马格努斯＋命中率数据的置信区间"),
        (2012,'A',"超级地球上的火山活动",["热学与能量","生物与标度律"],"建模深度","黏度-产热-散热平衡决定火山节奏"),
        (2012,'B',"乒乓球尺寸",["流体与空气动力","生物与标度律"],"数据处理","球尺寸对游戏影响的空气阻力标度分析"),
        (2013,'A',"木星卫星引力辅助减速入轨",["航天与轨道","数值仿真功底"],"建模深度","双曲线飞掠三件套：b、近心距、偏转角"),
        (2013,'B',"超重力环境下的生物结构",["生物与标度律","刚体与多体"],"机制解释","超重力下骨骼-肌肉结构的标度律"),
        (2014,'A',"环双星行星",["航天与轨道","数值仿真功底"],"建模深度","受限三体＋r0-v0 相空间稳定图"),
        (2014,'B',"喷泉高度优化",["流体与空气动力","工程与设计"],"工程优化","水泵-管路-喷嘴匹配的最大高度设计"),
        (2015,'A',"改造火星：定向撞击",["热学与能量","航天与轨道"],"建模深度","彗/陨撞击的能量账与火星气候后果"),
        (2015,'B',"绕树高尔夫球",["流体与空气动力"],"机制解释","马格努斯曲线球绕障弹道"),
        (2016,'A',"核废料太空处置",["航天与轨道","数据处理与统计"],"建模深度","坠日 vs 存带：Δv 统一货币＋小行星撞击概率"),
        (2016,'B',"恐龙 vs 哺乳动物体型上限",["生物与标度律","流体与空气动力"],"机制解释","呼吸/骨骼/散热约束下的体型上限标度"),
        (2017,'A',"太阳帆飞往火星",["航天与轨道","电磁与辐射","数值仿真功底"],"建模深度","光压三级模型＋帆角分段常值优化"),
        (2017,'B',"离子推进器排气磁场导向",["电磁与辐射"],"机制解释","量纲判决的负结果艺术：完美准直上界 6%"),
        (2018,'A',"激光光帆纳米飞行器",["航天与轨道","电磁与辐射","数值仿真功底"],"建模深度","相对论光压＋帆微扰＋nrad 精度预算"),
        (2018,'B',"堆肥堆尺寸",["热学与能量","生物与标度律"],"机制解释","Semenov 热平衡：自热与散热的尺寸博弈"),
        (2019,'A',"火星旅行辐射防护",["电磁与辐射","航天与轨道"],"建模深度","剂量三因子：时间×路径×屏蔽，559→1.86 Sv"),
        (2019,'B',"过山车设计",["刚体与多体","工程与设计"],"工程优化","g 值包络内的安全与刺激设计"),
        (2020,'A',"离子推进器去土星",["航天与轨道","数值仿真功底"],"建模深度","低推力螺旋逃逸＋借力链＋圆锥曲线拼接"),
        (2020,'B',"四旋翼无人机抗风",["流体与空气动力","刚体与多体","数值仿真功底"],"建模深度","ε 单因子参数化＋理论/仿真双轨互验"),
        (2021,'A',"火星大气演化",["热学与能量","航天与轨道"],"建模深度","0.2 bar 初始大气的逸散速率方程百年演化"),
        (2021,'B',"小行星撞击沿海城市",["流体与空气动力","热学与能量"],"建模深度","撞击-海啸-涌浪传播链与城市后果"),
        (2022,'A',"偏转小行星",["航天与轨道","刚体与多体"],"建模深度","动能撞击动量极值＋最短预警时间"),
        (2022,'B',"点球最优策略",["流体与空气动力","数据处理与统计"],"数据处理","射门运动学＋门将博弈的数据决策"),
        (2023,'A',"近太空跳伞安全高度",["流体与空气动力","工程与设计"],"建模深度","指数大气＋终末速度＋15g 反冲双档判据"),
        (2023,'B',"三人蹦床",["刚体与多体","流体与空气动力"],"机制解释","人-床耦合的能量同步与相位"),
        (2024,'A',"空间站空气逃逸时间",["流体与空气动力","数据处理与统计"],"数据处理","漏气速率方程与撤离时间窗"),
        (2024,'B',"火星 150 kW 电源",["电磁与辐射","工程与设计"],"工程优化","核/光电源最小质量设计权衡"),
        (2025,'A',"电声沙桑托琴声学保真",["声学与信号","数值仿真功底"],"建模深度","弦-腔物理模型＋IIR 滤波设计＋七域验证"),
        (2025,'B',"火炮弹道与射表",["流体与空气动力","数值仿真功底","数据处理与统计"],"数据处理","量级约化＋线性风修＋三表交付"),
    ]
    KW = {
        (2010,'A'):["aerobraking","neptune","drag","atmosphere","entry","rocket","fuel","trajectory"],
        (2010,'B'):["trebuchet","projectile","counterweight","torque","rotation","energy"],
        (2011,'A'):["space tower","launch","cost","elevator","altitude","delta-v"],
        (2011,'B'):["basketball","three point","shot","magnus","backspin","trajectory","fiba"],
        (2012,'A'):["super-earth","volcano","volcanism","mantle","heat","tidal","radiogenic"],
        (2012,'B'):["table tennis","ping pong","ball","diameter","drag","air resistance"],
        (2013,'A'):["jupiter","gravity assist","slingshot","flyby","orbital insertion","moon"],
        (2013,'B'):["hypergravity","centrifuge","bone","cardiovascular","skeleton","g-force"],
        (2014,'A'):["circumbinary","binary star","planet","stability","three-body","habitable"],
        (2014,'B'):["fountain","height","pump","nozzle","water","jet"],
        (2015,'A'):["mars","terraforming","asteroid","comet","atmosphere","impact energy"],
        (2015,'B'):["golf","magnus","curve","obstacle","tree","spin"],
        (2016,'A'):["nuclear waste","sun","disposal","delta-v","asteroid belt","probability"],
        (2016,'B'):["dinosaur","mammal","size","scaling","metabolism","breathing","upper limit"],
        (2017,'A'):["solar sail","radiation pressure","photon","mars","attitude","sail angle"],
        (2017,'B'):["ion thruster","exhaust","magnetic field","plasma","deflection","beam"],
        (2018,'A'):["light sail","nanocraft","proxima","laser","relativistic","pointing","accuracy"],
        (2018,'B'):["compost","pile","heat","semenov","thermal runaway","self-heating","size"],
        (2019,'A'):["radiation","dose","shielding","magnetic","cosmic rays","mars","transit"],
        (2019,'B'):["roller coaster","g-force","loop","safety","track","energy"],
        (2020,'A'):["ion thruster","saturn","spiral","gravity assist","low thrust","transfer"],
        (2020,'B'):["quadcopter","drone","wind","stability","control","gust","pid"],
        (2021,'A'):["atmosphere escape","jeans","sputtering","photochemistry","pressure","mars"],
        (2021,'B'):["asteroid","impact","tsunami","coastal","wave","inundation","city"],
        (2022,'A'):["deflection","kinetic impactor","momentum","warning time","orbit","nuclear"],
        (2022,'B'):["penalty kick","soccer","goalkeeper","game theory","magnus","statistics"],
        (2023,'A'):["skydive","stratosphere","terminal velocity","parachute","g-force","reentry"],
        (2023,'B'):["trampoline","bounce","sync","energy","phase","coupling"],
        (2024,'A'):["space station","air leak","evacuation","pressure decay","oxygen"],
        (2024,'B'):["mars","power","nuclear","solar","rtg","mass","kilowatt"],
        (2025,'A'):["sasando","acoustic","iir","filter","resonance","pickup","audio"],
        (2025,'B'):["artillery","ballistics","range table","drag","correction","firing"],
    }
    for y, p, cn, tags, style, oneline in PROBS:
        data.append({"y": y, "p": p, "cn": cn, "tags": tags, "style": style,
                     "line": oneline, "u": interp.get((str(y), p), "../index.html#years"),
                     "kw": KW.get((y, p), [])})
    body = r"""
<section class="pane on" id="pane-sel" style="display:block">
  <div class="card" style="margin-bottom:14px">
    <b style="font-size:14px">① 勾选队伍强项（可多选）</b>
    <div id="tags" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px"></div>
    <b style="font-size:14px;display:block;margin-top:14px">② 偏好题型</b>
    <div class="segs" id="styles" style="display:inline-flex;margin-top:8px">
      <a data-v="" class="on" style="padding:6px 13px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">不限</a>
      <a data-v="建模深度" style="padding:6px 13px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">建模深度</a>
      <a data-v="机制解释" style="padding:6px 13px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">机制解释</a>
      <a data-v="工程优化" style="padding:6px 13px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">工程优化</a>
      <a data-v="数据处理" style="padding:6px 13px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)">数据处理</a>
    </div>
  </div>
  <div class="card" style="margin-bottom:14px">
    <b style="font-size:14px">③ 高级：把 2026 新题原文粘贴进来（中英文都行）</b>
    <textarea id="qtext" rows="4" placeholder="把题面整段贴进来——例：A skydiver jumps from a stratospheric balloon at 38 km… 或 中文题面"
      style="width:100%;margin:8px 0 8px;border:1px solid var(--line2);border-radius:3px;background:var(--paper);padding:9px 12px;font-size:13px;outline:none;resize:vertical"></textarea>
    <button class="btn solid" id="qmatch" type="button">匹配历年同域题</button>
    <span class="note" id="qnote" style="font-size:12px;color:var(--dim);margin-left:10px">命中问题关键词与物理域标签后排序；清空文本恢复勾选模式</span>
  </div>
  <div id="rank"></div>
  <div class="notebox" style="margin-top:14px">选题铁律：<b>离主场模型更近</b>——UPC 评审不奖励难题，奖励自洽。匹配分只是参考，最终请对照对应年份的《题目深度解读》看两题的建模路线图再拍板。2026 新题拿到手后：先读题 → 在这里找同域历年题 → 并读其金牌赏析。</div>
</section>
"""
    script = r"""
var PROBS=__PROBS__;
var sel={};
var TAGS=[];PROBS.forEach(function(p){p.tags.forEach(function(t){if(TAGS.indexOf(t)<0)TAGS.push(t)})});
var tagbox=document.getElementById('tags');
TAGS.forEach(function(t){
  var b=document.createElement('button');b.type='button';b.className='btn';b.textContent=t;
  b.addEventListener('click',function(){
    sel[t]=!sel[t];b.classList.toggle('solid',!!sel[t]);rank();});
  tagbox.appendChild(b);
});
var styleF='';
document.getElementById('styles').addEventListener('click',function(ev){
  var a=ev.target.closest('a');if(!a)return;
  document.querySelectorAll('#styles a').forEach(function(x){x.classList.remove('on')});
  a.classList.add('on');styleF=a.dataset.v;rank();
});
document.getElementById("qmatch").addEventListener("click",function(){
  var q=document.getElementById("qtext").value.trim();
  var note=document.getElementById("qnote");
  if(!q){note.textContent="先粘贴题面，再点匹配";return;}
  var ql=q.toLowerCase();
  // 中文 2-gram
  var grams=[],runs=q.match(/[一-鿿]{2,}/g)||[];
  runs.forEach(function(run){for(var i=0;i<run.length-1;i++)grams.push(run.slice(i,i+2));});
  var rows=PROBS.map(function(p){
    var s=0,hits=[];
    p.tags.forEach(function(t){if(sel[t]&&q.toLowerCase().indexOf(t)>=0){s+=1;hits.push(t);}});
    p.kw.forEach(function(k){
      var c=ql.split(k).length-1;
      if(c){s+=3+2*(c-1);hits.push(k+(c>1?"×"+c:""));}
      else if(k.indexOf(" ")>0&&ql.indexOf(k.split(" ")[0])>=0){s+=1;hits.push(k.split(" ")[0]+"?");}
    });
    if(p.cn){grams.forEach(function(g){if(p.cn.indexOf(g)>=0){s+=2;hits.push(g);}});}
    return {p:p,s:s,why:hits.slice(0,6)};
  }).sort(function(a,b){return b.s-a.s;});
  var top=rows.slice(0,8),max=top.length?top[0].s:0;
  note.textContent="已按关键词命中排序（满分参考 "+max+"）";
  document.getElementById("rank").innerHTML='<div class="note" style="margin:0 0 10px;font-size:12px;color:var(--dim)">按题面关键词命中排序：</div>'+top.map(function(r){
    return '<div class="card" style="margin-bottom:10px;'+(r.s>=6?'border-color:var(--acc);border-width:1.5px':'')+'">'+
      '<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:baseline">'+
      '<b style="font-family:var(--mono);color:var(--acc);font-size:13px">'+r.p.y+' 题'+r.p.p+'</b>'+
      '<b style="font-family:var(--serif);font-size:15px">'+escHtml(r.p.cn)+'</b>'+
      (r.s?'<span style="margin-left:auto;font-size:11px;color:var(--acc);font-family:var(--mono)">命中 '+r.s+'</span>':'')+'</div>'+
      (r.why.length?'<p style="margin:4px 0;font-size:12px;color:var(--mut)">命中：'+escHtml(r.why.join("、"))+'</p>':'')+
      '<p style="margin:4px 0 8px;font-size:13px;color:var(--mut)">'+escHtml(r.p.line)+'</p>'+
      '<a class="btn sm solid" href="'+r.p.u+'" target="_blank">题目深度解读 →</a></div>';
  }).join('');
});
function rank(){
  var rows=PROBS.map(function(p){
    var s=0,why=[];
    p.tags.forEach(function(t){
      if(sel[t]){s+=2;why.push(t);}});
    if(styleF&&p.style===styleF){s+=3;why.push('题型·'+p.style);}
    return {p:p,s:s,why:why};
  }).sort(function(a,b){return b.s-a.s});
  var html=rows.slice(0,10).map(function(r){
    var hot=r.s>=4;
    return '<div class="card" style="margin-bottom:10px;'+(hot?'border-color:var(--acc);border-width:1.5px':'')+'">'+
      '<div style="display:flex;align-items:baseline;gap:9px;flex-wrap:wrap">'+
      '<b style="font-family:var(--mono);color:var(--acc);font-size:13px">'+r.p.y+' 题'+r.p.p+'</b>'+
      '<b style="font-family:var(--serif);font-size:15px">'+escHtml(r.p.cn)+'</b>'+
      '<span style="font-size:11px;color:var(--dim)">'+escHtml(r.p.style)+'</span>'+
      (r.s?'<span style="margin-left:auto;font-size:11px;color:var(--acc);font-family:var(--mono)">匹配 '+r.s+'</span>':'')+'</div>'+
      '<p style="margin:5px 0 8px;font-size:13px;color:var(--mut)">'+escHtml(r.p.line)+'</p>'+
      '<div style="display:flex;gap:8px;flex-wrap:wrap">'+
      '<a class="btn sm solid" href="'+r.p.u+'" target="_blank">题目深度解读 →</a>'+
      '<a class="btn sm" href="../index.html#papers" target="_blank">该题金牌论文库</a></div></div>';
  }).join('');
  document.getElementById('rank').innerHTML='<div class="note" style="margin:0 0 10px;font-size:12px;color:var(--dim)">按匹配度排序（勾选越多越准）：</div>'+html;
}
rank();
"""
    return page(ctx, "选题助手", "实战工具 · 平时开放",
                "UPC 选题助手：按队伍强项与题型偏好，从 16 年 32 道官方题目中匹配最合适的历年同域题与建模路线图。",
                "开赛读题的 30 分钟里用它：勾选队伍强项 → 得到同域历年题清单 → 并读对应《题目深度解读》与金牌赏析，判断 2026 两题哪道离主场更近。",
                body, script.replace("__PROBS__", json.dumps(data, ensure_ascii=False)))


# ================================================================
# 数值实验台（Pyodide，按需从 CDN 懒加载）
# ================================================================
SKYDIVING_PY = r'''# 2023-A 近太空跳伞（简化示范模型）
# 状态: v 垂直速度(向下为正), h 高度; 大气: 指数模型 rho = 1.225*exp(-h/8500)
import math

g     = 9.81      # m/s^2
RHO0  = 1.225     # kg/m^3 海平面密度
HSC   = 8500.0    # m     标高
H_GROUND = 0.0

def rho(h):
    return RHO0 * math.exp(-h / HSC)

def simulate(h0=30000.0, v0=0.0, m=90.0, cd_a=0.9, dt=0.05, g_override=None):
    """欧拉积分：返回 (ts, hs, vs) 与关键指标"""
    gloc = g if g_override is None else g_override
    ts, hs, vs = [0.0], [h0], [v0]
    v, h, t = v0, h0, 0.0
    vmax, h_vmax = v0, h0
    while h > H_GROUND and t < 1200:
        a = gloc - 0.5 * rho(h) * v * abs(v) * cd_a / m   # 阻力与速度反向
        v += a * dt
        h -= v * dt
        t += dt
        if v > vmax: vmax, h_vmax = v, h
        ts.append(t); hs.append(max(h, 0.0)); vs.append(v)
    return {"t": ts, "h": hs, "v": vs, "vmax": vmax, "h_vmax": h_vmax,
            "v_terminal_ground": math.sqrt(2*m*gloc/(rho(0)*cd_a)),
            "t_ground": ts[-1]}
'''


def render_lab(ctx):
    body = r"""
<section class="pane on" id="pane-lab" style="display:block">
  <div class="notebox" style="margin-bottom:14px"><b>数值实验台 v1</b>：在浏览器里直接跑 Python 物理模型（Pyodide/WASM，与本库精读里的代码同款风格）。
  首次使用需联网加载约 10 MB 运行时（约 30–60 秒，之后浏览器有缓存）；修改代码后点「运行」即时重算。本页是示范：2023-A 太空跳伞的 1D 竖直下落（指数大气＋平方阻力）。</div>
  <div class="card">
    <div style="display:flex;gap:14px;flex-wrap:wrap;align-items:flex-end;margin-bottom:10px">
      <label style="font-size:12.5px;color:var(--mut)">初始高度 h₀ = <b id="lh0" style="color:var(--ink);font-family:var(--mono)">30.0</b> km
        <input id="h0" type="range" min="5" max="60" step="0.5" value="30" style="display:block;width:180px;margin-top:4px;accent-color:#9C3F2E"></label>
      <label style="font-size:12.5px;color:var(--mut)">质量 m = <b id="lm" style="color:var(--ink);font-family:var(--mono)">90</b> kg
        <input id="m" type="range" min="50" max="160" step="1" value="90" style="display:block;width:180px;margin-top:4px;accent-color:#9C3F2E"></label>
      <label style="font-size:12.5px;color:var(--mut)">Cd·A = <b id="lca" style="color:var(--ink);font-family:var(--mono)">0.90</b> m²
        <input id="ca" type="range" min="0.2" max="3" step="0.05" value="0.9" style="display:block;width:180px;margin-top:4px;accent-color:#9C3F2E"></label>
      <button class="btn solid" id="run" type="button">运行（首次需加载运行时）</button>
    </div>
    <div id="status" style="font-size:12.5px;color:var(--dim);margin-bottom:8px">等待启动：点击「运行」后开始加载 Pyodide。</div>
  </div>
  <div class="card" style="margin-top:14px" id="resultbox"></div>
  <details class="card" style="margin-top:14px">
    <summary style="cursor:pointer;font-weight:600;font-size:14px">查看 / 编辑 Python 源码（这就是 2023-A 精读同款的建模骨架）</summary>
    <textarea id="pysrc" spellcheck="false" style="width:100%;margin-top:10px;border:1px solid var(--line2);border-radius:3px;background:var(--paper);padding:10px 12px;font-size:12.8px;font-family:var(--mono);line-height:1.7;outline:none;resize:vertical" rows="26"></textarea>
  </details>
</section>
"""
    script = r"""
var PY0=__PYSRC__;
var ta=document.getElementById('pysrc');
ta.value=localStorage.getItem('upcLab.src')||PY0;
ta.addEventListener('input',function(){localStorage.setItem('upcLab.src',ta.value)});
var h0=document.getElementById('h0'),m=document.getElementById('m'),ca=document.getElementById('ca');
[['h0','lh0',function(v){return (+v).toFixed(1)+' km';},10],['m','lm',function(v){return v+' kg';},1],['ca','lca',function(v){return (+v).toFixed(2)+' m²';},100]]
.forEach(function(cfg){
  var el=document.getElementById(cfg[0]);
  function upd(){document.getElementById(cfg[1]).textContent=cfg[2](el.value);}
  el.addEventListener('input',function(){upd();cfg[3]&&live();});
  upd();
});
var pyodide=null,loading=false;
var statusEl=document.getElementById('status'),runBtn=document.getElementById('run');
function setStatus(s,hot){statusEl.innerHTML=hot?'<b style="color:var(--acc)">'+s+'</b>':s;}
async function ensurePy(){
  if(pyodide)return pyodide;
  if(loading)return null;
  loading=true;runBtn.disabled=true;
  setStatus('正在加载 Pyodide 运行时（约 10 MB，首次 30–60 秒）…',true);
  try{
    await new Promise(function(res,rej){
      if(window.loadPyodide)return res();
      var s=document.createElement('script');
      s.src='https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js';
      s.onload=res;s.onerror=rej;
      document.head.appendChild(s);
    });
    pyodide=await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.26.4/full/'});
    setStatus('运行时就绪 ✓',true);
    runBtn.disabled=false;runBtn.textContent='运行';
  }catch(e){
    setStatus('加载失败（本页需要联网加载运行时；离线时请本地运行 Python）。'+e);
    runBtn.disabled=false;runBtn.textContent='重试加载';
  }
  loading=false;
  return pyodide;
}
function live(){ if(pyodide) runAll(); }
runBtn.addEventListener('click',async function(){
  var py=await ensurePy();
  if(py)runAll();
});
async function runAll(){
  var t0=performance.now();
  setStatus('计算中…',true);
  var code=ta.value+`\n__res = simulate(h0=${(+h0.value*1000).toFixed(1)}, m=${(+m.value).toFixed(0)}, cd_a=${(+ca.value).toFixed(2)})\nimport json\njson.dumps(__res)`;
  try{
    var resJson=await pyodide.runPythonAsync(code);
    var r=JSON.parse(resJson);
    draw(r);
    setStatus('完成 · '+(performance.now()-t0).toFixed(0)+' ms · '+r.t.length+' 步');
  }catch(e){
    setStatus('运行出错：'+String(e).slice(0,300));
  }
}
function draw(r){
  var W=900,H=300,pad=44;
  var n=r.t.length;
  function px(i){return pad+(W-2*pad)*i/(n-1);}
  var tmax=r.t[n-1]||1,vmax=Math.max.apply(null,r.v)*1.06||1,hmax=Math.max.apply(null,r.h)||1;
  function py(v){return H-pad-(H-2*pad)*v/vmax;}
  function ph(h){return H-pad-(H-2*pad)*h/hmax;}
  var s='<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:auto" xmlns="http://www.w3.org/2000/svg">';
  s+='<text x="'+pad+'" y="18" font-size="12" fill="#6E6557">速度 v(t) 与高度 h(t)　·　蓝色为速度、朱色为高度（虚线为当地终末速度参考）</text>';
  s+='<line x1="'+pad+'" y1="'+(H-pad)+'" x2="'+(W-pad)+'" y2="'+(H-pad)+'" stroke="#D9D0BD"/>';
  s+='<line x1="'+pad+'" y1="'+pad+'" x2="'+pad+'" y2="'+(H-pad)+'" stroke="#D9D0BD"/>';
  var pathV='',pathH='';
  for(var i=0;i<n;i++){pathV+=(i?'L':'M')+px(i).toFixed(1)+' '+py(r.v[i]).toFixed(1)+' ';}
  for(i=0;i<n;i++){pathH+=(i?'L':'M')+px(i).toFixed(1)+' '+ph(r.h[i]).toFixed(1)+' ';}
  s+='<path d="'+pathV+'" fill="none" stroke="#3A5A8C" stroke-width="1.8"/>';
  s+='<path d="'+pathH+'" fill="none" stroke="#9C3F2E" stroke-width="1.8" stroke-dasharray="4 3"/>';
  // 轴标注
  s+='<text x="'+(W-pad)+'" y="'+(H-pad+16)+'" font-size="11" fill="#9A9080" text-anchor="end">t / s（max '+tmax.toFixed(0)+'）</text>';
  s+='<text x="'+(pad-8)+'" y="'+(pad+8)+'" font-size="11" fill="#9A9080" text-anchor="end">'+vmax.toFixed(0)+'</text>';
  s+='<text x="'+(pad-8)+'" y="'+(H-pad)+'" font-size="11" fill="#9A9080" text-anchor="end">0</text>';
  s+='</svg>';
  var box=document.getElementById('resultbox');
  box.innerHTML='<div style="display:flex;gap:26px;flex-wrap:wrap;margin-bottom:10px">'+
    '<div><b style="font-family:var(--serif);font-size:22px;color:var(--ink)">'+r.vmax.toFixed(0)+' m/s</b><span style="font-size:11.5px;color:var(--dim)">　最大速度 @ h='+(r.h_vmax/1000).toFixed(1)+' km</span></div>'+
    '<div><b style="font-family:var(--serif);font-size:22px;color:var(--ink)">'+r.v_terminal_ground.toFixed(0)+' m/s</b><span style="font-size:11.5px;color:var(--dim)">　海平面终末速度（解析 √(2mg/ρ₀C)）</span></div>'+
    '<div><b style="font-family:var(--serif);font-size:22px;color:var(--ink)">'+r.t_ground.toFixed(0)+' s</b><span style="font-size:11.5px;color:var(--dim)">　落地总时长</span></div></div>'+s+
    '<div class="note" style="margin-top:8px;font-size:12px;color:var(--dim)">试试：把 h₀ 拉到 60 km 看最大速度出现在哪个高度；把 Cd·A 调到 3 模拟开伞后的急剧减速。完整版判据（15 g 反冲、驻点温度双档）见 2023-A 题目解读。</div>';
}
"""
    pyodide_head = ''   # pyodide.js 改为点击「运行」时动态注入，消除首屏 CDN 依赖
    return page(ctx, "数值实验台", "实战工具 · 平时开放",
                "UPC 数值实验台：浏览器里直接运行 Python 物理模型（Pyodide），v1 内置 2023-A 太空跳伞简化模型，参数可调、代码可改。",
                "不用装 Python 也能跑物理：滑杆调参数、代码框改模型，点运行立刻出曲线。示范模型来自 2023-A《近太空跳伞》精读。",
                body, script.replace("__PYSRC__", json.dumps(SKYDIVING_PY)),
                extra_head=pyodide_head)


# ================================================================
# 新手课堂（HTML 幻灯：三课程贯穿 2023-A 跳伞一道题）
# ================================================================
def render_tutorial(ctx):
    COURSES = {
        "model": {"name": "课程一 · 建模", "tag": "从一句话到方程", "slides": [
            {"t": "你只需要会一句话", "sub": "本课任务：把「人会越掉越快」变成一个方程",
             "body": [
                 {"k": "p", "text": "我们全程用 <b>2023 年 A 题「近太空跳伞」</b>做示范——一个从 39 km 高空跳下来的人。这道题好就好在：谁都知道人会往下掉，也就是说，<b>你已经有直觉了</b>。"},
                 {"k": "callout", "text": "UPC 评的不是方程高级不高级，而是「判据—方程—数值—检验」这条链完不完整。全库 74 篇金牌论文里，有一篇零数值模拟夺金（2013-B），最多的也只用最朴素的欧拉法。简单 + 完整 = 能赢。"},
                 {"k": "try", "text": "先看一眼题目的完整起步卡（之后随时回来对照）", "href": "../09_可视化总览/docs/07_题目解读/2023_题A_太空跳伞_零基础起步卡.html", "label": "零基础起步卡"},
             ]},
            {"t": "第一步 · 圈三样：对象 / 动作 / 数字", "sub": "拿到题不要想公式，先像划重点一样圈三样东西",
             "body": [
                 {"k": "list", "items": [
                     "<b>圈对象</b>：谁在动？—— 一个 90 kg 的人（带着伞）",
                     "<b>圈动作</b>：怎么动？—— 从 39 km 高空往下掉，越掉越快，中途开伞",
                     "<b>圈数字</b>：给了什么数？—— 39 km、「安全」这个词、最终要一个高度答案",
                 ]},
                 {"k": "p", "text": "输出一张「任务卡」：<b>预测人从多高起跳能安全落地</b>。注意「安全」是个模糊词——它之后会被你翻译成一个具体判据（例如「过载不超过 8g」），这是 UPC 的第一门功课：模糊词操作化。"},
             ]},
            {"t": "第二步 · 变量表：给每个直觉发身份证", "sub": "每个直觉背后都有一个会变的量——把它们列成表",
             "body": [
                 {"k": "table", "header": ["直觉", "变量", "符号", "单位", "合理范围"],
                  "rows": [
                      ["人会越掉越快", "速度", "v", "m/s", "0 – 400"],
                      ["掉的过程发生在空中", "高度", "h", "m", "0 – 39000"],
                      ["高空空气稀薄", "空气密度", "ρ", "kg/m³", "0 – 1.22"],
                      ["人的轻重有影响", "质量", "m", "kg", "60 – 120"],
                      ["伞越大减速越猛", "阻力面积", "C_dA", "m²", "0.5 – 150"],
                  ]},
                 {"k": "callout", "text": "新手最容易漏的是「单位」一列。写变量表时就填好单位，后面 90% 的量级错误都能避免。表格不用一次列全，边做边补。"},
             ]},
            {"t": "第三步 · 选骨架：74 篇金牌就用这几种", "sub": "骨架 = 你写的那条主方程的「类型」",
             "body": [
                 {"k": "list", "items": [
                     "<b>什么东西在动 / 速度在变？</b> → 牛顿第二定律：<b>m·dv/dt = ΣF</b>（力求和）",
                     "<b>热量在流动 / 温度在变？</b> → 能量平衡：收入 = 支出 + 累积",
                     "<b>数量在衰减 / 增长？</b> → 指数过程：dN/dt = ±λN",
                     "<b>多个物体互相绕？</b> → 还是牛顿第二定律，只是力里多了引力项",
                 ]},
                 {"k": "p", "text": "跳伞题：速度 v 在变 ⇒ 选<b>牛顿第二定律</b>。写出来就是 <b>m·dv/dt = ΣF</b>——左边是「质量 × 速度变化率」，右边是「所有力加起来」。骨架到此已经完成，剩下的问题只有一个：ΣF 里到底有哪些力？"},
             ]},
            {"t": "第四步 · 插零件：把「空气有阻力」翻译成一项", "sub": "零件 = 前人写好的现成公式，你只需要知道什么时候抓哪个",
             "body": [
                 {"k": "p", "text": "逐项问：<b>谁在对这个人施力？</b>"},
                 {"k": "list", "items": [
                     "<b>地球</b>拉他 → 重力 <b>mg</b>，方向向下（正号，因为我们取向下为正）",
                     "<b>空气</b>阻碍他 → 阻力 <b>½·ρ·v²·C_dA</b>，方向与运动方向相反（负号）",
                 ]},
                 {"k": "formula", "tex": "m\\,\\frac{dv}{dt} = \\underbrace{mg}_{\\text{重力零件}} - \\underbrace{\\tfrac{1}{2}\\,\\rho(h)\\,C_d A\\,v^2}_{\\text{阻力零件}}"},
                 {"k": "list", "items": [
                     "为什么是 v²？—— 高速运动（上百 m/s）的空气阻力与速度平方成正比，这是实验规律；低速（散步）才近似正比于 v",
                     "为什么有 ½？—— 纯粹是工程师约定：把 ½ 归进 C_d 的定义里，所有教科书都这么写",
                     "为什么 ρ 写成 ρ(h)？—— 密度随高度变，用零件「指数大气」：ρ = 1.225·e^(−h/8500)",
                 ]},
             ]},
            {"t": "第五步 · 量级自辩：学会说「这个项比那个小 100 倍」", "sub": "每个「忽略」都要配一句数字，这是评委最看重的动作之一",
             "body": [
                 {"k": "p", "text": "把数代进去粗算一遍（心算即可）："},
                 {"k": "table", "header": ["阶段", "代入", "阻力大小", "对比重力 mg≈0.9 kN", "结论"],
                  "rows": [
                      ["开伞前", "½×0.3×200²×1", "≈ 6 kN", "同量级以上", "必须建模"],
                      ["伞全开后", "½×0.3×8²×50", "≈ 0.5 kN", "同量级", "必须建模，且主导减速"],
                      ["刚出舱 v≈0", "½×0.03×0²×1", "≈ 0", "远小于", "瞬间可忽略（写一行数字封存）"],
                  ]},
                 {"k": "callout", "text": "看到没有：同一个阻力零件，在不同阶段「重要性」完全不同。论文里每个「忽略」都写上这样一行估算——2010 年金牌队的原话句式是 \"a 'significant' saving is not quantitative enough. For a fair estimation we decided to set 20%.\""},
             ]},
            {"t": "结课检验 + 下一步", "sub": "你已经把一句话变成了方程",
             "body": [
                 {"k": "p", "text": "回顾这五步：<b>圈三样 → 变量表 → 选骨架 → 插零件 → 量级自辩</b>。全程没有用到超过高中的数学。"},
                 {"k": "list", "items": [
                     "检验题（蹦床，2023-B）：人被蹦床弹起，骨架选什么？（答：还是 m·dv/dt=ΣF，力换成弹力+重力+阻力）→ <a href=\"../09_可视化总览/docs/07_题目解读/2023_题B_三人蹦床_零基础起步卡.html\" target=\"_blank\">起步卡</a>",
                     "检验题（堆肥堆，2018-B）：堆内温度在变？（答：换成能量平衡骨架）→ <a href=\"../09_可视化总览/docs/07_题目解读/2018_题B_堆肥堆尺寸_零基础起步卡.html\" target=\"_blank\">起步卡</a>",
                     "觉得不够深？→ 读本篇的《零基础起步卡》与完整《题目深度解读》",
                 ]},
                 {"k": "try", "text": "下一步：这个方程怎么变成代码和图？", "href": "javascript:void(0)", "label": "去课程三（页面顶部切换）"},
             ]},
            {"t": "起步卡合集 · 9 道直觉友好题", "sub": "每张卡五层结构，教一种「骨架」的选法——把 9 张刷完，骨架选择就长在身上了",
             "body": [
                 {"k": "table", "header": ["题", "练的骨架", "起步卡"],
                  "rows": [
                      ["2023-A 近太空跳伞", "牛顿第二定律 + 指数大气", "<a href=\"../09_可视化总览/docs/07_题目解读/2023_题A_太空跳伞_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2023-B 三人蹦床", "牛顿第二定律（弹力/周期）", "<a href=\"../09_可视化总览/docs/07_题目解读/2023_题B_三人蹦床_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2019-B 过山车设计", "能量守恒 + 过载分析", "<a href=\"../09_可视化总览/docs/07_题目解读/2019_题B_过山车设计_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2011-B 三分球投篮", "抛体 + 马格努斯修正", "<a href=\"../09_可视化总览/docs/07_题目解读/2011_题B_三分球投篮_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2018-B 堆肥堆尺寸", "能量平衡（热）", "<a href=\"../09_可视化总览/docs/07_题目解读/2018_题B_堆肥堆尺寸_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2016-B 恐龙体型上限", "标度律（幂律）", "<a href=\"../09_可视化总览/docs/07_题目解读/2016_题B_恐龙哺乳动物体型上限_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2024-A 空间站空气逃逸", "指数过程（流失率）", "<a href=\"../09_可视化总览/docs/07_题目解读/2024_题A_空间站空气逃逸_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2010-B 投石机动力学", "刚体转动（I·dω/dt）", "<a href=\"../09_可视化总览/docs/07_题目解读/2010_题B_投石机动力学_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                      ["2014-B 喷泉优化", "能量守恒 + 伯努利", "<a href=\"../09_可视化总览/docs/07_题目解读/2014_题B_喷泉优化_零基础起步卡.html\" target=\"_blank\">打开 →</a>"],
                  ]},
                 {"k": "callout", "text": "用法建议：先照着跳伞卡走一遍 → 挑两道自己有直觉的题，合上卡片自己走五层，再打开对照 → 开赛拿到任何新题，这五层就是你的作业纸。"},
             ]},
        ]},
        "paper": {"name": "课程二 · 论文", "tag": "从提纲到 PDF", "slides": [
            {"t": "论文不是作文，是填空", "sub": "每一节都有固定的一句话模板——你负责填内容，不负责发明结构",
             "body": [
                 {"k": "p", "text": "UPC 论文的结构几乎是固定的：<b>评委平均只花 3 分钟，看标题、摘要、全部图题</b>就定档。所以我们的策略是：把力气花在摘要和图上，其余各节按模板逐节填。"},
                 {"k": "callout", "text": "官方硬规定：标题页只放四样——队号、题号、标题、≤300 词摘要。全文不得出现姓名或学校（匿名评审）。完整规则见《比赛规则》。"},
             ]},
            {"t": "解剖一篇金牌论文", "sub": "2010-A-160《海王星气动制动》的标题页长这样",
             "body": [
                 {"k": "img", "src": "../06_论文页面图/2010/2010-GM-A-160_p1.png", "caption": "金牌论文标题页：只有队号 160、Problem A、标题、一页带数字的摘要"},
                 {"k": "p", "text": "注意它的摘要：<b>第二句就钉死符号与数值（R_N ≈ 24764 km），最后一句给区间结论（8.8296° < θ < 8.8549°）</b>。没有一句废话，也没有一句没有数字。"},
             ]},
            {"t": "逐节一句话模板（照抄即可）", "sub": "把下表的「模板」抄进你的提纲，每节展开 1–3 段",
             "body": [
                 {"k": "table", "header": ["节", "一句话模板"],
                  "rows": [
                      ["Abstract", "定义关键符号 → 摆出两难 → 方法一句话 → <b>数值结论</b> → 建议与适用域"],
                      ["Introduction", "用自己的话复述题目 → 列出判据（模糊词→数字）→ 简述路线"],
                      ["Baseline（基准）", "先算一个不用主模型的简单情形，给出「锚数字」"],
                      ["Model", "骨架方程 + 每个零件一段（含假设的一句量级自辩）"],
                      ["Numerical Method", "方法名+步长+初值+边界+终止条件，五要素缺一不可"],
                      ["Results", "图为主，每个图被正文点名，与基准对比"],
                      ["Discussion", "局限、误差来源、最坏情形——诚实是加分项"],
                      ["Conclusion", "答案 + 建议（负结论也是结论）"],
                  ]},
             ]},
            {"t": "英文怎么办：不用学英语", "sub": "38 句金牌句式 + 五步润色法，填空式写作",
             "body": [
                 {"k": "p", "text": "库里有现成的两件武器：<b>《写作句库》38 条按论文部位组织的句式</b>（直接抄），和<b>《中译英润色库》五步法</b>（中文草稿 → 英文）。先背这三个开头："},
                 {"k": "list", "items": [
                     "定义：<span style=\"font-family:var(--mono)\">We define the radius of Neptune, R_N, as …</span>",
                     "假设：<span style=\"font-family:var(--mono)\">To simplify our calculations, we assume …</span>",
                     "结论：<span style=\"font-family:var(--mono)\">We conclude that 8.83° < θ < 8.85°.</span>",
                 ]},
                 {"k": "try", "text": "赛时写作句库与中译英检索都在作战室里", "href": "warroom.html", "label": "打开作战室"},
             ]},
            {"t": "公式怎么插：LaTeX 15 个命令就够", "sub": "写一篇 UPC 论文需要的排版知识比一页 PPT 还少",
             "body": [
                 {"k": "table", "header": ["想要的效果", "写法", "渲染结果"],
                  "rows": [
                      ["行内公式", "$v^2$", "v² 嵌在句子里"],
                      ["分式", "$\\\\frac{mg}{C_dA}$", "上下结构的分数"],
                      ["下标 / 上标", "$C_d$、$v^2$", "C 的下标 d"],
                      ["希腊字母", "$\\\\rho$、$\\\\theta$、$\\\\Delta$", "ρ、θ、Δ"],
                      ["重要方程（带编号）", "$$m\\\\frac{dv}{dt}=mg-\\\\frac{1}{2}\\\\rho v^2 C_dA$$", "居中展示的方程"],
                      ["组合参数", "$\\\\sigma \\\\equiv C_d M A / 2k_B$", "把常数打包，方程干净"],
                  ]},
                 {"k": "callout", "text": "以上公式在本页由 KaTeX 实时渲染——你在 Overleaf 里写出来就是同样的效果。15 个命令用熟，足够写完全文；遇到没见过的去 ctan.org 搜，或直接问 AI「这句 LaTeX 怎么写」。"},
             ]},
            {"t": "图表怎么插：两个模板 + 三条规矩", "sub": "图是评委唯一会逐张看的东西",
             "body": [
                 {"k": "code", "title": "插图模板（main.tex 里直接改）", "text": "\\begin{figure}[h]\n  \\centering\n  \\includegraphics[width=0.8\\textwidth]{fig3_landing_speed.png}\n  \\caption{Landing speed converges to 40 m/s (4--5 significant figures).}\n  \\label{fig:speed}\n\\end{figure}\n\n\\begin{table}[h]\n  \\centering\n  \\begin{tabular}{lcc}\n    \\hline\n    Parameter & Value & Source \\\\\n    \\hline\n    Mass      & 90 kg & typical adult \\\\\n    \\hline\n  \\end{tabular}\n\\end{table}"},
                 {"k": "list", "items": [
                     "规矩一：每张图有编号，正文必须点名（\"Figure 3 shows …\"）",
                     "规矩二：轴标签带单位，轨迹图用等比例坐标",
                     "规矩三：<b>结论写进图题</b>（caption 里带数字）——评委看图题就能拿到结论",
                 ]},
                 {"k": "try", "text": "8 类图的现成 matplotlib 代码在图表配方库", "href": "../11_论文模板与工具/图表配方库/matplotlib_recipes.py", "label": "看配方源码"},
             ]},
            {"t": "编译出 PDF：Overleaf 三步", "sub": "不用装任何软件",
             "body": [
                 {"k": "list", "items": [
                     "<b>第一步</b>：overleaf.com 注册 → New Project → Blank Project",
                     "<b>第二步</b>：把本库「金牌骨架款」main.tex 的内容整个粘贴进去（或上传）",
                     "<b>第三步</b>：按本课的逐节模板替换内容，点 Recompile，右侧实时出 PDF",
                 ]},
                 {"k": "try", "text": "四套可选模板（金牌骨架款 / 官方同源款 / 双栏款 / 极简款）", "href": "../index.html#templates", "label": "去模板工坊"},
                 {"k": "callout", "text": "交卷前最后一步：打开作战室「提交终检」标签，A–G 30 项逐条勾——包括页首队号、摘要带数字、提前 2 小时交。"},
             ]},
        ]},
        "code": {"name": "课程三 · 编程", "tag": "从零到第一条轨迹", "slides": [
            {"t": "仿真是什么：一句话", "sub": "把连续时间切成小步，每步用「现在的状态」算「下一刻」",
             "body": [
                 {"k": "p", "text": "课程一得到的方程 <b>m·dv/dt = mg − ½ρv²C_dA</b> 描述的是「每一瞬间」的变化率。计算机不会算连续——但会算重复。所以我们把 48 小时里连续的 172800 秒，切成一小步一小步（比如每步 0.1 秒）："},
                 {"k": "list", "items": [
                     "知道现在的 v 和 h → 用方程算出现在的加速度 a",
                     "假设这 0.1 秒里 a 不变 → 算出 0.1 秒后的新 v、新 h",
                     "重复几万次 → 就得到整条下落轨迹",
                 ]},
                 {"k": "callout", "text": "这就是全部秘密。<b>你不需要会编程</b>——只需要看懂并修改接下来的 10 行代码。"},
             ]},
            {"t": "环境：什么都不用装", "sub": "两条路，推荐第一条",
             "body": [
                 {"k": "list", "items": [
                     "<b>路线 A（零安装）</b>：本站的数值实验台——浏览器里跑 Python（Pyodide），点一下就运行；手机也能开",
                     "<b>路线 B（本地）</b>：python.org 装 Python（勾选 Add to PATH），再 <span style=\"font-family:var(--mono)\">pip install numpy matplotlib</span>",
                 ]},
                 {"k": "try", "text": "先开着实验台，边看这页课边动手", "href": "lab.html", "label": "打开数值实验台"},
             ]},
            {"t": "第一个仿真：真的只有 10 行", "sub": "每一行都有注释——看不懂哪行就把哪行抄进 AI 问",
             "body": [
                 {"k": "code", "title": "skydive.py（可复制）", "text": "import math\nh, v, dt = 39000.0, 0.0, 0.1   # 高度(m)、速度(m/s)、步长(s)\nm, cda = 90.0, 1.0             # 质量(kg)、阻力面积(m^2)\nts, hs, vs = [0.0], [h], [v]   # 记录轨迹用的列表\nt = 0.0\nwhile h > 0:\n    rho = 1.225 * math.exp(-h / 8500)        # 零件：指数大气\n    a = 9.81 - 0.5 * rho * v * abs(v) * cda / m  # 骨架：m dv/dt = mg - 阻力\n    v += a * dt                              # 更新速度\n    h -= v * dt                              # 更新高度\n    t += dt\n    ts.append(t); hs.append(h); vs.append(v)\nprint(\"落地速度 %.1f m/s, 用时 %.0f s\" % (v, t))"},
                 {"k": "callout", "text": "看到第 9 行了吗？<b>它就是课程一那个方程</b>。仿真不难——难的那步（建模）你已经完成了。"},
             ]},
            {"t": "方程 ↔ 代码对照（本课最重要的一页）", "sub": "左边每个符号都能在右边找到位置",
             "body": [
                 {"k": "compare", "left": {"t": "方程（课程一）", "body": "m·<b style='color:#3A5A8C'>dv/dt</b> = <b style='color:#9C3F2E'>mg</b> − <b style='color:#2F7D6B'>½ρ(h)·C_dA·v²</b><br><br><span style='font-size:12.5px;color:#6E6557'>左端：速度的变化率<br>右端：重力项 − 阻力项</span>"},
                  "right": {"t": "代码（第 8–10 行）", "body": "<span style='font-family:var(--mono);font-size:12.5px;line-height:2.1'>a = 9.81<br>&nbsp;&nbsp;&nbsp;&nbsp;- 0.5 * rho * v * abs(v) * cda / m<br>v += a * dt</span><br><br><span style='font-size:12.5px;color:#6E6557'>9.81 就是 g；rho 来自上一行零件；<br>v*abs(v) 是「带方向的 v²」；<br>最后一句把 dv/dt 变成实际更新</span>"}},
                 {"k": "list", "items": [
                     "为什么写 v*abs(v) 而不是 v*v？—— 阻力永远与运动方向相反，这样写上升/下降都不会出符号错误",
                     "为什么除以 m？—— 方程两边除以 m，解出 a，这就是 dv/dt",
                     "为什么 v += a*dt？—— 「下一刻速度 = 现在 + 变化率 × 步长」，这就是欧拉法",
                 ]},
             ]},
            {"t": "画图：5 行", "sub": "没图的仿真等于没做——评委要的是图",
             "body": [
                 {"k": "code", "title": "在 skydive.py 末尾追加", "text": "import matplotlib.pyplot as plt\nplt.plot(ts, vs, label=\"speed v(t)\")\nplt.plot(ts, [x for x in hs], \"--\", label=\"altitude h(t)\")\nplt.xlabel(\"t / s\"); plt.ylabel(\"v / (m/s), h / m\")\nplt.legend(); plt.savefig(\"fig1_skydive.png\", dpi=200)\n# 图题要求：结论写进 caption，例如\n# \"Speed peaks at 183 m/s near 26 km, converging to 40 m/s at ground.\""},
                 {"k": "callout", "text": "三条图规矩回课程二：编号、轴带单位、结论进图题。配色语义全文一致（速度永远蓝色、高度永远红色）。"},
             ]},
            {"t": "验证：步长减半（3 行）", "sub": "金银牌的分水岭——数值结果必须自证可信",
             "body": [
                 {"k": "code", "title": "收敛检验", "text": "def land_speed(dt):\n    # 把主循环包成函数，传入不同步长各跑一遍\n    ...\ns1 = land_speed(0.1)\ns2 = land_speed(0.05)\nprint(s1, s2)   # 若前 4 位相同 → 声称 4 位有效数字"},
                 {"k": "p", "text": "论文里的标准写法（句库原句）：<i>\"Halving the step changes the exit speed in the fifth digit; we therefore claim 4–5 significant figures, worst case 4.\"</i>——再加两个检验：极限情形（令 cda→0 应回到真空抛体）与灵敏度（cda ±20% 扫描）。三件套齐了。"},
             ]},
            {"t": "结课：你已经走完一场迷你比赛", "sub": "建模课给了方程，这门课让它跑起来，论文课教你交出去",
             "body": [
                 {"k": "list", "items": [
                     "练手作业 1：在实验台把 Cd·A 拉到 50（模拟开伞），观察速度骤降——这就是「开伞冲击」的直观感受",
                     "练手作业 2：给代码加「过载 a/9.81」记录，找出最大过载出现的时刻（这正是 2023-A 判据的一部分）",
                     "练手作业 3：把落地速度写进一句英文摘要结论，对照句库检查有没有数字",
                 ]},
                 {"k": "try", "text": "现在去实验台把这三道作业做掉（改滑杆即可开始）", "href": "lab.html", "label": "打开实验台"},
             ]},
        ]},
    }

    # 构建期校验：幻灯内所有 try 链接必须能解析到磁盘文件（相对 12_赛时工具/；
    # 这些链接运行时注入，静态 href 扫描看不到，必须在源头断言）
    for _c in COURSES.values():
        for _s in _c["slides"]:
            for _b in _s["body"]:
                if _b.get("k") == "try":
                    _h = _b["href"]
                    if _h.startswith(("http", "javascript", "#")):
                        continue
                    _t = os.path.normpath(os.path.join(P(ctx, TOOLS_DIR), unquote(_h.split("#")[0])))
                    if not os.path.exists(_t):
                        raise SystemExit(f"tutorial try-link broken: {_h} -> {_t}")

    body = r"""
<nav class="tabs" id="ctabs"></nav>
<div class="card" style="padding:26px 30px 22px;min-height:420px">
  <div id="slide"></div>
</div>
<div style="display:flex;align-items:center;gap:14px;margin-top:14px">
  <button class="btn" id="prev" type="button">← 上一页</button>
  <div style="flex:1;height:6px;background:#EFEADC;border-radius:3px;overflow:hidden">
    <i id="sprog" style="display:block;height:100%;width:0;background:var(--acc);transition:width .25s"></i></div>
  <span class="note" id="snum" style="font-family:var(--mono);font-size:12px;color:var(--dim)"></span>
  <button class="btn solid" id="next" type="button">下一页 →</button>
</div>
<div class="notebox" style="margin-top:14px">三门课贯穿同一道题（2023-A 太空跳伞）：课程一把它变成方程，课程三让它跑起来，课程二教你交出去。键盘 ← → 也能翻页。</div>
"""

    script = r"""
var COURSES=__COURSES__;
var CPCACHE=[];
var cur=null, idx=0;
var tabsEl=document.getElementById('ctabs');
Object.keys(COURSES).forEach(function(k){
  var a=document.createElement('a');a.dataset.c=k;a.textContent=COURSES[k].name+' · '+COURSES[k].tag;
  a.addEventListener('click',function(){pick(k,0);});
  tabsEl.appendChild(a);
});
function esc(s){return escHtml(s);}
function blockHtml(b){
  if(b.k==='p')return '<p class="s-p">'+b.text+'</p>';
  if(b.k==='list')return '<ul class="s-list">'+b.items.map(function(i){return '<li>'+i+'</li>';}).join('')+'</ul>';
  if(b.k==='table'){
    return '<table style="margin:10px 0"><thead><tr>'+b.header.map(function(h){return '<th>'+esc(h)+'</th>';}).join('')+'</tr></thead><tbody>'+
      b.rows.map(function(r){return '<tr>'+r.map(function(c){return '<td>'+c+'</td>';}).join('')+'</tr>';}).join('')+'</tbody></table>';
  }
  if(b.k==='code'){
    CPCACHE.push(b.text);
    return '<div class="s-code"><div class="s-code-h"><span>'+esc(b.title||'')+'</span>'+
      '<button class="btn" data-cpi="'+(CPCACHE.length-1)+'" type="button">复制</button></div>'+
      '<pre><code>'+esc(b.text)+'</code></pre></div>';
  }
  if(b.k==='formula')return '<div class="s-formula">$$'+b.tex+'$$</div>';
  if(b.k==='compare'){
    return '<div class="s-compare"><div class="s-col"><div class="s-col-t">'+b.left.t+'</div>'+b.left.body+'</div>'+
      '<div class="s-col"><div class="s-col-t">'+b.right.t+'</div>'+b.right.body+'</div></div>';
  }
  if(b.k==='callout')return '<div class="notebox" style="margin:12px 0 2px">'+b.text+'</div>';
  if(b.k==='img')return '<figure class="s-fig"><img src="'+b.src+'" loading="lazy" alt="'+esc(b.caption||'')+'">'+(b.caption?'<figcaption>'+esc(b.caption)+'</figcaption>':'')+'</figure>';
  if(b.k==='try')return '<div class="s-try"><a class="btn solid" href="'+b.href+'" target="_blank">'+b.label+' →</a><span style="font-size:12.5px;color:var(--dim)">'+b.text+'</span></div>';
  return '';
}
function katexRender(el){
  if(window.renderMathInElement)renderMathInElement(el,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]});
}
function renderSlide(){
  var C=COURSES[cur], s=C.slides[idx];
  var el=document.getElementById('slide');
  el.innerHTML='<div class="s-kicker">'+esc(C.name)+' · '+esc(C.tag)+'</div>'+
    '<h2 class="s-title">'+esc(s.t)+'</h2>'+(s.sub?'<p class="s-sub">'+esc(s.sub)+'</p>':'')+
    s.body.map(blockHtml).join('');
  document.getElementById('sprog').style.width=((idx+1)/C.slides.length*100)+'%';
  document.getElementById('snum').textContent='第 '+(idx+1)+' / '+C.slides.length+' 页';
  document.getElementById('prev').disabled=(idx===0);
  document.getElementById('next').disabled=(idx===C.slides.length-1);
  katexRender(el);
  el.scrollIntoView({block:'nearest'});
}
function pick(k,i){
  cur=k;idx=i;
  document.querySelectorAll('#ctabs a').forEach(function(a){a.classList.toggle('on',a.dataset.c===k);});
  renderSlide();
}
document.getElementById('prev').addEventListener('click',function(){if(idx>0){idx--;renderSlide();}});
document.getElementById('next').addEventListener('click',function(){var C=COURSES[cur];if(idx<C.slides.length-1){idx++;renderSlide();}});
document.addEventListener('keydown',function(e){
  if(/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName))return;
  if(e.key==='ArrowRight'){document.getElementById('next').click();}
  if(e.key==='ArrowLeft'){document.getElementById('prev').click();}
});
document.getElementById('slide').addEventListener('click',function(ev){
  var b=ev.target.closest('button[data-cpi]');if(!b)return;
  copyText(CPCACHE[+b.dataset.cpi],b);
});
pick('model',0);
window.addEventListener('load',function(){renderSlide();});
"""

    css_extra = r"""
.s-kicker{font-size:11px;letter-spacing:.14em;color:var(--acc);margin-bottom:6px}
.s-title{font-family:var(--serif);font-size:23px;margin:0 0 4px;font-weight:700}
.s-sub{color:var(--mut);font-size:13.5px;margin:0 0 14px}
.s-p{font-size:14.5px;line-height:2}
.s-list{padding-left:1.5em;margin:8px 0;font-size:14px;line-height:2}
.s-list li{margin:3px 0}
.s-code{border:1px solid var(--line);border-radius:4px;overflow:hidden;margin:12px 0}
.s-code-h{display:flex;align-items:center;gap:8px;padding:7px 12px;background:#F8F5EC;font-size:12px;color:var(--dim)}
.s-code-h span{flex:1}
.s-code pre{margin:0;border:none;border-radius:0;background:var(--sheet);font-size:12.8px;line-height:1.8}
.s-formula{background:var(--paper);border:1px dashed var(--line2);border-radius:4px;padding:14px;margin:12px 0;text-align:center;font-size:15px}
.s-compare{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0}
.s-col{border:1px solid var(--line);border-radius:4px;padding:12px 14px;background:var(--paper)}
.s-col-t{font-weight:600;font-size:13px;color:var(--acc);margin-bottom:6px;font-family:var(--serif)}
.s-fig{margin:12px 0;text-align:center}
.s-fig img{max-width:420px;width:100%;border:1px solid var(--line);border-radius:4px}
.s-fig figcaption{font-size:12px;color:var(--dim);margin-top:6px}
.s-try{display:flex;gap:12px;align-items:center;margin-top:14px;flex-wrap:wrap}
@media(max-width:760px){.s-compare{grid-template-columns:1fr}}
"""

    tpl = PAGE_HEAD.replace("__EXTRA_HEAD__",
        '<link rel="stylesheet" href="../09_可视化总览/vendor/katex/katex.min.css">'
        '<script defer src="../09_可视化总览/vendor/katex/katex.min.js"></script>'
        '<script defer src="../09_可视化总览/vendor/katex/contrib/auto-render.min.js"></script>')
    tpl = tpl.replace("*{box-sizing:border-box}", "*{box-sizing:border-box}\n" + css_extra)
    html = (tpl.replace("__TITLE__", "新手课堂 · 从一句话到一篇论文")
              .replace("__CRUMB__", "实战工具 · 平时开放")
              .replace("__DESC__", "UPC 新手课堂：建模、编程、论文三门宝宝级幻灯课，用 2023-A 太空跳伞一道题贯穿，从一句话直觉走到方程、代码与论文。")
              .replace("__LEAD__", "给零经验队伍的入门课：不需要任何基础，跟着三课程走一遍，就等于完整做了一场迷你比赛。键盘 ←→ 翻页；所有代码可复制、公式实时渲染。")
              .replace("__BODY__", body).replace("__SCRIPT__", script)
              .replace("__COURSES__", json.dumps(COURSES, ensure_ascii=False))
              .replace("__HOME__", "../index.html")
              .replace("__EV_START__", str(ctx["ev_start"]))
              .replace("__EV_END__", str(ctx["ev_end"])))
    return html


# ================================================================
# 入口
# ================================================================
def render_tools(ctx):
    print("building tool pages:")
    write_out(ctx, "warroom.html", render_warroom(ctx))
    write_out(ctx, "prompts.html", render_prompts(ctx))
    write_out(ctx, "flashcards.html", render_flashcards(ctx))
    write_out(ctx, "selector.html", render_selector(ctx))
    write_out(ctx, "lab.html", render_lab(ctx))
    write_out(ctx, "tutorial.html", render_tutorial(ctx))
