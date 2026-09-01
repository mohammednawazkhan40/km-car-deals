/* KM Car Deals — Dealership OS  |  Dashboard */
(function(){"use strict";
var API="/api/v1";var CHARTS={};
var S={view:"dashboard",filter:"all",q:"",mode:"grid",apiOnline:false,vehicles:[],customers:[],_st:null};
var intakeFiles=[];

/* ── Helpers ── */
function $(s,c){return(c||document).querySelector(s);}
function $$(s,c){return Array.from((c||document).querySelectorAll(s));}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function money(v){if(!v)return"—";var n=Number(v);if(isNaN(n))return v;if(n>=10000000)return"₹"+(n/10000000).toFixed(2)+"Cr";if(n>=100000)return"₹"+(n/100000).toFixed(2)+"L";return"₹"+n.toLocaleString("en-IN");}
function km(v){if(v==null)return"—";var n=Number(v);return n>=1000?(n/1000).toFixed(1)+"k km":n.toLocaleString("en-IN")+" km";}
function num(v){return Number(v||0).toLocaleString("en-IN");}
function ini(name){return(name||"?").split(" ").map(function(w){return w[0]||"";}).slice(0,2).join("").toUpperCase()||"?";}
function bdg(s,lbl){if(!s)return"";return'<span class="badge badge-'+String(s).replace(/[^A-Z0-9_]/g,"_")+'">'+(lbl||String(s).replace(/_/g," "))+"</span>";}
function setContent(h){var c=$("#content");if(c)c.innerHTML=h;}
function destroyChart(k){if(CHARTS[k]){try{CHARTS[k].destroy();}catch(e){}delete CHARTS[k];}}
function gc(){var dk=document.documentElement.dataset.theme==="dark";return{grid:dk?"rgba(255,255,255,.06)":"rgba(0,0,0,.06)",text:dk?"#5d6d84":"#94a3b8",tip:{backgroundColor:"#1a2540",titleColor:"#e8edf5",bodyColor:"#a8b4c8",borderColor:"rgba(255,255,255,.1)",borderWidth:1,padding:12,cornerRadius:10}};}
function purl(p){var fp=p.file_path||p;return/^https?:/.test(fp)?fp:"/uploads/"+fp.replace(/^.*[\\/]data[\\/]uploads[\\/]/,"").replace(/\\/g,"/");}
function confColor(c){return c>=0.9?"var(--success)":c>=0.7?"var(--warning)":"var(--danger)";}

/* ── HTTP ── */
function http(m,u,b){
  var o={method:m,headers:{}};
  if(b instanceof FormData){o.body=b;}
  else if(b!==undefined){o.headers["Content-Type"]="application/json";o.body=JSON.stringify(b);}
  return fetch(u,o).then(function(r){return r.json().catch(function(){return null;}).then(function(d){if(!r.ok)throw new Error((d&&(d.detail||d.message))||"Error "+r.status);return d;});});
}
var GET=function(u){return http("GET",u);};
var POST=function(u,b){return http("POST",u,b);};
var PATCH=function(u,b){return http("PATCH",u,b);};

/* ── Toast ── */
function toast(msg,type,title){
  type=type||"info";
  var icons={success:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',error:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',warning:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',info:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'};
  var titles={success:"Success",error:"Error",warning:"Warning",info:"Info"};
  var stack=$("#toastStack");if(!stack)return;
  var el=document.createElement("div");el.className="toast "+type;
  el.innerHTML='<span class="toast-icon">'+icons[type]+'</span><div class="toast-content"><div class="toast-title">'+esc(title||titles[type])+'</div><div class="toast-msg">'+esc(msg)+'</div></div><button class="toast-dismiss" aria-label="Dismiss"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>';
  el.querySelector(".toast-dismiss").onclick=function(){el.classList.add("removing");setTimeout(function(){el.remove();},220);};
  stack.appendChild(el);setTimeout(function(){if(el.parentNode){el.classList.add("removing");setTimeout(function(){el.remove();},220);}},5000);
}

/* ── Modal ── */
function openModal(title,body){$("#modalTitle").textContent=title;$("#modalBody").innerHTML=body;$("#modalBackdrop").hidden=false;}
function closeModal(){$("#modalBackdrop").hidden=true;$("#modalBody").innerHTML="";}

/* ── Navigate ── */
var LABELS={dashboard:"Dashboard",inventory:"Inventory",intake:"AI Intake",approval:"Approval Queue",customers:"Customers",leads:"Leads",analytics:"Analytics",audit:"Audit Log",settings:"Settings",docs:"API Docs"};
function navigate(v){
  S.view=v;
  $$(".nav-item[data-view]").forEach(function(n){n.classList.toggle("active",n.dataset.view===v);});
  var pt=$("#pageTitle");if(pt)pt.textContent=LABELS[v]||v;
  var map={dashboard:renderDashboard,inventory:renderInventory,intake:renderIntake,approval:renderApproval,customers:renderCustomers,leads:renderLeads,analytics:renderAnalytics,audit:renderAudit,settings:renderSettings,docs:renderDocs};
  if(map[v])map[v]();
  window.scrollTo({top:0,behavior:"smooth"});
  $("#sidebar").classList.remove("open");
  $("#sidebarOverlay").classList.remove("show");
}
window.navigate=navigate;

/* ── Empty / loading ── */
function emptyState(icon,title,sub,btn,act){
  return'<div class="empty-state"><div class="empty-icon">'+icon+'</div><h3>'+esc(title)+'</h3><p>'+esc(sub)+'</p>'+(btn?'<button class="btn btn-primary" onclick="'+act+'">'+esc(btn)+'</button>':'')+'</div>';
}
function loadingState(msg){
  return'<div class="loading-state"><div class="spinner"></div><span>'+esc(msg||"Loading…")+'</span></div>';
}
function skeleton(n){
  return'<div class="skeleton-grid">'+Array(n||6).fill('<div class="skeleton-card"><div class="skeleton-photo"></div><div class="skeleton-body"><div class="skeleton-line medium"></div><div class="skeleton-line short"></div></div></div>').join("")+'</div>';
}

/* ── KPI card ── */
function kpiCard(label,val,sub,icon,color,trend){
  return'<div class="kpi kpi-'+color+'">'
    +'<div class="kpi-icon '+color+'">'+icon+'</div>'
    +'<div class="kpi-label">'+esc(label)+'</div>'
    +'<div class="kpi-value">'+esc(val)+'</div>'
    +'<div class="kpi-sub">'+(trend?'<span class="kpi-trend up">'+trend+'</span>':'')+esc(sub)+'</div>'
    +'</div>';
}

/* ── Spec item ── */
function si(k,v){return'<div class="spec-item"><div class="spec-key">'+esc(k)+'</div><div class="spec-val">'+esc(v==null?"—":v)+'</div></div>';}

/* ══════════════════════ DASHBOARD ══════════════════════ */
function renderDashboard(){
  setContent(loadingState("Loading dashboard…"));
  Promise.all([
    GET(API+"/ops/analytics").catch(function(){return null;}),
    GET(API+"/approval/pending?statuses=AI_DRAFT,EXTRACTED,NEEDS_REVIEW&limit=20").catch(function(){return[];})
  ]).then(function(res){paintDashboard(res[0]||{},res[1]||[]);});
}

function paintDashboard(a,pending){
  var sb=a.status_breakdown||{};var total=a.total_vehicles||1;

  var kpis=[
    kpiCard("Total Inventory",  num(a.total_vehicles||0),  "All vehicles",    svgIcon("car"),    "orange"),
    kpiCard("For Sale",         num(a.active_for_sale||0), "Active listings", svgIcon("check"),  "green"),
    kpiCard("Sold",             num(a.sold||0),            "All time",        svgIcon("money"),  "blue"),
    kpiCard("Customers",        num(a.total_customers||0), "In CRM",          svgIcon("users"),  "purple"),
    kpiCard("Pending Review",   num(pending.length),       "Awaiting action", svgIcon("alert"),  "red"),
    kpiCard("Open Handoffs",    num(a.open_handoffs||0),   "Needs attention", svgIcon("phone"),  "orange")
  ];

  var actHtml=pending.slice(0,5).map(function(v){
    var conf=v.confidence_summary||{};var fields=Object.keys(conf);
    var avg=fields.length?fields.reduce(function(s,f){return s+(conf[f].confidence||0);},0)/fields.length:0;
    return'<div class="activity-item" style="cursor:pointer" onclick="navigate(\'approval\')">'
      +'<div class="activity-icon '+(avg>=0.9?"green":avg>=0.7?"orange":"red")+'" style="border-radius:var(--radius)">'
        +'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2m14 0h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/><rect x="1" y="11" width="22" height="6" rx="1"/></svg>'
      +'</div>'
      +'<div class="activity-body"><div class="activity-title">'+esc(v.vehicle_name||v.stock_id||"New vehicle")+'</div>'
      +'<div class="activity-sub">'+bdg(v.status)+' · Confidence: <span style="color:'+confColor(avg)+'">'+Math.round(avg*100)+'%</span></div></div>'
      +'<div class="activity-time">'+(v.ready_for_approval?'<span style="color:var(--success);font-weight:700">Ready ✓</span>':'Review')+'</div>'
      +'</div>';
  }).join("")||('<div style="padding:24px 22px;color:var(--text-muted);font-size:13.5px">No vehicles pending review.</div>');

  var statItems=[{l:"Available",v:sb.AVAILABLE||0,c:"#22c55e"},{l:"Reserved",v:sb.RESERVED||0,c:"#f59e0b"},{l:"Negotiation",v:sb.NEGOTIATION||0,c:"#3b82f6"},{l:"Published",v:(sb.PUBLISHED||0)+(sb.DEALER_APPROVED||0),c:"#f97316"},{l:"Needs Review",v:(sb.NEEDS_REVIEW||0)+(sb.AI_DRAFT||0)+(sb.EXTRACTED||0),c:"#a855f7"},{l:"Sold",v:sb.SOLD||0,c:"#64748b"}];
  var qsHtml=statItems.map(function(i){var p=Math.round(i.v/total*100);return'<div class="qs-item"><div><div class="qs-label"><span class="qs-dot" style="background:'+i.c+'"></span>'+esc(i.l)+'</div><div class="qs-bar-wrap mt-8"><div class="qs-bar" style="width:'+p+'%;background:'+i.c+'"></div></div></div><div class="qs-val">'+i.v+'</div></div>';}).join("");

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Dashboard</h1><p>Welcome back, Admin. Here\'s KM Car Deals at a glance.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" onclick="navigate(\'analytics\')">'+svgIcon("bar")+'Full Report</button></div></div>'
    +'<div class="kpi-grid">'+kpis.join("")+'</div>'
    +'<div class="charts-row mb-24">'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Revenue & Sales Trend</span></div>'
      +'<div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="revenueChart"></canvas></div></div></div>'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock by Status</span></div>'
      +'<div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="statusChart"></canvas></div></div></div>'
    +'</div>'
    +'<div class="bottom-row">'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Pending Approval</span><button class="btn btn-ghost btn-sm" onclick="navigate(\'approval\')">View all →</button></div>'
      +'<div class="activity-list">'+actHtml+'</div></div>'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock Health</span></div>'
      +'<div class="quick-stats">'+qsHtml+'</div>'
      +'<div style="padding:14px 22px 20px;display:flex;flex-direction:column;gap:10px">'
        +'<button class="btn btn-primary" onclick="navigate(\'intake\')">'+svgIcon("spark")+' New AI Intake</button>'
        +'<a class="btn btn-ghost" href="/catalog" target="_blank">'+svgIcon("globe")+' Public Catalog ↗</a>'
      +'</div></div>'
    +'</div>'
  );
  buildRevenueChart();
  buildStatusChart(sb);
}

function buildRevenueChart(){
  var c=$("#revenueChart");if(!c)return;destroyChart("revenue");
  var d=gc();
  CHARTS.revenue=new Chart(c,{type:"line",data:{labels:["Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"],datasets:[
    {label:"Revenue (₹L)",data:Array(12).fill(0),borderColor:"#f97316",backgroundColor:"rgba(249,115,22,.12)",borderWidth:2.5,tension:.4,fill:true,pointBackgroundColor:"#f97316",pointRadius:4,pointHoverRadius:6},
    {label:"Units",data:Array(12).fill(0),borderColor:"#3b82f6",backgroundColor:"rgba(59,130,246,.08)",borderWidth:2,tension:.4,fill:true,pointBackgroundColor:"#3b82f6",pointRadius:3,pointHoverRadius:5,yAxisID:"y1"}
  ]},options:{maintainAspectRatio:false,interaction:{mode:"index",intersect:false},plugins:{legend:{position:"top",align:"end",labels:{boxWidth:10,boxHeight:10,padding:14,color:d.text,font:{size:12}}},tooltip:d.tip},scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},y:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11},callback:function(v){return"₹"+v+"L";}},position:"left"},y1:{grid:{drawOnChartArea:false},ticks:{color:d.text,font:{size:11}},position:"right"}}}});
}

