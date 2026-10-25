# -*- coding: utf-8 -*-
"""_build_site_tail.py — 总览页模板、部署辅助文件与全量链接校验（由 _build_site.py 调用）"""
import os, re, json
from urllib.parse import quote, unquote


def render_index(ctx):
    TIMELINE_SVG, BARS_SVG, MODEL_SVG, RULES_HTML = (ctx[k] for k in
        ("timeline", "bars", "model", "rules"))
    DATA_JS, NDOCS = ctx["data"], ctx["ndocs"]

    INDEX_TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UPC 国际大学生物理竞赛 · 2010–2025 全档案库</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏆</text></svg>">
<style>
:root{
 --bg0:#070a12;--bg1:#0b111e;--bg2:#101828;--bg3:#161f33;
 --line:rgba(151,167,197,.13);--line2:rgba(151,167,197,.28);
 --ink:#e9eef7;--mut:#9aa7bd;--dim:#68748e;
 --acc:#8b9dff;--accS:#6366f1;--cyan:#5eead4;--gold:#e5c07b;--r:14px;
 --mono:"JetBrains Mono","Cascadia Code",Consolas,"SFMono-Regular",monospace}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:78px}
body{margin:0;color:var(--ink);font-family:"Inter","Segoe UI","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
 line-height:1.75;font-size:15px;
 background:radial-gradient(900px 420px at 70% -8%,rgba(99,102,241,.15),transparent 60%),
            radial-gradient(700px 380px at 0% 12%,rgba(94,234,212,.05),transparent 60%),var(--bg0)}
