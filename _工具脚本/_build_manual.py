# -*- coding: utf-8 -*-
"""_build_manual.py — 全站说明书 + 树状便捷导航（manual.html）
树由构建期扫描档案目录自动生成（蓝图规定禁止手工维护树结构）；
说明书正文为静态撰写。由 _build_tools.render_tools 调用期导入。"""
import os, re, json, glob, posixpath
from urllib.parse import quote

from _build_tools import page, write_out, P

BS = chr(92)
BT = chr(96)

DOC_ROOTS = {"README.md", "02_题目汇总", "05_论文赏析", "07_题目解读",
             "08_物理模型综述", "10_论文精读", "11_论文模板与工具"}
RAW_KEEP = {".pdf", ".png", ".txt"}
SKIP_NAMES = {"_parsed.json", "_批次对比说明.md"}
DIR_DESC = {
    "01_官网原始页面": "官网 17 个年份页的 HTML 原件、提取文本与 PDF 链接清单（一手资料）",
    "02_官方成绩单": "各年官方成绩公告 PDF（金银铜全名单）",
    "02_题目汇总": "每年《题目与官方信息》+ 官方《比赛规则》中文导读",
    "03_优秀论文PDF": "74 篇金牌论文 PDF 原件（按年/题存放）",
    "04_论文文本": "74 篇论文的全文提取文本（检索与解析的数据源）",
    "05_论文赏析": "73 篇逐篇赏析（建模/算法/排版/获奖密码）+ 12 份批次对比",
    "06_论文页面图": "每篇论文的标题页与图表最密页渲染图",
    "07_题目解读": "32 道题深度解读 + 9 张零基础起步卡",
    "08_物理模型综述": "八大物理域综述 + 方法论总论",
    "10_论文精读": "73 篇手把手精读（逐节/逐图/逐式）",
    "11_论文模板与工具": "LaTeX 模板、配方库、句库、润色库、提示词包、手册、终检",
    "12_赛时工具": "八个实战工具页（本目录）",
    "_知识提炼": "模式卡片提炼管线（原料→卡片→聚合知识库）",
    "_工具脚本": "构建/体检/提炼/同步全流程脚本",
}
ROOT_DESC = {
    "index.html": ("站点首页", "四大访客入口 + 十大板块 + 全局搜索"),
    "404.html": ("404 页", "自定义兜底页"),
    "search-index.js": ("全文搜索索引", "235 份文档的正文索引（懒加载）"),
    "og-image.png": ("社交分享卡", "og:image 用的品牌图"),
    "网站蓝图与巡检标准.md": None,  # 在 _工具脚本 下，不出现
}


def rel_url(ctx, rel):
    """manual.html（位于 12_赛时工具/）到仓库根下某文件的 URL；无法服务返回 None"""
    rel = rel.replace(BS, "/")
    if rel.startswith("_知识提炼") or rel.startswith("_工具脚本") or rel.startswith("."):
        return None
    if rel.endswith(".md"):
        target = P(ctx, rel)
        if os.path.exists(target[:-3] + ".html"):
            return quote("../09_可视化总览/docs/" + rel[:-3] + ".html")
        return None
    if os.path.splitext(rel)[1].lower() in RAW_KEEP:
        return quote("../" + rel)
    if rel in ("index.html", "404.html", "og-image.png"):
        return quote("../" + rel)
    return None


def tree_node(ctx, abspath, rel, depth, maxdepth):
    name = os.path.basename(rel) or rel
    node = {"n": name}
    if os.path.isfile(abspath):
        ext = os.path.splitext(name)[1].lower()
        if ext in SKIP_EXT or name.startswith("_parsed") or name in SKIP_NAMES:
            return None
        node["u"] = rel_url(ctx, rel)
        if name == "README.md" and rel == "README.md":
            node["d"] = "总导航（内容详见本页说明书）"
        return node
    if depth >= maxdepth:
        return None
    desc = DIR_DESC.get(rel)
    if desc:
        node["d"] = desc
    kids = []
    try:
        entries = sorted(os.listdir(abspath))
    except OSError:
        return None
    for e in entries:
        child = tree_node(ctx, os.path.join(abspath, e), posixpath.join(rel, e), depth + 1, maxdepth)
        if child:
            kids.append(child)
    if not kids:
        return None
    node["ch"] = kids
    return node


