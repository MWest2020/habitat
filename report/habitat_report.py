#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Habitat run-rapport + hash-chained audit. Stdlib-only, geen runtime-deps.

Draait in de worker na `claude -p`: berekent de diff-hash van de gestagede
agent-wijziging, ketent een regel in .habitat/audit.jsonl, en schrijft
run-report.json + een zelfstandig, zelfverifiërend HTML-rapport.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

# Veldvolgorde van de payload die gehasht wordt. MOET gelijk zijn aan de JS in het
# HTML-rapport (pipe-join), anders faalt de in-browser-verificatie.
FIELDS = ["prev_hash", "ts", "role", "change", "run_id",
          "verdict", "subtype", "diff_hash", "cost", "turns"]


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def git(repo: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout


def build_entry(a) -> dict:
    diff = git(a.repo_dir, "diff", "--cached")
    e = {
        "ts": a.finished_at, "role": a.role, "change": a.change,
        "run_id": a.run_id, "verdict": a.verdict, "subtype": a.subtype,
        "cost": a.cost, "turns": a.turns, "diff_hash": sha256(diff),
    }
    audit = Path(a.repo_dir) / ".habitat" / "audit.jsonl"
    prev = ""
    if audit.exists():
        lines = [l for l in audit.read_text().splitlines() if l.strip()]
        if lines:
            prev = json.loads(lines[-1]).get("entry_hash", "")
    e["prev_hash"] = prev
    e["entry_hash"] = sha256("|".join(str(e[f]) if f != "prev_hash" else prev
                                      for f in FIELDS))
    return e


def main() -> None:
    p = argparse.ArgumentParser()
    for f in ("role", "change", "run-id", "verdict", "subtype", "repo",
              "finished-at", "cost", "turns", "exit"):
        p.add_argument("--" + f, default="")
    p.add_argument("--repo-dir", default=".")
    a = p.parse_args()
    a.run_id = a.run_id or ""
    a.finished_at = a.finished_at or ""

    hab = Path(a.repo_dir) / ".habitat"
    hab.mkdir(exist_ok=True)
    stat = git(a.repo_dir, "diff", "--cached", "--stat").strip()

    entry = build_entry(a)
    with (hab / "audit.jsonl").open("a") as fh:
        fh.write(json.dumps(entry) + "\n")

    # run-report.json (compat met eerdere entrypoint-output)
    (Path(a.repo_dir) / "run-report.json").write_text(json.dumps({
        "role": a.role, "change": a.change, "run_id": a.run_id, "repo": a.repo,
        "verdict": a.verdict, "subtype": a.subtype,
        "total_cost_usd": a.cost, "num_turns": a.turns,
        "claude_exit": a.exit, "finished_at": a.finished_at,
        "diff_hash": entry["diff_hash"],
    }, indent=2) + "\n")

    chain = [json.loads(l) for l in (hab / "audit.jsonl").read_text().splitlines()
             if l.strip()]
    (hab / f"run-report-{a.run_id}.html").write_text(render(entry, stat, chain))
    print(f"[report] .habitat/audit.jsonl (+1) + run-report-{a.run_id}.html")


def render(e: dict, stat: str, chain: list) -> str:
    import html
    badge = "ok" if e["verdict"] == "ok" else "bad"
    head = (f'{html.escape(e["role"])} · {html.escape(e["change"])}')
    tpl = HTML
    tpl = tpl.replace("__TITLE__", html.escape(f'Habitat run {e["run_id"]}'))
    tpl = tpl.replace("__HEAD__", head)
    tpl = tpl.replace("__BADGE__", badge)
    tpl = tpl.replace("__VERDICT__", html.escape(e["verdict"] or "?"))
    tpl = tpl.replace("__COST__", html.escape(str(e["cost"])))
    tpl = tpl.replace("__TURNS__", html.escape(str(e["turns"])))
    tpl = tpl.replace("__TS__", html.escape(e["ts"]))
    tpl = tpl.replace("__STAT__", html.escape(stat or "(geen wijziging)"))
    tpl = tpl.replace("__FIELDS__", json.dumps(FIELDS))
    tpl = tpl.replace("__CHAIN__", json.dumps(chain))
    return tpl


HTML = """<!doctype html><html lang=nl><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>__TITLE__</title>
<style>
:root{color-scheme:light dark}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:2rem;
 max-width:60rem;margin-inline:auto;line-height:1.5}
h1{font-size:1.4rem;margin:0 0 .25rem}
.sub{color:#888;margin-bottom:1.5rem}
.badge{display:inline-block;padding:.1rem .6rem;border-radius:1rem;font-weight:600;font-size:.85rem}
.ok{background:#1b7f3b;color:#fff}.bad{background:#b3261e;color:#fff}
.grid{display:flex;gap:2rem;flex-wrap:wrap;margin:1rem 0}
.grid div{font-size:.9rem}.grid b{display:block;color:#888;font-weight:500}
pre{background:#8881;padding:1rem;border-radius:.5rem;overflow-x:auto;font-size:.85rem}
table{border-collapse:collapse;width:100%;font-size:.8rem}
th,td{text-align:left;padding:.4rem .5rem;border-bottom:1px solid #8883}
code{font-family:ui-monospace,monospace}
.v-ok{color:#1b7f3b;font-weight:700}.v-bad{color:#b3261e;font-weight:700}
</style></head><body>
<h1>__HEAD__ <span class="badge __BADGE__">__VERDICT__</span></h1>
<div class=sub>Habitat run-rapport · __TS__</div>
<div class=grid>
 <div><b>verdict</b>__VERDICT__</div><div><b>kosten (USD)</b>__COST__</div>
 <div><b>turns</b>__TURNS__</div>
</div>
<h2>Diff-samenvatting</h2><pre>__STAT__</pre>
<h2>Audit-hashketen</h2>
<p class=sub>Herberekend in je browser — geen server, geen CDN.</p>
<table><thead><tr><th>run</th><th>rol</th><th>verdict</th><th>entry_hash</th><th>keten</th></tr></thead>
<tbody id=rows></tbody></table>
<script>
const FIELDS=__FIELDS__, CHAIN=__CHAIN__;
const payload=e=>FIELDS.map(f=>String(e[f]??"")).join("|");
async function sha(s){const b=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(s));
 return [...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,"0")).join("")}
(async()=>{const tb=document.getElementById("rows");let prev="";
 for(const e of CHAIN){const calc=await sha(payload(e));
  const ok=calc===e.entry_hash && e.prev_hash===prev;
  const tr=document.createElement("tr");
  // textContent (nooit innerHTML) — audit-waarden worden niet als HTML uitgevoerd
  const mk=(t,cls)=>{const td=document.createElement("td");td.textContent=t;if(cls)td.className=cls;tr.appendChild(td)};
  mk(e.run_id);mk(e.role);mk(e.verdict);mk((e.entry_hash||"").slice(0,12)+"\\u2026");
  mk(ok?"\\u2713 geldig":"\\u2717 gebroken", ok?"v-ok":"v-bad");
  tb.appendChild(tr);prev=e.entry_hash;}
})();
</script></body></html>"""


if __name__ == "__main__":
    main()
