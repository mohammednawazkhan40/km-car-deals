/* KM Car Deals — Dealership OS  |  Admin Dashboard */
(function(){"use strict";
var API="/api/v1";var CHARTS={};
var S={view:"dashboard",filter:"all",q:"",mode:"grid",apiOnline:false,vehicles:[],customers:[],_st:null};
var intakeFiles=[];var intakeStep=1;

/* ── Helpers ── */
function $(s,c){return(c||document).querySelector(s);}
function $$(s,c){return Array.from((c||document).querySelectorAll(s));}
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function money(v){if(!v)return"—";var n=Number(v);if(isNaN(n))return v;if(n>=10000000)return"₹"+(n/10000000).toFixed(2)+"Cr";if(n>=100000)return"₹"+(n/100000).toFixed(2)+"L";return"₹"+n.toLocaleString("en-IN");}
function km(v){if(v==null)return"—";var n=Number(v);return n>=1000?(n/1000).toFixed(1)+"k km":n.toLocaleString("en-IN")+" km";}
function num(v){return Number(v||0).toLocaleString("en-IN");}
function ini(name){return(name||"?").split(" ").map(function(w){return w[0]||"";}).slice(0,2).join("").toUpperCase()||"?";}
function bdg(s){if(!s)return"";return'<span class="badge badge-'+String(s).replace(/[^A-Z0-9_]/g,"_")+'">'+String(s).replace(/_/g," ")+"</span>";}
function setContent(h){var c=$("#content");if(c)c.innerHTML=h;}
function destroyChart(k){if(CHARTS[k]){try{CHARTS[k].destroy();}catch(e){}delete CHARTS[k];}}
function gc(){var dk=document.documentElement.dataset.theme==="dark";return{grid:dk?"rgba(255,255,255,.06)":"rgba(0,0,0,.06)",text:dk?"#5d6d84":"#94a3b8",tip:{backgroundColor:"#1a2540",titleColor:"#e8edf5",bodyColor:"#a8b4c8",borderColor:"rgba(255,255,255,.1)",borderWidth:1,padding:12,cornerRadius:10}};}
function purl(p){var fp=p.file_path||p;return/^https?:/.test(fp)?fp:"/uploads/"+fp.replace(/^.*[\\/]data[\\/]uploads[\\/]/,"").replace(/\\/g,"/");}
function confColor(c){return c>=0.9?"var(--success)":c>=0.7?"var(--warning)":"var(--danger)";}
function confIcon(c){return c>=0.9?"✅":c>=0.7?"⚠️":"❌";}

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
  type=type||"info";var icons={success:"✅",error:"❌",warning:"⚠️",info:"ℹ️"};
  var stack=$("#toastStack");if(!stack)return;
  var el=document.createElement("div");el.className="toast "+type;
  el.innerHTML='<span class="toast-icon">'+icons[type]+'</span><div class="toast-content"><div class="toast-title">'+(title||type)+'</div><div class="toast-msg">'+esc(msg)+'</div></div><button class="toast-dismiss">✕</button>';
  el.querySelector(".toast-dismiss").onclick=function(){el.remove();};
  stack.appendChild(el);setTimeout(function(){el.remove();},5000);
}

/* ── Modal ── */
function openModal(title,body){$("#modalTitle").textContent=title;$("#modalBody").innerHTML=body;$("#modalBackdrop").hidden=false;}
function closeModal(){$("#modalBackdrop").hidden=true;$("#modalBody").innerHTML="";}

/* ── Nav ── */
var LABELS={dashboard:"Dashboard",inventory:"Inventory",intake:"AI Intake",approval:"Approval Queue",customers:"Customers",leads:"Leads",analytics:"Analytics",audit:"Audit Log",settings:"Settings",docs:"API Docs"};
function navigate(v){
  S.view=v;
  $$(".nav-item").forEach(function(n){n.classList.toggle("active",n.dataset.view===v);});
  var pt=$("#pageTitle");if(pt)pt.textContent=LABELS[v]||v;
  var map={dashboard:renderDashboard,inventory:renderInventory,intake:renderIntake,approval:renderApproval,customers:renderCustomers,leads:renderLeads,analytics:renderAnalytics,audit:renderAudit,settings:renderSettings,docs:renderDocs};
  if(map[v])map[v]();
  window.scrollTo({top:0,behavior:"smooth"});
  $("#sidebar").classList.remove("open");$("#sidebarOverlay").classList.remove("show");
}
window.navigate=navigate;

/* ── Empty state ── */
function empty(icon,title,sub,btn,act){
  return '<div class="empty-state"><div style="font-size:40px">'+icon+'</div><h3>'+esc(title)+'</h3><p>'+esc(sub)+'</p>'+(btn?'<button class="btn btn-primary" onclick="'+act+'">'+esc(btn)+'</button>':'')+'</div>';
}

/* ══════════ DASHBOARD ══════════ */
function renderDashboard(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading…</span></div>');
  Promise.all([
    GET(API+"/ops/analytics").catch(function(){return null;}),
    GET(API+"/approval/pending?statuses=AI_DRAFT,EXTRACTED,NEEDS_REVIEW").catch(function(){return[];})
  ]).then(function(res){
    var a=res[0]||{total_vehicles:0,active_for_sale:0,sold:0,total_customers:0,open_handoffs:0,status_breakdown:{}};
    var pending=res[1]||[];
    paintDashboard(a,pending);
  });
}

function paintDashboard(a,pending){
  var sb=a.status_breakdown||{};var total=a.total_vehicles||1;
  var kpis=[
    {label:"Total Inventory",val:num(a.total_vehicles),icon:"🚗",color:"orange"},
    {label:"For Sale",val:num(a.active_for_sale),icon:"✅",color:"green"},
    {label:"Sold",val:num(a.sold),icon:"💰",color:"blue"},
    {label:"Customers",val:num(a.total_customers),icon:"👥",color:"purple"},
    {label:"Pending Review",val:num(pending.length),icon:"⏳",color:"red"},
    {label:"Open Handoffs",val:num(a.open_handoffs),icon:"🤝",color:"orange"}
  ];
  var kpiHtml=kpis.map(function(k){return'<div class="kpi kpi-'+k.color+'"><div class="kpi-icon '+k.color+'">'+k.icon+'</div><div class="kpi-label">'+esc(k.label)+'</div><div class="kpi-value">'+esc(k.val)+'</div></div>';}).join("");

  var pendHtml=pending.slice(0,6).map(function(v){
    var conf=v.confidence_summary||{};var fields=Object.keys(conf);
    var avg=fields.length?fields.reduce(function(s,f){return s+(conf[f].confidence||0);},0)/fields.length:0;
    return '<div class="activity-item" style="cursor:pointer" onclick="navigate(\'approval\')">'
      +'<div class="activity-icon orange">'+bdg(v.status)+'</div>'
      +'<div class="activity-body"><div class="activity-title">'+esc(v.vehicle_name||v.stock_id||"New vehicle")+'</div>'
      +'<div class="activity-sub">Avg confidence: <span style="color:'+confColor(avg)+'">'+Math.round(avg*100)+'%</span> · '+v.conflicts+' conflict(s)</div></div>'
      +'<div class="activity-time">'+(v.ready_for_approval?'<span style="color:var(--success)">Ready ✓</span>':'<span style="color:var(--warning)">Review needed</span>')+'</div></div>';
  }).join("")||'<div class="empty-state" style="padding:24px"><p>No vehicles pending review.</p></div>';

  var statItems=[{l:"Available",v:sb.AVAILABLE||0,c:"#22c55e"},{l:"Reserved",v:sb.RESERVED||0,c:"#f59e0b"},{l:"Negotiation",v:sb.NEGOTIATION||0,c:"#3b82f6"},{l:"Published",v:sb.PUBLISHED||0,c:"#f97316"},{l:"Review",v:sb.NEEDS_REVIEW||0,c:"#a855f7"}];
  var qsHtml=statItems.map(function(i){var p=Math.round(i.v/total*100);return'<div class="qs-item"><div><div class="qs-label"><span class="qs-dot" style="background:'+i.c+'"></span>'+esc(i.l)+'</div><div class="qs-bar-wrap mt-8"><div class="qs-bar" style="width:'+p+'%;background:'+i.c+'"></div></div></div><div class="qs-val">'+i.v+'</div></div>';}).join("");

  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Dashboard</h1><p>Welcome back, Admin. KM Car Deals Dealership OS.</p></div>'
    +'<div class="page-header-actions"><button class="btn btn-ghost btn-sm" onclick="navigate(\'analytics\')">📊 Full Report</button></div></div>'
    +'<div class="kpi-grid">'+kpiHtml+'</div>'
    +'<div class="charts-row mb-24">'
      +'<div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock by Status</span></div><div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="statusChart"></canvas></div></div></div>'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Pending Approval</span><button class="btn btn-ghost btn-sm" onclick="navigate(\'approval\')">View all →</button></div><div class="activity-list">'+pendHtml+'</div></div>'
    +'</div>'
    +'<div class="bottom-row">'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Stock Health</span></div><div class="quick-stats">'+qsHtml+'</div></div>'
      +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Quick Actions</div>'
        +'<div style="display:flex;flex-direction:column;gap:10px">'
          +'<button class="btn btn-primary" onclick="navigate(\'intake\')">⚡ New AI Intake</button>'
          +'<button class="btn btn-ghost" onclick="navigate(\'approval\')">✅ Review Queue ('+pending.length+')</button>'
          +'<a class="btn btn-ghost" href="/catalog" target="_blank">🌐 Public Catalog ↗</a>'
          +'<button class="btn btn-ghost" onclick="navigate(\'customers\')">👥 CRM</button>'
        +'</div>'
      +'</div>'
    +'</div>'
  );
  buildStatusChart(sb);
}