function buildStatusChart(sb){
  var c=$("#statusChart");if(!c)return;destroyChart("status");
  var palette={AVAILABLE:"#22c55e",RESERVED:"#f59e0b",NEGOTIATION:"#3b82f6",PUBLISHED:"#f97316",DEALER_APPROVED:"#f97316",NEEDS_REVIEW:"#a855f7",AI_DRAFT:"#0ea5e9",EXTRACTED:"#6366f1",SOLD:"#64748b",ARCHIVED:"#334155"};
  var labels=[],vals=[],cols=[];
  Object.keys(sb).forEach(function(k){if(sb[k]>0){labels.push(k.replace(/_/g," "));vals.push(sb[k]);cols.push(palette[k]||"#64748b");}});
  if(!vals.length){labels=["No data"];vals=[1];cols=["#334155"];}
  var d=gc();var dk=document.documentElement.dataset.theme==="dark";
  CHARTS.status=new Chart(c,{type:"doughnut",data:{labels:labels,datasets:[{data:vals,backgroundColor:cols,borderWidth:2,borderColor:dk?"#131d2e":"#fff",hoverOffset:8}]},options:{maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{padding:12,boxWidth:10,boxHeight:10,color:d.text,font:{size:11.5}}},tooltip:d.tip}}});
}

/* ══════════════════════ INVENTORY ══════════════════════ */
function renderInventory(){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Inventory</h1><p>All vehicles in stock.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" id="exportBtn">'+svgIcon("export")+' Export</button>'
    +'<button class="btn btn-primary btn-sm" onclick="navigate(\'intake\')">'+svgIcon("plus")+' Add Vehicle</button></div></div>'
    +'<div class="toolbar"><div class="toolbar-left">'
      +'<div class="search-box"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input type="text" id="invQ" placeholder="Search make, model, stock ID…" value="'+esc(S.q)+'"></div>'
      +'<div class="filter-pills">'
      +["all","AI_DRAFT","EXTRACTED","NEEDS_REVIEW","DEALER_APPROVED","PUBLISHED","AVAILABLE","RESERVED","NEGOTIATION","SOLD"].map(function(f){
        var lbl={all:"All",AI_DRAFT:"Draft",EXTRACTED:"Extracted",NEEDS_REVIEW:"Review",DEALER_APPROVED:"Approved",PUBLISHED:"Published",AVAILABLE:"Available",RESERVED:"Reserved",NEGOTIATION:"Negotiation",SOLD:"Sold"}[f]||f;
        return'<button class="pill filter-pill'+(S.filter===f?" active":"")+ '" data-f="'+f+'">'+lbl+'</button>';
      }).join("")
      +'</div>'
    +'</div>'
    +'<div class="toolbar-right"><div class="view-toggle">'
      +'<button class="view-btn'+(S.mode==="grid"?" active":"")+ '" id="vgrid" title="Grid">'+svgIcon("grid")+'</button>'
      +'<button class="view-btn'+(S.mode==="list"?" active":"")+ '" id="vlist" title="List">'+svgIcon("list")+'</button>'
    +'</div></div></div>'
    +'<div id="invBody"></div>'
  );
  $$(".filter-pill").forEach(function(b){b.addEventListener("click",function(){S.filter=b.dataset.f;$$(".filter-pill").forEach(function(p){p.classList.toggle("active",p.dataset.f===S.filter);});loadInv();});});
  var qi=$("#invQ");if(qi)qi.addEventListener("input",function(){S.q=qi.value;clearTimeout(S._st);S._st=setTimeout(loadInv,200);});
  var vg=$("#vgrid"),vl=$("#vlist");
  if(vg)vg.addEventListener("click",function(){S.mode="grid";vg.classList.add("active");vl.classList.remove("active");loadInv();});
  if(vl)vl.addEventListener("click",function(){S.mode="list";vl.classList.add("active");vg.classList.remove("active");loadInv();});
  var eb=$("#exportBtn");if(eb)eb.addEventListener("click",function(){GET(API+"/ops/excel/export").then(function(){toast("Export started","success");}).catch(function(){toast("Connect backend to export","info");});});
  loadInv();
}

