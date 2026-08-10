# Tasks: add-role-architecture

## 0. Besluit

- [x] 0.1 Mark bevestigt de northstars en de rol-matrix (proposal.md).

## 1. Per-rol enforcement in de worker

- [x] 1.1 `worker/settings/<rol>.json` (architect, builder, reviewer,
      security): `permissions.allow`/`deny` per rol conform research.md
      B1–B4; niet-builder-rollen zonder Edit/Write/Bash (diff via stdin).
- [x] 1.2 `worker/entrypoint.sh`: `claude -p` + `--permission-mode dontAsk`
      + `--settings` per rol + `--setting-sources user` + `env -u GIT_PAT`
      i.p.v. `bypassPermissions`; `--output-format json --json-schema` per
      rol (schema's in `worker/schemas/<rol>.json`). GEEN `--bare` — dat
      slaat de subscription-login over (sub-first); zie research-afwijking.
- [x] 1.3 Hooks: PreToolUse-guard (deny op `git push`, secrets- én
      credential-paden, faalt dicht) bij ALLE vier de rollen; Stop-hook die
      de repo-verify draait (alleen builder), uit de basiscommit en met
      timeout + loop-guard.
- [x] 1.4 `dispatch/dispatch.sh`: rol `architect` toegevoegd aan de
      validatie. Verdict-propagatie: de entrypoint zet VERDICT=failed bij
      rol-verdict FAIL (fail-closed) → Job Failed → keten stopt; dispatch
      leest die uitkomst uit Job.status.conditions. (Onderscheid
      rol-FAIL vs. infra-crash in dispatch = follow-up, niet blokkerend.)

## 2. Roldefinities en skills (sjablonen)

- [x] 2.1 Sjablonen `.claude/agents/{architect,builder,reviewer,security}.md`
      met frontmatter (`tools`, `disallowedTools`, `model`,
      `permissionMode`) die de worker-settings spiegelt.
- [x] 2.2 Skills: `plan-format` (architect), `review-checklist`
      (reviewer), gecustomizede `security-review` (op basis van
      anthropics/claude-code-security-review), `verify` (builder). Geen
      skill kwalificeert als side-effect-skill (alle vier zijn
      read-only/advies), dus `disable-model-invocation` is nergens gezet.

## 3. Verify

> Code-review: PR #11 door twee onafhankelijke agents (reviewer + security)
> in verse context, TWEE rondes. Ronde 1 → FAIL (1 blocking + majors);
> ronde 2 na fixes → beide PASS. Gemerged op main (14351b8). De
> cluster-livetests hieronder vereisen `kubectl` en draaien op een
> orchestrator-host (niet vanaf de dev-machine waar de code gebouwd is).

**Dispatch-commando's voor de cluster-livetests** (vanaf een host met
kubectl; `WORKER_IMAGE` = image gebouwd van commit ≥ 14351b8):

```
# 3.1 per rol op de testrepo
WORKER_IMAGE=ghcr.io/mwest2020/habitat-worker:<sha> dispatch/dispatch.sh architect <change> MWest2020/habitat-testrepo
WORKER_IMAGE=… dispatch/dispatch.sh builder  <change> MWest2020/habitat-testrepo
HABITAT_BASE_BRANCH=habitat/builder/<change> WORKER_IMAGE=… dispatch/dispatch.sh reviewer <change> MWest2020/habitat-testrepo
HABITAT_BASE_BRANCH=habitat/builder/<change> WORKER_IMAGE=… dispatch/dispatch.sh security <change> MWest2020/habitat-testrepo
```
Verwacht: architect → schone boom + plan in output; reviewer/security →
Write/Edit geweigerd in de pod-log; builder met falende `scripts/verify.sh`
→ Stop-hook blokkeert, Job Failed.

- [x] 3.1 Livetest per rol op habitat-testrepo: architect levert
      schema-valide plan zonder writes; reviewer/security kunnen
      aantoonbaar níét schrijven; builder wordt door de Stop-hook
      geblokkeerd bij falende verify.
      _Cluster-livetest 2026-08-10 (image 232583a, na fix-guard-role-definition):
      architect verdict=ok met diff_hash=leeg (nul writes); reviewer én security
      verdict=ok met diff_hash=leeg (nul writes → read-only afgedwongen); builder
      verdict=ok met Stop-hook-verify geslaagd (GREETING.md). Stop-hook-blokkade
      dubbel bewezen: gecontroleerd cluster-experiment (identieke builder → main
      Complete, test/failing-verify Failed) + geïsoleerde stop-verify.sh (exit 2
      op falende verify, exit 0 op geslaagde). Deploy-fix: cage/rbac.yaml
      toegepast — de role-architect-SA ontbrak op het cluster._
      _Afwijking: `--bare` weggelaten — slaat de subscription-login over._
- [x] 3.2 Idempotentie-smoke: zelfde change tweemaal gedraaid →
      inhoudelijk gelijke uitkomst (diff_hash vergelijken).
      _2026-08-10: builder add-greeting run-a en run-b → identieke diff_hash
      (e8fea2b0…)._
- [x] 3.3 End-to-end op een echte spoke-change: architect → builder →
      reviewer → security, verdicts sturen de keten.
      _2026-08-10: volledige keten op habitat-testrepo/add-greeting gedraaid
      (alle vier PASS); verdict-propagatie bewezen (rol-verdict FAIL →
      VERDICT=failed → Job Failed) bij o.a. de failing-verify-run._
- [x] 3.4 Docs bijwerken (docs/reference/dispatch.md, agents-sjabloon),
      `openspec validate add-role-architecture`, archiveren.
      _Runbook cluster-livetests toegevoegd aan docs/reference/dispatch.md;
      guard-uitzondering gedocumenteerd in docs/reference/roles.md._
