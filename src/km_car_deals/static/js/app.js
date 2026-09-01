/* KM Car Deals — Dashboard v2 */
(function(){"use strict";
var API="/api/v1";
var CHARTS={};

/* ── Mock Data ── */
var M={
  analytics:{total_vehicles:47,active_for_sale:23,sold:18,total_customers:134,open_handoffs:6,revenue_mtd:28450000,avg_days_to_sell:11,status_breakdown:{AVAILABLE:23,RESERVED:7,NEGOTIATION:4,SOLD:18,PENDING_REVIEW:3,ARCHIVED:2}},
  vehicles:[
    {vehicle_id:"v-001",stock_id:"KM-2024-001",vehicle_name:"Hyundai Creta SX(O) Diesel",manufacturer:"Hyundai",model:"Creta",manufacturing_year:2022,fuel_type:"Diesel",transmission:"Automatic",mileage_km:28400,owner_count:1,location:"Pune",selling_price:1595000,status:"AVAILABLE",color:"Pearl White",photos:[]},
    {vehicle_id:"v-002",stock_id:"KM-2024-002",vehicle_name:"Maruti Swift ZXI+ AMT",manufacturer:"Maruti",model:"Swift",manufacturing_year:2023,fuel_type:"Petrol",transmission:"Automatic",mileage_km:9200,owner_count:1,location:"Mumbai",selling_price:795000,status:"RESERVED",color:"Midnight Blue",photos:[]},
    {vehicle_id:"v-003",stock_id:"KM-2024-003",vehicle_name:"Tata Nexon EV Max",manufacturer:"Tata",model:"Nexon EV",manufacturing_year:2023,fuel_type:"Electric",transmission:"Automatic",mileage_km:14600,owner_count:1,location:"Bangalore",selling_price:1895000,status:"NEGOTIATION",color:"Fearless Red",photos:[]},
    {vehicle_id:"v-004",stock_id:"KM-2024-004",vehicle_name:"Honda City 5th Gen ZX CVT",manufacturer:"Honda",model:"City",manufacturing_year:2021,fuel_type:"Petrol",transmission:"CVT",mileage_km:42000,owner_count:2,location:"Delhi",selling_price:1075000,status:"AVAILABLE",color:"Radiant Red",photos:[]},
    {vehicle_id:"v-005",stock_id:"KM-2024-005",vehicle_name:"Toyota Fortuner Legender 4x4",manufacturer:"Toyota",model:"Fortuner",manufacturing_year:2022,fuel_type:"Diesel",transmission:"Automatic",mileage_km:31000,owner_count:1,location:"Hyderabad",selling_price:3950000,status:"AVAILABLE",color:"White Pearl",photos:[]},
    {vehicle_id:"v-006",stock_id:"KM-2024-006",vehicle_name:"Kia Seltos HTX+ DCT",manufacturer:"Kia",model:"Seltos",manufacturing_year:2023,fuel_type:"Petrol",transmission:"DCT",mileage_km:6800,owner_count:1,location:"Pune",selling_price:1445000,status:"AVAILABLE",color:"Gravity Grey",photos:[]},
    {vehicle_id:"v-007",stock_id:"KM-2024-007",vehicle_name:"Mahindra Scorpio N Z8 L",manufacturer:"Mahindra",model:"Scorpio N",manufacturing_year:2023,fuel_type:"Diesel",transmission:"Automatic",mileage_km:12300,owner_count:1,location:"Pune",selling_price:2195000,status:"RESERVED",color:"Deep Forest",photos:[]},
    {vehicle_id:"v-008",stock_id:"KM-2024-008",vehicle_name:"Volkswagen Virtus GT Plus DSG",manufacturer:"Volkswagen",model:"Virtus",manufacturing_year:2022,fuel_type:"Petrol",transmission:"DSG",mileage_km:19800,owner_count:1,location:"Mumbai",selling_price:1625000,status:"SOLD",color:"Candy White",photos:[]},
    {vehicle_id:"v-009",stock_id:"KM-2024-009",vehicle_name:"MG Hector Plus Sharp Pro",manufacturer:"MG",model:"Hector Plus",manufacturing_year:2023,fuel_type:"Petrol Hybrid",transmission:"CVT",mileage_km:8100,owner_count:1,location:"Chennai",selling_price:2250000,status:"PENDING_REVIEW",color:"Burgundy Red",photos:[]},
    {vehicle_id:"v-010",stock_id:"KM-2024-010",vehicle_name:"Maruti Baleno Alpha CVT",manufacturer:"Maruti",model:"Baleno",manufacturing_year:2023,fuel_type:"Petrol",transmission:"CVT",mileage_km:5400,owner_count:1,location:"Pune",selling_price:925000,status:"AVAILABLE",color:"Grandeur Grey",photos:[]}
  ],
  customers:[
    {customer_id:"c-001",name:"Arjun Mehta",whatsapp_number:"919876543210",lead_status:"NEGOTIATION",preferred_vehicle:"Creta / Seltos",opt_out:false,city:"Pune",created_at:"2024-08-01"},
    {customer_id:"c-002",name:"Priya Sharma",whatsapp_number:"919812345678",lead_status:"INTERESTED",preferred_vehicle:"Nexon EV",opt_out:false,city:"Mumbai",created_at:"2024-08-05"},
    {customer_id:"c-003",name:"Rahul Singh",whatsapp_number:"919988776655",lead_status:"CLOSED_WON",preferred_vehicle:"Fortuner",opt_out:false,city:"Delhi",created_at:"2024-07-18"},
    {customer_id:"c-004",name:"Sneha Patil",whatsapp_number:"919765432109",lead_status:"INTERESTED",preferred_vehicle:"Swift / Baleno",opt_out:false,city:"Pune",created_at:"2024-08-10"},
    {customer_id:"c-005",name:"Vikram Reddy",whatsapp_number:"919654321098",lead_status:"QUALIFIED",preferred_vehicle:"Scorpio N",opt_out:false,city:"Hyderabad",created_at:"2024-08-03"},
    {customer_id:"c-006",name:"Anjali Iyer",whatsapp_number:"919543210987",lead_status:"CLOSED_LOST",preferred_vehicle:"City / Verna",opt_out:true,city:"Chennai",created_at:"2024-07-22"},
    {customer_id:"c-007",name:"Deepak Nair",whatsapp_number:"919432109876",lead_status:"INTERESTED",preferred_vehicle:"Virtus / Vento",opt_out:false,city:"Bangalore",created_at:"2024-08-14"},
    {customer_id:"c-008",name:"Meera Joshi",whatsapp_number:"919321098765",lead_status:"NEGOTIATION",preferred_vehicle:"Hector / Compass",opt_out:false,city:"Pune",created_at:"2024-08-08"}
  ],
  activity:[
    {icon:"✅",color:"green", title:"Volkswagen Virtus GT sold",          sub:"KM-2024-008 · ₹16.25L",          time:"2m ago"},
    {icon:"🚗",color:"orange",title:"MG Hector Plus added via AI intake", sub:"KM-2024-009 · Pending review",   time:"38m ago"},
    {icon:"📞",color:"blue",  title:"New lead: Deepak Nair",              sub:"Interested in Virtus / Vento",   time:"1h ago"},
    {icon:"🔒",color:"purple",title:"Scorpio N reserved",                 sub:"KM-2024-007 · Vikram Reddy",     time:"3h ago"},
    {icon:"💬",color:"green", title:"WhatsApp inquiry — Nexon EV",        sub:"91-981-234-5678 · Priya Sharma", time:"4h ago"},
    {icon:"⚠️",color:"red",  title:"Conflict detected on RC scan",        sub:"KM-2024-009 · Reg mismatch",     time:"5h ago"}
  ],
  revenue:[42,58,51,67,73,62,81,95,88,102,91,115],
  units:   [22,29,31,28,36,34,39,43,41,38,47,53]
};

/* ── State ── */
var S={view:"dashboard",filter:"all",q:"",mode:"grid",apiOnline:false,vehicles:null,customers:null,_st:null};
var intakeFiles=[];

/* ── Helpers ── */
function $(s,c){return(c||document).querySelector(s);}
function $$(s,c){return Array.from((c||document).querySelectorAll(s));}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function money(v){if(v==null)return"—";var n=Number(v);if(isNaN(n))return v;if(n>=10000000)return"₹"+(n/10000000).toFixed(2)+"Cr";if(n>=100000)return"₹"+(n/100000).toFixed(2)+"L";return"₹"+n.toLocaleString("en-IN");}
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
function openModal(title,body){
  $("#modalTitle").textContent=title;
  $("#modalBody").innerHTML=body;
  $("#modalBackdrop").hidden=false;
}
function closeModal(){$("#modalBackdrop").hidden=true;$("#modalBody").innerHTML="";}

/* ── Navigate ── */
var LABELS={dashboard:"Dashboard",inventory:"Inventory",intake:"AI Intake",customers:"Customers",leads:"Leads",analytics:"Analytics",docs:"API Docs"};
function navigate(v){
  S.view=v;
  $$(".nav-item").forEach(function(n){n.classList.toggle("active",n.dataset.view===v);});
  var pt=$("#pageTitle");if(pt)pt.textContent=LABELS[v]||v;
  ({dashboard:renderDashboard,inventory:renderInventory,intake:renderIntake,customers:renderCustomers,leads:renderLeads,analytics:renderAnalytics,docs:renderDocs})[v]&&({dashboard:renderDashboard,inventory:renderInventory,intake:renderIntake,customers:renderCustomers,leads:renderLeads,analytics:renderAnalytics,docs:renderDocs})[v]();
  window.scrollTo({top:0,behavior:"smooth"});
  $("#sidebar").classList.remove("open");
  $("#sidebarOverlay").classList.remove("show");
}
window.navigate=navigate;

/* ══ DASHBOARD ══ */
function renderDashboard(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading…</span></div>');
  var a=M.analytics;
  var sb=a.status_breakdown;
  var total=a.total_vehicles||1;

  var kpis=[
    {label:"Total Inventory",  val:num(a.total_vehicles), sub:"All vehicles",       icon:"🚗", color:"orange"},
    {label:"For Sale",         val:num(a.active_for_sale),sub:"Active listings",    icon:"✅", color:"green"},
    {label:"Sold",             val:num(a.sold),           sub:"All time",           icon:"💰", color:"blue"},
    {label:"Customers",        val:num(a.total_customers),sub:"In CRM",             icon:"👥", color:"purple"},
    {label:"Revenue MTD",      val:money(a.revenue_mtd),  sub:"This month",         icon:"📈", color:"orange"},
    {label:"Open Handoffs",    val:num(a.open_handoffs),  sub:"Needs attention",    icon:"⚠️", color:"red"}
  ];

  var kpiHtml=kpis.map(function(k){return(
    '<div class="kpi kpi-'+k.color+'">'
    +'<div class="kpi-icon '+k.color+'">'+k.icon+'</div>'
    +'<div class="kpi-label">'+esc(k.label)+'</div>'
    +'<div class="kpi-value">'+esc(k.val)+'</div>'
    +'<div class="kpi-sub">'+esc(k.sub)+'</div>'
    +'</div>'
  );}).join("");

  var actHtml=M.activity.map(function(a){return(
    '<div class="activity-item">'
    +'<div class="activity-icon '+a.color+'">'+a.icon+'</div>'
    +'<div class="activity-body"><div class="activity-title">'+esc(a.title)+'</div><div class="activity-sub">'+esc(a.sub)+'</div></div>'
    +'<div class="activity-time">'+esc(a.time)+'</div>'
    +'</div>'
  );}).join("");

  var statItems=[
    {label:"Available", val:sb.AVAILABLE||0, color:"#22c55e"},
    {label:"Reserved",  val:sb.RESERVED||0,  color:"#f59e0b"},
    {label:"Negotiation",val:sb.NEGOTIATION||0,color:"#3b82f6"},
    {label:"Sold",      val:sb.SOLD||0,      color:"#f97316"},
    {label:"Review",    val:sb.PENDING_REVIEW||0,color:"#a855f7"}
  ];
  var qsHtml=statItems.map(function(i){
    var p=Math.round(i.val/total*100);
    return '<div class="qs-item"><div><div class="qs-label"><span class="qs-dot" style="background:'+i.color+'"></span>'+esc(i.label)+'</div>'
      +'<div class="qs-bar-wrap mt-8"><div class="qs-bar" style="width:'+p+'%;background:'+i.color+'"></div></div>'
      +'</div><div class="qs-val">'+i.val+'</div></div>';
  }).join("");

  var brands={};
  (S.vehicles||M.vehicles).forEach(function(v){var b=v.manufacturer||"Other";brands[b]=(brands[b]||0)+1;});
  var bkeys=Object.keys(brands).sort(function(a,b){return brands[b]-brands[a];}).slice(0,5);
  var bmax=brands[bkeys[0]]||1;
  var bcols=["#f97316","#3b82f6","#22c55e","#a855f7","#f59e0b"];
  var brandHtml=bkeys.map(function(b,i){
    var p=Math.round(brands[b]/bmax*100);
    return '<div style="margin-bottom:12px"><div class="flex justify-between mb-8" style="font-size:12.5px;font-weight:600"><span>'+esc(b)+'</span><span class="text-muted">'+brands[b]+'</span></div>'
      +'<div class="progress-wrap"><div class="progress-bar" style="width:'+p+'%;background:'+bcols[i%5]+'"></div></div></div>';
  }).join("");

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Dashboard</h1><p>Welcome back, Admin.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" onclick="navigate(\'analytics\')">📊 Full Report</button></div></div>'
    +'<div class="kpi-grid">'+kpiHtml+'</div>'
    +'<div class="charts-row mb-24">'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Revenue & Sales Trend</span></div>'
      +'<div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="revenueChart"></canvas></div></div></div>'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock by Status</span></div>'
      +'<div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="statusChart"></canvas></div></div></div>'
    +'</div>'
    +'<div class="bottom-row">'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Recent Activity</span>'
      +'<button class="btn btn-ghost btn-sm" onclick="navigate(\'inventory\')">View all →</button></div>'
      +'<div class="activity-list">'+actHtml+'</div></div>'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock Health</span></div>'
      +'<div class="quick-stats">'+qsHtml+'</div>'
      +'<div style="padding:18px 22px 22px"><div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px">Top Brands</div>'+brandHtml+'</div>'
      +'</div>'
    +'</div>'
  );

  buildRevenueChart();
  buildStatusChart(a.status_breakdown);
}

function buildRevenueChart(){
  var c=$("#revenueChart");if(!c)return;destroyChart("revenue");
  var d=gc();
  CHARTS.revenue=new Chart(c,{
    type:"line",
    data:{labels:["Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug"],
      datasets:[
        {label:"Revenue (₹L)",data:M.revenue,borderColor:"#f97316",backgroundColor:"rgba(249,115,22,.12)",borderWidth:2.5,tension:.4,fill:true,pointBackgroundColor:"#f97316",pointRadius:4,pointHoverRadius:6},
        {label:"Units Sold",data:M.units,borderColor:"#3b82f6",backgroundColor:"rgba(59,130,246,.08)",borderWidth:2,tension:.4,fill:true,pointBackgroundColor:"#3b82f6",pointRadius:3,pointHoverRadius:5,yAxisID:"y1"}
      ]},
    options:{maintainAspectRatio:false,interaction:{mode:"index",intersect:false},
      plugins:{legend:{position:"top",align:"end",labels:{boxWidth:10,boxHeight:10,padding:14,color:d.text,font:{size:12}}},tooltip:d.tip},
      scales:{
        x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},
        y:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11},callback:function(v){return"₹"+v+"L";}},position:"left"},
        y1:{grid:{drawOnChartArea:false},ticks:{color:d.text,font:{size:11}},position:"right"}
      }}
  });
}