function loadInv(){
  var body=$("#invBody");if(!body)return;
  body.innerHTML=skeleton(6);
  var url=API+"/vehicles?limit=100&active_only=false"+(S.filter&&S.filter!=="all"?"&status="+S.filter:"")+(S.q?"&q="+encodeURIComponent(S.q):"");
  GET(url).then(function(cars){
    if(!body.parentNode)return;
    if(!cars||!cars.length){body.innerHTML=emptyState(svgIcon("car"),"No vehicles found",S.filter!=="all"||S.q?"Try a different filter.":"Add your first vehicle via AI Intake.",S.filter==="all"&&!S.q?"Add Vehicle":null,"navigate('intake')");return;}
    body.innerHTML='<div class="inv-grid'+(S.mode==="list"?" list-view":"")+'">'+cars.map(carCard).join("")+'</div>';
  }).catch(function(){body.innerHTML=emptyState(svgIcon("alert"),"Backend offline","Start the server to see inventory.","","");});
}

function carCard(v){
  var photos=v.photos||[];var main=photos.slice().sort(function(a,b){return(b.is_primary?1:0)-(a.is_primary?1:0);})[0];
  var imgHtml=main?'<img src="'+esc(purl(main))+'" alt="'+esc(v.vehicle_name||"")+'" loading="lazy">'
    :'<div class="car-photo-placeholder">'+svgIcon("car")+'</div>';
  var name=v.vehicle_name||((v.manufacturer||"")+" "+(v.model||"")).trim()||"Vehicle";
  var isWorkflow=["AI_DRAFT","EXTRACTED","NEEDS_REVIEW","DEALER_APPROVED"].includes(v.status);
  return'<div class="car-card">'
    +'<div class="car-photo"><div class="photo-gradient"></div>'+imgHtml
    +'<div class="badge-pos">'+bdg(v.status)+'</div>'
    +(photos.length>1?'<div class="photo-count"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="11" height="11"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>'+photos.length+'</div>':'')
    +'</div>'
    +'<div class="car-body">'
      +'<div class="car-top"><div><div class="car-name">'+esc(name)+'</div><div class="car-id">'+esc(v.stock_id||"")+'</div></div><div class="car-price">'+money(v.selling_price||v.price)+'</div></div>'
      +'<div class="car-specs">'+si("Year",v.manufacturing_year)+si("Fuel",v.fuel_type)+si("Trans.",v.transmission)+si("KM",km(v.mileage_km))+si("Owner",v.owner_count)+si("City",v.location)+'</div>'
      +'<div class="car-footer">'
        +'<button class="btn btn-ghost btn-sm flex-1" onclick="'+(isWorkflow?"showApprovalDetail('"+esc(v.vehicle_id)+"')":"showVehicle('"+esc(v.vehicle_id)+"')")+'">'+svgIcon("eye")+' '+(isWorkflow?"Review":"Details")+'</button>'
        +(isWorkflow&&v.status!=="DEALER_APPROVED"?'<button class="btn btn-primary btn-sm" onclick="quickApprove(\''+esc(v.vehicle_id)+'\')">'+svgIcon("check")+' Approve</button>':'')
        +(v.status==="DEALER_APPROVED"?'<button class="btn btn-success btn-sm" onclick="quickPublish(\''+esc(v.vehicle_id)+'\')">'+svgIcon("globe")+' Publish</button>':'')
        +(!isWorkflow&&v.status!=="SOLD"&&v.status!=="ARCHIVED"?'<select class="input status-select" onchange="setVehicleStatus(\''+esc(v.vehicle_id)+'\',this.value)"><option value="">Status…</option>'+["AVAILABLE","RESERVED","NEGOTIATION","SOLD"].map(function(s){return'<option'+(v.status===s?" selected":"")+'>'+s.replace(/_/g," ")+'</option>';}).join("")+'</select>':'')
      +'</div>'
    +'</div></div>';
}

window.quickApprove=function(id){POST(API+"/approval/"+id+"/approve",{approved_by:"admin"}).then(function(){toast("Vehicle approved","success");loadInv();updateApprovalBadge();}).catch(function(e){toast(e.message,"error");});};
window.quickPublish=function(id){POST(API+"/approval/"+id+"/publish",{published_by:"admin"}).then(function(){toast("Vehicle published to catalog","success");loadInv();updateApprovalBadge();}).catch(function(e){toast(e.message,"error");});};
window.setVehicleStatus=function(id,status){if(!status)return;POST(API+"/vehicles/"+id+"/status",{status:status,reason:"admin-ui"}).then(function(){toast("Status updated","success");loadInv();}).catch(function(e){toast(e.message,"error");});};
window.showVehicle=function(id){GET(API+"/vehicles/"+id).then(function(v){showVehicleModal(v);}).catch(function(e){toast(e.message,"error");});};
window.showApprovalDetail=function(id){renderApprovalDetail(id);};

function showVehicleModal(v){
  var photos=(v.photos||[]);
  var ph=photos.length?'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">'+photos.map(function(p){return'<img src="'+esc(purl(p))+'" style="width:140px;height:96px;object-fit:cover;border-radius:10px;cursor:pointer;border:1px solid var(--border)" onclick="window.open(this.src)" loading="lazy">';}).join("")+'</div>':'<div style="height:80px;display:grid;place-items:center;background:var(--surface-2);border-radius:10px;margin-bottom:18px;color:var(--text-muted)">No photos</div>';
  var name=v.vehicle_name||((v.manufacturer||"")+" "+(v.model||"")).trim();
  var facts=(v.facts||[]).map(function(f){return'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px"><span class="text-2">'+esc(f.field)+'</span><span class="font-semibold">'+esc(f.value||"—")+'</span></div>';}).join("")||'<div class="text-muted" style="font-size:13px;padding:10px 0">No facts recorded</div>';
  openModal(name,
    ph
    +'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px"><div>'
      +'<div style="font-size:22px;font-weight:900;color:var(--brand-primary)">'+money(v.selling_price||v.price)+'</div>'
      +'<div style="font-weight:700;margin-top:4px">'+esc(name)+'</div></div>'
      +'<div>'+bdg(v.status)+' <span class="badge badge-outline" style="margin-left:4px">'+esc(v.stock_id||"")+'</span></div></div>'
    +'<div class="car-specs" style="margin-bottom:16px">'+si("Year",v.manufacturing_year)+si("Fuel",v.fuel_type)+si("Trans.",v.transmission)+si("KM",km(v.mileage_km))+si("Owner",v.owner_count)+si("Color",v.vehicle_color)+si("Location",v.location)+'</div>'
    +'<div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Extracted Facts</div>'+facts
  );
}