SKIP_EXT = {".pyc", ".log", ".json"}  # json：_meta/parsed 为内部数据；卡片 JSON 在说明书里以链接代替
SKIP_EXT |= {".json"}



def _count_links(n):
    c = 1 if n.get("u") else 0
    for ch in n.get("ch", []):
        c += _count_links(ch)
    return c

def build_tree(ctx):
    root_children = []
    for d in ["01_官网原始页面", "02_官方成绩单", "02_题目汇总", "03_优秀论文PDF",
              "04_论文文本", "05_论文赏析", "06_论文页面图", "07_题目解读",
              "08_物理模型综述", "10_论文精读", "11_论文模板与工具", "12_赛时工具"]:
        n = tree_node(ctx, P(ctx, d), d, 0, 4)
        if n:
            root_children.append(n)
    for d in ["_知识提炼", "_工具脚本"]:
        n = tree_node(ctx, P(ctx, d), d, 0, 3)
        if n:
            root_children.append(n)
    for rf in ["index.html", "404.html", "search-index.js", "og-image.png"]:
        n = tree_node(ctx, P(ctx, rf), rf, 0, 0)
        if n:
            root_children.append(n)
    for n in root_children:
        n["cnt"] = _count_links(n)
    # 补充：工具页（12_ 下已在扫描中）+ 根 README
    rm = tree_node(ctx, P(ctx, "README.md"), "README.md", 0, 0)
    if rm:
        rm["d"] = "仓库总导航（本页说明书的压缩版）"
        root_children.insert(0, rm)
    for n in root_children:
        n["cnt"] = _count_links(n)
    return {"n": "UPC 档案库", "ch": root_children, "cnt": sum(n["cnt"] for n in root_children)}


css_tree = (".tn{line-height:2;font-size:13px}" + chr(10)
    + ".tn a{color:var(--acc)}" + chr(10)
    + ".tn a:hover{text-decoration:underline;text-underline-offset:3px}" + chr(10)
    + ".tn .caret{width:18px;height:18px;border:none;background:none;color:var(--mut);cursor:pointer;font-family:var(--mono);padding:0;margin-right:4px}" + chr(10)
    + ".tn .caret:hover{color:var(--acc)}" + chr(10)
    + ".tn .leafdot{color:var(--line2);margin:0 6px 0 10px}" + chr(10)
    + ".kids{border-left:1px dashed var(--line2);margin-left:9px}")