function buildStatusChart(sb){
  var c=$("#statusChart");if(!c)return;destroyChart("status");
  sb=sb||M.analytics.status_breakdown;
  var palette={AVAILABLE:"#22c55e",RESERVED:"#f59e0b",NEGOTIATION:"#3b82f6",SOLD:"#f97316",PENDING_REVIEW:"#a855f7",ARCHIVED:"#64748b"};
  var labels=[],vals=[],cols=[];
  Object.keys(sb).forEach(function(k){if(sb[k]>0){labels.push(k.replace(/_/g," "));vals.push(sb[k]);cols.push(palette[k]||"#64748b");}});
  var d=gc();var dk=document.documentElement.dataset.theme==="dark";
  CHARTS.status=new Chart(c,{
    type:"doughnut",
    data:{labels:labels,datasets:[{data:vals,backgroundColor:cols,borderWidth:2,borderColor:dk?"#131d2e":"#fff",hoverOffset:8}]},
    options:{maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{padding:12,boxWidth:10,boxHeight:10,color:d.text,font:{size:11.5}}},tooltip:d.tip}}
  });
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
  var eb=$("#exportBtn");if(eb)eb.addEventListener("click",function(){toast("Export queued","success");});
  loadInv();
}

function pill(f,label){return'<button class="pill filter-pill'+(S.filter===f?" active":"")+ '" data-f="'+f+'">'+esc(label)+'</button>';}

