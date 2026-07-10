## MODIFIED Requirements

### Requirement: Duurzaam run-rapport in de branch

De worker SHALL naast de code een `run-report.json` in de gepushte branch schrijven,
zodat het run-resultaat reconstrueerbaar is los van de vluchtige `kubectl logs`.

`run-report.json` SHALL minimaal bevatten: rol, change, run-id, verdict,
`total_cost_usd`, aantal turns en timestamps.

De worker SHALL daarnaast de inhoudelijke eind-uitvoer van de agent (het
`result`-veld uit het `claude -p`-JSON-eindobject) als markdown bewaren in
`.habitat/run-output-<run_id>.md` en meecommitten op de branch, zodat reviews en
bevindingen reconstrueerbaar blijven nadat de pod is opgeruimd. Dit bestand SHALL ná
de audit/diff-hash-berekening worden geschreven, zodat het de code-diff-hash niet
beïnvloedt. Ontbreekt of faalt het JSON-eindobject, dan SHALL de worker dit bestand
overslaan zonder de run te laten crashen.

#### Scenario: Rapport na een run

- **WHEN** een run eindigt (geslaagd of niet)
- **THEN** bevat de branch een `run-report.json` met het verdict en `total_cost_usd`
- **AND** blijft dat rapport bestaan nadat de Job is opgeruimd

#### Scenario: Agent-uitvoer bewaard

- **WHEN** het `claude -p`-JSON-eindobject een `result`-veld bevat
- **THEN** bevat de branch `.habitat/run-output-<run_id>.md` met die uitvoer
- **AND** blijft de code-diff-hash in de audit gelijk aan die zonder dit bestand

#### Scenario: Gecrashte run zonder parseerbare JSON

- **WHEN** `claude -p` geen parseerbaar JSON-eindobject oplevert
- **THEN** slaat de worker het uitvoer-bestand over
- **AND** eindigt de run zonder extra fout door dit onderdeel
