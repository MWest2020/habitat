# Habitat builder — apply-docs-contract

_run_id builder-apply-docs-contract-20260712-185947 · verdict ok · 2026-07-12T19:02:53Z_

---

Done. Change `apply-docs-contract` is geïmplementeerd, lokaal gecommit op `habitat/builder/apply-docs-contract` (niet gepusht).

## Run-report — builder / apply-docs-contract

**Resultaat**: klaar, commit `ab24ad0`. Niet gepusht, geen PR, geen merge (CLAUDE.md-invariant + builder-rol).

**Wijzigingen**
| Bestand | Actie |
|---|---|
| `docs/index.md` | nieuw — wat is habitat, status, link README, links naar secties |
| `docs/explanation/architecture.md` | migratie van `docs/architecture.md` (relatieve `openspec/`-link naar `../../` gecorrigeerd) |
| `docs/architecture.md` | stub met verwijzing (`status: deprecated`) op de oude plek |
| `docs/reference/dispatch.md` | nieuw — dispatch-contract, feiten uit `dispatch.sh` + `job-template.yaml` + README |
| `docs/audit-dashboard.html` | ongewijzigd (asset, geen markdown) — conform proposal |
| `.mcp.json` | stond al correct met placeholder `TODO-change-3` — ongewijzigd |
| `tasks.md` | checkboxes bijgewerkt |

**Zelfcheck tegen het contract**: elke `.md` heeft YAML front matter met `status` + `last_reviewed: 2026-07-12`, **geen** `owner`-veld; markdown alleen in `explanation/`, `reference/` en `index.md` (+ de expliciet gevraagde redirect-stub); één taal (Nederlands). Alle gemigreerde/nieuwe pagina's op `status: draft` — pas een echte review zet `current`.

**Afwijkingen (bewust, gemeld i.p.v. geïmproviseerd)**
1. **Branch (1.1)**: gewerkt op de dispatch-branch `habitat/builder/apply-docs-contract` i.p.v. `docs/contract` — de habitat-conventie `habitat/<rol>/<change>` vervangt de losse naam uit de seed.
2. **PR (4.1) niet uitgevoerd**: CLAUDE.md "Commits blijven lokaal tot Mark pusht" en de builder-rol ("Never merge / never push") gaan vóór de taak-tekst. Push + PR + merge horen bij Mark. PR-titel staat vast: `docs: apply handbook docs contract`.

**PR-body (kant-en-klaar voor Mark)**
- [x] `docs/`-structuur volgens contract (index/how-to/reference/explanation; lege mappen weggelaten)
- [x] `docs/architecture.md` → `docs/explanation/architecture.md` + stub
- [x] Nieuw `docs/reference/dispatch.md` (dispatch-contract)
- [x] Nieuw `docs/index.md` (verwijst naar README, vervangt niet)
- [x] Front matter per pagina, geen `owner`, gemigreerd = `draft`
- [x] `.mcp.json` met placeholder `TODO-change-3`
- [x] Eén taal (Nederlands); `audit-dashboard.html` blijft als asset

Volgende stap is aan Mark: pushen + PR openen (titel hierboven) en mergen.
