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
- [ ] 3.2 `docs/reference/dispatch.md`: bewaarplek, retentie en de log-route.

## 4. Gate

- [ ] 4.1 `openspec validate move-run-artifacts-out-of-git --strict` groen.
- [ ] 4.2 CI groen (verify + docs-gates).
- [ ] 4.3 Na merge: image gebouwd, nieuwe tag genoteerd.
- [ ] 4.4 Opruimen in de doelrepo's (handbook 4, wordsworth 4, boomhuis 4) + `.gitignore`.
