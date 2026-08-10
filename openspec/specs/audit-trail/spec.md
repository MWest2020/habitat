# audit-trail Specification

## Purpose
TBD - created by archiving change add-audit-report. Update Purpose after archive.
## Requirements
### Requirement: Append-only hash-chained audit-log

Elke run SHALL één regel toevoegen aan `.habitat/audit.jsonl` met minimaal: rol,
change, run-id, verdict, kosten, aantal turns, diff-hash, timestamp, `prev_hash` en
`entry_hash`. `entry_hash` SHALL `sha256` zijn van `prev_hash` samengevoegd met de
runvelden, zodat elke wijziging aan een eerdere regel de keten breekt.

#### Scenario: Eerste run

- **WHEN** er nog geen `.habitat/audit.jsonl` bestaat
- **THEN** ontstaat het bestand met één regel waarvan `prev_hash` leeg is
- **AND** `entry_hash` is de sha256 van de payload

#### Scenario: Volgende run keten

- **WHEN** er al regels bestaan
- **THEN** verwijst `prev_hash` van de nieuwe regel naar de `entry_hash` van de vorige

#### Scenario: Manipulatie detecteerbaar

- **WHEN** een eerdere regel wordt gewijzigd
- **THEN** klopt de herberekende `entry_hash` van die of een latere regel niet meer

### Requirement: Diff-hash bindt de audit aan de code

De audit-regel SHALL een `diff_hash` bevatten = sha256 van de
agent-codewijziging t.o.v. de basis, zodat de log aan de concrete
codeverandering vastzit. De `diff_hash` SHALL **exact de door habitat
gegenereerde artefacten van de run** uitsluiten — op vaste naam plus de
dispatch-bepaalde run-id, zónder wildcards (`literal`-pathspec):
`.habitat/audit.jsonl`, `.habitat/run-report-<run-id>.html`,
`.habitat/run-output-<run-id>.md`, `run-report.json`. Hij SHALL NIET de hele
`.habitat/`-map noch een naam-wildcard uitsluiten, zodat hij **reproduceerbaar**
is vanaf de gepushte branch — die die artefacten wél bevat — zónder een
smokkelkanaal te openen: elk ander bestand dat de agent onder `.habitat/`
schrijft (code als `.habitat/evil.py`, of een als artefact vermomde
`.habitat/run-report-<willekeurig>.html`) SHALL binnen de `diff_hash` blijven.
`run-report.json` SHALL het reproductie-bereik documenteren (`diff_hash_scope`,
met de concrete run-id).

#### Scenario: Diff-hash aanwezig

- **WHEN** de agent bestanden wijzigt
- **THEN** bevat de audit-regel de sha256 van die codewijziging, met de
  habitat-artefacten uitgesloten

#### Scenario: Reproduceerbaar vanaf de branch

- **WHEN** een auditor `git diff <base-ref> HEAD` op de gepushte branch draait
  met exact de run-artefacten uitgesloten (`.habitat/audit.jsonl`,
  `.habitat/run-report-<run-id>.html`, `.habitat/run-output-<run-id>.md`,
  `run-report.json`)
- **THEN** komt de herberekende sha256 exact overeen met de opgeslagen `diff_hash`
- **AND** verstoren de meegecommitte habitat-artefacten die hash niet

#### Scenario: Geen smokkelkanaal via .habitat/

- **WHEN** een agent zelf een bestand schrijft onder `.habitat/` dat geen
  artefact van deze run is — code (`.habitat/evil.py`) of een als artefact
  vermomde naam (`.habitat/run-report-evil.html`, genest, enz.)
- **THEN** telt dat bestand mee in de `diff_hash` (het valt buiten de exacte
  run-id-exclusie), zodat de audit de volledige codewijziging blijft binden

