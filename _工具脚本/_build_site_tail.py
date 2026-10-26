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
    TEX_JS, JOURNEY_URL = ctx["tex"], ctx["journey"]

    INDEX_TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UPC 国际大学生物理竞赛 · 2010–2025 全档案库</title>
<meta name="description" content="UPC 国际大学生物理竞赛 2010–2025 全档案库：16 届 32 道官方题目、74 篇金牌论文原件，配中文深度解读、逐篇赏析与手把手精读，外加 LaTeX 模板与 48 小时备赛手册。">
<meta property="og:type" content="website">
<meta property="og:site_name" content="UPC 全档案库">
<meta property="og:title" content="UPC 国际大学生物理竞赛 · 2010–2025 全档案库">
<meta property="og:description" content="16 届 32 道官方题目 + 74 篇金牌论文 + 中文解读、赏析、精读教程与写作模板。">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="#9C3F2E">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%239C3F2E'/%3E%3Ctext x='50' y='70' font-size='58' font-weight='700' text-anchor='middle' fill='%23FDFCF8' font-family='Georgia,serif'%3EU%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='14' fill='%239C3F2E'/%3E%3Ctext x='50' y='70' font-size='58' font-weight='700' text-anchor='middle' fill='%23FDFCF8' font-family='Georgia,serif'%3EU%3C/text%3E%3C/svg%3E">
<style>
:root{
 --paper:#F7F4ED;--sheet:#FDFCF8;--ink:#2A251E;--mut:#6E6557;--dim:#786E60;
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
.brand{display:flex;align-items:center;gap:9px;color:var(--ink);font-weight:600;font-size:14px;white-space:nowrap;min-width:0;overflow:hidden}
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
#sres .sn{display:block;color:var(--dim);font-size:11.5px;margin-top:2px;line-height:1.5;
 overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:340px}
#sres mark{background:rgba(156,63,46,.14);color:var(--acc);padding:0 1px;border-radius:2px}
#sres .hint{padding:10px 13px;color:var(--dim);font-size:12px}
/* ---- 移动端导航：≤920px 收起顶部链接，改用抽屉 ---- */
#mnb{display:none;flex-shrink:0;align-items:center;justify-content:center;width:34px;height:32px;
 border:1px solid var(--line2);border-radius:3px;background:var(--sheet);color:var(--mut);cursor:pointer;padding:0}
#mnb:hover{border-color:var(--acc);color:var(--acc)}
#mnb svg{width:17px;height:17px}
#mdrawer{display:none;position:fixed;top:52px;left:0;right:0;z-index:29;background:var(--sheet);
 border-bottom:1px solid var(--line2);box-shadow:0 14px 34px rgba(70,58,38,.14);padding:6px 18px 12px}
#mdrawer.on{display:block}
#mdrawer a{display:block;padding:11px 4px;font-size:14.5px;color:var(--ink);border-bottom:1px solid var(--line)}
#mdrawer a:last-of-type{border-bottom:none}
#mdrawer .mk{font-family:var(--mono);font-size:11px;color:var(--dim);margin-right:9px}
@media(max-width:920px){
 #bar nav{display:none}
 #mnb{display:inline-flex;margin-left:auto}
 .swrap{margin-left:10px}
 .brand small{display:none}
 #q{width:108px}
 #q:focus{width:128px}
 .kbd{display:none}
}

/* ---- 首屏 ---- */
#hero{padding:70px 0 6px}
#hero .kicker{display:flex;align-items:center;gap:10px;color:var(--dim);font-size:12.5px;letter-spacing:.1em;margin-bottom:16px}
#hero .kicker::before{content:"";width:26px;height:1px;background:var(--acc)}
#hero h1{font-family:var(--serif);font-size:clamp(28px,4vw,40px);font-weight:700;line-height:1.4;margin:0 0 14px;text-wrap:balance}
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

/* ---- 赛事时钟（第 17 届） ---- */
.race{margin:26px 0 4px;border:1px solid var(--line);border-left:3px solid var(--acc);
 border-radius:0 4px 4px 0;background:var(--sheet);padding:15px 20px 17px;scroll-margin-top:70px}
.race[data-state="live"]{border-left-color:#B23A22;
 background:linear-gradient(180deg,rgba(156,63,46,.055),rgba(253,252,248,0) 62%)}
