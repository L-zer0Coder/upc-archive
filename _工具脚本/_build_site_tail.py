# -*- coding: utf-8 -*-
"""_build_site_tail.py — 总览页模板、部署辅助文件与全量链接校验（由 _build_site.py 调用）

设计语言「文献阅读室」：暖纸底 / 墨色字 / 朱砂点缀，衬线标题 + 无衬线正文，
发丝线表格，克制交互。总览页第一个板块即「使用指南」，集中说明全站内容与按钮含义。
"""
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
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%239C3F2E'/%3E%3Ctext x='50' y='70' font-size='58' font-weight='700' text-anchor='middle' fill='%23FDFCF8' font-family='Georgia,serif'%3EU%3C/text%3E%3C/svg%3E">
<style>
:root{
 --paper:#F7F4ED;--sheet:#FDFCF8;--ink:#2A251E;--mut:#6E6557;--dim:#9A9080;
 --line:#E7E0D1;--line2:#D9D0BD;
 --acc:#9C3F2E;--acc-d:#7E3225;--acc-soft:rgba(156,63,46,.07);
 --serif:Georgia,"Times New Roman","Source Han Serif SC","Noto Serif SC","Songti SC","STSong","SimSun",serif;
 --sans:"Segoe UI","PingFang SC","HarmonyOS Sans SC","Microsoft YaHei",system-ui,sans-serif;
 --mono:ui-monospace,"Cascadia Code",Consolas,monospace}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:66px}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.85}
a{color:var(--acc);text-decoration:none}
a:hover{color:var(--acc-d)}
::selection{background:rgba(156,63,46,.16)}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:var(--line2);border-radius:5px;border:2px solid var(--paper)}
.wrap{max-width:1080px;margin:0 auto;padding:0 24px}

/* ---- 顶栏 ---- */
#bar{position:sticky;top:0;z-index:30;background:rgba(253,252,248,.94);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
#bar .in{max-width:1080px;margin:0 auto;display:flex;align-items:center;gap:6px;height:52px;padding:0 24px}
.brand{display:flex;align-items:center;gap:9px;color:var(--ink);font-weight:600;font-size:14px;white-space:nowrap}
.brand:hover{color:var(--ink)}
.brand .seal{width:26px;height:26px;border-radius:5px;background:var(--acc);color:#FDFCF8;display:flex;align-items:center;justify-content:center;font-family:var(--serif);font-size:14px;font-weight:700}
.brand small{color:var(--dim);font-weight:400;font-size:11px;margin-left:2px;letter-spacing:.08em}
#bar nav{display:flex;gap:1px;flex:1;min-width:0;overflow-x:auto;scrollbar-width:none;margin-left:10px}
#bar nav::-webkit-scrollbar{display:none}
#bar nav a{padding:5px 11px;font-size:13px;color:var(--mut);border-radius:3px;white-space:nowrap}
#bar nav a:hover{color:var(--ink);background:rgba(42,37,30,.05)}
#bar nav a.on{color:var(--acc);background:var(--acc-soft)}
.swrap{position:relative;flex-shrink:0;margin-left:auto}
#q{width:196px;height:32px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);color:var(--ink);
 padding:0 30px 0 11px;font-size:13px;outline:none;font-family:inherit;transition:border-color .15s,width .2s}
#q:focus{border-color:var(--acc);width:236px}
#q::placeholder{color:var(--dim)}
.kbd{position:absolute;right:9px;top:50%;transform:translateY(-50%);font-size:10.5px;color:var(--dim);
 border:1px solid var(--line2);border-radius:3px;padding:0 5px;line-height:15px;pointer-events:none;background:var(--sheet)}
#sres{position:absolute;top:38px;right:0;width:400px;max-width:86vw;max-height:62vh;overflow:auto;background:var(--sheet);
 border:1px solid var(--line2);border-radius:4px;box-shadow:0 14px 40px rgba(70,58,38,.16);display:none;z-index:40}
