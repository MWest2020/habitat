# Tasks: reproducible-diff-hash

## 1. Report

- [x] 1.1 `report/habitat_report.py`: diff + `--stat` sluiten **exact de
      run-artefacten** uit — op vaste naam + dispatch-run-id, `literal` (geen
      wildcard): `.habitat/audit.jsonl`, `.habitat/run-report-<id>.html`,
      `.habitat/run-output-<id>.md`, `run-report.json`. Niet de hele
      `.habitat/`-map en geen naam-wildcard, zodat agent-code én als-artefact
      vermomde namen onder `.habitat/` in de hash blijven (geen smokkelkanaal).
      `diff_hash`-waarde ongewijzigd voor normale runs, nu reproduceerbaar vanaf
      de branch.
- [x] 1.2 `run-report.json` krijgt `diff_hash_scope` (reproductie-commando),
      buiten de gehashte auditvelden.
- [x] 1.3 `report/test_habitat_report.py`: reproduceerbaarheid vanaf de branch +
      anti-smokkel (agent-`.habitat/evil.py`, vermomde `run-report-evil.html`,
      `run-output-evil.md` én genest tellen mee) + controle dat de grove
      map-exclusie, de naam-wildcard én de kale diff wél zouden afwijken; scope
      bevat de exacte run-id, geen `*`.

## 2. Spec

- [x] 2.1 Spec-delta `audit-trail`: `diff_hash` dekt de agent-code exclusief
      exact de habitat-artefacten, is reproduceerbaar vanaf de gepushte branch en
      opent geen smokkelkanaal via `.habitat/`.

## 3. Verify

- [x] 3.1 `python3 report/test_habitat_report.py` groen; shellcheck n.v.t.
      (python), py-syntax ok.
- [x] 3.2 Code-review reviewer + security in verse context; bevindingen verwerkt.
      Reviewer PASS. Security round 1 FAIL (grove `.habitat/`-exclusie) →
      round 2 FAIL (naam-wildcard `run-report-*.html`/`run-output-*.md` nog
      agent-noembaar, `*` matcht ook `/`) → verholpen met exacte run-id-exclusie
      (`literal`, geen wildcard) + uitgebreide anti-smokkel-test.
- [ ] 3.3 Nieuwe image; cluster-sanity: een run → `run-report.json` heeft
      `diff_hash_scope`, en `git diff <base> HEAD` mét exclusies op de branch
      reproduceert de opgeslagen `diff_hash`. Daarna afvinken/archiveren.