body::before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;
 background-image:linear-gradient(rgba(151,167,197,.045) 1px,transparent 1px),linear-gradient(90deg,rgba(151,167,197,.045) 1px,transparent 1px);
 background-size:44px 44px;-webkit-mask-image:radial-gradient(900px 520px at 60% 0%,#000 25%,transparent 75%);
 mask-image:radial-gradient(900px 520px at 60% 0%,#000 25%,transparent 75%)}
a{color:var(--acc);text-decoration:none} a:hover{color:#c3cdff}
::selection{background:rgba(99,102,241,.35)}
::-webkit-scrollbar{width:9px;height:9px}::-webkit-scrollbar-thumb{background:#232d44;border-radius:6px}
header{max-width:1160px;margin:0 auto;padding:78px 28px 10px;text-align:center}
.pills{display:flex;justify-content:center;gap:8px;margin-bottom:24px;flex-wrap:wrap}
.pill{font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--dim);border:1px solid var(--line);
 border-radius:99px;padding:4px 15px;font-family:var(--mono)}
h1{font-size:clamp(28px,4.6vw,46px);font-weight:700;letter-spacing:-.02em;line-height:1.25;margin:0 0 14px;
 background:linear-gradient(180deg,#fff 30%,#a9b7d8);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{color:var(--mut);font-size:14.5px;margin:0 auto;max-width:660px}
.stats{display:inline-flex;flex-wrap:wrap;justify-content:center;margin:36px 0 10px;border:1px solid var(--line);
 border-radius:var(--r);background:linear-gradient(180deg,rgba(255,255,255,.028),rgba(255,255,255,0));overflow:hidden}
.stat{padding:16px 30px;text-align:center;border-right:1px solid var(--line)}
.stat:last-child{border-right:none}
.stat b{font-family:var(--mono);font-size:25px;font-weight:600;color:#dbe4ff;display:block;font-variant-numeric:tabular-nums}
.stat span{font-size:11.5px;color:var(--dim);letter-spacing:.06em}
nav{position:sticky;top:0;z-index:20;background:rgba(7,10,18,.82);backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
nav .in{max-width:1160px;margin:0 auto;display:flex;gap:2px;padding:8px 20px;flex-wrap:wrap;align-items:center}
nav a.tab{padding:6px 13px;border-radius:9px;font-size:13.5px;color:var(--mut);transition:.15s}
nav a.tab:hover{background:var(--bg3);color:var(--ink)}
.searchwrap{position:relative;margin-left:auto}
#q{background:var(--bg2);border:1px solid var(--line);color:var(--ink);border-radius:99px;padding:7px 16px 7px 34px;
 font-size:13px;width:230px;outline:none;transition:.2s}
#q:focus{border-color:rgba(99,102,241,.55);width:300px}
.searchwrap::before{content:"⌕";position:absolute;left:12px;top:5px;font-size:17px;opacity:.55;color:var(--mut)}
#sres{position:absolute;top:42px;right:0;width:400px;max-height:60vh;overflow:auto;background:var(--bg2);
 border:1px solid var(--line2);border-radius:12px;box-shadow:0 24px 60px rgba(0,0,0,.55);display:none}
#sres a{display:flex;gap:10px;padding:9px 14px;border-bottom:1px solid var(--line);font-size:13px;color:var(--ink)}
#sres a:last-child{border:none} #sres a:hover{background:var(--bg3)}
#sres .d{color:var(--cyan);font-size:10.5px;white-space:nowrap;padding-top:3px;font-family:var(--mono)}
main{max-width:1160px;margin:0 auto;padding:26px 20px 100px}
section{margin:64px 0 56px;scroll-margin-top:78px}
h2.st{display:flex;align-items:baseline;gap:13px;font-size:22px;font-weight:650;letter-spacing:-.01em;margin:0 0 6px}
h2.st .no{font-family:var(--mono);font-size:12px;color:var(--acc);letter-spacing:.12em;font-weight:500}
h2.st::after{content:"";flex:1;height:1px;background:var(--line);align-self:center;margin-left:8px}
.lead{color:var(--mut);font-size:13.5px;margin:4px 0 20px;max-width:840px}
.svgbox{background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,0)),var(--bg2);
 border:1px solid var(--line);border-radius:var(--r);padding:18px;margin:16px 0}
.svgbox svg{width:100%;height:auto;display:block}
.yr{background:var(--bg2);border:1px solid var(--line);border-radius:var(--r);margin:12px 0;overflow:hidden;
 transition:border-color .2s,transform .2s;scroll-margin-top:78px}
.yr:hover{border-color:var(--line2)}
.yr[open]{border-color:var(--line2)}
.yr>summary{cursor:pointer;padding:15px 20px;font-size:15.5px;font-weight:600;display:flex;align-items:center;gap:12px;
 list-style:none;letter-spacing:-.01em}
.yr>summary::-webkit-details-marker{display:none}
.yr>summary .n{font-family:var(--mono);color:var(--acc);font-variant-numeric:tabular-nums;font-size:17px;font-weight:600}
.yr>summary .cnt{margin-left:auto;color:var(--dim);font-size:11.5px;font-weight:400;font-family:var(--mono)}
.chip{font-size:10.5px;padding:2px 9px;border-radius:6px;font-weight:600;white-space:nowrap;letter-spacing:.02em}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:4px 18px 18px}
@media(max-width:920px){.grid2{grid-template-columns:1fr}}
.card{background:var(--bg2);border:1px solid var(--line);border-radius:12px;padding:16px;transition:.18s}
.card:hover{border-color:var(--line2);transform:translateY(-1px)}
.card h4{margin:0 0 6px;font-size:15px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-weight:650}
.card .en{color:var(--dim);font-size:12px;font-style:italic;margin-bottom:8px}
.card p{font-size:13px;color:#c4cfe2;margin:6px 0;white-space:pre-line}
.btns{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}
.btn{font-size:12px;border:1px solid var(--line);border-radius:8px;padding:4px 10px;background:transparent;
 color:var(--mut);transition:.15s;cursor:pointer}
.btn:hover{border-color:var(--line2);color:var(--ink);background:rgba(255,255,255,.035);text-decoration:none}
.btn.hl{background:var(--accS);border-color:transparent;color:#fff;font-weight:600}
.btn.hl:hover{background:#7481f4;color:#fff}
.teams{margin:10px 0 0;font-size:12.3px;color:var(--mut)}
.teams summary{cursor:pointer;color:var(--acc)}
.teams table{margin-top:6px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase}
tr:hover td{background:rgba(255,255,255,.018)}
.tr-thumb{width:62px;border-radius:6px;border:1px solid var(--line);display:block;transition:.2s}
.tr-thumb:hover{transform:scale(2.1) translateY(14px);box-shadow:0 14px 40px rgba(0,0,0,.6);position:relative;z-index:5}
.rule{display:flex;gap:15px;background:linear-gradient(180deg,rgba(255,255,255,.02),rgba(255,255,255,0)),var(--bg2);
 border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:11px 0;align-items:flex-start;transition:.18s}
.rule:hover{border-color:var(--line2)}
.rule-n{border:1px solid var(--line2);color:var(--acc);font-weight:600;border-radius:9px;min-width:32px;height:32px;
 display:flex;align-items:center;justify-content:center;font-size:13.5px;font-family:var(--mono);flex-shrink:0}
.rule-t{font-weight:650;letter-spacing:-.01em}.rule-d{color:var(--mut);font-size:13.5px}
.libgroup{background:var(--bg2);border:1px solid var(--line);border-radius:12px;margin:12px 0;overflow:hidden}
.libgroup>summary{cursor:pointer;padding:13px 18px;font-weight:650;font-size:14.5px;display:flex;gap:10px;align-items:center;list-style:none}
.libgroup>summary::-webkit-details-marker{display:none}
.libgroup>summary .desc{color:var(--dim);font-weight:400;font-size:12px}
.libgroup>summary .n2{margin-left:auto;color:var(--acc);font-size:12px;font-family:var(--mono)}
.libitems{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px;padding:4px 16px 16px}
.libitems a{font-size:12.5px;background:var(--bg1);border:1px solid var(--line);border-radius:8px;padding:7px 11px;
 color:#c4cfe2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;transition:.15s}
.libitems a:hover{border-color:var(--line2);color:var(--ink);background:var(--bg3)}
.note{color:var(--mut);font-size:13px}
#top{position:fixed;right:26px;bottom:26px;z-index:30;background:var(--bg3);border:1px solid var(--line2);color:var(--ink);
 border-radius:12px;width:42px;height:42px;font-size:17px;cursor:pointer;opacity:0;pointer-events:none;transition:.25s}
#top.on{opacity:1;pointer-events:auto}
#top:hover{background:var(--accS);border-color:transparent}
footer{text-align:center;color:var(--dim);font-size:12px;padding:36px 20px;border-top:1px solid var(--line)}
.reveal{opacity:0;transform:translateY(14px);transition:all .6s ease}
.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}}
#pbar{position:fixed;top:0;left:0;height:2px;width:0;z-index:60;background:linear-gradient(90deg,var(--accS),var(--cyan));transition:width .1s}
#sidenav{position:fixed;top:0;left:0;bottom:0;width:244px;z-index:40;background:rgba(9,13,23,.94);backdrop-filter:blur(14px);
 border-right:1px solid var(--line);display:flex;flex-direction:column;padding:16px 0 12px;overflow:hidden}
#sidenav .brand{display:flex;align-items:center;gap:11px;padding:6px 18px 18px;font-weight:700;font-size:14.5px;
 color:var(--ink);text-decoration:none;letter-spacing:-.01em}
#sidenav .brand:hover{text-decoration:none;color:#fff}
#sidenav .brand .logo{width:30px;height:30px;border-radius:9px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
 display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0}