function buildStatusChart(sb){
  var c=$("#statusChart");if(!c)return;destroyChart("status");
  var palette={AVAILABLE:"#22c55e",RESERVED:"#f59e0b",NEGOTIATION:"#3b82f6",PUBLISHED:"#f97316",NEEDS_REVIEW:"#a855f7",SOLD:"#64748b",AI_DRAFT:"#1e293b",EXTRACTED:"#0ea5e9"};
  var labels=[],vals=[],cols=[];
  Object.keys(sb).forEach(function(k){if(sb[k]>0){labels.push(k.replace(/_/g," "));vals.push(sb[k]);cols.push(palette[k]||"#64748b");}});
  if(!vals.length){labels=["No data"];vals=[1];cols=["#334155"];}
  var d=gc();var dk=document.documentElement.dataset.theme==="dark";
  CHARTS.status=new Chart(c,{type:"doughnut",data:{labels:labels,datasets:[{data:vals,backgroundColor:cols,borderWidth:2,borderColor:dk?"#131d2e":"#fff",hoverOffset:8}]},options:{maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{padding:12,boxWidth:10,boxHeight:10,color:d.text,font:{size:11.5}}},tooltip:d.tip}}});
}

/* ══════════ INVENTORY ══════════ */
function renderInventory(){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Inventory</h1></div>'
    +'<div class="page-header-actions"><button class="btn btn-primary btn-sm" onclick="navigate(\'intake\')">＋ Add Vehicle</button></div></div>'
    +'<div class="toolbar"><div class="toolbar-left"><div class="search-box"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input type="text" id="invQ" placeholder="Search make, model, stock ID…" value="'+esc(S.q)+'"></div>'
    +'<div class="filter-pills">'
    +["all","AI_DRAFT","EXTRACTED","NEEDS_REVIEW","DEALER_APPROVED","PUBLISHED","AVAILABLE","RESERVED","SOLD"].map(function(f){return'<button class="pill filter-pill'+(S.filter===f?" active":"")+ '" data-f="'+f+'">'+f.replace(/_/g," ")+'</button>';}).join("")
    +'</div></div></div><div id="invBody"></div>'
  );
  $$(".filter-pill").forEach(function(b){b.addEventListener("click",function(){S.filter=b.dataset.f;$$(".filter-pill").forEach(function(p){p.classList.toggle("active",p.dataset.f===S.filter);});loadInv();});});
  var qi=$("#invQ");if(qi)qi.addEventListener("input",function(){S.q=qi.value;clearTimeout(S._st);S._st=setTimeout(loadInv,200);});
  loadInv();
}

function loadInv(){
  var body=$("#invBody");if(!body)return;
  body.innerHTML='<div class="loading-state"><div class="spinner"></div><span>Loading…</span></div>';
  var url=API+"/vehicles?limit=100&active_only=false"+(S.filter&&S.filter!=="all"?"&status="+S.filter:"")+(S.q?"&q="+encodeURIComponent(S.q):"");
  GET(url).then(function(cars){
    if(!body.parentNode)return;
    if(!cars||!cars.length){body.innerHTML=empty("🚗","No vehicles found","Try a different filter.","Add Vehicle","navigate('intake')");return;}
    body.innerHTML='<div class="inv-grid">'+cars.map(invCard).join("")+'</div>';
  }).catch(function(){body.innerHTML=empty("⚠️","Backend offline","Start the server to see inventory.","","");});
}

