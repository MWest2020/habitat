# worker-execution Specification

## Purpose

Wat er binnen de kooi gebeurt: de env-interface van een worker, hoe hij aan code
komt, hoe hij `claude -p` aanroept en hoe je achteraf ziet wat hij deed.

Dit is de capability waar alle grenzen samenkomen, want dit is het enige stuk
waar een agent echt iets doet. Vandaar de vorm: de interface is expliciet (een
worker krijgt env, geen verrassingen), git is het overdrachtsmedium (clone en
push over HTTPS met een PAT — geen gedeelde volumes, geen andere weg naar
buiten), en elke run laat een rapport in de branch achter.

De eis die het geheel draagt is de **tool-guard die credentials afschermt, niet
de rol-definitie**. Dat onderscheid is met opzet scherp: een worker mag niet bij
de sleutels waarmee hij zelf draait, maar hij moet wel kunnen lezen wat zijn rol
is. Een guard die alles dichtgooit levert een agent die niet weet wat hij mag —
en die vraagt het dan aan zichzelf.

## Requirements

### Requirement: Env-interface van een worker

De worker SHALL zijn opdracht volledig uit environment-variabelen en git lezen en
geen andere invoerkanalen (sockets, live kanalen, netwerk buiten de
egress-allowlist) gebruiken, zodat elke run reproduceerbaar is uit zijn Job-spec
+ git.

De verplichte env-variabelen zijn: `HABITAT_REPO` (doelrepo, HTTPS-URL),
`HABITAT_ROLE` (builder/reviewer/security), `HABITAT_CHANGE` (naam van de
OpenSpec-change), `HABITAT_RUN_ID` (unieke run-identifier) en `GIT_PAT`
(single-repo fine-grained PAT voor git). Claude-auth komt uit gemounte
subscription-credentials (sub-first), niet uit een verplichte env-variabele.

Daarnaast MAY een optionele `HABITAT_TASK_REF` gezet zijn: een pad **relatief aan
de doelrepo-root** naar een taak/context-bestand dat de worker ná de checkout uit
de gecloonde repo leest en als extra context aan de rol-run meegeeft. Dit is git,
geen nieuw invoerkanaal. De worker SHALL het pad begrenzen tot binnen de repo (geen
absolute paden, geen `..`); een pad buiten de repo of een niet-bestaand bestand
SHALL fail-closed behandeld worden (niet-nul exit, geen run, geen push), net als
een ontbrekende verplichte env-variabele.

#### Scenario: Alle env aanwezig

- **WHEN** de worker start met alle verplichte env-variabelen gezet
- **THEN** clonet hij `HABITAT_REPO` en start hij de rol-run zonder verdere invoer

#### Scenario: Ontbrekende verplichte env

- **WHEN** een verplichte env-variabele ontbreekt of leeg is
- **THEN** stopt de worker vóór de clone met een niet-nul exit en een leesbare
  foutmelding, en pusht hij niets

#### Scenario: Optionele taak-referentie aanwezig

- **WHEN** `HABITAT_TASK_REF` is gezet naar een bestaand pad binnen de doelrepo
- **THEN** leest de worker dat bestand ná de checkout en voegt de inhoud als
  context toe aan de rol-run; de run blijft reproduceerbaar uit Job-spec + git

#### Scenario: Taak-referentie buiten de repo of ontbrekend

- **WHEN** `HABITAT_TASK_REF` een absoluut pad, een `..`-pad, of een
  niet-bestaand bestand aanwijst
- **THEN** stopt de worker fail-closed (niet-nul exit, geen run, geen push)

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

### Requirement: A role's branch push retries before the role fails

The worker SHALL push a role's branch up to four times, with increasing waits between attempts, and SHALL fail the role on the push only when every attempt has failed. Each failed attempt SHALL be logged with its exit code. A retried push SHALL never be a force push.

#### Scenario: A transient push error

- **WHEN** the first push of a role's branch is rejected by the remote and a later attempt succeeds
- **THEN** the role's result stands and the log shows the failed attempts and the success

#### Scenario: The push keeps failing

- **WHEN** every push attempt fails
- **THEN** the role fails as it does today, after the last attempt

### Requirement: The builder can install and test a Node project

The builder role SHALL be allowed to run `npm install` (with or without
package names), `npm test` and `node --test`, so that it can create a
lockfile and run a Node repository's tests itself, not hand in tests that
never ran.

#### Scenario: A new package gets a lockfile and green tests

- **WHEN** a change adds a `package.json`
- **THEN** the builder can run `npm install` to write `package-lock.json`
- **AND** run the tests with `npm test` or `node --test`

### Requirement: The role knows its structured answer is final

The role prompt SHALL tell the role that its structured answer is its final
verdict, ends the run, is given exactly once at the end, and is never a
trial call, because under `--json-schema` the first structured answer is the
one the chain reads.

#### Scenario: A role does not try out the schema

- **WHEN** a role runs under `--json-schema`
- **THEN** its prompt states that the structured answer is final and must not
  be a trial call

### Requirement: Who pays for a worker

Dispatch SHALL run a worker on the subscription by default, and with
`HABITAT_AUTH=api` on the API key from Secret `habitat-api-key`, in which case
the worker SHALL have neither the setup-token nor the subscription
credentials, so it cannot fall back to the subscription. Any other value
SHALL stop the dispatch.

#### Scenario: An api-mode worker runs on the key

- **WHEN** a Job is dispatched with `HABITAT_AUTH=api`
- **THEN** the worker's `ANTHROPIC_API_KEY` comes from `habitat-api-key`
- **AND** it has no `CLAUDE_CODE_OAUTH_TOKEN` and no mounted credentials

#### Scenario: The default is unchanged

- **WHEN** a Job is dispatched without `HABITAT_AUTH`
- **THEN** it uses the setup-token and the optional credentials, as before

### Requirement: A throwaway test database in every worker

Every worker Job SHALL run a PostgreSQL 16 database as a native sidecar,
reachable only on the pod's loopback, started before the worker and stopped
with it, and SHALL give the worker its connection URL as
`HABITAT_TEST_DATABASE_URL` and as `WORDSWORTH_TEST_DATABASE_URL`, so a role
can run a repository's database tests instead of skipping them. The sidecar
SHALL run without root, without capabilities and without privilege
escalation, and its data SHALL NOT outlive the pod.

#### Scenario: The worker starts once the database answers

- **WHEN** a worker Job starts
- **THEN** the worker container starts only after the sidecar's
  `pg_isready` probe succeeds
- **AND** a connection to `HABITAT_TEST_DATABASE_URL` succeeds

#### Scenario: Nothing survives the run

- **WHEN** the worker container ends
- **THEN** the sidecar stops and its `emptyDir` is removed with the pod
