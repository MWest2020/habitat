# Tasks: add-role-architecture

## 0. Besluit

- [ ] 0.1 Mark bevestigt de northstars en de rol-matrix (proposal.md).

## 1. Per-rol enforcement in de worker

- [ ] 1.1 `worker/settings/<rol>.json` (architect, builder, reviewer,
      security): `permissions.allow`/`deny` per rol conform research.md
      B1–B4; niet-builder-rollen zonder Edit/Write/Bash (diff via stdin).
- [ ] 1.2 `worker/entrypoint.sh`: `claude --bare -p` +
      `--permission-mode dontAsk` + `--settings` per rol i.p.v.
      `bypassPermissions`; `--output-format json --json-schema` per rol
      (schema's in `worker/schemas/<rol>.json`).
- [ ] 1.3 Hooks: Stop-hook die de repo-verify draait (builder), 
      PreToolUse-deny op secrets-paden en `git push` (alle rollen).
- [ ] 1.4 `dispatch/dispatch.sh`: rol `architect` toevoegen aan de
      validatie; verdict-parsing uit de json-output (PASS/FAIL machinaal).

## 2. Roldefinities en skills (sjablonen)

- [ ] 2.1 Sjablonen `.claude/agents/{architect,builder,reviewer,security}.md`
      met frontmatter (`tools`, `disallowedTools`, `model`,
      `permissionMode`) die de worker-settings spiegelt.
- [ ] 2.2 Skills: `plan-format` (architect), `review-checklist`
      (reviewer), gecustomizede `security-review` (op basis van
      anthropics/claude-code-security-review), `verify` (builder);
      side-effect-skills met `disable-model-invocation: true`.

## 3. Verify

- [ ] 3.1 Livetest per rol op habitat-testrepo: architect levert
      schema-valide plan zonder writes; reviewer/security kunnen
      aantoonbaar níét schrijven (writes geweigerd in de log); builder
      wordt door de Stop-hook geblokkeerd bij falende verify.
- [ ] 3.2 Idempotentie-smoke: zelfde change tweemaal gedraaid →
      inhoudelijk gelijke uitkomst (diff_hash vergelijken).
- [ ] 3.3 End-to-end op een echte spoke-change: architect → builder →
      reviewer → security, verdicts sturen de keten.
- [ ] 3.4 Docs bijwerken (docs/reference/dispatch.md, agents-sjabloon),
      `openspec validate add-role-architecture`, archiveren.