def render_manual(ctx):
    TREE = build_tree(ctx)
    n_files = json.dumps(TREE).count('"u":')

    body = r"""
<nav class="tabs" id="mtabs">
  <a data-t="tree" class="on">树状导航</a>
  <a data-t="doc">全站说明书</a>
</nav>

<section class="pane on" id="pane-tree">
  <div style="margin-bottom:10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <input id="tq" type="search" placeholder="过滤节点（输入即筛，自动展开祖先）…"
      style="flex:1;min-width:240px;max-width:460px;height:32px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);padding:0 10px;font-size:13px;outline:none">
    <button class="btn" id="tall" type="button">全部展开</button>
  </div>
  <div class="card" style="max-height:70vh;overflow:auto"><div id="tree"></div></div>
  <div class="notebox" style="margin-top:12px">树由构建期扫描档案目录自动生成（不是手工维护）。<b>下划线目录</b>（_知识提炼/_工具脚本）是生产管线不对外服务；01–12 目录与根文件均可点击跳转。页数统计：共 <span id="tcount"></span> 个可点击节点。</div>
</section>

<section class="pane" id="pane-doc">
__MANUAL__
</section>
"""

    manual = r"""
<h2>一、这个网站是什么</h2>
<p>UPC（国际大学生物理竞赛）2010–2025 全档案库：16 届、32 道官方题目、74 篇金牌论文原件，配中文深度解读、逐篇赏析、手把手精读、模型综述，外加八个实战工具页。四类访客四条路线：<b>新手</b>走新手课堂→起步卡；<b>备赛者</b>走解读→赏析/精读→综述/闪卡→模板句库；<b>赛时队伍</b>住在作战室；<b>查阅者</b>用搜索/论文库/全库导航。</p>

<h2>二、首页十大板块</h2>
<table>
<tr><th>板块</th><th>是什么</th><th>怎么用</th></tr>
<tr><td>赛事时钟</td><td>第 17 届三态时钟（赛前/赛中/赛后），赛中自动落到 T0–T9 阶段</td><td>开赛前后各看一次；赛中显示当前阶段与剩余时间</td></tr>
<tr><td>使用指南</td><td>三条读者路径 + 九类内容卡片 + 按钮图例</td><td>第一次来从这里开始</td></tr>
<tr><td>我的打卡</td><td>73 论文 + 32 解读的进度系统（浏览自动记/手动打卡）</td><td>点格子打卡；数据存本浏览器，可导出导入</td></tr>
<tr><td>赛题图谱</td><td>16 年物理域散点图 + 金牌论文数柱状图</td><td>看题目演化趋势</td></tr>
<tr><td>历年赛题</td><td>每年手风琴卡：原题要点/奖牌统计/金牌队伍/全部论文直达</td><td>按年查阅，点年份按钮速跳</td></tr>
<tr><td>模型地图</td><td>八大物理域辐射图 + 专题卡</td><td>按域找综述</td></tr>
<tr><td>论文库</td><td>74 篇可筛选表格（标题页缩略图/直达按钮）</td><td>按年份/题别/关键词筛</td></tr>
<tr><td>模板工坊</td><td>四套可编译 LaTeX 模板</td><td>预览/复制/下载</td></tr>
<tr><td>获奖密码</td><td>七条评审不变量</td><td>当模拟赛自查表</td></tr>
<tr><td>全库文件</td><td>每个目录每个文件的直达入口</td><td>找具体文件时用</td></tr>
</table>
<p>全局功能：<b>搜索</b>（右上角，快捷键 /，首页与每个文档页顶栏都有）、<b>移动端抽屉</b>（≤920px 顶栏汉堡）、<b>回到顶部</b>。</p>

<h2>三、工具页（12_赛时工具/，共八个）</h2>
<table>
<tr><th>页面</th><th>定位</th><th>核心功能</th></tr>
<tr><td><a href="tutorial.html">新手课堂</a></td><td>零基础三门课</td><td>建模/编程/论文各 7 页幻灯，同一道跳伞题贯穿；键盘翻页、代码可复制</td></tr>
<tr><td><a href="warroom.html">48 小时作战室</a></td><td>赛时主控台</td><td>思路时间线（自动盖 T0–T9 阶段戳）/ 交互手册 / 提交终检（30 项）/ 句库检索 / 中译英润色 / 思路导图 / 阶段速查，共 7 标签</td></tr>
<tr><td><a href="xray.html">论文透视</a></td><td>跨论文横向分析</td><td>同题对比矩阵（16 组多金牌题 ×6 维）/ 结构图谱（74 篇章节体量条带）/ 摘要解剖室（68 篇逐句功能标注）</td></tr>
<tr><td><a href="flashcards.html">模型闪卡</a></td><td>模型自测</td><td>49 张翻卡（场景/方程/要点/易错），掌握进度本地保存</td></tr>
<tr><td><a href="selector.html">选题助手</a></td><td>开赛选题</td><td>强项勾选匹配 + 粘贴 2026 新题原文的关键词匹配</td></tr>
<tr><td><a href="prompts.html">提示词工坊</a><b>（含总指挥）</b></td><td>AI 协作入口</td><td>0 号「总指挥·全程完赛」主控提示词（GPT/Codex 与 DeepSeek 接入卡）+ 11 条分任务提示词，一键复制</td></tr>
<tr><td><a href="lab.html">数值实验台</a></td><td>浏览器跑 Python</td><td>2023-A 跳伞模型：滑杆改参、代码可改、即时出图（Pyodide 按需加载）</td></tr>
<tr><td><a href="forge.html">论文组装机</a></td><td>成稿排版</td><td>把你的判据/方程/结果组装成完整 LaTeX 初稿（空白留 TODO），配总指挥提示词使用</td></tr>
</table>

<h2>四、内容层（01–11 目录）</h2>
<table>
<tr><th>目录</th><th>规模</th><th>建议读法</th></tr>
<tr><td>02_题目汇总</td><td>17 份 + 规则</td><td>查题面/奖牌统计/金牌队伍；《比赛规则》有一分钟合规卡</td></tr>
<tr><td>05_论文赏析</td><td>73 篇 + 12 批次表</td><td>每篇六节：速览/建模拆解/算法/图表/获奖密码/可借鉴清单</td></tr>
<tr><td>07_题目解读</td><td>32 篇 + 9 起步卡</td><td>每题：物理本质/路线图/陷阱/金牌思路对比；起步卡给零基础五层路线</td></tr>
<tr><td>08_物理模型综述</td><td>9 篇</td><td>按域通读；00 总览有「按骨架查」</td></tr>
<tr><td>10_论文精读</td><td>73 篇</td><td>逐节导读/每图复现代码/每式推导/决策链——吃透一篇的最快路径</td></tr>
<tr><td>11_模板与工具</td><td>12 份</td><td>模板四套、句库、润色库、提示词包、手册、终检——写论文全程用</td></tr>
<tr><td>01/03/04/06</td><td>原件层</td><td>官网原件/论文 PDF/全文文本/页面渲染图——一手资料</td></tr>
</table>

<h2>五、全局功能</h2>
<ul>
<li><b>搜索</b>：首页右上角与每个文档页顶栏（/ 快捷键），覆盖 235 份文档正文。</li>
<li><b>打卡系统</b>：文档页停留 3 秒自动记「浏览过」，顶栏按钮手动打卡「已吃透」；首页看进度条与连续天数；导出/导入 JSON 换设备。</li>
<li><b>AI 技能</b>：仓库 `.agents/skills/` 下 7 个技能（建模/写作/图表/评审教练 + 运维三件套），在 ZCode 中打开本仓库自动生效。</li>
<li><b>AI 总接口</b>：提示词工坊第 0 号「总指挥」+ 知识包 K1–K10，把全库喂给任意强模型（见说明书上方工具表）。</li>
<li><b>讨论区</b>（可选）：文档页预留 giscus 挂载点，配置后启用。</li>
</ul>

<h2>六、数据与隐私</h2>
<p>所有工具页数据只存<b>本浏览器</b> localStorage（键 upc*）；换设备用各页的导出/导入。站点运行时零外部请求（唯一例外：实验台的 Pyodide 按需加载）。打卡/进度不上传服务器。</p>

<h2>七、常见任务速查</h2>
<table>
<tr><th>我想…</th><th>去哪</th></tr>
<tr><td>第一次了解这个比赛</td><td>首页小档案 + 新手课堂课程一</td></tr>
<tr><td>练一道真题</td><td>年鉴选题 → 题目深度解读 → 起步卡 → 精读</td></tr>
<tr><td>写论文卡壳</td><td>写作句库 / 中译英润色库 / 模板工坊 / 组装机</td></tr>
<tr><td>检查能不能交</td><td>作战室「提交终检」+ 规则页合规卡</td></tr>
<tr><td>找某年的某篇论文</td><td>论文库筛选 或 全库文件导航</td></tr>
<tr><td>让 AI 用本库干活</td><td>提示词工坊 0 号总指挥（配知识包 K1–K10）</td></tr>
</table>

<h2>八、维护与部署</h2>
<p>站点由 `_工具脚本/_build_site.py` 构建（文档渲染 + 工具页生成 + 链接校验 + 搜索索引），`_site_check.py` 独立体检，pre-commit 双门拦截；部署为 GitHub Pages。完整维护手册见仓库 `_工具脚本/网站蓝图与巡检标准.md` 与 `README.md`。数据抓取于 2026-10-24，官方事实核查于 2026-10-31。</p>
"""

    manual_html = markdown_fragment(manual)

    script = r"""
var TREE=__TREE__;
function esc(s){return escHtml(s);}
/* 可展开/合拢的真文件夹树：文件夹节点带箭头，子容器可折叠 */
function nodeHtml(n,depth){
  var isDir=!!n.ch;
  var row='<div class="tn" style="padding-left:'+(depth*14+4)+'px">'+
    (isDir?'<button class="caret" type="button" aria-label="展开/合拢">▸</button>'
          :'<span class="leafdot">·</span>')+
    (n.u?'<a href="'+n.u+'"'+(n.u.indexOf('../')===0?' target="_blank"':'')+'>'+esc(n.n)+'</a>':esc(n.n))+
    (n.d?' <span style="color:var(--dim);font-size:11px">— '+esc(n.d)+'</span>':'')+
    (isDir&&n.cnt?' <span style="color:var(--dim);font-size:10.5px;font-family:var(--mono)">('+n.cnt+')</span>':'')+
    '</div>';
  if(isDir){
    row+='<div class="kids" style="display:none">'+n.ch.map(function(c){return nodeHtml(c,depth+1);}).join('')+'</div>';
  }
  return row;
}
function countLinks(n){
  var c=n.u?1:0;
  (n.ch||[]).forEach(function(x){c+=countLinks(x);});
  return c;
}
function countAll(n){return 1+(n.ch||[]).reduce(function(s,x){return s+countAll(x);},0);}
(function buildTree(){
  TREE.cnt=countLinks(TREE);
  document.getElementById('tree').innerHTML=nodeHtml(TREE,0);
  var rootKids=document.querySelector('#tree > div.kids');
  if(rootKids)rootKids.style.display='block';   // 默认展开一层：顶层目录可见
  document.getElementById('tcount').textContent=countLinks(TREE);
  // 默认：根的子文件夹（顶层目录）展开一层，更深层收拢
  document.querySelectorAll('#tree > div > div.kids > div > div.kids').forEach(function(k){k.style.display='none';});
  document.querySelectorAll('#tree .caret').forEach(function(b){
    b.addEventListener('click',function(ev){
      ev.stopPropagation();
      var kids=b.parentElement.nextElementSibling;
      var open=kids.style.display!=='none';
      kids.style.display=open?'none':'block';
      b.textContent=open?'▸':'▾';
    });
  });
  // 点文件夹名也可展开/合拢
  document.querySelectorAll('#tree .tn').forEach(function(d){
    var b=d.querySelector('.caret');
    if(b)d.querySelector('a,span')?.addEventListener('click',function(e){});
  });
})();
document.getElementById('tall').addEventListener('click',function(){
  var anyClosed=[...document.querySelectorAll('#tree .kids')].some(function(k){return k.style.display==='none';});
  document.querySelectorAll('#tree .kids').forEach(function(k){k.style.display=anyClosed?'block':'none';});
  document.querySelectorAll('#tree .caret').forEach(function(b){b.textContent=anyClosed?'▾':'▸';});
  this.textContent=anyClosed?'全部合拢':'全部展开';
});
document.getElementById('tq').addEventListener('input',function(){
  var kw=this.value.trim().toLowerCase();
  var items=[...document.querySelectorAll('#tree .tn')];
  items.forEach(function(d){d.style.display='none';});
  document.querySelectorAll('#tree .kids').forEach(function(k){
    if(kw)k.style.display='block';
  });
  items.forEach(function(d){
    if(kw&&d.textContent.toLowerCase().indexOf(kw)>=0){
      d.style.display='';
      var p=d.parentElement;
      while(p&&p.id!=='tree'){ if(p.classList&&p.classList.contains('kids'))p.style.display='block'; p=p.parentElement; }
      var b=d.querySelector('.caret');if(b)b.textContent='▾';
    }
  });
  if(!kw){ // 还原默认：仅根层展开
    document.querySelectorAll('#tree .kids').forEach(function(k){k.style.display='none';});
    var rk=document.querySelector('#tree > div.kids');
    if(rk)rk.style.display='block';
    document.querySelectorAll('#tree .caret').forEach(function(b){
      var kids=b.parentElement.nextElementSibling;
      b.textContent=(kids&&kids.style.display!=='none')?'▾':'▸';
    });
  }
});
"""

    n_clickable = json.dumps(TREE).count('"u": "')
    return page(ctx, "全站说明书 · 树状导航", "实战工具 · 平时开放",
                "UPC 档案库全站说明书与树状导航：左侧文件夹树可点击跳转全站每个文件，右侧详解首页板块、八个工具页、内容目录与全局功能。",
                "整站的地图与说明书：树状导航覆盖全部可跳转节点（" + str(n_clickable) + " 个链接），说明书详解每个板块的功能与用法。",
                body.replace("__MANUAL__", manual_html),
                script.replace("__TREE__", json.dumps(TREE, ensure_ascii=False)),
                extra_head='<style>' + css_tree + '</style>')


import markdown as _markdown
_mdm = _markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"], output_format="html5")


def markdown_fragment(text):
    return _mdm.reset().convert(text)
