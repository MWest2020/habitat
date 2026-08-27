## MODIFIED Requirements

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