#sres a{display:flex;gap:10px;padding:8px 13px;border-bottom:1px solid var(--line);font-size:13px;color:var(--ink);align-items:baseline}
#sres a:last-child{border:none}
#sres a:hover{background:#F3EEE2}
#sres .d{color:var(--dim);font-size:11px;white-space:nowrap}
@media(max-width:920px){#bar nav{display:none}}

/* ---- 首屏 ---- */
#hero{padding:70px 0 6px}
#hero .kicker{display:flex;align-items:center;gap:10px;color:var(--dim);font-size:12.5px;letter-spacing:.1em;margin-bottom:16px}
#hero .kicker::before{content:"";width:26px;height:1px;background:var(--acc)}
#hero h1{font-family:var(--serif);font-size:clamp(28px,4vw,40px);font-weight:700;line-height:1.4;margin:0 0 14px}
#hero .lead{color:var(--mut);font-size:15.5px;max-width:660px;margin:0}
.stats{display:flex;flex-wrap:wrap;margin:30px 0 0}
.stat{padding:0 26px;margin-right:26px;border-right:1px solid var(--line2)}
.stat:last-child{border-right:none;margin-right:0;padding-right:0}
.stat b{font-family:var(--serif);font-size:26px;font-weight:700;display:block;line-height:1.35;font-variant-numeric:tabular-nums}
.stat span{font-size:12px;color:var(--dim)}
.hero-act{display:flex;gap:10px;margin:28px 0 4px;flex-wrap:wrap;align-items:center}
.btn{display:inline-flex;align-items:center;height:36px;padding:0 18px;border:1px solid var(--line2);border-radius:3px;
 font-size:13.5px;color:var(--ink);background:var(--sheet);transition:.15s}
.btn:hover{border-color:var(--acc);color:var(--acc)}
.btn.solid{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.btn.solid:hover{background:var(--acc-d);color:#FDFCF8}

/* ---- 板块 ---- */
main{padding-bottom:40px}
section{margin:62px 0 0;scroll-margin-top:66px}
.sec-h{border-bottom:1px solid var(--line);padding-bottom:12px;margin-bottom:22px}
h2.st{font-family:var(--serif);font-size:22px;font-weight:700;display:flex;align-items:baseline;gap:12px;margin:0}
h2.st .no{font-family:var(--mono);font-size:11.5px;color:var(--acc);letter-spacing:.08em;font-weight:400}
.lead{color:var(--mut);font-size:13.5px;margin:6px 0 0;max-width:860px}
.svgbox{background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:18px;margin:14px 0}
.svgbox svg{width:100%;height:auto;display:block}
.note{color:var(--dim);font-size:12.5px}
.notebox{border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:0 3px 3px 0;background:var(--sheet);
 padding:12px 16px;color:var(--mut);font-size:13px;margin-top:20px;line-height:1.9}

/* ---- 使用指南 ---- */
.paths{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:2px 0 22px}
.path{border:1px solid var(--line);background:var(--sheet);border-radius:4px;padding:16px 18px}
.path .pn{font-family:var(--serif);color:var(--acc);font-size:19px;font-weight:700;display:block;margin-bottom:4px}
.path b{font-size:14.5px}
.path p{color:var(--mut);font-size:12.8px;margin:6px 0 0;line-height:1.8}
.types{display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));gap:12px}
.type{border:1px solid var(--line);background:var(--sheet);border-radius:4px;padding:15px 17px;display:flex;flex-direction:column;gap:6px;transition:border-color .15s}
.type:hover{border-color:var(--acc)}
a.type b{color:var(--ink)}
.type .tt{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.type b{font-family:var(--serif);font-size:15.5px;font-weight:700}
.type .n{color:var(--dim);font-size:11.5px;font-variant-numeric:tabular-nums;white-space:nowrap}
.type p{color:var(--mut);font-size:12.5px;margin:0;line-height:1.75;flex:1}
.type>a{font-size:12.5px;align-self:flex-start}
.legend{display:flex;flex-wrap:wrap;gap:8px 24px;padding:13px 17px;border:1px dashed var(--line2);border-radius:4px;margin-top:18px}
.lg{font-size:12.5px;color:var(--mut)}
.lg b{color:var(--acc);font-weight:600;margin-right:7px;font-family:var(--mono);font-size:11.5px}

/* ---- 年鉴 ---- */
.yjump{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 16px}
.yjump button{font-family:inherit;font-size:12.5px;min-width:56px;padding:4px 8px;border:1px solid var(--line2);
 background:var(--sheet);border-radius:3px;color:var(--mut);cursor:pointer;font-variant-numeric:tabular-nums;line-height:1.5}
.yjump button i{font-style:normal;display:block;font-size:10px;color:var(--dim)}
.yjump button:hover{border-color:var(--acc);color:var(--acc)}
#yexp{margin-left:auto;border:none;background:none;color:var(--dim);cursor:pointer;font-size:12.5px;
 font-family:inherit;text-decoration:underline dotted;text-underline-offset:3px;padding:4px}
#yexp:hover{color:var(--acc)}
.yr{background:var(--sheet);border:1px solid var(--line);border-radius:4px;margin:8px 0;overflow:hidden;transition:border-color .2s;scroll-margin-top:66px}
.yr:hover,.yr[open]{border-color:var(--line2)}
.yr[open]{border-color:var(--line2)}
.yr>summary{cursor:pointer;min-height:52px;padding:10px 20px;font-size:15px;color:var(--ink);
 display:flex;align-items:center;gap:12px;list-style:none;flex-wrap:wrap}
.yr>summary::-webkit-details-marker{display:none}
.yr>summary:hover{background:#F8F5EC}
.yr[open]>summary{border-bottom:1px solid var(--line)}
.yr>summary .chev{width:15px;height:15px;color:var(--dim);flex-shrink:0;transition:transform .2s;display:inline-flex}
.yr[open]>summary .chev{transform:rotate(90deg)}
.yr>summary .n{font-family:var(--serif);font-variant-numeric:tabular-nums;font-size:16.5px;font-weight:700}
.yr>summary .cnt{margin-left:auto;color:var(--dim);font-size:12px;font-weight:400}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;color:var(--mut);
 background:rgba(42,37,30,.045);border-radius:3px;padding:2px 8px;white-space:nowrap}
.chip::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--dot,var(--dim));flex-shrink:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:16px 18px 18px}
@media(max-width:920px){.grid2{grid-template-columns:1fr}}
.pcard{border:1px solid var(--line);background:var(--sheet);border-radius:4px;padding:16px 18px}
.pcard h4{margin:0 0 4px;font-size:15.5px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-weight:600}
.pcard h4 .cn{font-family:var(--serif);font-weight:700;font-size:16px}
.pcard .en{color:var(--dim);font-size:12px;margin-bottom:8px}
.pcard p{font-size:13px;color:var(--mut);margin:6px 0;line-height:1.8;
 display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.btns{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;align-items:center}
.btn.sm{height:29px;padding:0 12px;font-size:12.5px}
.tlink{font-size:12.5px;color:var(--mut)}
.tlink:hover{color:var(--acc)}
.tlink.off{opacity:.35}
.teams{margin:10px 0 0;font-size:12.5px;color:var(--mut)}
.teams summary{cursor:pointer;color:var(--acc)}
.teams table{margin-top:6px}

/* ---- 表格 ---- */
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border-bottom:1px solid var(--line);padding:9px 12px;text-align:left;vertical-align:top}
th{color:var(--dim);font-weight:600;font-size:11.5px;letter-spacing:.05em;
 position:sticky;top:0;background:var(--sheet);z-index:2;border-bottom:1px solid var(--line2)}
