# worker-execution Specification

## Purpose
TBD - created by archiving change add-worker-image. Update Purpose after archive.
## Requirements
### Requirement: Env-interface van een worker

De worker SHALL zijn opdracht volledig uit environment-variabelen lezen en geen
andere invoerkanalen gebruiken, zodat elke run reproduceerbaar is uit zijn Job-spec.

De verplichte env-variabelen zijn: `HABITAT_REPO` (doelrepo, HTTPS-URL),
`HABITAT_ROLE` (builder/reviewer/security), `HABITAT_CHANGE` (naam van de
OpenSpec-change), `HABITAT_RUN_ID` (unieke run-identifier) en `GIT_PAT` (single-repo
fine-grained PAT voor git). Claude-auth komt uit gemounte
subscription-credentials (sub-first), niet uit een verplichte env-variabele.

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

De worker SHALL naar een **run-unieke** branch `habitat/<rol>/<change>-<run_id>`
pushen en SHALL `main` nooit rechtstreeks pushen. Omdat de branch per run uniek
is, SHALL de worker niet force-pushen en SHALL geen eerdere run overschreven
worden. De keten SHALL de builder-branch expliciet doorgeven aan reviewer en
security (via `HABITAT_BASE_BRANCH`), zodat die de juiste run lezen ook na een
retry.

#### Scenario: Clone via de proxy

- **WHEN** de worker clonet met `HTTPS_PROXY` gezet en een geldige PAT
- **THEN** slaagt de clone via de proxy
- **AND** verschijnt de PAT niet in `git remote -v`, de reflog of stdout

#### Scenario: Push van de resultaat-branch

- **WHEN** de rol-run een wijziging heeft geproduceerd
- **THEN** pusht de worker naar branch `habitat/<HABITAT_ROLE>/<HABITAT_CHANGE>-<HABITAT_RUN_ID>`
- **AND** pusht hij `main` nooit rechtstreeks
- **AND** force-pusht hij niet (de branch is uniek per run)

#### Scenario: Retry overschrijft de vorige run niet

- **WHEN** dezelfde rol+change een tweede keer draait (retry)
- **THEN** landt de nieuwe run op een andere run-unieke branch
- **AND** blijft de branch van de eerdere run bestaan

### Requirement: Aanroep van claude -p en succesbepaling

De worker SHALL `claude -p` niet-interactief draaien met `--output-format json`, een
`--max-budget-usd`-kostenrem en een non-interactieve permission-mode, en SHALL succes
uit het JSON-eindobject bepalen (`is_error`/`subtype`), niet uit de proces-exit-code.

Auth SHALL sub-first zijn: gemounte Claude-subscription-credentials
(`~/.claude/.credentials.json`), met `ANTHROPIC_API_KEY` als alternatief. Er SHALL
geen interactieve login nodig zijn.

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

### Requirement: Doel-repo-deps runtime, worker-tools gebakken

De worker-image SHALL alleen zijn eigen tools (`claude`, `uv`, `git`) bevatten;
doel-repo-afhankelijkheden SHALL runtime worden geïnstalleerd via de proxy.

#### Scenario: Doelrepo met eigen deps

- **WHEN** de doelrepo zijn eigen afhankelijkheden nodig heeft voor tests
- **THEN** installeert de rol-run die runtime via de proxy (pypi/npm)
- **AND** hoeft de worker-image daarvoor niet opnieuw gebouwd te worden

### Requirement: Tool-guard schermt credentials af, niet de rol-definitie

De PreToolUse-guard (tweede verdedigingslaag) SHALL secret- en
credential-paden weigeren voor alle rollen — minimaal `.credentials.json`,
`/var/run/claude/`, `/secrets/`, `.env`, `*.pem`, `id_rsa`, `/proc/` en
`/sys/` — ongeacht de allowlist, en SHALL faalt-dicht zijn (bij een parse- of
logicafout: weigeren).

De guard SHALL het **lezen** van de rol-definitie
`.claude/agents/<rol>.md` in de doelrepo toestaan, omdat de worker elke rol
opdraagt die te volgen. Deze uitzondering SHALL alléén gelden voor `Read` en
alléén voor paden die eindigen op `.claude/agents/<naam>.md`; `Edit`, `Write`
en `NotebookEdit` op `.claude/` SHALL geweigerd blijven, en alle overige
credential-/secret-paden onder `.claude/` (zoals `.credentials.json`) SHALL
geweigerd blijven.

#### Scenario: Rol leest zijn eigen definitie

- **WHEN** een rol `Read` aanroept op `.claude/agents/architect.md` in de doelrepo
- **THEN** staat de guard de lezing toe
- **AND** kan de rol de instructie volgen zonder de hook te omzeilen

#### Scenario: Credentials blijven dicht

- **WHEN** een tool een credential-pad raakt (`.claude/.credentials.json`,
  `/var/run/claude/…`) of een secret-pad (`.env`, `*.pem`, `id_rsa`, `/secrets/`)
- **THEN** weigert de guard, ook als het pad onder `.claude/` valt

#### Scenario: Schrijven naar de rol-definitie geweigerd

- **WHEN** een rol `Edit` of `Write` aanroept op `.claude/agents/<rol>.md`
- **THEN** weigert de guard (de uitzondering geldt alleen voor lezen)