function invCard(v){
  var photos=v.photos||[];var main=photos.slice().sort(function(a,b){return(b.is_primary?1:0)-(a.is_primary?1:0);})[0];
  var imgHtml=main?'<img src="'+esc(purl(main))+'" alt="" loading="lazy">'
    :'<div class="car-photo-placeholder" style="font-size:40px;display:grid;place-items:center;height:100%">🚗</div>';
  var name=v.vehicle_name||((v.manufacturer||"")+" "+(v.model||"")).trim()||"Vehicle";
  return '<div class="car-card">'
    +'<div class="car-photo"><div class="photo-gradient"></div>'+imgHtml
    +'<div class="badge-pos">'+bdg(v.status)+'</div></div>'
    +'<div class="car-body">'
      +'<div class="car-top"><div><div class="car-name">'+esc(name)+'</div><div class="car-id">'+esc(v.stock_id||"")+'</div></div><div class="car-price">'+money(v.selling_price)+'</div></div>'
      +'<div class="car-specs"><div class="spec-item"><div class="spec-key">Year</div><div class="spec-val">'+esc(v.manufacturing_year||"—")+'</div></div><div class="spec-item"><div class="spec-key">Fuel</div><div class="spec-val">'+esc(v.fuel_type||"—")+'</div></div><div class="spec-item"><div class="spec-key">KM</div><div class="spec-val">'+km(v.mileage_km)+'</div></div><div class="spec-item"><div class="spec-key">Owner</div><div class="spec-val">'+esc(v.owner_count||"—")+'</div></div></div>'
      +'<div class="car-footer"><button class="btn btn-ghost btn-sm flex-1" onclick="showVehicleApproval(\''+esc(v.vehicle_id)+'\')">👁 Review</button>'
      +(["AI_DRAFT","EXTRACTED","NEEDS_REVIEW"].includes(v.status)?'<button class="btn btn-primary btn-sm" onclick="quickApprove(\''+esc(v.vehicle_id)+'\')">✅ Approve</button>':'')
      +(v.status==="DEALER_APPROVED"?'<button class="btn btn-success btn-sm" onclick="quickPublish(\''+esc(v.vehicle_id)+'\')">🚀 Publish</button>':'')
      +'</div>'
    +'</div></div>';
}

window.quickApprove=function(id){
  POST(API+"/approval/"+id+"/approve",{approved_by:"admin"}).then(function(){toast("Vehicle approved","success");loadInv();}).catch(function(e){toast(e.message,"error");});
};
window.quickPublish=function(id){
  POST(API+"/approval/"+id+"/publish",{published_by:"admin"}).then(function(){toast("Vehicle published to catalog","success");loadInv();}).catch(function(e){toast(e.message,"error");});
};

/* ══════════ AI INTAKE (3-step wizard) ══════════ */
function renderIntake(){
  intakeStep=1;intakeFiles=[];
  setContent(buildIntakeStep1());
  wireIntakeStep1();
}

function buildIntakeStep1(){
  return '<div class="page-header"><div class="page-header-text"><h1>AI Vehicle Intake</h1><p>Step 1 of 3 — Upload RC Card & Documents</p></div></div>'
  +'<div class="wizard-steps mb-24"><div class="wstep active">1 Upload RC</div><div class="wstep">2 Review & Edit</div><div class="wstep">3 Photos & Publish</div></div>'
  +'<div class="grid-2" style="align-items:start">'
    +'<div style="display:flex;flex-direction:column;gap:20px">'
      +'<div class="card card-pad">'
        +'<div class="form-section-title">📄 RC Card / Documents</div>'
        +'<div class="dropzone" id="dzRC"><div class="dropzone-icon">⬆</div><h3>Drag & drop RC card here</h3><p>or <strong>browse</strong> to choose · JPG, PNG, PDF</p><p style="font-size:12px;margin-top:6px;color:var(--text-muted)">RC images, insurance, PUC accepted</p></div>'
        +'<input type="file" id="fiRC" multiple accept="image/*,.pdf" hidden>'
        +'<div class="file-list" id="flRC"></div>'
      +'</div>'
      +'<div class="card card-pad">'
        +'<div class="form-section-title">📸 Vehicle Photos</div>'
        +'<div class="dropzone" id="dzPh"><div class="dropzone-icon">📷</div><h3>Drag & drop car photos here</h3><p>Exterior, interior, odometer, engine bay</p></div>'
        +'<input type="file" id="fiPh" multiple accept="image/*" hidden>'
        +'<div class="file-list" id="flPh"></div>'
      +'</div>'
    +'</div>'
    +'<div style="display:flex;flex-direction:column;gap:20px">'
      +'<div class="card card-pad">'
        +'<div class="form-section-title">ℹ️ Vehicle Details (optional — AI extracts from RC)</div>'
        +'<div style="display:flex;flex-direction:column;gap:14px">'
          +'<div class="field"><label>Seller WhatsApp</label><input class="input" id="fWhat" placeholder="91XXXXXXXXXX"></div>'
          +'<div class="field"><label>Vehicle hint (e.g. "Hyundai Creta 2022 Diesel")</label>'
            +'<div style="display:flex;gap:8px">'
              +'<input class="input" id="fName" placeholder="Type or speak…">'
              +'<button class="btn btn-ghost btn-sm" id="voiceBtn" title="Voice input">🎤</button>'
            +'</div>'
          +'</div>'
          +'<div class="field"><label>Price (₹)</label><input class="input" id="fPrice" placeholder="Leave blank if unknown — shows as Pending"></div>'
          +'<div class="field"><label>Referral Source</label>'
            +'<select class="input" id="fReferral">'
              +'<option value="">Select referral…</option>'
              +["WALK_IN","WHATSAPP","INSTAGRAM","FACEBOOK","WEBSITE","REFERENCE","DEALER","CUSTOMER","OTHER"].map(function(r){return'<option value="'+r+'">'+r.replace(/_/g," ")+'</option>';}).join("")
            +'</select>'
          +'</div>'
        +'</div>'
      +'</div>'
      +'<div class="card card-pad" style="font-size:13px;color:var(--text-2)">'
        +'<div style="font-size:12px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px">What the AI does</div>'
        +["Reads RC via OCR — extracts registration, chassis, engine, owner","Identifies make / model / year from photos using vision AI","Flags low-confidence fields for your review","Detects duplicate registrations before creating a record","Generates a professional listing description","Never publishes without your approval"].map(function(t,i){return'<div style="display:flex;gap:10px;align-items:flex-start;margin-bottom:8px"><div style="width:20px;height:20px;border-radius:50%;background:var(--brand-gradient);color:#fff;display:grid;place-items:center;font-size:10px;font-weight:800;flex-shrink:0">'+(i+1)+'</div><span>'+esc(t)+'</span></div>';}).join("")
      +'</div>'
      +'<button class="btn btn-primary btn-lg w-full" id="intakeBtn" style="justify-content:center">⚡ Run AI Intake</button>'
      +'<div id="progWrap" style="display:none;margin-top:16px">'
        +'<div style="display:flex;justify-content:space-between;font-size:13px;font-weight:600;margin-bottom:6px"><span id="progLabel">Uploading…</span><span id="progPct">0%</span></div>'
        +'<div class="progress-wrap"><div class="progress-bar" id="progBar" style="width:0%"></div></div>'
      +'</div>'
    +'</div>'
  +'</div>';
}