.race[data-state="post"]{border-left-color:var(--line2)}
.race-h{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:11px}
.rpill{font-size:10.5px;letter-spacing:.14em;padding:2px 9px;border-radius:2px;
 background:var(--acc);color:#FDFCF8;white-space:nowrap;font-weight:600}
.race[data-state="pre"] .rpill{background:rgba(156,63,46,.1);color:var(--acc)}
.race[data-state="post"] .rpill{background:rgba(42,37,30,.07);color:var(--mut)}
.rtitle{color:var(--mut);font-size:12.5px}
.race-pre,.race-live,.race-post{display:none}
.race[data-state="pre"] .race-pre,.race[data-state="live"] .race-live,.race[data-state="post"] .race-post{display:block}
.cd{display:flex;align-items:baseline}
.cd-u{display:flex;align-items:baseline;gap:5px;padding:0 15px;border-right:1px solid var(--line2)}
.cd-u:first-child{padding-left:0}
.cd-u:last-child{border-right:none}
.cd b{font-family:var(--serif);font-size:clamp(25px,4vw,34px);font-weight:700;line-height:1.2;
 font-variant-numeric:tabular-nums;letter-spacing:.01em;display:inline-block;min-width:2.2ch}
.cd span{font-size:11.5px;color:var(--dim)}
.race-note{margin:9px 0 0;font-size:12.5px;color:var(--dim)}
.race-note a{color:var(--acc)}
.rl-row{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--dim)}
.rl-row b{font-family:var(--mono);font-size:19px;color:var(--ink);font-variant-numeric:tabular-nums;letter-spacing:.02em}
.rl-row b.hot{color:var(--acc)}
.rl-bar{height:4px;background:#EFEADC;border-radius:2px;overflow:hidden;margin:9px 0 13px}
.rl-bar i{display:block;height:100%;width:0;background:var(--acc);border-radius:2px;transition:width .8s ease}
.race[data-state="live"] .rl-bar i{background:linear-gradient(90deg,var(--acc),#C0503A)}
.rl-phase{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;font-size:12.5px;color:var(--dim)}
.rl-phase b{font-family:var(--serif);font-size:15px;color:var(--ink);font-weight:700}
.rl-next{margin-top:5px;font-size:12px;color:var(--dim)}
.rl-link{margin:11px 0 0;font-size:12.5px;border-top:1px solid var(--line);padding-top:9px}
.race-post p{margin:0;font-size:13px;color:var(--mut)}
@media(max-width:640px){
 .race{padding:13px 15px 15px}
 .cd-u{padding:0 10px;gap:4px}
 .cd b{font-size:24px}
 .rl-row b{font-size:16px}
}

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
.tr-thumb{width:56px;border-radius:2px;border:1px solid var(--line);display:block;transition:transform .15s;
 transform-origin:left center;background:var(--paper);padding:2px}
.tr-thumb:hover{transform:scale(2);box-shadow:0 12px 32px rgba(70,58,38,.25);position:relative;z-index:5}
.col-yq{white-space:nowrap}
#ptable{table-layout:fixed;min-width:920px}
#ptable .btns{gap:6px;flex-wrap:nowrap}
#ptable .btn.sm{padding:0 10px}
#ptable th:nth-child(1),#ptable td:nth-child(1){width:78px}
#ptable th:nth-child(2),#ptable td:nth-child(2){width:126px}
#ptable th:nth-child(3),#ptable td:nth-child(3){width:162px}
#ptable th:nth-child(4),#ptable td:nth-child(4){width:68px}
#ptable th:nth-child(6),#ptable td:nth-child(6){width:44px}
#ptable th:nth-child(7),#ptable td:nth-child(7){width:210px}
.col-cn .dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:6px;vertical-align:1px}
.ttl{display:block;max-width:400px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--mut)}
.dup{display:inline-block;font-size:10.5px;color:var(--dim);border:1px solid var(--line2);border-radius:2px;
 padding:0 4px;margin-left:4px;line-height:1.5;vertical-align:1px}

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

/* ---- 我的打卡 ---- */
.ck-summary{display:flex;gap:28px;align-items:center;background:var(--sheet);border:1px solid var(--line);border-radius:4px;padding:18px 22px;margin-bottom:14px;flex-wrap:wrap}
.ck-big b{font-family:var(--serif);font-size:34px;font-weight:700;color:var(--acc);display:block;line-height:1.25}
.ck-big span{font-size:12px;color:var(--dim)}
.ck-bars{flex:1;min-width:280px;display:grid;gap:9px}
.ck-bar{display:grid;grid-template-columns:140px 1fr 66px;gap:10px;align-items:center;font-size:12.5px;color:var(--mut)}
.ck-bar i{display:block;height:8px;background:#EFEADC;border-radius:4px;overflow:hidden}
.ck-bar em{display:block;height:100%;background:var(--acc);border-radius:4px;width:0;transition:width .4s}
.ck-bar b{font-family:var(--mono);font-size:12px;color:var(--mut);text-align:right;font-variant-numeric:tabular-nums;font-weight:400;white-space:nowrap}
.ck-streak{display:flex;gap:10px;align-items:center}
.ck-streak b{font-family:var(--serif);font-size:30px;font-weight:700;color:var(--ink)}
.ck-streak span{font-size:11.5px;color:var(--dim);line-height:1.5}
.ck-tools{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.ck-grid{display:grid;gap:6px}
.ck-row{display:flex;gap:10px;align-items:flex-start}
.ck-row .y{font-family:var(--mono);font-size:12.5px;color:var(--dim);width:38px;padding-top:5px;flex-shrink:0;font-variant-numeric:tabular-nums}
.ck-cells{display:flex;flex-wrap:wrap;gap:5px}
.ckc{font-family:var(--mono);font-size:12px;min-width:46px;padding:4px 7px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);color:var(--mut);cursor:pointer;font-variant-numeric:tabular-nums;line-height:1.5;text-align:center}
.ckc:hover{border-color:var(--acc);color:var(--acc)}
.ckc.seen{border-color:rgba(156,63,46,.45);color:var(--acc);background:var(--acc-soft)}
.ckc.done{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.ckc.done:hover{background:var(--acc-d);color:#FDFCF8}
.ckc.dim{opacity:.22}
.ck-sep{width:1px;align-self:stretch;background:var(--line2);margin:2px 5px}
.ckc.ic{background:#FAF6EC;border-style:dashed;color:var(--dim);font-size:11px}
.ckc.ic.seen{border-color:rgba(156,63,46,.45);color:var(--acc);background:var(--acc-soft)}
.ckc.ic.done{background:var(--acc);border-color:var(--acc);color:#FDFCF8}
.ck-recent{margin-top:18px;border:1px dashed var(--line2);border-radius:4px;padding:12px 16px}
.ck-recent .tt{font-size:11px;color:var(--dim);letter-spacing:.12em;margin-bottom:6px}
.ck-recent ul{list-style:none;margin:0;padding:0;font-size:12.5px;color:var(--mut)}
.ck-recent li{padding:2px 0;line-height:1.9}
.ck-recent .d{font-family:var(--mono);color:var(--dim);margin-right:10px;font-size:11.5px}

/* ---- 论文模板工坊 ---- */
.tcards{display:grid;grid-template-columns:repeat(auto-fill,minmax(242px,1fr));gap:12px}
.tcard{border:1px solid var(--line);background:var(--sheet);border-radius:4px;padding:16px 18px;display:flex;flex-direction:column;gap:8px;transition:border-color .15s}
.tcard:hover{border-color:var(--acc)}
.tcard .tt{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.tcard b{font-family:var(--serif);font-size:15.5px;font-weight:700}
.tcard .kb{color:var(--dim);font-size:11px;font-family:var(--mono);white-space:nowrap}
.tcard p{color:var(--mut);font-size:12.5px;margin:0;line-height:1.75;flex:1}
.tcard .use{font-size:12px;color:var(--acc)}

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
 #q{width:104px}
 #q:focus{width:122px}
 .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:14px 0}
 .stat{border-right:none;margin-right:0;padding:0 0 12px;border-bottom:1px solid var(--line)}
 .paths,.rules-grid{grid-template-columns:1fr}
 .ck-bar{grid-template-columns:104px 1fr 58px;font-size:11.5px}
 .ck-big b{font-size:26px}
 .wrap{padding:0 16px}
 #bar .in{padding:0 16px}
}
/* ---- 打印：适配 48h 现场打印自查表 ---- */
@media print{
 #bar,#mdrawer,#pbar,#top,.hero-act,.ptools,.ck-tools,#sres{display:none!important}
 body{background:#fff;font-size:11pt;line-height:1.7}
 section{margin:22px 0 0;page-break-inside:auto}
 .yr,.libgroup{page-break-inside:avoid}
 h2.st{page-break-after:avoid}
 a{color:#000;text-decoration:none}
}
</style>
</head>
<body>
<div id="pbar"></div>
<div id="bar"><div class="in">
  <a class="brand" href="#hero"><span class="seal">U</span>UPC 全档案库<small>2010–2025</small></a>
  <nav>
    <a href="#guide">指南</a>
    <a href="#progress">打卡</a>
    <a href="#timeline">图谱</a>
    <a href="#years">年鉴</a>
    <a href="#models">模型</a>
    <a href="#papers">论文库</a>
    <a href="#templates">模板</a>
    <a href="#rules">密码</a>
    <a href="#library">全库</a>
  </nav>
  <button id="mnb" type="button" aria-label="打开导航" aria-expanded="false" aria-controls="mdrawer"><svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 4h12M2 8h12M2 12h12"/></svg></button>
  <div class="swrap">
    <input id="q" type="search" placeholder="搜索 __NDOCS__ 份文档…" autocomplete="off">
    <span class="kbd">/</span>
    <div id="sres"></div>
  </div>
</div></div>
<div id="mdrawer">
  <a href="#guide"><span class="mk">01</span>使用指南</a>
  <a href="#progress"><span class="mk">02</span>我的打卡</a>
  <a href="#timeline"><span class="mk">03</span>赛题图谱</a>
  <a href="#years"><span class="mk">04</span>历年赛题</a>
  <a href="#models"><span class="mk">05</span>模型地图</a>
  <a href="#papers"><span class="mk">06</span>论文库</a>
  <a href="#templates"><span class="mk">07</span>模板工坊</a>
  <a href="#rules"><span class="mk">08</span>获奖密码</a>
  <a href="#library"><span class="mk">09</span>全库文件</a>
</div>

<header id="hero">
  <div class="wrap">
    <div class="kicker">University Physics Competition · 第 1–16 届存档</div>
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
      <a class="btn" href="__MODEL_URL__">物理模型综述</a>
    </div>
    <div class="race" id="race" data-state="pre">
      <div class="race-h">
        <span class="rpill" id="rpill">赛前</span>
        <span class="rtitle" id="rtitle">第 17 届 UPC · 2026.11.07 09:00 开赛（北京时间 UTC+8）</span>
      </div>
      <div class="race-pre">
        <div class="cd">
          <div class="cd-u"><b id="rd">—</b><span>天</span></div>
          <div class="cd-u"><b id="rh">--</b><span>时</span></div>
          <div class="cd-u"><b id="rm">--</b><span>分</span></div>
          <div class="cd-u"><b id="rs">--</b><span>秒</span></div>
        </div>
        <p class="race-note">距开赛。分工还没定？先过一遍 <a href="__MANUAL__">48 小时作战手册</a>。</p>
      </div>
      <div class="race-live">
        <div class="rl-row">
          <span>已用</span><b id="ru">--:--:--</b>
          <span style="margin-left:18px">剩余</span><b id="rr" class="hot">--:--:--</b>
        </div>
        <div class="rl-bar"><i id="rbar"></i></div>
        <div class="rl-phase"><span>当前阶段</span><b id="rpn">—</b><span id="rpd"></span></div>
        <div class="rl-next" id="rnx"></div>
        <p class="rl-link"><a href="__MANUAL__">对照 48 小时作战手册逐阶段执行 →</a></p>
      </div>
      <div class="race-post">
        <p>第 17 届已于 2026 年 11 月 9 日 09:00（北京时间）截止；第 18 届信息待官网公布。</p>
        <p class="race-note">赛后复盘最有效的动作：把本年 A/B 两题与 <a href="#years">历届同域金牌论文</a> 并排放，逐条对「判据—方程—数值—检验」。</p>
      </div>
      <noscript><p class="race-note">2026 年 11 月 7 日 09:00 开赛，11 月 9 日 09:00 截止（北京时间）。</p></noscript>
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

<section id="progress">
  <div class="sec-h">
    <h2 class="st"><span class="no">02</span>我的打卡</h2>
    <p class="lead">点格子 = 手动打卡「已吃透」；打开论文的赏析或精读页停留 3 秒，会自动记为「浏览过」。数据只存在本浏览器，换设备用导出 / 导入搬运。</p>
  </div>
  <div class="ck-summary">
    <div class="ck-big"><b id="ckpct">0%</b><span>论文打卡进度</span></div>
    <div class="ck-bars">
      <div class="ck-bar"><span>金牌论文（73 篇）</span><i><em id="ckbarp"></em></i><b id="ckpnum">—</b></div>
      <div class="ck-bar"><span>题目深度解读（32 篇）</span><i><em id="ckbari"></em></i><b id="ckinum">—</b></div>
    </div>
    <div class="ck-streak"><b id="ckstreak">0</b><span>连续天数<br>（浏览或打卡均计入）</span></div>
  </div>
  <div class="ck-tools">
    <div class="segs" id="ckfilter"><a data-v="all" class="on">全部</a><a data-v="none">未读</a><a data-v="v">浏览过</a><a data-v="d">已打卡</a></div>
    <button class="btn sm" id="ckexport" type="button">导出记录</button>
    <button class="btn sm" id="ckimport" type="button">导入记录</button>
    <input type="file" id="ckfile" accept=".json,application/json" hidden>
    <button class="btn sm" id="ckreset" type="button">清空</button>
  </div>
  <div class="ck-grid" id="ckgrid"></div>
  <div class="legend">
    <span class="lg"><b>○</b>未读</span>
    <span class="lg"><b>◐</b>浏览过（自动）</span>
    <span class="lg"><b>✓</b>已打卡（手动）</span>
    <span class="lg">格子按队伍号标号，悬停看论文；每行末尾的虚线格（如 25A）= 该年 A / B 题深度解读</span>
  </div>
  <div class="ck-recent"><div class="tt">最近动态</div><ul id="ckrecent"></ul></div>
</section>

<section id="timeline">
  <div class="sec-h">
    <h2 class="st"><span class="no">03</span>十六年赛题物理域图谱</h2>
    <p class="lead">每个圆点 = 一道题（上排 A 题 / 下排 B 题），颜色为主导物理域。UPC 题域经历了"航天·力学为主 → 生物·热学介入 → 电磁·声学·信号处理出圈"的演化。</p>
  </div>
  <div class="svgbox">__TIMELINE__</div>
  <div class="svgbox">__BARS__</div>
</section>

<section id="years">
  <div class="sec-h">
    <h2 class="st"><span class="no">04</span>历年赛题 · 金牌队伍 · 论文</h2>
    <p class="lead">点年份直达，或在下面展开任一年份；每道题附深度解读、官方信息与全部论文入口。</p>
  </div>
  <div class="yjump" id="yjump"><button id="yexp" type="button">全部展开</button></div>
  <div id="years-box"></div>
</section>

<section id="models">
  <div class="sec-h">
    <h2 class="st"><span class="no">05</span>物理模型地图</h2>
    <p class="lead">八大专题覆盖 16 年全部模型，点击色块或下方卡片直达综述（含公式与建模套路）。</p>
  </div>
  <div class="svgbox">__MODEL__</div>
  <div class="mcards" id="modelcards"></div>
</section>

<section id="papers">
  <div class="sec-h">
    <h2 class="st"><span class="no">06</span>金牌论文库（74 篇）</h2>
    <p class="lead">按年份、题别或关键词筛选；✓ 标记 = 已打卡，· 标记 = 浏览过。「直达」一列可打开赏析、精读与各类原件。</p>
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

<section id="templates">
  <div class="sec-h">
    <h2 class="st"><span class="no">07</span>论文模板工坊</h2>
    <p class="lead">四套可直接编译的 LaTeX 模板，提炼自 73 篇金牌论文与官方 <code>template.tex</code>；不确定从哪套开始，先读<a href="__JOURNEY__">《一篇金牌论文的完整历程》</a>（拿题 → 交卷全流程）。</p>
  </div>
  <div class="tcards" id="tcards"></div>
  <div class="legend">
    <span class="lg"><b>选型</b>第一次参赛 → 金牌骨架款；要官方同源 → elsarticle 款；图表多 → 双栏款；现场求稳 → 极简款</span>
    <span class="lg"><b>依赖</b>elsarticle 款需要 elsarticle.cls（TeX Live / MiKTeX 均内置）；其余三套零额外依赖</span>
  </div>
</section>

<section id="rules">
  <div class="sec-h">
    <h2 class="st"><span class="no">08</span>获奖密码 · 贯穿 16 年的评审不变量</h2>
    <p class="lead">从 74 篇金牌论文中反复验证的七条共性，逐题详解见题目解读，逐篇实证见论文赏析。</p>
  </div>
  <div class="rules-grid">__RULES__</div>
  <p class="note" style="margin-top:14px">一句话：<span class="em">UPC 评的不是答案，是"判据—方程—数值—检验"这条链的完整与诚实。</span></p>
</section>

<section id="library">
  <div class="sec-h">
    <h2 class="st"><span class="no">09</span>全库文件导航</h2>
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
 {k:"11_论文模板与工具",t:"模板与工具箱",d:"四套 LaTeX 模板、8 类图表配方库、写作句库、建模决策树、48 小时作战手册、终检清单，以及《一篇金牌论文的完整历程》。"},
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

/* ---------- 我的打卡：localStorage 进度 ---------- */
const CKS='upcProgress.v1';
const ckNorm=k=>k.replace(/-611$/,'-611a');
const pkeyOf=f=>{const b=String(f).replace(/\.(pdf|PDF)$/,'');return /-611$/.test(b)?null:ckNorm(b);};  // null = 611 同文异版，归并到 611a
function ckLoad(){try{return JSON.parse(localStorage.getItem(CKS)||'{}')}catch(e){return{}}}
function ckSave(s){try{localStorage.setItem(CKS,JSON.stringify(s))}catch(e){}}
function ckEntry(k,g){const s=ckLoad();return ((g==='paper'?(s.p||{}):(s.i||{}))[k])||{};}
const pmeta={},ckMetaI={};let P_TOTAL=0;
DATA.years.forEach(y=>y.probs.forEach(p=>{
  ckMetaI[y.year+'-'+p.prob]=`${y.year} 题${p.prob} ${p.cn}`;
  p.papers.forEach(pp=>{
    const k=pkeyOf(pp.file);
    if(!k)return;
    if(!pmeta[k])P_TOTAL++;
    pmeta[k]={y:y.year,prob:p.prob,cn:p.cn,team:pp.team};
  });
}));
const I_TOTAL=DATA.years.length*2;
const ckgrid=document.getElementById('ckgrid');
DATA.years.forEach(y=>{
  const cells=[];
  y.probs.forEach(p=>p.papers.forEach(pp=>{
    const k=pkeyOf(pp.file);
    if(!k)return;
    cells.push(`<button type="button" class="ckc" data-k="${k}" data-g="paper" title="${y.year} 题${p.prob} ${p.cn} · #${pp.team} — 点击打卡">${pp.team}</button>`);
  }));
  // 该年 A/B 两道题的深度解读紧跟在论文格子后面，避免单独一行与年份错位
  const icells=y.probs.map(p=>
    `<button type="button" class="ckc ic" data-k="${y.year}-${p.prob}" data-g="interp" title="${y.year} 题${p.prob} ${p.cn} · 深度解读">${String(y.year).slice(2)+p.prob}</button>`).join('');
  const row=document.createElement('div');row.className='ck-row';
  row.innerHTML=`<span class="y">${y.year}</span><div class="ck-cells">${cells.join('')||'<span class="note" style="padding-top:4px">官方未公开论文</span>'}<span class="ck-sep" title="分隔线右侧为深度解读"></span>${icells}</div>`;
  ckgrid.appendChild(row);
});
ckgrid.addEventListener('click',ev=>{
  const b=ev.target.closest('.ckc');if(!b)return;
  const k=b.dataset.k,g=b.dataset.g,s=ckLoad();
  const bag=g==='paper'?(s.p=s.p||{}):(s.i=s.i||{});
  const it=bag[k]||{},now=Date.now();
  if(it.d){delete it.d;(s.log=s.log||[]).unshift({k:k,t:g,s:'u',ts:now});}
  else{it.d=now;if(!it.v)it.v=now;(s.log=s.log||[]).unshift({k:k,t:g,s:'d',ts:now});}
  if(s.log.length>80)s.log.length=80;
  bag[k]=it;ckSave(s);ckRefresh();
});
let ckF='all';
document.querySelectorAll('#ckfilter a').forEach(a=>a.addEventListener('click',()=>{
  document.querySelectorAll('#ckfilter a').forEach(x=>x.classList.remove('on'));
  a.classList.add('on');ckF=a.dataset.v;ckRefresh();
}));
function ckMatch(e){if(ckF==='all')return true;if(ckF==='none')return !e.v&&!e.d;if(ckF==='v')return !!e.v&&!e.d;return !!e.d;}
function ckStreak(s){
  const days=new Set();
  ['p','i'].forEach(g=>{const grp=s[g]||{};Object.values(grp).forEach(e=>{
    if(e.v)days.add(new Date(e.v).toDateString());
    if(e.d)days.add(new Date(e.d).toDateString());});});
  let n=0;const d=new Date();
  if(!days.has(d.toDateString()))d.setDate(d.getDate()-1);
  while(days.has(d.toDateString())){n++;d.setDate(d.getDate()-1);}
  return n;
}
function ckRefresh(){
  const s=ckLoad();
  let pd=0,pv=0,idd=0;
  document.querySelectorAll('.ckc').forEach(b=>{
    const e=ckEntry(b.dataset.k,b.dataset.g);
    const done=!!e.d,seen=!!e.v;
    b.classList.toggle('done',done);
    b.classList.toggle('seen',seen&&!done);
    b.classList.toggle('dim',!ckMatch(e));
    if(b.dataset.g==='paper'){if(done)pd++;else if(seen)pv++;}
    else if(done)idd++;
  });
  const pct=P_TOTAL?Math.round(pd/P_TOTAL*100):0;
  document.getElementById('ckpct').textContent=pct+'%';
  document.getElementById('ckbarp').style.width=pct+'%';
  document.getElementById('ckpnum').textContent=pd+' / '+P_TOTAL+(pv?`（另有 ${pv} 篇浏览过）`:'');
  const ipct=I_TOTAL?Math.round(idd/I_TOTAL*100):0;
  document.getElementById('ckbari').style.width=ipct+'%';
  document.getElementById('ckinum').textContent=idd+' / '+I_TOTAL;
  document.getElementById('ckstreak').textContent=ckStreak(s);
  const ul=document.getElementById('ckrecent');
  ul.innerHTML=((s.log||[]).slice(0,8)).map(ev=>{
    let label=ev.k;
    if(ev.t==='paper'&&pmeta[ev.k]){const m=pmeta[ev.k];label=`${m.y} 题${m.prob}《${m.cn}》#${m.team}`;}
    else if(ev.t==='interp'){label=ckMetaI[ev.k]||ev.k;}
    const verb=ev.s==='d'?'<b class="em">打卡</b>':(ev.s==='u'?'取消打卡':'浏览过');
    const d=new Date(ev.ts);
    return `<li><span class="d">${d.getMonth()+1}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}</span>${verb} ${label}</li>`;
  }).join('')||'<li class="note">还没有记录——去打开一篇论文的赏析或精读页，3 秒后自动记「浏览过」。</li>';
  renderPapers();
}
document.getElementById('ckexport').addEventListener('click',()=>{
  const blob=new Blob([JSON.stringify(ckLoad(),null,1)],{type:'application/json'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download='upc-打卡记录-'+new Date().toISOString().slice(0,10)+'.json';
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href),4000);
});
document.getElementById('ckimport').addEventListener('click',()=>document.getElementById('ckfile').click());
document.getElementById('ckfile').addEventListener('change',ev=>{
  const f=ev.target.files[0];if(!f)return;
  const r=new FileReader();
  r.onload=()=>{try{
    const inc=JSON.parse(r.result),s=ckLoad();
    ['p','i'].forEach(g=>{if(!inc[g])return;s[g]=s[g]||{};
      Object.entries(inc[g]).forEach(([k,e])=>{
        const cur=s[g][k]||{},nx={};
        const mv=Math.max(cur.v||0,e.v||0);if(mv)nx.v=mv;
        const md=Math.max(cur.d||0,e.d||0);if(md)nx.d=md;
        s[g][k]=nx;
      });});
    if(Array.isArray(inc.log))s.log=inc.log.concat(s.log||[]).slice(0,80);
    ckSave(s);ckRefresh();ev.target.value='';
  }catch(err){alert('导入失败：不是有效的打卡记录 JSON');}};
  r.readAsText(f);
});
document.getElementById('ckreset').addEventListener('click',()=>{
  if(!confirm('确定清空全部打卡记录？此操作不可恢复，建议先导出备份。'))return;
  try{localStorage.removeItem(CKS)}catch(e){}
  ckRefresh();
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
  tbody.innerHTML=list.map(p=>{
    const k=pkeyOf(p.file);
    const e=k?ckEntry(k,'paper'):{};
    const mark=e.d?'<b style="color:var(--acc)">✓</b> ':(e.v?'<span style="color:var(--dim)">·</span> ':'');
    return `<tr>
    <td><a href="${p.png1}" target="_blank" rel="noopener"><img class="tr-thumb" loading="lazy" src="${p.png1}" alt="${p.y} 题${p.prob} 队伍 ${p.team} 论文标题页"></a></td>
    <td class="col-yq">${mark}${p.y} 题${p.prob}${/-611\./.test(p.file)?'<span class="dup">同文异版</span>':''}</td>
    <td class="col-cn"><span class="dot" style="background:${D[p.dom].color}"></span>${p.cn}</td>
    <td>#${p.team}</td><td><span class="ttl" title="${p.title.replace(/"/g,'&quot;')}">${p.title}</span></td><td class="num">${p.pages}</td>
    <td><div class="btns"><a class="btn sm solid" href="${p.ana}">赏析</a>${p.jd?`<a class="tlink" href="${p.jd}">精读</a>`:`<span class="tlink off">精读</span>`}<a class="tlink" href="${p.pdf}">PDF</a><a class="tlink" href="${p.txt}">文本</a><a class="tlink" href="${p.pngf}">图页</a></div></td>
  </tr>`;}).join('');
  document.getElementById('cnt').textContent=`${list.length} / ${all.length} 篇`;
}
renderPapers();
document.getElementById('q2').addEventListener('input',renderPapers);
fy.addEventListener('change',renderPapers);

/* ---------- 全站搜索（标题 + 正文全文，索引按需加载） ---------- */
const q=document.getElementById('q'),res=document.getElementById('sres');
let SIDX=null,SLOADING=false,SWAIT=[];
function escHtml(s){return String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function hl(txt,kw){
  const t=escHtml(txt),i=t.toLowerCase().indexOf(kw);
  if(i<0)return t;
  return t.slice(0,i)+'<mark>'+t.slice(i,i+kw.length)+'</mark>'+t.slice(i+kw.length);
}
function snip(txt,kw){
  const i=txt.toLowerCase().indexOf(kw);
  if(i<0)return '';
  const a=Math.max(0,i-22),b=Math.min(txt.length,i+kw.length+46);
  return (a>0?'…':'')+txt.slice(a,b)+(b<txt.length?'…':'');
}
function ensureIdx(){
  return new Promise(ok=>{
    if(SIDX){ok();return;}
    SWAIT.push(ok);
    if(SLOADING)return;
    SLOADING=true;
    res.style.display='block';
    res.innerHTML='<div class="hint">正在载入全文索引…</div>';
    const s=document.createElement('script');
    s.src='search-index.js';
    s.onload=()=>{SIDX=window.UPC_SEARCH||[];SLOADING=false;SWAIT.splice(0).forEach(f=>f());};
    s.onerror=()=>{SIDX=[];SLOADING=false;res.innerHTML='<div class="hint">索引载入失败，刷新页面重试</div>';};
    document.head.appendChild(s);
  });
}
function runSearch(){
  const kw=q.value.trim().toLowerCase();
  if(!kw){res.style.display='none';return;}
  if(SIDX===null)return;
  const hits=[];
  for(const x of SIDX){
    const t=(x.t||'').toLowerCase(),c=(x.c||'').toLowerCase(),d=(x.d||'').toLowerCase();
    let sc=0,cHit=false;
    if(t.indexOf(kw)>=0)sc+=6;
    if(d.indexOf(kw)>=0)sc+=2;
    if(c.indexOf(kw)>=0){sc+=3;cHit=true;}
    if(sc)hits.push({x:x,sc:sc,cHit:cHit});
  }
  hits.sort((a,b)=>b.sc-a.sc||a.x.t.length-b.x.t.length);
  const shown=hits.slice(0,18);
  res.innerHTML=shown.length
    ? shown.map(h=>{
        const s2=h.cHit?snip(h.x.c,kw):'';
        return `<a href="${h.x.u}"><span class="d">${escHtml(h.x.d)}</span><span><span>${hl(h.x.t,kw)}</span>`+
               (s2?`<span class="sn">${hl(s2,kw)}</span>`:'')+`</span></a>`;
      }).join('')+(hits.length>shown.length?`<div class="hint">另有 ${hits.length-shown.length} 条，输入更具体的关键词可缩小范围</div>`:'')
    : `<div class="hint">全库正文中都没有「${escHtml(q.value)}」</div>`;
  res.style.display='block';
}
q.addEventListener('input',()=>{ensureIdx().then(runSearch);});
q.addEventListener('focus',()=>{ensureIdx();});
document.addEventListener('click',e=>{if(!e.target.closest('.swrap'))res.style.display='none'});

/* ---------- 论文模板工坊 ---------- */
const TEX=__TEX__;
const TPLMETA={
 "main.tex":{t:"金牌骨架款",d:"从 73 篇金牌论文提炼的 article 类骨架：一页带数字的摘要、章.序式号、三线表、附录代码，注释里写明每节该写什么、对应哪条获奖密码。",use:"第一次参赛，想直接照着写"},
 "elsarticle.tex":{t:"官方同源款",d:"官方 template.tex（Elsevier elsarticle）的清理版：frontmatter 标题页、匿名规范、elsarticle-num 参考文献，结构与官方示例完全同源。",use:"要官方同源结构 / 习惯 elsarticle"},
 "twocolumn.tex":{t:"双栏紧凑款",d:"10pt 双栏 + 摘要横贯页首，关键宽图用 figure* 跨两栏；信息密度高、评委翻页快。",use:"图表多 / 想压缩页数"},
 "minimal.tex":{t:"极简快启款",d:"只用任何 LaTeX 发行版都自带的宏包，10 分钟起稿零踩坑；先把内容写完，赛前再迁到骨架款精修。",use:"现场求稳 / 环境不确定"}
};
const tc=document.getElementById('tcards');
TEX.forEach(f=>{
  const m=TPLMETA[f.n]||{t:f.n,d:"",use:""};
  const card=document.createElement('div');card.className='tcard';
  card.innerHTML=`<div class="tt"><b>${m.t}</b><span class="kb">${f.kb} KB</span></div>
    <p>${m.d}</p><div class="use">适合：${m.use}</div>
    <div class="btns"><a class="btn sm" href="${f.u}" target="_blank">预览</a>
    <button class="btn sm" data-copy="${f.u}" type="button">复制全文</button>
    <a class="btn sm solid" href="${f.u}" download>下载</a></div>`;
  tc.appendChild(card);
});
tc.addEventListener('click',ev=>{
  const b=ev.target.closest('button[data-copy]');if(!b)return;
  copyTex(b.dataset.copy,b);
});
async function copyTex(u,btn){
  try{
    const r=await fetch(u);if(!r.ok)throw 0;
    const t=await r.text();
    if(navigator.clipboard&&navigator.clipboard.writeText){await navigator.clipboard.writeText(t);}
    else{const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();document.execCommand('copy');ta.remove();}
    btn.textContent='已复制 ✓';setTimeout(()=>{btn.textContent='复制全文';},1600);
  }catch(e){window.open(u,'_blank');}  // file:// 下 fetch 受限时退回打开源码
}

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
/* ---------- 移动端导航抽屉 ---------- */
const mnb=document.getElementById('mnb'),mdl=document.getElementById('mdrawer');
function setDrawer(on){mdl.classList.toggle('on',on);mnb.setAttribute('aria-expanded',on?'true':'false');}
mnb.addEventListener('click',ev=>{ev.stopPropagation();setDrawer(!mdl.classList.contains('on'));});
mdl.addEventListener('click',ev=>{if(ev.target.closest('a'))setDrawer(false);});
document.addEventListener('click',ev=>{if(!ev.target.closest('#mdrawer')&&!ev.target.closest('#mnb'))setDrawer(false);});
addEventListener('scroll',()=>{if(mdl.classList.contains('on'))setDrawer(false);},{passive:true});
addEventListener('keydown',e=>{if(e.key==='Escape'&&mdl.classList.contains('on'))setDrawer(false);});
/* 窄屏搜索框放不下完整占位文案，自动缩短 */
(function(){
  const full=q.getAttribute('placeholder');
  function fit(){const short=window.innerWidth<=920?'搜索全库…':full;
    if(q.getAttribute('placeholder')!==short)q.setAttribute('placeholder',short);}
  fit();addEventListener('resize',fit,{passive:true});
})();
/* ---------- 第 17 届赛事时钟：赛前倒计时 / 赛中计时 + 阶段定位 ---------- */
(function(){
  var S=__EV_START__,E=__EV_END__,P=__PHASES__;
  var root=document.getElementById('race');if(!root)return;
  var pill=document.getElementById('rpill'),title=document.getElementById('rtitle');
  var rd=document.getElementById('rd'),rh=document.getElementById('rh'),
      rm=document.getElementById('rm'),rs=document.getElementById('rs');
  var ru=document.getElementById('ru'),rr=document.getElementById('rr'),
      rbar=document.getElementById('rbar'),rpn=document.getElementById('rpn'),
      rpd=document.getElementById('rpd'),rnx=document.getElementById('rnx');
  function p2(n){return n<10?'0'+n:''+n;}
  function hms(ms){var s=Math.max(0,Math.floor(ms/1000));
    return p2(Math.floor(s/3600))+':'+p2(Math.floor(s%3600/60))+':'+p2(s%60);}
  var last='';
  function tick(){
    var t=Date.now(),st;
    if(t<S)st='pre';else if(t<E)st='live';else st='post';
    if(st!==last){
      last=st;root.dataset.state=st;
      pill.textContent=st==='pre'?'赛前':(st==='live'?'比赛进行中':'已结束');
      title.textContent=st==='pre'?'第 17 届 UPC · 2026.11.07 09:00 开赛（北京时间 UTC+8）'
        :st==='live'?'第 17 届 UPC · 2026.11.09 09:00 截止（北京时间 UTC+8）'
        :'第 17 届 UPC · 2026.11.07 09:00 — 11.09 09:00';
    }
    if(st==='pre'){
      var ms=S-t,d=Math.floor(ms/864e5),h=Math.floor(ms%864e5/36e5),
          m=Math.floor(ms%36e5/6e4),s=Math.floor(ms%6e4/1e3);
      rd.textContent=d;rh.textContent=p2(h);rm.textContent=p2(m);rs.textContent=p2(s);
    }else if(st==='live'){
      var used=t-S,left=E-t;
      ru.textContent=hms(used);rr.textContent=hms(left);
      rbar.style.width=Math.min(100,used/(E-S)*100)+'%';
      var hr=used/36e5,cur=P[0],nx=null;
      for(var i=0;i<P.length;i++){if(hr>=P[i][0]&&hr<P[i][1]){cur=P[i];break;}}
      for(var j=0;j<P.length;j++){if(P[j][0]>hr){nx=P[j];break;}}
      rpn.textContent=cur[2]+' · '+cur[3];
      rpd.textContent='第 '+cur[0]+'–'+cur[1]+' 小时 · 还剩 '+hms(cur[1]*36e5-used);
      rnx.textContent=nx?('下一阶段 '+nx[2]+' · '+nx[3]+'（第 '+nx[0]+' 小时起）· '+nx[4])
                       :'已是最后一个阶段：提前 2 小时交卷。';
    }
  }
  tick();
  var timer=setInterval(tick,1000);
  document.addEventListener('visibilitychange',function(){
    if(document.hidden){clearInterval(timer);timer=0;}
    else{tick();if(!timer)timer=setInterval(tick,1000);}
  });
})();
ckRefresh();
</script>
</body>
</html>"""

    html = (INDEX_TPL.replace("__TIMELINE__", TIMELINE_SVG)
            .replace("__BARS__", BARS_SVG).replace("__MODEL__", MODEL_SVG)
            .replace("__RULES__", RULES_HTML).replace("__DATA__", DATA_JS)
            .replace("__TEX__", TEX_JS).replace("__JOURNEY__", JOURNEY_URL)
            .replace("__MODEL_URL__", ctx.get("model_url", ""))
            .replace("__MANUAL__", ctx.get("manual_url", ""))
            .replace("__EV_START__", str(ctx.get("ev_start", 0)))
            .replace("__EV_END__", str(ctx.get("ev_end", 0)))
            .replace("__PHASES__", ctx.get("phases", "[]"))
            .replace("__NDOCS__", str(NDOCS)))
    out = os.path.join(ctx.get("root") or ctx["site"], "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("index written:", len(html) // 1024, "KB")
    return out


def _repo_base(root):
    """GitHub Pages 项目站点前缀，如 /upc-archive/；解析失败返回 /"""
    try:
        import subprocess
        url = subprocess.run(["git", "-C", root, "config", "--get", "remote.origin.url"],
                             capture_output=True, text=True).stdout.strip()
        m = re.search(r"[/:]([^/:]+)/([^/]+?)(?:\.git)?$", url)
        if m:
            return f"/{m.group(2)}/"
    except Exception:
        pass
    return "/"


def write_deploy_helpers(root, site):
    # .nojekyll（关闭 Jekyll：_ 开头目录也能被服务、部署更快）
    open(os.path.join(root, ".nojekyll"), "w").close()
    # 旧地址兜底：早期分享出去的 /09_可视化总览/index.html 仍可进入（并保留 #锚点）
    with open(os.path.join(site, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><meta charset="utf-8"><title>UPC 全档案库</title>'
                '<meta name="robots" content="noindex">'
                '<meta http-equiv="refresh" content="0;url=../index.html">'
                '<link rel="canonical" href="../index.html">'
                '<script>location.replace("../index.html"+(location.hash||""));</script>'
                '<p>正在进入 <a href="../index.html">UPC 2010–2025 全档案库</a>…</p>')
    # 自定义 404：GitHub Pages 会对任何缺失路径返回它
    base = _repo_base(root)
    with open(os.path.join(root, "404.html"), "w", encoding="utf-8") as f:
        f.write('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>页面不存在 · UPC 全档案库</title><style>'
                'body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;'
                'background:#F7F4ED;color:#2A251E;font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}'
                '.b{max-width:520px;padding:0 28px;text-align:center}'
                '.n{font-family:Georgia,serif;font-size:64px;font-weight:700;color:#9C3F2E;line-height:1;margin:0}'
                'h1{font-family:Georgia,"Songti SC",serif;font-size:22px;margin:18px 0 10px}'
                'p{color:#6E6557;font-size:14px;line-height:1.9;margin:0 0 22px}'
                'a{display:inline-block;padding:0 18px;height:36px;line-height:34px;border:1px solid #D9D0BD;'
                'border-radius:3px;color:#2A251E;text-decoration:none;font-size:13.5px;margin:0 4px;background:#FDFCF8}'
                'a:hover{border-color:#9C3F2E;color:#9C3F2E}'
                '</style></head><body><div class="b"><p class="n">404</p><h1>这一页不在档案库里</h1>'
                '<p>可能是链接拼写有误，或该文档尚未收录。<br>档案库覆盖 2010–2025 共 16 届的全部题目、74 篇金牌论文与解读。</p>'
                f'<a href="{base}">回到总览</a><a href="{base}#papers">金牌论文库</a>'
                '<a href="javascript:history.back()">返回上一页</a></div></body></html>')
    # .gitignore 白名单：只提交档案库，不提交 6.6GB 的个人文件
    gi = """# UPC 档案库部署白名单：只上传档案内容，忽略其余个人文件（LaTeX 安装包/视频/课件等）
/*
!/.gitignore
!/.nojekyll
!/index.html
!/404.html
!/search-index.js
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
!/10_论文精读
!/11_论文模板与工具
!/_工具脚本
__pycache__/
*.pyc
"""
    with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write(gi)
    print("deploy helpers written: .nojekyll / 404.html / legacy index / .gitignore")


# ---------------- 大小写敏感 + git 感知的链接校验 ----------------
def _real_index(root):
    """小写相对路径 -> 磁盘上的真实相对路径（用来发现 Linux 上的大小写 404）"""
    idx = {}
    for dirpath, dirnames, files in os.walk(root):
        if ".git" in dirpath.replace("\\", "/").split("/"):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            continue
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        for fn in files:
            real_rel = (fn if rel_dir == "." else rel_dir + "/" + fn)
            idx.setdefault(real_rel.lower(), real_rel)
    return idx


def _tracked_files(root):
    try:
        import subprocess
        out = subprocess.run(["git", "-C", root, "ls-files", "-z"], capture_output=True)
        if out.returncode != 0:
            return None
        return set(x for x in out.stdout.decode("utf-8", "replace").split("\0") if x)
    except Exception:
        return None


def _check(root, idx, tracked, base_abs, url):
    """返回 (kind, detail)；kind ∈ {"MISSING","CASE","UNTRACKED",None}"""
    dec = unquote(url.split("#")[0].split("?")[0])
    if not dec or dec.startswith("/"):
        return (None, None)   # 站内绝对路径指向仓库根，构建期无法判定，跳过
    abspath = os.path.normpath(os.path.join(base_abs, dec))
    rel = os.path.relpath(abspath, root).replace("\\", "/")
    if rel.startswith("../"):
        return ("MISSING", f"越界路径 {rel}")
    real = idx.get(rel.lower())
    if real is None:
        return ("MISSING", rel)
    if real != rel:
        return ("CASE", f"{rel}  →  实际为 {real}")
    if tracked is not None and real not in tracked:
        return ("UNTRACKED", real)
    return (None, real)


def validate(root, site, extra=()):
    """校验 index.html + 全部文档页的相对链接，外加 DATA 里运行时注入的 URL。

    与旧版的区别：① 大小写敏感（GitHub Pages 跑在 Linux 上）；② 检查文件是否真的
    进了 git（.gitignore 白名单漏掉目录时线上必 404）；③ 覆盖 DATA JSON 里的
    u/pdf/jd/png 等字段，而不只是静态 href/src。
    """
    idx = _real_index(root)
    tracked = _tracked_files(root)
    if tracked is None:
        print("WARN: 无法读取 git 索引，跳过「是否已提交」检查")
    bad = []
    pages = [os.path.join(root, "index.html"), os.path.join(root, "404.html"),
             os.path.join(site, "index.html")] + [
        os.path.join(dirpath, fn)
        for dirpath, _, files in os.walk(os.path.join(site, "docs")) for fn in files
        if fn.endswith(".html")]
    href_re = re.compile(r'(?:href|src)="([^"]+)"')
    for pg in pages:
        base = os.path.dirname(pg)
        text = open(pg, encoding="utf-8").read()
        for u in href_re.findall(text):
            if re.match(r"^(https?:|data:|#|mailto:|javascript:)", u) or "${" in u:
                continue
            kind, detail = _check(root, idx, tracked, base, u)
            if kind:
                bad.append((kind, os.path.relpath(pg, root), detail))
    for base_abs, url, label in extra:
        kind, detail = _check(root, idx, tracked, base_abs, url)
        if kind:
            bad.append((kind, label, detail))
    if bad:
        from collections import Counter
        c = Counter(k for k, _, _ in bad)
        print(f"VALIDATION FAILED: {len(bad)} broken links "
              f"(MISSING={c['MISSING']} CASE={c['CASE']} UNTRACKED={c['UNTRACKED']})")
        for k, f, u in bad[:40]:
            print(f"   [{k}] {f} -> {u}")
        raise SystemExit(1)
    print(f"link validation ok: {len(pages)} pages + {len(extra)} runtime urls "
          f"(case-sensitive, git-aware)")
