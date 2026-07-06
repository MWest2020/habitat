## ADDED Requirements

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

De audit-regel SHALL een `diff_hash` bevatten = sha256 van de gestagede
agent-wijziging, zodat de log aan de concrete codeverandering vastzit.

#### Scenario: Diff-hash aanwezig

- **WHEN** de agent bestanden wijzigt
- **THEN** bevat de audit-regel de sha256 van die diff, berekend vóór de
  rapport-bestanden worden geschreven