function wireIntakeStep1(){
  wireDropzone("dzRC","fiRC","flRC");
  wireDropzone("dzPh","fiPh","flPh");
  var btn=$("#intakeBtn");if(btn)btn.addEventListener("click",runIntake);
  wireVoice();
}

function wireDropzone(dzId,fiId,flId){
  var dz=$($("#"+dzId)),fi=$("#"+fiId);
  if(!dz||!fi)return;
  dz.addEventListener("click",function(e){if(e.target!==fi)fi.click();});
  dz.addEventListener("dragover",function(e){e.preventDefault();dz.classList.add("drag");});
  dz.addEventListener("dragleave",function(){dz.classList.remove("drag");});
  dz.addEventListener("drop",function(e){e.preventDefault();dz.classList.remove("drag");addFiles(e.dataTransfer.files,flId);});
  fi.addEventListener("change",function(){addFiles(fi.files,flId);fi.value="";});
}

function wireVoice(){
  var btn=$("#voiceBtn");if(!btn)return;
  if(!("webkitSpeechRecognition" in window||"SpeechRecognition" in window)){btn.style.display="none";return;}
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  btn.addEventListener("click",function(){
    var rec=new SR();rec.lang="en-IN";rec.interimResults=false;
    btn.textContent="🔴";btn.disabled=true;
    rec.onresult=function(e){var txt=e.results[0][0].transcript;var f=$("#fName");if(f)f.value=txt;toast("Heard: "+txt,"info");};
    rec.onerror=function(){toast("Voice input failed","error");};
    rec.onend=function(){btn.textContent="🎤";btn.disabled=false;};
    rec.start();
  });
}

function addFiles(list,flId){
  var fl=$("#"+flId);if(!fl)return;
  Array.from(list).forEach(function(f){
    if(intakeFiles.length>=20){toast("Max 20 files","warning");return;}
    intakeFiles.push(f);
    var li=document.createElement("div");li.className="file-item";
    li.innerHTML='<div class="file-item-icon">'+(f.type.startsWith("image")?"🖼":"📄")+'</div>'
      +'<div class="file-item-name">'+esc(f.name)+'</div>'
      +'<div class="file-item-size">'+(f.size/1024).toFixed(1)+' KB</div>'
      +'<button class="file-item-rm">✕</button>';
    li.querySelector(".file-item-rm").onclick=function(){var i=intakeFiles.indexOf(f);if(i>-1)intakeFiles.splice(i,1);li.remove();};
    fl.appendChild(li);
  });
}

function runIntake(){
  var btn=$("#intakeBtn"),pw=$("#progWrap");if(!btn)return;
  var nameVal=($("#fName")||{value:""}).value;
  var priceVal=($("#fPrice")||{value:""}).value;
  if(priceVal){nameVal+=" "+priceVal+" lakh";}
  if(!intakeFiles.length&&!nameVal){toast("Upload RC or add vehicle details","warning");return;}
  btn.disabled=true;btn.innerHTML="⚡ Processing…";if(pw)pw.style.display="block";
  var pct=0,si=0,steps=["Uploading files…","Reading RC document…","Running OCR extraction…","Analysing photos…","Checking duplicates…","Building confidence scores…","Creating stock record…"];
  var timer=setInterval(function(){pct=Math.min(pct+Math.random()*14,92);var bar=$("#progBar"),lbl=$("#progLabel"),pp=$("#progPct");if(bar)bar.style.width=pct.toFixed(0)+"%";if(pp)pp.textContent=pct.toFixed(0)+"%";if(lbl&&si<steps.length)lbl.textContent=steps[si++];},500);
  var fd=new FormData();
  intakeFiles.forEach(function(f){fd.append("files",f,f.name);});
  fd.append("message",nameVal);
  fd.append("seller_whatsapp",($("#fWhat")||{value:""}).value);
  fd.append("referral",($("#fReferral")||{value:""}).value);
  fd.append("intake_source","ADMIN_UI");
  fd.append("process_images","false");
  http("POST",API+"/intake/vehicle",fd).then(function(r){
    clearInterval(timer);var bar=$("#progBar");if(bar)bar.style.width="100%";
    setTimeout(function(){
      if(r&&r.vehicle_id){renderApprovalDetail(r.vehicle_id,true);}
      else{toast(r&&r.message||"Intake complete","success");navigate("approval");}
    },500);
  }).catch(function(e){clearInterval(timer);if(btn){btn.disabled=false;btn.innerHTML="⚡ Run AI Intake";}if(pw)pw.style.display="none";toast(e.message||"Intake failed","error");});
}

/* ══════════ APPROVAL QUEUE ══════════ */
function renderApproval(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading approval queue…</span></div>');
  GET(API+"/approval/pending?statuses=AI_DRAFT,EXTRACTED,NEEDS_REVIEW,DEALER_APPROVED&limit=100").then(function(items){
    paintApprovalQueue(items||[]);
  }).catch(function(){setContent(empty("⚠️","Backend offline","Start the server.","",""));});
}

