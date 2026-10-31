(function(){
var R=window.UPC_UI_ROOT||"";
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c];});}
var st=document.createElement("style");st.textContent=".uig-btnL,.uig-btnR{position:fixed;top:50%;transform:translateY(-50%);z-index:85;\n writing-mode:vertical-rl;letter-spacing:.2em;font-size:12.5px;padding:14px 6px;\n border:1px solid #D9D0BD;background:#FDFCF8;color:#6E6557;cursor:pointer;font-family:inherit}\n.uig-btnL{left:0;border-left:none;border-radius:0 4px 4px 0}\n.uig-btnR{right:0;border-right:none;border-radius:4px 0 0 4px}\n.uig-btnL:hover,.uig-btnR:hover{color:#9C3F2E;border-color:#9C3F2E}\n.uig-panel{position:fixed;top:0;bottom:0;width:min(380px,88vw);z-index:95;background:#F7F4ED;\n box-shadow:0 0 40px rgba(70,58,38,.3);transition:transform .25s;overflow-y:auto;visibility:hidden}\n.uig-panel.on{visibility:visible}\n#uig-nav{left:0;transform:translateX(-105%)}#uig-nav.on{transform:none}\n#uig-doc{right:0;transform:translateX(105%)}#uig-doc.on{transform:none}\n.uig-h{font-family:Georgia,serif;font-size:16px;font-weight:700;padding:14px 16px;border-bottom:1px solid #E7E0D1}\n.uig-x{position:absolute;top:10px;right:10px;width:30px;height:30px;border:1px solid #D9D0BD;background:#FDFCF8;border-radius:3px;font-size:16px;color:#6E6557;cursor:pointer}\n.uig-tree,.uig-doc{padding:8px 12px 20px;font-size:13px;line-height:2}\n.uig-tn{line-height:2}\n.uig-tn a{color:#9C3F2E}.uig-tn a:hover{text-decoration:underline}\n.uig-c{width:18px;height:18px;border:none;background:none;color:#6E6557;cursor:pointer;font-family:monospace;padding:0;margin-right:3px}\n.uig-kids{border-left:1px dashed #D9D0BD;margin-left:8px}\n.uig-doc table{border-collapse:collapse;width:100%;font-size:12.5px;margin:8px 0}\n.uig-doc th,.uig-doc td{border:1px solid #E7E0D1;padding:6px 8px;text-align:left;vertical-align:top}\n.uig-doc a{color:#9C3F2E}\n.uig-doc h2{font-family:Georgia,serif;font-size:16px;margin:1.2em 0 .4em;border-bottom:1px solid #E7E0D1;padding-bottom:.3em}\n.uig-doc h2:first-child{margin-top:.2em}\n@media print{.uig-btnL,.uig-btnR,.uig-panel{display:none!important}}";document.head.appendChild(st);
function openPanel(side){
  ensureData(function(){ buildPanel(side); document.getElementById("uig-"+side).classList.add("on"); });
}
function ensureData(cb){
  if(window.UPC_UI_DATA)return cb();
  var s=document.createElement("script");s.src=R+"global-ui-data.js";
  s.onload=cb;s.onerror=function(){alert("全局导航数据加载失败");};
  document.head.appendChild(s);
}
function buildPanel(side){
  if(document.getElementById("uig-"+side))return;
  var wrap=document.createElement("div");wrap.id="uig-"+side;wrap.className="uig-panel";
  wrap.innerHTML='<button class="uig-x" type="button" aria-label="关闭">×</button>'+
    (side==="nav"?navHtml():docHtml());
  wrap.querySelector(".uig-x").addEventListener("click",function(){wrap.classList.remove("on");});
  document.body.appendChild(wrap);
  if(side==="nav")bindTree(wrap);
}
function navHtml(){
  return '<div class="uig-h">☰ 全站目录</div>'+
    '<div style="padding:8px 10px"><input id="uig-q" type="search" placeholder="过滤全站文件…" '+
    'style="width:100%;box-sizing:border-box;height:30px;border:1px solid #D9D0BD;border-radius:3px;padding:0 8px;font-size:12.5px;outline:none"></div>'+
    '<div class="uig-tree" id="uig-tree"></div>'+
    '<div style="padding:6px 12px;color:#8a8172;font-size:11px">树由构建期自动生成 · 点击文件名跳转</div>';
}
function docHtml(){
  return '<div class="uig-h">📖 全站说明</div><div class="uig-doc">'+window.UPC_UI_DATA.manual+'</div>'+
    '<div style="padding:6px 12px 18px;color:#8a8172;font-size:11px">完整版见 12_赛时工具/manual.html</div>';
}
function nodeHtml(n,depth){
  var row='<div class="uig-tn" style="padding-left:'+(depth*13+4)+'px">'+
    (n.ch?'<button class="uig-c" type="button">▸</button>':'<span style="color:#D9D0BD;margin:0 5px 0 9px">·</span>')+
    (n.u?'<a href="'+R+n.u+'">'+esc(n.n)+'</a>':'<span>'+esc(n.n)+'</span>')+
    (n.d?' <span style="color:#8a8172;font-size:10.5px">'+esc(n.d)+'</span>':'')+'</div>';
  if(n.ch)row+='<div class="uig-kids" style="display:none">'+
    n.ch.map(function(c){return nodeHtml(c,depth+1);}).join("")+'</div>';
  return row;
}
function bindTree(wrap){
  var tree=wrap.querySelector("#uig-tree");
  tree.innerHTML=nodeHtml(window.UPC_UI_DATA.tree,0);
  var rk=tree.querySelector(":scope > div.uig-kids");if(rk)rk.style.display="block";
  tree.addEventListener("click",function(ev){
    var b=ev.target.closest(".uig-c");if(!b)return;
    var kids=b.parentElement.nextElementSibling;
    var open=kids.style.display!=="none";
    kids.style.display=open?"none":"block";
    b.textContent=open?"▸":"▾";
  });
  var q=wrap.querySelector("#uig-q");
  q.addEventListener("input",function(){
    var kw=this.value.trim().toLowerCase();
    var tns=[].slice.call(wrap.querySelectorAll(".uig-tn"));
    tns.forEach(function(d){d.style.display="none";});
    [].slice.call(wrap.querySelectorAll(".uig-kids")).forEach(function(k){k.style.display=kw?"block":"none";});
    tns.forEach(function(d){
      if(!kw||d.textContent.toLowerCase().indexOf(kw)>=0)d.style.display="";
    });
    if(!kw){var rk=wrap.querySelector("#uig-tree > div.uig-kids");if(rk)rk.style.display="block";}
  });
}
function btn(side,cls,label){
  var b=document.createElement("button");b.id=cls;b.type="button";b.textContent=label;
  b.addEventListener("click",function(){
    var p=document.getElementById("uig-"+side);
    if(p&&p.classList.contains("on")){p.classList.remove("on");return;}
    openPanel(side);
  });
  document.body.appendChild(b);
}
function init(){btn("nav","uig-btnL","☰ 目录");btn("doc","uig-btnR","📖 说明");}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();
