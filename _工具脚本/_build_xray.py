# -*- coding: utf-8 -*-
"""_build_xray.py — 论文透视（同题对比/结构图谱/摘要解剖）+ 彩蛋·论文组装机
由 _build_tools.render_tools 在调用期导入（避免循环导入）。"""
import os, re, json, glob

from _build_tools import page, write_out  # 共享页面骨架与写出工具

ROOT_OF = lambda ctx: ctx["root"]
P = lambda ctx, *a: os.path.join(ctx["root"], *a)
TOOLS_DIR = "12_赛时工具"
BS = chr(92)

BUCKET_COLORS = {"abstract": "#3A5A8C", "intro": "#647C35", "model": "#9C3F2E",
                 "numerics": "#2F7D6B", "results": "#B0543B", "conclusion": "#6E5599",
                 "references": "#9A9080", "appendix": "#C9BFA8", "other": "#E7E0D1",
                 "front": "#EFEADC"}
BUCKET_ORDER = ["abstract", "intro", "model", "numerics", "results",
                "conclusion", "references", "appendix", "other", "front"]


def doc_url(md_rel):
    return "../09_可视化总览/docs/" + md_rel[:-3] + ".html"


def load_json(ctx, *a):
    fp = P(ctx, *a)
    if os.path.exists(fp):
        with open(fp, encoding="utf-8") as f:
            return json.load(f)
    return None


def collect_compare(ctx):
    groups = {}
    for f in sorted(glob.glob(P(ctx, "_知识提炼", "卡片", "*.json"))):
        try:
            c = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        key = f"{c['year']}-{c['problem']}"
        base = c["id"]
        ana = os.path.join("09_可视化总览", "docs", "05_论文赏析", str(c["year"]), base + ".html")
        jd = os.path.join("09_可视化总览", "docs", "10_论文精读", str(c["year"]), base + "_精读.html")
        groups.setdefault(key, []).append({
            "id": base, "team": c["team"], "pages": c["pages"],
            "title": c.get("title_zh", ""),
            "core": c.get("core_idea", ""),
            "models": "；".join(f"{m.get('name','')}（{m.get('why','')}）" for m in c.get("models", [])),
            "numerics": "；".join(c.get("numerics", [])),
            "figures": "；".join(f"{x.get('type','')}" for x in c.get("figures", []) if isinstance(x, dict) and x.get("type")),
            "gold": "；".join(c.get("gold_secret", [])),
            "pit": "；".join(c.get("pitfalls", [])),
            "ana": ana.replace(BS, "/"), "jd": jd.replace(BS, "/"),
        })
    out = []
    for key in sorted(groups):
        papers = sorted(groups[key], key=lambda x: x["team"])
        if len(papers) >= 2:
            out.append({"key": key, "cn": papers[0]["title"], "papers": papers})
    return out


