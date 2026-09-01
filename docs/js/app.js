/* KM Car Deals — Dashboard v2  |  No mock data */
(function(){"use strict";
var API="/api/v1";
var CHARTS={};

/* ── Empty defaults (no fake data) ── */
var EMPTY_ANALYTICS={total_vehicles:0,active_for_sale:0,sold:0,total_customers:0,open_handoffs:0,revenue_mtd:0,avg_days_to_sell:0,status_breakdown:{}};

/* ── State ── */
var S={view:"dashboard",filter:"all",q:"",mode:"grid",apiOnline:false,vehicles:[],customers:[],_st:null};
var intakeFiles=[];

/* ── Helpers ── */
function $(s,c){return(c||document).querySelector(s);}
function $$(s,c){return Array.from((c||document).querySelectorAll(s));}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function money(v){if(!v||v==0)return"₹0";var n=Number(v);if(isNaN(n))return v;if(n>=10000000)return"₹"+(n/10000000).toFixed(2)+"Cr";if(n>=100000)return"₹"+(n/100000).toFixed(2)+"L";return"₹"+n.toLocaleString("en-IN");}
function km(v){if(v==null)return"—";var n=Number(v);return n>=1000?(n/1000).toFixed(1)+"k km":n.toLocaleString("en-IN")+" km";}
function num(v){return Number(v||0).toLocaleString("en-IN");}
function ini(name){return(name||"?").split(" ").map(function(w){return w[0]||"";}).slice(0,2).join("").toUpperCase()||"?";}
function bdg(s,lbl){if(!s)return"";return'<span class="badge badge-'+String(s).replace(/[^A-Z0-9_]/g,"_")+'">'+(lbl||String(s).replace(/_/g," "))+"</span>";}
function setContent(h){var c=$("#content");if(c)c.innerHTML=h;}
function destroyChart(k){if(CHARTS[k]){try{CHARTS[k].destroy();}catch(e){}delete CHARTS[k];}}
function gc(){var dk=document.documentElement.dataset.theme==="dark";return{grid:dk?"rgba(255,255,255,.06)":"rgba(0,0,0,.06)",text:dk?"#5d6d84":"#94a3b8",tip:{backgroundColor:"#1a2540",titleColor:"#e8edf5",bodyColor:"#a8b4c8",borderColor:"rgba(255,255,255,.1)",borderWidth:1,padding:12,cornerRadius:10}};}

/* ── HTTP ── */
function http(m,u,b){
  var o={method:m,headers:{}};
  if(b instanceof FormData){o.body=b;}
  else if(b!==undefined){o.headers["Content-Type"]="application/json";o.body=JSON.stringify(b);}
  return fetch(u,o).then(function(r){return r.json().catch(function(){return null;}).then(function(d){if(!r.ok)throw new Error((d&&(d.detail||d.message))||"Error "+r.status);return d;});});
}
var GET=function(u){return http("GET",u);};
var POST=function(u,b){return http("POST",u,b);};

/* ── Toast ── */
function toast(msg,type,title){
  type=type||"info";
  var icons={success:"✅",error:"❌",warning:"⚠️",info:"ℹ️"};
  var titles={success:"Success",error:"Error",warning:"Warning",info:"Info"};
  var stack=$("#toastStack");if(!stack)return;
  var el=document.createElement("div");
  el.className="toast "+type;
  el.innerHTML='<span class="toast-icon">'+icons[type]+'</span><div class="toast-content"><div class="toast-title">'+esc(title||titles[type])+'</div><div class="toast-msg">'+esc(msg)+'</div></div><button class="toast-dismiss" aria-label="Dismiss">✕</button>';
  el.querySelector(".toast-dismiss").onclick=function(){rm(el);};
  stack.appendChild(el);
  setTimeout(function(){rm(el);},4500);
}
function rm(el){if(!el.parentNode)return;el.classList.add("removing");setTimeout(function(){el.parentNode&&el.remove();},220);}

/* ── Modal ── */
function openModal(title,body){$("#modalTitle").textContent=title;$("#modalBody").innerHTML=body;$("#modalBackdrop").hidden=false;}
function closeModal(){$("#modalBackdrop").hidden=true;$("#modalBody").innerHTML="";}

/* ── Navigate ── */
var LABELS={dashboard:"Dashboard",inventory:"Inventory",intake:"AI Intake",customers:"Customers",leads:"Leads",analytics:"Analytics",docs:"API Docs"};
function navigate(v){
  S.view=v;
  $$(".nav-item").forEach(function(n){n.classList.toggle("active",n.dataset.view===v);});
  var pt=$("#pageTitle");if(pt)pt.textContent=LABELS[v]||v;
  ({dashboard:renderDashboard,inventory:renderInventory,intake:renderIntake,customers:renderCustomers,leads:renderLeads,analytics:renderAnalytics,docs:renderDocs})[v]&&
  ({dashboard:renderDashboard,inventory:renderInventory,intake:renderIntake,customers:renderCustomers,leads:renderLeads,analytics:renderAnalytics,docs:renderDocs})[v]();
  window.scrollTo({top:0,behavior:"smooth"});
  $("#sidebar").classList.remove("open");
  $("#sidebarOverlay").classList.remove("show");
}
window.navigate=navigate;

/* ── Empty state helper ── */
function emptyCard(icon,title,sub,btnLabel,btnAction){
  return '<div class="empty-state">'
    +'<div class="empty-icon" style="font-size:32px">'+icon+'</div>'
    +'<h3>'+esc(title)+'</h3>'
    +'<p>'+esc(sub)+'</p>'
    +(btnLabel?'<button class="btn btn-primary" onclick="'+btnAction+'">'+esc(btnLabel)+'</button>':'')
    +'</div>';
}

/* ── KPI card ── */
function kpiCard(label,val,sub,icon,color){
  return '<div class="kpi kpi-'+color+'">'
    +'<div class="kpi-icon '+color+'">'+icon+'</div>'
    +'<div class="kpi-label">'+esc(label)+'</div>'
    +'<div class="kpi-value">'+esc(val)+'</div>'
    +'<div class="kpi-sub">'+esc(sub)+'</div>'
    +'</div>';
}

/* ══ DASHBOARD ══ */
function renderDashboard(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading dashboard…</span></div>');
  GET(API+"/ops/analytics").then(function(a){
    paintDashboard(a);
  }).catch(function(){
    paintDashboard(EMPTY_ANALYTICS);
  });
}

function paintDashboard(a){
  var sb=a.status_breakdown||{};
  var total=a.total_vehicles||0;
  var noData=total===0;

  var kpis=[
    kpiCard("Total Inventory", num(a.total_vehicles), "All vehicles",   "🚗","orange"),
    kpiCard("For Sale",        num(a.active_for_sale),"Active listings","✅","green"),
    kpiCard("Sold",            num(a.sold),           "All time",       "💰","blue"),
    kpiCard("Customers",       num(a.total_customers),"In CRM",         "👥","purple"),
    kpiCard("Revenue MTD",     money(a.revenue_mtd),  "This month",     "📈","orange"),
    kpiCard("Open Handoffs",   num(a.open_handoffs),  "Needs attention","⚠️","red")
  ];

  /* Status bar rows */
  var statItems=[
    {label:"Available",   val:sb.AVAILABLE||0,    color:"#22c55e"},
    {label:"Reserved",    val:sb.RESERVED||0,     color:"#f59e0b"},
    {label:"Negotiation", val:sb.NEGOTIATION||0,  color:"#3b82f6"},
    {label:"Sold",        val:sb.SOLD||0,         color:"#f97316"},
    {label:"Review",      val:sb.PENDING_REVIEW||0,color:"#a855f7"}
  ];
  var qsHtml=statItems.map(function(i){
    var p=total>0?Math.round(i.val/total*100):0;
    return '<div class="qs-item"><div><div class="qs-label"><span class="qs-dot" style="background:'+i.color+'"></span>'+esc(i.label)+'</div>'
      +'<div class="qs-bar-wrap mt-8"><div class="qs-bar" style="width:'+p+'%;background:'+i.color+'"></div></div>'
      +'</div><div class="qs-val">'+i.val+'</div></div>';
  }).join("");

  /* Activity — empty if no API */
  var actHtml = S.apiOnline
    ? '<div class="empty-state" style="padding:32px"><p>No recent activity yet.</p></div>'
    : '<div class="empty-state" style="padding:32px"><p>Connect to the backend to see live activity.</p></div>';

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Dashboard</h1>'
    +'<p>'+(S.apiOnline?'Connected to backend — live data.':'Backend offline — connect PostgreSQL to see real data.')+'</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" onclick="navigate(\'analytics\')">📊 Full Report</button></div></div>'
    +'<div class="kpi-grid">'+kpis.join("")+'</div>'
    +'<div class="charts-row mb-24">'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Revenue & Sales Trend</span></div>'
      +'<div style="padding:16px 22px 22px">'+(noData
        ?emptyCard("📈","No sales data yet","Add vehicles and close deals to see your revenue trend.","","")
        :'<div class="chart-box"><canvas id="revenueChart"></canvas></div>')
      +'</div></div>'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock by Status</span></div>'
      +'<div style="padding:16px 22px 22px">'+(noData
        ?emptyCard("🚗","No vehicles yet","Add your first vehicle to see stock breakdown.","Add Vehicle","navigate('intake')")
        :'<div class="chart-box"><canvas id="statusChart"></canvas></div>')
      +'</div></div>'
    +'</div>'
    +'<div class="bottom-row">'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Recent Activity</span>'
      +(S.apiOnline?'<button class="btn btn-ghost btn-sm" onclick="navigate(\'inventory\')">View all →</button>':'')+'</div>'
      +'<div class="activity-list">'+actHtml+'</div></div>'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock Health</span></div>'
      +'<div class="quick-stats">'+qsHtml+'</div>'
      +'<div style="padding:18px 22px 22px">'+(noData
        ?emptyCard("🏷️","No stock data","Vehicles you add will appear here grouped by brand.","","")
        :'<div id="brandBars"></div>')
      +'</div></div>'
    +'</div>'
  );

  if(!noData){
    buildRevenueChart(a);
    buildStatusChart(sb);
    buildBrandBars();
  }
}

function buildRevenueChart(a){
  var c=$("#revenueChart");if(!c)return;destroyChart("revenue");
  /* Real chart — data comes from API; show empty months if no history */
  var months=["Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"];
  var d=gc();
  CHARTS.revenue=new Chart(c,{
    type:"line",
    data:{labels:months,datasets:[
      {label:"Revenue (₹L)",data:Array(12).fill(0),borderColor:"#f97316",backgroundColor:"rgba(249,115,22,.12)",borderWidth:2.5,tension:.4,fill:true,pointBackgroundColor:"#f97316",pointRadius:4,pointHoverRadius:6},
      {label:"Units Sold",data:Array(12).fill(0),borderColor:"#3b82f6",backgroundColor:"rgba(59,130,246,.08)",borderWidth:2,tension:.4,fill:true,pointBackgroundColor:"#3b82f6",pointRadius:3,pointHoverRadius:5,yAxisID:"y1"}
    ]},
    options:{maintainAspectRatio:false,interaction:{mode:"index",intersect:false},
      plugins:{legend:{position:"top",align:"end",labels:{boxWidth:10,boxHeight:10,padding:14,color:d.text,font:{size:12}}},tooltip:d.tip},
      scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},
        y:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11},callback:function(v){return"₹"+v+"L";}},position:"left"},
        y1:{grid:{drawOnChartArea:false},ticks:{color:d.text,font:{size:11}},position:"right"}}}
  });
}

