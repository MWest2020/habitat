# job-dispatch Specification

## Purpose
TBD - created by archiving change add-dispatch. Update Purpose after archive.
## Requirements
### Requirement: Geparametriseerde worker-Job

Een rol-run SHALL als K8s-Job in de namespace `agents` gestart worden vanuit een
geparametriseerd template. De Job SHALL `restartPolicy: Never`, `backoffLimit: 0` en
een `activeDeadlineSeconds` hebben, en het pod-label `habitat/component: worker`
dragen zodat de egress-policy hem selecteert. De Job SHALL de rol-ServiceAccount
gebruiken, de Claude-subscription-credentials read-only mounten (sub-first), en
`GIT_PAT` via `secretKeyRef` krijgen.

#### Scenario: Dispatch van een builder-run

- **WHEN** de orchestrator een builder-run dispatcht voor een change
- **THEN** ontstaat er één Job met `backoffLimit: 0`, de worker-label en de
  rol-SA, die de secrets gemount krijgt

#### Scenario: Geen stille herstart

- **WHEN** de worker-pod faalt
- **THEN** wordt er geen nieuwe pod-poging gestart (één shot per Job)

### Requirement: Harde begrenzing in tijd en kosten

De Job SHALL wall-clock begrensd zijn via `activeDeadlineSeconds` en de worker SHALL
kosten begrenzen via `--max-budget-usd`. Bij overschrijding van de deadline SHALL de
Job actief beëindigd worden.

#### Scenario: Time-out

- **WHEN** een run langer duurt dan `activeDeadlineSeconds`
- **THEN** wordt de pod beëindigd en de Job als `Failed`/`DeadlineExceeded` gemarkeerd

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