function loadInv(){
  var body=$("#invBody");if(!body)return;
  body.innerHTML='<div class="skeleton-grid">'+Array(6).fill('<div class="skeleton-card"><div class="skeleton-photo"></div><div class="skeleton-body"><div class="skeleton-line medium"></div><div class="skeleton-line short"></div></div></div>').join("")+'</div>';
  var cars=(S.vehicles||M.vehicles).filter(function(v){
    if(S.filter&&S.filter!=="all"&&v.status!==S.filter)return false;
    if(S.q){var q=S.q.toLowerCase();return(v.vehicle_name||"").toLowerCase().includes(q)||(v.manufacturer||"").toLowerCase().includes(q)||(v.stock_id||"").toLowerCase().includes(q);}
    return true;
  });
  GET(API+"/vehicles?limit=100&"+(S.filter&&S.filter!=="all"?"status="+S.filter:"")+
      (S.q?"&q="+encodeURIComponent(S.q):""))
    .then(function(d){if(body.parentNode)paintInv(body,d&&d.length?d:cars);})
    .catch(function(){if(body.parentNode)paintInv(body,cars);});
}

function paintInv(body,cars){
  if(!cars.length){body.innerHTML='<div class="empty-state"><div class="empty-icon">🚗</div><h3>No vehicles found</h3><p>Try a different filter.</p></div>';return;}
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
      +'<div class="car-specs">'
        +si("Year",v.manufacturing_year)+si("Fuel",v.fuel_type)+si("Trans.",v.transmission)
        +si("KM",km(v.mileage_km))+si("Owner",v.owner_count)+si("City",v.location)
      +'</div>'
      +'<div class="car-footer">'
        +'<button class="btn btn-ghost btn-sm flex-1" onclick="showVehicle(\''+esc(v.vehicle_id)+'\')">👁 Details</button>'
        +(v.status!=="SOLD"&&v.status!=="ARCHIVED"
          ?'<select class="input status-select" onchange="setStatus(\''+esc(v.vehicle_id)+'\',this.value)">'
            +'<option value="">Status…</option>'
            +["AVAILABLE","RESERVED","NEGOTIATION","SOLD"].map(function(s){return'<option'+(v.status===s?" selected":"")+'>'+(s.replace(/_/g," "))+'</option>';}).join("")
          +'</select>'
          :'')
      +'</div>'
    +'</div>'
  +'</div>';
}

