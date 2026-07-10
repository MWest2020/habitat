<!doctype html><html lang="nl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Habitat — audit-dashboard</title>
<style>
:root{
  --sans: system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono: ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --paper:#eaeef0; --surface:#fff; --ink:#12191c; --muted:#54666c; --line:#d5dde0;
  --accent:#1f8a7d; --ok:#2e7d55; --warn:#b7791f; --crit:#bb4630;
  --shadow:0 1px 2px rgba(16,30,34,.06),0 2px 8px rgba(16,30,34,.05);
}
@media (prefers-color-scheme:dark){:root{
  --paper:#0c1315; --surface:#121c1f; --ink:#e7eef0; --muted:#8ba1a6; --line:#213137;
  --accent:#3fb3a3; --ok:#57b184; --warn:#d4a24a; --crit:#e0715a; --shadow:none; }}
:root[data-theme="light"]{--paper:#eaeef0;--surface:#fff;--ink:#12191c;--muted:#54666c;--line:#d5dde0;--accent:#1f8a7d;--ok:#2e7d55;--warn:#b7791f;--crit:#bb4630;--shadow:0 1px 2px rgba(16,30,34,.06),0 2px 8px rgba(16,30,34,.05);}
:root[data-theme="dark"]{--paper:#0c1315;--surface:#121c1f;--ink:#e7eef0;--muted:#8ba1a6;--line:#213137;--accent:#3fb3a3;--ok:#57b184;--warn:#d4a24a;--crit:#e0715a;--shadow:none;}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{max-width:72rem;margin-inline:auto;padding:2.5rem 1.5rem 4rem}
.eyebrow{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:600}
h1{font-size:1.7rem;margin:.3rem 0 .2rem;letter-spacing:-.01em;text-wrap:balance}
.sub{color:var(--muted);font-size:.95rem}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(8.5rem,1fr));gap:.75rem;margin:1.75rem 0}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:.6rem;padding:.9rem 1rem;box-shadow:var(--shadow)}
.tile .k{font-size:.72rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.tile .v{font-size:1.5rem;font-weight:650;margin-top:.15rem;font-variant-numeric:tabular-nums}
h2{font-size:1.05rem;margin:2.25rem 0 .75rem;letter-spacing:-.005em}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:.6rem;background:var(--surface);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:.86rem;min-width:46rem}
th,td{text-align:left;padding:.62rem .8rem;border-bottom:1px solid var(--line);white-space:nowrap}
thead th{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;background:var(--surface);position:sticky;top:0}
tbody tr:last-child td{border-bottom:none}
td.num{font-variant-numeric:tabular-nums;text-align:right}
.mono{font-family:var(--mono);font-size:.82em}
.change{font-weight:600}.role{color:var(--muted)}
.pill{display:inline-block;padding:.08rem .5rem;border-radius:1rem;font-size:.74rem;font-weight:600;border:1px solid transparent}
.pill.ok{color:var(--ok);background:color-mix(in srgb,var(--ok) 15%,transparent);border-color:color-mix(in srgb,var(--ok) 32%,transparent)}
.pill.warn{color:var(--warn);background:color-mix(in srgb,var(--warn) 15%,transparent);border-color:color-mix(in srgb,var(--warn) 32%,transparent)}
.pill.crit{color:var(--crit);background:color-mix(in srgb,var(--crit) 15%,transparent);border-color:color-mix(in srgb,var(--crit) 32%,transparent)}
tr.failed td:first-child{box-shadow:inset 3px 0 0 var(--crit)}
.verify{font-weight:700}.verify.good{color:var(--ok)}.verify.bad{color:var(--crit)}
.flag{color:var(--warn);font-size:.75rem}
.findings{display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem;margin-top:.5rem}
.card{background:var(--surface);border:1px solid var(--line);border-radius:.6rem;padding:1.1rem 1.2rem;box-shadow:var(--shadow)}
.card h3{margin:.1rem 0 .5rem;font-size:.98rem;display:flex;align-items:center;gap:.5rem}
.dot{width:.6rem;height:.6rem;border-radius:50%;flex:none}
.card p{margin:.3rem 0 0;font-size:.86rem;color:var(--muted)}
.card code{font-family:var(--mono);font-size:.82em;color:var(--ink)}
footer{margin-top:2.5rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:1rem}
</style></head>
<body><div class="wrap">
<header>
  <div class="eyebrow">Habitat &middot; agent-platform</div>
  <h1>Audit-dashboard</h1>
  <div class="sub">Wordsworth-roadmap gebouwd via dispatched K8s-Jobs &middot; __DATE__ &middot; hashketen in je browser geverifieerd</div>
</header>
<div class="tiles" id="tiles"></div>
<h2>Runs</h2>
<div class="tablewrap"><table>
<thead><tr><th>Change</th><th>Rol</th><th>Status</th><th class="num">src</th><th class="num">turns</th><th class="num">kosten&nbsp;$</th><th>diff_hash</th><th>entry_hash</th><th>keten</th></tr></thead>
<tbody id="rows"></tbody></table></div>
<h2>Wat het platform ving</h2>
<div class="findings" id="findings"></div>
<footer>Bron: <span class="mono">.habitat/audit.jsonl</span> + self-verifying HTML per branch op <span class="mono">habitat/&lt;rol&gt;/&lt;change&gt;</span>. Niets auto-gemerged &mdash; elke branch wacht op review (v0-escalatie). Hashketen per run herberekend met <span class="mono">crypto.subtle</span>; geen externe requests.</footer>
</div>
<script>
const D = __DATA__;
const payload = e => D.fields.map(f => String(e[f] ?? "")).join("|");
async function sha(s){const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("");}
function statusOf(r){if(r.verdict!=="ok")return{cls:"crit",label:"time-out"};if(r.role!=="builder")return{cls:"ok",label:"goedgekeurd"};if(!r.src_files)return{cls:"warn",label:"no-op"};return{cls:"ok",label:"gebouwd"};}
const short=h=>h?h.slice(0,10)+"…":"—";
(async()=>{
  const rows=document.getElementById("rows");let verified=0,built=0,approved=0,noop=0,failed=0;
  for(const r of D.runs){
    const st=statusOf(r);
    if(st.label==="gebouwd")built++;else if(st.label==="goedgekeurd")approved++;else if(st.label==="no-op")noop++;else failed++;
    const tr=document.createElement("tr");if(r.verdict!=="ok")tr.className="failed";
    const cell=(t,cls)=>{const td=document.createElement("td");if(cls)td.className=cls;td.textContent=t;tr.appendChild(td);};
    cell(r.change,"change");cell(r.role,"role");
    const pt=document.createElement("td");pt.innerHTML='<span class="pill '+st.cls+'">'+st.label+'</span>';tr.appendChild(pt);
    cell(r.src_files==null?"—":String(r.src_files),"num");
    cell(r.turns||"—","num");cell(r.cost?Number(r.cost).toFixed(2):"—","num mono");
    const dt=document.createElement("td");dt.className="mono";
    if(!r.diff_hash)dt.textContent="—";
    else if(r.diff_hash===D.empty)dt.innerHTML='<span class="mono">'+short(r.diff_hash)+'</span> <span class="flag">∅ leeg (pre-fix)</span>';
    else dt.textContent=short(r.diff_hash);
    tr.appendChild(dt);
    cell(short(r.entry_hash),"mono");
    const vt=document.createElement("td");tr.appendChild(vt);
    if(r.entry_hash){const ok=(await sha(payload(r)))===r.entry_hash;if(ok)verified++;vt.innerHTML='<span class="verify '+(ok?'good':'bad')+'">'+(ok?'✓':'✗')+'</span>';}
    else vt.textContent="—";
    rows.appendChild(tr);
  }
  const chained=D.runs.filter(r=>r.entry_hash).length;
  const tiles=[["Runs",D.runs.length],["Gebouwd",built],["Goedgekeurd",approved],["No-op",noop],["Time-out",failed],["Kosten","$"+D.totalCost],["Keten ✓",verified+"/"+chained]];
  document.getElementById("tiles").innerHTML=tiles.map(t=>'<div class="tile"><div class="k">'+t[0]+'</div><div class="v">'+t[1]+'</div></div>').join("");
  document.getElementById("findings").innerHTML=D.findings.map(f=>'<div class="card"><h3><span class="dot" style="background:'+f[0]+'"></span>'+f[1]+'</h3><p>'+f[2]+'</p></div>').join("");
})();
</script></body></html>
