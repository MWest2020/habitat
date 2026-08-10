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

- [ ] 3.1 `bash worker/hooks/test-pretooluse-guard.sh` groen; `shellcheck`
      op beide scripts schoon.
- [ ] 3.2 Code-review door reviewer + security in verse context; bevindingen
      verwerkt.
- [ ] 3.3 Nieuwe worker-image gebouwd (CI op `worker/**`); cluster-livetests
      van add-role-architecture (3.1–3.3) hervat en groen; daarna beide changes
      afvinken/archiveren.
