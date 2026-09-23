# worker-image-build Specification

## Purpose

Het image waar een worker in draait: reproduceerbaar, gepind, en per commit-SHA
gepubliceerd.

Een agent die zijn eigen gereedschap tijdens de run installeert, is een agent
waarvan je achteraf niet kunt zeggen wát er draaide. Dus zit alles wat hij nodig
heeft er al in — tools, testrunners, skills — en wordt het image geadresseerd op
commit-SHA in plaats van op een tag die kan verschuiven.

De skills zijn hier het interessante deel: ze zitten gepind in het image en
worden **per rol gematerialiseerd**. Een zoeker heeft een andere subset nodig dan
een architect, en alles meegeven kost context die de rol niet gebruikt. Het model
komt om dezelfde reden uit de rol en niet uit een default: welk model iets deed,
is onderdeel van wat er gebeurd is.

## Requirements

### Requirement: Reproduceerbare, gepinde Containerfile

De worker-image SHALL gebouwd worden uit een Containerfile met gepinde versies voor
de base-image en voor `git`, `uv`, Claude Code en de OpenSpec-CLI, zodat een build
reproduceerbaar is. De Containerfile SHALL nooit een `latest`-tag of ongepinde
installatie gebruiken.

#### Scenario: Build uit gepinde bronnen

- **WHEN** de image gebouwd wordt
- **THEN** verwijst elke tool-installatie naar een expliciete versie
- **AND** komt de tag `latest` nergens in de Containerfile voor

#### Scenario: Een rol kan zijn eigen change valideren

- **WHEN** een rol tijdens een run `openspec validate` op de change draait
- **THEN** is de CLI aanwezig in de image en staat de rol-allowlist precies dat
  subcommando toe, zodat het bewijs uit de run zelf komt in plaats van uit een
  latere handmatige controle

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

### Requirement: Toegestane testrunners zitten in de image

Elk commando dat een rol-allowlist toestaat als test- of buildrunner SHALL in de
worker-image aanwezig zijn. Een toegestaan maar ontbrekend commando is erger dan
een verboden commando: een `verify.sh` die de runner alleen "indien aanwezig"
aanroept, degradeert dan stil tot een no-op en de run meldt groen voor een
controle die niet gedraaid heeft.

#### Scenario: shellcheck is aanroepbaar in de kooi

- **WHEN** een builder-run `shellcheck` aanroept op een shellscript in de doelrepo
- **THEN** draait shellcheck echt en geeft hij zijn bevindingen terug, in plaats
  van te falen op een ontbrekend commando of overgeslagen te worden

### Requirement: Go-builds in de kooi zijn offline en falen hard op netwerk

De worker-image SHALL een Go-toolchain bevatten, gepind op tag en digest, zodat
de toegestane `go test|build|vet` echt draaien. De image SHALL
`GOTOOLCHAIN=local`, `GOPROXY=off` en `GOFLAGS=-mod=vendor` zetten, zodat een
Go-build uitsluitend uit de `vendor/` van de doelrepo bouwt en elke poging tot
module- of toolchain-download direct faalt. De egress-policy SHALL hiervoor
niet worden verruimd.

#### Scenario: Gevendorde doelrepo bouwt offline

- **WHEN** een builder-run `go build ./...` draait in een doelrepo met `vendor/`
- **THEN** bouwt Go uit `vendor/` zonder enige netwerkverbinding

#### Scenario: Ontbrekende vendor faalt hard

- **WHEN** een builder-run `go build ./...` draait in een Go-doelrepo zonder
  `vendor/`
- **THEN** faalt het commando direct met een Go-foutmelding over vendoring of
  `GOPROXY=off`, in plaats van te hangen op een geweigerde verbinding

#### Scenario: Nieuwere toolchain gevraagd

- **WHEN** de `go.mod` van een doelrepo een nieuwere Go-versie eist dan de image
- **THEN** faalt de build op `GOTOOLCHAIN=local` en downloadt Go niets
