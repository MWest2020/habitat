# Tasks: fix-guard-role-definition

## 1. Guard-fix

- [ ] 1.1 `worker/hooks/pretooluse-guard.sh`: `Read` krijgt een uitzondering voor
      `(^|/)\.claude/agents/[^/]+\.md$` vóór de secret-check; `Edit`/`Write`/
      `NotebookEdit` blijven ongewijzigd geweigerd op `.claude/`. Faalt-dicht
      gedrag en alle overige denies (push, .env, .pem, id_rsa, .credentials.json,
      /var/run/claude/, /proc/, /sys/, /secrets/) blijven intact.

## 2. Test

- [ ] 2.1 `worker/hooks/test-pretooluse-guard.sh`: allow = lezen van
      `.claude/agents/<rol>.md` en een gewoon repobestand; deny = credentials,
      `.claude/settings.json`, schrijven naar `.claude/agents/`, `git push`,
      en secret-paden in een Bash-commando. `shellcheck` schoon.

## 3. Verify

- [x] 3.1 `bash worker/hooks/test-pretooluse-guard.sh` groen (27 gevallen);
      `shellcheck` op beide scripts schoon.
- [x] 3.2 Code-review door reviewer + security in verse context; bevindingen
      verwerkt. _Ronde 1: reviewer PASS, security FAIL (B1 symlink-bypass).
      Ronde 2 na fix (component-walk `[ -L ]` + newline-hardening): beide PASS.
      Gemerged als PR #13 (232583a). Follow-ups genoteerd: Glob/Grep, hardlinks,
      interpreter-exfil._
- [x] 3.3 Nieuwe worker-image gebouwd (CI op `worker/**`, 232583a); cluster-
      livetests van add-role-architecture (3.1–3.3) hervat en groen.
      _2026-08-10: architect gaf vóór de fix FAIL (rol-definitie onleesbaar), ná
      de fix verdict=ok. Volledige keten groen; zie add-role-architecture 3.1–3.3._
