## ADDED Requirements

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