/* ══════════════════════ AI INTAKE ══════════════════════ */
function renderIntake(){
  intakeFiles=[];
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>AI Vehicle Intake</h1><p>Upload RC card and photos — AI extracts all details automatically.</p></div></div>'
    +'<div class="grid-2" style="align-items:start">'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad">'
          +'<div class="form-section-title">'+svgIcon("camera")+' RC Card & Photos</div>'
          +'<div class="dropzone" id="dz"><div class="dropzone-icon">'+svgIcon("upload")+'</div><h3>Drag & drop files here</h3><p>or <strong>browse</strong> to choose</p><p style="margin-top:6px;font-size:12px">RC image, insurance, PUC, car photos · Max 20 files</p></div>'
          +'<input type="file" id="fileInput" multiple accept="image/*,.pdf" hidden>'
          +'<div class="file-list" id="fileList"></div>'
        +'</div>'
        +'<div class="card card-pad">'
          +'<div class="form-section-title">'+svgIcon("info")+' Seller Details <span class="text-muted" style="text-transform:none;letter-spacing:0;font-weight:400">(optional)</span></div>'
          +'<div class="form-grid">'
            +'<div class="field"><label>Seller WhatsApp</label><input class="input" id="fWhat" placeholder="91XXXXXXXXXX"></div>'
            +'<div class="field"><label>Vehicle hint</label>'
              +'<div style="display:flex;gap:8px"><input class="input" id="fName" placeholder="e.g. Hyundai Creta SX 2022"><button class="btn btn-ghost btn-sm" id="voiceBtn" title="Voice input">'+svgIcon("mic")+'</button></div>'
            +'</div>'
            +'<div class="field"><label>Price (₹) — leave blank if unknown</label><input class="input" id="fPrice" placeholder="e.g. 12.5 lakh"></div>'
            +'<div class="field"><label>Referral Source</label>'
              +'<select class="input" id="fReferral"><option value="">Select referral…</option>'
              +["WALK_IN","WHATSAPP","INSTAGRAM","FACEBOOK","WEBSITE","REFERENCE","DEALER","CUSTOMER","OTHER"].map(function(r){return'<option value="'+r+'">'+r.replace(/_/g," ")+'</option>';}).join("")
              +'</select>'
            +'</div>'
          +'</div>'
        +'</div>'
      +'</div>'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad">'
          +'<div class="form-section-title">'+svgIcon("spark")+' AI Processing</div>'
          +'<div style="display:flex;flex-direction:column;gap:14px">'
            +'<div class="field"><label>Enhance Photos</label><select class="input" id="fProc"><option value="true">Yes — generate web/social/thumbnail variants</option><option value="false">No — store originals only</option></select></div>'
            +'<div class="field"><label>Background Style</label><select class="input" id="fBg"><option value="premium_showroom">Premium Showroom</option><option value="dealership">Professional Dealership</option><option value="km_branded">KM Branded</option><option value="neutral_studio">Neutral Studio</option></select></div>'
          +'</div>'
        +'</div>'
        +'<div class="card card-pad" style="font-size:13px;color:var(--text-2)">'
          +'<div class="form-section-title">'+svgIcon("info")+' What the AI does</div>'
          +['Reads RC via OCR — extracts registration, chassis, engine, owner','Identifies make / model / year from photos','Detects duplicate registrations before creating a record','Flags low-confidence fields for your review','Generates professional listing description','Never publishes without your approval'].map(function(t,i){return'<div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:9px"><div style="width:20px;height:20px;border-radius:50%;background:var(--brand-gradient);color:#fff;display:grid;place-items:center;font-size:10px;font-weight:800;flex-shrink:0">'+(i+1)+'</div><span>'+esc(t)+'</span></div>';}).join("")
        +'</div>'
        +'<button class="btn btn-primary btn-lg w-full" id="intakeBtn" style="justify-content:center">'+svgIcon("spark")+' Run AI Intake</button>'
        +'<div id="progWrap" style="display:none;margin-top:16px">'
          +'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px"><span id="progLabel">Uploading…</span><span id="progPct">0%</span></div>'
          +'<div class="progress-wrap"><div class="progress-bar" id="progBar" style="width:0%"></div></div>'
        +'</div>'
      +'</div>'
    +'</div>'
  );
  wireDropzone();
  wireVoice();
  var btn=$("#intakeBtn");if(btn)btn.addEventListener("click",runIntake);
}

function wireDropzone(){
  var dz=$("#dz"),fi=$("#fileInput");if(!dz||!fi)return;
  dz.addEventListener("click",function(e){if(e.target!==fi)fi.click();});
  dz.addEventListener("dragover",function(e){e.preventDefault();dz.classList.add("drag");});
  dz.addEventListener("dragleave",function(){dz.classList.remove("drag");});
  dz.addEventListener("drop",function(e){e.preventDefault();dz.classList.remove("drag");addFiles(e.dataTransfer.files);});
  fi.addEventListener("change",function(){addFiles(fi.files);fi.value="";});
}

function wireVoice(){
  var btn=$("#voiceBtn");if(!btn)return;
  if(!("webkitSpeechRecognition" in window||"SpeechRecognition" in window)){btn.style.display="none";return;}
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  btn.addEventListener("click",function(){
    var rec=new SR();rec.lang="en-IN";rec.interimResults=false;
    btn.innerHTML=svgIcon("mic");btn.style.color="var(--danger)";btn.disabled=true;
    rec.onresult=function(e){var txt=e.results[0][0].transcript;var f=$("#fName");if(f)f.value=txt;toast("Heard: "+txt,"info","Voice Input");};
    rec.onerror=function(){toast("Voice input failed","error");};
    rec.onend=function(){btn.innerHTML=svgIcon("mic");btn.style.color="";btn.disabled=false;};
    rec.start();
  });
}

function addFiles(list){
  Array.from(list).forEach(function(f){
    if(intakeFiles.length>=20){toast("Max 20 files","warning");return;}
    intakeFiles.push(f);
    var li=document.createElement("div");li.className="file-item";
    li.innerHTML='<div class="file-item-icon">'+svgIcon(f.type.startsWith("image")?"camera":"docs")+'</div>'
      +'<div class="file-item-name">'+esc(f.name)+'</div>'
      +'<div class="file-item-size">'+(f.size/1024).toFixed(1)+' KB</div>'
      +'<button class="file-item-rm" aria-label="Remove"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button>';
    li.querySelector(".file-item-rm").onclick=function(){var i=intakeFiles.indexOf(f);if(i>-1)intakeFiles.splice(i,1);li.remove();};
    var fl=$("#fileList");if(fl)fl.appendChild(li);
  });
}

function runIntake(){
  var btn=$("#intakeBtn"),pw=$("#progWrap");if(!btn)return;
  var hint=($("#fName")||{value:""}).value;
  var price=($("#fPrice")||{value:""}).value;
  if(price){hint=(hint+" "+price+" lakh").trim();}
  if(!intakeFiles.length&&!hint){toast("Add files or a vehicle description first","warning");return;}
  btn.disabled=true;btn.innerHTML=svgIcon("spark")+" Processing…";if(pw)pw.style.display="block";
  var pct=0,si=0,steps=["Uploading files…","Reading RC document…","Running OCR extraction…","Analysing photos…","Checking for duplicates…","Building confidence scores…","Creating stock record…"];
  var timer=setInterval(function(){pct=Math.min(pct+Math.random()*13,92);var bar=$("#progBar"),lbl=$("#progLabel"),pp=$("#progPct");if(bar)bar.style.width=pct.toFixed(0)+"%";if(pp)pp.textContent=pct.toFixed(0)+"%";if(lbl&&si<steps.length)lbl.textContent=steps[si++];},550);
  var fd=new FormData();
  intakeFiles.forEach(function(f){fd.append("files",f,f.name);});
  fd.append("message",hint);
  fd.append("seller_whatsapp",($("#fWhat")||{value:""}).value);
  fd.append("referral",($("#fReferral")||{value:""}).value);
  fd.append("intake_source","ADMIN_UI");
  fd.append("process_images",($("#fProc")||{value:"false"}).value);
  fd.append("background",($("#fBg")||{value:"premium_showroom"}).value);
  http("POST",API+"/intake/vehicle",fd).then(function(r){
    clearInterval(timer);var bar=$("#progBar");if(bar)bar.style.width="100%";var pp=$("#progPct");if(pp)pp.textContent="100%";
    setTimeout(function(){
      if(btn){btn.disabled=false;btn.innerHTML=svgIcon("spark")+" Run AI Intake";}
      if(pw)pw.style.display="none";
      toast(r&&r.message||"Intake complete","success","Done");
      intakeFiles=[];var fl=$("#fileList");if(fl)fl.innerHTML="";
      if(r&&r.vehicle_id){setTimeout(function(){renderApprovalDetail(r.vehicle_id);},400);}
      else{navigate("approval");}
      updateApprovalBadge();
    },600);
  }).catch(function(e){
    clearInterval(timer);
    if(btn){btn.disabled=false;btn.innerHTML=svgIcon("spark")+" Run AI Intake";}
    if(pw)pw.style.display="none";
    toast(e.message||"Intake failed","error");
  });
}