function buildStatusChart(sb){
  var c=$("#statusChart");if(!c)return;destroyChart("status");
  var palette={AVAILABLE:"#22c55e",RESERVED:"#f59e0b",NEGOTIATION:"#3b82f6",SOLD:"#f97316",PENDING_REVIEW:"#a855f7",ARCHIVED:"#64748b"};
  var labels=[],vals=[],cols=[];
  Object.keys(sb).forEach(function(k){if(sb[k]>0){labels.push(k.replace(/_/g," "));vals.push(sb[k]);cols.push(palette[k]||"#64748b");}});
  if(!vals.length){labels=["No data"];vals=[1];cols=["#334155"];}
  var d=gc();var dk=document.documentElement.dataset.theme==="dark";
  CHARTS.status=new Chart(c,{
    type:"doughnut",
    data:{labels:labels,datasets:[{data:vals,backgroundColor:cols,borderWidth:2,borderColor:dk?"#131d2e":"#fff",hoverOffset:8}]},
    options:{maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{padding:12,boxWidth:10,boxHeight:10,color:d.text,font:{size:11.5}}},tooltip:d.tip}}
  });
}

function buildBrandBars(){
  var el=$("#brandBars");if(!el)return;
  var brands={};
  (S.vehicles||[]).forEach(function(v){var b=v.manufacturer||"Other";brands[b]=(brands[b]||0)+1;});
  var keys=Object.keys(brands).sort(function(a,b){return brands[b]-brands[a];}).slice(0,5);
  if(!keys.length){el.innerHTML='<div class="text-muted" style="font-size:13px">No vehicles in stock yet.</div>';return;}
  var max=brands[keys[0]]||1;
  var cols=["#f97316","#3b82f6","#22c55e","#a855f7","#f59e0b"];
  el.innerHTML=keys.map(function(b,i){
    var p=Math.round(brands[b]/max*100);
    return '<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:12.5px;font-weight:600;margin-bottom:5px"><span>'+esc(b)+'</span><span class="text-muted">'+brands[b]+'</span></div>'
      +'<div class="progress-wrap"><div class="progress-bar" style="width:'+p+'%;background:'+cols[i%5]+'"></div></div></div>';
  }).join("");
}