#sidenav .brand small{display:block;font-weight:400;font-size:10px;color:var(--dim);letter-spacing:.14em;font-family:var(--mono)}
#sidenav .scroll{overflow-y:auto;flex:1;padding-bottom:8px}
#sidenav .scroll::-webkit-scrollbar{width:5px}#sidenav .scroll::-webkit-scrollbar-thumb{background:#232d44}
#sidenav .grp{font-size:10px;color:var(--dim);letter-spacing:.22em;padding:16px 20px 6px;font-weight:700;font-family:var(--mono)}
#sidenav a.si{display:flex;align-items:center;gap:10px;padding:7px 18px;color:var(--mut);font-size:13.3px;text-decoration:none;
 border-left:2px solid transparent;transition:.16s;white-space:nowrap;letter-spacing:-.005em}
#sidenav a.si:hover{color:var(--ink);background:rgba(255,255,255,.03)}
#sidenav a.si.on{color:var(--ink);border-left-color:var(--accS);background:linear-gradient(90deg,rgba(99,102,241,.15),transparent);font-weight:600}
#sidenav a.si .ic{width:17px;text-align:center;flex-shrink:0;font-size:13px}
#sidenav .yrs{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;padding:2px 12px}
#sidenav .yrs a{font-size:11.5px;color:var(--mut);text-decoration:none;text-align:center;padding:4.5px 0;border-radius:7px;
 border:1px solid transparent;font-variant-numeric:tabular-nums;transition:.14s;font-family:var(--mono)}
