## MODIFIED Requirements

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
