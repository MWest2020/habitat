## ADDED Requirements

### Requirement: Skills zijn gepind meegebakken en worden per rol gematerialiseerd

De worker-image SHALL de skill-bodies uit skill-forge bevatten, gepind op een
commit (nooit een branch). Bij een run SHALL de worker **alleen** de skills
materialiseren die het rolbestand van de doelrepo noemt
(`.claude/agents/<rol>.md`, front-matter `skills:`). Een naam die geen slug is
SHALL geweigerd worden en een naam die niet in de image bestaat SHALL gemeld
worden; beide zonder de run te laten falen.

#### Scenario: Alleen wat de rol noemt

- **WHEN** een rolbestand één skill noemt terwijl de image er tientallen bevat
- **THEN** staat alleen die ene skill in het skills-pad van de agent

#### Scenario: Een naam die geen skill kan zijn

- **WHEN** het rolbestand een naam met padtekens of hoofdletters bevat
- **THEN** wordt die geweigerd met een melding, en wordt er niets buiten de
  skills-map van de image gekopieerd

#### Scenario: Skill-update is een zichtbare pin-bump

- **WHEN** skill-forge nieuwe of gewijzigde skills publiceert
- **THEN** verandert er niets aan draaiende runs tot de commit-pin in de
  Containerfile wordt opgehoogd

### Requirement: De worker draait op het model uit de rol

De worker SHALL het model uit het rolbestand van de doelrepo meegeven aan de
agent-run, en zonder dat veld draaien zoals voorheen (geen `--model`), zodat een
oudere doelrepo blijft werken.

#### Scenario: Model uit de rol

- **WHEN** het rolbestand `model: sonnet` declareert
- **THEN** draait de agent-run op dat model, zichtbaar in het runlog
