# -*- coding: utf-8 -*-
"""_build_tools.py — 赛时工具页构建器（由 _build_site.py 调用）

生成 12_赛时工具/ 下的交互式工具页。数据在构建期从库内 md 解析注入，
保持「md 是唯一数据源」：改了 手册/checklist/句库 重建即可同步。

  warroom.html   48 小时作战室：思路时间线 / 交互手册 / 交互终检 / 写作句库 / 思路导图 / 速查
（提示词工坊、闪卡、选题助手、实验台由后续 render_* 函数追加）
"""
import os, re, json, glob
import markdown
from urllib.parse import quote

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
    ck_secs, ck_note = parse_checklist(read(ctx, "11_论文模板与工具", "提交前终检checklist.md"))
    sent = parse_sentbank(read(ctx, "11_论文模板与工具", "写作句库.md"))

    links = {
        "decision_tree": doc_url(ctx, "11_论文模板与工具/建模决策树.md"),
        "manual": doc_url(ctx, "11_论文模板与工具/48小时作战手册.md"),
        "sentbank": doc_url(ctx, "11_论文模板与工具/写作句库.md"),
        "recipes": quote("../11_论文模板与工具/图表配方库/matplotlib_recipes.py"),
        "method": doc_url(ctx, "08_物理模型综述/08_方法论与数值算法总论.md"),
        "home_years": "../index.html#years",
        "home_models": "../index.html#models",
        "home_templates": "../index.html#templates",
        "home_papers": "../index.html#papers",
    }
    # T0–T9 每阶段该看的库内入口（速查标签页）
    phase_links = [
        ["home_years|年鉴对照历年两题风格", "decision_tree|建模决策树从 Q1 走"],
        ["decision_tree|去模糊化 Q5", "sentbank|句库·模糊词操作化"],
        ["decision_tree|Q2 基准情形", "sentbank|句库·基准与动机"],
        ["home_models|物理模型地图查套路", "sentbank|句库·建模与假设"],
        ["method|方法论与数值算法总论", "recipes|图表配方库源码"],
        ["decision_tree|Q3 量级表", "method|数值算法速查"],
        ["sentbank|句库·数值方法（收敛声明）", "manual|手册 T6 验证三件套"],
        ["recipes|8 类配方对照补图", "decision_tree|验证先于美化"],
        ["sentbank|句库按部位检索", "home_templates|LaTeX 模板工坊"],
        ["manual|危机预案", "decision_tree|五条主干原则再过一遍"],
    ]

    body = r"""
<nav class="tabs" id="tabs">
  <a data-t="log" class="on">思路时间线</a>
  <a data-t="manual">作战手册</a>
  <a data-t="check">提交终检</a>
  <a data-t="sent">写作句库</a>
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

/* ---------- 思路导图（无依赖径向 SVG） ---------- */
function tryMermaid(n){
  if(!document.querySelector('pre code.language-mermaid'))return;
  if(window.mermaid){
    mermaid.initialize({startOnLoad:false,theme:"neutral",securityLevel:"loose"});
    document.querySelectorAll('pre code.language-mermaid').forEach(function(el){
      var d=document.createElement('div');d.className='mermaid';d.textContent=el.textContent;
      el.parentElement.replaceWith(d);});
    mermaid.run({querySelector:'.mermaid'});
  }else if(n>0){setTimeout(function(){tryMermaid(n-1);},300);}
}
tryMermaid(60);
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

    return page(ctx, "48 小时作战室", "第 17 届赛时工具",
                "UPC 48 小时作战室：思路时间线、交互式作战手册、提交终检清单、写作句库检索、思路导图与阶段速查。",
                "开赛后把这一页钉在屏幕上：随手记思路（自动盖阶段戳）、对照手册推进、句库即查即抄、交卷前过终检。所有数据只存在本浏览器，可导出备份。",
                body.replace("__MANUAL__", manual_html).replace("__CKNOTE__", ck_note),
                script
                .replace("__PHASES__", json.dumps(ctx["phases"], ensure_ascii=False))
                .replace("__CHECKLIST__", json.dumps(ck_secs, ensure_ascii=False))
                .replace("__SENTBANK__", json.dumps(sent, ensure_ascii=False))
                .replace("__LINKS__", json.dumps(links, ensure_ascii=False))
                .replace("__PLINKS__", json.dumps(phase_links, ensure_ascii=False)),
                extra_head='<script defer src="../09_可视化总览/vendor/mermaid/mermaid.min.js"></script>')


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
    return page(ctx, "AI 提示词工坊", "第 17 届赛时工具",
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
    return page(ctx, "物理模型闪卡", "第 17 届赛时工具",
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
    for y, p, cn, tags, style, oneline in PROBS:
        data.append({"y": y, "p": p, "cn": cn, "tags": tags, "style": style,
                     "line": oneline, "u": interp.get((str(y), p), "../index.html#years")})
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
    return page(ctx, "选题助手", "第 17 届赛时工具",
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
    pyodide_head = '<script src="https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js"></script>'
    return page(ctx, "数值实验台", "第 17 届赛时工具",
                "UPC 数值实验台：浏览器里直接运行 Python 物理模型（Pyodide），v1 内置 2023-A 太空跳伞简化模型，参数可调、代码可改。",
                "不用装 Python 也能跑物理：滑杆调参数、代码框改模型，点运行立刻出曲线。示范模型来自 2023-A《近太空跳伞》精读。",
                body, script.replace("__PYSRC__", json.dumps(SKYDIVING_PY)),
                extra_head=pyodide_head)


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