tbody tr:nth-child(2n) td{background:#F8F5EC}
tbody tr:hover td{background:var(--acc-soft)}
.num{font-variant-numeric:tabular-nums;text-align:right;font-family:var(--mono);font-size:12.5px}
.tr-thumb{width:44px;border-radius:2px;border:1px solid var(--line);display:block;transition:transform .15s;
 transform-origin:left center;background:var(--paper);padding:2px}
.tr-thumb:hover{transform:scale(2);box-shadow:0 12px 32px rgba(70,58,38,.25);position:relative;z-index:5}

/* ---- 模型地图 ---- */
.mcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(238px,1fr));gap:12px;margin-top:14px}

/* ---- 论文库 ---- */
.ptools{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
#q2{width:270px;max-width:100%;height:34px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);
 color:var(--ink);padding:0 12px;font-size:13px;outline:none;font-family:inherit}
#q2:focus{border-color:var(--acc)}
#fy{height:34px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);color:var(--mut);
 font-family:inherit;font-size:12.5px;padding:0 8px;outline:none}
.segs{display:flex;border:1px solid var(--line2);border-radius:3px;overflow:hidden}
.segs a{padding:6px 13px;font-size:12.5px;color:var(--mut);cursor:pointer;background:var(--sheet)}
.segs a:hover{color:var(--ink)}
.segs a.on{background:var(--acc);color:#FDFCF8}
.ptable-wrap{background:var(--sheet);border:1px solid var(--line);border-radius:4px;overflow:auto;max-height:72vh}

/* ---- 获奖密码 ---- */
.rules-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 36px}
.rule{display:flex;gap:14px;padding:14px 2px;border-bottom:1px solid var(--line);align-items:flex-start}
.rule-n{font-family:var(--serif);color:var(--acc);font-weight:700;font-size:19px;min-width:28px;line-height:1.5;font-variant-numeric:tabular-nums}
.rule-t{font-weight:600;font-size:14.5px;font-family:var(--serif)}
.rule-d{color:var(--mut);font-size:13.2px;margin-top:2px;line-height:1.8}
.em{color:var(--acc);font-weight:600}