function paintApprovalQueue(items){
  if(!items.length){setContent(empty("✅","All clear","No vehicles pending review.","Run Intake","navigate('intake')"));return;}
  var tabs=[{s:"AI_DRAFT,EXTRACTED",l:"AI Draft / Extracted"},{s:"NEEDS_REVIEW",l:"Needs Review"},{s:"DEALER_APPROVED",l:"Ready to Publish"}];
  var activeTab=items[0]?items[0].status:"AI_DRAFT";
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Approval Queue</h1><p>'+items.length+' vehicles awaiting action.</p></div></div>'
    +'<div class="card">'
      +'<div class="card-header" style="flex-wrap:wrap;gap:8px">'
        +tabs.map(function(t){var cnt=items.filter(function(i){return t.s.includes(i.status);}).length;return'<button class="btn btn-ghost btn-sm apq-tab" data-s="'+t.s+'" onclick="filterApprovalTab(this,\''+esc(t.s)+'\')">'+esc(t.l)+' <span style="background:var(--brand-primary);color:#fff;border-radius:999px;padding:1px 7px;font-size:10px">'+cnt+'</span></button>';}).join("")
      +'</div>'
      +'<div class="table-wrap" id="apqBody"><table><thead><tr><th>Stock ID</th><th>Vehicle</th><th>Status</th><th>Confidence</th><th>Conflicts</th><th>Referral</th><th>Photos</th><th>Actions</th></tr></thead>'
      +'<tbody>'+items.map(apqRow).join("")+'</tbody></table></div>'
    +'</div>'
  );
}
window.filterApprovalTab=function(btn,s){
  $$(".apq-tab").forEach(function(b){b.classList.toggle("active",b.dataset.s===s);});
};

function apqRow(v){
  var conf=v.confidence_summary||{};var fields=Object.keys(conf);
  var avg=fields.length?fields.reduce(function(s,f){return s+(conf[f].confidence||0);},0)/fields.length:0;
  var confHtml='<span style="color:'+confColor(avg)+';font-weight:700">'+Math.round(avg*100)+'%</span>';
  var actions='<button class="btn btn-ghost btn-sm" onclick="showVehicleApproval(\''+esc(v.vehicle_id)+'\')">👁 Review</button>';
  if(["AI_DRAFT","EXTRACTED","NEEDS_REVIEW"].includes(v.status)){
    actions+=' <button class="btn btn-primary btn-sm" onclick="quickApprove(\''+esc(v.vehicle_id)+'\')">✅ Approve</button>';
    actions+=' <button class="btn btn-danger btn-sm" onclick="rejectPrompt(\''+esc(v.vehicle_id)+'\')">✗ Reject</button>';
  }
  if(v.status==="DEALER_APPROVED"){
    actions+=' <button class="btn btn-success btn-sm" onclick="quickPublish(\''+esc(v.vehicle_id)+'\')">🚀 Publish</button>';
  }
  return '<tr>'
    +'<td class="font-mono" style="font-size:12px">'+esc(v.stock_id||"—")+'</td>'
    +'<td><div style="font-weight:600">'+esc(v.vehicle_name||"Unnamed")+'</div><div style="font-size:12px;color:var(--text-muted)">'+esc(v.registration_number||"No reg")+'</div></td>'
    +'<td>'+bdg(v.status)+'</td>'
    +'<td>'+confHtml+'</td>'
    +'<td>'+(v.conflicts>0?'<span style="color:var(--danger);font-weight:700">'+v.conflicts+'</span>':'-')+'</td>'
    +'<td>'+esc(v.referral||"—")+'</td>'
    +'<td>'+v.photos+'</td>'
    +'<td>'+actions+'</td>'
    +'</tr>';
}

window.rejectPrompt=function(id){
  openModal("Reject Vehicle",
    '<div class="field"><label>Rejection reason</label><textarea class="input" id="rejReason" rows="3" placeholder="Why is this being rejected?"></textarea></div>'
    +'<div style="margin-top:16px;display:flex;gap:10px">'
    +'<button class="btn btn-danger" onclick="doReject(\''+esc(id)+'\')">Reject</button>'
    +'<button class="btn btn-ghost" onclick="closeModal()">Cancel</button></div>'
  );
};
window.doReject=function(id){
  var r=($("#rejReason")||{value:"Rejected by admin"}).value||"Rejected by admin";
  POST(API+"/approval/"+id+"/reject",{reason:r,rejected_by:"admin"}).then(function(){closeModal();toast("Rejected","warning");renderApproval();}).catch(function(e){toast(e.message,"error");});
};

window.showVehicleApproval=function(id,fresh){
  renderApprovalDetail(id,fresh);
};

function renderApprovalDetail(id,fresh){
  if(fresh){navigate("approval");}
  GET(API+"/approval/"+id).then(function(v){
    setContent(buildApprovalDetail(v));
    wireApprovalDetail(v);
  }).catch(function(e){toast(e.message,"error");});
}

