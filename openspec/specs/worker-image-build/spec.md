# worker-image-build Specification

## Purpose
TBD - created by archiving change add-worker-image. Update Purpose after archive.
## Requirements
### Requirement: Reproduceerbare, gepinde Containerfile

De worker-image SHALL gebouwd worden uit een Containerfile met gepinde versies voor
de base-image en voor `git`, `uv` en Claude Code, zodat een build reproduceerbaar
is. De Containerfile SHALL nooit een `latest`-tag of ongepinde installatie gebruiken.

#### Scenario: Build uit gepinde bronnen

- **WHEN** de image gebouwd wordt
- **THEN** verwijst elke tool-installatie naar een expliciete versie
- **AND** komt de tag `latest` nergens in de Containerfile voor

### Requirement: Publicatie naar GHCR per commit-SHA

De image SHALL door GitHub Actions gebouwd en naar GHCR gepusht worden, publiek en
getagd met de commit-SHA, nooit met `latest`, zodat elke gedraaide worker exact naar
één immutable image herleidbaar is.

#### Scenario: Push op een wijziging van de Containerfile

- **WHEN** de Containerfile of het entrypoint wijzigt op de default branch
- **THEN** bouwt de workflow de image en pusht die naar
  `ghcr.io/mwest2020/habitat-worker:<sha>`
- **AND** wordt er geen `latest`-tag gepubliceerd

#### Scenario: Herleidbaarheid van een run naar een image

- **WHEN** een worker-Job draait
- **THEN** verwijst zijn image-referentie naar een concrete SHA-tag
- **AND** is die tag terug te vinden bij een specifieke commit in de repo

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