/* ---- 全库文件 ---- */
.libgroup{background:var(--sheet);border:1px solid var(--line);border-radius:4px;margin:8px 0;overflow:hidden}
.libgroup>summary{cursor:pointer;padding:12px 18px;font-weight:600;font-size:14px;display:flex;gap:10px;align-items:center;list-style:none;flex-wrap:wrap}
.libgroup>summary::-webkit-details-marker{display:none}
.libgroup>summary:hover{background:#F8F5EC}
.libgroup>summary .desc{color:var(--dim);font-weight:400;font-size:12px}
.libgroup>summary .n2{margin-left:auto;color:var(--acc);font-size:12px;font-family:var(--mono)}
.libitems{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px;padding:4px 16px 16px}
.libitems a{font-size:12.5px;background:var(--paper);border:1px solid var(--line);border-radius:3px;padding:6px 11px;
 color:var(--mut);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;transition:.15s}
.libitems a:hover{border-color:var(--acc);color:var(--acc)}

/* ---- 其他 ---- */
#top{position:fixed;right:26px;bottom:26px;z-index:30;background:var(--sheet);border:1px solid var(--line2);color:var(--mut);
 border-radius:50%;width:40px;height:40px;font-size:16px;cursor:pointer;opacity:0;pointer-events:none;transition:.2s}
#top.on{opacity:1;pointer-events:auto}
#top:hover{color:var(--acc);border-color:var(--acc)}
#pbar{position:fixed;top:0;left:0;height:2px;width:0;z-index:60;background:var(--acc);transition:width .1s}
footer{margin-top:80px;border-top:1px solid var(--line);text-align:center;color:var(--dim);font-size:12px;padding:30px 20px;line-height:2}
@media(max-width:640px){
 #hero{padding:52px 0 4px}
 #q{width:148px}
 #q:focus{width:170px}
 .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:14px 0}
 .stat{border-right:none;margin-right:0;padding:0 0 12px;border-bottom:1px solid var(--line)}
 .paths,.rules-grid{grid-template-columns:1fr}
 .wrap{padding:0 16px}
 #bar .in{padding:0 16px}
}
</style>
</head>
<body>
<div id="pbar"></div>
<div id="bar"><div class="in">
  <a class="brand" href="#hero"><span class="seal">U</span>UPC 全档案库<small>2010–2025</small></a>
  <nav>
    <a href="#guide">指南</a>
    <a href="#timeline">图谱</a>
    <a href="#years">年鉴</a>
    <a href="#models">模型</a>
    <a href="#papers">论文库</a>
    <a href="#rules">密码</a>
    <a href="#library">全库</a>
  </nav>
  <div class="swrap">
    <input id="q" type="search" placeholder="搜索 __NDOCS__ 份文档…" autocomplete="off">
    <span class="kbd">/</span>
    <div id="sres"></div>
  </div>
</div></div>

<header id="hero">
  <div class="wrap">
    <div class="kicker">University Physics Competition · 第 1–16 届</div>
    <h1>国际大学生物理竞赛全档案库</h1>
    <p class="lead">收录 2010–2025 年全部官方题目与 74 篇金牌论文原件，并为每道题、每篇论文整理了中文深度解读、逐篇赏析与手把手精读教程。</p>
    <div class="stats">
      <div class="stat"><b>16</b><span>届赛事</span></div>
      <div class="stat"><b>32</b><span>道官方题目</span></div>
      <div class="stat"><b>74</b><span>篇金牌论文</span></div>
      <div class="stat"><b>__NDOCS__</b><span>份库内文档</span></div>
    </div>
    <div class="hero-act">
      <a class="btn solid" href="#guide">开始使用</a>
      <a class="btn" href="#papers">金牌论文库</a>
      <a class="btn" href="docs/08_%E7%89%A9%E7%90%86%E6%A8%A1%E5%9E%8B%E7%BB%BC%E8%BF%B0/00_%E6%80%BB%E8%A7%88.html">物理模型综述</a>
    </div>
  </div>
</header>

<main class="wrap">