function si(k,v){return'<div class="spec-item"><div class="spec-key">'+esc(k)+'</div><div class="spec-val">'+esc(v==null?"—":v)+'</div></div>';}
function purl(p){var fp=p.file_path||p;return/^https?:/.test(fp)?fp:"/uploads/"+fp.replace(/^.*[\\/]data[\\/]uploads[\\/]/,"").replace(/\\/g,"/");}

window.showVehicle=function(id){
  var v=(S.vehicles||M.vehicles).find(function(x){return x.vehicle_id===id;});
  if(!v){GET(API+"/vehicles/"+id).then(function(d){modalV(d);}).catch(function(){toast("Not found","error");});return;}
  modalV(v);
};

function modalV(v){
  var photos=(v.photos||[]);
  var ph=photos.length
    ?'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px">'+photos.map(function(p){return'<img src="'+esc(purl(p))+'" style="width:140px;height:96px;object-fit:cover;border-radius:10px;cursor:pointer;border:1px solid var(--border)" onclick="window.open(this.src)" loading="lazy">';}).join("")+'</div>'
    :'<div style="height:90px;display:grid;place-items:center;background:var(--surface-2);border-radius:10px;margin-bottom:18px;color:var(--text-muted)">No photos</div>';
  var name=v.vehicle_name||((v.manufacturer||"")+" "+(v.model||"")).trim();
  var facts=(v.facts||[]).map(function(f){return'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px"><span class="text-2">'+esc(f.field)+'</span><span class="font-semibold">'+esc(f.value)+'</span></div>';}).join("")||'<div class="text-muted" style="font-size:13px;padding:10px 0">No extracted facts</div>';
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
  POST(API+"/vehicles/"+id+"/status",{status:status,reason:"admin-ui"}).then(function(){toast("Status → "+status.replace(/_/g," "),"success");loadInv();}).catch(function(){var v=(S.vehicles||M.vehicles).find(function(x){return x.vehicle_id===id;});if(v)v.status=status;toast("Status → "+status.replace(/_/g," "),"success");loadInv();});
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
          +'<div class="form-section-title" style="display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid var(--border)">ℹ️ Seller Details (optional)</div>'
          +'<div class="form-grid">'
            +'<div class="field"><label>Seller WhatsApp</label><input class="input" id="fWhat" placeholder="91XXXXXXXXXX"></div>'
            +'<div class="field"><label>Vehicle Hint</label><input class="input" id="fName" placeholder="Hyundai Creta SX 2022"></div>'
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
          +'<div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px">What happens</div>'
          +['Reads RC to extract chassis, engine, reg numbers','Identifies make/model/variant from photos','Detects duplicates & blurry shots','Generates showroom-quality variants','Creates stock entry with all facts'].map(function(t,i){return'<div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:10px"><div style="width:20px;height:20px;border-radius:50%;background:var(--brand-gradient);color:#fff;display:grid;place-items:center;font-size:10px;font-weight:800;flex-shrink:0">'+(i+1)+'</div><span>'+esc(t)+'</span></div>';}).join("")
        +'</div>'
        +'<button class="btn btn-primary btn-lg w-full" id="intakeBtn" style="justify-content:center">⚡ Run AI Intake</button>'
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
  if(!intakeFiles.length&&!($("#fName")||{value:""}).value){toast("Add files or a vehicle name","warning");return;}
  btn.disabled=true;btn.innerHTML="⚡ Processing…";
  if(pw)pw.style.display="block";
  var pct=0,si=0,steps=["Uploading…","Reading RC…","Analysing photos…","Generating variants…","Saving to DB…"];
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
  POST(API+"/intake/vehicle",fd).then(function(r){clearInterval(timer);doneIntake(true,r.message||"Intake complete");}).catch(function(){clearInterval(timer);doneIntake(true,"Intake complete (demo mode)");});
}

