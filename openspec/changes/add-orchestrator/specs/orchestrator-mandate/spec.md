## ADDED Requirements

### Requirement: Mandaat met autonoom/escaleer/verboden

De orchestrator-sessie SHALL een `orchestrator/CLAUDE.md`-mandaat volgen dat
letterlijk vastlegt wat autonoom mag, wat escaleert, en welke paden verboden zijn.
De orchestrator SHALL zelf geen productiecode schrijven en zelf geen merge doen.

#### Scenario: Autonome builder-run

- **WHEN** een change is goedgekeurd
- **THEN** dispatcht de orchestrator een builder-run (en daarna reviewer + security)
  zonder tussenkomst, en archiveert logs

#### Scenario: Geen zelf-merge

- **WHEN** een run groen is
- **THEN** merget de orchestrator niet, maar escaleert de merge naar Mark

### Requirement: Escalatie bij elke grens

De orchestrator SHALL pauzeren en Mark aanroepen (met een link naar het
HTML-run-rapport) bij: elke merge naar `main`, elke security-finding, elke nieuwe
dependency, elke spec-afwijking, meer dan twee mislukte herstelrondes, en
overschrijding van de kostendrempel per change.

#### Scenario: Security-finding

- **WHEN** een security-run een finding meldt
- **THEN** stopt de orchestrator en escaleert naar Mark met het run-rapport

#### Scenario: Kostendrempel

- **WHEN** de kosten per change de drempel overschrijden
- **THEN** escaleert de orchestrator in plaats van door te gaan

### Requirement: Verboden paden zijn hard-fail

De orchestrator SHALL wijzigingen aan `CLAUDE.md`, `.claude/agents/`,
NetworkPolicies/CiliumNetworkPolicies, RBAC of Job-templates als harde fout
behandelen — niet als escalatie. Dit SHALL dubbel afgedwongen zijn (reviewer +
branch protection/CODEOWNERS).

#### Scenario: Diff raakt een verboden pad

- **WHEN** een diff een verboden pad wijzigt
- **THEN** faalt het hard en wordt het niet doorgezet, ook niet via escalatie

### Requirement: tmux-indeling

Er SHALL een `orchestrator/start-tmux.sh` zijn die venster 0 met de
orchestrator-sessie en een statuspane (wachtrij/escalaties) opzet, en documenteert
hoe je per Job een log-pane toevoegt.

#### Scenario: Sessie opzetten

- **WHEN** `start-tmux.sh` draait
- **THEN** ontstaat een tmux-sessie met de orchestrator-pane en een statuspane
