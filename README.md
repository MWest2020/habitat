# Habitat

Een minimaal platform waarop Claude Code-agents autonoom aan repositories werken
binnen expliciete, niet-onderhandelbare grenzen — op een thuiscluster (3× K8s-node,
VPN-/overlaynetwerk). Habitat weet níets van domeinlogica; het levert vijf dingen:

**werkverdeling · executie · isolatie · escalatie · audit**

Eerste afnemer wordt *wordsworth* (documentpijplijn, aparte repo). Bewust géén
runner-infrastructuur: Git is het overdrachtsmedium, K8s Jobs zijn de executievorm,
één orchestrator-sessie dispatcht.

## Gebruik — de éne ingang

```bash
WORKER_IMAGE=ghcr.io/mwest2020/habitat-worker:<commit-sha> \
  dispatch/dispatch.sh <rol> <change> <owner/repo>
```

Dat is alles. De worker clonet de doelrepo, draait `claude -p` in de opgegeven
rol (builder/reviewer/security — roldefinities leven in de **doelrepo**), en pusht
branch `habitat/<rol>/<change>` met een `run-report.json`. Volledige referentie:
[docs/reference/dispatch.md](docs/reference/dispatch.md).

## Architectuur in het kort

```
  orchestrator-host                       thuiscluster (namespace: agents)
  ┌────────────────────┐                 ┌──────────────────────────────────┐
  │ 1 Claude Code-     │  dispatch.sh /  │  Job: worker (claude -p)          │
  │ sessie, mandaat in │────kubectl─────▶│  default-deny egress + Cilium     │
  │ orchestrator/      │                 │  toFQDNs-allowlist (anthropic,    │
  │ CLAUDE.md          │◀── run-rapport  │  github, pypi, npm) · RBAC min.   │
  └────────────────────┘                 └──────────────┬───────────────────┘
       escaleert → Mark                                 │ push branch + run-report
                                                        ▼
                                              GitHub (doelrepo, main beschermd)
```

- **Isolatie**: namespace-brede default-deny egress + `CiliumNetworkPolicy` met
  domein-allowlist; rol-SA's zonder API-token; secrets via SOPS+age
  (decrypt-at-apply) en per-node PAT's. Egress-audit via Hubble.
- **Audit**: elke run hash-chained JSONL + single-file HTML-run-rapport op de
  branch, naast de code.
- **Escalatie**: merges naar `main`, security-findings en spec-afwijkingen gaan
  altijd via Mark; het volledige mandaat staat in `orchestrator/CLAUDE.md`.

Details en waarom-besluiten: [docs/](docs/index.md), met name
[docs/explanation/architecture.md](docs/explanation/architecture.md).

## Status

v0 is compleet en live bewezen: kooi, worker-image (GHCR, SHA-getagd), dispatch,
audit-rapportage en orchestrator-mandaat draaien; end-to-end runs op een testrepo
en op deze repo zelf zijn groen. Afgeronde changes staan in
[openspec/changes/archive/](openspec/changes/archive/).

## Grenzen

**Verboden, hard-fail, nooit escaleerbaar** — agents verbouwen hun eigen kooi niet:
wijzigingen aan `CLAUDE.md`, `.claude/agents/`, NetworkPolicies, RBAC of
Job-templates. Dubbel afgedwongen (reviewer hard-fail + branch protection/CODEOWNERS).

## Werkwijze

Conversational design → OpenSpec (`propose` → `apply` → `archive`) → implementatie.
Changes staan onder [`openspec/`](openspec/). Zie [`CLAUDE.md`](CLAUDE.md) voor conventies.
Documentatie beweegt mee met gedrag: wie `dispatch/`, `worker/` of `cage/` wijzigt,
werkt [docs/](docs/index.md) in dezelfde change bij (reviewer let hierop).

## Licentie

[EUPL-1.2](LICENSE).