/* ══ INVENTORY ══ */
function renderInventory(){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Inventory</h1><p>All vehicles in stock.</p></div>'
    +'<div class="page-header-actions">'
    +'<button class="btn btn-ghost btn-sm" id="exportBtn">⬇ Export</button>'
    +'<button class="btn btn-primary btn-sm" onclick="navigate(\'intake\')">＋ Add Vehicle</button>'
    +'</div></div>'
    +'<div class="toolbar">'
      +'<div class="toolbar-left">'
        +'<div class="search-box"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>'
        +'<input type="text" id="invQ" placeholder="Search make, model, stock ID…" value="'+esc(S.q)+'"></div>'
        +'<div class="filter-pills" id="pills">'
        +pill("all","All")+pill("AVAILABLE","Available")+pill("RESERVED","Reserved")+pill("NEGOTIATION","Negotiation")+pill("PENDING_REVIEW","Review")+pill("SOLD","Sold")
        +'</div>'
      +'</div>'
      +'<div class="toolbar-right"><div class="view-toggle">'
        +'<button class="view-btn'+(S.mode==="grid"?" active":"")+ '" id="vgrid" title="Grid">⊞</button>'
        +'<button class="view-btn'+(S.mode==="list"?" active":"")+ '" id="vlist" title="List">☰</button>'
      +'</div></div>'
    +'</div>'
    +'<div id="invBody"></div>'
  );
  $$(".filter-pill").forEach(function(b){b.addEventListener("click",function(){S.filter=b.dataset.f;$$(".filter-pill").forEach(function(p){p.classList.toggle("active",p.dataset.f===S.filter);});loadInv();});});
  var qi=$("#invQ");if(qi)qi.addEventListener("input",function(){S.q=qi.value;clearTimeout(S._st);S._st=setTimeout(loadInv,200);});
  var vg=$("#vgrid"),vl=$("#vlist");
  if(vg)vg.addEventListener("click",function(){S.mode="grid";vg.classList.add("active");vl.classList.remove("active");loadInv();});
  if(vl)vl.addEventListener("click",function(){S.mode="list";vl.classList.add("active");vg.classList.remove("active");loadInv();});
  var eb=$("#exportBtn");
  if(eb)eb.addEventListener("click",function(){
    GET(API+"/ops/export").then(function(r){toast(r.message||"Export started","success");}).catch(function(){toast("Connect backend to export","warning");});
  });
  loadInv();
}

function pill(f,label){return'<button class="pill filter-pill'+(S.filter===f?" active":"")+ '" data-f="'+f+'">'+esc(label)+'</button>';}

function loadInv(){
  var body=$("#invBody");if(!body)return;
  body.innerHTML='<div class="skeleton-grid">'+Array(6).fill('<div class="skeleton-card"><div class="skeleton-photo"></div><div class="skeleton-body"><div class="skeleton-line medium"></div><div class="skeleton-line short"></div></div></div>').join("")+'</div>';
  var url=API+"/vehicles?limit=100"+(S.filter&&S.filter!=="all"?"&status="+S.filter:"")+(S.q?"&q="+encodeURIComponent(S.q):"");
  GET(url).then(function(cars){
    if(body.parentNode)paintInv(body,cars||[]);
  }).catch(function(){
    /* API offline — show empty state, not fake data */
    if(body.parentNode)paintInv(body,[]);
  });
}

