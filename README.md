# Habitat

Een minimaal platform waarop Claude Code-agents autonoom aan repositories werken
binnen expliciete, niet-onderhandelbare grenzen — op een thuiscluster (3× K8s-node,
Tailscale). Habitat weet níets van domeinlogica; het levert vijf dingen:

**werkverdeling · executie · isolatie · escalatie · audit**

Eerste afnemer wordt *wordsworth* (documentpijplijn, aparte repo). Bewust géén
runner-infrastructuur: Git is het overdrachtsmedium, K8s Jobs zijn de executievorm,
één orchestrator-sessie dispatcht.

## Architectuur

```
  laptop (tmux)                          thuiscluster (namespace: agents)
  ┌────────────────────┐                 ┌──────────────────────────────────┐
  │ orchestrator       │  kubectl (SA:   │  ┌─────────┐   default-deny egress│
  │ (1 Claude Code-    │──Jobs CRUD,────▶│  │ Job     │   ─────────────────  │
  │  sessie, mandaat    │   logs lezen)   │  │ worker  │──▶ CoreDNS + Squid    │
  │  in CLAUDE.md)     │                 │  │ claude  │      proxy (allowlist)│
  │                    │                 │  │  -p     │──▶ github/anthropic/… │
  │  escaleert → Mark  │◀── run-rapport  │  └────┬────┘                       │
  └────────────────────┘    (HTML)       └───────┼────────────────────────────┘
                                                  │ push branch + run-report.json
                                                  ▼
                                             GitHub (doelrepo, main beschermd)
```

- **Orchestrator**: één Claude Code-sessie op de laptop. Dispatcht Jobs, streamt
  logs, escaleert naar Mark. Schrijft zelf nooit productiecode.
- **Workers**: K8s Jobs, één image (`claude -p` + `uv` + `git`). Rollen
  (builder/reviewer/security) zijn `.claude/agents/`-files in de **doelrepo**.
- **Isolatie**: default-deny egress; alle uitgaand verkeer via één Squid-proxy met
  domein-allowlist. RBAC per rol, minimaal. Secrets via SOPS+age.
- **Audit**: elke run hash-chained JSONL + single-file HTML-run-rapport naast de code.

## Grenzen

**Verboden, hard-fail, nooit escaleerbaar** — agents verbouwen hun eigen kooi niet:
wijzigingen aan `CLAUDE.md`, `.claude/agents/`, NetworkPolicies, RBAC of
Job-templates. Dubbel afgedwongen (reviewer hard-fail + branch protection/CODEOWNERS).

De volledige escalatiematrix staat in het orchestrator-mandaat (change `add-orchestrator`).

## Werkwijze

Conversational design → OpenSpec (`propose` → `apply` → `archive`) → implementatie.
Changes staan onder [`openspec/`](openspec/). Zie [`CLAUDE.md`](CLAUDE.md) voor conventies.

## Licentie

[EUPL-1.2](LICENSE).