<section id="guide">
  <div class="sec-h">
    <h2 class="st"><span class="no">01</span>使用指南</h2>
    <p class="lead">这个站里有什么、从哪里开始、每个按钮是什么意思——都在这一节。</p>
  </div>
  <div class="paths">
    <div class="path"><span class="pn">一</span><div><b>备赛，想写出一篇金牌论文</b>
      <p>先读「物理模型综述」打底，再挑 2–3 道对口题看「题目深度解读」，然后对照「论文赏析 + 手把手精读」吃透原文，最后用「模板与工具箱」动笔；「获奖密码」七条可当模拟赛自查表。</p></div></div>
    <div class="path"><span class="pn">二</span><div><b>想研究某一年的某道题</b>
      <p>到「历年赛题」展开该年份：英文原题要点、官方奖牌统计、金牌队伍名单、全部论文的 PDF / 文本 / 赏析 / 精读都在同一张卡片里。</p></div></div>
    <div class="path"><span class="pn">三</span><div><b>只想快速查一份资料</b>
      <p>右上角搜索可直达全部 __NDOCS__ 份文档（快捷键 /）；或在「论文库」按年份、A/B 题、队伍号筛选，一跳直达原件。</p></div></div>
  </div>
  <div class="types" id="types"></div>
  <div class="legend">
    <span class="lg"><b>PDF</b>官方论文原件</span>
    <span class="lg"><b>文本</b>提取的全文文字</span>
    <span class="lg"><b>图页</b>标题页 / 图表页渲染图</span>
    <span class="lg"><b>赏析</b>中文逐篇拆解</span>
    <span class="lg"><b>精读</b>手把手复现教程</span>
  </div>
  <div class="notebox">档案边界：2024 年官方未公开论文 PDF（已收录 15 支金牌队伍名单）；2026 届 11 月开赛、尚未发布；2013 年 611 / 611a 为同文异版，赏析与精读以 611a 为准。数据抓取于 2026-10-24；论文版权归原队伍与 UPC 官方（uphysicsc.com），仅供学习交流。</div>
</section>

<section id="timeline">
  <div class="sec-h">
    <h2 class="st"><span class="no">02</span>十六年赛题物理域图谱</h2>
    <p class="lead">每个圆点 = 一道题（上排 A 题 / 下排 B 题），颜色为主导物理域。UPC 题域经历了"航天·力学为主 → 生物·热学介入 → 电磁·声学·信号处理出圈"的演化。</p>
  </div>
  <div class="svgbox">__TIMELINE__</div>
  <div class="svgbox">__BARS__</div>
</section>

<section id="years">
  <div class="sec-h">
    <h2 class="st"><span class="no">03</span>历年赛题 · 金牌队伍 · 论文</h2>
    <p class="lead">点年份直达，或在下面展开任一年份；每道题附深度解读、官方信息与全部论文入口。</p>
  </div>
  <div class="yjump" id="yjump"><button id="yexp" type="button">全部展开</button></div>
  <div id="years-box"></div>
</section>

<section id="models">
  <div class="sec-h">
    <h2 class="st"><span class="no">04</span>物理模型地图</h2>
    <p class="lead">八大专题覆盖 16 年全部模型，点击色块或下方卡片直达综述（含公式与建模套路）。</p>
  </div>
  <div class="svgbox">__MODEL__</div>
  <div class="mcards" id="modelcards"></div>
</section>

<section id="papers">
  <div class="sec-h">
    <h2 class="st"><span class="no">05</span>金牌论文库（74 篇）</h2>
    <p class="lead">按年份、题别或关键词筛选；「直达」一列可打开赏析、精读与各类原件。</p>
  </div>
  <div class="ptools">
    <input id="q2" type="search" placeholder="筛论文：年份 / 题号 / 队伍号 / 标题关键词…">
    <select id="fy"><option value="">全部年份</option></select>
    <div class="segs" id="fp">
      <a data-v="" class="on">全部</a><a data-v="A">A 题</a><a data-v="B">B 题</a>
    </div>
    <span class="note" id="cnt"></span>
  </div>
  <div class="ptable-wrap">
  <table id="ptable"><thead><tr>
    <th>标题页</th><th>年·题</th><th>题目</th><th>队伍</th><th>论文标题（PDF 首行）</th><th>页</th><th>直达</th>
  </tr></thead><tbody></tbody></table>
  </div>
</section>

<section id="rules">
  <div class="sec-h">
    <h2 class="st"><span class="no">06</span>获奖密码 · 贯穿 16 年的评审不变量</h2>
    <p class="lead">从 74 篇金牌论文中反复验证的七条共性，逐题详解见题目解读，逐篇实证见论文赏析。</p>
  </div>
  <div class="rules-grid">__RULES__</div>
  <p class="note" style="margin-top:14px">一句话：<span class="em">UPC 评的不是答案，是"判据—方程—数值—检验"这条链的完整与诚实。</span></p>
