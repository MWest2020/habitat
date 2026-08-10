## MODIFIED Requirements

### Requirement: Duurzaam run-rapport in de branch

De worker SHALL naast de code een `run-report.json` in de gepushte branch schrijven,
zodat het run-resultaat reconstrueerbaar is los van de vluchtige `kubectl logs`.

`run-report.json` SHALL minimaal bevatten: rol, change, run-id, verdict,
`total_cost_usd`, aantal turns en timestamps.

De worker SHALL daarnaast de inhoudelijke eind-uitvoer van de agent (het
`result`-veld uit het `claude -p`-JSON-eindobject) als markdown bewaren in
`.habitat/run-output-<run_id>.md` en meecommitten op de branch, zodat reviews en
bevindingen reconstrueerbaar blijven nadat de pod is opgeruimd. Dit bestand SHALL
ná de audit/diff-hash-berekening worden geschreven, zodat het de code-diff-hash
niet beïnvloedt. De worker SHALL dit bestand **altijd** schrijven — óók wanneer
het JSON-eindobject ontbreekt of onparseerbaar is — dan met een placeholder in
plaats van de agent-uitvoer. Zo bezit habitat dit artefact-bestand deterministisch
en kan een agent geen eigen `.habitat/run-output-<run_id>.md` op de branch
smokkelen die buiten de diff-hash valt (die is per exacte naam uitgesloten). Het
schrijven SHALL de run niet laten crashen.

#### Scenario: Rapport na een run

- **WHEN** een run eindigt (geslaagd of niet)
- **THEN** bevat de branch een `run-report.json` met het verdict en `total_cost_usd`
- **AND** blijft dat rapport bestaan nadat de Job is opgeruimd

#### Scenario: Agent-uitvoer bewaard

- **WHEN** het `claude -p`-JSON-eindobject een `result`-veld bevat
- **THEN** bevat de branch `.habitat/run-output-<run_id>.md` met die uitvoer
- **AND** blijft de code-diff-hash in de audit gelijk aan die zonder dit bestand

#### Scenario: Gecrashte run zonder parseerbare JSON

- **WHEN** `claude -p` geen parseerbaar JSON-eindobject (of geen `result`) oplevert
- **THEN** bevat de branch tóch `.habitat/run-output-<run_id>.md`, met een
  placeholder in plaats van de agent-uitvoer
- **AND** eindigt de run zonder extra fout door dit onderdeel

#### Scenario: Geen gesmokkelde run-output

- **WHEN** een agent zelf een `.habitat/run-output-<run_id>.md` schrijft vóór het
  rapport
- **THEN** overschrijft habitat dat bestand met de eigen (placeholder- of
  `result`-)inhoud, zodat geen agent-gestuurde inhoud buiten de diff-hash op de
  branch belandt
