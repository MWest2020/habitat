## 1. Artefacten buiten de repo

- [x] 1.1 `--artifact-dir` + `--emit-stdout` in `report/habitat_report.py`.
- [x] 1.2 `worker/entrypoint.sh` schrijft naar `/work/artifacts`.
- [x] 1.3 Bewezen: na een run bevat de werkboom alleen de agent-wijziging.

## 2. Operator bewaart

- [x] 2.1 `dispatch/dispatch.sh` knipt de artefacten uit het log naar
      `$HABITAT_LOGDIR/artifacts/<repo>/<run_id>/`.
- [x] 2.2 Retentie 14 dagen op artefacten én logs.
- [x] 2.3 Bewezen: de vier artefacten komen byte-identiek uit het log.

## 3. Spec + docs

- [x] 3.1 Spec-delta `run-report`: niet in de branch, lokaal bij de operator, 14 dagen.
- [x] 3.2 `docs/reference/dispatch.md`: bewaarplek, retentie en de log-route.

## 4. Gate

- [x] 4.1 `openspec validate move-run-artifacts-out-of-git --strict` groen.
- [x] 4.2 CI groen (verify + docs-gates) — PR #21, run `success`.
- [x] 4.3 Image gebouwd, tag `ghcr.io/mwest2020/habitat-worker:2155dda562b452f6a246809dc9aa828ae3f795df`.
      **In productie bewezen** op de eerste run met die tag: de artefacten kwamen
      via het Job-log naar `run-logs/artifacts/habitat-/20260907-191821-20137`
      (4 stuks), en de run meldde `commit: niets gewijzigd` — er ging dus niets
      onder `.habitat/` mee de branch in. Precies wat deze change beoogde.
- [x] 4.4 Opruimen in de doelrepo's + `.gitignore`. Nagemeten op `origin/main`:
      handbook, wordsworth en boomhuis hebben **nul** bestanden onder
      `.habitat/` of `run-report.json`, en alle drie negeren ze in
      `.gitignore` (handbook#13, wordsworth#37, boomhuis#19).
