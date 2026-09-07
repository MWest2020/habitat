# Change: bake-skills-into-worker

## Why

Skills stonden in de agent-definities maar bereikten de agent nergens: de listener
gaf ze niet mee en de worker kende ze niet. Besluit Mark (2026-09-06): **geen MCP
op skill-forge** — skills horen bij de agent zelf, en meebakken in de image.

Token-grond, gemeten op het register: alle 44 gepromoveerde skills aanbieden kost
**≈ 4.010 tokens** per run aan slug+beschrijving (gemiddeld 91 per skill). Een rol
noemt er nul of één (`security`/`roodteam`: `thinking-red-team`, ≈ 52 tokens). Per
rol materialiseren scheelt dus ~95% op dat oppervlak, elke run opnieuw.

## What changes

- **Containerfile**: skill-bodies uit skill-forge, gepind op commit
  `44ce9a8d2b3e560e4927ed4e803eccccc9e7fe5f`, naar `/opt/habitat/skills`.
  Nooit een branch — een skill-update hoort een zichtbare pin-bump te zijn, net
  als bij `BUZZ_IMAGE` en de CLI-versies.
- **Entrypoint** leest het rolbestand van de doelrepo
  (`.claude/agents/<rol>.md`, front-matter uit handbook#12):
  - `skills:` → alleen die skills worden naar `~/.claude/skills/` gekopieerd;
  - `model:` → wordt als `--model` aan de agent-run meegegeven.

## Grenzen

- Namen worden op slug-vorm gefilterd (`a-z0-9-`), dus `../../etc` komt er niet
  door — met een melding, niet stil. Een onbekende skill wordt gemeld en de run
  gaat door: een ontbrekende skill is geen reden om bouwwerk te laten mislukken.
- Zonder `model:` in het rolbestand draait de run zoals voorheen. Oudere doelrepo's
  blijven dus werken.
- skill-forge is publiek, dus de build heeft geen token nodig.

## Impact

- Image wordt ~7 MB groter (47 skill-mappen). Alleen de beschrijvingen van de
  gematerialiseerde skills kosten context; bodies laden pas bij aanroep.
- Nieuwe image-tag nodig; dispatchers verzetten `WORKER_IMAGE`.
- Werkt pas volledig na handbook#12 (dat zet `model:` en `skills:` in de seeds).
