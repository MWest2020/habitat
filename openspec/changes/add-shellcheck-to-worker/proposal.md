# Change: add-shellcheck-to-worker

## Why

`shellcheck` staat in de builder-allowlist (`worker/settings/builder.json`:
`Bash(shellcheck *)`) en in `docs/reference/roles.md` als toegestane testrunner —
maar hij zit niet in de image. Gedeclareerd, toegestaan, afwezig: precies de vorm
van het openspec-CLI-gat dat `add-openspec-cli-to-worker` dichtte.

Het gevolg is erger dan een ontbrekend commando, want het faalt **stil**. De
`verify.sh` van de doelrepo's draait shellcheck alleen "indien aanwezig". In de
kooi is hij dat nooit, dus de shell-controle wordt een no-op zonder dat iemand
het merkt. Uit de eigen run-archieven van deze repo, letterlijk uit twee
verschillende runs op `internetnl-cli`:

> "`sh scripts/verify.sh` … pytest groen, **shellcheck niet geïnstalleerd** (dus
> ook in verify.sh zelf een no-op)"

> "verify.sh is niets meer dan `uv run pytest -q` + optionele shellcheck, en
> **shellcheck ontbreekt toch**"

Een verify-gate die in CI shell-fouten vangt (`.github/workflows/verify.yml`
installeert shellcheck wél) maar in de kooi niets doet, geeft een run een groen
vinkje voor werk dat niet is gedaan.

## What changes

- **`worker/Containerfile`**: `shellcheck` bij de bestaande apt-regel.
- **`docs/reference/roles.md`**: de regel over testrunners hoeft niet te wijzigen
  (shellcheck stond er al) — wel een noot dat hij nu daadwerkelijk in de image zit.

## Waarom apt en niet gepind

De bestaande apt-regel installeert `git`, `ca-certificates`, `jq` en `python3`
ongepind; de pin-conventie van deze repo geldt voor **images en CLI's** waar een
versieverschil het oordeel verandert (`BUZZ_IMAGE`, claude-code, de openspec-CLI).
shellcheck rapporteert shell-fouten, geen oordeel dat tussen versies verschuift,
en Debian bookworm levert één vaste versie per release — de image-basis is al
gepind op `node:22.11.0-bookworm-slim`. Meegaan met de bestaande regel is hier
dus consistent, niet slordig. Wie dat anders wil, pint de hele apt-regel in één
keer; dat is een eigen change.

## Impact

- Image wordt enkele MB's groter; nieuwe tag nodig, dispatchers verzetten
  `WORKER_IMAGE`.
- Geen gedragswijziging voor rollen die shellcheck niet aanroepen.
