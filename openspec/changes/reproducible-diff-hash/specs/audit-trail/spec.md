## MODIFIED Requirements

### Requirement: Diff-hash bindt de audit aan de code

De audit-regel SHALL een `diff_hash` bevatten = sha256 van de
agent-codewijziging t.o.v. de basis, zodat de log aan de concrete
codeverandering vastzit. De `diff_hash` SHALL de habitat-artefacten uitsluiten
(`.habitat/` en `run-report.json`), zodat hij **reproduceerbaar** is vanaf de
gepushte branch — die die artefacten wél bevat. `run-report.json` SHALL het
reproductie-bereik documenteren (`diff_hash_scope`).

#### Scenario: Diff-hash aanwezig

- **WHEN** de agent bestanden wijzigt
- **THEN** bevat de audit-regel de sha256 van die codewijziging, met de
  habitat-artefacten uitgesloten

#### Scenario: Reproduceerbaar vanaf de branch

- **WHEN** een auditor `git diff <base-ref> HEAD` op de gepushte branch draait
  met `.habitat/` en `run-report.json` uitgesloten
- **THEN** komt de herberekende sha256 exact overeen met de opgeslagen `diff_hash`
- **AND** verstoren de meegecommitte habitat-artefacten die hash niet
