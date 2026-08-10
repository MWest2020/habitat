# Change: add-role-architecture

> Vier rollen (architect · builder · reviewer · security) met per rol
> expliciete skills en een minimale, afgedwongen tool-allowlist
> (deny-by-default), zodat het bouwproces idempotent en voorspelbaar is.
> Onderbouwing: `research.md` (webresearch naar officiële
> Anthropic-aanbevelingen, 2026-07-29).

## Northstars (besluit Mark, 2026-07-29)

1. **Alles wat gebouwd wordt, gaat via habitat.** Geen hand-edits op
   spokes; git is het overdrachtsmedium, het run-report het bewijs.
2. **Vier rollen, minimale bevoegdheden.** Architect ontwerpt (read-only +
   plan-output), builder implementeert binnen het plan, reviewer en
   security lezen en oordelen. Wat niet op de allowlist staat, kan niet.
3. **Idempotent en saai.** Zelfde change + zelfde input → zelfde uitkomst;
   gepinde images, budget-/deadline-caps, geen netwerk buiten het nodige.
   Verrassingen zijn per definitie een bug.
4. **Verdicten sturen het proces.** Een rol-verdict is een gate, geen
   rapport: PASS → volgende stap, FAIL → stop, mens erbij.

## Why

De worker draait nu élke rol met `--permission-mode bypassPermissions`:
reviewer en security hebben feitelijk volledige schrijfrechten en de
roldefinities (`.claude/agents/<rol>.md` in de doelrepo) zijn alleen
advisory prompt-tekst. Anthropic's eigen lijn is het omgekeerde:
onderzoeks-/planrollen zijn strikt read-only ("Write and Edit are
denied"), permissions zijn deny-by-default afdwingbaar (`dontAsk`), hooks
zijn "deterministic" waar prompts "advisory" zijn, en `--bare` bestaat
juist voor "the same result on every machine" (zie research.md, sectie A).

## What Changes

- **Architect-rol** naast builder/reviewer/security: read-only
  (Read/Grep/Glob), levert een plan als gestructureerde output
  (`--json-schema`) met per builder-taak doel, formaat, grenzen en
  verificatiecriteria.
- **Worker-hardening** (`worker/entrypoint.sh`): `claude -p` met
  `--permission-mode dontAsk`, `--setting-sources user`, `env -u GIT_PAT`
  en een per-rol settings-JSON
  (`worker/settings/<rol>.json`) i.p.v. `bypassPermissions`:
  - architect/reviewer/security: `Read`, `Grep`, `Glob` (diff via stdin
    waar mogelijk; anders alleen `Bash(git diff *)`, `Bash(git log *)`)
  - builder: + `Edit`, `Write`, scoped `Bash(uv run *)`/test-/build-
    commando's, `Bash(git add *)`, `Bash(git commit *)`; **deny**
    `Bash(git push *)` (push blijft van de entrypoint), `Read(./.env)`,
    secrets-paden
  - alle rollen: `--output-format json` + rol-specifiek `--json-schema`
- **Deterministische gates:** Stop-hook draait de repo-verify
  (tests/dry-run) vóór een builder-run mag eindigen; PreToolUse-hook
  blokkeert secrets-paden en push. Container (non-root, Cilium-egress)
  blijft de buitenste isolatiegrens — permissions zijn laag twee, niet de
  enige verdediging (bekende deny-rule-bug, research.md E).
- **Skills per rol** (template in habitat, uitgerold naar doelrepo's):
  `plan-format` (architect), `review-checklist` (reviewer, "gaps, not
  style"), gecustomizede `security-review` op basis van Anthropics eigen
  command (security), `verify` (builder). Side-effect-skills krijgen
  `disable-model-invocation: true`.
- **Verdict-gates in dispatch/orchestrator:** reviewer/security-verdict
  bepaalt machinaal of de volgende stap mag (PASS/FAIL uit de
  json-output i.p.v. vrije tekst).
- Roldefinities blijven in de doelrepo (`.claude/agents/<rol>.md`), maar
  krijgen frontmatter met `tools`/`disallowedTools` die de worker-settings
  spiegelt; habitat levert het sjabloon.

## Capabilities

### New Capabilities

- `role-architecture`: vier rollen met afgedwongen minimale toolsets,
  gestructureerde output en verdict-gates.

### Modified Capabilities

- `job-dispatch`: accepteert rol `architect`; geeft per rol de juiste
  settings/flags door aan de worker.

## Impact

- `worker/entrypoint.sh`, `worker/settings/*.json` (nieuw),
  `dispatch/dispatch.sh` (rol-validatie), sjablonen voor
  `.claude/agents/*` en skills richting doelrepo's, docs.
- Bestaande runs blijven werken tot de omschakeling; de wijziging is per
  rol te testen op habitat-testrepo vóór uitrol.
- Buiten scope (aparte changes): auto-merge-gates op PR-niveau
  (confidence-score), eval-set per rol (~20 taken, end-state-evaluatie) —
  geland in de roadmap-notitie van research.md C5.