function paintInv(body,cars){
  if(!cars.length){
    body.innerHTML=emptyCard("🚗","No vehicles found",
      S.filter!=="all"||S.q?"Try a different search or filter.":"Add your first vehicle using AI Intake.",
      S.filter==="all"&&!S.q?"Add Vehicle":null,"navigate('intake')");
    return;
  }
  body.innerHTML='<div class="inv-grid'+(S.mode==="list"?" list-view":"")+'">'+cars.map(carCard).join("")+'</div>';
}

function carCard(v){
  var photos=v.photos||[];
  var main=photos.slice().sort(function(a,b){return(b.is_primary?1:0)-(a.is_primary?1:0);})[0];
  var imgHtml=main?'<img src="'+esc(purl(main))+'" alt="'+esc(v.vehicle_name)+'" loading="lazy">'
    :'<div class="car-photo-placeholder"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity=".25"><path d="M5 17H3a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h2m14 0h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2"/><rect x="1" y="11" width="22" height="6" rx="1"/><path d="M5 11V8a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v3"/><circle cx="7.5" cy="17" r="1.5"/><circle cx="16.5" cy="17" r="1.5"/></svg></div>';
  var name=v.vehicle_name||((v.manufacturer||"")+" "+(v.model||"")).trim()||"Vehicle";
  return '<div class="car-card">'
    +'<div class="car-photo"><div class="photo-gradient"></div>'+imgHtml
    +'<div class="badge-pos">'+bdg(v.status)+'</div>'
    +(photos.length>1?'<div class="photo-count">📷 '+photos.length+'</div>':'')
    +'</div>'
    +'<div class="car-body">'
      +'<div class="car-top"><div><div class="car-name">'+esc(name)+'</div><div class="car-id">'+esc(v.stock_id||"")+'</div></div><div class="car-price">'+esc(money(v.selling_price||v.price))+'</div></div>'
      +'<div class="car-specs">'+si("Year",v.manufacturing_year)+si("Fuel",v.fuel_type)+si("Trans.",v.transmission)+si("KM",km(v.mileage_km))+si("Owner",v.owner_count)+si("City",v.location)+'</div>'
      +'<div class="car-footer">'
        +'<button class="btn btn-ghost btn-sm flex-1" onclick="showVehicle(\''+esc(v.vehicle_id)+'\')">👁 Details</button>'
        +(v.status!=="SOLD"&&v.status!=="ARCHIVED"
          ?'<select class="input status-select" onchange="setStatus(\''+esc(v.vehicle_id)+'\',this.value)">'
            +'<option value="">Status…</option>'
            +["AVAILABLE","RESERVED","NEGOTIATION","SOLD"].map(function(s){return'<option'+(v.status===s?" selected":"")+'>'+(s.replace(/_/g," "))+'</option>';}).join("")
          +'</select>':'')
      +'</div>'
    +'</div>'
  +'</div>';
}

function si(k,v){return'<div class="spec-item"><div class="spec-key">'+esc(k)+'</div><div class="spec-val">'+esc(v==null?"—":v)+'</div></div>';}
function purl(p){var fp=p.file_path||p;return/^https?:/.test(fp)?fp:"/uploads/"+fp.replace(/^.*[\\/]data[\\/]uploads[\\/]/,"").replace(/\\/g,"/");}

window.showVehicle=function(id){
  GET(API+"/vehicles/"+id).then(function(v){modalV(v);}).catch(function(){
    var v=(S.vehicles||[]).find(function(x){return x.vehicle_id===id;});
    if(v)modalV(v);else toast("Vehicle not found","error");
  });
};

function modalV(v){
  var photos=(v.photos||[]);
  var ph=photos.length
    ?'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">'+photos.map(function(p){return'<img src="'+esc(purl(p))+'" style="width:140px;height:96px;object-fit:cover;border-radius:10px;cursor:pointer;border:1px solid var(--border)" onclick="window.open(this.src)" loading="lazy">';}).join("")+'</div>'
    :'<div style="height:90px;display:grid;place-items:center;background:var(--surface-2);border-radius:10px;margin-bottom:18px;color:var(--text-muted)">No photos attached</div>';
  var name=v.vehicle_name||((v.manufacturer||"")+" "+(v.model||"")).trim();
  var facts=(v.facts||[]).map(function(f){return'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px"><span class="text-2">'+esc(f.field)+'</span><span class="font-semibold">'+esc(f.value)+'</span></div>';}).join("")||'<div class="text-muted" style="font-size:13px;padding:10px 0">No extracted facts yet</div>';
  openModal(name,
    ph
    +'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px">'
      +'<div><div style="font-size:22px;font-weight:900;color:var(--brand-primary)">'+esc(money(v.selling_price||v.price))+'</div><div style="font-weight:700;margin-top:4px">'+esc(name)+'</div></div>'
      +'<div>'+bdg(v.status)+'<span class="badge badge-outline" style="margin-left:6px">'+esc(v.stock_id||"")+'</span></div>'
    +'</div>'
    +'<div class="car-specs" style="margin-bottom:16px">'+si("Year",v.manufacturing_year)+si("Fuel",v.fuel_type)+si("Trans.",v.transmission)+si("KM",km(v.mileage_km))+si("Owner",v.owner_count)+si("Color",v.color)+si("Location",v.location)+'</div>'
    +'<div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px">Extracted Facts</div>'+facts
  );
}