</section>

<section id="library">
  <div class="sec-h">
    <h2 class="st"><span class="no">07</span>全库文件导航</h2>
    <p class="lead">档案库每个目录、每个文件的直达入口（官方页面原件 / 成绩单 / 题目汇总 / 论文文本 / 全部文档页 / 构建脚本）。</p>
  </div>
  <div id="lib-box"></div>
</section>

</main>
<button id="top" aria-label="回到顶部">↑</button>
<footer>UPC 2010–2025 全档案库 · 抓取与多智能体整理于 2026-10-24 · 数据源 uphysicsc.com · 可部署于 GitHub Pages</footer>
<script>
const DATA = __DATA__;
const D = DATA.domains;
// robust scrolling: works even where smooth/window-scroll is flaky (embedded webviews)
function curY(){return window.scrollY||document.documentElement.scrollTop||document.body.scrollTop||0;}
function scrollWin(y,smooth){
  var h=document.documentElement,b=document.body;
  try{window.scrollTo({top:y,behavior:smooth?'smooth':'auto'});}catch(e){try{window.scrollTo(0,y);}catch(_){}}
  function nudge(){
    if(Math.abs(curY()-y)>4){h.scrollTop=y;if(b)b.scrollTop=y;}
    if(Math.abs(curY()-y)>4){
      var m=document.createElement('div');
      m.style.cssText='position:absolute;top:'+y+'px;height:1px;width:1px;pointer-events:none;';
      document.body.appendChild(m);
      m.scrollIntoView({block:'start',behavior:'instant'});
      document.body.removeChild(m);
    }
  }
  setTimeout(nudge,smooth?450:60);
  setTimeout(nudge,smooth?950:130);
  setTimeout(nudge,smooth?1600:200);
}
function jumpTo(el,offset){
  var r=el.getBoundingClientRect();
  scrollWin(Math.max(0,r.top+curY()-(offset==null?16:offset)),true);
}
const CHEV='<svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>';
const chip = (t,c)=>`<span class="chip" style="--dot:${c}">${t}</span>`;
const libByName={}; DATA.lib.forEach(g=>libByName[g.name]=g);
const libCount=k=>(libByName[k]?libByName[k].items.length:0);
function openLib(k){
  const g=document.querySelector('#lib-box .libgroup[data-key="'+k+'"]');
  if(g){g.open=true;setTimeout(()=>jumpTo(g,60),40);}
}

/* ---------- 使用指南：内容类型卡片 ---------- */
const GUIDE=[
 {k:"07_题目解读",t:"题目深度解读",d:"32 道题逐题拆解：物理本质、建模路线图、常见陷阱、金牌思路对比。不知道从哪读起，先看这里。"},
 {k:"05_论文赏析",t:"论文赏析",d:"73 篇金牌论文逐篇中文拆解：建模体系、数学算法、排版图表、可借鉴清单，另有 12 份批次对比表。"},
 {k:"10_论文精读",t:"手把手精读",d:"逐节导读、每张图为什么这样画（附 matplotlib 复现代码）、每个关键公式完整推导、建模决策链。"},
 {k:"08_物理模型综述",t:"物理模型综述",d:"八大专题把 16 年所有题目与论文涉及的物理模型分类汇编，含方法论与数值算法总论。"},
 {k:"11_论文模板与工具",t:"模板与工具箱",d:"LaTeX 模板、8 类图表配方库、写作句库、建模决策树、48 小时作战手册、提交前终检清单。"},
 {k:"02_题目汇总",t:"题目与官方信息",d:"每年英文原题全文、奖牌统计、金牌队伍名单与论文链接清单。"},
 {k:"02_官方成绩单",t:"官方成绩单",d:"各年成绩公告 PDF：金 / 银 / 铜 / Accomplished Competitor 全名单。"},
 {k:"01_官网原始页面",t:"原始档案",d:"官网 17 个年份页 HTML 原件与提取文本；论文 PDF、全文文本、页面渲染图均为一手资料。"},
];
const typesBox=document.getElementById('types');
GUIDE.forEach(g=>{
  const d=document.createElement('div');d.className='type';
  d.innerHTML=`<div class="tt"><b>${g.t}</b><span class="n">${libCount(g.k)} 份</span></div>
    <p>${g.d}</p><a href="#library" data-open="${g.k}">浏览全部 →</a>`;
  typesBox.appendChild(d);
});

