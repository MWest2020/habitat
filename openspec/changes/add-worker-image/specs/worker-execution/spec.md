## ADDED Requirements

### Requirement: Env-interface van een worker

De worker SHALL zijn opdracht volledig uit environment-variabelen lezen en geen
andere invoerkanalen gebruiken, zodat elke run reproduceerbaar is uit zijn Job-spec.

De verplichte env-variabelen zijn: `HABITAT_REPO` (doelrepo, HTTPS-URL),
`HABITAT_ROLE` (builder/reviewer/security), `HABITAT_CHANGE` (naam van de
OpenSpec-change), `HABITAT_RUN_ID` (unieke run-identifier), `ANTHROPIC_API_KEY`
(Claude-auth) en `GIT_PAT` (single-repo fine-grained PAT voor git).

#### Scenario: Alle env aanwezig

- **WHEN** de worker start met alle verplichte env-variabelen gezet
- **THEN** clonet hij `HABITAT_REPO` en start hij de rol-run zonder verdere invoer

#### Scenario: Ontbrekende verplichte env

- **WHEN** een verplichte env-variabele ontbreekt of leeg is
- **THEN** stopt de worker vóór de clone met een niet-nul exit en een leesbare
  foutmelding, en pusht hij niets

### Requirement: Clone en push over HTTPS met PAT

De worker SHALL de doelrepo over HTTPS clonen en pushen met de fine-grained PAT, en
SHALL geen SSH gebruiken, zodat al het git-verkeer door de egress-proxy past.

De PAT SHALL nooit in een commando-argument, de remote-URL of `run-report.json`
belanden dat in reflog of logs terechtkomt.

#### Scenario: Clone via de proxy

- **WHEN** de worker clonet met `HTTPS_PROXY` gezet en een geldige PAT
- **THEN** slaagt de clone via de proxy
- **AND** verschijnt de PAT niet in `git remote -v`, de reflog of stdout

#### Scenario: Push van de resultaat-branch

- **WHEN** de rol-run een wijziging heeft geproduceerd
- **THEN** pusht de worker naar branch `habitat/<HABITAT_ROLE>/<HABITAT_CHANGE>`
- **AND** pusht hij `main` nooit rechtstreeks

### Requirement: Aanroep van claude -p en succesbepaling

De worker SHALL `claude -p` niet-interactief draaien met `--output-format json`, een
`--max-budget-usd`-kostenrem en een non-interactieve permission-mode, en SHALL succes
uit het JSON-eindobject bepalen (`is_error`/`subtype`), niet uit de proces-exit-code.

Auth SHALL via `ANTHROPIC_API_KEY` gaan; er SHALL geen afhankelijkheid zijn van een
interactieve `~/.claude`-login.

#### Scenario: Geslaagde run

- **WHEN** het JSON-eindobject `is_error: false` heeft
- **THEN** merkt de worker de run als geslaagd en gaat door naar push

#### Scenario: Kostenrem bereikt

- **WHEN** `claude -p` de `--max-budget-usd`-grens raakt (mogelijk non-nul exit, maar
  wel JSON)
- **THEN** leest de worker het `subtype`/`is_error`-signaal uit de JSON
- **AND** merkt hij de run als niet-geslaagd, niet als crash

#### Scenario: Non-interactieve permission-mode

- **WHEN** de agent een tool wil gebruiken die anders om goedkeuring zou vragen
- **THEN** blokkeert de run niet op een prompt die nooit beantwoord wordt

### Requirement: Duurzaam run-rapport in de branch

De worker SHALL naast de code een `run-report.json` in de gepushte branch schrijven,
zodat het run-resultaat reconstrueerbaar is los van de vluchtige `kubectl logs`.

`run-report.json` SHALL minimaal bevatten: rol, change, run-id, verdict,
`total_cost_usd`, aantal turns en timestamps.

#### Scenario: Rapport na een run

- **WHEN** een run eindigt (geslaagd of niet)
- **THEN** bevat de branch een `run-report.json` met het verdict en `total_cost_usd`
- **AND** blijft dat rapport bestaan nadat de Job is opgeruimd

### Requirement: Doel-repo-deps runtime, worker-tools gebakken

De worker-image SHALL alleen zijn eigen tools (`claude`, `uv`, `git`) bevatten;
doel-repo-afhankelijkheden SHALL runtime worden geïnstalleerd via de proxy.

#### Scenario: Doelrepo met eigen deps

- **WHEN** de doelrepo zijn eigen afhankelijkheden nodig heeft voor tests
- **THEN** installeert de rol-run die runtime via de proxy (pypi/npm)
- **AND** hoeft de worker-image daarvoor niet opnieuw gebouwd te worden
