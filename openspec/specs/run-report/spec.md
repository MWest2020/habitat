# run-report Specification

## Purpose
TBD - created by archiving change add-audit-report. Update Purpose after archive.
## Requirements
### Requirement: Zelfstandig single-file HTML-run-rapport

Elke run SHALL een `.habitat/run-report-<run_id>.html` genereren: één bestand,
systeemfonts, geen CDN of externe requests, met diff-samenvatting, verdict,
kosten/turns en de audit-hashketen. Het rapport SHALL geversioneerd naast de code in
de branch staan.

#### Scenario: Rapport is zelfstandig

- **WHEN** het HTML-rapport in een browser wordt geopend zonder netwerk
- **THEN** rendert het volledig (geen externe scripts, fonts of afbeeldingen)

#### Scenario: Rapport staat in de branch

- **WHEN** een run een branch pusht
- **THEN** bevat de branch het HTML-rapport naast `run-report.json` en `.habitat/audit.jsonl`

### Requirement: In-browser verificatie van de hashketen

Het HTML-rapport SHALL de audit-keten met vanilla JS (`crypto.subtle`) herberekenen
en per schakel geldig/ongeldig tonen, zodat de lezer zonder tooling kan verifiëren.

#### Scenario: Geldige keten

- **WHEN** de keten intact is
- **THEN** toont het rapport elke schakel als geldig (✓)

#### Scenario: Gebroken keten

- **WHEN** een regel is gemanipuleerd
- **THEN** toont het rapport de betreffende schakel als ongeldig (✗)

