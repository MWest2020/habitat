## MODIFIED Requirements

### Requirement: Append-only hash-chained audit-log

Elke run SHALL één regel toevoegen aan `.habitat/audit.jsonl` met minimaal: rol,
change, run-id, verdict, kosten, aantal turns, diff-hash, timestamp, `prev_hash` en
`entry_hash`. `entry_hash` SHALL `sha256` zijn van `prev_hash` samengevoegd met de
runvelden, zodat elke wijziging aan een eerdere regel de keten breekt. Het
rapport-script SHALL een onparseerbare (bv. door de agent beschadigde) laatste
regel **fail-closed** behandelen: het SHALL niet crashen en `prev_hash` leeg laten,
zodat de keten zichtbaar breekt in de verificatie in plaats van de run af te breken.
Onleesbare of niet-object regels SHALL in het HTML-rapport als een expliciet
gebroken rij worden getoond en NIET stil worden weggelaten, zodat een agent de
keten niet kan "opschonen" door alle eerdere regels te bederven.

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

#### Scenario: Beschadigde audit-regel is fail-closed

- **WHEN** de laatste regel van een bestaande `.habitat/audit.jsonl` onparseerbaar
  is (door een agent beschadigd)
- **THEN** crasht het rapport-script niet en wordt de nieuwe regel met een lege
  `prev_hash` geschreven
- **AND** breekt de keten daardoor zichtbaar in de verificatie (fail-closed)

#### Scenario: Onleesbare regels blijven zichtbaar

- **WHEN** een agent alle eerdere regels van `.habitat/audit.jsonl` bederft
- **THEN** toont het HTML-rapport elke onleesbare regel als een expliciet gebroken
  rij (niet stil weggelaten), zodat de nieuwe entry niet als enige valide root
  overblijft