#sidenav .yrs a:hover{color:#fff;border-color:var(--line2);background:var(--bg3)}
#sidenav .yrs a.on{color:#fff;background:rgba(99,102,241,.30);border:1px solid rgba(99,102,241,.55);font-weight:700}
#sidenav .foot{border-top:1px solid var(--line);padding:10px 18px 4px;font-size:10.5px;color:var(--dim);line-height:1.7}
#burger{position:fixed;left:16px;bottom:26px;z-index:45;width:44px;height:44px;border-radius:12px;border:1px solid var(--line2);
 background:rgba(9,13,23,.95);color:var(--ink);font-size:17px;cursor:pointer;display:none}
#burger.on{background:var(--accS);color:#fff;border-color:transparent}
body{transition:margin-left .25s}
@media(min-width:1180px){
 body.side{margin-left:244px}
 #burger{display:none!important}
 #sidenav{transform:none!important}
}
@media(max-width:1179.5px){
 #sidenav{transform:translateX(-100%);transition:transform .25s;z-index:70;box-shadow:20px 0 60px rgba(0,0,0,.5)}
 body.side #sidenav{transform:none}
 #burger{display:block}
 body.side #mask{display:block}
}
#mask{position:fixed;inset:0;background:rgba(4,8,18,.6);z-index:65;display:none}
</style>
</head>
<body>
<div id="pbar"></div>
<button id="burger" onclick="document.body.classList.toggle('side')">☰</button>
<div id="mask" onclick="document.body.classList.remove('side')"></div>
<aside id="sidenav">
  <a class="brand" href="#top" onclick="document.body.classList.remove('side')"><span class="logo">🏆</span><span>UPC 全档案库<small>2010 – 2025</small></span></a>
  <div class="scroll">
    <div class="grp">栏目导航</div>
    <a class="si" href="#timeline"><span class="ic">📊</span>年代图谱</a>
    <a class="si" href="#years"><span class="ic">🗓</span>历年赛题</a>
    <a class="si" href="#models"><span class="ic">🧭</span>模型地图</a>
    <a class="si" href="#library"><span class="ic">🗂</span>全库文件</a>
    <a class="si" href="#papers"><span class="ic">📄</span>论文库</a>
    <a class="si" href="#rules"><span class="ic">🏅</span>获奖密码</a>
    <a class="si" href="#guide"><span class="ic">📖</span>使用指南</a>
    <div class="grp">年份速跳</div>
    <div class="yrs" id="sideyrs"></div>
  </div>
  <div class="foot">按 <b>/</b> 聚焦搜索<br>github.io 可能需代理访问</div>
</aside>
<script>(function(){var f=function(){document.body.classList.toggle('side',innerWidth>=1180)};f();addEventListener('resize',f)})()</script>
<header id="top">
  <div class="pills"><span class="pill">University Physics Competition</span><span class="pill">2010 — 2025</span></div>
  <h1>国际大学生物理竞赛 · 全档案库</h1>
  <p class="sub">uphysicsc.com 官方题目 · 74 篇金牌论文 · 逐篇赏析 · 逐题解读 · 物理模型综述 —— 本页可跳转库内全部文件</p>
  <div class="stats">
    <div class="stat"><b>16</b><span>届赛事</span></div>
    <div class="stat"><b>32</b><span>道官方题目</span></div>
    <div class="stat"><b>74</b><span>篇金牌论文 PDF</span></div>
    <div class="stat"><b>73</b><span>篇论文赏析</span></div>
    <div class="stat"><b>32</b><span>份题目解读</span></div>
    <div class="stat"><b>9</b><span>份模型综述</span></div>
  </div>
