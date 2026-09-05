# Change: add-openspec-cli-to-worker

## Why

Changes in dit ecosysteem verifiëren zichzelf met `openspec validate --strict`;
dat staat als taak in vrijwel elke change. Een worker kan die taak niet uitvoeren:
de CLI zit niet in de image, en `openspec` staat in geen enkele rol-allowlist —
dus zelfs mét de CLI zou de aanroep door de deny-by-default-laag geweigerd worden.

Waargenomen 2026-09-04 op `internetnl-cli` (change `polish-supporter-mail`): een
builder-run van $4,14 en 116 turns had T2–T4 en het meeste van T5/T6 geïmplementeerd
en meldde toen:

> "de `openspec` CLI was niet beschikbaar in deze sandbox (`Failed to spawn:
> openspec`, ook niet via npx), dus `openspec validate ... --strict` kon niet
> daadwerkelijk gedraaid worden in dit run"

De rol deed precies wat hoort — niet doen alsof, geen work-around zoeken — maar het
gevolg is dat het bewijs dat de gate vraagt bij een mens terechtkomt in plaats van
in de run. Dat holt de keten uit: een run die "klaar" zegt zonder de validatie
gedraaid te hebben, is minder waard dan een run die het aantoont.

## What changes

- **`worker/Containerfile`**: `@fission-ai/openspec@1.3.1` erbij op de bestaande
  npm-regel, gepind conform de spec-eis "nooit `latest`, nooit ongepind".
  - Het kale `openspec` op npm is een **lege placeholder** (`0.0.0`); het echte
    pakket is `@fission-ai/openspec`. Wie dit bumpt: let daarop.
  - Versie **1.3.1** = wat lokaal en in de hub gebruikt wordt, zodat een validatie
    in een run hetzelfde oordeelt als op een werkstation. (npm staat inmiddels op
    1.12.0; bumpen is een bewuste eenregelige wijziging, geen bijvangst.)
- **Rol-allowlists**: `Bash(openspec validate *)` voor **builder**, **reviewer** en
  **security**.

## Waarom alleen `validate`, en waarom deze drie rollen

De allowlist is deny-by-default: alles wat er niet in staat, kan niet. Door
uitsluitend het subcommando `validate` toe te staan blijven de **muterende**
subcommando's geweigerd — met name `openspec archive`, dat mappen verplaatst en dus
buiten een builder-mandaat valt (archiveren is een besluit, geen bouwstap).

- **builder** — heeft de taak aantoonbaar nodig (zie hierboven).
- **reviewer** en **security** — beoordelen werk dat aan dezelfde gate moet voldoen;
  ze moeten die gate zelf kunnen draaien in plaats van de logica met de hand na te
  lopen. (Dat gebeurde 2026-09-05 op de handbook-review: "verified by tracing the
  script's logic manually, since executing uv run was sandbox-denied" — een
  eerlijke, maar zwakkere vorm van bewijs.)
- **architect** — bewust **niet**. Die plant en bouwt niet; hij heeft geen artefact
  om te valideren. Toe te voegen zodra daar een concrete run naar vraagt.

## Impact

- Image wordt marginaal groter; geen nieuwe runtime, npm zit al in de base.
- **Na merge bouwt de workflow een nieuwe image-tag. Dispatchers moeten
  `WORKER_IMAGE` naar die nieuwe SHA zetten** — een oudere pin heeft de CLI niet.
- Geen wijziging aan NetworkPolicies, RBAC, Job-templates of `CLAUDE.md`.
- De allowlist wordt verruimd. Dat is een bewuste, nauwe verruiming van de
  kooi-enforcement en hoort bij Mark te liggen, niet bij een agent — vandaar deze
  change in plaats van een stille aanpassing.
