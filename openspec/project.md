# Project: Habitat

## Scope

Een minimaal platform waarop Claude Code-agents autonoom aan repositories werken
binnen expliciete, niet-onderhandelbare grenzen — op een thuiscluster (3× K8s-node,
Tailscale). Habitat levert werkverdeling, executie, isolatie, escalatie en audit.
Het weet níets van domeinlogica. Eerste afnemer: *wordsworth* (aparte repo).

Single-user platform voor Mark Westerweel. Persoonlijke infrastructuur.

## Waarom dit bestaat

Claude Code-agents zijn nuttig maar ongebreideld gevaarlijk: ze mogen alles wat de
sessie mag. Habitat zet er een kooi omheen — netwerk-, RBAC- en credential-isolatie,
een harde escalatiematrix, en een reconstrueerbaar audit-spoor — zodat een agent
autonoom kan werken zonder dat een fout of een compromittering buiten de Job en de
branch reikt. Bewust géén runner-infrastructuur (geen Actions-runners, geen
polling-daemons): Git is het overdrachtsmedium, K8s Jobs zijn de executievorm,
één orchestrator-sessie dispatcht en escaleert.

## Architectuur (besloten)

```
INPUT                     EXECUTIE                  OUTPUT
─────                     ────────                  ──────
goedgekeurde         ┐                          ┌── branch (habitat/<rol>/<change>)
OpenSpec-change      │    K8s Job (worker):     │── run-report.json (in branch)
+ rol (builder/      ├──▶ claude -p in de kooi ─┤── hash-chained audit-JSONL
  reviewer/security) │    (default-deny egress) │── HTML-run-rapport
in de DOELREPO       ┘                          └── escalatie → Mark (tmux)
```

- **Orchestrator**: één Claude Code-sessie op de laptop (tmux). Jobs CRUD + logs +
  escalatie. Schrijft zelf nooit productiecode.
- **Workers**: K8s Jobs, één image (`claude -p` + `uv` + `git`). Rollen zijn
  `.claude/agents/`-files in de doelrepo, niet in Habitat.
- **Isolatie**: default-deny egress → alleen CoreDNS + één Squid-proxy (domein-
  allowlist). RBAC per rol. Secrets via SOPS+age (één cluster-age-key).
- **Git-auth**: single-repo fine-grained PAT over HTTPS, per node intrekbaar.

## Conventies

- OpenSpec-flow: conversational design → propose → apply → archive. Geen code vóór
  "apply".
- Python via `uv`, nooit `pip`. Bestanden ≤ 200 regels.
- Saai en auditeerbaar boven snel of slim.
- Immutable images, per commit-SHA getagd, nooit `latest`.
- Secrets: alleen SOPS+age; nooit hardcoded of client-side.
- Licentie: EUPL-1.2.

## Definition of done (v0)

Orchestrator dispatcht een builder-Job naar een node voor een triviale change in een
testrepo → log streamt in tmux → reviewer- en security-Jobs volgen → orchestrator
escaleert de merge naar Mark, mét HTML-run-rapport. Eén volledige loop, één keer.