function doneIntake(ok,msg){
  var bar=$("#progBar");if(bar)bar.style.width="100%";
  var pp=$("#progPct");if(pp)pp.textContent="100%";
  setTimeout(function(){
    var btn=$("#intakeBtn"),pw=$("#progWrap");
    if(btn){btn.disabled=false;btn.innerHTML="⚡ Run AI Intake";}
    if(pw)pw.style.display="none";
    toast(msg,ok?"success":"error",ok?"Done":"Error");
    intakeFiles=[];var fl=$("#fileList");if(fl)fl.innerHTML="";
  },500);
}

/* ══ CUSTOMERS ══ */
function renderCustomers(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading…</span></div>');
  var rows=S.customers||M.customers;
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Customers</h1><p>'+rows.length+' contacts in CRM.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm">⬇ Export CSV</button></div></div>'
    +'<div class="card">'
      +'<div class="card-header"><span class="card-title"><span class="card-title-dot"></span>All Customers</span>'
        +'<div class="card-actions"><div class="search-box" style="max-width:220px"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input type="text" id="custQ" placeholder="Search…"></div></div>'
      +'</div>'
      +'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>WhatsApp</th><th>City</th><th>Lead Status</th><th>Preferred</th><th>Consent</th><th>Since</th></tr></thead>'
      +'<tbody id="custBody">'+custRows(rows)+'</tbody></table></div>'
    +'</div>'
  );
  var qi=$("#custQ");
  if(qi)qi.addEventListener("input",function(){
    var q=qi.value.toLowerCase();
    var all=S.customers||M.customers;
    var f=all.filter(function(c){return(c.name||"").toLowerCase().includes(q)||(c.city||"").toLowerCase().includes(q);});
    var tb=$("#custBody");if(tb)tb.innerHTML=custRows(f);
  });
}