</header>
<nav><div class="in">
  <a class="tab" href="#timeline">年代图谱</a><a class="tab" href="#years">历年赛题</a><a class="tab" href="#models">模型地图</a>
  <a class="tab" href="#library">全库文件</a><a class="tab" href="#papers">论文库</a><a class="tab" href="#rules">获奖密码</a><a class="tab" href="#guide">指南</a>
  <div class="searchwrap"><input id="q" type="search" placeholder="搜索 __NDOCS__ 份文档…" autocomplete="off"><div id="sres"></div></div>
</div></nav>
<main>

<section id="timeline" class="reveal">
  <h2 class="st"><span class="no">01</span>十六年赛题物理域图谱</h2>
  <p class="lead">每个圆点 = 一道题（上排 A 题 / 下排 B 题），颜色为主导物理域。UPC 题域经历了"航天·力学为主 → 生物·热学介入 → 电磁·声学·信号处理出圈"的演化。</p>
  <div class="svgbox">__TIMELINE__</div>
  <div class="svgbox">__BARS__</div>
</section>

<section id="years" class="reveal">
  <h2 class="st"><span class="no">02</span>历年赛题 · 金牌队伍 · 论文</h2>
  <p class="lead">展开任一年份：题目要点、双语题名、深度解读、队伍名单、全部论文直达（PDF / 赏析 / 文本 / 标题页 / 图表页）。</p>
  <div id="years-box"></div>
</section>

<section id="models" class="reveal">
  <h2 class="st"><span class="no">03</span>物理模型地图</h2>
  <p class="lead">八大专题覆盖 16 年全部模型。点击色块或下方卡片直达综述（含公式与建模套路）。</p>
  <div class="svgbox">__MODEL__</div>
  <div id="modelcards" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin-top:14px"></div>
</section>

<section id="library" class="reveal">
  <h2 class="st"><span class="no">04</span>全库文件导航</h2>
  <p class="lead">档案库每个目录、每个文件的直达入口（官方页面原件 / 成绩单 / 题目汇总 / 论文文本 / 全部文档页 / 构建脚本）。</p>
  <div id="lib-box"></div>
</section>

<section id="papers" class="reveal">
  <h2 class="st"><span class="no">05</span>金牌论文库（74 篇）</h2>
  <div class="btns" style="margin-bottom:10px"><input id="q2" type="search" placeholder="筛选：年份 / 题号 / 队伍 / 关键词…" style="background:var(--bg2);border:1px solid var(--line);color:var(--ink);border-radius:9px;padding:8px 14px;font-size:13.5px;min-width:280px;outline:none"><span class="note" id="cnt"></span></div>
  <div class="svgbox" style="padding:0;overflow:auto;max-height:72vh">
  <table id="ptable"><thead><tr>
    <th>标题页</th><th>年份/题</th><th>队伍</th><th>论文标题（PDF 首行）</th><th>页数</th><th>直达</th>
  </tr></thead><tbody></tbody></table>
  </div>
</section>

<section id="rules" class="reveal">
  <h2 class="st"><span class="no">06</span>获奖密码 · 贯穿 16 年的评审不变量</h2>
  __RULES__
  <p class="note" style="margin-top:12px">一句话：<b style="color:#cfe0ff">UPC 评的不是答案，是"判据—方程—数值—检验"这条链的完整与诚实。</b>逐题详解见题目解读，逐篇实证见论文赏析。</p>
</section>

