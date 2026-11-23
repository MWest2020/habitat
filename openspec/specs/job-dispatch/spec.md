# job-dispatch Specification

## Purpose

Hoe werk een draaiende agent wordt: één geparametriseerde K8s-Job, en verder
niets.

Bewust géén runner-infrastructuur. Een Job heeft een begin, een eind en een
status, en dat is precies wat je van een agent-run wilt weten zonder een tweede
systeem te bouwen dat dat bijhoudt.

De dragende eis is de **harde begrenzing in tijd en kosten**. Een agent die
vastloopt, doorloopt of in een lus komt kost geld en aandacht zolang niemand
kijkt — en niemand kijkt, want dat is het hele punt van autonoom werk. De grens
hoort daarom in de Job zelf te zitten en niet in het oordeel van de agent. Dat de
uitkomst uit de Job-status afleesbaar is volgt daaruit: als de grens toesloeg,
moet dat zichtbaar anders zijn dan "klaar".

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

### Requirement: The builder's own budget

When `HABITAT_BUILDER_BUDGET_USD` is set, dispatch SHALL run the builder role
with that budget and every other role with `HABITAT_MAX_BUDGET_USD`.

#### Scenario: A builder gets more room than the reviewers

- **WHEN** a chain is dispatched with `HABITAT_BUILDER_BUDGET_USD=10` and `HABITAT_MAX_BUDGET_USD=5`
- **THEN** the builder's `--max-budget-usd` is 10 and the other roles' is 5

### Requirement: Deadline per role

Without an explicit `ACTIVE_DEADLINE_SECONDS`, dispatch SHALL give a builder
Job an `activeDeadlineSeconds` of 3600 and every other role 1800, because a
builder runs the repository's tests, its database tests included, and the
other roles read and judge.

#### Scenario: A builder gets an hour

- **WHEN** a builder Job is dispatched without `ACTIVE_DEADLINE_SECONDS`
- **THEN** its `activeDeadlineSeconds` is 3600

#### Scenario: Other roles keep 30 minutes

- **WHEN** an architect, reviewer or security Job is dispatched without
  `ACTIVE_DEADLINE_SECONDS`
- **THEN** its `activeDeadlineSeconds` is 1800

### Requirement: One retry on a failed structured answer

When a role's run ends on `error_max_structured_output_retries`, the chain
SHALL dispatch that role once more before deciding; any other failure SHALL
stop the chain as before.

#### Scenario: A structured-output hiccup does not stop the chain

- **WHEN** the security role ends on `error_max_structured_output_retries`
- **THEN** the chain dispatches security once more
- **AND** stops only if that run fails too

### Requirement: A role's definition comes from the handbook at a pinned commit

When `HABITAT_HANDBOOK_REF` is set, the worker SHALL use
`docs/agents/seeds/<role>.md` of MWest2020/handbook at that commit as the
role file, stored outside the work tree, and SHALL stop the run when it cannot
be fetched; it SHALL NOT fall back to a copy in the target repository.

#### Scenario: The handbook seed is used

- **WHEN** a reviewer run starts with `HABITAT_HANDBOOK_REF` set to a handbook commit that has `docs/agents/seeds/reviewer.md`
- **THEN** that file is the role file, its body is in the prompt
- **AND** it does not appear in the role's commit

#### Scenario: A missing seed fails closed

- **WHEN** an architect run starts with a ref at which the handbook has no `docs/agents/seeds/architect.md`
- **THEN** the run stops with a non-zero exit and a `fail closed` log line
- **AND** the repository's `.claude/agents/architect.md` is not used

#### Scenario: Without a ref, the repo copy is a logged fallback

- **WHEN** a run starts without `HABITAT_HANDBOOK_REF`
- **THEN** the target repository's `.claude/agents/<role>.md` is the role file
- **AND** the log carries a `WARNING` naming the fallback