window.setStatus=function(id,status){
  if(!status)return;
  POST(API+"/vehicles/"+id+"/status",{status:status,reason:"admin-ui"})
    .then(function(){toast("Status → "+status.replace(/_/g," "),"success");loadInv();})
    .catch(function(){toast("Connect backend to update status","warning");});
};

/* ══ INTAKE ══ */
function renderIntake(){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>AI Vehicle Intake</h1><p>Drop photos or an RC image — AI extracts all details automatically.</p></div></div>'
    +'<div class="grid-2" style="align-items:start">'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad">'
          +'<div class="form-section-title" style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)">📷 Photos & Documents</div>'
          +'<div class="dropzone" id="dz"><div class="dropzone-icon">⬆</div><h3>Drag & drop files here</h3><p>or <strong>browse</strong> to choose</p><p style="margin-top:6px;font-size:12px">RC, insurance, PUC, car photos · Max 15 files</p></div>'
          +'<input type="file" id="fileInput" multiple accept="image/*,.pdf" hidden>'
          +'<div class="file-list" id="fileList"></div>'
        +'</div>'
        +'<div class="card card-pad">'
          +'<div class="form-section-title" style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)">ℹ️ Seller Details <span style="font-weight:400;text-transform:none;letter-spacing:0">(optional)</span></div>'
          +'<div class="form-grid">'
            +'<div class="field"><label>Seller WhatsApp</label><input class="input" id="fWhat" placeholder="91XXXXXXXXXX"></div>'
            +'<div class="field"><label>Vehicle Hint</label><input class="input" id="fName" placeholder="e.g. Hyundai Creta SX 2022"></div>'
          +'</div>'
        +'</div>'
      +'</div>'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad">'
          +'<div class="form-section-title" style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)">⚡ AI Options</div>'
          +'<div style="display:flex;flex-direction:column;gap:16px">'
            +'<div class="field"><label>Enhance Photos</label><select class="input" id="fProc"><option value="true">Yes — generate web/social/thumbnail variants</option><option value="false">No — store originals only</option></select></div>'
            +'<div class="field"><label>Background Style</label><select class="input" id="fBg"><option value="premium_showroom">Premium Showroom</option><option value="dealership">Professional Dealership</option><option value="km_branded">KM Branded</option><option value="neutral_studio">Neutral Studio</option><option value="outdoor">Outdoor</option></select></div>'
          +'</div>'
        +'</div>'
        +'<div class="card card-pad" style="font-size:13px;color:var(--text-2)">'
          +'<div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px">What the AI does</div>'
          +['Reads RC to extract chassis, engine, registration numbers','Identifies make / model / variant from photos','Detects duplicates and blurry shots','Generates showroom-quality image variants (originals untouched)','Creates stock entry with all extracted facts in the database'].map(function(t,i){return'<div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:10px"><div style="width:20px;height:20px;border-radius:50%;background:var(--brand-gradient);color:#fff;display:grid;place-items:center;font-size:10px;font-weight:800;flex-shrink:0">'+(i+1)+'</div><span>'+esc(t)+'</span></div>';}).join("")
        +'</div>'
        +'<div class="info-block" style="background:var(--info-bg);border:1px solid rgba(59,130,246,.2);border-radius:var(--radius);padding:14px 16px;font-size:13px;color:var(--text-2);margin-bottom:0">ℹ️ Add your OpenAI API key in <code>.env</code> to enable live AI extraction.</div>'
        +'<button class="btn btn-primary btn-lg w-full" id="intakeBtn" style="justify-content:center;margin-top:16px">⚡ Run AI Intake</button>'
        +'<div id="progWrap" style="display:none;margin-top:16px">'
          +'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px"><span id="progLabel">Processing…</span><span id="progPct">0%</span></div>'
          +'<div class="progress-wrap"><div class="progress-bar" id="progBar" style="width:0%"></div></div>'
        +'</div>'
      +'</div>'
    +'</div>'
  );
  intakeFiles=[];
  var dz=$("#dz"),fi=$("#fileInput");
  if(dz&&fi){
    dz.addEventListener("click",function(e){if(e.target!==fi)fi.click();});
    dz.addEventListener("dragover",function(e){e.preventDefault();dz.classList.add("drag");});
    dz.addEventListener("dragleave",function(){dz.classList.remove("drag");});
    dz.addEventListener("drop",function(e){e.preventDefault();dz.classList.remove("drag");addFiles(e.dataTransfer.files);});
    fi.addEventListener("change",function(){addFiles(fi.files);fi.value="";});
  }
  var btn=$("#intakeBtn");if(btn)btn.addEventListener("click",runIntake);
}

function addFiles(list){
  Array.from(list).forEach(function(f){
    if(intakeFiles.length>=15){toast("Max 15 files","warning");return;}
    intakeFiles.push(f);
    var li=document.createElement("div");li.className="file-item";
    li.innerHTML='<div class="file-item-icon">'+(f.type.startsWith("image")?"🖼":"📄")+'</div>'
      +'<div class="file-item-name">'+esc(f.name)+'</div>'
      +'<div class="file-item-size">'+(f.size/1024).toFixed(1)+' KB</div>'
      +'<button class="file-item-rm" aria-label="Remove">✕</button>';
    li.querySelector(".file-item-rm").onclick=function(){var i=intakeFiles.indexOf(f);if(i>-1)intakeFiles.splice(i,1);li.remove();};
    var fl=$("#fileList");if(fl)fl.appendChild(li);
  });
}

