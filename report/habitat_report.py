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

# De diff_hash dekt uitsluitend de agent-codewijziging. Uitgesloten worden EXACT
# de door habitat gegenereerde artefacten van DÉZE run — op vaste naam + de door
# dispatch bepaalde run-id, mét `literal`-magic (géén wildcards), niet de hele
# .habitat/-map. Zo kan een agent geen bestand onder .habitat/ noemen dat buiten
# de hash valt (`.habitat/evil.py`, `.habitat/run-report-evil.html`, … blijven
# gehasht) en is de hash tóch reproduceerbaar vanaf de gepushte branch — die die
# artefacten wél bevat. run-id komt van dispatch, niet van de agent.
def artifact_excludes(run_id: str) -> list:
    return [
        ":(exclude,literal).habitat/audit.jsonl",
        f":(exclude,literal).habitat/run-report-{run_id}.html",
        f":(exclude,literal).habitat/run-output-{run_id}.md",
        ":(exclude,literal)run-report.json",
    ]


def diff_excludes(run_id: str) -> list:
    return ["--", ".", *artifact_excludes(run_id)]


def diff_hash_scope(run_id: str) -> str:
    return ("git diff <base-ref> HEAD -- . "
            + " ".join(f"'{e}'" for e in artifact_excludes(run_id))
            + " | sha256sum")


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def git(repo: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout


def build_entry(a) -> dict:
    # diff t.o.v. de basis vóór de agent (vangt óók door de agent gecommitte
    # wijzigingen); val terug op --cached als er geen base-ref is meegegeven.
    # Habitat-artefacten uitgesloten -> reproduceerbaar vanaf de branch.
    excl = diff_excludes(a.run_id)
    diff = (git(a.repo_dir, "diff", a.base_ref, *excl) if a.base_ref
            else git(a.repo_dir, "diff", "--cached", *excl))
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
            # De laatste regel kan door een agent zijn beschadigd; een kapotte
            # regel mag het rapport niet laten crashen. prev="" -> de keten breekt
            # zichtbaar in de in-browser-verificatie (fail-closed).
            try:
                prev = json.loads(lines[-1]).get("entry_hash", "")
            except (json.JSONDecodeError, AttributeError):
                prev = ""
    e["prev_hash"] = prev
    e["entry_hash"] = sha256("|".join(str(e[f]) if f != "prev_hash" else prev
                                      for f in FIELDS))
    return e


def agent_result(output_file: str) -> str:
    """Lees het `result`-veld uit het `claude -p`-JSON-eindobject. Robuust: geeft
    "" terug bij ontbrekend/onleesbaar/niet-object JSON of een niet-string result."""
    if not output_file:
        return ""
    try:
        data = json.loads(Path(output_file).read_text())
    except (OSError, json.JSONDecodeError):
        return ""
    r = data.get("result") if isinstance(data, dict) else None
    return r if isinstance(r, str) else ""


def write_run_output(a, hab: Path) -> None:
    """Bewaar de agent-eind-uitvoer als markdown-artefact. ALTIJD schrijven — óók
    zonder leesbaar `result` (dan een placeholder) — zodat habitat dit bestand
    deterministisch bezit en een agent geen eigen `.habitat/run-output-<id>.md` kan
    smokkelen die buiten de diff_hash valt. Wordt ná de hash aangeroepen en is per
    exacte naam uitgesloten, dus de hash-waarde blijft gelijk."""
    result = agent_result(a.output_file)
    body = result if result.strip() else "_(geen agent-result in de CLI-output)_"
    md = (f"# Habitat {a.role} — {a.change}\n\n"
          f"_run_id {a.run_id} · verdict {a.verdict} · {a.finished_at}_\n\n---\n\n"
          f"{body}\n")
    (hab / f"run-output-{a.run_id}.md").write_text(md)


def main() -> None:
    p = argparse.ArgumentParser()
    for f in ("role", "change", "run-id", "verdict", "subtype", "repo",
              "finished-at", "cost", "turns", "exit"):
        p.add_argument("--" + f, default="")
    p.add_argument("--repo-dir", default=".")
    p.add_argument("--base-ref", default="")
    p.add_argument("--output-file", default="")
    a = p.parse_args()
    a.run_id = a.run_id or ""
    a.finished_at = a.finished_at or ""

    hab = Path(a.repo_dir) / ".habitat"
    hab.mkdir(exist_ok=True)
    excl = diff_excludes(a.run_id)
    stat = (git(a.repo_dir, "diff", a.base_ref, "--stat", *excl) if a.base_ref
            else git(a.repo_dir, "diff", "--cached", "--stat", *excl)).strip()

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
        # Reproduceerbaar vanaf de branch: de commit bevat óók de door habitat
        # gegenereerde artefacten van deze run (audit.jsonl, run-report-<id>.html,
        # run-output-<id>.md, dit bestand) die buiten de diff_hash vallen; overige
        # .habitat/-writes van de agent vallen er WÉL binnen.
        "diff_hash_scope": diff_hash_scope(a.run_id),
    }, indent=2) + "\n")

    # Fail-closed: een door de agent beschadigde regel mag het rapport niet laten
    # crashen. Onleesbare/niet-object regels worden NIET stil weggelaten maar als
    # expliciet gebroken rij getoond (lege entry_hash -> de in-browser-verificatie
    # markeert ze ✗ gebroken). Zo kan een agent de keten niet "opschonen" door alle
    # eerdere regels te bederven; de rij blijft zichtbaar in het rapport.
    chain = []
    for l in (hab / "audit.jsonl").read_text().splitlines():
        if not l.strip():
            continue
        try:
            obj = json.loads(l)
        except json.JSONDecodeError:
            obj = None
        if isinstance(obj, dict):
            chain.append(obj)
        else:
            chain.append({"run_id": "(onleesbare regel)", "entry_hash": "",
                          "prev_hash": ""})
    (hab / f"run-report-{a.run_id}.html").write_text(render(entry, stat, chain))

    # Agent-eind-uitvoer als markdown — altijd, ná de hash (zie write_run_output).
    write_run_output(a, hab)
    print(f"[report] .habitat/audit.jsonl (+1) + run-report-{a.run_id}.html "
          f"+ run-output-{a.run_id}.md")


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
