# Change: move-run-artifacts-out-of-git

## Why

Elke run commit nu zijn eigen artefacten mee de doelrepo in:
`.habitat/audit.jsonl`, `.habitat/run-report-<id>.html`,
`.habitat/run-output-<id>.md` en `run-report.json`. Bij een merge van de
run-branch landen die op `main`. Stand vandaag: handbook 4 bestanden, wordsworth
4, boomhuis 4, internetnl-cli 0 (daar zijn ze achteraf met de hand naar habitat
gearchiveerd en verwijderd — twee praktijken naast elkaar).

Besluit Mark (2026-09-06): **runs en output horen niet in git.** Lokaal bewaren
mag, met een maximum van veertien dagen.

## What changes

- **`report/habitat_report.py`**: `--artifact-dir` (waar de artefacten heen gaan;
  default blijft `<repo-dir>/.habitat` voor compat) en `--emit-stdout` (print elk
  artefact als `<naam> <base64>` tussen twee markers).
- **`worker/entrypoint.sh`**: schrijft naar `/work/artifacts` — buiten de working
  tree, dus `git add -A` ziet ze niet en de push bevat alleen de agent-wijziging.
- **`dispatch/dispatch.sh`**: knipt de artefacten uit het gearchiveerde Job-log
  naar `$HABITAT_LOGDIR/artifacts/<repo>/<run_id>/` en ruimt artefacten én logs
  ouder dan veertien dagen op.

## Waarom via het log en niet `kubectl cp`

De pod is weg zodra de Job's TTL verloopt, en `kubectl cp` breekt met een remote
`KUBECTL="ssh <host> kubectl"` (zelfde herparse-probleem als in #17). Het log is
het enige kanaal dat in beide gevallen werkt. Base64 zodat newlines, HTML en
quotes de logstroom niet kunnen breken.

## Bekende consequentie (bewust)

De hashketen in `audit.jsonl` had zijn voorganger uit de gekloonde branch. Zonder
git-artefacten begint elke run een eigen keten (`prev_hash` leeg) en is de
**lokale bewaarplek van de operator de doorlopende ledger**, niet de repo. Het
HTML-rapport verifieert daardoor nog steeds zijn eigen entry, maar niet meer de
keten van eerdere runs in diezelfde repo.

Alternatief was de ketenkop als env-var doorgeven — dat vergt een wijziging aan
`dispatch/job-template.yaml`, en Job-templates zijn voor agents een verboden pad
(`CLAUDE.md`). Operator-side ketening is een eigen change waard als de doorlopende
keten terug moet.

## Impact

- Oudere worker-images zonder markers: `dispatch.sh` vindt niets en gaat door —
  geen fout, wel geen artefacten.
- Nieuwe image-tag nodig; dispatchers verzetten `WORKER_IMAGE`.
- De al gecommitte artefacten in handbook, wordsworth en boomhuis worden in aparte
  commits in die repo's verwijderd (`.gitignore` erbij), niet hier.