function buildApprovalDetail(v){
  var conf=v.confidence_summary||{};
  var IMPORTANT=["registration_number","manufacturer","vehicle_model","fuel_type","vehicle_color","owner_count","manufacturing_year"];
  var needsReview=v.needs_review_fields||[];
  var lowConf=v.low_confidence_fields||[];

  // Build confidence table
  var confRows=(v.facts||[]).map(function(f){
    var pct=Math.round((f.confidence||0)*100);
    var bar='<div style="width:80px;height:6px;background:var(--surface-3);border-radius:3px;display:inline-block;vertical-align:middle"><div style="width:'+pct+'%;height:100%;background:'+confColor(f.confidence||0)+';border-radius:3px"></div></div>';
    var flag=f.needs_review?'<span style="color:var(--warning)"> ⚠ Review</span>':'';
    return '<tr><td style="font-weight:600;font-size:12px">'+esc(f.field)+'</td>'
      +'<td>'+esc(f.value||"—")+'</td>'
      +'<td><span class="badge badge-outline" style="font-size:10px">'+esc(f.source)+'</span></td>'
      +'<td>'+bar+' <span style="font-size:11px;color:'+confColor(f.confidence||0)+'">'+pct+'%</span>'+flag+'</td>'
      +'</tr>';
  }).join("");

  // Build editable fields
  var editForm='<div class="form-grid">'
    +['manufacturer','model','variant','vehicle_color','fuel_type','transmission','owner_count','mileage_km','location'].map(function(k){
      var cur=v[k]||(conf[k]&&conf[k].value)||"";
      return'<div class="field"><label>'+k.replace(/_/g," ")+'</label><input class="input edit-field" data-key="'+k+'" value="'+esc(cur)+'"></div>';
    }).join("")
    +'<div class="field"><label>manufacturing_year</label><input class="input edit-field" data-key="manufacturing_year" value="'+esc(v.manufacturing_year||"")+'"></div>'
    +'<div class="field"><label>selling_price (₹)</label><input class="input edit-field" data-key="selling_price" value="'+esc(v.selling_price||"")+'"></div>'
    +'</div>'
    +'<div class="field mt-16"><label>Description (auto-generated — editable)</label>'
    +'<textarea class="input edit-field" data-key="description" rows="4">'+esc(v.description||"")+'</textarea></div>'
    +'<div class="form-grid mt-16">'
    +'<div class="field"><label>Referral Source</label><select class="input edit-field" data-key="referral">'
    +["","WALK_IN","WHATSAPP","INSTAGRAM","FACEBOOK","WEBSITE","REFERENCE","DEALER","CUSTOMER","OTHER"].map(function(r){return'<option value="'+r+'"'+(v.referral===r?" selected":"")+'>'+r.replace(/_/g," ")+'</option>';}).join("")
    +'</select></div></div>';

  // Photos grid
  var photosHtml=(v.photos_detail||[]).map(function(p){
    var flag=p.duplicate_of?'<span style="color:var(--danger);font-size:10px">Dup</span>':(p.blur_detected?'<span style="color:var(--warning);font-size:10px">Blurry</span>':"");
    return'<div style="position:relative;cursor:pointer" onclick="window.open(\''+esc(purl(p))+'\')"><img src="'+esc(purl(p))+'" style="width:100%;height:100px;object-fit:cover;border-radius:8px;border:2px solid '+(p.is_primary?"var(--brand-primary)":"var(--border)")+'" loading="lazy"><div style="position:absolute;bottom:4px;left:4px;font-size:10px;color:#fff;background:rgba(0,0,0,.6);border-radius:4px;padding:1px 5px">'+esc(p.category||"—")+'</div>'+flag+'</div>';
  }).join("");

  var statusBanner=v.ready_for_approval
    ?'<div style="background:var(--success-bg);color:var(--success);border:1px solid var(--success);border-radius:var(--radius);padding:12px 16px;margin-bottom:20px;font-weight:700">✓ Ready for Approval — all fields have high confidence</div>'
    :(needsReview.length>0||lowConf.length>0
      ?'<div style="background:var(--warning-bg);color:var(--warning);border:1px solid var(--warning);border-radius:var(--radius);padding:12px 16px;margin-bottom:20px">⚠ Some fields need review: '+esc([...new Set([...needsReview,...lowConf])].join(", "))+'</div>'
      :"");

  return '<div class="page-header"><div class="page-header-text"><h1>Review: '+esc(v.vehicle_name||v.stock_id||"Vehicle")+'</h1><p>'+bdg(v.status)+' · '+esc(v.stock_id||"")+'</p></div>'
    +'<div class="page-header-actions">'
    +(["AI_DRAFT","EXTRACTED","NEEDS_REVIEW"].includes(v.status)
      ?'<button class="btn btn-primary" id="btnApprove" data-id="'+esc(v.vehicle_id)+'">✅ Approve & Publish</button> <button class="btn btn-danger" id="btnReject" data-id="'+esc(v.vehicle_id)+'">✗ Reject</button>'
      :'')
    +(v.status==="DEALER_APPROVED"?'<button class="btn btn-success" id="btnPublish" data-id="'+esc(v.vehicle_id)+'">🚀 Publish</button>':'')
    +'<button class="btn btn-ghost" id="btnBack" onclick="navigate(\'approval\')">← Back</button>'
    +'</div></div>'
    +statusBanner
    +'<div style="display:grid;grid-template-columns:1.5fr 1fr;gap:20px;align-items:start">'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Edit & Confirm Fields</div>'+editForm+'<button class="btn btn-ghost btn-sm mt-16" id="btnSave" data-id="'+esc(v.vehicle_id)+'">💾 Save Changes</button></div>'
        +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Photos ('+v.photos+')</div>'
        +(photosHtml?'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px">'+photosHtml+'</div>':empty("📷","No photos","Upload via AI Intake","",""))
        +'</div>'
      +'</div>'
      +'<div style="display:flex;flex-direction:column;gap:20px">'
        +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>AI Confidence</div>'
        +'<div class="table-wrap"><table><thead><tr><th>Field</th><th>Value</th><th>Source</th><th>Confidence</th></tr></thead><tbody>'+confRows+'</tbody></table></div>'
        +'</div>'
        +'<div class="card card-pad"><div class="card-title mb-16"><span class="card-title-dot"></span>Status History</div>'
        +(v.status_history||[]).map(function(h){return'<div style="font-size:12.5px;padding:6px 0;border-bottom:1px solid var(--border)"><span class="badge badge-outline">'+esc(h.from||"START")+'</span> → <span class="badge badge-outline">'+esc(h.to)+'</span> <span style="color:var(--text-muted);margin-left:8px">'+esc(h.by||"system")+'</span></div>';}).join("")
        +'</div>'
      +'</div>'
    +'</div>';
}

function wireApprovalDetail(v){
  var id=v.vehicle_id;
  var btnA=$("#btnApprove");if(btnA)btnA.onclick=function(){quickApprove(id);setTimeout(function(){navigate("approval");},600);};
  var btnR=$("#btnReject");if(btnR)btnR.onclick=function(){rejectPrompt(id);};
  var btnP=$("#btnPublish");if(btnP)btnP.onclick=function(){quickPublish(id);setTimeout(function(){navigate("approval");},600);};
  var btnS=$("#btnSave");
  if(btnS)btnS.onclick=function(){
    var payload={updated_by:"admin"};
    $$(".edit-field").forEach(function(el){var k=el.dataset.key;var val=el.value.trim();if(val)payload[k]=isNaN(val)?val:Number(val);});
    PATCH(API+"/approval/"+id+"/fields",payload).then(function(){toast("Saved","success");renderApprovalDetail(id,false);}).catch(function(e){toast(e.message,"error");});
  };
}