/* ---------- 全站锚点：统一平滑跳转 ---------- */
document.addEventListener('click',ev=>{
  const a=ev.target.closest('a[href^="#"]');
  if(!a)return;
  const id=a.getAttribute('href').slice(1);
  const el=id&&document.getElementById(id);
  if(!el)return;
  ev.preventDefault();
  if(a.dataset.open)openLib(a.dataset.open);
  jumpTo(el,60);
});

/* ---------- 年鉴：速跳 chips + 手风琴 ---------- */
const yjump=document.getElementById('yjump');
DATA.years.forEach(y=>{
  const np=y.probs.reduce((s,p)=>s+p.papers.length,0);
  const b=document.createElement('button');b.type='button';
  b.innerHTML=`${y.year}<i>${np} 篇</i>`;
  b.addEventListener('click',()=>{
    const card=document.getElementById('year-'+y.year);
    if(card){card.open=true;setTimeout(()=>jumpTo(card,60),50);}
  });
  yjump.insertBefore(b,document.getElementById('yexp'));
});
const yexp=document.getElementById('yexp');
yexp.addEventListener('click',()=>{
  const anyOpen=!!document.querySelector('#years-box details[open]');
  document.querySelectorAll('#years-box details').forEach(d=>d.open=!anyOpen);
  yexp.textContent=anyOpen?'全部展开':'全部收起';
});
const box=document.getElementById('years-box');
DATA.years.forEach(y=>{
  const d=document.createElement('details');d.className='yr';d.id='year-'+y.year;
  const np=y.probs.reduce((s,p)=>s+p.papers.length,0);
  const chips=y.probs.map(p=>chip(`题${p.prob} ${p.cn}`,D[p.dom].color)).join(' ');
  let inner=`<summary><span class="chev">${CHEV}</span><span class="n">${y.year}</span><span style="display:flex;gap:8px;flex-wrap:wrap">${chips}</span><span class="cnt">${np} 篇论文</span></summary><div class="grid2">`;
  y.probs.forEach(p=>{
    const dm=D[p.dom];
    const papers=p.papers.length?`<table style="margin-top:8px"><thead><tr><th>队伍</th><th>论文（PDF 首行）</th><th>页</th><th>直达</th></tr></thead><tbody>`+
      p.papers.map(pp=>`<tr><td><b>#${pp.team}</b></td><td style="max-width:320px">${pp.title}</td><td class="num">${pp.pages}</td>
        <td><div class="btns"><a class="btn sm solid" href="${pp.ana}">赏析</a>${pp.jd?`<a class="tlink" href="${pp.jd}">精读</a>`:`<span class="tlink off">精读</span>`}<a class="tlink" href="${pp.pdf}">PDF</a><a class="tlink" href="${pp.txt}">文本</a><a class="tlink" href="${pp.pngf}">图页</a></div></td></tr>`).join('')
      +`</tbody></table>`:`<p class="note" style="margin-top:8px">${y.year===2024?'该年官方未公开论文':''}</p>`;
    const teams=p.teams.length?`<details class="teams"><summary>金牌队伍（${p.teams.length}）</summary>
      <table>${p.teams.map(t=>`<tr><td><b>#${t.team}</b></td><td>${t.names}</td><td>${t.institution}</td></tr>`).join('')}</table></details>`:'';
    inner+=`<div class="pcard">
      <h4>${chip(`题${p.prob} · ${dm.name}`,dm.color)} <span class="cn">${p.cn}</span></h4>
      <div class="en">${p.en}</div>
      <p>${p.head}</p>${teams}${papers}
      <div class="btns"><a class="btn sm solid" href="${p.interp}">题目深度解读</a><a class="btn sm" href="${p.summary}">官方信息汇总</a></div>
    </div>`;
  });
  inner+=`</div>`;
  d.innerHTML=inner;box.appendChild(d);
});

/* ---------- 模型地图卡片 ---------- */
const mc=document.getElementById('modelcards');
libByName["08_物理模型综述"].items.forEach(it=>{
  const a=document.createElement('a');a.className='type';a.href=it.u;
  a.innerHTML=`<div class="tt"><b>${it.n.replace('.md','')}</b></div><p>专题综述 · 公式与建模套路</p>`;
  mc.appendChild(a);
});

/* ---------- 全库文件 ---------- */
const lb=document.getElementById('lib-box');
DATA.lib.forEach(g=>{
  const d=document.createElement('details');d.className='libgroup';d.dataset.key=g.name;
  d.innerHTML=`<summary>${g.name}<span class="desc">${g.desc}</span><span class="n2">${g.items.length||'—'}</span></summary>
    <div class="libitems">${g.items.map(it=>`<a href="${it.u}" title="${it.n}">${it.n}</a>`).join('')||'<span class="note" style="padding:0 4px 8px">见「论文库」表格直达</span>'}</div>`;
  lb.appendChild(d);
});

