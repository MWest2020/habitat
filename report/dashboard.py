#!/usr/bin/env python3
# SPDX-License-Identifier: EUPL-1.2
"""Habitat aggregaat-dashboard: bundelt alle habitat/*-branches tot één
self-contained, zelfverifiërend HTML-overzicht. Stdlib-only, geen runtime-deps.

Leest per branch de laatste eigen regel uit .habitat/audit.jsonl (via `git show`),
telt de gewijzigde src-bestanden t.o.v. de basis-branch, en rendert dezelfde
tegels/tabel/hashketen-JS als report/habitat_report.py. De keten wordt in de
browser herberekend (crypto.subtle) — dit script tikt hashes nooit over.

Draaien vanuit een checkout van de DOELrepo met de habitat/*-refs gefetcht:
    python3 report/dashboard.py --repo-dir ../wordsworth --out docs/audit-dashboard.html
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

# MOET gelijk zijn aan FIELDS in report/habitat_report.py, anders faalt verificatie.
FIELDS = ["prev_hash", "ts", "role", "change", "run_id",
          "verdict", "subtype", "diff_hash", "cost", "turns"]
EMPTY = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
ROLE_ORDER = {"builder": 0, "reviewer": 1, "security": 2}

# Redactionele bevindingen: default hier, te overschrijven met een sidecar-JSON
# (report/dashboard-findings.json) zodat de tekst los van de code te beheren is.
DEFAULT_FINDINGS = [
    ["var(--ok)", "Audit-integriteit hersteld & bevestigd",
     "De eerste batch toonde <code>diff_hash</code> = sha256(\"\") omdat builders hun "
     "werk zelf committen; de audit bond niet aan de code. Gefixt: <code>diff_hash</code> "
     "meet nu <code>git diff &lt;clone-basis&gt;</code>. Live bevestigd op "
     "<code>add-key-lifecycle</code> en <code>add-ocr</code>."],
    ["var(--warn)", "No-op eerlijk vastgelegd",
     "<code>add-openanonymiser-driver</code> en <code>add-thesis-evaluation</code>: "
     "verdict=ok maar 0 src-files. Beide vereisen iets buiten de kooi. Het platform legt "
     "eerlijk vast dat het niet kan zonder externe input."],
    ["var(--ok)", "Deadline: begrensd én opgelost",
     "<code>add-key-lifecycle</code> en <code>add-ocr</code> raakten eerst de 600s-deadline "
     "(kooi killde netjes, géén deel-branch). Met <code>ACTIVE_DEADLINE_SECONDS=1800</code> "
     "gingen ze alsnog groen. De grens beschermt, de her-run lost op."],
    ["var(--ok)", "3-rol-loop gesloten",
     "<code>add-key-lifecycle</code> en <code>add-ocr</code> doorliepen builder → reviewer "
     "→ security, alle groen. Niets auto-gemerged — elke branch wacht op review."],
]


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout


def discover(repo, prefix):
    """Alle habitat/<rol>/<change>-branches onder <prefix> (bv. origin)."""
    out = git(repo, "branch", "-r", "--format=%(refname:short)")
    pat = re.compile(rf"^{re.escape(prefix)}/habitat/(builder|reviewer|security)/(.+)$")
    found = []
    for line in out.splitlines():
        m = pat.match(line.strip())
        if m:
            found.append((line.strip(), m.group(1), m.group(2)))
    return found


def src_count(repo, ref, base_branch):
    """Gewijzigde bestanden t.o.v. de merge-basis, excl. platform-artefacten."""
    base = git(repo, "merge-base", base_branch, ref).strip()
    if not base:
        return None
    names = git(repo, "diff", "--name-only", base, ref).splitlines()
    skip = re.compile(r"^\.habitat/|^run-report\.json$")
    return sum(1 for n in names if n and not skip.match(n))


def collect(repo, prefix, base_branch):
    """Eén record per run, toegewezen aan zijn eigen branch."""
    runs = []
    for ref, role, change in discover(repo, prefix):
        raw = git(repo, "show", f"{ref}:.habitat/audit.jsonl")
        own = None
        for line in raw.splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("role") == role and rec.get("change") == change:
                own = rec  # laatste eigen regel wint (reviewer/security appenden 1)
        if own is None:
            continue
        own["branch"] = f"habitat/{role}/{change}"
        own["src_files"] = src_count(repo, ref, base_branch)
        runs.append(own)
    runs.sort(key=lambda r: (r["change"], ROLE_ORDER.get(r["role"], 9)))
    return runs


def build(repo, prefix, base_branch, findings):
    runs = collect(repo, prefix, base_branch)
    if not runs:
        raise SystemExit("geen habitat/*-branches met audit.jsonl gevonden")
    date = max(r["ts"] for r in runs)[:10]
    total = round(sum(float(r["cost"]) for r in runs if r.get("cost")), 2)
    data = {"fields": FIELDS, "empty": EMPTY, "runs": runs,
            "totalCost": total, "findings": findings}
    tpl = (Path(__file__).resolve().parent / "dashboard.html.tpl").read_text()
    return tpl.replace("__DATE__", date).replace(
        "__DATA__", json.dumps(data, ensure_ascii=False))


def main():
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser()
    p.add_argument("--repo-dir", default=".", help="checkout van de doelrepo")
    p.add_argument("--prefix", default="origin", help="remote-refprefix")
    p.add_argument("--base-branch", default="origin/main")
    p.add_argument("--findings", default=str(here / "dashboard-findings.json"))
    p.add_argument("--out", default=str(here.parent / "docs" / "audit-dashboard.html"))
    a = p.parse_args()

    findings = DEFAULT_FINDINGS
    fp = Path(a.findings)
    if fp.exists():
        findings = json.loads(fp.read_text())

    html = build(a.repo_dir, a.prefix, a.base_branch, findings)
    Path(a.out).write_text(html)
    n = html.count('"run_id"')
    print(f"[dashboard] {a.out} — {n} runs, basis {a.base_branch}")


if __name__ == "__main__":
    main()