/* ══════════════════════ APPROVAL QUEUE ══════════════════════ */
function renderApproval(){
  setContent(loadingState("Loading approval queue…"));
  GET(API+"/approval/pending?statuses=AI_DRAFT,EXTRACTED,NEEDS_REVIEW,DEALER_APPROVED&limit=100").then(function(items){
    paintApprovalQueue(items||[]);
  }).catch(function(){setContent(emptyState(svgIcon("alert"),"Backend offline","Start the server.","",""));});
}

function paintApprovalQueue(items){
  if(!items.length){setContent(emptyState(svgIcon("check"),"All clear","No vehicles pending review.","Run AI Intake","navigate('intake')"));return;}
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Approval Queue</h1><p>'+items.length+' vehicle'+(items.length===1?"":"s")+' awaiting action.</p></div></div>'
    +'<div class="card">'
      +'<div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Pending Vehicles</span></div>'
      +'<div class="table-wrap"><table><thead><tr><th>Stock ID</th><th>Vehicle</th><th>Status</th><th>Avg Confidence</th><th>Conflicts</th><th>Referral</th><th>Photos</th><th>Actions</th></tr></thead>'
      +'<tbody>'+items.map(apqRow).join("")+'</tbody></table></div>'
    +'</div>'
  );
}

function apqRow(v){
  var conf=v.confidence_summary||{};var fields=Object.keys(conf);
  var avg=fields.length?fields.reduce(function(s,f){return s+(conf[f].confidence||0);},0)/fields.length:0;
  var confBar='<div style="display:flex;align-items:center;gap:8px"><div style="width:60px;height:6px;background:var(--surface-3);border-radius:3px;overflow:hidden"><div style="width:'+Math.round(avg*100)+'%;height:100%;background:'+confColor(avg)+';border-radius:3px"></div></div><span style="font-size:12px;font-weight:700;color:'+confColor(avg)+'">'+Math.round(avg*100)+'%</span></div>';
  var actions='<button class="btn btn-ghost btn-sm" onclick="renderApprovalDetail(\''+esc(v.vehicle_id)+'\')">'+svgIcon("eye")+' Review</button>';
  if(["AI_DRAFT","EXTRACTED","NEEDS_REVIEW"].includes(v.status)){
    actions+=' <button class="btn btn-primary btn-sm" onclick="quickApprove(\''+esc(v.vehicle_id)+'\')">'+svgIcon("check")+' Approve</button>';
    actions+=' <button class="btn btn-danger btn-sm" onclick="rejectPrompt(\''+esc(v.vehicle_id)+'\')"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M18 6 6 18M6 6l12 12"/></svg> Reject</button>';
  }
  if(v.status==="DEALER_APPROVED"){
    actions+=' <button class="btn btn-success btn-sm" onclick="quickPublish(\''+esc(v.vehicle_id)+'\')">'+svgIcon("globe")+' Publish</button>';
  }
  return'<tr>'
    +'<td class="font-mono" style="font-size:11.5px">'+esc(v.stock_id||"—")+'</td>'
    +'<td><div style="font-weight:600;font-size:13.5px">'+esc(v.vehicle_name||"Unnamed")+'</div><div class="text-muted" style="font-size:12px">'+esc(v.registration_number||"No reg #")+'</div></td>'
    +'<td>'+bdg(v.status)+'</td>'
    +'<td>'+confBar+'</td>'
    +'<td>'+(v.conflicts>0?'<span style="color:var(--danger);font-weight:700">'+v.conflicts+' open</span>':'<span class="text-muted">None</span>')+'</td>'
    +'<td class="text-2" style="font-size:12.5px">'+esc(v.referral||"—")+'</td>'
    +'<td class="text-muted">'+v.photos+'</td>'
    +'<td style="white-space:nowrap">'+actions+'</td>'
    +'</tr>';
}

window.renderApprovalDetail=function(id){
  setContent(loadingState("Loading vehicle review…"));
  GET(API+"/approval/"+id).then(function(v){
    S.view="approval";var pt=$("#pageTitle");if(pt)pt.textContent="Approval Queue";
    $$(".nav-item[data-view]").forEach(function(n){n.classList.toggle("active",n.dataset.view==="approval");});
    paintApprovalDetail(v);
  }).catch(function(e){toast(e.message,"error");navigate("approval");});
};

