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

- [ ] 3.1 Livetest per rol op habitat-testrepo: architect levert
      schema-valide plan zonder writes; reviewer/security kunnen
      aantoonbaar níét schrijven (writes geweigerd in de log); builder
      wordt door de Stop-hook geblokkeerd bij falende verify.
      _Deels lokaal bewezen (2026-07-29, buiten K8s): reviewer-settings
      weigerden Write/Edit/Bash aantoonbaar (geen bestand aangemaakt,
      verdict FAIL in schema-output); architect leverde schema-valide
      plan met schone boom, verdict PASS. Rest vergt het cluster._
      _Afwijking: `--bare` weggelaten — slaat de subscription-login over
      (lokaal bewezen); zie entrypoint-commentaar._
- [ ] 3.2 Idempotentie-smoke: zelfde change tweemaal gedraaid →
      inhoudelijk gelijke uitkomst (diff_hash vergelijken).
- [ ] 3.3 End-to-end op een echte spoke-change: architect → builder →
      reviewer → security, verdicts sturen de keten.
- [ ] 3.4 Docs bijwerken (docs/reference/dispatch.md, agents-sjabloon),
      `openspec validate add-role-architecture`, archiveren.