def _coverage_html(ctx):
    """覆盖地图：每道题 ×（解读 / 起步卡 / 赏析 / 精读）实扫矩阵。
    文件系统即事实——每格都能在仓库里找到对应实体，构建期生成、永不过期。"""
    root = ctx["root"]
    P = lambda *a: os.path.join(root, *a)
    jd = {}
    for f in glob.glob(P("07_题目解读", "*_题[AB]_*.md")):
        b = os.path.basename(f)
        if "起步卡" in b:
            continue
        m = re.match(r"(\d{4})_题([AB])_", b)
        if m:
            jd[(m.group(1), m.group(2))] = re.sub(r"^\d{4}_题[AB]_", "", b[:-3])
    start = set()
    for f in glob.glob(P("07_题目解读", "*起步卡.md")):
        m = re.match(r"(\d{4})_题([AB])_", os.path.basename(f))
        if m:
            start.add((m.group(1), m.group(2)))
    ana = {}
    for f in glob.glob(P("05_论文赏析", "*", "*.md")):
        m = re.match(r"(\d{4})-GM-([AB])-", os.path.basename(f)[:-3])
        if m:
            ana[(m.group(1), m.group(2))] = ana.get((m.group(1), m.group(2)), 0) + 1

    def dot(b):
        return '<b style="color:var(--acc)">✓</b>' if b else '<span style="color:var(--dim)">—</span>'

    rows = []
    tot = {"start": 0, "ana": 0, "read": 0}
    for (yr, pb) in sorted(jd):
        n_ana = ana.get((yr, pb), 0)
        n_read = len([f for f in glob.glob(P("10_论文精读", yr, "*.md"))
                      if re.match(r"\d{4}-GM-" + pb + "-", os.path.basename(f))])
        has_start = (yr, pb) in start
        tot["ana"] += n_ana
        tot["read"] += n_read
        tot["start"] += 1 if has_start else 0
        rows.append(
            '<tr><td>{} 题{}</td><td>{}</td><td style="text-align:center">{}</td>'
            '<td style="text-align:center">{}</td><td style="text-align:center">{}</td>'
            '<td style="text-align:center">{}</td></tr>'.format(
                yr, pb, jd[(yr, pb)], dot(True), dot(has_start), n_ana, n_read))
    head = ('<tr><th>题</th><th>题名（来自解读文件）</th><th>解读</th><th>起步卡</th>'
            '<th>赏析</th><th>精读</th></tr>')
    summary = ('<div class="notebox" style="margin-top:12px">总计：<b>{n} 题</b> · 解读 {n}/{n} · '
               '起步卡 {s}/{n} · 赏析 {a} 篇 · 精读 {r} 篇。'
               '缺口坦然列出：起步卡与部分批次精读仍在补齐（见维护路线图）。</div>').format(
        n=len(jd), s=tot["start"], a=tot["ana"], r=tot["read"])
    return ('<div style="overflow:auto"><table style="border-collapse:collapse;width:100%;'
            'font-size:13px"><thead>' + head + '</thead><tbody>' + "".join(rows) +
            '</tbody></table></div>' + summary)


def _divergence_html():
    """分歧类型学：16 组多金牌题的人工提炼（2026-11-01 逐组读完卡片 core_idea/models 归类）。
    人工结论入库为代码常量——这是该结论的唯一来源，更新需重读卡片。"""
    rows = [
        ("2016-A", "方案空间展开", "双方案深挖+渐近线挖出第三方案 vs 六方案决策树再收敛——方案枚举宽度不同"),
        ("2017-A", "求解范式", "网格搜索 / 庞特里亚金间接法 / SLSQP 双目标 NLP——同一控制问题的三种数值范式"),
        ("2018-A", "问题分解", "解耦筛选矩阵 / 单模型贯穿全部子题 / 反问题反解容差"),
        ("2018-B", "代理量选择", "以已反应氧质量为效率代理 vs 自重压实 ρ(h) 作枢纽闭式解"),
        ("2019-A", "技术路线取舍", "三因子分解 / 押注主动磁屏蔽 / 8 构型枚举排名——48.3 吨 vs 16.53 吨的系统级分歧"),
        ("2019-B", "验证策略", "文献判据+数值积分 vs 解析递推+商业仿真器双轨互证（94.26% 吻合）"),
        ("2020-A", "问题形式化", "策略先于方程 / 贴真实任务借力链 / trade study / 最优控制形式化——四档谱系"),
        ("2020-B", "不确定性建模", "Dryden 随机风+闭环仿真 vs 单参数 ε 闭式解+理论仿真互验"),
        ("2021-A", "模型约化", "三通道并行+贡献排序 vs 砍到单通道实测锚定"),
        ("2021-B", "判据来源与正逆链", "文献波高阈值 / 10 m 浪倒推动能 / 四效应排除定理化 / Ward 波场 FFT 真跑"),
        ("2022-A", "解析-数值光谱", "递进证伪链 / 参数化数值搜索 / 反问题+DART 锚定 / 全程解析零数值——光谱极宽"),
        ("2022-B", "策略层反转", "概率场死角必进 / 规划解偏差 1.18 cm / 用世界杯统计反转题面主张射下角"),
        ("2023-A", "判据集设计", "三判据取最严 / 出舱即开伞消解问题 / 排除法锁定热积累 / 原创积分判据 / 双档分人群"),
        ("2023-B", "保真度与互证", "理想+修正双模型 / 自研物理引擎+视频实测闭环 / 解析稳态-数值吸引子双轨互证"),
        ("2025-A", "判据先行程度", "七域验证矩阵 / 敏感性第一性论证选型 / 判据闭环到 MIPS 与成本"),
        ("2025-B", "交付形式蒸馏", "13 金牌同一物理骨架，交付从拟合式/查表/列线图/心算口诀到历史走廊——七种降维形态"),
    ]
    trs = "".join('<tr><td style="white-space:nowrap"><b>{}</b></td>'
                  '<td style="white-space:nowrap;color:var(--acc)">{}</td><td>{}</td></tr>'.format(k, t, d)
                  for (k, t, d) in rows)
    return ('<div class="card" style="margin-top:14px">'
            '<b style="font-family:var(--serif);font-size:15px">分歧类型学 · 16 组多金牌题的人工提炼</b>'
            '<p style="font-size:12.5px;color:var(--dim);margin:6px 0 8px">同一道题的多篇金牌论文在哪里分歧？逐组读完 16 组的核心思路与模型链后归类，'
            '分歧集中在五类：<b>问题形式化 / 解析-数值光谱 / 判据来源 / 交付形式蒸馏 / 验证策略</b>——'
            '而基础物理层几乎不分歧：物理立住之后，评审奖励的是形式化与交付层的个性决策。这就是"不设标准答案"的可教版本。</p>'
            '<table style="border-collapse:collapse;width:100%;font-size:12.5px"><tbody>' + trs + '</tbody></table>'
            '<div class="note" style="margin-top:8px;font-size:12px;color:var(--dim)">口径：人工逐组归类（2026-11-01，基于 73 张模式卡片的 core_idea/models 字段），主观归类、可复核——数据在 _知识提炼/卡片/。</div></div>')