function paintApprovalDetail(v){
  var conf=v.confidence_summary||{};
  var needsReview=v.needs_review_fields||[];var lowConf=v.low_confidence_fields||[];
  var confRows=(v.facts||[]).map(function(f){
    var pct=Math.round((f.confidence||0)*100);
    return'<tr><td style="font-weight:600;font-size:12px;white-space:nowrap">'+esc(f.field)+'</td>'
      +'<td style="font-size:13px">'+esc(f.value||"—")+'</td>'
      +'<td><span class="badge badge-outline" style="font-size:10px">'+esc(f.source)+'</span></td>'
      +'<td><div style="display:flex;align-items:center;gap:8px"><div style="width:60px;height:5px;background:var(--surface-3);border-radius:3px;overflow:hidden"><div style="width:'+pct+'%;height:100%;background:'+confColor(f.confidence||0)+';border-radius:3px"></div></div><span style="font-size:11px;color:'+confColor(f.confidence||0)+'">'+pct+'%</span>'+(f.needs_review?'<span style="color:var(--warning);font-size:10px">⚠</span>':'')+'</div></td>'
      +'</tr>';
  }).join("");

  var banner=v.ready_for_approval
    ?'<div style="background:var(--success-bg);color:var(--success);border:1px solid var(--success);border-radius:var(--radius);padding:12px 16px;margin-bottom:20px;font-weight:700;display:flex;align-items:center;gap:8px">'+svgIcon("check")+' Ready for Approval — all fields have high confidence</div>'
    :(needsReview.length||lowConf.length
      ?'<div style="background:var(--warning-bg);color:var(--warning);border:1px solid var(--warning);border-radius:var(--radius);padding:12px 16px;margin-bottom:20px;display:flex;align-items:center;gap:8px">'+svgIcon("alert")+' Fields needing review: <strong>'+esc([...new Set([...needsReview,...lowConf])].join(", "))+'</strong></div>'
      :"");

  var photosHtml=(v.photos_detail||[]).map(function(p){
    return'<div style="position:relative;cursor:pointer" onclick="window.open(\''+esc(purl(p))+'\')">'
      +'<img src="'+esc(purl(p))+'" style="width:100%;height:100px;object-fit:cover;border-radius:8px;border:2px solid '+(p.is_primary?"var(--brand-primary)":"var(--border)")+'" loading="lazy">'
      +'<div style="position:absolute;bottom:4px;left:4px;font-size:10px;color:#fff;background:rgba(0,0,0,.6);border-radius:4px;padding:1px 5px">'+esc(p.category||"—")+'</div>'
      +(p.duplicate_of?'<div style="position:absolute;top:4px;right:4px;font-size:9px;background:var(--danger);color:#fff;border-radius:4px;padding:1px 5px">Dup</div>':'')
      +(p.blur_detected?'<div style="position:absolute;top:4px;right:4px;font-size:9px;background:var(--warning);color:#fff;border-radius:4px;padding:1px 5px">Blurry</div>':'')
      +'</div>';
  }).join("");

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>'+esc(v.vehicle_name||v.stock_id||"Vehicle Review")+'</h1><p>'+bdg(v.status)+' · '+esc(v.stock_id||"")+(v.registration_number?' · Reg: '+esc(v.registration_number):'')+'</p></div>'
    +'<div class="page-header-actions">'
    +(["AI_DRAFT","EXTRACTED","NEEDS_REVIEW"].includes(v.status)?'<button class="btn btn-primary" id="btnApprove">'+svgIcon("check")+' Approve</button> <button class="btn btn-danger" id="btnReject"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 6 6 18M6 6l12 12"/></svg> Reject</button>':'')
    +(v.status==="DEALER_APPROVED"?'<button class="btn btn-success" id="btnPublish">'+svgIcon("globe")+' Publish Now</button>':'')
    +'<button class="btn btn-ghost" onclick="navigate(\'approval\')">← Back</button></div></div>'
    +banner
    +'<div style="display:grid;grid-template-columns:1.5fr 1fr;gap:20px;align-items:start">'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad">'
          +'<div class="card-title mb-16"><span class="card-title-dot"></span>Edit & Confirm Fields</div>'
          +'<div class="form-grid">'
          +["manufacturer","model","variant","vehicle_color","fuel_type","transmission","owner_count","mileage_km","location","body_type"].map(function(k){var cur=v[k]||(conf[k]&&conf[k].value)||"";return'<div class="field"><label>'+k.replace(/_/g," ")+'</label><input class="input edit-field" data-key="'+k+'" value="'+esc(cur)+'"></div>';}).join("")
          +'<div class="field"><label>manufacturing year</label><input class="input edit-field" data-key="manufacturing_year" value="'+esc(v.manufacturing_year||"")+'"></div>'
          +'<div class="field"><label>selling price (₹)</label><input class="input edit-field" data-key="selling_price" value="'+esc(v.selling_price||"")+'"></div>'
          +'</div>'
          +'<div class="field mt-16"><label>Description (auto-generated)</label><textarea class="input edit-field" data-key="description" rows="4">'+esc(v.description||"")+'</textarea></div>'
          +'<div class="form-grid mt-16"><div class="field"><label>Referral Source</label><select class="input edit-field" data-key="referral"><option value="">—</option>'+["WALK_IN","WHATSAPP","INSTAGRAM","FACEBOOK","WEBSITE","REFERENCE","DEALER","CUSTOMER","OTHER"].map(function(r){return'<option value="'+r+'"'+(v.referral===r?" selected":"")+'>'+r.replace(/_/g," ")+'</option>';}).join("")+'</select></div></div>'
          +'<div style="display:flex;gap:10px;margin-top:16px">'
            +'<button class="btn btn-ghost btn-sm" id="btnSaveFields">'+svgIcon("check")+' Save Changes</button>'
            +'<button class="btn btn-ghost btn-sm" id="btnRegenDesc">↺ Regenerate Description</button>'
          +'</div>'
        +'</div>'
        +'<div class="card card-pad">'
          +'<div class="card-title mb-16"><span class="card-title-dot"></span>Photos ('+v.photos+')</div>'
          +(photosHtml?'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px">'+photosHtml+'</div>':emptyState(svgIcon("camera"),"No photos","Upload via AI Intake","",""))
        +'</div>'
      +'</div>'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad">'
          +'<div class="card-title mb-16"><span class="card-title-dot"></span>AI Confidence</div>'
          +'<div class="table-wrap"><table><thead><tr><th>Field</th><th>Value</th><th>Source</th><th>Confidence</th></tr></thead><tbody>'+confRows+'</tbody></table></div>'
        +'</div>'
        +'<div class="card card-pad">'
          +'<div class="card-title mb-16"><span class="card-title-dot"></span>Status History</div>'
          +(v.status_history||[]).map(function(h){return'<div style="font-size:12.5px;padding:6px 0;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px">'+bdg(h.from||"START")+' → '+bdg(h.to)+' <span class="text-muted" style="margin-left:4px">'+esc(h.by||"system")+'</span></div>';}).join("")
        +'</div>'
      +'</div>'
    +'</div>'
  );

  // Wire buttons
  var btnA=$("#btnApprove");if(btnA)btnA.onclick=function(){POST(API+"/approval/"+v.vehicle_id+"/approve",{approved_by:"admin"}).then(function(){toast("Approved","success");updateApprovalBadge();renderApprovalDetail(v.vehicle_id);}).catch(function(e){toast(e.message,"error");});};
  var btnR=$("#btnReject");if(btnR)btnR.onclick=function(){rejectPrompt(v.vehicle_id);};
  var btnP=$("#btnPublish");if(btnP)btnP.onclick=function(){POST(API+"/approval/"+v.vehicle_id+"/publish",{published_by:"admin"}).then(function(){toast("Published to catalog","success");updateApprovalBadge();navigate("approval");}).catch(function(e){toast(e.message,"error");});};
  var btnS=$("#btnSaveFields");if(btnS)btnS.onclick=function(){
    var payload={updated_by:"admin"};
    $$(".edit-field").forEach(function(el){var k=el.dataset.key;var val=el.value.trim();if(val)payload[k]=["manufacturing_year","owner_count","mileage_km"].includes(k)?Number(val):["selling_price"].includes(k)?parseFloat(val):val;});
    PATCH(API+"/approval/"+v.vehicle_id+"/fields",payload).then(function(){toast("Saved","success");renderApprovalDetail(v.vehicle_id);}).catch(function(e){toast(e.message,"error");});
  };
  var btnRD=$("#btnRegenDesc");if(btnRD)btnRD.onclick=function(){POST(API+"/approval/"+v.vehicle_id+"/generate-description",{}).then(function(r){var el=$(".edit-field[data-key='description']");if(el)el.value=r.description||"";toast("Description regenerated","success");}).catch(function(e){toast(e.message,"error");});};
}

window.rejectPrompt=function(id){
  openModal("Reject Vehicle",
    '<div class="field"><label>Rejection reason</label><textarea class="input" id="rejReason" rows="3" placeholder="What needs to be corrected?"></textarea></div>'
    +'<div style="margin-top:16px;display:flex;gap:10px">'
    +'<button class="btn btn-danger" onclick="doReject(\''+esc(id)+'\')">Reject</button>'
    +'<button class="btn btn-ghost" onclick="closeModal()">Cancel</button></div>'
  );
};
window.doReject=function(id){
  var r=($("#rejReason")||{value:"Rejected by admin"}).value||"Rejected by admin";
  POST(API+"/approval/"+id+"/reject",{reason:r,rejected_by:"admin"}).then(function(){closeModal();toast("Vehicle rejected","warning");renderApproval();updateApprovalBadge();}).catch(function(e){toast(e.message,"error");});
};

/* ══════════════════════ CUSTOMERS ══════════════════════ */
function renderCustomers(){
  setContent(loadingState("Loading customers…"));
  GET(API+"/customers?limit=200").then(function(rows){paintCustomers(rows||[]);}).catch(function(){setContent(emptyState(svgIcon("alert"),"Backend offline","","",""));});
}
function paintCustomers(rows){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Customers</h1><p>'+rows.length+' contact'+(rows.length!==1?"s":"")+'in CRM.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm">'+svgIcon("export")+' Export CSV</button></div></div>'
    +'<div class="card">'
      +'<div class="card-header"><span class="card-title"><span class="card-title-dot"></span>All Customers</span>'
        +'<div class="card-actions"><div class="search-box" style="max-width:220px"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input type="text" id="custQ" placeholder="Search…"></div></div>'
      +'</div>'
      +(rows.length
        ?'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>WhatsApp</th><th>City</th><th>Lead Status</th><th>Interest</th><th>Consent</th><th>Actions</th></tr></thead><tbody id="custBody">'+custRows(rows)+'</tbody></table></div>'
        :'<div>'+emptyState(svgIcon("users"),"No customers yet","Customers appear here once they interact via WhatsApp or are added manually.","","")+'</div>')
    +'</div>'
  );
  var qi=$("#custQ");
  if(qi&&rows.length)qi.addEventListener("input",function(){
    var q=qi.value.toLowerCase();
    var f=rows.filter(function(c){return(c.name||"").toLowerCase().includes(q)||(c.city||"").toLowerCase().includes(q)||(c.whatsapp_number||"").includes(q);});
    var tb=$("#custBody");if(tb)tb.innerHTML=custRows(f);
  });
}
function custRows(rows){
  if(!rows.length)return'<tr><td colspan="7">'+emptyState(svgIcon("users"),"No results","","","")+'</td></tr>';
  return rows.map(function(c){
    return'<tr>'
      +'<td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></div></td>'
      +'<td class="font-mono" style="font-size:12px">'+esc(c.whatsapp_number||"—")+'</td>'
      +'<td>'+esc(c.location||c.city||"—")+'</td>'
      +'<td>'+bdg(c.lead_status)+'</td>'
      +'<td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td>'
      +'<td>'+(c.opt_out?'<span class="badge badge-CLOSED_LOST">Opted Out</span>':'<span class="badge badge-AVAILABLE">Opted In</span>')+'</td>'
      +'<td><button class="btn btn-ghost btn-sm" onclick="genFollowup(\''+esc(c.customer_id)+'\')">'+svgIcon("chat")+' Follow-up</button></td>'
      +'</tr>';
  }).join("");
}
window.genFollowup=function(id){
  GET(API+"/customers/"+id+"/followup-message").then(function(r){
    openModal("AI Follow-up Message",
      '<div style="background:var(--surface-2);border-radius:var(--radius);padding:16px;font-size:14px;line-height:1.6;margin-bottom:16px">'+esc(r.message)+'</div>'
      +'<button class="btn btn-primary" onclick="navigator.clipboard.writeText(decodeURIComponent(\''+encodeURIComponent(r.message)+'\')).then(function(){\'success\'}).catch(function(){});toast(\'Copied!\',\'success\');closeModal()">'+svgIcon("check")+' Copy Message</button>'
      +' <button class="btn btn-ghost" onclick="closeModal()">Close</button>'
    );
  }).catch(function(e){toast(e.message,"error");});
};

