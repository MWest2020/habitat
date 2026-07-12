---
status: draft
last_reviewed: 2026-07-12
---

# Habitat — architectuur

Habitat is een minimaal platform waarop Claude Code-agents autonoom aan repositories
werken binnen harde, niet-onderhandelbare grenzen. Het levert vijf dingen —
**werkverdeling, executie, isolatie, escalatie, audit** — en weet níets van
domeinlogica. Eerste afnemer wordt *wordsworth* (aparte repo).

## Waar draait wat

```
  LAPTOP (buiten de kooi)                THUISCLUSTER (kubeadm, Cilium v1.19, Hubble)
  ┌──────────────────────┐              ┌───────────────────────────────────────────┐
  │ orchestrator          │  kubectl     │ control-plane (HA):  cp-01 .202            │
  │ 1 Claude Code-sessie  │  (SA:        │                      cp-02 .203            │
  │ in tmux               │──orchestr.)─▶│                      cp-03 .204            │
  │ mandaat in CLAUDE.md  │  API-VIP     │ workers:             node-01 .205          │
  │                       │  .201:6443   │                      node-02 .206          │
  │ escaleert → Mark      │◀─run-rapport │                      node-03 .207          │
  └──────────────────────┘              │  namespace: agents  ← de kooi              │
                                         └───────────────────────────────────────────┘
```

SSH-aliassen (`~/.ssh/config`): `cp-01`→.201 (API-VIP), `worker-01`→.202,
`worker-02`→.203. De OS-hostnames van de nodes zijn cp-01…cp-03 / node-01…node-03.
De orchestrator draait op de laptop en praat via `kubectl` (SA `orchestrator`) met
het cluster; de agents draaien als K8s Jobs op de nodes, binnen de kooi.

## Componenten

- **Orchestrator** — één Claude Code-sessie op de laptop (tmux). Mag: Jobs CRUD'en
  in `agents`, logs streamen, branches inspecteren, Mark aanroepen. Schrijft zelf
  nooit productiecode. (change `add-orchestrator`, nog te doen)
- **Workers** — K8s Jobs, één image (`claude -p` + `uv` + `git`). Rollen
  (builder/reviewer/security) zijn `.claude/agents/`-files in de **doelrepo**, niet
  in Habitat. (change `add-worker-image`, propose)
- **Kooi** — namespace `agents`: default-deny egress + Cilium `toFQDNs`-allowlist,
  minimale RBAC, SOPS+age-secrets. (change `add-cage`, **live toegepast + getest**)

## De kooi (isolatie) — zoals gebouwd en getest

- **Netwerk**: namespace-brede default-deny egress (k8s NetworkPolicy) +
  `CiliumNetworkPolicy` met `toFQDNs`. Een worker (label `habitat/component=worker`)
  mag alleen DNS + HTTPS naar `*.anthropic.com`, `*.github(usercontent).com`,
  pypi/pythonhosted en npmjs. Al het andere dropt de CNI. Geen egress-proxy nodig:
  Cilium filtert native op domeinnaam. Egress-audit uit **Hubble**.
- **RBAC**: rol-SA's hebben geen API-token en nul rechten (een worker praat nooit
  met de API). De orchestrator-SA mag alleen Jobs CRUD + logs lezen in `agents`.
- **Secrets**: SOPS+age, één cluster-age-key (privé alleen op de orchestrator-host),
  decrypt-at-apply. Per-node PAT-secrets → node per stuk intrekbaar.

Bewijs (2026-07-05): `github.com`→200, `api.anthropic.com`→404 (toegestaan),
`example.com`→time-out/curl-28 (gedropt); orchestrator-SA kan geen secrets/andere
namespaces/cluster-resources.

## Levensloop van één run

```
goedgekeurde change + rol   →  orchestrator dispatcht Job  →  worker in de kooi:
                                                               clone (PAT/HTTPS)
                                                               claude -p (rol)
                                                               push branch + run-report.json
  ←  orchestrator escaleert merge naar Mark (met HTML-rapport)  ←  reviewer- + security-Job
```

Merges naar `main` doet **altijd Mark** (v0). Alles reconstrueerbaar uit git +
hash-chained audit-JSONL.

## Escalatiematrix

- **Autonoom**: builder-run per goedgekeurde change; tests; reviewer + security;
  max 2 herstelrondes na rood; Jobs herstarten; logs archiveren.
- **Escaleren** (pauzeer, wacht op Mark, link rapport): elke merge naar `main`; elke
  security-finding; elke nieuwe dependency; spec-afwijking; >2 mislukte
  herstelrondes; kostendrempel per change overschreden.
- **Verboden, hard-fail, nooit escaleerbaar**: wijziging aan `CLAUDE.md`,
  `.claude/agents/`, NetworkPolicies, RBAC of Job-templates. Dubbel afgedwongen:
  reviewer faalt hard + GitHub branch protection/CODEOWNERS.

## Rollback (drie lagen, allemaal saai)

1. **Code** — agents werken alleen op branches; `main` beschermd; Mark merget.
   Rollback = `git revert` of branch weggooien.
2. **Cluster** — Jobs zijn wegwerp; images immutable + per SHA getagd, nooit
   `latest`; `kubectl delete job` (of `delete ns agents`) laat niets achter.
3. **Data** — afnemer-verantwoordelijkheid (wordsworth regelt eigen idempotentie);
   Habitat garandeert alleen dat runs geen state buiten Job en branch achterlaten.

## Status & vervolgstappen

| Change | Wat | Status |
|---|---|---|
| `add-cage` | namespace, egress-policy (Cilium toFQDNs), RBAC, SOPS-structuur | **live toegepast + getest** |
| `add-worker-image` | Containerfile + entrypoint + GHCR-build | propose (klaar voor implementatie) |
| `add-dispatch` | Job-template (`activeDeadlineSeconds`, `backoffLimit:0`) + dispatch-script | nog te schrijven |
| `add-orchestrator` | orchestrator-`CLAUDE.md` (mandaat + escalatiematrix) + tmux-indeling | nog te schrijven |
| `add-audit-report` | hash-chained JSONL + single-file HTML-run-rapport | nog te schrijven |

**Openstaand beslispunt**: nu er geen egress-proxy meer is, is git-auth via een
SSH-deploy-key (de oorspronkelijke keuze) weer mogelijk naast de PAT-over-HTTPS die
nu gekozen is. Zie de repo-README en `openspec/changes/add-worker-image/`.

**Definition of done (v0)**: orchestrator dispatcht een builder-Job voor een triviale
change in een testrepo → log streamt in tmux → reviewer + security volgen →
orchestrator escaleert de merge naar Mark, mét HTML-run-rapport. Eén volledige loop.

De volledige, formele specificatie staat per change onder
[`openspec/changes/`](../../openspec/changes/).
