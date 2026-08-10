# Tasks: reproducible-diff-hash

## 1. Report

- [ ] 1.1 `report/habitat_report.py`: diff + `--stat` sluiten `.habitat/` en
      `run-report.json` uit (pathspec-exclusie); `diff_hash`-waarde ongewijzigd,
      nu reproduceerbaar vanaf de branch.
- [ ] 1.2 `run-report.json` krijgt `diff_hash_scope` (reproductie-commando),
      buiten de gehashte auditvelden.
- [ ] 1.3 `report/test_habitat_report.py`: reproduceerbaarheid vanaf de branch +
      controle dat de kale diff wél zou afwijken.

## 2. Spec

- [ ] 2.1 Spec-delta `audit-trail`: `diff_hash` dekt de agent-code exclusief
      habitat-artefacten en is reproduceerbaar vanaf de gepushte branch.

## 3. Verify

- [ ] 3.1 `python3 report/test_habitat_report.py` groen; shellcheck n.v.t.
      (python), py-syntax ok.
- [ ] 3.2 Code-review reviewer + security in verse context; bevindingen verwerkt.
- [ ] 3.3 Nieuwe image; cluster-sanity: een run → `run-report.json` heeft
      `diff_hash_scope`, en `git diff <base> HEAD` mét exclusies op de branch
      reproduceert de opgeslagen `diff_hash`. Daarna afvinken/archiveren.