/* ══════════ CUSTOMERS ══════════ */
function renderCustomers(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading…</span></div>');
  GET(API+"/customers?limit=200").then(function(rows){paintCustomers(rows||[]);}).catch(function(){setContent(empty("⚠️","Backend offline","","",""));});
}
function paintCustomers(rows){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Customers</h1><p>'+rows.length+' contacts in CRM.</p></div></div>'
    +'<div class="card">'
      +'<div class="card-header"><span class="card-title"><span class="card-title-dot"></span>All Customers</span>'
        +'<div class="card-actions"><div class="search-box" style="max-width:220px"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg><input type="text" id="custQ" placeholder="Search…"></div></div>'
      +'</div>'
      +(rows.length
        ?'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>WhatsApp</th><th>City</th><th>Lead Status</th><th>Interest</th><th>Consent</th><th>Actions</th></tr></thead><tbody id="custBody">'+custRows(rows)+'</tbody></table></div>'
        :'<div>'+empty("👥","No customers yet","","","")+'</div>')
    +'</div>'
  );
  var qi=$("#custQ");
  if(qi&&rows.length)qi.addEventListener("input",function(){
    var q=qi.value.toLowerCase();var f=rows.filter(function(c){return(c.name||"").toLowerCase().includes(q)||(c.city||"").toLowerCase().includes(q)||(c.whatsapp_number||"").includes(q);});
    var tb=$("#custBody");if(tb)tb.innerHTML=custRows(f);
  });
}
function custRows(rows){
  return rows.map(function(c){
    return'<tr><td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></td>'
      +'<td class="font-mono" style="font-size:12px">'+esc(c.whatsapp_number||"—")+'</td>'
      +'<td>'+esc(c.location||"—")+'</td>'
      +'<td>'+bdg(c.lead_status)+'</td>'
      +'<td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td>'
      +'<td>'+(c.opt_out?'<span class="badge badge-CLOSED_LOST">Opted Out</span>':'<span class="badge badge-AVAILABLE">In</span>')+'</td>'
      +'<td><button class="btn btn-ghost btn-sm" onclick="genFollowup(\''+esc(c.customer_id)+'\')">💬 Follow-up</button></td>'
      +'</tr>';
  }).join("");
}
window.genFollowup=function(id){
  GET(API+"/customers/"+id+"/followup-message").then(function(r){
    openModal("AI Follow-up Message",
      '<div style="background:var(--surface-2);border-radius:var(--radius);padding:16px;font-size:14px;line-height:1.6;margin-bottom:16px">'+esc(r.message)+'</div>'
      +'<button class="btn btn-primary" onclick="navigator.clipboard.writeText(\''+esc(r.message.replace(/'/g,"\\'")+'\');toast(\'Copied!\',\'success\');closeModal()")">📋 Copy</button>'
      +' <button class="btn btn-ghost" onclick="closeModal()">Close</button>'
    );
  }).catch(function(e){toast(e.message,"error");});
};

/* ══════════ LEADS ══════════ */
function renderLeads(){
  GET(API+"/customers?limit=200").then(function(rows){
    rows=rows||[];
    var active=rows.filter(function(c){return c.lead_status!=="LOST"&&c.lead_status!=="NOT_INTERESTED";});
    setContent(
      '<div class="page-header"><div class="page-header-text"><h1>Leads Pipeline</h1></div></div>'
      +'<div class="card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Active Leads</span></div>'
      +(active.length
        ?'<div class="table-wrap"><table><thead><tr><th>Customer</th><th>Interest</th><th>Stage</th><th>WhatsApp</th><th>Actions</th></tr></thead><tbody>'
          +active.map(function(c){return'<tr><td><div class="avatar-row"><div class="avatar">'+esc(ini(c.name))+'</div><div class="avatar-name">'+esc(c.name||"—")+'</div></div></td><td class="text-2">'+esc(c.preferred_vehicle||"—")+'</td><td>'+bdg(c.lead_status)+'</td><td class="font-mono" style="font-size:12px">'+esc((c.whatsapp_number||"").replace("91",""))+'</td><td><button class="btn btn-ghost btn-sm" onclick="genFollowup(\''+esc(c.customer_id)+'\')">💬 Follow-up</button><button class="btn btn-ghost btn-sm" onclick="updateLeadStatus(\''+esc(c.customer_id)+'\',\''+esc(c.lead_status)+'\')">✎ Status</button></td></tr>';}).join("")
          +'</tbody></table></div>'
        :'<div>'+empty("📞","No active leads","","","")+'</div>')
      +'</div>'
    );
  }).catch(function(){setContent(empty("⚠️","Backend offline","","",""));});
}
window.updateLeadStatus=function(id,cur){
  var statuses=["NEW","CONTACTED","INTERESTED","QUALIFIED","NEGOTIATING","FOLLOW_UP","BOOKED","PURCHASED","LOST","NOT_INTERESTED"];
  openModal("Update Lead Status",
    '<div class="field"><label>New Status</label><select class="input" id="newStatus">'+statuses.map(function(s){return'<option'+(s===cur?" selected":"")+'>'+s+'</option>';}).join("")+'</select></div>'
    +'<div class="field mt-16"><label>Notes (optional)</label><input class="input" id="statusNotes" placeholder="Add a note…"></div>'
    +'<div style="margin-top:16px;display:flex;gap:10px">'
    +'<button class="btn btn-primary" onclick="doUpdateStatus(\''+esc(id)+'\')">Update</button>'
    +'<button class="btn btn-ghost" onclick="closeModal()">Cancel</button></div>'
  );
};
window.doUpdateStatus=function(id){
  var s=($("#newStatus")||{value:""}).value;var n=($("#statusNotes")||{value:""}).value;
  PATCH(API+"/customers/"+id+"/lead-status?status="+s+(n?"&notes="+encodeURIComponent(n):""),{}).then(function(){closeModal();toast("Status updated","success");renderLeads();}).catch(function(e){toast(e.message,"error");});
};

/* ══════════ ANALYTICS ══════════ */
function renderAnalytics(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Building report…</span></div>');
  GET(API+"/ops/analytics").then(function(a){
    a=a||{total_vehicles:0,active_for_sale:0,sold:0,total_customers:0,open_handoffs:0,status_breakdown:{}};
    var kpis=[{label:"Total Vehicles",val:num(a.total_vehicles),icon:"🚗",color:"orange"},{label:"For Sale",val:num(a.active_for_sale),icon:"✅",color:"green"},{label:"Sold",val:num(a.sold),icon:"💰",color:"blue"},{label:"Customers",val:num(a.total_customers),icon:"👥",color:"purple"},{label:"Open Handoffs",val:num(a.open_handoffs),icon:"🤝",color:"red"}];
    setContent(
      '<div class="page-header"><div class="page-header-text"><h1>Analytics</h1></div></div>'
      +'<div class="kpi-grid mb-24">'+kpis.map(function(k){return'<div class="kpi kpi-'+k.color+'"><div class="kpi-icon '+k.color+'">'+k.icon+'</div><div class="kpi-label">'+esc(k.label)+'</div><div class="kpi-value">'+esc(k.val)+'</div></div>';}).join("")+'</div>'
      +'<div class="charts-row"><div class="card chart-card"><div class="card-header"><span class="card-title"><span class="card-title-dot"></span>Inventory by Status</span></div><div style="padding:16px 22px 22px"><div class="chart-box"><canvas id="statusChart"></canvas></div></div></div></div>'
    );
    buildStatusChart(a.status_breakdown||{});
  }).catch(function(){setContent(empty("⚠️","Backend offline","","",""));});
}

/* ══════════ AUDIT LOG ══════════ */
function renderAudit(){
  setContent('<div class="loading-state"><div class="spinner"></div><span>Loading…</span></div>');
  GET(API+"/settings/audit-log?limit=100").then(function(logs){
    logs=logs||[];
    setContent(
      '<div class="page-header"><div class="page-header-text"><h1>Audit Log</h1><p>All AI and dealer actions.</p></div></div>'
      +'<div class="card"><div class="table-wrap"><table><thead><tr><th>Time</th><th>Actor</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead><tbody>'
      +(logs.length?logs.map(function(l){return'<tr><td class="font-mono" style="font-size:11px">'+esc((l.created_at||"").replace("T"," ").slice(0,19))+'</td><td>'+esc(l.actor||"system")+'</td><td><span class="badge badge-outline">'+esc(l.action)+'</span></td><td class="text-muted" style="font-size:12px">'+esc(l.entity_type||"")+(l.entity_id?" / "+l.entity_id.slice(0,8)+"…":"")+'</td><td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;font-size:12px">'+esc(l.notes||JSON.stringify(l.after_data||{}))+'</td></tr>';}).join(""):('<tr><td colspan="5">'+empty("📋","No audit entries yet","Actions will appear here.","","")+'</td></tr>'))
      +'</tbody></table></div></div>'
    );
  }).catch(function(){setContent(empty("⚠️","Backend offline","","",""));});
}

/* ══════════ SETTINGS ══════════ */
function renderSettings(){
  GET(API+"/settings/business").then(function(s){paintSettings(s||{});}).catch(function(){paintSettings({});});
}
function paintSettings(s){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>Business Settings</h1><p>KM Car Deals dealer configuration — never hard-coded.</p></div></div>'
    +'<div class="card card-pad">'
    +'<div class="form-grid">'
    +[["business_name","Business Name"],["tagline","Tagline"],["address_line1","Address Line 1"],["address_line2","Address Line 2"],["city","City"],["state","State"],["pincode","Pincode"],["phone_primary","Primary Phone"],["phone_secondary","Secondary Phone"],["whatsapp_number","WhatsApp Number"],["email","Email"],["website_url","Website URL"],["google_maps_url","Google Maps URL"],["default_location","Default Location"]].map(function(f){return'<div class="field"><label>'+f[1]+'</label><input class="input sett-field" data-key="'+f[0]+'" value="'+esc(s[f[0]]||"")+'"></div>';}).join("")
    +'<div class="field"><label>Currency</label><input class="input sett-field" data-key="currency" value="'+esc(s.currency||"INR")+'"></div>'
    +'<div class="field"><label>Auto-publish approved vehicles</label><select class="input sett-field" data-key="auto_publish"><option value="false"'+(s.auto_publish?"":' selected')+'>No — require manual publish</option><option value="true"'+(s.auto_publish?' selected':'')+'>Yes — auto publish on approval</option></select></div>'
    +'</div>'
    +'<button class="btn btn-primary mt-16" id="btnSaveSettings">💾 Save Settings</button>'
    +'</div>'
  );
  var btn=$("#btnSaveSettings");
  if(btn)btn.onclick=function(){
    var payload={updated_by:"admin"};
    $$(".sett-field").forEach(function(el){var k=el.dataset.key;var v=el.value.trim();if(v)payload[k]=k==="auto_publish"?(v==="true"):v;});
    PATCH(API+"/settings/business",payload).then(function(){toast("Settings saved","success");}).catch(function(e){toast(e.message,"error");});
  };
}

