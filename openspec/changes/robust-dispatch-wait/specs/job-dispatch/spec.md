## MODIFIED Requirements

### Requirement: Uitkomst afleesbaar uit Job-status

Het dispatch-script SHALL de logs streamen en de uitkomst uit
`Job.status.conditions` bepalen — `Complete` versus `Failed` (met `reason`) — en niet
uit de pod-exit-code.

Het dispatch-script SHALL wachten op een **terminale** Job-conditie
(`Complete` of `Failed`) met een timeout die ruim de Job-deadline
(`ACTIVE_DEADLINE_SECONDS`) plus scheduling- en (cold) image-pull-tijd dekt,
zodat een trage pull of een lange run niet ten onrechte als onbekend eindigt.
Alleen wanneer binnen die timeout géén terminale conditie verschijnt SHALL
dispatch een niet-nul "geen uitkomst"-status (exit 2) melden.

#### Scenario: Afgeronde run

- **WHEN** de worker klaar is en de Job `Complete` is
- **THEN** rapporteert dispatch afgerond en is `run-report.json` op de branch te lezen

#### Scenario: Onderscheid time-out van andere fout

- **WHEN** de Job `Failed` is
- **THEN** onderscheidt dispatch `reason: DeadlineExceeded` (time-out) van een andere
  faalreden

#### Scenario: Trage image-pull eindigt niet als onbekend

- **WHEN** de pod pas na een cold image-pull gaat draaien, ná het oude korte
  wachtvenster
- **THEN** blijft dispatch wachten tot de Job een terminale conditie heeft
- **AND** rapporteert het de echte uitkomst (`Complete`/`Failed`), niet "onbekend"