<section id="guide" class="reveal">
  <h2 class="st"><span class="no">07</span>使用指南</h2>
  <div class="rule"><div class="rule-n">🎯</div><div><div class="rule-t">备考路径</div>
    <div class="rule-d">① 读《08_物理模型综述 / 08_方法论与数值算法总论》 → ② 挑 2–3 道对口题目读深度解读 → ③ 对照赏析精读论文 PDF 原文 → ④ 用"获奖密码"七条做模拟赛 checklist。</div></div></div>
  <div class="rule"><div class="rule-n">🗂</div><div><div class="rule-t">档案边界</div>
    <div class="rule-d">2024 年官方未公开论文（已收录 15 支金牌队伍名单）；2026 届尚未开赛；2013 年 611 / 611a 为同文异版。数据抓取于 2026-10-24，论文版权归原队伍与 UPC 官方（uphysicsc.com），仅供学习交流。</div></div></div>
</section>

</main>
<button id="top" onclick="scrollTo({top:0,behavior:'smooth'})">↑</button>
<footer>UPC 2010–2025 全档案库 · 抓取与多智能体整理于 2026-10-24 · 数据源 uphysicsc.com · 可部署于 GitHub Pages</footer>
<script>
const DATA = __DATA__;
const D = DATA.domains;
const chip = (t,c)=>`<span class="chip" style="background:${c}1f;color:${c};border:1px solid ${c}42">${t}</span>`;

// years accordion
const box = document.getElementById('years-box');
DATA.years.forEach(y=>{
  const d = document.createElement('details'); d.className='yr'; d.id='year-'+y.year;
  const np = y.probs.reduce((s,p)=>s+p.papers.length,0);
  const chips = y.probs.map(p=>chip(`题${p.prob} ${p.cn}`, D[p.dom].color)).join(' ');
  let inner = `<summary><span class="n">${y.year}</span><span style="display:flex;gap:8px;flex-wrap:wrap">${chips}</span><span class="cnt">${np} 篇论文</span></summary><div class="grid2">`;
  y.probs.forEach(p=>{
    const dm = D[p.dom];
    const papers = p.papers.length? `<table style="margin-top:8px"><thead><tr><th>队伍</th><th>论文（PDF 首行）</th><th>页</th><th>直达</th></tr></thead><tbody>` +
      p.papers.map(pp=>`<tr><td><b>#${pp.team}</b></td><td style="max-width:320px">${pp.title}</td><td>${pp.pages}</td>
        <td><div class="btns"><a class="btn" href="${pp.pdf}">PDF</a><a class="btn hl" href="${pp.ana}">赏析</a><a class="btn" href="${pp.txt}">文本</a><a class="btn" href="${pp.png1}">题图</a><a class="btn" href="${pp.pngf}">图页</a></div></td></tr>`).join('')
      + `</tbody></table>` : `<p class="note" style="margin-top:8px">${y.year===2024?'该年官方未公开论文':''}</p>`;
    const teams = p.teams.length? `<details class="teams"><summary>金牌队伍（${p.teams.length}）</summary>
      <table>${p.teams.map(t=>`<tr><td><b>#${t.team}</b></td><td>${t.names}</td><td>${t.institution}</td></tr>`).join('')}</table></details>`:'';
    inner += `<div class="card">
      <h4>${chip(`题${p.prob} · ${dm.name}`, dm.color)} ${p.cn}</h4>
      <div class="en">${p.en}</div>
      <p>${p.head}</p>${teams}${papers}
      <div class="btns"><a class="btn hl" href="${p.interp}">📑 题目深度解读</a><a class="btn" href="${p.summary}">官方信息汇总</a></div>
    </div>`;
  });
  inner += `</div>`;
  d.innerHTML = inner; box.appendChild(d);
});

// model cards
const mc = document.getElementById('modelcards');
DATA.lib.find(g=>g.name==="08_物理模型综述").items.forEach(it=>{
  const a=document.createElement('a');a.className='card';a.href=it.u;
  a.style.display='block';a.innerHTML=`<b style="color:#cfe0ff">${it.n.replace('.md','')}</b>`;
  mc.appendChild(a);
});