/* ---------- 论文库：筛选 + 表格 ---------- */
const tbody=document.querySelector('#ptable tbody');
const all=[];
DATA.years.forEach(y=>y.probs.forEach(p=>p.papers.forEach(pp=>all.push({y:y.year,prob:p.prob,cn:p.cn,dom:p.dom,...pp}))));
all.sort((a,b)=>a.y-b.y||a.prob.localeCompare(b.prob)||(+a.team)-(+b.team));
const fy=document.getElementById('fy');
DATA.years.forEach(y=>{const o=document.createElement('option');o.value=y.year;o.textContent=y.year+' 年';fy.appendChild(o);});
let probF='';
document.querySelectorAll('#fp a').forEach(a=>a.addEventListener('click',()=>{
  document.querySelectorAll('#fp a').forEach(x=>x.classList.remove('on'));
  a.classList.add('on');probF=a.dataset.v;renderPapers();
}));
function renderPapers(){
  const s=document.getElementById('q2').value.trim().toLowerCase();
  const yv=fy.value;
  const list=all.filter(p=>(!yv||String(p.y)===yv)&&(!probF||p.prob===probF)&&
    (!s||`${p.y} ${p.prob} ${p.team} ${p.cn} ${p.title} ${D[p.dom].name}`.toLowerCase().includes(s)));
  tbody.innerHTML=list.map(p=>`<tr>
    <td><a href="${p.png1}" target="_blank"><img class="tr-thumb" loading="lazy" src="${p.png1}" alt="标题页"></a></td>
    <td>${p.y} 题${p.prob}</td>
    <td style="max-width:180px"><span style="display:inline-flex;align-items:center;gap:6px"><i style="width:7px;height:7px;border-radius:50%;background:${D[p.dom].color};flex-shrink:0"></i>${p.cn}</span></td>
    <td>#${p.team}</td><td style="max-width:400px">${p.title}</td><td class="num">${p.pages}</td>
    <td><div class="btns"><a class="btn sm solid" href="${p.ana}">赏析</a>${p.jd?`<a class="tlink" href="${p.jd}">精读</a>`:`<span class="tlink off">精读</span>`}<a class="tlink" href="${p.pdf}">PDF</a><a class="tlink" href="${p.txt}">文本</a><a class="tlink" href="${p.pngf}">图页</a></div></td>
  </tr>`).join('');
  document.getElementById('cnt').textContent=`${list.length} / ${all.length} 篇`;
}
renderPapers();
document.getElementById('q2').addEventListener('input',renderPapers);
fy.addEventListener('change',renderPapers);

/* ---------- 全站搜索 ---------- */
const q=document.getElementById('q'),res=document.getElementById('sres');
q.addEventListener('input',()=>{
  const s=q.value.trim().toLowerCase();
  if(!s){res.style.display='none';return;}
  const hits=DATA.search.filter(x=>(x.t+x.d).toLowerCase().includes(s)).slice(0,14);
  res.innerHTML=hits.map(h=>`<a href="${h.u}"><span class="d">${h.d}</span><span>${h.t}</span></a>`).join('')||'<a><span class="d">∅</span><span>无结果</span></a>';
  res.style.display='block';
});
document.addEventListener('click',e=>{if(!e.target.closest('.swrap'))res.style.display='none'});

/* ---------- 回顶 / 阅读进度 / 顶栏高亮 ---------- */
const tb=document.getElementById('top');
tb.addEventListener('click',()=>scrollWin(0,true));
addEventListener('scroll',()=>{
  const h=document.documentElement;
  tb.classList.toggle('on',curY()>600);
  document.getElementById('pbar').style.width=((window.scrollY!=null?window.scrollY:h.scrollTop)/(h.scrollHeight-h.clientHeight)*100||0)+'%';
},{passive:true});
const navs=[].slice.call(document.querySelectorAll('#bar nav a'));
const secSpy=new IntersectionObserver(es=>{
  es.forEach(e=>{if(e.isIntersecting){
    navs.forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id));
  }});
},{rootMargin:'-30% 0px -60% 0px'});
document.querySelectorAll('main section[id]').forEach(s=>secSpy.observe(s));
addEventListener('keydown',e=>{
  if(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)){e.preventDefault();q.focus();}
  if(e.key==='Escape'){q.value='';res.style.display='none';q.blur();}
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