/* ══════════ DOCS ══════════ */
function renderDocs(){
  setContent(
    '<div class="page-header"><div class="page-header-text"><h1>API Documentation</h1></div></div>'
    +'<div class="docs-grid mb-24">'
    +'<a class="docs-card" href="/docs" target="_blank"><div class="docs-card-icon orange">⚡</div><h3>Swagger UI</h3><p>Interactive API explorer.</p><div class="arrow">Open →</div></a>'
    +'<a class="docs-card" href="/redoc" target="_blank"><div class="docs-card-icon blue">📖</div><h3>ReDoc</h3><p>Structured reference docs.</p><div class="arrow">Open →</div></a>'
    +'<a class="docs-card" href="/catalog" target="_blank"><div class="docs-card-icon green">🌐</div><h3>Public Catalog</h3><p>Website-facing vehicle listing.</p><div class="arrow">Open →</div></a>'
    +'</div>'
  );
}

/* ══════════ API CHECK ══════════ */
function checkApi(){
  GET("/health").then(function(){
    S.apiOnline=true;
    var s=$("#apiStatus");if(s){s.className="status-chip ok";s.innerHTML='<span class="dot"></span>Online';}
    GET(API+"/vehicles?limit=200&active_only=false").then(function(d){if(d&&d.length)S.vehicles=d;}).catch(function(){});
    GET(API+"/customers?limit=200").then(function(d){if(d&&d.length)S.customers=d;}).catch(function(){});
    GET(API+"/approval/pending?statuses=AI_DRAFT,EXTRACTED,NEEDS_REVIEW&limit=100").then(function(d){
      var nb=$("#nb-approval");if(nb)nb.textContent=(d&&d.length)||"";
    }).catch(function(){});
  }).catch(function(){
    S.apiOnline=false;
    var s=$("#apiStatus");if(s){s.className="status-chip err";s.innerHTML='<span class="dot"></span>Offline';}
  });
}

/* ══════════ THEME ══════════ */
function initTheme(){document.documentElement.dataset.theme=localStorage.getItem("km_theme")||"dark";}
function toggleTheme(){var t=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=t;localStorage.setItem("km_theme",t);Object.keys(CHARTS).forEach(function(k){destroyChart(k);});navigate(S.view);}

/* ══════════ BOOT ══════════ */
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
  var rb=$("#refreshBtn");if(rb)rb.addEventListener("click",function(){rb.style.transform="rotate(360deg)";checkApi();setTimeout(function(){rb.style.transform="";navigate(S.view);toast("Refreshed","success");},1000);});
  var gs=$("#globalSearch");if(gs)gs.addEventListener("keydown",function(e){if(e.key==="Enter"&&gs.value.trim()){S.q=gs.value.trim();S.filter="all";navigate("inventory");gs.value="";}});
  checkApi();
  navigate("dashboard");
}
if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",boot);}else{boot();}
})();