// library groups
const lb = document.getElementById('lib-box');
DATA.lib.forEach(g=>{
  const d=document.createElement('details');d.className='libgroup';
  d.innerHTML=`<summary>📁 ${g.name}<span class="desc">${g.desc}</span><span class="n2">${g.items.length||'—'}</span></summary>
    <div class="libitems">${g.items.map(it=>`<a href="${it.u}" title="${it.n}">${it.n}</a>`).join('')||'<span class="note" style="padding:0 4px 8px">见上方论文库表格与卡片直达</span>'}</div>`;
  lb.appendChild(d);
});

// papers table
const tbody = document.querySelector('#ptable tbody');
const all = [];
DATA.years.forEach(y=>y.probs.forEach(p=>p.papers.forEach(pp=>all.push({y:y.year,prob:p.prob,cn:p.cn,dom:p.dom,...pp}))));
all.sort((a,b)=>a.y-b.y||a.prob.localeCompare(b.prob)||(+a.team)-(+b.team));
function render(list){
  tbody.innerHTML = list.map(p=>`<tr>
    <td><a href="${p.png1}" target="_blank"><img class="tr-thumb" loading="lazy" src="${p.png1}" alt="标题页"></a></td>
    <td>${p.y} 题${p.prob}<br><span style="color:var(--mut);font-size:11px">${D[p.dom].name}</span></td>
    <td>#${p.team}</td><td style="max-width:400px">${p.title}</td><td>${p.pages}</td>
    <td><div class="btns"><a class="btn" href="${p.pdf}">PDF</a><a class="btn hl" href="${p.ana}">赏析</a><a class="btn" href="${p.txt}">文本</a><a class="btn" href="${p.pngf}">图页</a></div></td>
  </tr>`).join('');
  document.getElementById('cnt').textContent = `${list.length} / ${all.length} 篇`;
}
render(all);
document.getElementById('q2').addEventListener('input',e=>{
  const s=e.target.value.trim().toLowerCase();
  render(all.filter(p=>!s||`${p.y} ${p.prob} ${p.team} ${p.cn} ${p.title} ${D[p.dom].name}`.toLowerCase().includes(s)));
});

// global doc search
const q=document.getElementById('q'),res=document.getElementById('sres');
q.addEventListener('input',()=>{
  const s=q.value.trim().toLowerCase();
  if(!s){res.style.display='none';return;}
  const hits=DATA.search.filter(x=>(x.t+x.d).toLowerCase().includes(s)).slice(0,14);
  res.innerHTML=hits.map(h=>`<a href="${h.u}"><span class="d">${h.d}</span><span>${h.t}</span></a>`).join('')||'<a><span class="d">∅</span><span>无结果</span></a>';
  res.style.display='block';
});
document.addEventListener('click',e=>{if(!e.target.closest('.searchwrap'))res.style.display='none'});

// back-to-top + reveal
const tb=document.getElementById('top');
addEventListener('scroll',()=>tb.classList.toggle('on',scrollY>600),{passive:true});
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:0});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
setTimeout(()=>document.querySelectorAll('.reveal:not(.in)').forEach(e=>e.classList.add('in')),2500);