function runIntake(){
  var btn=$("#intakeBtn"),pw=$("#progWrap");
  if(!btn)return;
  if(!intakeFiles.length&&!($("#fName")||{value:""}).value){toast("Add files or a vehicle name first","warning");return;}
  btn.disabled=true;btn.innerHTML="⚡ Processing…";
  if(pw)pw.style.display="block";
  var pct=0,si=0,steps=["Uploading files…","Reading RC document…","Analysing photos…","Generating variants…","Saving to database…"];
  var timer=setInterval(function(){
    pct=Math.min(pct+Math.random()*18,92);
    var bar=$("#progBar"),lbl=$("#progLabel"),pp=$("#progPct");
    if(bar)bar.style.width=pct.toFixed(0)+"%";
    if(pp)pp.textContent=pct.toFixed(0)+"%";
    if(lbl&&si<steps.length)lbl.textContent=steps[si++];
  },600);
  var fd=new FormData();
  intakeFiles.forEach(function(f){fd.append("files",f,f.name);});
  fd.append("message",($("#fName")||{value:""}).value);
  fd.append("seller_whatsapp",($("#fWhat")||{value:""}).value);
  fd.append("process_images",($("#fProc")||{value:"true"}).value);
  fd.append("background",($("#fBg")||{value:"premium_showroom"}).value);
  POST(API+"/intake/vehicle",fd)
    .then(function(r){clearInterval(timer);doneIntake(true,r.message||"Intake complete");})
    .catch(function(e){clearInterval(timer);doneIntake(false,e.message||"Intake failed — is the backend running?");});
}

function doneIntake(ok,msg){
  var bar=$("#progBar");if(bar)bar.style.width="100%";
  var pp=$("#progPct");if(pp)pp.textContent="100%";
  setTimeout(function(){
    var btn=$("#intakeBtn"),pw=$("#progWrap");
    if(btn){btn.disabled=false;btn.innerHTML="⚡ Run AI Intake";}
    if(pw)pw.style.display="none";
    toast(msg,ok?"success":"error",ok?"Done":"Error");
    if(ok){intakeFiles=[];var fl=$("#fileList");if(fl)fl.innerHTML="";}
  },500);
}

/* ══ CUSTOMERS ══ */
function renderCustomers(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading customers…</span></div>');
  GET(API+"/customers").then(function(rows){
    paintCustomers(rows||[]);
  }).catch(function(){
    paintCustomers([]);
  });
}

function paintCustomers(rows){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Customers</h1><p>'+rows.length+' contact'+(rows.length!==1?'s':'')+' in CRM.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" id="csvBtn">⬇ Export CSV</button></div></div>'
    +'<div class="card">'
      +'<div class="card-header"><span class="card-title"><span class="card-title-dot"></span>All Customers</span>'
        +'<div class="card-actions"><div class="search-box" style="max-width:220px"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input type="text" id="custQ" placeholder="Search…"></div></div>'
      +'</div>'
      +(rows.length
        ?'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>WhatsApp</th><th>City</th><th>Lead Status</th><th>Preferred Vehicle</th><th>Consent</th><th>Since</th></tr></thead>'
          +'<tbody id="custBody">'+custRows(rows)+'</tbody></table></div>'
        :'<div style="padding:0">'+emptyCard("👥","No customers yet","Customers will appear here once they interact via WhatsApp or are added manually.","","")+'</div>'
      )
    +'</div>'
  );
  var qi=$("#custQ");
  if(qi&&rows.length)qi.addEventListener("input",function(){
    var q=qi.value.toLowerCase();
    var f=rows.filter(function(c){return(c.name||"").toLowerCase().includes(q)||(c.city||"").toLowerCase().includes(q)||(c.whatsapp_number||"").includes(q);});
    var tb=$("#custBody");if(tb)tb.innerHTML=custRows(f);
  });
  var cb=$("#csvBtn");
  if(cb)cb.addEventListener("click",function(){toast("Connect backend to export CSV","info");});
}

function custRows(rows){
  if(!rows.length)return'<tr><td colspan="7">'+emptyCard("🔍","No results","Try a different search term.","","")+'</td></tr>';
  return rows.map(function(c){
    return'<tr>'
      +'<td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></td>'
      +'<td class="font-mono" style="font-size:12.5px">'+esc(c.whatsapp_number||"—")+'</td>'
      +'<td>'+esc(c.city||"—")+'</td>'
      +'<td>'+bdg(c.lead_status)+'</td>'
      +'<td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td>'
      +'<td>'+(c.opt_out?'<span class="badge badge-CLOSED_LOST">Opted Out</span>':'<span class="badge badge-AVAILABLE">Opted In</span>')+'</td>'
      +'<td class="text-muted" style="font-size:12.5px">'+esc(c.created_at||"—")+'</td>'
    +'</tr>';
  }).join("");
}

/* ══ LEADS ══ */
function renderLeads(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading leads…</span></div>');
  GET(API+"/customers").then(function(rows){
    paintLeads(rows||[]);
  }).catch(function(){
    paintLeads([]);
  });
}