def render_xray(ctx):
    CMP = collect_compare(ctx)
    ST = load_json(ctx, "_知识提炼", "汇总", "结构图谱.json") or {"papers": [], "names": {}}
    AB = load_json(ctx, "_知识提炼", "汇总", "摘要解剖.json") or {"papers": [], "names": {}}
    COV = _coverage_html(ctx)

    # 见解一：金牌摘要真实配方（73 篇逐句标注的统计基线）——教数据不教感觉
    from collections import Counter as _C
    _fc = _C()
    _lens = []
    for _p in AB.get("papers", []):
        _lens.append(_p.get("n", len(_p.get("sents", []))))
        _fc.update(s["f"] for s in _p.get("sents", []))
    _tot = sum(_fc.values()) or 1
    _lens.sort()
    _med = _lens[len(_lens) // 2] if _lens else 0
    _bars = "".join(
        '<div style="display:flex;align-items:center;gap:8px;margin:3px 0">'
        '<span style="width:58px;font-size:12px;color:var(--dim)">{}</span>'
        '<i style="flex:1;height:10px;background:var(--paper);border:1px solid var(--line);border-radius:5px;overflow:hidden">'
        '<em style="display:block;height:100%;width:{}%;background:var(--acc)"></em></i>'
        '<b style="width:120px;font-size:11.5px;font-family:var(--mono);color:var(--ink)">{} 句 · {}%</b></div>'.format(
            _k, round(_fc.get(_k, 0) / _tot * 100, 1), _fc.get(_k, 0), round(_fc.get(_k, 0) / _tot * 100, 1))
        for _k in ["叙述", "数字", "方法", "num结论", "定义", "建议", "两难"])
    ABSTAT = ('<div class="card" style="margin-bottom:12px">'
              '<b style="font-family:var(--serif);font-size:15px">金牌摘要真实配方（{} 篇 · {} 句逐句标注）</b>'
              + _bars +
              '<div class="note" style="margin-top:8px;font-size:12.5px">读法：摘要以<b>叙述铺陈 + 数字结论</b>为骨架（带数字句约 1/3，'
              '其中明确的数字结论句另有 6%）；<b>"建议"句全库仅 7 句、"两难"句仅 5 句</b>——两难不必写、建议 ≤1 句；'
              '篇幅锚点：中位 {} 句（3–24 句）。写摘要时对照此配比，不凭感觉。</div></div>').format(
                  len(AB.get("papers", [])), _tot, _med)

    body = r"""
<nav class="tabs" id="xtabs">
  <a data-t="cmp" class="on">同题对比矩阵</a>
  <a data-t="atlas">结构图谱</a>
  <a data-t="abs">摘要解剖室</a>
  <a data-t="cov">覆盖地图</a>
</nav>

<section class="pane on" id="pane-cmp">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px">
    <select id="cmpsel" style="height:32px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);font-family:inherit;font-size:13px;padding:0 8px;color:var(--ink)"></select>
    <span class="note" style="color:var(--dim);font-size:12px" id="cmpcnt"></span>
  </div>
  <div style="overflow:auto"><div id="cmptable"></div></div>
  <div class="notebox" style="margin-top:12px">矩阵数据来自 <b>73 张模式卡片</b>（赏析「获奖密码」+ 精读「决策链」的结构化提炼）。用法：先纵向读每队的「核心思路」找分歧点，再横向看「模型链/数值/图表」四行的同与不同——同一道题的合法解法谱系，就是评审"不设标准答案"的实证。</div>
  __TYPOLOGY__
</section>

<section class="pane" id="pane-atlas">
  <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px">
    <b style="font-size:14px">全部金牌论文的章节体量占比（近似页配比）</b>
    <span class="note" style="font-size:12px;color:var(--dim)" id="atcnt"></span>
  </div>
  <div class="card" style="margin-bottom:12px" id="atavg"></div>
  <div class="card" id="atlist"></div>
  <div class="notebox" style="margin-top:12px">每行 = 一篇论文，条带宽度 = 该部分文本体量占比（无分页符的近似，个别论文章节名非标准会有归桶误差）。看规律：<b>验证与误差章节在每篇金牌论文里都稳定存在</b>——这就是"验证三件套是金银牌分水岭"的数据实证。</div>
</section>

<section class="pane" id="pane-abs">
  __ABSTAT__
  <div class="card" style="margin-bottom:12px" id="abstats"></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px" id="ablegend"></div>
  <div style="margin-bottom:10px"><input id="abq" type="search" placeholder="筛：年份/题号/队伍号/句中关键词…" style="width:min(420px,100%);height:32px;border:1px solid var(--line2);border-radius:3px;background:var(--sheet);padding:0 10px;font-size:13px;outline:none"></div>
  <div id="ablist"></div>
</section>

<section class="pane" id="pane-cov">
  <div class="notebox" style="margin-bottom:12px"><b>覆盖地图</b>：全库内容对 16 年 32 道题的覆盖实况——
  每一格都对应仓库里的真实文件，构建期扫描生成。哪些题有起步卡、哪篇论文还没精读，一目了然。</div>
  __COV__
</section>
"""

    script = r"""
var CMP=__CMP__, ST=__ST__, AB=__AB__;
var BC=__BC__, BO=__BO__, BN=__BN__;
var xtabs=document.getElementById('xtabs');
xtabs.addEventListener('click',function(ev){
  var a=ev.target.closest('a');if(!a)return;
  document.querySelectorAll('#xtabs a').forEach(function(x){x.classList.remove('on')});
  a.classList.add('on');
  document.querySelectorAll('.pane').forEach(function(p){p.classList.remove('on')});
  document.getElementById('pane-'+a.dataset.t).classList.add('on');
});
function esc(s){return escHtml(s);}

/* ---------- 同题对比矩阵 ---------- */
var csel=document.getElementById('cmpsel');
CMP.forEach(function(g,i){
  var o=document.createElement('option');
  o.value=i;o.textContent=g.key+' · '+g.cn+'（'+g.papers.length+' 篇）';
  csel.appendChild(o);
});
function renderCmp(){
  var g=CMP[+csel.value];
  if(!g)return;
  document.getElementById('cmpcnt').textContent=g.papers.length+' 篇金牌 · 共 '+g.papers.reduce(function(s,p){return s+p.pages;},0)+' 页';
  var rows=[
    ['核心思路', function(p){return p.core;}],
    ['模型链（选择理由）', function(p){return p.models;}],
    ['数值方法', function(p){return p.numerics;}],
    ['图表', function(p){return p.figures;}],
    ['获奖密码', function(p){return p.gold;}],
    ['陷阱与规避', function(p){return p.pit;}]
  ];
  var html='<table style="min-width:'+(240+g.papers.length*230)+'px"><thead><tr><th style="min-width:90px">维度</th>'+
    g.papers.map(function(p){
      return '<th style="min-width:220px">#'+p.team+' · '+p.pages+' 页<br>'+
        '<a href="'+p.ana+'" target="_blank" style="font-weight:400;font-size:11px">赏析</a> · '+
        '<a href="'+p.jd+'" target="_blank" style="font-weight:400;font-size:11px">精读</a></th>';
    }).join('')+'</tr></thead><tbody>'+
    rows.map(function(r){
      return '<tr><td style="font-weight:600;font-size:12px;white-space:nowrap">'+r[0]+'</td>'+
        g.papers.map(function(p){return '<td style="font-size:12.5px;line-height:1.9">'+esc(r[1](p))+'</td>';}).join('')+'</tr>';
    }).join('')+'</tbody></table>';
  document.getElementById('cmptable').innerHTML=html;
  document.getElementById('cmptable').firstChild.style.width='max-content';
}
csel.addEventListener('change',renderCmp);
if(CMP.length){renderCmp();}else{document.getElementById('cmptable').innerHTML='<p style="color:var(--dim)">暂无 ≥2 篇金牌的题目</p>';}

/* ---------- 结构图谱 ---------- */
function strip(p){
  var segs='';
  BO.forEach(function(b){
    var v=p.alloc[b]||0;
    if(v<=0)return;
    segs+='<span title="'+BN[b]+' '+v+'%" style="display:inline-block;height:18px;width:'+v+'%;background:'+(BC[b]||'#ccc')+'"></span>';
  });
  return segs;
}
function avgAlloc(){
  var acc={},n=ST.papers.length;
  ST.papers.forEach(function(p){Object.keys(p.alloc).forEach(function(k){acc[k]=(acc[k]||0)+p.alloc[k];});});
  var out={};Object.keys(acc).forEach(function(k){out[k]=acc[k]/n;});
  return out;
}
function renderAtlas(){
  var avg=avgAlloc();
  document.getElementById('atcnt').textContent=ST.papers.length+' 篇 · 按年份-题号排序';
  var avgSeg=BO.map(function(b){var v=avg[b]||0;return v>0?'<span title="'+BN[b]+' '+v.toFixed(1)+'%" style="display:inline-block;height:20px;width:'+(v*2.2)+'%;background:'+(BC[b]||'#ccc')+'"></span>':'';}).join('');
  var avgLegend=BO.filter(function(b){return (avg[b]||0)>0.05;}).map(function(b){return '<span style="font-size:11.5px;color:var(--mut)"><i style="display:inline-block;width:9px;height:9px;background:'+(BC[b]||'#ccc')+';border-radius:2px;margin-right:4px"></i>'+BN[b]+' '+(avg[b]||0).toFixed(1)+'%</span>';}).join('　');
  document.getElementById('atavg').innerHTML='<b style="font-size:12.5px;color:var(--dim)">平均配比（条带 ×2.2 拉伸显示）</b><div style="margin-top:6px;line-height:0">'+avgSeg+'</div><div style="margin-top:6px;line-height:2">'+avgLegend+'</div>';
  document.getElementById('atlist').innerHTML=ST.papers.map(function(p){
    var ana='../09_可视化总览/docs/05_论文赏析/'+p.year+'/'+p.id+'.html';
    return '<div style="display:flex;gap:8px;align-items:center;padding:5px 0;border-bottom:1px solid var(--line)">'+
      '<a href="'+ana+'" target="_blank" style="font-family:var(--mono);font-size:11.5px;color:var(--mut);min-width:120px" title="打开赏析">'+p.id+'</a>'+
      '<div style="flex:1;line-height:0">'+strip(p)+'</div>'+
      '<span style="font-family:var(--mono);font-size:10.5px;color:var(--dim);min-width:30px;text-align:right">'+p.pages+'页</span></div>';
  }).join('');
}
renderAtlas();

/* ---------- 摘要解剖室 ---------- */
var FC={'num结论':['#9C3F2E','数字结论'],'数字':['#C0704F','数字陈述'],'定义':['#3A5A8C','定义'],'两难':['#6E5599','两难'],'方法':['#2F7D6B','方法'],'建议':['#9A6232','建议'],'叙述':['#786E60','叙述']};
var abq=document.getElementById('abq');
document.getElementById('ablegend').innerHTML=Object.keys(FC).map(function(k){return '<span style="font-size:11.5px"><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:'+FC[k][0]+';margin-right:4px"></i>'+FC[k][1]+'</span>';}).join('　');
function renderAbs(){
  var kw=abq.value.trim().toLowerCase();
  var st=document.getElementById('abstats');
  var all=[].concat.apply([],AB.papers.map(function(p){return p.sents;}));
  var dist={};all.forEach(function(s){dist[s.f]=(dist[s.f]||0)+1;});
  var withNum=AB.papers.filter(function(p){return p.sents.some(function(s){return s.f==='num结论'||s.f==='数字';});}).length;
  st.innerHTML='<b style="font-family:var(--serif)">'+AB.papers.length+' / 74 篇</b> 摘要可解析（其余无标准 Abstract 节）· 共 '+all.length+' 句 · 平均 '+(all.length/AB.papers.length).toFixed(1)+' 句 · <b>'+withNum+'</b> 篇含数字句 —— <span style="color:var(--acc)">数字不是加分项，是入场券</span>';
  var html='';
  AB.papers.forEach(function(p){
    var head=p.year+'-'+p.problem+' #'+p.team;
    if(kw&&head.toLowerCase().indexOf(kw)<0&&!p.sents.some(function(s){return s.t.toLowerCase().indexOf(kw)>=0;}))return;
    html+='<div class="card" style="margin-bottom:10px"><b style="font-family:var(--mono);font-size:12px;color:var(--acc)">'+head+'</b>'+
      '<span style="font-size:11px;color:var(--dim);margin-left:8px">'+p.n+' 句</span><div style="margin-top:5px;font-size:13px;line-height:2.1">'+
      p.sents.map(function(s){var col=FC[s.f]?FC[s.f][0]:'#999';var tip=FC[s.f]?FC[s.f][1]:s.f;
        return '<span title="'+tip+'" style="border-bottom:2px solid '+col+';padding-bottom:1px">'+esc(s.t)+'</span>';}).join(' ')+'</div></div>';
  });
  document.getElementById('ablist').innerHTML=html||'<div class="notebox">没有匹配的摘要</div>';
}
abq.addEventListener('input',renderAbs);
renderAbs();
"""

    katex = ('<link rel="stylesheet" href="../09_可视化总览/vendor/katex/katex.min.css">'
             '<script defer src="../09_可视化总览/vendor/katex/katex.min.js"></script>')
    return page(ctx, "论文透视", "实战工具 · 平时开放",
                "UPC 论文透视：同题对比矩阵、结构图谱、摘要解剖室与覆盖地图——跨论文横向分析金牌论文的判据、模型、验证与摘要配方。",
                "单篇精读之上的一层：横向看 74 篇金牌论文。同题对比看合法解法谱系，结构图谱看章节配比规律，摘要解剖看逐句功能配方，覆盖地图看全库对 32 题的覆盖实况。",
                body.replace("__COV__", COV).replace("__TYPOLOGY__", _divergence_html())
                     .replace("__ABSTAT__", ABSTAT),
                script.replace("__CMP__", json.dumps(CMP, ensure_ascii=False))
                      .replace("__ST__", json.dumps(ST, ensure_ascii=False))
                      .replace("__AB__", json.dumps(AB, ensure_ascii=False))
                      .replace("__BC__", json.dumps(BUCKET_COLORS))
                      .replace("__BO__", json.dumps(BUCKET_ORDER))
                      .replace("__BN__", json.dumps(ST.get("names", {}), ensure_ascii=False)),
                extra_head=katex)


# ================================================================
# 论文组装机（与总指挥提示词配套：六阶段产出各节 → 本页组装整稿）
# ================================================================
def render_forge(ctx):
    body = r"""
<div class="notebox" style="margin-bottom:14px"><b>与总指挥提示词的关系</b>：完整流水线是——<a href="prompts.html#psec0" target="_blank">① 主控提示词六阶段</a>（配 K1–K10 知识包，AI 起草各节）→ <b>② 本页组装成整稿 LaTeX</b>（你核验各节、填齐 [TODO]）→ ③ 编译出 PDF 后过作战室终检。它自动化的是排版苦役，<b>物理必须你自己填</b>（空白处会留下 [TODO]）；若让 AI 润色/扩写，按官方规则须附 <b>Report on the Use of AI</b>（见<a href="../09_可视化总览/docs/02_%E9%A2%98%E7%9B%AE%E6%B1%87%E6%80%BB/%E6%AF%94%E8%B5%9B%E8%A7%84%E5%88%99_ContestRules.html" target="_blank">比赛规则 §5.1 与文末模板</a>）。</div>

<div class="card">
  <div style="display:flex;gap:12px;flex-wrap:wrap">
    <label style="font-size:12.5px;color:var(--mut)">队号 <input id="f-team" type="text" placeholder="160" style="width:90px;height:30px;border:1px solid var(--line2);border-radius:3px;padding:0 8px;font-family:var(--mono)"></label>
    <label style="font-size:12.5px;color:var(--mut)">题号
      <select id="f-prob" style="height:30px;border:1px solid var(--line2);border-radius:3px;font-family:inherit"><option>A</option><option>B</option></select></label>
    <label style="font-size:12.5px;color:var(--mut);flex:1;min-width:220px">论文标题（英文）<input id="f-title" type="text" placeholder="Aerobraking at Neptune: …" style="width:100%;height:30px;border:1px solid var(--line2);border-radius:3px;padding:0 8px"></label>
  </div>
  <p style="margin:12px 0 4px;font-size:13px"><b>① 判据</b>（一行一条，模糊词→数字）</p>
  <textarea id="f-crit" rows="3" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="significant → 燃耗节省 ≥ 20%&#10;safely → 全程过载 ≤ 8g"></textarea>
  <p style="margin:12px 0 4px;font-size:13px"><b>② 基准（解析锚数字）</b></p>
  <textarea id="f-base" rows="2" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="无阻力情形闭式解：v_t = 67 m/s（§1 锚数字）"></textarea>
  <p style="margin:12px 0 4px;font-size:13px"><b>③ 假设（一行一条，配量级自辩）</b></p>
  <textarea id="f-assum" rows="3" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="大气 = 指数模型（每 8.5 km 降一个 e，实测标度）&#10;c_d = 0.4（半球，0.3–0.5 间影响小于入射角敏感性）"></textarea>
  <p style="margin:12px 0 4px;font-size:13px"><b>④ 主方程（LaTeX，不含定界符）</b></p>
  <textarea id="f-eq" rows="2" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="m\,\frac{dv}{dt} = mg - \tfrac{1}{2}\rho(h) C_dA v^2"></textarea>
  <p style="margin:12px 0 4px;font-size:13px"><b>⑤ 数值方法</b></p>
  <textarea id="f-num" rows="2" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="Euler method, dt=0.001 s, 初始 v=0/h=h0, 边界 h≥0，步长减半收敛检验"></textarea>
  <p style="margin:12px 0 4px;font-size:13px"><b>⑥ 结果（一行一条，必须带数字）</b></p>
  <textarea id="f-res" rows="3" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="临界入射角窗口 8.8296°–8.8549°（允许误差 0.0253°）&#10;建议：不采用该机动（负结论也是结论）"></textarea>
  <p style="margin:12px 0 4px;font-size:13px"><b>⑦ 图（一行一张：文件名 | 图题结论）</b></p>
  <textarea id="f-fig" rows="2" style="width:100%;box-sizing:border-box;border:1px solid var(--line2);border-radius:3px;padding:8px;font-family:var(--mono);font-size:12px" placeholder="fig1_traj.png | 图 1：三类入射角轨迹对比，窗口仅 0.0253°"></textarea>
  <div style="display:flex;gap:10px;margin-top:14px;flex-wrap:wrap">
    <button class="btn solid" id="f-gen" type="button">组装 LaTeX 初稿</button>
    <button class="btn" id="f-copy" type="button" disabled>复制</button>
    <a class="btn" id="f-dl" type="button" download="upc_draft.tex" style="display:none">下载 .tex</a>
  </div>
</div>
<div class="card" style="margin-top:14px"><textarea id="f-out" rows="18" readonly placeholder="点「组装」后这里出现完整 LaTeX……" style="width:100%;box-sizing:border-box;border:none;background:transparent;font-family:var(--mono);font-size:12px;line-height:1.8;outline:none;resize:vertical"></textarea></div>
"""

    script = r"""
function L(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;');}
function lines(id){return document.getElementById(id).value.split('\n').map(function(x){return x.trim();}).filter(Boolean);}
document.getElementById('f-gen').addEventListener('click',function(){
  var team=document.getElementById('f-team').value.trim()||'XXX';
  var prob=document.getElementById('f-prob').value;
  var title=document.getElementById('f-title').value.trim()||'[TODO: 论文标题——包含方法与结论关键词]';
  var crit=lines('f-crit'), base=document.getElementById('f-base').value.trim(),
      assum=lines('f-assum'), eq=document.getElementById('f-eq').value.trim(),
      num=document.getElementById('f-num').value.trim(), res=lines('f-res'), fig=lines('f-fig');
  function items(arr, todo){return arr.length?arr.map(function(x){return '\\item '+x;}).join('\n'):'\\item [TODO: ' + todo + ']';}
  var eqs=eq?('\\['+eq+'\\]'):'\\[TODO: 主方程——从守恒律/牛顿第二定律写出，参考建模决策树]';
  var figs=fig.length?fig.map(function(x){
      var seg=x.split('|');
      return '\\begin{figure}[h]\\centering\\includegraphics[width=0.8\\textwidth]{'+(seg[0]||'fig.png').trim()+'}'+
        '\\caption{'+(seg[1]||'[TODO: 结论进图题]').trim()+'}\\label{fig:'+(seg[0]||'fig').trim().replace(/\\.[a-z]+$/,'')+'}\\end{figure}';
    }).join('\n'):'% [TODO: 至少 4 张图，结论进图题——见图表配方库]';
  var tex='% UPC 论文初稿 —— 由档案库「论文组装机」生成\n'+
    '% 组装的是排版结构；所有物理内容来自你上方的输入，[TODO] 处必须自己补齐。\n'+
    '% 若再用 AI 润色/扩写，按官方规则 §5.1 须附 Report on the Use of AI（见比赛规则页）。\n'+
    '\\documentclass[11pt]{article}\n\\usepackage[margin=2.5cm]{geometry}\n'+
    '\\usepackage{amsmath,graphicx,booktabs}\n'+
    '\\begin{document}\n'+
    '\\begin{center}{\\large\\bf Team '+team+' --- Problem '+prob+'}\\\\[4pt]{\\Large\\bf '+title+'}\\end{center}\n'+
    '\\section*{Abstract}\n[TODO: 一页摘要——符号定义 → 方法一句话 → 数字结论（≥2 句，带数字与精度）→ 建议（可选 ≤1 句）与适用域；'+
    '金牌统计：叙述≈55%、带数字≈33%，两难/长篇建议近乎缺席——配比数据见「摘要解剖室」配方卡]\n\n'+
    '\\section{Introduction and Criteria}\n[TODO: 用自己的话复述题目与建模路线]\n\n'+
    'Criteria (operationalized):\n\\begin{itemize}\n'+items(crit,'把题面模糊词翻译成可计算判据')+'\\end{itemize}\n\n'+
    '\\section{Baseline}\n'+(base||'[TODO: 解析基准与锚数字——评审的对照起点]')+'\n\n'+
    '\\section{Model}\n\\begin{itemize}\n'+items(assum,'每条假设配一句量级自辩')+'\\end{itemize}\n'+eqs+'\n\n'+
    '\\section{Numerical Method}\n'+(num||'[TODO: 方法名+步长+初值+边界+终止条件，五要素]')+'\n\n'+
    '\\section{Results}\n\\begin{itemize}\n'+items(res,'结论必须带数字——没有数字先回数值环节')+'\\end{itemize}\n\n'+figs+'\n\n'+
    '\\section{Discussion}\n[TODO: 局限、误差来源、最坏情形——诚实是加分项]\n\n'+
    '\\section{Conclusion}\n[TODO: 答案 + 建议 + 适用域；负结论也是结论]\n\n'+
    '\\begin{thebibliography}{9}\n\\item [TODO: 5–15 条文献，标注访问日期，每条都被正文引用]\n\\end{thebibliography}\n'+
    '\\end{document}\n';
  document.getElementById('f-out').value=tex;
  document.getElementById('f-copy').disabled=false;
  var dl=document.getElementById('f-dl');
  dl.style.display='inline-flex';
  dl.href='data:text/plain;charset=utf-8,'+encodeURIComponent(tex);
});
document.getElementById('f-copy').addEventListener('click',function(){
  copyText(document.getElementById('f-out').value,this);
});
"""
    return page(ctx, "论文组装机", "实战工具 · 平时开放",
                "UPC 论文组装机：把自己的判据、方程、结果数字组装成结构完整的 LaTeX 初稿，TODO 处留给你自己填物理。与「总指挥」主提示词配套使用。",
                "六阶段流水线（AI 提示词工坊第 0 号）产出各节内容后，本页把成果组装成整稿 LaTeX。自动化的只是排版；物理与思考必须你自己完成——若再用 AI 润色，按官方规则附 AI 使用披露。",
                body, script, extra_head="")


# ================================================================
# 入口
# ================================================================