function custRows(rows){
  if(!rows.length)return'<tr><td colspan="7"><div class="empty-state" style="padding:40px"><h3>No customers found</h3></div></td></tr>';
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
  var pipe=[{stage:"New Inquiries",count:22,color:"#3b82f6"},{stage:"Contacted",count:17,color:"#a855f7"},{stage:"Qualified",count:11,color:"#f59e0b"},{stage:"Negotiation",count:6,color:"#f97316"},{stage:"Won",count:4,color:"#22c55e"}];
  var max=pipe[0].count;
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Leads Pipeline</h1><p>Track every lead from first contact to closed deal.</p></div></div>'
    +'<div class="grid-2 mb-24">'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Sales Funnel</div><div style="display:flex;flex-direction:column;gap:14px">'
      +pipe.map(function(p){var pct=Math.round(p.count/max*100);return'<div><div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px"><span>'+esc(p.stage)+'</span><span class="text-muted">'+p.count+'</span></div><div class="progress-wrap"><div class="progress-bar" style="width:'+pct+'%;background:'+p.color+'"></div></div></div>';}).join("")
      +'</div></div>'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Pipeline Chart</div><div class="chart-box"><canvas id="funnelChart"></canvas></div></div>'
    +'</div>'
    +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Active Leads</span></div>'
    +'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>Interest</th><th>Stage</th><th>WhatsApp</th><th>Action</th></tr></thead><tbody>'
    +(S.customers||M.customers).filter(function(c){return c.lead_status!=="CLOSED_LOST";}).map(function(c){
      return'<tr><td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></td>'
        +'<td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td>'
        +'<td>'+bdg(c.lead_status)+'</td>'
        +'<td class="font-mono" style="font-size:12.5px">'+esc((c.whatsapp_number||"").replace("91",""))+'</td>'
        +'<td><button class="btn btn-ghost btn-sm">📞 Follow Up</button></td></tr>';
    }).join("")
    +'</tbody></table></div></div>'
  );
  var fc=$("#funnelChart");if(!fc)return;destroyChart("funnel");
  var d=gc();
  CHARTS.funnel=new Chart(fc,{type:"bar",data:{labels:pipe.map(function(p){return p.stage;}),datasets:[{data:pipe.map(function(p){return p.count;}),backgroundColor:pipe.map(function(p){return p.color+"cc";}),borderColor:pipe.map(function(p){return p.color;}),borderWidth:1.5,borderRadius:8}]},options:{indexAxis:"y",maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:d.tip},scales:{x:{grid:{color:d.grid},ticks:{color:d.text,font:{size:11}}},y:{grid:{display:false},ticks:{color:d.text,font:{size:12}}}}}});
}