function paintLeads(rows){
  var pipe=[
    {stage:"New Inquiries", count:0,color:"#3b82f6"},
    {stage:"Contacted",     count:0,color:"#a855f7"},
    {stage:"Qualified",     count:0,color:"#f59e0b"},
    {stage:"Negotiation",   count:0,color:"#f97316"},
    {stage:"Won",           count:0,color:"#22c55e"}
  ];
  /* Count from real data */
  rows.forEach(function(c){
    if(c.lead_status==="INTERESTED")        pipe[0].count++;
    else if(c.lead_status==="QUALIFIED")    pipe[2].count++;
    else if(c.lead_status==="NEGOTIATION")  pipe[3].count++;
    else if(c.lead_status==="CLOSED_WON")   pipe[4].count++;
    else                                     pipe[1].count++;
  });
  var max=Math.max.apply(null,pipe.map(function(p){return p.count;}))||1;
  var activeLeads=rows.filter(function(c){return c.lead_status!=="CLOSED_LOST";});

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Leads Pipeline</h1><p>Track every lead from first contact to closed deal.</p></div></div>'
    +'<div class="grid-2 mb-24">'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Sales Funnel</div>'
      +(rows.length
        ?'<div style="display:flex;flex-direction:column;gap:14px">'+pipe.map(function(p){var pct=Math.round(p.count/max*100);return'<div><div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px"><span>'+esc(p.stage)+'</span><span class="text-muted">'+p.count+'</span></div><div class="progress-wrap"><div class="progress-bar" style="width:'+pct+'%;background:'+p.color+'"></div></div></div>';}).join("")+'</div>'
        :emptyCard("📊","No lead data yet","Leads will populate as customers interact with your WhatsApp agent.","","")
      )
      +'</div>'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Pipeline Chart</div>'
      +(rows.length?'<div class="chart-box"><canvas id="funnelChart"></canvas></div>':emptyCard("📈","No data","—","",""))
      +'</div>'
    +'</div>'
    +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Active Leads</span></div>'
    +(activeLeads.length
      ?'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>Interest</th><th>Stage</th><th>WhatsApp</th><th>Action</th></tr></thead><tbody>'
        +activeLeads.map(function(c){return'<tr><td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></td><td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td><td>'+bdg(c.lead_status)+'</td><td class="font-mono" style="font-size:12.5px">'+esc((c.whatsapp_number||"").replace("91",""))+'</td><td><button class="btn btn-ghost btn-sm">📞 Follow Up</button></td></tr>';}).join("")
        +'</tbody></table></div>'
      :'<div style="padding:0">'+emptyCard("📞","No active leads","Leads will appear here once customers start interacting.","","")+'</div>'
    )
    +'</div>'
  );

  if(rows.length){
    var fc=$("#funnelChart");if(!fc)return;destroyChart("funnel");
    var d=gc();
    CHARTS.funnel=new Chart(fc,{type:"bar",data:{labels:pipe.map(function(p){return p.stage;}),datasets:[{data:pipe.map(function(p){return p.count;}),backgroundColor:pipe.map(function(p){return p.color+"cc";}),borderColor:pipe.map(function(p){return p.color;}),borderWidth:1.5,borderRadius:8}]},options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:d.tip},scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},y:{grid:{display:false},ticks:{color:d.text,font:{size:12}}}}}});
  }
}

/* ══ ANALYTICS ══ */
function renderAnalytics(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Building report…</span></div>');
  GET(API+"/ops/analytics").then(function(a){
    paintAnalytics(a);
  }).catch(function(){
    paintAnalytics(EMPTY_ANALYTICS);
  });
}

function paintAnalytics(a){
  var noData=!a.total_vehicles;
  var locs={};(S.vehicles||[]).forEach(function(v){var l=v.location||"Other";locs[l]=(locs[l]||0)+1;});
  var lkeys=Object.keys(locs).sort(function(a,b){return locs[b]-locs[a];});
  var lcols=["#f97316","#3b82f6","#22c55e","#a855f7","#f59e0b","#ef4444"];
  var locHtml=lkeys.length
    ?lkeys.map(function(l,i){var p=Math.round(locs[l]/(locs[lkeys[0]]||1)*100);return'<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:5px"><span>'+esc(l)+'</span><span class="text-muted">'+locs[l]+'</span></div><div class="progress-wrap"><div class="progress-bar" style="width:'+p+'%;background:'+lcols[i%6]+'"></div></div></div>';}).join("")
    :'<div class="text-muted" style="font-size:13px">No location data yet.</div>';

  var kpis=[
    kpiCard("Total Vehicles",  num(a.total_vehicles),   "All stock",        "🚗","orange"),
    kpiCard("Active Listings", num(a.active_for_sale),  "Ready to sell",    "✅","green"),
    kpiCard("Sold",            num(a.sold),              "All time",         "💰","blue"),
    kpiCard("Avg Days to Sell",num(a.avg_days_to_sell||0),"Per vehicle",     "📅","purple"),
    kpiCard("Revenue MTD",     money(a.revenue_mtd||0), "This month",        "📈","orange"),
    kpiCard("Customers",       num(a.total_customers),  "In CRM",            "👥","green")
  ];

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Analytics</h1><p>Full performance overview.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" onclick="toast(\'Connect backend to export\',\'info\')">⬇ Export Report</button></div></div>'
    +'<div class="kpi-grid mb-24">'+kpis.join("")+'</div>'
    +'<div class="charts-row mb-24">'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Revenue Trend</span></div>'
      +'<div style="padding:16px 22px 22px">'+(noData?emptyCard("📈","No revenue data yet","Close your first sale to see trends.","",""):'<div class="chart-box"><canvas id="revenueChart"></canvas></div>')+'</div></div>'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Inventory by Status</span></div>'
      +'<div style="padding:16px 22px 22px">'+(noData?emptyCard("🚗","No vehicles yet","Add vehicles to see stock breakdown.","Add Vehicle","navigate('intake')"):'<div class="chart-box"><canvas id="statusChart"></canvas></div>')+'</div></div>'
    +'</div>'
    +'<div class="analytics-grid">'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Fuel Type Distribution</div>'
      +(noData?emptyCard("⛽","No data yet","","",""):'<div class="chart-box" style="height:200px"><canvas id="fuelChart"></canvas></div>')+'</div>'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Top Locations</div>'+locHtml+'</div>'
    +'</div>'
  );

  if(!noData){
    buildRevenueChart(a);
    buildStatusChart(a.status_breakdown||{});
    buildFuelChart();
  }
}