/* ══════════════════════ LEADS ══════════════════════ */
function renderLeads(){
  GET(API+"/customers?limit=200").then(function(rows){
    rows=rows||[];var active=rows.filter(function(c){return c.lead_status!=="LOST"&&c.lead_status!=="NOT_INTERESTED";});
    setContent(
      '<div class="page-header"><div class="page-header-text"><h1>Leads Pipeline</h1><p>Track every lead from first contact to closed deal.</p></div></div>'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Active Leads</span></div>'
      +(active.length
        ?'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>Interest</th><th>Stage</th><th>WhatsApp</th><th>Actions</th></tr></thead><tbody>'
          +active.map(function(c){return'<tr>'
            +'<td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></td>'
            +'<td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td>'
            +'<td>'+bdg(c.lead_status)+'</td>'
            +'<td class="font-mono" style="font-size:12px">'+esc((c.whatsapp_number||"").replace("91",""))+'</td>'
            +'<td><button class="btn btn-ghost btn-sm" onclick="genFollowup(\''+esc(c.customer_id)+'\')">'+svgIcon("chat")+' Follow-up</button> <button class="btn btn-ghost btn-sm" onclick="updateLeadStatus(\''+esc(c.customer_id)+'\',\''+esc(c.lead_status)+'\')">'+svgIcon("edit")+' Status</button></td>'
            +'</tr>';}).join("")
          +'</tbody></table></div>'
        :'<div>'+emptyState(svgIcon("phone"),"No active leads","","","")+'</div>')
      +'</div>'
    );
  }).catch(function(){setContent(emptyState(svgIcon("alert"),"Backend offline","","",""));});
}
window.updateLeadStatus=function(id,cur){
  openModal("Update Lead Status",
    '<div class="field"><label>New Status</label><select class="input" id="newStatus">'+["NEW","CONTACTED","INTERESTED","QUALIFIED","NEGOTIATING","FOLLOW_UP","BOOKED","PURCHASED","LOST","NOT_INTERESTED"].map(function(s){return'<option'+(s===cur?" selected":"")+'>'+s+'</option>';}).join("")+'</select></div>'
    +'<div class="field mt-16"><label>Notes (optional)</label><input class="input" id="statusNotes" placeholder="Add a note…"></div>'
    +'<div style="margin-top:16px;display:flex;gap:10px">'
    +'<button class="btn btn-primary" onclick="doUpdateStatus(\''+esc(id)+'\')">Update</button>'
    +'<button class="btn btn-ghost" onclick="closeModal()">Cancel</button></div>'
  );
};
window.doUpdateStatus=function(id){
  var s=($("#newStatus")||{value:""}).value;var n=($("#statusNotes")||{value:""}).value;
  PATCH(API+"/customers/"+id+"/lead-status?status="+encodeURIComponent(s)+(n?"&notes="+encodeURIComponent(n):""),{}).then(function(){closeModal();toast("Lead status updated","success");renderLeads();}).catch(function(e){toast(e.message,"error");});
};

/* ══════════════════════ ANALYTICS ══════════════════════ */
function renderAnalytics(){
  setContent(loadingState("Building report…"));
  GET(API+"/ops/analytics").then(function(a){
    a=a||{};
    var kpis=[
      kpiCard("Total Vehicles",  num(a.total_vehicles||0),  "All stock",     svgIcon("car"),   "orange"),
      kpiCard("For Sale",        num(a.active_for_sale||0), "Ready to sell", svgIcon("check"), "green"),
      kpiCard("Sold",            num(a.sold||0),            "All time",      svgIcon("money"), "blue"),
      kpiCard("Avg Days to Sell",num(a.avg_days_to_sell||0),"Per vehicle",   svgIcon("spark"), "purple"),
      kpiCard("Revenue MTD",     money(a.revenue_mtd||0),   "This month",    svgIcon("money"), "orange"),
      kpiCard("Customers",       num(a.total_customers||0), "In CRM",        svgIcon("users"), "green")
    ];
    setContent(
      '<div class="page-header"><div class="page-header-text"><h1>Analytics</h1><p>Full performance overview.</p></div>'
      +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm">'+svgIcon("export")+' Export Report</button></div></div>'
      +'<div class="kpi-grid mb-24">'+kpis.join("")+'</div>'
      +'<div class="charts-row mb-24">'
        +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Revenue Trend</span></div><div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="revenueChart"></canvas></div></div></div>'
        +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Inventory by Status</span></div><div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="statusChart"></canvas></div></div></div>'
      +'</div>'
    );
    buildRevenueChart();buildStatusChart(a.status_breakdown||{});
  }).catch(function(){setContent(emptyState(svgIcon("alert"),"Backend offline","","",""));});
}

/* ══════════════════════ AUDIT ══════════════════════ */
function renderAudit(){
  setContent(loadingState("Loading audit log…"));
  GET(API+"/settings/audit-log?limit=100").then(function(logs){
    logs=logs||[];
    setContent(
      '<div class="page-header"><div class="page-header-text"><h1>Audit Log</h1><p>All AI and dealer actions recorded.</p></div></div>'
      +'<div class="card"><div class="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Notes</th></tr></thead><tbody>'
      +(logs.length?logs.map(function(l){
        return'<tr>'
          +'<td class="font-mono" style="font-size:11px;white-space:nowrap">'+esc((l.created_at||"").replace("T"," ").slice(0,19))+'</td>'
          +'<td style="font-weight:600">'+esc(l.actor||"system")+'</td>'
          +'<td><span class="badge badge-outline">'+esc(l.action)+'</span></td>'
          +'<td class="text-muted" style="font-size:12px">'+esc(l.entity_type||"")+(l.entity_id?" / "+l.entity_id.slice(0,8)+"…":"")+'</td>'
          +'<td class="text-2" style="max-width:280px;overflow:hidden;text-overflow:ellipsis;font-size:12px">'+esc(l.notes||JSON.stringify(l.after_data||{}).slice(0,80))+'</td>'
          +'</tr>';
      }).join(""):('<tr><td colspan="5">'+emptyState(svgIcon("docs"),"No audit entries yet","Actions will appear here.","","")+'</td></tr>'))
      +'</tbody></table></div></div>'
    );
  }).catch(function(){setContent(emptyState(svgIcon("alert"),"Backend offline","","",""));});
}