// ---------- sidenav: year grid + scroll-spy + drawer ----------
const sideyrs=document.getElementById('sideyrs');
DATA.years.forEach(y=>{
  const a=document.createElement('a');a.href='#year-'+y.year;a.textContent=y.year;
  a.addEventListener('click',ev=>{
    const card=document.getElementById('year-'+y.year);
    if(card){ card.open=true; ev.preventDefault();
      card.scrollIntoView({behavior:'smooth',block:'start'});
    }
    document.body.classList.remove('side');
  });
  sideyrs.appendChild(a);
});
// section scroll-spy
const sideSecs=[].slice.call(document.querySelectorAll('#sidenav a.si'));
const secSpy=new IntersectionObserver(es=>{
  es.forEach(e=>{ if(e.isIntersecting){
    sideSecs.forEach(a=>a.classList.toggle('on', a.getAttribute('href')==='#'+e.target.id));
  }});
},{rootMargin:'-25% 0px -65% 0px'});
document.querySelectorAll('main section[id]').forEach(s=>secSpy.observe(s));
// year scroll-spy (highlight the year grid as you pass its card)
const yrLinks={}; sideyrs.querySelectorAll('a').forEach(a=>yrLinks[a.getAttribute('href').slice(1)]=a);
const yrSpy=new IntersectionObserver(es=>{
  es.forEach(e=>{ if(e.isIntersecting){
    Object.values(yrLinks).forEach(a=>a.classList.remove('on'));
    yrLinks[e.target.id]&&yrLinks[e.target.id].classList.add('on');
  }});
},{rootMargin:'-20% 0px -70% 0px'});
document.querySelectorAll('details.yr').forEach(c=>yrSpy.observe(c));
// reading progress
addEventListener('scroll',()=>{
  const h=document.documentElement;
  document.getElementById('pbar').style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100||0)+'%';
},{passive:true});
// "/" focuses global search; Esc closes it
addEventListener('keydown',e=>{
  if(e.key==='/'&&!/INPUT|TEXTAREA/.test(document.activeElement.tagName)){e.preventDefault();q.focus();}
  if(e.key==='Escape'){q.value='';res.style.display='none';q.blur();document.body.classList.remove('side');}
});
</script>
</body>
</html>"""

    html = (INDEX_TPL.replace("__TIMELINE__", TIMELINE_SVG)
            .replace("__BARS__", BARS_SVG).replace("__MODEL__", MODEL_SVG)
            .replace("__RULES__", RULES_HTML).replace("__DATA__", DATA_JS)
            .replace("__NDOCS__", str(NDOCS)))
    out = os.path.join(ctx["site"], "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("index written:", len(html) // 1024, "KB")
    return out


def write_deploy_helpers(root, site):
    # .nojekyll（关闭 Jekyll：_ 开头目录也能被服务、部署更快）
    open(os.path.join(root, ".nojekyll"), "w").close()
    # 根 index.html → 跳转到 09_可视化总览/index.html（Pages 首页直达）
    with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><meta charset="utf-8"><title>UPC 全档案库</title>'
                '<meta http-equiv="refresh" content="0;url=09_%E5%8F%AF%E8%A7%86%E5%8C%96%E6%80%BB%E8%A7%88/index.html">'
                '<p>正在进入 <a href="09_%E5%8F%AF%E8%A7%86%E5%8C%96%E6%80%BB%E8%A7%88/index.html">UPC 2010–2025 全档案库总览</a>…</p>')
    # .gitignore 白名单：只提交档案库，不提交 6.6GB 的个人文件
    gi = """# UPC 档案库部署白名单：只上传档案内容，忽略其余个人文件（LaTeX 安装包/视频/课件等）
/*
!/.gitignore
!/.nojekyll
!/index.html
!/README.md
!/01_官网原始页面
!/02_官方成绩单
!/02_题目汇总
!/03_优秀论文PDF
!/04_论文文本
!/05_论文赏析
!/06_论文页面图
!/07_题目解读
!/08_物理模型综述
!/09_可视化总览
!/_工具脚本
__pycache__/
*.pyc
"""
    with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write(gi)
    print("deploy helpers written: .nojekyll / index.html / .gitignore")


def validate(root, site):
    """validate every relative href/src in index.html + all generated doc pages"""
    bad = []
    pages = [os.path.join(site, "index.html")] + [
        os.path.join(dirpath, fn)
        for dirpath, _, files in os.walk(os.path.join(site, "docs")) for fn in files
        if fn.endswith(".html")]
    href_re = re.compile(r'(?:href|src)="([^"]+)"')
    for pg in pages:
        base = os.path.dirname(pg)
        text = open(pg, encoding="utf-8").read()
        for u in href_re.findall(text):
            if re.match(r"^(https?:|data:|#|mailto:)", u) or "${" in u:
                continue
            target = os.path.normpath(os.path.join(base, unquote(u.split("#")[0])))
            if not os.path.exists(target):
                bad.append((os.path.relpath(pg, root), u))
    if bad:
        print(f"VALIDATION FAILED: {len(bad)} broken links")
        for f, u in bad[:40]:
            print("  ", f, "->", u)
        raise SystemExit(1)
    print(f"link validation ok: {len(pages)} pages checked")