/* ══ ANALYTICS ══ */
function renderAnalytics(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Building report…</span></div>');
  var a=M.analytics;

  var locs={};(S.vehicles||M.vehicles).forEach(function(v){var l=v.location||"Other";locs[l]=(locs[l]||0)+1;});
  var lkeys=Object.keys(locs).sort(function(a,b){return locs[b]-locs[a];});
  var lmax=locs[lkeys[0]]||1;
  var lcols=["#f97316","#3b82f6","#22c55e","#a855f7","#f59e0b","#ef4444"];
  var locHtml=lkeys.map(function(l,i){var p=Math.round(locs[l]/lmax*100);return'<div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:5px"><span>'+esc(l)+'</span><span class="text-muted">'+locs[l]+'</span></div><div class="progress-wrap"><div class="progress-bar" style="width:'+p+'%;background:'+lcols[i%6]+'"></div></div></div>';}).join("");

  var kpis=[
    {label:"Total Vehicles",val:num(a.total_vehicles),sub:"All stock",icon:"🚗",color:"orange"},
    {label:"Active Listings",val:num(a.active_for_sale),sub:"Ready to sell",icon:"✅",color:"green"},
    {label:"Sold",val:num(a.sold),sub:"All time",icon:"💰",color:"blue"},
    {label:"Avg Days to Sell",val:num(a.avg_days_to_sell||11),sub:"Per vehicle",icon:"📅",color:"purple"},
    {label:"Revenue MTD",val:money(a.revenue_mtd),sub:"This month",icon:"📈",color:"orange"},
    {label:"Customers",val:num(a.total_customers),sub:"In CRM",icon:"👥",color:"green"}
  ];
  var kpiHtml=kpis.map(function(k){return'<div class="kpi kpi-'+k.color+'"><div class="kpi-icon '+k.color+'">'+k.icon+'</div><div class="kpi-label">'+esc(k.label)+'</div><div class="kpi-value">'+esc(k.val)+'</div><div class="kpi-sub">'+esc(k.sub)+'</div></div>';}).join("");

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Analytics</h1><p>Full performance overview.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm">⬇ Export Report</button></div></div>'
    +'<div class="kpi-grid mb-24">'+kpiHtml+'</div>'
    +'<div class="charts-row mb-24">'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Revenue Trend</span></div><div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="revenueChart"></canvas></div></div></div>'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Inventory by Status</span></div><div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="statusChart"></canvas></div></div></div>'
    +'</div>'
    +'<div class="analytics-grid">'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Fuel Type Distribution</div><div class="chart-box" style="height:200px"><canvas id="fuelChart"></canvas></div></div>'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Top Locations</div>'+locHtml+'</div>'
    +'</div>'
  );
  buildRevenueChart();
  buildStatusChart(a.status_breakdown);
  var fc=$("#fuelChart");if(!fc)return;destroyChart("fuel");
  var fuels={};(S.vehicles||M.vehicles).forEach(function(v){var f=v.fuel_type||"Other";fuels[f]=(fuels[f]||0)+1;});
  var fl=Object.keys(fuels),fv=fl.map(function(l){return fuels[l];});
  var d=gc();var dk=document.documentElement.dataset.theme==="dark";
  CHARTS.fuel=new Chart(fc,{type:"pie",data:{labels:fl,datasets:[{data:fv,backgroundColor:["#3b82f6","#22c55e","#a855f7","#f59e0b","#f97316"].slice(0,fl.length),borderWidth:2,borderColor:dk?"#131d2e":"#fff"}]},options:{maintainAspectRatio:false,plugins:{legend:{position:"right",labels:{padding:12,boxWidth:10,boxHeight:10,color:d.text,font:{size:11.5}}},tooltip:d.tip}}});
}

