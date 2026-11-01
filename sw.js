const V='upc-offline-v1';
self.addEventListener('install',function(e){
  var B=self.registration.scope;
  var pre=['index.html','12_赛时工具/warroom.html','12_赛时工具/manual.html',
    '12_赛时工具/prompts.html','12_赛时工具/flashcards.html','12_赛时工具/selector.html',
    '12_赛时工具/tutorial.html','12_赛时工具/lab.html','12_赛时工具/forge.html','12_赛时工具/xray.html',
    'global-ui.js','global-ui-data.js','manifest.webmanifest','icon.svg',
    '09_可视化总览/docs/02_题目汇总/比赛规则_ContestRules.html'].map(function(p){return new URL(p,B).href;});
  e.waitUntil(caches.open(V).then(function(c){
    return Promise.allSettled(pre.map(function(u){return c.add(u);}));
  }).then(function(){return self.skipWaiting();}));
});
self.addEventListener('activate',function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.filter(function(k){return k!==V;}).map(function(k){return caches.delete(k);}));
  }).then(function(){return self.clients.claim();}));
});
self.addEventListener('fetch',function(e){
  var u=new URL(e.request.url);
  if(e.request.method!=='GET'||u.origin!==location.origin)return;
  if(u.pathname.endsWith('/sw.js'))return;
  var isNav=e.request.mode==='navigate';
  e.respondWith((async function(){
    var c=await caches.open(V);
    var hit=await c.match(e.request,{ignoreSearch:true});
    if(isNav){
      try{var r=await fetch(e.request);if(r&&r.ok)c.put(e.request,r.clone());return r;}
      catch(_){return hit||Response.error();}
    }
    if(hit){fetch(e.request).then(function(r){if(r&&r.ok)c.put(e.request,r.clone());}).catch(function(){});
      return hit;}
    try{var r2=await fetch(e.request);if(r2&&r2.ok)c.put(e.request,r2.clone());return r2;}
    catch(_){return Response.error();}
  })());
});
