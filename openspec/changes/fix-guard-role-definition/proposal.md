# fix-guard-role-definition

## Why

De PreToolUse-guard (`worker/hooks/pretooluse-guard.sh`, tweede
verdedigingslaag uit add-role-architecture) weigert élk pad dat `/.claude/`
bevat, om credential-locaties af te schermen. Maar de worker draagt élke rol
juist op om **`.claude/agents/<rol>.md` van de dóelrepo** te lezen
(`worker/entrypoint.sh`: "rollen leven in `.claude/agents/` van de DÓELREPO" +
de prompt "Volg `.claude/agents/${ROLE}.md`"). De guard blokkeert dus de
rol-definitie die de worker zelf verplicht stelt — een interne tegenspraak.

Gevonden in de cluster-livetest van add-role-architecture (2026-08-10): de
architect gaf verdict FAIL met als reden dat `.claude/agents/architect.md`
onleesbaar is en hij de hook bewust niet omzeilde via `cat`. Correct gedrag van
de agent, maar de keten kan zo geen enkele rol z'n eigen instructie laten lezen.

## What Changes

- `worker/hooks/pretooluse-guard.sh`: voor **`Read`** een smalle uitzondering —
  paden die matchen op `(^|/)\.claude/agents/[^/]+\.md$` worden toegestaan,
  vóór de secret-check. Alle credential-/secret-paden blijven geweigerd
  (`.credentials.json`, `/var/run/claude/`, `/secrets/`, `.env`, `*.pem`,
  `id_rsa`, `/proc/`, `/sys/`), en `Edit`/`Write`/`NotebookEdit` op `.claude/`
  blijven volledig dicht (de uitzondering is alléén lezen).
- `worker/hooks/test-pretooluse-guard.sh`: nieuwe unittest die allow/deny per
  geval vastlegt (rol-definitie lezen = allow; credentials/settings/schrijven =
  deny; `git push` en secret-paden in Bash = deny).

## Impact

- Geen contractbreuk in de afscherming: credentials blijven onbereikbaar; alleen
  het lezen van `.claude/agents/*.md` wordt mogelijk — precies wat de worker al
  verlangt. Vereist een **nieuwe worker-image** (wijziging onder `worker/**` →
  CI tagt per commit-SHA); daarna de `WORKER_IMAGE`-pin bij de volgende dispatch
  bijwerken.
- Deblokkeert de cluster-livetests van add-role-architecture (3.1–3.3).

## Overwogen risico (voor review)

De uitzondering matcht op **padpatroon**, niet op bestandstype. Een spoke die
een symlink `.claude/agents/x.md` → een credential-bestand commit, zou zo een
credential kunnen laten lezen. Beperkingen: alleen lezen, alleen op vertrouwde
eigen spokes, en de agent zou de inhoud daarna nog moeten lekken (secret-scan
vóór push vangt commits). Hardening-optie als de security-rol dat eist: in de
guard een `[ ! -L "$fp" ]`-check toevoegen (afgewogen tegen fail-closed-gedrag
bij een relatief pad met afwijkende cwd).