/* ══ DOCS ══ */
function renderDocs(){
  var eps=[
    {m:"GET", p:"/api/v1/vehicles",                  d:"List vehicles"},
    {m:"POST",p:"/api/v1/vehicles",                  d:"Create vehicle"},
    {m:"GET", p:"/api/v1/vehicles/{id}",              d:"Get vehicle detail"},
    {m:"POST",p:"/api/v1/vehicles/{id}/status",       d:"Update status"},
    {m:"POST",p:"/api/v1/intake/vehicle",             d:"AI intake upload"},
    {m:"GET", p:"/api/v1/customers",                  d:"List customers"},
    {m:"POST",p:"/api/v1/customers",                  d:"Create customer"},
    {m:"GET", p:"/api/v1/ops/analytics",              d:"Dashboard analytics"},
    {m:"GET", p:"/api/v1/ops/export",                 d:"Export to Excel"},
    {m:"POST",p:"/webhook/whatsapp",                  d:"WhatsApp webhook"},
    {m:"GET", p:"/health",                            d:"Health check"}
  ];
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>API Documentation</h1><p>Explore every backend endpoint.</p></div></div>'
    +'<div class="docs-grid mb-24">'
      +'<a class="docs-card" href="/docs" target="_blank"><div class="docs-card-icon orange" style="font-size:22px">⚡</div><h3>Swagger UI</h3><p>Interactive API explorer — try every endpoint live.</p><div class="arrow">Open →</div></a>'
      +'<a class="docs-card" href="/redoc" target="_blank"><div class="docs-card-icon blue" style="font-size:22px">📖</div><h3>ReDoc</h3><p>Clean structured reference documentation.</p><div class="arrow">Open →</div></a>'
      +'<a class="docs-card" href="/openapi.json" target="_blank"><div class="docs-card-icon green" style="font-size:22px">{ }</div><h3>OpenAPI JSON</h3><p>Import into Postman or any API client.</p><div class="arrow">Open →</div></a>'
    +'</div>'
    +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Endpoints</span></div>'
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
    GET(API+"/vehicles?limit=100").then(function(d){if(d&&d.length){S.vehicles=d;updateBadges();}}).catch(function(){});
    GET(API+"/customers").then(function(d){if(d&&d.length)S.customers=d;}).catch(function(){});
  }).catch(function(){
    S.apiOnline=false;
    var s=$("#apiStatus");if(s){s.className="status-chip err";s.innerHTML='<span class="dot"></span>Demo Mode';}
    toast("No DB — running demo data","info","Demo Mode");
  });
}

function updateBadges(){
  var vs=S.vehicles||M.vehicles;
  var av=vs.filter(function(v){return v.status==="AVAILABLE";}).length;
  var pr=vs.filter(function(v){return v.status==="PENDING_REVIEW";}).length;
  var nb=$("#nb-inventory");if(nb)nb.textContent=av||"";
  var nd=$("#nb-dashboard");if(nd)nd.textContent=pr||"";
  var nc=$("#nb-customers");if(nc)nc.textContent=(S.customers||M.customers).length||"";
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
    checkApi();
    setTimeout(function(){rb.classList.remove("spinning");navigate(S.view);toast("Refreshed","success");},1200);
  });
  var gs=$("#globalSearch");
  if(gs)gs.addEventListener("keydown",function(e){if(e.key==="Enter"&&gs.value.trim()){S.q=gs.value.trim();S.filter="all";navigate("inventory");gs.value="";}});
  updateBadges();
  checkApi();
  navigate("dashboard");
}

if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",boot);}else{boot();}
})();