/* ══════════════════════ SETTINGS ══════════════════════ */
function renderSettings(){
  setContent(loadingState("Loading settings…"));
  GET(API+"/settings/business").then(function(s){paintSettings(s||{});}).catch(function(){paintSettings({});});
}
function paintSettings(s){
  var fields=[["business_name","Business Name"],["tagline","Tagline"],["address_line1","Address Line 1"],["address_line2","Address Line 2"],["city","City"],["state","State"],["pincode","Pincode"],["phone_primary","Primary Phone"],["phone_secondary","Secondary Phone"],["whatsapp_number","WhatsApp Number"],["email","Email"],["website_url","Website URL"],["google_maps_url","Google Maps URL"],["default_location","Default Location"],["currency","Currency"]];
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Business Settings</h1><p>KM Car Deals dealer configuration — stored in database, never hard-coded.</p></div></div>'
    +'<div class="card card-pad">'
    +'<div class="form-grid">'+fields.map(function(f){return'<div class="field"><label>'+esc(f[1])+'</label><input class="input sett-field" data-key="'+esc(f[0])+'" value="'+esc(s[f[0]]||"")+'"></div>';}).join("")
    +'<div class="field"><label>Auto-publish on Approval</label><select class="input sett-field" data-key="auto_publish"><option value="false"'+(s.auto_publish?"":' selected')+'>No — require manual publish</option><option value="true"'+(s.auto_publish?' selected':'')+'>Yes — auto-publish on dealer approval</option></select></div>'
    +'</div>'
    +'<button class="btn btn-primary mt-16" id="btnSaveSettings">'+svgIcon("check")+' Save Settings</button>'
    +'</div>'
  );
  var btn=$("#btnSaveSettings");
  if(btn)btn.onclick=function(){
    var payload={updated_by:"admin"};
    $$(".sett-field").forEach(function(el){var k=el.dataset.key;var v=el.value.trim();if(v!==undefined&&v!=="")payload[k]=k==="auto_publish"?(v==="true"):v;});
    PATCH(API+"/settings/business",payload).then(function(){toast("Settings saved","success");}).catch(function(e){toast(e.message,"error");});
  };
}

/* ══════════════════════ DOCS ══════════════════════ */
function renderDocs(){
  var eps=[{m:"GET",p:"/api/v1/vehicles",d:"List vehicles"},{m:"POST",p:"/api/v1/intake/vehicle",d:"AI intake upload"},{m:"GET",p:"/api/v1/approval/pending",d:"Approval queue"},{m:"POST",p:"/api/v1/approval/{id}/approve",d:"Approve vehicle"},{m:"POST",p:"/api/v1/approval/{id}/publish",d:"Publish vehicle"},{m:"GET",p:"/api/v1/customers",d:"List customers"},{m:"PATCH",p:"/api/v1/customers/{id}/lead-status",d:"Update lead status"},{m:"GET",p:"/api/v1/settings/business",d:"Business settings"},{m:"GET",p:"/api/v1/settings/audit-log",d:"Audit log"},{m:"GET",p:"/api/v1/ops/analytics",d:"Analytics"},{m:"GET",p:"/health",d:"Health check"}];
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>API Documentation</h1><p>Every backend endpoint powering this dashboard.</p></div></div>'
    +'<div class="docs-grid mb-24">'
    +'<a class="docs-card" href="/docs" target="_blank"><div class="docs-card-icon orange" style="font-size:22px">⚡</div><h3>Swagger UI</h3><p>Interactive API explorer — try endpoints live.</p><div class="arrow">Open '+svgIcon("arrow")+'</div></a>'
    +'<a class="docs-card" href="/redoc" target="_blank"><div class="docs-card-icon blue" style="font-size:22px">📖</div><h3>ReDoc</h3><p>Structured reference documentation.</p><div class="arrow">Open '+svgIcon("arrow")+'</div></a>'
    +'<a class="docs-card" href="/catalog" target="_blank"><div class="docs-card-icon green" style="font-size:22px">🌐</div><h3>Public Catalog</h3><p>Customer-facing vehicle listing page.</p><div class="arrow">Open '+svgIcon("arrow")+'</div></a>'
    +'</div>'
    +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Key Endpoints</span></div><div style="padding:18px 22px"><div class="endpoint-list">'
    +eps.map(function(e){return'<div class="endpoint"><span class="method '+e.m+'">'+e.m+'</span><span class="endpoint-path">'+esc(e.p)+'</span><span class="endpoint-desc">'+esc(e.d)+'</span></div>';}).join("")
    +'</div></div></div>'
  );
}

/* ── SVG icon helper ── */
function svgIcon(name){
  var icons={
    car:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2m14 0h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/><rect x="1" y="11" width="22" height="6" rx="1"/><path d="M5 11V8a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v3"/><circle cx="7.5" cy="17" r="1.5"/><circle cx="16.5" cy="17" r="1.5"/></svg>',
    check:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="20 6 9 17 4 12"/></svg>',
    money:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    users:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    alert:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    phone:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    spark:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    upload:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="24" height="24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    camera:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>',
    docs:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    export:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    eye:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>',
    edit:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    chat:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    mic:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>',
    globe:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
    info:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    grid:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    list:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>',
    plus:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
    bar:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M18 20V10M12 20V4M6 20v-6"/></svg>',
    arrow:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>'
  };
  return icons[name]||"";
}

/* ── API check + badges ── */
function checkApi(){
  GET("/health").then(function(){
    S.apiOnline=true;
    var s=$("#apiStatus");if(s){s.className="status-chip ok";s.innerHTML='<span class="dot"></span>API Online';}
    GET(API+"/vehicles?limit=200&active_only=false").then(function(d){if(d&&d.length)S.vehicles=d;}).catch(function(){});
    GET(API+"/customers?limit=200").then(function(d){if(d&&d.length)S.customers=d;}).catch(function(){});
    updateApprovalBadge();
  }).catch(function(){
    S.apiOnline=false;
    var s=$("#apiStatus");if(s){s.className="status-chip err";s.innerHTML='<span class="dot"></span>Offline';}
  });
}

function updateApprovalBadge(){
  GET(API+"/approval/pending?statuses=AI_DRAFT,EXTRACTED,NEEDS_REVIEW&limit=100").then(function(d){
    var nb=$("#nb-approval");if(nb)nb.textContent=(d&&d.length)||"";
  }).catch(function(){});
}

/* ── Theme ── */
function initTheme(){document.documentElement.dataset.theme=localStorage.getItem("km_theme")||"dark";}
function toggleTheme(){var t=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=t;localStorage.setItem("km_theme",t);Object.keys(CHARTS).forEach(function(k){destroyChart(k);});navigate(S.view);}

/* ── Boot ── */
function boot(){
  initTheme();
  $$(".nav-item[data-view]").forEach(function(n){n.addEventListener("click",function(e){e.preventDefault();navigate(n.dataset.view);});});
  $$("[data-goto]").forEach(function(b){b.addEventListener("click",function(){navigate(b.dataset.goto);});});
  var mt=$("#menuToggle"),sb=$("#sidebar"),ov=$("#sidebarOverlay"),sc=$("#sidebarClose");
  if(mt)mt.addEventListener("click",function(){sb.classList.add("open");ov.classList.add("show");});
  if(sc)sc.addEventListener("click",function(){sb.classList.remove("open");ov.classList.remove("show");});
  if(ov)ov.addEventListener("click",function(){sb.classList.remove("open");ov.classList.remove("show");});
  var tt=$("#themeToggle");if(tt)tt.addEventListener("click",toggleTheme);
  var mc=$("#modalClose"),mb=$("#modalBackdrop");
  if(mc)mc.addEventListener("click",closeModal);
  if(mb)mb.addEventListener("click",function(e){if(e.target===mb)closeModal();});
  document.addEventListener("keydown",function(e){if(e.key==="Escape")closeModal();});
  var rb=$("#refreshBtn");
  if(rb)rb.addEventListener("click",function(){
    rb.classList.add("spinning");
    S.vehicles=[];S.customers=[];
    checkApi();
    setTimeout(function(){rb.classList.remove("spinning");navigate(S.view);toast("Refreshed","success");},1200);
  });
  var gs=$("#globalSearch");
  if(gs)gs.addEventListener("keydown",function(e){if(e.key==="Enter"&&gs.value.trim()){S.q=gs.value.trim();S.filter="all";navigate("inventory");gs.value="";}});
  checkApi();
  navigate("dashboard");
}

if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",boot);}else{boot();}
})();
