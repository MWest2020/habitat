## MODIFIED Requirements

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