function buildFuelChart(){
  var fc=$("#fuelChart");if(!fc)return;destroyChart("fuel");
  var fuels={};(S.vehicles||[]).forEach(function(v){var f=v.fuel_type||"Other";fuels[f]=(fuels[f]||0)+1;});
  var fl=Object.keys(fuels);if(!fl.length)return;
  var d=gc();var dk=document.documentElement.dataset.theme==="dark";
  CHARTS.fuel=new Chart(fc,{type:"pie",data:{labels:fl,datasets:[{data:fl.map(function(l){return fuels[l];}),backgroundColor:["#3b82f6","#22c55e","#a855f7","#f59e0b","#f97316"].slice(0,fl.length),borderWidth:2,borderColor:dk?"#131d2e":"#fff"}]},options:{maintainAspectRatio:false,plugins:{legend:{position:"right",labels:{padding:12,boxWidth:10,boxHeight:10,color:d.text,font:{size:11.5}}},tooltip:d.tip}}});
}

/* ══ DOCS ══ */
function renderDocs(){
  var eps=[
    {m:"GET", p:"/api/v1/vehicles",               d:"List all vehicles"},
    {m:"POST",p:"/api/v1/vehicles",               d:"Create a vehicle"},
    {m:"GET", p:"/api/v1/vehicles/{id}",           d:"Get vehicle details"},
    {m:"POST",p:"/api/v1/vehicles/{id}/status",    d:"Update vehicle status"},
    {m:"POST",p:"/api/v1/intake/vehicle",          d:"AI intake — upload photos/RC"},
    {m:"GET", p:"/api/v1/customers",               d:"List all customers"},
    {m:"POST",p:"/api/v1/customers",               d:"Create / upsert customer"},
    {m:"GET", p:"/api/v1/ops/analytics",           d:"Dashboard analytics summary"},
    {m:"GET", p:"/api/v1/ops/export",              d:"Export inventory to Excel"},
    {m:"POST",p:"/webhook/whatsapp",               d:"WhatsApp webhook receiver"},
    {m:"GET", p:"/health",                         d:"Health check"}
  ];
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>API Documentation</h1><p>Explore every backend endpoint.</p></div></div>'
    +'<div class="docs-grid mb-24">'
      +'<a class="docs-card" href="/docs" target="_blank"><div class="docs-card-icon orange" style="font-size:22px">⚡</div><h3>Swagger UI</h3><p>Interactive API explorer — try every endpoint live in-browser.</p><div class="arrow">Open →</div></a>'
      +'<a class="docs-card" href="/redoc" target="_blank"><div class="docs-card-icon blue" style="font-size:22px">📖</div><h3>ReDoc</h3><p>Clean structured reference documentation for all routes.</p><div class="arrow">Open →</div></a>'
      +'<a class="docs-card" href="/openapi.json" target="_blank"><div class="docs-card-icon green" style="font-size:22px">{ }</div><h3>OpenAPI JSON</h3><p>Import into Postman or any HTTP client.</p><div class="arrow">Open →</div></a>'
    +'</div>'
    +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Available Endpoints</span></div>'
    +'<div style="padding:18px 22px"><div class="endpoint-list">'
    +eps.map(function(e){return'<div class="endpoint"><span class="method '+e.m+'">'+e.m+'</span><span class="endpoint-path">'+esc(e.p)+'</span><span class="endpoint-desc">'+esc(e.d)+'</span></div>';}).join("")
    +'</div></div></div>'
  );
}

/* ══ API CHECK ══ */
function checkApi(){
  GET("/health").then(function(){
    S.apiOnline=true;
    var s=$("#apiStatus");if(s){s.className="status-chip ok";s.innerHTML='<span class="dot"></span>API Online';}
    /* Load real vehicles and customers into state */
    GET(API+"/vehicles?limit=200").then(function(d){if(d&&d.length){S.vehicles=d;updateBadges();}}).catch(function(){});
    GET(API+"/customers?limit=200").then(function(d){if(d&&d.length)S.customers=d;}).catch(function(){});
  }).catch(function(){
    S.apiOnline=false;
    var s=$("#apiStatus");if(s){s.className="status-chip err";s.innerHTML='<span class="dot"></span>Offline';}
  });
}

function updateBadges(){
  var vs=S.vehicles||[];
  var av=vs.filter(function(v){return v.status==="AVAILABLE";}).length;
  var pr=vs.filter(function(v){return v.status==="PENDING_REVIEW";}).length;
  var nb=$("#nb-inventory");if(nb)nb.textContent=av||"";
  var nd=$("#nb-dashboard");if(nd)nd.textContent=pr||"";
  var nc=$("#nb-customers");if(nc)nc.textContent=(S.customers||[]).length||"";
}

/* ══ THEME ══ */
function initTheme(){document.documentElement.dataset.theme=localStorage.getItem("km_theme")||"dark";}
function toggleTheme(){
  var t=document.documentElement.dataset.theme==="dark"?"light":"dark";
  document.documentElement.dataset.theme=t;localStorage.setItem("km_theme",t);
  Object.keys(CHARTS).forEach(function(k){destroyChart(k);});
  navigate(S.view);
}

/* ══ BOOT ══ */
function boot(){
  initTheme();
  $$(".nav-item").forEach(function(n){n.addEventListener("click",function(e){e.preventDefault();navigate(n.dataset.view);});});
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
